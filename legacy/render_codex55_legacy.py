from PIL import Image, ImageDraw, ImageFont
import os
import pathlib

from xianyu_common import assert_text_above, stack_layout, wrap_text_fit

W=H=1080
BORDER=38
BLUE=(47,93,255)
DARK=(30,41,59)
GRAY=(100,116,139)
LIGHT_BG=(248,250,252)

# 课时数集中声明，改数量只改这里；找不到源目录时可用环境变量覆盖。
LESSONS = int(os.environ.get("XIANYU_CODEX_LESSONS", "55"))
MODULES = 6
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
    im = Image.new("RGB", (W,H), BLUE)
    draw = ImageDraw.Draw(im)
    # inner white rounded
    radius=32
    draw.rounded_rectangle([BORDER, BORDER, W-BORDER, H-BORDER], radius=radius, fill="white")
    return im, draw

def wrap_text(text, font, max_w, draw):
    # simple wrap
    chars=[]
    line=""
    for ch in text:
        test=line+ch
        w=draw.textlength(test, font=font)
        if w>max_w:
            chars.append(line)
            line=ch
        else:
            line=test
    if line:
        chars.append(line)
    return chars

out = pathlib.Path(
    os.environ.get(
        "XIANYU_LEGACY_OUT",
        r"D:\闲鱼\Codex职场高效办公实战，AI自动化赋能日常办公",
    )
)
out.mkdir(parents=True, exist_ok=True)

# --- 01 Cover ---
# 封面下半部分的常量：特色卡可伸展区域，以及卡片自身的留白。
FEATURE_TOP = 330
FOOTER_H = 86
FOOTER_TOP = H - BORDER - FOOTER_H
TAG_GAP = 36
FEATURE_CARD_PAD = 28

def features_layout(count: int) -> tuple[int, int]:
    """返回封面特色卡的 (顶部 y, 单卡高度)。

    早先特色块的 y 和高度都写死：内容在 540px 就结束，底部标语在 920px，
    中间留下约 380px 死区，封面看起来头重脚轻。

    光把卡片拉高填满是没用的（试过：卡片长到 460px 而内容只有 180px，
    底部又空出一片，反而更难看）。真正的解法是往卡里补实质内容 ——
    每张卡加一段"跟着课能做出什么"的细节，封面信息量上去了，留白自然
    变成内容间距。卡片高度贴合内容（不拉伸），剩余空间由 stack_layout
    均分到上下各约 117px。

    注意 stack_layout 返回 ``(tops, sizes)``，sizes[0] 才是特色卡高度。
    """
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("count must be a positive integer")
    base_h = 318
    tops, sizes = stack_layout(
        [base_h],
        FEATURE_TOP,
        FOOTER_TOP - TAG_GAP,
    )
    card_h = int(sizes[0])
    if card_h < base_h:
        raise ValueError(f"封面特色卡高度 {card_h} 小于基准 {base_h}，布局计算有误")
    return tops[0], card_h

# 卡内内容（图标 + 标题 + 副标题 + 细节）的高度，用于在卡里垂直居中
FEATURE_ICON_H = 76
FEATURE_TITLE_H = 46
FEATURE_SUB_H = 44
FEATURE_DETAIL_LINES = 3
FEATURE_DETAIL_H = 30
FEATURE_CONTENT_H = (
    FEATURE_ICON_H + FEATURE_TITLE_H + FEATURE_SUB_H
    + 26 + 1 + 24 + FEATURE_DETAIL_H * FEATURE_DETAIL_LINES
)

im, draw = draw_board()
# top badge
badge_font=get_font(26, bold=True)
badge_text=f"{LESSON_SHORT}全  多场景实战"
# badge bg
bw = draw.textlength(badge_text, font=badge_font)+40
bh=42
bx=(W-bw)//2
by=BORDER+36
draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=21, fill=BLUE)
draw.text((bx+(bw-draw.textlength(badge_text, font=badge_font))//2, by+9), badge_text, fill="white", font=badge_font)
# title
title="Codex职场高效办公实战"
subtitle="AI自动化赋能日常办公"
tfont=get_font(66, bold=True)
sfont=get_font(36, bold=False)
# center title
tw=draw.textlength(title, font=tfont)
draw.text(((W-tw)//2, by+bh+46), title, fill=DARK, font=tfont)
sw=draw.textlength(subtitle, font=sfont)
draw.text(((W-sw)//2, by+bh+46+82), subtitle, fill=GRAY, font=sfont)
# divider
draw.line([(W-200)//2, by+bh+46+82+56, (W+200)//2, by+bh+46+82+56], fill=BLUE, width=4)
# features 3 points
feat_font=get_font(31, bold=True)
feat_sub=get_font(20)
features=[
    (
        "多模型一站式",
        "国产/第三方/API自由切换",
        "DeepSeek / 智谱 / 通义 随用随切",
    ),
    (
        "音视频全覆盖",
        "图片·视频·语音·剪辑",
        "生图、生视频、配音、剪辑一条龙",
    ),
    (
        "飞书+知识库",
        "自动化办公到企业沉淀",
        "多维表格、云文档、知识库沉淀",
    ),
]
feat_top, feat_h = features_layout(len(features))
slot_w = (W - 2 * BORDER - 120) // 3
for i,(a,b,c) in enumerate(features):
    x = BORDER+60 + i*slot_w
    # 卡片底：让整块特色有实体边框，避免大片纯白死区
    card_x = x - 8
    card_w = slot_w - 8
    draw.rounded_rectangle(
        [card_x, feat_top, card_x + card_w, feat_top + feat_h],
        radius=20,
        fill=(248, 250, 252),
        outline=(226, 232, 240),
        width=2,
    )
    # 卡内垂直居中：内容整体居中，不贴卡片顶部
    inner_y = feat_top + (feat_h - FEATURE_CONTENT_H) // 2
    # icon circle
    cx=x+70
    cy=inner_y+FEATURE_ICON_H//2
    draw.ellipse([cx-38, cy-38, cx+38, cy+38], fill=(239,246,255), outline=BLUE, width=2)
    icon_font=get_font(32, bold=True)
    # msyh 字体里没有 ◉ 和 ▣ 的字形，早先渲染成两个豆腐块（□），
    # 中间的 ◆ 反而正常。这里只挑实测存在的字形：● ◆ ▲。
    icons=["●","◆","▲"]
    iw=draw.textlength(icons[i], font=icon_font)
    draw.text((cx-iw//2, cy-19), icons[i], fill=BLUE, font=icon_font)
    # text
    aw=draw.textlength(a, font=feat_font)
    ax= max(x-8+20, min(x-8+slot_w-8-20-aw, x+70 - aw//2))
    title_y=cy+44
    draw.text((ax, title_y), a, fill=DARK, font=feat_font)
    # 文字一律按卡片自身内边距裁剪，不能按画布边界：
    # 居中后向左溢出时会跑到卡片边框外面。
    text_left = card_x + 20
    text_right = card_x + card_w - 20
    sub_w = text_right - text_left
    lines2=wrap_text_fit(b, feat_sub, sub_w, 2, draw, label=f"封面特色 {a}")
    sub_top=title_y+44
    detail_y=sub_top+len(lines2)*30
    assert_text_above(
        draw, lines2[-1], feat_sub, sub_top + (len(lines2) - 1) * 30,
        detail_y, f"封面特色 {a}",
    )
    for line_index, line in enumerate(lines2):
        line_w=draw.textlength(line, font=feat_sub)
        line_x= max(text_left, min(text_right - line_w, x+70 - line_w//2))
        draw.text((line_x, sub_top+line_index*30), line, fill=GRAY, font=feat_sub)
    # 细分割线 + 细节说明：把"跟着课能做出什么"写清楚，填满卡片
    rule_y=detail_y+10
    draw.line(
        [(text_left, rule_y), (text_right, rule_y)],
        fill=(203,213,225), width=1,
    )
    detail_font=get_font(19)
    detail_lines=wrap_text_fit(
        c, detail_font, sub_w, FEATURE_DETAIL_LINES,
        draw, label=f"封面特色细节 {a}",
    )
    detail_top=rule_y+24
    assert_text_above(
        draw, detail_lines[-1], detail_font,
        detail_top + (len(detail_lines) - 1) * FEATURE_DETAIL_H,
        feat_top + feat_h - FEATURE_CARD_PAD // 2, f"封面特色细节 {a}",
    )
    for line_index, line in enumerate(detail_lines):
        draw.text(
            (text_left, detail_top + line_index * FEATURE_DETAIL_H),
            line, fill=(71,85,105), font=detail_font,
        )

# bottom bar
bar_h=FOOTER_H
draw.rounded_rectangle([BORDER, H-BORDER-bar_h, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
bar_font=get_font(24, bold=True)
bar_font2=get_font(22)
bar_text="只发夸克"
bar_text2="虚拟资料 · 拍后发网盘链接 · 无需物流"
draw.text((BORDER+40, H-BORDER-bar_h+18), bar_text, fill="white", font=bar_font)
# second line centered? put right
w2=draw.textlength(bar_text2, font=bar_font2)
draw.text((W-BORDER-40-w2, H-BORDER-bar_h+48), bar_text2, fill=(203,213,225), font=bar_font2)
# bottom tag
tag_font=get_font(20)
tag=f"Codex · {LESSON_FULL} · 办公自动化"
tw3=draw.textlength(tag, font=tag_font)
draw.text(((W-tw3)//2, H-BORDER-34), tag, fill=(148,163,184), font=tag_font) if False else None
# actually draw inside white area
draw.text((BORDER+40, FOOTER_TOP-TAG_GAP+8), f"Codex · {LESSON_FULL} · 办公自动化 · 即学即用", fill=GRAY, font=get_font(22))

im.save(out/"01.png", "PNG")
print("01 saved", (out/"01.png").stat().st_size)

# --- 02 Catalog ---
im, draw = draw_board()
title_font=get_font(44, bold=True)
draw.text((BORDER+40, BORDER+28), "课程目录", fill=DARK, font=title_font)
sub_font=get_font(24)
draw.text((BORDER+40, BORDER+28+56), f"{LESSON_FULL} · {MODULES_LABEL} · 办公全场景覆盖", fill=GRAY, font=sub_font)
# badge right
badge2=LESSON_BADGE
bf2=get_font(26, bold=True)
bw2=draw.textlength(badge2, font=bf2)+30
draw.rounded_rectangle([W-BORDER-40-bw2, BORDER+36, W-BORDER-40, BORDER+36+36], radius=18, fill=(239,246,255))
draw.text((W-BORDER-40-bw2+15, BORDER+42), badge2, fill=BLUE, font=bf2)

# modules 6 cards 2 columns x 3 rows
mods=[
    ("模块1 基础入门", "1-5", ["课程介绍","软件安装/登录","CCSwitch切国产模型","切第三方模型","配置模型生图/音视频"], BLUE),
    ("模块2 模型实战", "6-10", ["gpt-image2生图","Seedream生图","Seedance生视频","豆包生语音","edge文本转语音"], (124,58,237)),
    ("模块3 办公提效", "11-16", ["快速上手","批量整理文件","智能分析数据","撰写商业文档","市场调研洞察","实战经验总结"], (14,165,233)),
    ("模块4 行业报表", "17-26", ["行业数据分析","电商周报/年报","降本增效洞察","研发周报/年报","多行业PPT","研发/机器人/电商PPT"], (16,185,129)),
    ("模块5 视频与电商", "27-41", ["自动化剪辑","字幕/音乐/切片","文稿生成视频/特效","产品套图流水线","带货视频/宣传视频","数字人多角度/口播"], (249,115,22)),
    # 末个模块的结束课时必须跟 LESSONS 走，否则改数量后目录止于旧数字，
    # 和封面徽章、正文的"55个实战视频"对不上。
    ("模块6 飞书与知识库", f"42-{LESSONS}", ["飞书多场景办公","安装/上手CLI","云文档/会议/表格","管理项目任务","Obsidian知识库","资讯归档/Skill/PPT"], (225,29,72)),
]
CAT_COLS=2
CAT_ROWS=3
CAT_GAP=24
CAT_TOP=BORDER+130
# 末行卡片与底栏之间留出 20px 呼吸空间，否则卡片底边几乎贴着深色底栏
CAT_FOOT=H-BORDER-86-20
card_w=(W-2*BORDER-80-CAT_GAP)//CAT_COLS
max_items=max(len(m[2]) for m in mods)
# 卡片高度由可用高度反推，再让行距吃掉剩余空间，避免大片空白
card_h=(CAT_FOOT-CAT_TOP-(CAT_ROWS-1)*CAT_GAP)//CAT_ROWS
item_pitch=(card_h-52-18)//max_items
start_y=CAT_TOP
gap=CAT_GAP
if item_pitch < 22:
    raise ValueError("课程目录行距过小，版式无法容纳")
for idx, (mtitle, mrange, items, color) in enumerate(mods):
    col=idx%CAT_COLS
    row=idx//CAT_COLS
    x=BORDER+40+col*(card_w+gap)
    y=start_y+row*(card_h+gap)
    # card bg
    draw.rounded_rectangle([x, y, x+card_w, y+card_h], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # top line color
    draw.rounded_rectangle([x, y, x+card_w, y+6], radius=6, fill=color)
    # title
    tf=get_font(22, bold=True)
    draw.text((x+14, y+18), mtitle, fill=DARK, font=tf)
    rf=get_font(18, bold=True)
    rw=draw.textlength(mrange, font=rf)
    draw.rounded_rectangle([x+card_w-14-rw-14, y+18, x+card_w-14, y+18+22], radius=11, fill=color)
    draw.text((x+card_w-14-rw-7, y+19), mrange, fill="white", font=rf)
    # items
    it_font=get_font(20)
    iy=y+52
    for it in items:
        # bullet
        draw.ellipse([x+14, iy+7, x+14+6, iy+7+6], fill=color)
        draw.text((x+26, iy), "· "+it, fill=(51,65,85), font=it_font)
        iy+=item_pitch

# bottom bar
draw.rounded_rectangle([BORDER, H-BORDER-86, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, H-BORDER-68), "只发夸克", fill="white", font=get_font(24, bold=True))
draw.text((W-BORDER-40-draw.textlength("虚拟资料 · 拍后发网盘链接 · 整理即用", font=get_font(22)), H-BORDER-36), "虚拟资料 · 拍后发网盘链接 · 整理即用", fill=(203,213,225), font=get_font(22))

im.save(out/"02.png", "PNG")
print("02 saved", (out/"02.png").stat().st_size)

# --- 03 Harvest ---
im, draw = draw_board()
# 步骤数从列表长度派生，早先手写"6步"，增删条目后副标题会与实际不符
points=[
    ("一站式模型调度", "国产/第三方/API，CCSwitch自由切，适配图片/音视频"),
    ("办公文档自动化", "商业文档·市场调研·智能数据分析·经验总结"),
    ("行业报表与PPT", "电商周报/年报·研发交付·人形机器人调研·高质量PPT"),
    ("视频与电商流水线", "自动剪辑·批量字幕·切片混剪·产品套图·数字人带货"),
    ("飞书深度集成", "云文档·智能约会·多维表·项目任务全自动"),
    ("企业知识库闭环", "Obsidian+Codex+Skill，白板知识地图与资讯归档"),
]
draw.text((BORDER+40, BORDER+28), "你将获得", fill=DARK, font=title_font)
draw.text((BORDER+40, BORDER+28+56), f"从入门到实战，{len(points)}步打通职场自动化", fill=GRAY, font=sub_font)
y=start_y
PT_COLS=2
PT_ROWS=3
# 副标题在 BORDER+84 处，24 号字高约 33，卡片必须从它下方开始
PT_TOP=BORDER+170
SUIT_TOP=H-BORDER-86-140
PT_FOOT=SUIT_TOP-20
PT_PAD=22
PT_GAP_MAX=56
PT_GAP=20
pt_w=(W-2*BORDER-80-PT_GAP)//PT_COLS
pt_desc_font=get_font(16)
pt_lines={t:wrap_text_fit(d, pt_desc_font, pt_w-32, 2, draw, label=f"收获 {t}") for t,d in points}
max_block=max(44+len(v)*22 for v in pt_lines.values())
PT_H=max_block+PT_PAD*2
PT_GAP=min(PT_GAP_MAX, (PT_FOOT-PT_TOP-PT_ROWS*PT_H)//(PT_ROWS-1))
if PT_GAP < 16:
    raise ValueError("收获卡片与适合谁区块重叠")
# 间距封顶后整块垂直居中，避免底部堆积空白
pt_top=PT_TOP+(PT_FOOT-PT_TOP-(PT_ROWS*PT_H+(PT_ROWS-1)*PT_GAP))//2
for i,(ptitle, pdesc) in enumerate(points):
    col=i%PT_COLS
    row=i//PT_COLS
    x=BORDER+40+col*(pt_w+PT_GAP)
    yy=pt_top+row*(PT_H+PT_GAP)
    draw.rounded_rectangle([x, yy, x+pt_w, yy+PT_H], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    lines=pt_lines[ptitle]
    oy=yy+PT_PAD
    # number
    num_font=get_font(20, bold=True)
    draw.rounded_rectangle([x+14, oy, x+14+28, oy+28], radius=14, fill=BLUE)
    draw.text((x+14+8, oy+2), str(i+1), fill="white", font=num_font)
    draw.text((x+14+40, oy+2), ptitle, fill=DARK, font=get_font(22, bold=True))
    # desc wrap
    dy=oy+44
    for l in lines[:2]:
        draw.text((x+14, dy), l, fill=GRAY, font=pt_desc_font)
        dy+=22

# suitable scenes bottom
draw.rounded_rectangle([BORDER+40, H-BORDER-86-140, W-BORDER-40, H-BORDER-86-20], radius=18, fill=(239,246,255))
st_font=get_font(22, bold=True)
draw.text((BORDER+60, H-BORDER-86-120), "适合谁", fill=DARK, font=st_font)
scenes=["职场办公党","运营/产品/研发","电商/视频创作者","想用AI提效的所有人"]
sf=get_font(20)
sx=BORDER+60
for s in scenes:
    w=draw.textlength(s, font=sf)+28
    draw.rounded_rectangle([sx, H-BORDER-86-82, sx+w, H-BORDER-86-52], radius=14, fill="white", outline=BLUE, width=1)
    draw.text((sx+14, H-BORDER-86-78), s, fill=BLUE, font=sf)
    sx+=w+14

draw.rounded_rectangle([BORDER, H-BORDER-86, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, H-BORDER-68), "只发夸克", fill="white", font=get_font(24, bold=True))
draw.text((W-BORDER-40-draw.textlength("虚拟资料 · 无需物流 · 即学即用", font=get_font(22)), H-BORDER-36), "虚拟资料 · 无需物流 · 即学即用", fill=(203,213,225), font=get_font(22))

im.save(out/"03.png", "PNG")
print("03 saved", (out/"03.png").stat().st_size)

# --- 04 Guide ---
im, draw = draw_board()
draw.text((BORDER+40, BORDER+28), "发货指南", fill=DARK, font=title_font)
draw.text((BORDER+40, BORDER+28+56), "虚拟资料 · 只发夸克网盘 · 不发百度/实物", fill=GRAY, font=sub_font)
steps=[
    ("1","拍后提供链接","下单后发送夸克网盘链接与提取码"),
    ("2","不限时·需提取码","带文件名，永久有效，反复下载"),
    ("3","即学即用",f"{LESSONS}个实战视频，按顺序学习即可复刻"),
    ("4","售后说明","虚拟资料不包变现承诺，按需拍"),
]
# 这一页原先是手写坐标，副标题、提醒框和卡片互相压字。改成用公共库的
# stack_layout 自适应排布：顶部从副标题墨迹下方起，底部停在底栏上方，
# 剩余空间均分到间距，内容增减不用再调坐标。
STEP_H=110
STEP_GAP=20
WARN_H=86
BAR_TOP=H-BORDER-86
tops, _ = stack_layout(
    [STEP_H]*len(steps) + [WARN_H],
    BORDER+28+56+30+20,
    BAR_TOP-30,
    min_gap=STEP_GAP,
    max_gap=36,
)
yy=tops[0]
for num, ttitle, tdesc in steps:
    draw.rounded_rectangle([BORDER+40, yy, W-BORDER-40, yy+STEP_H], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # left num
    draw.ellipse([BORDER+60, yy+32, BORDER+60+48, yy+32+48], fill=BLUE)
    nf=get_font(28, bold=True)
    tw=draw.textlength(num, font=nf)
    draw.text((BORDER+60+24-tw//2, yy+38), num, fill="white", font=nf)
    draw.text((BORDER+130, yy+22), ttitle, fill=DARK, font=get_font(26, bold=True))
    draw.text((BORDER+130, yy+58), tdesc, fill=GRAY, font=get_font(22))
    # 箭头放在卡片右缘内侧，早先画在 W-BORDER-60 会溢出到卡片外面
    if num!="4":
        draw.text((W-BORDER-92, yy+40), "→", fill=(226,232,240), font=get_font(28))
    yy+=STEP_H+STEP_GAP

# warning box
warn_y=tops[-1]
draw.rounded_rectangle([BORDER+40, warn_y, W-BORDER-40, warn_y+WARN_H], radius=14, fill=(255,251,235), outline=(253,230,138), width=1)
draw.text((BORDER+60, warn_y+12), "提醒", fill=(146,64,14), font=get_font(22, bold=True))
wf=get_font(16)
warn_text="虚拟资料一经发货不退不换，请确认是 Codex 职场办公需要再拍"
for idx, wl in enumerate(wrap_text_fit(warn_text, wf, W-2*BORDER-120, 2, draw, label="提醒")):
    draw.text((BORDER+60, warn_y+44+ idx*20), wl, fill=(120,113,108), font=wf)

draw.rounded_rectangle([BORDER, BAR_TOP, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, BAR_TOP+12), "只发夸克网盘", fill="white", font=get_font(24, bold=True))
draw.text((BORDER+40, BAR_TOP+48), "不发百度 · 不发实物 · 不包变现", fill=(203,213,225), font=get_font(18))

im.save(out/"04.png", "PNG")
print("04 saved", (out/"04.png").stat().st_size)
print("done", out)
