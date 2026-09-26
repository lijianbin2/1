import re
import unittest
from pathlib import Path

import render_camera_basics as camera


SOURCE = Path(camera.__file__).read_text(encoding="utf-8")
DECLARED_CONSTANTS = ("LESSONS =", "CHAPTERS =")
COURSE_COUNT = re.compile(r"(\d+)\s*(?:节|个章节)")

# verify_source.py 对 M:\WebDAV\夸克\教程\相机基础入门课… 的实测结果：
# 41 个 mp4，文件名前缀 1.x~12.x 覆盖 12 个章节。
VERIFIED_LESSONS = 41
VERIFIED_CHAPTERS = 12


class CameraBasicsTests(unittest.TestCase):
    def test_course_size_matches_verified_source_scan(self):
        """课时数和章节数必须等于源目录实测值。"""
        self.assertEqual(camera.LESSONS, VERIFIED_LESSONS)
        self.assertEqual(camera.CHAPTERS, VERIFIED_CHAPTERS)

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
