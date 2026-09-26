import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageFont

from render_map_collection import (
    W,
    H,
    image_fit,
    image_panel,
    render_catalog,
    render_cover,
    render_guide,
    render_outcomes,
)


class RenderMapCollectionTests(unittest.TestCase):
    def test_image_helpers_resize_and_paste(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            Image.new("RGB", (200, 120), "white").save(source)
            fitted = image_fit(source, (100, 80))
            self.assertEqual(fitted.size, (100, 80))

            base = Image.new("RGB", (200, 200), "white")
            image_panel(base, fitted, (20, 30, 120, 130), radius=8)
            self.assertEqual(base.getpixel((20, 30)), (255, 255, 255))
            with self.assertRaises(ValueError):
                image_panel(base, fitted, (20, 30, 10, 130))

    def test_all_renderers_create_four_square_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            (root / "中国各省高清晰巨幅地图").mkdir(parents=True)
            for name in ("超高清晰世界地图.jpg", "一亿像素中国地图.jpg", "中国各省高清晰巨幅地图/中国.jpg"):
                Image.new("RGB", (300, 180), "white").save(root / name)

            out = Path(directory) / "out"
            out.mkdir()
            with patch("render_map_collection.get_font", return_value=ImageFont.load_default()):
                render_cover(root, out)
                render_catalog(root, out)
                render_outcomes(root, out)
                render_guide(root, out)

            self.assertEqual((W, H), (1080, 1080))
            for number in range(1, 5):
                with Image.open(out / f"{number:02d}.png") as image:
                    self.assertEqual(image.size, (W, H))
