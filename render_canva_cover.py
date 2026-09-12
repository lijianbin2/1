from PIL import Image, ImageDraw, ImageFont
import pathlib

W = H = 1080
BORDER = 38
BLUE = (47,93,255)
DARK = (30,41,59)
GRAY = (100,116,139)
LIGHT = (241,245,249)
LIGHT2 = (239,246,255)
LIGHT_BG = (248,250,252)

def get_font(size, bold=False):
    path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_board():
    im = Image.new("RGB", (W,H), BLUE)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle([BORDER, BORDER, W-BORDER, H-BORDER], radius=32, fill="white")
    return im, draw

def wrap_text(text, font, max_w, draw):
    lines=[]; line=""
    for ch in text:
        test=line+ch
        if draw.textlength(test, font=font) > max_w:
            lines.append(line); line=ch
        else:
            line=test
    if line: lines.append(line)
    return lines

out = pathlib.Path(r"D:\闲鱼\Codex职场高效办公实战，AI自动化赋能日常办公")
out.mkdir(parents=True, exist_ok=True)

# === 01 Cover Canva-grade v2 ===
im, draw = draw_board()
# top badge dynamic width
badge_font = get_font(26, bold=True)
badge_text = "55集全  多场景实战"
bw = int(draw.textlength(badge_text, font=badge_font) + 40)
bh = 42
bx = (W - bw)//2
by = BORDER + 36
draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=21, fill=BLUE)
draw.text((bx + (bw - draw.textlength(badge_text, font=badge_font))//2, by+9), badge_text, fill="white", font=badge_font)
# title
tfont = get_font(66, bold=True)
sfont = get_font(36)
title = "Codex职场高效办公实战"
subtitle = "AI自动化赋能日常办公"
tw = draw.textlength(title, font=tfont)
draw.text(((W-tw)//2, by+bh+46), title, fill=DARK, font=tfont)
sw = draw.textlength(subtitle, font=sfont)
draw.text(((W-sw)//2, by+bh+46+82), subtitle, fill=GRAY, font=sfont)
draw.line([(W-200)//2, by+bh+46+82+56, (W+200)//2, by+bh+46+82+56], fill=BLUE, width=4)
# 3 features
feat_font = get_font(28, bold=True)
feat_sub = get_font(18)
features = [
    ("多模型一站式", "国产/第三方/API自由切换"),
    ("音视频全覆盖", "图片·视频·语音·剪辑"),
    ("飞书+知识库", "自动化办公到企业沉淀"),
]
icons = ["◈", "▶", "◆"]
y0 = by+bh+46+82+76+40
for i,(a,b) in enumerate(features):
    x = BORDER+60 + i * ((W-2*BORDER-120)//3)
    cx = x+70; cy = y0+30
    draw.ellipse([cx-32, cy-32, cx+32, cy+32], fill=LIGHT2, outline=BLUE, width=2)
    iw = draw.textlength(icons[i], font=get_font(28, bold=True))
    draw.text((cx-iw//2, cy-16), icons[i], fill=BLUE, font=get_font(28, bold=True))
    aw = draw.textlength(a, font=feat_font)
    draw.text((x+70 - aw//2, cy+44), a, fill=DARK, font=feat_font)
    bw2 = draw.textlength(b, font=feat_sub)
    bx2 = max(BORDER+20, min(W-BORDER-20-bw2, x+70 - bw2//2))
    if bw2 > (W-2*BORDER-120)//3 - 20:
        lines2 = wrap_text(b, feat_sub, (W-2*BORDER-120)//3 -20, draw)
        for li, line in enumerate(lines2[:2]):
            lw = draw.textlength(line, font=feat_sub)
            draw.text((x+70 - lw//2, cy+78+li*20), line, fill=GRAY, font=feat_sub)
    else:
        draw.text((bx2, cy+78), b, fill=GRAY, font=feat_sub)

# middle gray card - fix overlap: card_y = y0+150
card_y = y0 + 150
card_h = 320
card_x = BORDER+32
card_w = W - 2*BORDER - 64
draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h], radius=20, fill=LIGHT)
# left notebook mock 420x240
mock_x = card_x + 24
mock_y = card_y + 24
mock_w = 420
mock_h = 240
draw.rounded_rectangle([mock_x, mock_y, mock_x+mock_w, mock_y+mock_h], radius=16, fill="white", outline=(226,232,240), width=1)
# mock header
draw.rounded_rectangle([mock_x, mock_y, mock_x+mock_w, mock_y+36], radius=8, fill=(30,41,59))
# window dots
for di, col in enumerate([(239,68,68),(234,179,8),(34,197,94)]):
    draw.ellipse([mock_x+14+di*22, mock_y+12, mock_x+14+di*22+12, mock_y+24], fill=col)
draw.text((mock_x+90, mock_y+9), "Codex · 自动化工作流", fill="white", font=get_font(16, bold=True))
# mock code lines
code_lines = ["import codex", "workflow.run()", "data.analyze()", "report.export()", "auto.deploy()"]
for ci, cl in enumerate(code_lines):
    y = mock_y + 56 + ci*32
    # line number
    draw.text((mock_x+14, y), str(ci+1), fill=(148,163,184), font=get_font(14))
    # code text
    draw.text((mock_x+36, y), cl, fill=DARK, font=get_font(14))
    # bar chart on right side of mock
    bar_w = 40 + ci*18
    draw.rounded_rectangle([mock_x+mock_w-90, y+4, mock_x+mock_w-90+bar_w, y+14], radius=4, fill=BLUE if ci%2==0 else (99,102,241))
# right 6 chips 3x2 dynamic badge width
mods = [
    ("01-05","基础入门","课程/安装/模型"),
    ("06-10","模型实战","生图/生视频/语音"),
    ("11-16","办公提效","文件/数据/文档"),
    ("17-26","行业报表","周报/年报/PPT"),
    ("27-41","视频电商","剪辑/套图/带货"),
    ("42-55","飞书知识库","文档/项目/沉淀"),
]
chip_w = (card_w - mock_w - 48 - 16) // 3  # 3 columns gap 8
chip_h = 86
chip_gap_x = 8
chip_gap_y = 12
chip_start_x = mock_x + mock_w + 16
chip_start_y = mock_y + 8
for idx,(rng, tit, desc) in enumerate(mods):
    col = idx % 3
    row = idx // 3
    x = chip_start_x + col*(chip_w+chip_gap_x)
    y = chip_start_y + row*(chip_h+chip_gap_y)
    draw.rounded_rectangle([x, y, x+chip_w, y+chip_h], radius=12, fill="white", outline=(226,232,240), width=1)
    # badge dynamic width: rng text + padding
    bf = get_font(13, bold=True)
    # dynamic badge width to avoid truncation of 01-0
    bw_chip = int(draw.textlength(rng, font=bf) + 16)
    # cap to chip width
    bw_chip = min(bw_chip, chip_w-10)
    draw.rounded_rectangle([x+8, y+10, x+8+bw_chip, y+10+18], radius=9, fill=BLUE)
    draw.text((x+8+(bw_chip-draw.textlength(rng, font=bf))//2, y+11), rng, fill="white", font=bf)
    draw.text((x+10, y+34), tit, fill=DARK, font=get_font(15, bold=True))
    draw.text((x+10, y+54), desc, fill=GRAY, font=get_font(12))

# bottom pill
pill_text = "55集完整版 · 即学即用 · 零基础友好"
pill_font = get_font(20, bold=True)
pw = int(draw.textlength(pill_text, font=pill_font) + 36)
ph = 36
px = (W - pw)//2
py = card_y + card_h + 22
draw.rounded_rectangle([px, py, px+pw, py+ph], radius=18, fill=BLUE)
draw.text((px+18, py+7), pill_text, fill="white", font=pill_font)

# bottom bar dark
bar_h = 86
draw.rounded_rectangle([BORDER, H-BORDER-bar_h, W-BORDER, H-BORDER], radius=22, fill=DARK)
draw.text((BORDER+40, H-BORDER-bar_h+18), "只发夸克", fill="white", font=get_font(24, bold=True))
bar2 = "虚拟资料 · 拍后发网盘链接 · 无需物流"
w2 = draw.textlength(bar2, font=get_font(22))
draw.text((W-BORDER-40-w2, H-BORDER-bar_h+48), bar2, fill=(203,213,225), font=get_font(22))
draw.text((BORDER+40, H-BORDER-bar_h-36), "Codex · 55课时 · 办公自动化 · 即学即用", fill=GRAY, font=get_font(22))

im.save(out/"01.png", "PNG")
# also save canva copy
im.save(out/"01_canva.png", "PNG")
print("01 saved", (out/"01.png").stat().st_size)
