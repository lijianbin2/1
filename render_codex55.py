from PIL import Image, ImageDraw, ImageFont
import pathlib, textwrap

W=H=1080
BORDER=38
BLUE=(47,93,255)
DARK=(30,41,59)
GRAY=(100,116,139)
LIGHT_BG=(248,250,252)

def get_font(size, bold=False):
    path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

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

out = pathlib.Path(r"D:\闲鱼\Codex职场高效办公实战，AI自动化赋能日常办公")
out.mkdir(parents=True, exist_ok=True)

# --- 01 Cover ---
im, draw = draw_board()
# top badge
badge_font=get_font(26, bold=True)
badge_text="55集全  多场景实战"
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
feat_font=get_font(28, bold=True)
feat_sub=get_font(18)
features=[
    ("多模型一站式", "国产/第三方/API自由切换"),
    ("音视频全覆盖", "图片·视频·语音·剪辑"),
    ("飞书+知识库", "自动化办公到企业沉淀"),
]
y0= by+bh+46+82+76+40
for i,(a,b) in enumerate(features):
    x = BORDER+60 + i* ( (W-2*BORDER-120)//3 )
    # icon circle
    cx=x+70
    cy=y0+30
    draw.ellipse([cx-32, cy-32, cx+32, cy+32], fill=(239,246,255), outline=BLUE, width=2)
    icon_font=get_font(28, bold=True)
    icons=["◉","◆","▣"]
    iw=draw.textlength(icons[i], font=icon_font)
    draw.text((cx-iw//2, cy-16), icons[i], fill=BLUE, font=icon_font)
    # text
    aw=draw.textlength(a, font=feat_font)
    ax= x+70 - aw//2
    draw.text((ax, cy+44), a, fill=DARK, font=feat_font)
    bw2=draw.textlength(b, font=feat_sub)
    bx2= max(BORDER+20, min(W-BORDER-20-bw2, x+70 - bw2//2))
    # wrap if still wide
    if bw2 > (W-2*BORDER-120)//3 -20:
        lines2=wrap_text(b, feat_sub, (W-2*BORDER-120)//3 -20, draw)
        bx2a = x+70 - draw.textlength(lines2[0], font=feat_sub)//2
        draw.text((max(BORDER+10, bx2a), cy+78), lines2[0], fill=GRAY, font=feat_sub)
        if len(lines2)>1:
            bx2b = x+70 - draw.textlength(lines2[1], font=feat_sub)//2
            draw.text((max(BORDER+10, bx2b), cy+98), lines2[1], fill=GRAY, font=feat_sub)
    else:
        draw.text((bx2, cy+78), b, fill=GRAY, font=feat_sub)

# bottom bar
bar_h=86
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
tag="Codex · 55课时 · 办公自动化"
tw3=draw.textlength(tag, font=tag_font)
draw.text(((W-tw3)//2, H-BORDER-34), tag, fill=(148,163,184), font=tag_font) if False else None
# actually draw inside white area
draw.text((BORDER+40, H-BORDER-bar_h-36), "Codex · 55课时 · 办公自动化 · 即学即用", fill=GRAY, font=get_font(22))

im.save(out/"01.png", "PNG")
print("01 saved", (out/"01.png").stat().st_size)

# --- 02 Catalog ---
im, draw = draw_board()
title_font=get_font(44, bold=True)
draw.text((BORDER+40, BORDER+28), "课程目录", fill=DARK, font=title_font)
sub_font=get_font(24)
draw.text((BORDER+40, BORDER+28+56), "55课时 · 6大模块 · 办公全场景覆盖", fill=GRAY, font=sub_font)
# badge right
badge2="55节"
bf2=get_font(26, bold=True)
bw2=draw.textlength(badge2, font=bf2)+30
draw.rounded_rectangle([W-BORDER-40-bw2, BORDER+36, W-BORDER-40, BORDER+36+36], radius=18, fill=(239,246,255))
draw.text((W-BORDER-40-bw2+15, BORDER+42), badge2, fill=BLUE, font=bf2)

# modules 6 cards 3 columns x 2 rows
mods=[
    ("模块1 基础入门", "1-5", ["课程介绍","软件安装/登录","CCSwitch切国产模型","切第三方模型","配置模型生图/音视频"], BLUE),
    ("模块2 模型实战", "6-10", ["gpt-image2生图","Seedream生图","Seedance生视频","豆包生语音","edge文本转语音"], (124,58,237)),
    ("模块3 办公提效", "11-16", ["快速上手","批量整理文件","智能分析数据","撰写商业文档","市场调研洞察","实战经验总结"], (14,165,233)),
    ("模块4 行业报表", "17-26", ["行业数据分析","电商周报/年报","降本增效洞察","研发周报/年报","多行业PPT","研发/机器人/电商PPT"], (16,185,129)),
    ("模块5 视频与电商", "27-41", ["自动化剪辑","字幕/音乐/切片","文稿生成视频/特效","产品套图流水线","带货视频/宣传视频","数字人多角度/口播"], (249,115,22)),
    ("模块6 飞书与知识库", "42-55", ["飞书多场景办公","安装/上手CLI","云文档/会议/表格","管理项目任务","Obsidian知识库","资讯归档/Skill/PPT"], (225,29,72)),
]
card_w=(W-2*BORDER-80)//3
card_h=  (H-2*BORDER-140-86)//2 - 10
start_y=BORDER+130
gap=20
for idx, (mtitle, mrange, items, color) in enumerate(mods):
    col=idx%3
    row=idx//3
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
    it_font=get_font(18)
    iy=y+52
    for it in items:
        # bullet
        draw.ellipse([x+14, iy+7, x+14+6, iy+7+6], fill=color)
        draw.text((x+26, iy), "· "+it, fill=(51,65,85), font=it_font)
        iy+=22

# bottom bar
draw.rounded_rectangle([BORDER, H-BORDER-86, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, H-BORDER-68), "只发夸克", fill="white", font=get_font(24, bold=True))
draw.text((W-BORDER-40-draw.textlength("虚拟资料 · 拍后发网盘链接 · 整理即用", font=get_font(22)), H-BORDER-36), "虚拟资料 · 拍后发网盘链接 · 整理即用", fill=(203,213,225), font=get_font(22))

im.save(out/"02.png", "PNG")
print("02 saved", (out/"02.png").stat().st_size)

# --- 03 Harvest ---
im, draw = draw_board()
draw.text((BORDER+40, BORDER+28), "你将获得", fill=DARK, font=title_font)
draw.text((BORDER+40, BORDER+28+56), "从入门到实战，6步打通职场自动化", fill=GRAY, font=sub_font)
# 6 points left
points=[
    ("一站式模型调度", "国产/第三方/API，CCSwitch自由切，适配图片/音视频"),
    ("办公文档自动化", "商业文档·市场调研·智能数据分析·经验总结"),
    ("行业报表与PPT", "电商周报/年报·研发交付·人形机器人调研·高质量PPT"),
    ("视频与电商流水线", "自动剪辑·批量字幕·切片混剪·产品套图·数字人带货"),
    ("飞书深度集成", "云文档·智能约会·多维表·项目任务全自动"),
    ("企业知识库闭环", "Obsidian+Codex+Skill，白板知识地图与资讯归档"),
]
y=start_y
for i,(ptitle, pdesc) in enumerate(points):
    col=i%2
    row=i//2
    x=BORDER+40+col*( (W-2*BORDER-80)//2 +20)
    yy=BORDER+110+row*145
    draw.rounded_rectangle([x, yy, x+(W-2*BORDER-80)//2, yy+125], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # number
    num_font=get_font(20, bold=True)
    draw.rounded_rectangle([x+14, yy+14, x+14+28, yy+14+28], radius=14, fill=BLUE)
    draw.text((x+14+8, yy+16), str(i+1), fill="white", font=num_font)
    draw.text((x+14+40, yy+16), ptitle, fill=DARK, font=get_font(22, bold=True))
    # desc wrap
    df=get_font(18)
    lines=wrap_text(pdesc, df, (W-2*BORDER-80)//2 -28, draw)
    dy=yy+52
    for l in lines[:2]:
        draw.text((x+14, dy), l, fill=GRAY, font=df)
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
    ("1","拍下即得","夸克网盘链接自动发货，无需等待"),
    ("2","不限时·需提取码","带文件名，永久有效，反复下载"),
    ("3","即学即用","55个实战视频，按顺序学习即可复刻"),
    ("4","售后说明","虚拟资料不包变现承诺，按需拍"),
]
yy=BORDER+120
for num, ttitle, tdesc in steps:
    draw.rounded_rectangle([BORDER+40, yy, W-BORDER-40, yy+110], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # left num
    draw.ellipse([BORDER+60, yy+32, BORDER+60+48, yy+32+48], fill=BLUE)
    nf=get_font(28, bold=True)
    tw=draw.textlength(num, font=nf)
    draw.text((BORDER+60+24-tw//2, yy+38), num, fill="white", font=nf)
    draw.text((BORDER+130, yy+22), ttitle, fill=DARK, font=get_font(26, bold=True))
    draw.text((BORDER+130, yy+58), tdesc, fill=GRAY, font=get_font(22))
    # arrow
    if num!="4":
        draw.text((W-BORDER-60, yy+40), "→", fill=(226,232,240), font=get_font(28))
    yy+=130

# warning box
warn_y=yy+10
draw.rounded_rectangle([BORDER+40, warn_y, W-BORDER-40, warn_y+70], radius=14, fill=(255,251,235), outline=(253,230,138), width=1)
draw.text((BORDER+60, warn_y+16), "提醒", fill=(146,64,14), font=get_font(22, bold=True))
draw.text((BORDER+60, warn_y+38), "虚拟资料一经发货不退不换，请确认是 Codex 职场办公需要再拍", fill=(120,113,108), font=get_font(18))

draw.rounded_rectangle([BORDER, H-BORDER-86, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, H-BORDER-68), "只发夸克网盘", fill="white", font=get_font(24, bold=True))
draw.text((BORDER+40, H-BORDER-38), "不发百度 · 不发实物 · 不包变现", fill=(203,213,225), font=get_font(18))

im.save(out/"04.png", "PNG")
print("04 saved", (out/"04.png").stat().st_size)
print("done", out)
