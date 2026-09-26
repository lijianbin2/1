import re
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from xianyu_common import (
    FONT_BOLD,
    assert_no_overlap,
    assert_text_above,
    draw_board,
    enable_utf8_stdout,
    fit_font,
    get_font,
    require_valid_pngs,
    stack_blocks,
    stack_layout,
    text_extent,
    validate_png_files,
    wrap_text,
    wrap_text_fit,
)


class XianyuCommonTests(unittest.TestCase):
    def test_stack_layout_centers_blocks_without_grow(self):
        tops, sizes = stack_layout([100, 50], 0, 300, min_gap=0, max_gap=0)
        self.assertEqual(sizes, [100.0, 50.0])
        self.assertEqual(tops[0] + 100, tops[1])
        self.assertEqual(tops[0], stack_blocks([100, 50], 0, 300, min_gap=0, max_gap=0)[0])
        self.assertEqual(stack_layout([], 0, 100), ([], []))

    def test_stack_layout_grow_absorbs_leftover_space(self):
        """可伸缩区块吸收剩余空间，避免底部留大片空白。"""
        _, sizes = stack_layout([100, 50], 0, 400, grow=[0])
        self.assertGreater(sizes[0], 100)
        self.assertEqual(sizes[1], 50)

    def test_stack_layout_grow_respects_max_grow(self):
        _, sizes = stack_layout([100], 0, 900, grow=[0], max_grow=50, min_gap=20)
        self.assertLessEqual(sizes[0], 150)

    def test_stack_layout_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            stack_layout([0], 0, 100)
        with self.assertRaises(ValueError):
            stack_layout([100], 100, 0)
        with self.assertRaises(ValueError):
            stack_layout([100], 0, 100, grow=[3])
        with self.assertRaises(ValueError):
            stack_layout([100], 0, 100, grow=[0], max_grow=0)
        with self.assertRaises(ValueError):
            stack_layout([500, 500], 0, 300)

    def test_assert_no_overlap_detects_collision(self):
        assert_no_overlap([(0, 100), (120, 200)], "示例")
        assert_no_overlap([(120, 200), (0, 100)], "示例")
        with self.assertRaises(ValueError):
            assert_no_overlap([(0, 100), (80, 200)], "示例")

    def test_draw_board_returns_requested_size(self):
        image, draw = draw_board()
        self.assertEqual(image.size, (1080, 1080))
        self.assertEqual(draw.textlength(""), 0)
        with self.assertRaises(ValueError):
            draw_board(radius=-1)

    def test_wrap_text_handles_empty_and_wraps_by_width(self):
        image, draw = draw_board()
        font = ImageFont.load_default()
        self.assertEqual(wrap_text("", font, 100, draw), [])
        lines = wrap_text("abcdef", font, 20, draw)
        self.assertGreater(len(lines), 1)
        self.assertEqual("".join(lines), "abcdef")

    def test_wrap_text_fit_rejects_silent_truncation(self):
        """超行必须报错，而不是像 wrap_text(...)[:N] 那样丢掉末行。"""
        image, draw = draw_board()
        font = get_font(18)
        base = "素材包含不同尺寸和格式，请根据软件兼容性、设计需求和使用场景选择文件。"
        width = 400
        self.assertEqual(len(wrap_text(base, font, width, draw)), 2)
        # 正好占满上限时放行
        self.assertEqual(len(wrap_text_fit(base, font, width, 2, draw)), 2)
        # 再加一句就变 3 行，旧写法会静默丢掉第 3 行
        longer = base + "另外还包含大量高清预览与配套源文件可直接使用。"
        self.assertEqual(len(wrap_text(longer, font, width, draw)), 3)
        with self.assertRaises(ValueError) as ctx:
            wrap_text_fit(longer, font, width, 2, draw, label="04 页提示")
        message = str(ctx.exception)
        self.assertIn("04 页提示", message)
        self.assertIn("3 行", message)

    def test_wrap_text_fit_validates_max_lines(self):
        image, draw = draw_board()
        font = get_font(18)
        for bad in (0, -1, True, False, 1.5, "2"):
            with self.subTest(max_lines=bad):
                with self.assertRaises(ValueError):
                    wrap_text_fit("文案", font, 300, bad, draw)

    def test_no_renderer_silently_truncates_wrapped_text(self):
        """渲染器里不允许再出现 wrap_text(...)[:N]，那种写法会悄悄丢文案。"""
        root = Path(__file__).resolve().parent.parent
        targets = sorted(
            [*(root / "legacy").glob("*.py"), *root.glob("*.py")]
        )
        # 用非贪婪 .* 兼容嵌套括号，如 wrap_text(v, get_font(22, True), cw-32, d)[:2]；
        # 字面量 "wrap_text(" 不会匹配 wrap_text_fit(。
        pattern = re.compile(r"wrap_text\(.*\)\s*\[:\s*\d+\s*\]")
        offenders = []
        for path in targets:
            if path.name == "xianyu_common.py":
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if pattern.search(line):
                    offenders.append(f"{path.name}:{number} {line.strip()}")
        self.assertEqual(offenders, [], "改用 wrap_text_fit 以便超行时报警")

    def test_symbols_in_source_exist_in_font(self):
        """源码里的符号必须在 msyh 里有字形，否则图上会出现豆腐块。

        codex55 封面早先用了 ◉ 和 ▣，两个字形 msyh 都没有，页面上直接出现
        两个方框。这里用私用区字符（必定缺字）做指纹，逐一比对源码里出现的
        非中文符号是否和缺字渲染结果一致。
        """
        root = Path(__file__).resolve().parent.parent
        targets = sorted(
            [*(root / "legacy").glob("*.py"), *root.glob("*.py")]
        )
        image, draw = draw_board()
        font = get_font(28, True)

        def rendered(char: str) -> bytes:
            draw.rectangle([0, 0, 200, 200], fill="white")
            draw.text((10, 10), char, font=font, fill="black")
            return draw._image.tobytes()

        tofu = {rendered(chr(code)) for code in (0xE000, 0xE001, 0xE002)}
        offenders = []
        for path in targets:
            source = path.read_text(encoding="utf-8")
            # 只查字符串字面量里的非中文、非 ASCII 字符
            for literal in re.findall(r'"([^"\n]*)"|\'([^\'\n]*)\'', source):
                text = literal[0] or literal[1]
                for char in text:
                    if ord(char) < 128 or "一" <= char <= "鿿":
                        continue
                    if rendered(char) in tofu:
                        offenders.append(f"{path.name}: {char!r} (U+{ord(char):04X})")
        self.assertEqual(
            sorted(set(offenders)), [], "这些符号在 msyh 里缺字，会渲染成豆腐块"
        )

    def test_validate_png_files_reports_missing_wrong_size_and_corrupt_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (1080, 1080), "white").save(root / "01.png")
            Image.new("RGB", (640, 480), "white").save(root / "02.png")
            (root / "03.png").write_bytes(b"not a png")
            problems = validate_png_files(root, names=("01.png", "02.png", "03.png", "04.png"))
            self.assertEqual(problems, [root / "02.png", root / "03.png", root / "04.png"])

    def test_validate_png_files_reports_truncated_png(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = (root / "source.png")
            Image.new("RGB", (1080, 1080), "white").save(data)
            truncated = root / "01.png"
            payload = bytearray(data.read_bytes())
            idat_offset = payload.find(b"IDAT")
            self.assertGreaterEqual(idat_offset, 0)
            payload[idat_offset + 4] ^= 0xFF
            truncated.write_bytes(payload)
            self.assertEqual(validate_png_files(root, names=("01.png",)), [truncated])

    def test_validate_png_files_rejects_invalid_parameters_and_paths(self):
        with self.assertRaises(ValueError):
            validate_png_files(".", count=0)
        with self.assertRaises(ValueError):
            validate_png_files(".", size=(0, 1080))
        with self.assertRaises(ValueError):
            validate_png_files(".", names=[])
        with tempfile.TemporaryDirectory() as directory:
            problems = validate_png_files(directory, names=("../escape.png", "01.png", "01.png"))
            self.assertEqual(problems[0], Path("../escape.png"))
            self.assertEqual(problems[1], Path(directory) / "01.png")
            self.assertEqual(problems[2], Path(directory) / "01.png")

    def test_validate_png_files_refuses_to_pass_on_an_empty_file_list(self):
        """校验零个文件却报"通过"，比不校验更危险：调用方会以为验过了。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 5):
                Image.new("RGB", (1080, 1080), "white").save(root / f"{index:02d}.png")
            with self.assertRaises(ValueError) as caught:
                validate_png_files(root, names=[])
            self.assertIn("names", str(caught.exception))
            # require_valid_pngs 传空列表同样要拒，不能打印 validated
            with self.assertRaises(ValueError):
                require_valid_pngs(root, names=())

    def test_require_valid_pngs_passes_and_raises(self):
        """七个渲染入口共用的强制校验：产物可用才返回。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 5):
                Image.new("RGB", (1080, 1080), "white").save(root / f"{index:02d}.png")
            require_valid_pngs(root)
            require_valid_pngs(root, names=("01.png", "02.png"), label="封面")

            (root / "04.png").unlink()
            with self.assertRaises(RuntimeError) as caught:
                require_valid_pngs(root)
            self.assertIn("04.png", str(caught.exception))

    def test_require_valid_pngs_accepts_generator_names_once(self):
        """names 是生成器时不能被重复消费。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (1080, 1080), "white").save(root / "01.png")
            require_valid_pngs(root, names=(name for name in ("01.png",)), label="封面")

    def test_enable_utf8_stdout_survives_unconfigurable_streams(self):
        """标准输出被重定向到不支持编码设置的对象时不应抛错。"""
        class Stub:
            encoding = "gbk"

        import sys

        original = sys.stdout
        try:
            sys.stdout = Stub()  # type: ignore[assignment]
            enable_utf8_stdout()
        finally:
            sys.stdout = original
        self.assertIs(sys.stdout, original)

    def test_text_extent_measures_ink_not_anchor(self):
        """text 的 y 是顶部锚点，真实墨迹比 y+字号 更靠下，朴素估算会漏掉碰撞。"""
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(FONT_BOLD, 30)
        top, bottom = text_extent(draw, "超精细地理素材合集", font, 214)
        self.assertGreater(top, 214, "墨迹起点应在锚点之后")
        self.assertGreater(bottom, 214 + 30, "朴素 y+字号 会低估文字底部")
        assert_text_above(draw, "超精细地理素材合集", font, 214, bottom + 1, "封面")

    def test_assert_text_above_catches_what_naive_estimate_misses(self):
        """这正是地图封面副标题被图框压住的成因。"""
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(FONT_BOLD, 30)
        naive_bottom = 224 + 30
        self.assertLess(naive_bottom, 258, "朴素估算看起来没超")
        with self.assertRaises(ValueError):
            assert_text_above(draw, "超精细地理素材合集", font, 224, 258, "封面副标题")

    def test_assert_text_above_catches_collision(self):
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(FONT_BOLD, 30)
        with self.assertRaises(ValueError) as caught:
            assert_text_above(draw, "超精细地理素材合集", font, 214, 250, "封面副标题")
        self.assertIn("封面副标题", str(caught.exception))

    def test_fit_font_keeps_size_when_text_already_fits(self):
        """本来就放得下就不该缩字号。"""
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        font, width = fit_font(draw, "Skill知识库自动化", 262, 30, bold=True)
        self.assertEqual(font.size, 30)
        self.assertLessEqual(width, 262)

    def test_fit_font_shrinks_only_as_needed(self):
        """放不下时缩到刚好放下，不该无脑缩到最小。"""
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        font, width = fit_font(draw, "Skill知识库自动化", 170, 30, bold=True, min_size=16)
        self.assertLess(font.size, 30)
        self.assertLessEqual(width, 170)

    def test_fit_font_raises_instead_of_overflowing(self):
        """缩到下限仍放不下必须报错，不能静默把字压出卡片。

        这正是 cover_v2_legacy 里那个 while 的成因：break 写在循环体里，
        只试一次 20px 就退出，剩下放不下的部分直接溢出卡片右缘。
        """
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        with self.assertRaises(ValueError) as caught:
            fit_font(draw, "这是一段无论如何都放不下的超长文字", 40, 30, min_size=16)
        self.assertIn("放不下", str(caught.exception))

    def test_fit_font_never_drops_below_min_size(self):
        """步长跨过下限时不能交出比 min_size 更小的字号。

        size 和 min_size 相差不到 step 时（21 和 20），照直减就是 19px，
        调用方拿到一个它从没要求过的字号，排版基线就悄悄变了。
        """
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        for size, min_size, step in ((21, 20, 2), (15, 14, 2), (17, 15, 3)):
            with self.subTest(size=size, min_size=min_size, step=step):
                try:
                    font, _width = fit_font(
                        draw,
                        "宣传片背景音乐合集一键提升质感",
                        300,
                        size,
                        min_size=min_size,
                        step=step,
                    )
                except ValueError:
                    # 放不下时报错是正确行为，只是不该先跌破下限再报
                    continue
                self.assertGreaterEqual(
                    font.size,
                    min_size,
                    f"字号 {font.size} 跌破了声明的下限 {min_size}",
                )

    def test_fit_font_error_reports_the_size_it_actually_measured(self):
        """报错里的字号要是真量过的那个，否则排查会被带偏。"""
        im = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(im)
        with self.assertRaises(ValueError) as caught:
            fit_font(
                draw, "宣传片背景音乐合集一键提升影片质感与感染力", 250, 15,
                min_size=14, step=2,
            )
        self.assertIn("14px", str(caught.exception))
        self.assertNotIn("13px", str(caught.exception))
