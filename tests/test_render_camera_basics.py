import re
import unittest
from pathlib import Path

import render_camera_basics as camera


SOURCE = Path(camera.__file__).read_text(encoding="utf-8")
DECLARED_CONSTANTS = ("LESSONS =", "CHAPTERS =")
COURSE_COUNT = re.compile(r"(\d+)\s*(?:节|个章节)")


class CameraBasicsTests(unittest.TestCase):
    def test_all_renderers_create_four_square_images(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            camera.render_cover(out)
            camera.render_catalog(out)
            camera.render_outcomes(out)
            camera.render_guide(out)
            for number in range(1, 5):
                self.assertTrue((out / f"{number:02d}.png").is_file())

    def test_course_counts_come_from_single_source(self):
        """节数和章节数只能在常量处声明，图上文案一律用标签推导。"""
        self.assertEqual(camera.LESSON_LABEL, f"{camera.LESSONS}节")
        self.assertEqual(camera.CHAPTER_LABEL, f"{camera.CHAPTERS}个章节")

        offenders = []
        for line in SOURCE.splitlines():
            if any(marker in line for marker in DECLARED_CONSTANTS):
                continue
            if COURSE_COUNT.search(line):
                offenders.append(line.strip())
        self.assertEqual(offenders, [])

    def test_layout_blocks_stay_above_footer(self):
        self.assertLess(camera.FOOTER_TOP, camera.H)
        self.assertGreater(camera.FOOTER_TOP, 0)


if __name__ == "__main__":
    unittest.main()
