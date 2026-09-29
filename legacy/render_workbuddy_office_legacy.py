from PIL import Image, ImageDraw, ImageFont
import os
import pathlib
from xianyu_common import assert_text_above, chip_positions, stack_layout, wrap_text_fit

W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)

# 课程规模来自 verify_source.py 对源目录的实测结果（38 个视频，去重后 37 集）。
LESSONS = int(os.environ.get("XIANYU_WORKBUDDY_OFFICE_LESSONS", "37"))
MODULES = 11
LESSON_SHORT = f"{LESSONS}集"
LESSON_FULL = f"{LESSONS}课时"
LESSON_BADGE = f"{LESSONS}节"
MODULES_LABEL = f"{MODULES}大模块"


def get_font(size, bold=False):
    path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        raise RuntimeError(f"无法加载字体：{path}") from None


def draw_board():
    im = Image.new("RGB", (W, H), BLUE)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle([BORDER, BORDER, W - BORDER, H - BORDER], radius=32, fill="white")
    return im, draw


out = pathlib.Path(
    os.environ.get(
        "XIANYU_LEGACY_OUT",
        "D:/闲鱼/小白从零上手WorkBuddy，AI办公新范式实战，全自动提高效率",
    )
)
out.mkdir(parents=True, exist_ok=True)

# --- 01 Cover ---
FOOTER_H = 86
FOOTER_TOP = H - BORDER - FOOTER_H
TAG_GAP = 36
FEATURE_ICON_H = 76
FEATURE_TITLE_H = 46
FEATURE_SUB_H = 44
FEATURE_DETAIL_LINES = 3
FEATURE_DETAIL_H = 30
FEATURE_CONTENT_H = (
    FEATURE_ICON_H
    + FEATURE_TITLE_H
    + FEATURE_SUB_H
    + 26
    + 1
    + 24
    + FEATURE_DETAIL_H * FEATURE_DETAIL_LINES
)


def features_layout(count: int, top: int) -> tuple[int, int]:
    base_h = 318
    tops, sizes = stack_layout([base_h], top, FOOTER_TOP - TAG_GAP)
    card_h = int(sizes[0])
    if card_h < base_h:
        raise ValueError(f"封面特色卡高度 {card_h} 小于基准 {base_h}，布局计算有误")
    return tops[0], card_h


im, draw = draw_board()

badge_font = get_font(26, bold=True)
badge_text = f"{LESSON_SHORT}全 办公提效"
bw = draw.textlength(badge_text, font=badge_font) + 40
bh = 42
bx = (W - bw) // 2
by = BORDER + 36
draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=21, fill=BLUE)
draw.text(
    (bx + (bw - draw.textlength(badge_text, font=badge_font)) // 2, by + 9),
    badge_text,
    fill="white",
    font=badge_font,
)

title = "WorkBuddy办公新范式"
subtitle = "零上手全自动提效"
tfont = get_font(58, bold=True)
sfont = get_font(34)
tw = draw.textlength(title, font=tfont)
draw.text(((W - tw) // 2, by + bh + 46), title, fill=DARK, font=tfont)
sw = draw.textlength(subtitle, font=sfont)
draw.text(((W - sw) // 2, by + bh + 46 + 78), subtitle, fill=GRAY, font=sfont)
rule_y = by + bh + 46 + 78 + 52
draw.line([(W - 200) // 2, rule_y, (W + 200) // 2, rule_y], fill=BLUE, width=4)

# 导语填在副标题和特色卡之间。早先这块留了 170px 空白，扫描器判为死区：
# 拉高卡片只会把空洞挪进卡内，正确做法是补内容。
pitch_font = get_font(25)
pitch_lines = wrap_text_fit(
    "从安装到定时简报周报自动推送，文件文档数据全流程跟练",
    pitch_font,
    W - 2 * BORDER - 200,
    2,
    draw,
    label="封面导语",
)
pitch_line_h = 40
pitch_top = rule_y + 46
for line_index, line in enumerate(pitch_lines):
    line_w = draw.textlength(line, font=pitch_font)
    draw.text(
        ((W - line_w) // 2, pitch_top + line_index * pitch_line_h),
        line,
        fill=(71, 85, 105),
        font=pitch_font,
    )
pitch_bottom = pitch_top + len(pitch_lines) * pitch_line_h

features = [
    ("零基础上手", "安装模式任务管理", "从下载安装到派第一个任务"),
    ("办公全流程", "文件文档数据分析", "提取归档发票清洗报告成稿"),
    ("自动化提效", "定时简报周报推送", "每天早上情报自己送到手"),
]
feat_top, feat_h = features_layout(len(features), pitch_bottom + 40)
feat_font = get_font(31, bold=True)
feat_sub = get_font(20)
detail_font = get_font(19)
feat_w = (W - 2 * BORDER - 120 - 2 * 24) // 3
for i, (a, b, c) in enumerate(features):
    x = BORDER + 60 + i * (feat_w + 24)
    draw.rounded_rectangle(
        [x, feat_top, x + feat_w, feat_top + feat_h],
        radius=20,
        fill=(248, 250, 252),
        outline=(226, 232, 240),
        width=2,
    )
    inner_y = feat_top + (feat_h - FEATURE_CONTENT_H) // 2
    cx = x + feat_w // 2
    cy = inner_y + FEATURE_ICON_H // 2
    draw.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=(239, 246, 255), outline=BLUE, width=2)
    icon_font = get_font(32, bold=True)
    iw = draw.textlength(str(i + 1), font=icon_font)
    draw.text((cx - iw // 2, cy - 19), str(i + 1), fill=BLUE, font=icon_font)
    text_left = x + 20
    text_right = x + feat_w - 20
    aw = draw.textlength(a, font=feat_font)
    title_y = cy + 44
    ax = max(text_left, min(text_right - aw, cx - aw // 2))
    draw.text((ax, title_y), a, fill=DARK, font=feat_font)
    lines2 = wrap_text_fit(b, feat_sub, text_right - text_left, 2, draw, label=f"封面特色 {a}")
    sub_top = title_y + 44
    detail_y = sub_top + len(lines2) * 30
    assert_text_above(draw, lines2[-1], feat_sub, sub_top + (len(lines2) - 1) * 30, detail_y, f"封面特色 {a}")
    for line_index, line in enumerate(lines2):
        line_w = draw.textlength(line, font=feat_sub)
        draw.text(
            (max(text_left, min(text_right - line_w, cx - line_w // 2)), sub_top + line_index * 30),
            line,
            fill=GRAY,
            font=feat_sub,
        )
    rule_y = detail_y + 10
    draw.line([(text_left, rule_y), (text_right, rule_y)], fill=(203, 213, 225), width=1)
    detail_lines = wrap_text_fit(c, detail_font, text_right - text_left, FEATURE_DETAIL_LINES, draw, label=f"封面特色细节 {a}")
    detail_top = rule_y + 24
    assert_text_above(
        draw,
        detail_lines[-1],
        detail_font,
        detail_top + (len(detail_lines) - 1) * FEATURE_DETAIL_H,
        feat_top + feat_h - 14,
        f"封面特色细节 {a}",
    )
    for line_index, line in enumerate(detail_lines):
        draw.text((text_left, detail_top + line_index * FEATURE_DETAIL_H), line, fill=(71, 85, 105), font=detail_font)

draw.rounded_rectangle([BORDER, H - BORDER - FOOTER_H, W - BORDER, H - BORDER], radius=22, fill=DARK)
draw.text((BORDER + 40, H - BORDER - FOOTER_H + 18), "只发夸克", fill="white", font=get_font(24, bold=True))
bar_text2 = "虚拟资料 · 拍后发网盘链接 · 无需物流"
draw.text(
    (W - BORDER - 40 - draw.textlength(bar_text2, font=get_font(22)), H - BORDER - FOOTER_H + 48),
    bar_text2,
    fill=(203, 213, 225),
    font=get_font(22),
)
draw.text(
    (BORDER + 40, FOOTER_TOP - TAG_GAP + 8),
    f"WorkBuddy · {LESSON_FULL} · 办公提效 · 即学即用",
    fill=GRAY,
    font=get_font(22),
)

im.save(out / "01.png", "PNG")
print("01 saved", (out / "01.png").stat().st_size)

# --- 02 Catalog ---
im, draw = draw_board()
title_font = get_font(44, bold=True)
sub_font = get_font(24)
draw.text((BORDER + 40, BORDER + 28), "课程目录", fill=DARK, font=title_font)
draw.text((BORDER + 40, BORDER + 28 + 56), f"{LESSON_FULL} · {MODULES_LABEL} · 从安装到自动化闭环", fill=GRAY, font=sub_font)

bf2 = get_font(26, bold=True)
bw2 = draw.textlength(LESSON_BADGE, font=bf2) + 30
draw.rounded_rectangle([W - BORDER - 40 - bw2, BORDER + 36, W - BORDER - 40, BORDER + 36 + 36], radius=18, fill=(239, 246, 255))
draw.text((W - BORDER - 40 - bw2 + 15, BORDER + 42), LESSON_BADGE, fill=BLUE, font=bf2)

mods = [
    ("模块1 认识", "1-2", ["AI办公新范式", "与传统工具区别", "技术架构与套餐", "适用人群"], BLUE),
    ("模块2 快速上手", "3-4", ["安装WorkBuddy", "几种工作模式", "派第一个任务", "任务管理"], (124, 58, 237)),
    ("模块3 Claw远程", "5-6", ["远程控制原理", "模式与接入配置", "手机端使用技巧", "实战用例"], (14, 165, 233)),
    ("模块4 提示词", "7-8", ["高质量模板", "常见错误", "编写方法", "实战套用"], (16, 185, 129)),
    ("模块5 文件处理", "9-13", ["批量提取信息", "归档重命名", "数据清洗合并", "识别发票/转换"], (249, 115, 22)),
    ("模块6 文档生成", "14-18", ["结构化报告", "会议纪要整理", "从零生成方案", "模板标准化"], (225, 29, 72)),
    ("模块7 数据分析", "19-23", ["销售数据分析", "财务数据分析", "运营数据分析", "问卷分析"], (13, 148, 136)),
    ("模块8 自动化", "24-26", ["每天定时AI简报", "每周自动周报", "定时竞品分析"], (190, 24, 93)),
    ("模块9 高效技巧", "27-29", ["养虾技巧01-03", "养虾技巧04-07", "养虾技巧08-10"], (147, 51, 234)),
    ("模块10 Skill精选", "30-35", ["办公文档套件", "录音转文字", "视频下载", "网页检索"], (2, 132, 199)),
    ("模块11 专家中心", f"36-{LESSONS}", ["专家就干专业的活", "专业案例", "课程总结"], (180, 83, 9)),
]

CAT_COLS = 3
CAT_ROWS = 4
CAT_GAP = 18
CAT_TOP = BORDER + 126
CAT_FOOT = H - BORDER - 86 - 16
card_w = (W - 2 * BORDER - 80 - CAT_GAP) // CAT_COLS
max_items = max(len(m[2]) for m in mods)
card_h = (CAT_FOOT - CAT_TOP - (CAT_ROWS - 1) * CAT_GAP) // CAT_ROWS
item_pitch = (card_h - 48 - 14) // max_items
if item_pitch < 20:
    raise ValueError("课程目录行距过小，版式无法容纳")
if max_items > 4:
    raise ValueError("3 列 × 4 行版式每个模块最多 4 条，超出请改成 2 列布局")
for idx, (mtitle, mrange, items, color) in enumerate(mods):
    col = idx % CAT_COLS
    row = idx // CAT_COLS
    x = BORDER + 40 + col * (card_w + CAT_GAP)
    y = CAT_TOP + row * (card_h + CAT_GAP)
    draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    draw.rounded_rectangle([x, y, x + card_w, y + 5], radius=5, fill=color)
    tf = get_font(21, bold=True)
    draw.text((x + 13, y + 15), mtitle, fill=DARK, font=tf)
    rf = get_font(17, bold=True)
    rw = draw.textlength(mrange, font=rf)
    draw.rounded_rectangle([x + card_w - 13 - rw - 12, y + 15, x + card_w - 13, y + 15 + 21], radius=10, fill=color)
    draw.text((x + card_w - 13 - rw - 6, y + 16), mrange, fill="white", font=rf)
    it_font = get_font(17)
    iy = y + 48
    for it in items:
        draw.ellipse([x + 13, iy + 6, x + 19, iy + 12], fill=color)
        text = "· " + it
        while draw.textlength(text, font=it_font) > card_w - 39 and it_font.size > 12:
            it_font = get_font(it_font.size - 1)
        draw.text((x + 25, iy), text, fill=(51, 65, 85), font=it_font)
        iy += item_pitch

draw.rounded_rectangle([BORDER, H - BORDER - 86, W - BORDER, H - BORDER], radius=22, fill=DARK)
draw.text((BORDER + 40, H - BORDER - 68), "只发夸克", fill="white", font=get_font(24, bold=True))
tail = "虚拟资料 · 拍后发网盘链接 · 整理即用"
draw.text((W - BORDER - 40 - draw.textlength(tail, font=get_font(22)), H - BORDER - 36), tail, fill=(203, 213, 225), font=get_font(22))

im.save(out / "02.png", "PNG")
print("02 saved", (out / "02.png").stat().st_size)

# --- 03 Harvest ---
im, draw = draw_board()
points = [
    ("安装与模式", "装好WorkBuddy搞懂工作模式"),
    ("远程控制", "Claw接入手机随时指挥"),
    ("提示词", "模板与纠错写出好指令"),
    ("文件处理", "提取归档清洗发票识别"),
    ("文档生成", "报告纪要方案邮件成稿"),
    ("数据分析", "销售财务运营可视化"),
    ("自动化任务", "简报周报竞品定时推送"),
    ("Skill精选", "文档转写下载网页检索"),
    ("专家中心", "专家干专业的活"),
]
draw.text((BORDER + 40, BORDER + 28), "你将获得", fill=DARK, font=title_font)
draw.text((BORDER + 40, BORDER + 28 + 56), f"从零上手到自动化，{len(points)}项能力一次打通", fill=GRAY, font=sub_font)

PT_COLS = 3
PT_ROWS = 3
PT_TOP = BORDER + 126
PT_FOOT = H - BORDER - 86 - 132 - 16
PT_PAD = 20
PT_GAP_MAX = 44
PT_GAP = 22
pt_desc_font = get_font(16)
max_block = 40 + 2 * 21
pt_h = max_block + PT_PAD * 2
# 行距吃满剩余高度。早先固定 22px 再垂直居中，卡片整块浮在上方，
# 卡片底边到"适合谁"之间空出一大片，视觉上像是内容没排完。
slack = PT_FOOT - PT_TOP - PT_ROWS * pt_h
if slack < 0:
    raise ValueError("收获卡片没有可用高度")
PT_GAP = min(PT_GAP_MAX, slack // (PT_ROWS - 1))
pt_top = PT_TOP + (slack - (PT_ROWS - 1) * PT_GAP) // 2
# 列宽必须在 PT_GAP 定稿之后再算。早先用占位 22px 算列宽，
# 随后把行距撑到 44px，x + pt_w + col*PT_GAP 就越过右边界了。
pt_w = (W - 2 * BORDER - 80 - 2 * PT_GAP) // PT_COLS
pt_lines = {t: wrap_text_fit(d, pt_desc_font, pt_w - 30, 2, draw, label=f"收获 {t}") for t, d in points}
for i, (ptitle, pdesc) in enumerate(points):
    col = i % PT_COLS
    row = i // PT_COLS
    x = BORDER + 40 + col * (pt_w + PT_GAP)
    yy = pt_top + row * (pt_h + PT_GAP)
    draw.rounded_rectangle([x, yy, x + pt_w, yy + pt_h], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    lines = pt_lines[ptitle]
    block_h = 40 + len(lines) * 21
    oy = yy + (pt_h - block_h) // 2
    num_font = get_font(19, bold=True)
    draw.rounded_rectangle([x + 13, oy, x + 13 + 26, oy + 26], radius=13, fill=BLUE)
    draw.text((x + 13 + 7, oy + 1), str(i + 1), fill="white", font=num_font)
    draw.text((x + 13 + 36, oy + 1), ptitle, fill=DARK, font=get_font(21, bold=True))
    dy = oy + 40
    for l in lines[:2]:
        draw.text((x + 13, dy), l, fill=GRAY, font=pt_desc_font)
        dy += 21

draw.rounded_rectangle([BORDER + 40, H - BORDER - 86 - 132, W - BORDER - 40, H - BORDER - 86 - 16], radius=16, fill=(239, 246, 255))
draw.text((BORDER + 60, H - BORDER - 86 - 112), "适合谁", fill=DARK, font=get_font(22, bold=True))
scenes = ["职场办公党", "行政财务", "运营新媒体", "想用AI提效的人"]
sf = get_font(20)
for s, sx, w in chip_positions(draw, scenes, font=sf, left=BORDER + 60, right=W - BORDER - 60, label="03 页适合谁"):
    draw.rounded_rectangle([sx, H - BORDER - 86 - 76, sx + w, H - BORDER - 86 - 46], radius=13, fill="white", outline=BLUE, width=1)
    draw.text((sx + 13, H - BORDER - 86 - 72), s, fill=BLUE, font=sf)

draw.rounded_rectangle([BORDER, H - BORDER - 86, W - BORDER, H - BORDER], radius=22, fill=DARK)
draw.text((BORDER + 40, H - BORDER - 68), "只发夸克", fill="white", font=get_font(24, bold=True))
tail2 = "虚拟资料 · 无需物流 · 即学即用"
draw.text((W - BORDER - 40 - draw.textlength(tail2, font=get_font(22)), H - BORDER - 36), tail2, fill=(203, 213, 225), font=get_font(22))

im.save(out / "03.png", "PNG")
print("03 saved", (out / "03.png").stat().st_size)

# --- 04 Guide ---
im, draw = draw_board()
draw.text((BORDER + 40, BORDER + 28), "发货指南", fill=DARK, font=title_font)
draw.text((BORDER + 40, BORDER + 28 + 56), "虚拟资料 · 只发夸克网盘 · 不发百度/实物", fill=GRAY, font=sub_font)
steps = [
    ("1", "拍后提供链接", "下单后发送夸克网盘链接与提取码"),
    ("2", "不限时·需提取码", "带文件名，永久有效，反复下载"),
    ("3", "即学即用", f"{LESSONS}个实战视频，按顺序跟练即可"),
    ("4", "售后说明", "虚拟资料不包变现承诺，按需拍"),
]
STEP_TOP = BORDER + 126
STEP_GAP = 18
STEP_H = (H - BORDER - 86 - 40 - 86 - 16 - STEP_TOP - (len(steps) - 1) * STEP_GAP) // len(steps)
if STEP_H < 104:
    raise ValueError("发货指南卡片高度不足以容纳两行文字")
yy = STEP_TOP
for num, ttitle, tdesc in steps:
    draw.rounded_rectangle([BORDER + 40, yy, W - BORDER - 40, yy + STEP_H], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    num_cy = yy + (STEP_H - 46) // 2
    draw.ellipse([BORDER + 60, num_cy, BORDER + 60 + 46, num_cy + 46], fill=BLUE)
    nf = get_font(27, bold=True)
    tw = draw.textlength(num, font=nf)
    draw.text((BORDER + 60 + 23 - tw // 2, num_cy + 5), num, fill="white", font=nf)
    ty = yy + (STEP_H - 34 - 28) // 2
    draw.text((BORDER + 126, ty), ttitle, fill=DARK, font=get_font(25, bold=True))
    draw.text((BORDER + 126, ty + 34), tdesc, fill=GRAY, font=get_font(21))
    if num != "4":
        draw.text((W - BORDER - 90, num_cy + 1), "→", fill=(226, 232, 240), font=get_font(27))
    yy += STEP_H + STEP_GAP

warn_y = yy + 8
draw.rounded_rectangle([BORDER + 40, warn_y, W - BORDER - 40, warn_y + 80], radius=14, fill=(255, 251, 235), outline=(253, 230, 138), width=1)
draw.text((BORDER + 60, warn_y + 10), "提醒", fill=(146, 64, 14), font=get_font(21, bold=True))
wf = get_font(16)
warn_text = "虚拟资料一经发货不退不换，请确认需要WorkBuddy办公提效再拍"
for idx, wl in enumerate(wrap_text_fit(warn_text, wf, W - 2 * BORDER - 120, 2, draw, label="提醒")):
    draw.text((BORDER + 60, warn_y + 40 + idx * 20), wl, fill=(120, 113, 108), font=wf)

BAR_TOP = H - BORDER - 86
draw.rounded_rectangle([BORDER, BAR_TOP, W - BORDER, H - BORDER], radius=22, fill=DARK)
draw.text((BORDER + 40, BAR_TOP + 12), "只发夸克网盘", fill="white", font=get_font(24, bold=True))
draw.text((BORDER + 40, BAR_TOP + 48), "不发百度 · 不发实物 · 不包变现", fill=(203, 213, 225), font=get_font(18))

im.save(out / "04.png", "PNG")
print("04 saved", (out / "04.png").stat().st_size)
print("done", out)
