import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageFont

from xianyu_common import draw_board, validate_png_files, wrap_text


class XianyuCommonTests(unittest.TestCase):
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
        with tempfile.TemporaryDirectory() as directory:
            problems = validate_png_files(directory, names=("../escape.png", "01.png", "01.png"))
            self.assertEqual(problems[0], Path("../escape.png"))
            self.assertEqual(problems[1], Path(directory) / "01.png")
            self.assertEqual(problems[2], Path(directory) / "01.png")
