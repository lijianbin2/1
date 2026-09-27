"""生成企业宣传视频剪映模板合集的四张闲鱼图文。

分类明细不是手打的：源目录里 41 个 zip 的文件名自带主题词（历程、企业文化、
照片墙、卡点……），``categorize`` 按关键词把这些文件归到七个分类，各分类
数量由 ``scan_source`` 实测后统计得出，分类漏掉任何一个文件都会直接报错。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from verify_source import SourceStats, scan_source
from xianyu_common import (
    assert_no_overlap,
    assert_text_above,
    chip_positions,
    draw_board,
    enable_utf8_stdout,
    get_font,
    require_valid_pngs,
    save_png,
    stack_layout,
    text_extent,
    wrap_text_fit,
)


W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
PALE = (248, 250, 252)
PURPLE = (124, 58, 237)
TEAL = (14, 165, 233)
GREEN = (16, 185, 129)
ORANGE = (249, 115, 22)
ROSE = (225, 29, 72)
FOOTER_H = 86
FOOTER_TOP = H - BORDER - FOOTER_H

# 封面卡片网格。末行底边必须落在 SUMMARY_TOP 上方，否则会压住摘要文字。
CARD_W, CARD_H, CARD_GAP = 280, 124, 18
CARD_TOP, SUMMARY_TOP = 366, 815
COVER_COLS = 3

# 02 页分类卡版式。位置由条目数推出，不写死行数。
CAT_COLS = 2
CAT_CARD_H = 154
CAT_CARD_GAP = 22
CAT_CARD_TOP = 190

# 03 页收获卡与"适合谁"横条。走 stack_layout 按可用高度分配。
OUT_COLS = 2
OUT_CARD_H = 190
OUT_GAP = 24
OUT_SUIT_H = 82
OUT_TOP = 190

# 04 页步骤卡与提示框，同样走 stack_layout。
STEP_H_BASE = 110
STEP_GAP = 16
STEP_TOP = 190
WARN_H = 133

# 七个分类的关键词规则。**顺序有意义**：命中即归类，不再往下看。
# 例如"13-70秒红底金边企业励志文化"同时含"励志"和"文化"，按本顺序归到
# 表彰励志；"25-企业活动宣传高级卡点视频"同时含"卡点"和"高级"，按本顺序
# 归到卡点快闪。调换顺序会让实测数量对不上，test_classify_matches_the_real
# _source_directory 会立刻变红。
CATEGORY_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("企业历程回顾", "蓝底", ("历程", "回顾", "大事件")),
    ("表彰励志年会", "金红", ("励志", "表彰", "颁奖", "优秀员工", "年会")),
    ("照片墙相册", "暖橙", ("照片墙", "相册")),
    ("卡点快闪电商", "玫红", ("卡点", "快闪", "电商", "促销")),
    ("企业文化介绍", "青绿", ("企业文化", "文化")),
    ("科技风高级感", "紫调", ("科技", "高级", "藏蓝", "3维", "中国风")),
    ("片头与通用宣传", "天蓝", ("片头", "开头", "宣讲", "视察", "企业宣传", "企业模板")),
)
COLORS = (BLUE, ORANGE, ROSE, GREEN, PURPLE, TEAL, BLUE)
SHORT_NAMES = (
    "历程", "表彰", "照片墙", "卡点", "文化", "科技", "片头",
)
CATEGORY_DESC = {
    "企业历程回顾": "发展历程、大事件、图文回顾",
    "表彰励志年会": "表彰大会、优秀员工、年会开场",
    "照片墙相册": "照片墙、相册带倒影动态展示",
    "卡点快闪电商": "活动快闪、卡点节奏、电商促销",
    "企业文化介绍": "动态文字、简约白底中国文化风",
    "科技风高级感": "科技蓝、藏蓝高级质感模板",
    "片头与通用宣传": "通用片头、宣讲开头、领导视察",
}
SUMMARY = "套模板换图换字，企业短片自己就能剪出来"

DEFAULT_ROOT = Path(
    r"M:/WebDAV/夸克/软件/企业宣传视频剪映模板合集，一键制作专业级推广短片"
)
DEFAULT_OUT = Path("D:/闲鱼/企业宣传视频剪映模板合集，一键制作专业级推广短片")


def categorize(filename: str) -> str:
    """按文件名里的主题词归类；命中不了就抛错，不静默丢文件。"""
    stem = Path(filename).stem
    for name, _tone, keywords in CATEGORY_RULES:
        if any(keyword in stem for keyword in keywords):
            return name
    raise ValueError(f"文件名里认不出分类，请补一条关键词规则：{filename}")


def category_table(root: Path) -> list[tuple[str, int, tuple[int, int, int]]]:
    """扫描源目录，按关键词派生七个分类的实测数量。"""
    paths = sorted(p for p in root.rglob("*") if p.is_file())
    if not paths:
        raise ValueError(f"源目录没有文件：{root}")
    counts = {name: 0 for name, _tone, _kw in CATEGORY_RULES}
    for path in paths:
        counts[categorize(path.name)] += 1
    return [
        (name, counts[name], COLORS[index])
        for index, (name, _tone, _kw) in enumerate(CATEGORY_RULES)
    ]


def cover_grid(card_count: int) -> tuple[int, int]:
    """由卡片数推出封面网格的行数与末行底边。"""
    if card_count < 1:
        raise ValueError("封面至少要 1 张卡片")
    rows = -(-card_count // COVER_COLS)
    bottom = CARD_TOP + rows * CARD_H + (rows - 1) * CARD_GAP
    if bottom >= SUMMARY_TOP:
        raise ValueError(
            f"封面 {card_count} 张卡放不下：末行底边 {bottom}，摘要从 {SUMMARY_TOP} 开始"
        )
    return rows, bottom


def catalog_grid(card_count: int) -> tuple[int, int]:
    """由条目数推出 02 页网格的行数与底边，放不下就报错。"""
    if card_count < 1:
        raise ValueError("02 页至少要 1 张分类卡")
    rows = -(-card_count // CAT_COLS)
    bottom = CAT_CARD_TOP + rows * CAT_CARD_H + (rows - 1) * CAT_CARD_GAP
    if bottom > FOOTER_TOP - CAT_CARD_GAP:
        raise ValueError(
            f"02 页 {card_count} 张卡放不下：网格底边 {bottom}，底栏从 {FOOTER_TOP} 开始"
        )
    return rows, bottom


def outcomes_layout(count: int) -> tuple[int, int, int]:
    """返回 03 页的 (卡片区顶部, 横条顶部, 单卡高度)。"""
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("03 页卡片数量必须为正整数")
    rows = -(-count // OUT_COLS)
    tops, sizes = stack_layout(
        [OUT_CARD_H * rows + OUT_GAP * (rows - 1), OUT_SUIT_H],
        OUT_TOP,
        FOOTER_TOP - 40,
        grow=[0],
        max_grow=40,
    )
    card_h = int((sizes[0] - OUT_GAP * (rows - 1)) / rows)
    if card_h < OUT_CARD_H:
        raise ValueError(f"03 页卡片高度 {card_h} 小于基准 {OUT_CARD_H}")
    assert_no_overlap(
        [(tops[0], tops[0] + sizes[0]), (tops[1], tops[1] + OUT_SUIT_H)],
        "03 页",
    )
    return tops[0], tops[1], card_h


def guide_layout(count: int) -> tuple[list[int], int, int, int]:
    """返回 04 页的 (各步顶边, 单步高, 提示框顶, 提示框底)。"""
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("04 页步骤数量必须为正整数")
    tops, sizes = stack_layout(
        [count * STEP_H_BASE + (count - 1) * STEP_GAP, WARN_H],
        STEP_TOP,
        FOOTER_TOP - 30,
        grow=[0],
        max_grow=40,
    )
    step_h = int((sizes[0] - (count - 1) * STEP_GAP) / count)
    if step_h < STEP_H_BASE:
        raise ValueError(f"04 页步骤高度 {step_h} 小于基准 {STEP_H_BASE}")
    # 逐张画步骤卡，所以要的是每一步的顶边。早先直接把 stack_layout 的两个
    # 块顶边返回出去，render_guide 里 zip(tops, steps) 只配上前 2 步，
    # 4 步的后两步被静默丢掉，04 页少一半内容还照样退出码 0。
    step_tops = [tops[0] + i * (step_h + STEP_GAP) for i in range(count)]
    warn_top = tops[1]
    warn_bottom = warn_top + WARN_H
    assert_no_overlap(
        [(tops[0], tops[0] + sizes[0]), (warn_top, warn_bottom)],
        "04 页步骤卡与提示框",
    )
    return step_tops, step_h, warn_top, warn_bottom


def centered(draw, text: str, y: int, font, fill=DARK) -> None:
    draw.text(((W - draw.textlength(text, font=font)) // 2, y), text, fill=fill, font=font)


def footer(draw, right: str) -> None:
    draw.rounded_rectangle([BORDER, FOOTER_TOP, W - BORDER, H - BORDER], radius=22, fill=DARK)
    draw.text((BORDER + 40, FOOTER_TOP + 12), "只发夸克", fill="white", font=get_font(24, True))
    font = get_font(20)
    draw.text(
        (W - BORDER - 40 - draw.textlength(right, font=font), FOOTER_TOP + 48),
        right, fill=(203, 213, 225), font=font,
    )


def render_cover(out: Path, table: list[tuple[str, int, tuple[int, int, int]]],
                 files_label: str, size_label: str) -> None:
    im, d = draw_board()
    badge = f"企业宣传 {files_label}剪映模板"
    badge_font = get_font(25, True)
    badge_w = d.textlength(badge, font=badge_font) + 40
    badge_y = 78
    d.rounded_rectangle(
        [(W - badge_w) // 2, badge_y, (W + badge_w) // 2, badge_y + 42], radius=21, fill=BLUE
    )
    centered(d, badge, badge_y + 8, badge_font, "white")
    centered(d, "企业宣传视频剪映模板", 150, get_font(52, True))
    centered(d, "一键制作专业级推广短片", 232, get_font(30), GRAY)
    d.line([400, 308, 680, 308], fill=BLUE, width=4)

    rows, grid_bottom = cover_grid(len(table))
    start_x = (W - CARD_W * COVER_COLS - CARD_GAP * (COVER_COLS - 1)) // 2
    for index, (name, count, color) in enumerate(table):
        row, col = divmod(index, COVER_COLS)
        x = start_x + col * (CARD_W + CARD_GAP)
        y = CARD_TOP + row * (CARD_H + CARD_GAP)
        d.rounded_rectangle(
            [x, y, x + CARD_W, y + CARD_H], radius=20, fill=PALE,
            outline=(226, 232, 240), width=1,
        )
        d.ellipse([x + 24, y + 24, x + 84, y + 84], fill=color)
        d.text((x + 40, y + 42), "剪", fill="white", font=get_font(24, True))
        name_font = get_font(25, True)
        d.text((x + 100, y + 26), SHORT_NAMES[index], fill=DARK, font=name_font)
        assert_text_above(
            d, SHORT_NAMES[index], name_font, y + 26, y + 66,
            f"封面卡片 {SHORT_NAMES[index]} 标题与下方数量",
        )
        d.text((x + 100, y + 68), f"{count}个", fill=color, font=get_font(25, True))
    assert_no_overlap(
        [(CARD_TOP, grid_bottom), (SUMMARY_TOP, H - BORDER)], "01 页卡片区与摘要"
    )

    summary_line = " · ".join(SHORT_NAMES)
    d.text((BORDER + 40, SUMMARY_TOP), summary_line, fill=DARK, font=get_font(22, True))
    d.text((BORDER + 40, SUMMARY_TOP + 43), SUMMARY, fill=GRAY, font=get_font(21))
    footer(d, f"{size_label} · {len(table)}大分类 · 剪映可直接导入")
    save_png(im, out / "01.png")


def render_catalog(out: Path, table: list[tuple[str, int, tuple[int, int, int]]],
                   files_label: str, size_label: str) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "模板目录", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        f"按用途分类整理，{files_label}挑模板不用翻", fill=GRAY, font=get_font(24),
    )
    badge = f"共{files_label}"
    bf = get_font(24, True)
    bw = d.textlength(badge, font=bf) + 34
    d.rounded_rectangle(
        [W - BORDER - 40 - bw, BORDER + 36, W - BORDER - 40, BORDER + 76],
        radius=19, fill=(239, 246, 255),
    )
    d.text((W - BORDER - 40 - bw + 17, BORDER + 45), badge, fill=BLUE, font=bf)

    _, grid_bottom = catalog_grid(len(table))
    card_w = (W - BORDER * 2 - 80 - 24) // 2
    for index, (name, count, color) in enumerate(table):
        row, col = divmod(index, CAT_COLS)
        x = BORDER + 40 + col * (card_w + 24)
        y = CAT_CARD_TOP + row * (CAT_CARD_H + CAT_CARD_GAP)
        d.rounded_rectangle(
            [x, y, x + card_w, y + CAT_CARD_H], radius=18, fill=PALE,
            outline=(226, 232, 240), width=1,
        )
        d.rounded_rectangle([x, y, x + card_w, y + 8], radius=5, fill=color)
        title = f"{index + 1:02d} {name}"
        d.text((x + 18, y + 24), title, fill=DARK, font=get_font(23, True))
        d.text((x + 18, y + 66), f"{count}个", fill=color, font=get_font(29, True))
        desc = CATEGORY_DESC[name]
        desc_font = get_font(18)
        lines = wrap_text_fit(desc, desc_font, card_w - 36, 2, d, label=f"02 页 {name}")
        for line_no, line in enumerate(lines):
            d.text((x + 18, y + 112 + line_no * 24), line, fill=GRAY, font=desc_font)
    assert_no_overlap(
        [(CAT_CARD_TOP, grid_bottom), (FOOTER_TOP, H - BORDER)], "02 页分类区与底栏"
    )
    footer(d, f"7大分类 · {files_label} · 剪映时间线直接用")
    save_png(im, out / "02.png")


def render_outcomes(out: Path, table: list[tuple[str, int, tuple[int, int, int]]],
                    files_label: str, size_label: str) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "使用收获", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        "不用从零搭剪映，套模板换素材就能出片", fill=GRAY, font=get_font(24),
    )
    points = [
        ("套模板即成片", "导入剪映时间线，替换图片和文字，几十秒出粗剪", BLUE),
        ("分类清楚好找", "历程、文化、表彰、卡点按用途分好，不用逐个试", PURPLE),
        ("横竖屏都有", "横屏适合官网大屏，竖屏适合朋友圈和短视频", TEAL),
        ("新手也能剪", "动效和转场已经调好，不用懂关键帧和调色", GREEN),
    ]
    grid_y, suit_y, card_h = outcomes_layout(len(points))
    card_w = 460
    for index, (title, desc, color) in enumerate(points):
        row, col = divmod(index, OUT_COLS)
        x = BORDER + 40 + col * (card_w + OUT_GAP)
        y = grid_y + row * (card_h + OUT_GAP)
        d.rounded_rectangle(
            [x, y, x + card_w, y + card_h], radius=20, fill=PALE,
            outline=(226, 232, 240), width=1,
        )
        d.rounded_rectangle([x + 22, y + 22, x + 76, y + 76], radius=20, fill=color)
        d.text((x + 37, y + 35), str(index + 1), fill="white", font=get_font(24, True))
        d.text((x + 96, y + 25), title, fill=DARK, font=get_font(25, True))
        body_font = get_font(18)
        for line_no, line in enumerate(
            wrap_text_fit(desc, body_font, card_w - 120, 3, d, label=f"03 页 {title}")
        ):
            d.text((x + 96, y + 77 + line_no * 27), line, fill=GRAY, font=body_font)

    d.rounded_rectangle(
        [BORDER + 40, suit_y, W - BORDER - 40, suit_y + OUT_SUIT_H],
        radius=18, fill=(239, 246, 255),
    )
    d.text((BORDER + 60, suit_y + 14), "适合", fill=BLUE, font=get_font(20, True))
    chip_font = get_font(20)
    for text, x, width in chip_positions(
        d,
        ("中小企业主", "宣传片剪辑", "活动策划", "行政HR", "电商运营"),
        font=chip_font,
        left=BORDER + 130,
        right=W - BORDER - 60,
        pad=26,
        gap=14,
        label="03 页适合谁标签行",
    ):
        d.rounded_rectangle([x, suit_y + 38, x + width, suit_y + 72], radius=17, fill="white")
        d.text((x + 13, suit_y + 45), text, fill=DARK, font=chip_font)
    footer(d, f"横竖屏通用 · {files_label} · 剪映专业版可用")
    save_png(im, out / "03.png")


def render_guide(out: Path, table: list[tuple[str, int, tuple[int, int, int]]],
                 files_label: str, size_label: str) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "购买前说明", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        "虚拟资料 · 拍后发夸克链接", fill=GRAY, font=get_font(24),
    )
    steps = [
        ("1", "资料内容", f"剪映企业宣传片模板{files_label}，压缩包形式打包"),
        ("2", "适用软件", "剪映专业版，导入后可直接在时间线上替换素材"),
        ("3", "使用方法", "解压后导入模板，替换图片和文字，调整时长即可"),
        ("4", "交付方式", "拍下后发送夸克网盘链接与提取码"),
    ]
    tops, step_h, warn_top, warn_bottom = guide_layout(len(steps))
    for y, (number, title, desc) in zip(tops, steps):
        d.rounded_rectangle(
            [BORDER + 40, y, W - BORDER - 40, y + step_h], radius=18, fill=PALE,
            outline=(226, 232, 240), width=1,
        )
        d.ellipse([BORDER + 60, y + 30, BORDER + 106, y + 76], fill=BLUE)
        number_font = get_font(23, True)
        nw = d.textlength(number, font=number_font)
        d.text((BORDER + 83 - nw / 2, y + 40), number, fill="white", font=number_font)
        d.text((BORDER + 130, y + 22), title, fill=DARK, font=get_font(24, True))
        desc_font = get_font(18)
        for line_no, line in enumerate(
            wrap_text_fit(desc, desc_font, W - BORDER * 2 - 155, 2, d, label=f"04 页 {title}")
        ):
            d.text((BORDER + 130, y + 59 + line_no * 24), line, fill=GRAY, font=desc_font)

    d.rounded_rectangle(
        [BORDER + 40, warn_top, W - BORDER - 40, warn_bottom], radius=18,
        fill=(255, 251, 235), outline=(253, 230, 138), width=1,
    )
    d.text((BORDER + 62, warn_top + 25), "温馨提示", fill=(146, 64, 14), font=get_font(23, True))
    tip = "模板为剪映时间线工程，需自备剪映专业版使用；素材版权与商用范围请自行确认，拍前可先咨询适配需求。"
    tip_font = get_font(18)
    for index, line in enumerate(
        wrap_text_fit(tip, tip_font, W - BORDER * 2 - 130, 3, d, label="04 页提示")
    ):
        d.text((BORDER + 62, warn_top + 69 + index * 25), line, fill=(120, 113, 108), font=tip_font)
    footer(d, f"{size_label} · 企业宣传片剪映模板合集")
    save_png(im, out / "04.png")


def stats_labels(stats: SourceStats) -> tuple[str, str]:
    """把实测统计转成图上用的短标签，数量与体积都不手打。"""
    return f"{stats.total_files}个模板", f"约{stats.size_gb:.2f}GB"


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="生成企业宣传视频剪映模板合集四张图文")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="剪映模板源目录")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="图片输出目录")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # 数量、体积、分类明细一律来自源目录实测
    stats = scan_source(args.root)
    files_label, size_label = stats_labels(stats)
    table = category_table(args.root)
    classified = sum(count for _name, count, _color in table)
    if classified != stats.total_files:
        raise ValueError(
            f"分类合计 {classified} 与实测文件数 {stats.total_files} 对不上"
        )
    render_cover(args.out, table, files_label, size_label)
    render_catalog(args.out, table, files_label, size_label)
    render_outcomes(args.out, table, files_label, size_label)
    render_guide(args.out, table, files_label, size_label)
    require_valid_pngs(args.out, size=(W, H))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
