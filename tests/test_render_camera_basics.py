import re
import unittest
from pathlib import Path

import render_camera_basics as camera
from PIL import Image, ImageDraw

from xianyu_common import get_font, text_extent


SOURCE = Path(camera.__file__).read_text(encoding="utf-8")
DECLARED_CONSTANTS = ("LESSONS =", "CHAPTERS =")
COURSE_COUNT = re.compile(r"(\d+)\s*(?:节|个章节)")
LESSON_RANGE = re.compile(r"\"(\d+)\.(\d+)(?:-(\d+)\.(\d+))?\"")

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

    def test_module_lesson_ranges_chain_to_declared_course_length(self):
        """目录页的课号区间必须首尾相接，累加后等于 LESSONS，章数等于 CHAPTERS。

        这张目录图上的 12 个模块各写了一个课号区间，商品文案写的是 41 节。
        两处数字各写各的，一旦改动其一，图上就会出现目录止于第 40 课、商品却
        卖 41 课的矛盾，所以这里从源码里把区间解析出来做累加守卫。
        """
        block = re.search(
            r"^\s*modules = \[(.*?)^\s*\]", SOURCE, re.MULTILINE | re.DOTALL
        )
        assert block is not None, "找不到 modules 数据表"
        ranges = LESSON_RANGE.findall(block.group(1))
        self.assertEqual(len(ranges), camera.CHAPTERS, "模块数与章节数不一致")

        by_chapter = {}
        for chapter, first, last_chapter, last in ranges:
            start, end = int(first), int(last or first)
            self.assertEqual(
                int(chapter), len(by_chapter) + 1, "章节号必须从 1 开始连续"
            )
            self.assertEqual(
                int(last_chapter or chapter), int(chapter), "课号区间不能跨章"
            )
            self.assertEqual(start, 1, f"第 {chapter} 章必须从 .1 开始")
            self.assertGreaterEqual(end, start, f"第 {chapter} 章区间终点小于起点")
            by_chapter[int(chapter)] = (start, end)

        total = 0
        # 课号是"章.节"，每章都从 .1 重新起编，所以累加的是各章的节数本身
        for start, end in by_chapter.values():
            total += end - start + 1
        self.assertEqual(total, camera.LESSONS)
        self.assertEqual(total, VERIFIED_LESSONS)

    def test_footer_two_lines_do_not_overlap(self):
        """底栏两行必须按 FOOTER_TOP 相对定位，墨迹之间要有可见间距。

        早先这里写成 H-BORDER-68 / H-BORDER-47，相差 21px，而 24px 与 20px
        两行的真实墨迹几乎占满行高，实测间距 -4px，两行是叠在一起的。
        """
        footer_body = re.search(
            r"^def footer\(.*?(?=^\S)", SOURCE, re.MULTILINE | re.DOTALL
        )
        assert footer_body is not None, "找不到 footer 函数"
        # 注释里会引用旧写法说明来由，负向检查只针对真实代码
        body = "\n".join(
            line
            for line in footer_body.group(0).splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertNotIn("H-BORDER-68", body.replace(" ", ""))
        self.assertNotIn("H-BORDER-47", body.replace(" ", ""))
        self.assertIn("FOOTER_TOP+12", body.replace(" ", ""))
        self.assertIn("FOOTER_TOP+48", body.replace(" ", ""))

        draw = ImageDraw.Draw(Image.new("RGB", (camera.W, camera.H), "white"))
        first = text_extent(draw, "只发夸克", get_font(24, True), camera.FOOTER_TOP + 12)
        second = text_extent(
            draw,
            f"相机基础 · {camera.LESSON_LABEL} · 摄影入门",
            get_font(20),
            camera.FOOTER_TOP + 48,
        )
        self.assertGreater(
            second[0] - first[1], 6, "底栏两行墨迹几乎贴在一起，会看成一团"
        )


if __name__ == "__main__":
    unittest.main()
