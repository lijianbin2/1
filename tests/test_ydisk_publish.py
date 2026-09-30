import tempfile
import unittest
import unittest.mock
from pathlib import Path

from ydisk_delivery import DeliveryError
from ydisk_publish import check_body, encode_multipart, load_body, load_images, publish


class CheckBodyTests(unittest.TestCase):
    def test_clean_body_passes(self):
        self.assertEqual(
            check_body("37 集视频课，从零搭建个人 AI 效率系统。\n虚拟资料，拍后发网盘链接。"),
            [],
        )

    def test_flags_share_url_and_passcode(self):
        self.assertIn("url-in-body", check_body("链接 https://pan.quark.cn/s/baaaaabbbbbb"))
        self.assertIn("url-in-body", check_body("见 https://www.quark.cn/s/x"))
        self.assertIn("delivery-field-in-body", check_body("提取码：ZZZZ"))

    def test_flags_price_and_shipping_promise(self):
        self.assertIn("price-in-body", check_body("仅售 9.9 元"))
        self.assertIn("shipping-promise-in-body", check_body("支持自动发货"))

    def test_empty_body_is_rejected(self):
        self.assertIn("empty-body", check_body("   \n  "))


class LoadBodyTests(unittest.TestCase):
    def _write(self, tmp: str, text: str) -> Path:
        path = Path(tmp) / "copy.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_first_line_becomes_the_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "WorkBuddy 智能体实战\n\n第一行正文\n第二行")
            title, description = load_body(path)
        self.assertEqual(title, "WorkBuddy 智能体实战")
        # 描述里必须保留标题首行，否则平台会把副标题当成标题
        self.assertEqual(description, "WorkBuddy 智能体实战\n\n第一行正文\n第二行")
        self.assertTrue(description.startswith(title))

    def test_description_keeps_title_so_platform_title_is_correct(self):
        """闲鱼没有独立标题栏：标题就是正文第一行。

        实测两个商品把标题拆出去单独提交后，平台把副标题提升成了标题，
        搜索结果里显示成"从零搭建个人AI效率系统…"。所以这里断言描述首行
        就是标题，防止以后有人为了"字段对齐"再拆一次。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp, "WorkBuddy 智能体实战 37集视频课\n从零搭建个人AI效率系统\n\n正文"
            )
            title, description = load_body(path)
        self.assertEqual(title, "WorkBuddy 智能体实战 37集视频课")
        self.assertEqual(description.split("\n")[0], title)
        self.assertIn("从零搭建个人AI效率系统", description)

    def test_title_over_thirty_characters_is_rejected(self):
        """闲鱼标题上限 30 字，超长会被平台截断，而 ydisk 这里直接报错更早。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "标" * 31 + "\n正文")
            with self.assertRaises(DeliveryError) as ctx:
                load_body(path)
        self.assertIn("30", str(ctx.exception))

    def test_blank_title_and_blank_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DeliveryError):
                load_body(self._write(tmp, "\n正文"))
            with self.assertRaises(DeliveryError):
                load_body(self._write(tmp, "   \n"))


class LoadImagesTests(unittest.TestCase):
    def test_returns_paths_in_requested_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("01.png", "02.png", "03.png"):
                (folder / name).write_bytes(b"x")
            images = load_images(folder, ["03.png", "01.png"])
        self.assertEqual([p.name for p in images], ["03.png", "01.png"])

    def test_more_than_three_images_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DeliveryError) as ctx:
                load_images(Path(tmp), ["a.png", "b.png", "c.png", "d.png"])
        self.assertIn("3", str(ctx.exception))

    def test_missing_image_and_empty_list_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DeliveryError):
                load_images(Path(tmp), [])
            with self.assertRaises(DeliveryError):
                load_images(Path(tmp), ["nope.png"])


class EncodeMultipartTests(unittest.TestCase):
    def test_carries_fields_boundary_and_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "01.png"
            image.write_bytes(b"\x89PNG-bytes")
            payload, content_type = encode_multipart(
                {"cookie_id": "123", "description": "正文"}, [image]
            )
        self.assertIn("multipart/form-data; boundary=", content_type)
        boundary = content_type.split("boundary=")[1]
        self.assertIn(f"--{boundary}--\r\n".encode(), payload)
        self.assertIn(b'name="cookie_id"', payload)
        self.assertIn("正文".encode("utf-8"), payload)
        self.assertIn(b'filename="01.png"', payload)
        self.assertIn(b"Content-Type: image/png", payload)
        self.assertIn(b"\x89PNG-bytes", payload)


class PublishQuantityTests(unittest.TestCase):
    """库存只能在下单那一刻设进去，发布后就再也改不动了。

    早先的结论是"ydisk 没有库存字段，只能手改"。实测是错的：
    ``POST /api/v1/items/publish`` 的 multipart 里有 ``quantity`` 字段，
    前端"库存数量"输入框绑的就是它。错在 ``publish()`` 有这个参数，
    而 ``main()`` 从来没往下传，恒为默认的 1。
    """

    def _captured_fields(self, quantity):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "01.png"
            image.write_bytes(b"\x89PNG-bytes")
            captured = {}

            def fake_encode(fields, images):
                captured.update(fields)
                return b"payload", "multipart/form-data; boundary=x"

            response = unittest.mock.MagicMock()
            response.read.return_value = b'{"success": true}'
            response.__enter__.return_value = response

            client = unittest.mock.Mock()
            client.base_url = "https://example.invalid"
            client.user_agent = "UA"
            client.cookies.return_value = []
            client.opener.open.return_value = response

            with unittest.mock.patch(
                "ydisk_publish.encode_multipart", side_effect=fake_encode
            ):
                publish(
                    client,
                    cookie_id="123",
                    title="标题",
                    body="正文",
                    price="1",
                    images=[image],
                    category_id="50023914",
                    category_name="电子资料",
                    channel_category_id="202036301",
                    quantity=quantity,
                )
        return captured

    def test_requested_stock_reaches_the_publish_payload(self):
        self.assertEqual(self._captured_fields(1111)["quantity"], "1111")

    def test_stock_defaults_to_one(self):
        self.assertEqual(self._captured_fields(1)["quantity"], "1")


if __name__ == "__main__":
    unittest.main()
