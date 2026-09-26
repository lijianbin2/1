from PIL import Image, ImageDraw, ImageFont
import os
import pathlib

W=H=1080
BORDER=38
BLUE=(47,93,255)
DARK=(30,41,59)
GRAY=(100,116,139)
LIGHT_BG=(248,250,252)

# 课程规模来自 verify_source.py 对源目录的实测结果（37 个视频），改数量只改这里。
LESSONS = int(os.environ.get("XIANYU_WORKBUDDY_LESSONS", "37"))
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
        "D:/闲鱼/WorkBuddy智能体实战，打造个人AI效率系统",
    )
)
out.mkdir(parents=True, exist_ok=True)

# --- 01 Cover ---
im, draw = draw_board()
# top badge
badge_font=get_font(26, bold=True)
badge_text=f'{LESSON_SHORT}全 智能体实战'
# badge bg
bw = draw.textlength(badge_text, font=badge_font)+40
bh=42
bx=(W-bw)//2
by=BORDER+36
draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=21, fill=BLUE)
draw.text((bx+(bw-draw.textlength(badge_text, font=badge_font))//2, by+9), badge_text, fill="white", font=badge_font)
# title
title='WorkBuddy智能体实战'
subtitle='打造个人AI效率系统'
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
bar_h=86
feat_font=get_font(28, bold=True)
feat_sub=get_font(18)
features=[
    ('智能体一站式', 'Skill知识库自动化'),
    ('数字人全流程', '形象声音口播视频'),
    ('办公全场景', 'PPT数据剪辑飞书'),
];
y0= by+bh+46+82+76+40
FEAT_CARD_H=196
FEAT_FOOT=H-BORDER-bar_h-64
# 特色区在分隔线与底栏之间垂直居中，底栏上方不留大片空白
y0=max(y0, y0+(FEAT_FOOT-y0-FEAT_CARD_H)//2)
feat_w=(W-2*BORDER-120-2*24)//3
for i,(a,b) in enumerate(features):
    x = BORDER+60 + i* (feat_w+24)
    draw.rounded_rectangle([x, y0, x+feat_w, y0+FEAT_CARD_H], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # icon circle
    cx=x+feat_w//2
    cy=y0+34
    draw.ellipse([cx-32, cy-32, cx+32, cy+32], fill=(239,246,255), outline=BLUE, width=2)
    icon_font=get_font(28, bold=True)
    icons=["1","2","3"]
    iw=draw.textlength(icons[i], font=icon_font)
    draw.text((cx-iw//2, cy-16), icons[i], fill=BLUE, font=icon_font)
    # text
    aw=draw.textlength(a, font=feat_font)
    ax= cx - aw//2
    draw.text((ax, cy+50), a, fill=DARK, font=feat_font)
    bw2=draw.textlength(b, font=feat_sub)
    bx2= max(x+10, min(x+feat_w-10-bw2, cx - bw2//2))
    # wrap if still wide
    if bw2 > feat_w-20:
        lines2=wrap_text(b, feat_sub, feat_w-20, draw)
        bx2a = cx - draw.textlength(lines2[0], font=feat_sub)//2
        draw.text((max(x+10, bx2a), cy+88), lines2[0], fill=GRAY, font=feat_sub)
        if len(lines2)>1:
            bx2b = x+70 - draw.textlength(lines2[1], font=feat_sub)//2
            draw.text((max(x+10, bx2b), cy+110), lines2[1], fill=GRAY, font=feat_sub)
    else:
        draw.text((bx2, cy+88), b, fill=GRAY, font=feat_sub)

# bottom bar
draw.rounded_rectangle([BORDER, H-BORDER-bar_h, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
bar_font=get_font(24, bold=True)
bar_font2=get_font(22)
bar_text="只发夸克"
bar_text2="虚拟资料 · 拍后发网盘链接 · 无需物流"
draw.text((BORDER+40, H-BORDER-bar_h+18), bar_text, fill="white", font=bar_font)
# second line centered? put right
w2=draw.textlength(bar_text2, font=bar_font2)
draw.text((W-BORDER-40-w2, H-BORDER-bar_h+48), bar_text2, fill=(203,213,225), font=bar_font2)
# bottom tag, drawn inside the white area above the bar
draw.text((BORDER+40, H-BORDER-bar_h-36), f'WorkBuddy · {LESSON_FULL} · 智能体实战 · 即学即用', fill=GRAY, font=get_font(22))

im.save(out/"01.png", "PNG")
print("01 saved", (out/"01.png").stat().st_size)

# --- 02 Catalog ---
im, draw = draw_board()
title_font=get_font(44, bold=True)
draw.text((BORDER+40, BORDER+28), "课程目录", fill=DARK, font=title_font)
sub_font=get_font(24)
draw.text((BORDER+40, BORDER+28+56), f'{LESSON_FULL} · {MODULES_LABEL} · 智能体全场景覆盖', fill=GRAY, font=sub_font)
# badge right
badge2=LESSON_BADGE
bf2=get_font(26, bold=True)
bw2=draw.textlength(badge2, font=bf2)+30
draw.rounded_rectangle([W-BORDER-40-bw2, BORDER+36, W-BORDER-40, BORDER+36+36], radius=18, fill=(239,246,255))
draw.text((W-BORDER-40-bw2+15, BORDER+42), badge2, fill=BLUE, font=bf2)

# modules 6 cards 2 columns x 3 rows
mods=[
    ('模块1 基础入门', '1-7', ['课前须知', '安装入门', '基础配置', '积分任务', '核心能力', '知识库应用'], BLUE),
    ('模块2 Skill技能', '8-12', ['认识Skill', '使用Skill', '创建Skill', '发布SkillHub', '搜索Skill'], (124,58,237)),
    ('模块3 自动化创作', '13-17', ['新闻创作', '海报图片', '制作3D模型', '生成视频', '小红书配图'], (14,165,233)),
    ('模块4 知识库进阶', '18-22', ['Obsidian安装', '接入WorkBuddy', '个人知识体系', '插件配置', '外部插件'], (16,185,129)),
    ('模块5 数字人', '23-28', ['定制分身', '形象定制', '声音复刻', '文案视频', '口播生成器', '数字人Skill'], (249,115,22)),
    # 末个模块的结束课时跟 LESSONS 走，否则改数量后目录仍停在旧数字
    ('模块6 办公实战', f'29-{LESSONS}', ['小程序开发', 'PPT整理成稿', '数据分析报告', '写作周报', '剪辑实战', '飞书双工作台'], (225,29,72)),
];
CAT_COLS=2
CAT_ROWS=3
CAT_GAP=24
CAT_TOP=BORDER+130
# 末行卡片与底栏之间留出 20px 呼吸空间，否则卡片底边几乎贴着深色底栏
CAT_FOOT=H-BORDER-86-20
card_w=(W-2*BORDER-80-CAT_GAP)//CAT_COLS
max_items=max(len(m[2]) for m in mods)
# 卡片高度由可用高度反推，行距吃掉剩余空间，避免大片空白
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
    ('Skill技能体系', '认识使用创建发布搜索全通'),
    ('知识库搭建', 'Obsidian接入个人体系插件'),
    ('自动化创作', '新闻海报3D视频配图量产'),
    ('数字人全套', '形象声音口播视频生成器'),
    ('办公提效实战', '小程序PPT数据写作剪辑'),
    ('双工作台交付', '飞书接入自媒体创作闭环'),
];
draw.text((BORDER+40, BORDER+28), "你将获得", fill=DARK, font=title_font)
draw.text((BORDER+40, BORDER+28+56), f'从入门到实战，{len(points)}步打通个人效率系统', fill=GRAY, font=sub_font)
PT_COLS=2
PT_ROWS=3
PT_TOP=BORDER+130
PT_FOOT=H-BORDER-86-140-20
PT_PAD=22
PT_GAP_MAX=56
PT_GAP=24
pt_w=(W-2*BORDER-80-PT_GAP)//PT_COLS
pt_desc_font=get_font(16)
pt_lines={t:wrap_text(d, pt_desc_font, pt_w-32, draw)[:2] for t,d in points}
max_block=max(44+len(v)*22 for v in pt_lines.values())
pt_h=max_block+PT_PAD*2
PT_GAP=min(PT_GAP_MAX, (PT_FOOT-PT_TOP-PT_ROWS*pt_h)//(PT_ROWS-1))
if PT_GAP < 16:
    raise ValueError("收获卡片与适合谁区块重叠")
# 间距封顶后整块垂直居中，避免底部堆积空白
pt_top=PT_TOP+(PT_FOOT-PT_TOP-(PT_ROWS*pt_h+(PT_ROWS-1)*PT_GAP))//2
for i,(ptitle, pdesc) in enumerate(points):
    col=i%PT_COLS
    row=i//PT_COLS
    x=BORDER+40+col*(pt_w+PT_GAP)
    yy=pt_top+row*(pt_h+PT_GAP)
    draw.rounded_rectangle([x, yy, x+pt_w, yy+pt_h], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # 标题与描述整体垂直居中，避免文字全部堆在卡片顶部
    lines=pt_lines[ptitle]
    block_h=44+len(lines)*22
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
scenes=['职场办公党', '新媒体运营', '知识付费创作者', '想用AI提效的所有人']
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
    ('3','即学即用',f'{LESSONS}个实战视频，按顺序学习即可复刻'),
    ("4","售后说明","虚拟资料不包变现承诺，按需拍"),
]
STEP_TOP=BORDER+130
STEP_GAP=20
STEP_H=(H-BORDER-86-40-86-20-STEP_TOP-(len(steps)-1)*STEP_GAP)//len(steps)
if STEP_H < 110:
    raise ValueError("发货指南卡片高度不足以容纳两行文字")
yy=STEP_TOP
for num, ttitle, tdesc in steps:
    draw.rounded_rectangle([BORDER+40, yy, W-BORDER-40, yy+STEP_H], radius=18, fill=(248,250,252), outline=(226,232,240), width=1)
    # left num
    num_cy=yy+(STEP_H-48)//2
    draw.ellipse([BORDER+60, num_cy, BORDER+60+48, num_cy+48], fill=BLUE)
    nf=get_font(28, bold=True)
    tw=draw.textlength(num, font=nf)
    draw.text((BORDER+60+24-tw//2, num_cy+6), num, fill="white", font=nf)
    ty=yy+(STEP_H-36-30)//2
    draw.text((BORDER+130, ty), ttitle, fill=DARK, font=get_font(26, bold=True))
    draw.text((BORDER+130, ty+36), tdesc, fill=GRAY, font=get_font(22))
    # arrow
    if num!="4":
        draw.text((W-BORDER-60, num_cy+2), "→", fill=(226,232,240), font=get_font(28))
    yy+=STEP_H+STEP_GAP

# warning box
warn_y=yy+10
draw.rounded_rectangle([BORDER+40, warn_y, W-BORDER-40, warn_y+86], radius=14, fill=(255,251,235), outline=(253,230,138), width=1)
draw.text((BORDER+60, warn_y+12), "提醒", fill=(146,64,14), font=get_font(22, bold=True))
wf=get_font(16)
warn_text='虚拟资料一经发货不退不换，请确认是WorkBuddy智能体需要再拍'
for idx, wl in enumerate(wrap_text(warn_text, wf, W-2*BORDER-120, draw)[:2]):
    draw.text((BORDER+60, warn_y+44+ idx*20), wl, fill=(120,113,108), font=wf)

# 底栏两行用 BAR_TOP 相对定位并留足行距。早先按 H-BORDER-68/-38 硬写，
# 24px 与 18px 两行的真实墨迹只差 3px，几乎连成一片。
BAR_TOP=H-BORDER-86
draw.rounded_rectangle([BORDER, BAR_TOP, W-BORDER, H-BORDER], radius=22, fill=(30,41,59))
draw.text((BORDER+40, BAR_TOP+12), "只发夸克网盘", fill="white", font=get_font(24, bold=True))
draw.text((BORDER+40, BAR_TOP+48), "不发百度 · 不发实物 · 不包变现", fill=(203,213,225), font=get_font(18))

im.save(out/"04.png", "PNG")
print("04 saved", (out/"04.png").stat().st_size)
print("done", out)
