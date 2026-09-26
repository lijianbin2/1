from PIL import Image, ImageDraw, ImageFont
import os
from xianyu_common import wrap_text_fit

VER = os.environ.get("XIANYU_LEGACY_VERSION", "v7.23").strip()
VER_PREFIX = (VER + " ") if VER else ""
import pathlib

# 安装包体积集中声明。默认 4.1MB 对应源文件实测 4,102,490 字节（十进制 MB）；
# 换版本时用环境变量覆盖，或用 verify_source.py 重新核验后改这里。
PACKAGE_MB = os.environ.get("XIANYU_WINRAR_MB", "4.1").strip()
SIZE_LABEL = f"约{PACKAGE_MB}MB"
SIZE_SHORT = f"{PACKAGE_MB}MB"

W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)

def get_font(size, bold=False):
    p = "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"
    try:
        return ImageFont.truetype(p, size)
    except OSError:
        raise RuntimeError(f"无法加载字体：{p}") from None

def draw_board():
    im = Image.new("RGB", (W, H), BLUE)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([BORDER, BORDER, W - BORDER, H - BORDER], radius=32, fill="white")
    return im, d

def wrap_text(text, font, max_w, d):
    lines = []
    line = ""
    for ch in text:
        t = line + ch
        if d.textlength(t, font=font) > max_w:
            lines.append(line)
            line = ch
        else:
            line = t
    if line:
        lines.append(line)
    return lines

def bottom_bar(d, left, right):
    d.rounded_rectangle([BORDER, BAR_TOP, W - BORDER, H - BORDER], radius=22, fill=(30, 41, 59))
    d.text((BORDER + 40, BAR_TOP + 16), left, fill="white", font=get_font(24, bold=True))
    f2 = get_font(20)
    w2 = d.textlength(right, font=f2)
    d.text((W - BORDER - 60 - w2, BAR_TOP + 40), right, fill=(203, 213, 225), font=f2)

def center_text(d, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) // 2, y), text, fill=fill, font=font)

# 页内信息条的高度（封面 01 的"下载exe…"那一条）。
# 早先它和底部深色横条都叫 FOOTER_H，但两者含义完全不同：
# 改一个不动另一个，很容易以为改了其实没改。现在分开命名。
NOTE_H = 60
# 底部深色横条的顶部。
# BAR_H 是横条本身的高度，WARN_H 是 04 页"提醒"框的高度。两者数值都是 86，
# 但含义完全无关：早先都用裸字面量 86，改一个不动另一个，
# 看起来改过其实没改到要改的地方。
BAR_H = 86
WARN_H = 86
BAR_TOP = H - BORDER - BAR_H

def stack(heights, top, bottom, min_gap=20, max_gap=48):
    """把若干区块在 [top, bottom] 内纵向排布，返回每个区块的起始 y。

    间距按剩余空间自适应并封顶，整块再垂直居中，因此不会再出现
    固定写死坐标导致的底部大片空白。
    """
    heights = list(heights)
    n = len(heights) - 1
    slack = bottom - top - sum(heights)
    gap = min(max_gap, max(min_gap, slack // n)) if n > 0 else 0
    used = sum(heights) + gap * n
    # 间距封顶后剩余空间才会留在两端，此时才做居中
    leftover = bottom - top - used
    y = top + (leftover // 2 if leftover > 0 else 0)
    tops = []
    for h in heights:
        tops.append(y)
        y += h + gap
    if tops and tops[-1] + heights[-1] > bottom:
        raise ValueError("区块总高度超出可用区域，版式无法容纳")
    return tops

out = pathlib.Path(
    os.environ.get(
        "XIANYU_LEGACY_OUT",
        pathlib.Path("D:/闲鱼") / f"WinRAR {VER_PREFIX}解压缩工具",
    )
)
out.mkdir(parents=True, exist_ok=True)

# ---------- 01 cover ----------
im, d = draw_board()
bf = get_font(26, bold=True)
bt = "WinRAR " + VER_PREFIX + "64位"
bw = d.textlength(bt, font=bf) + 56
bx = (W - bw) // 2
by = BORDER + 36
d.rounded_rectangle([bx, by, bx + bw, by + 42], radius=21, fill=BLUE)
d.text((bx + (bw - d.textlength(bt, font=bf)) // 2, by + 9), bt, fill="white", font=bf)
center_text(d, by + 42 + 40, "WinRAR解压缩神器", get_font(66, bold=True), DARK)
center_text(d, by + 42 + 40 + 82, "经典稳定 装机必备", get_font(36), GRAY)
d.line([(W - 200) // 2, by + 42 + 40 + 82 + 56, (W + 200) // 2, by + 42 + 40 + 82 + 56], fill=BLUE, width=4)
feats = [("1", "极速解压", "RAR ZIP 7Z全支持"), ("2", "压缩分卷", "加密分卷批量处理"), ("3", "稳定纯净", "Win10/11 64位亲测")]
FEAT_H = 176
INFO_H = 140
y0 = by + 42 + 40 + 82 + 76 + 34
fmt_y, info_y, foot_y = stack(
    [110, INFO_H, NOTE_H],
    by + 42 + 40 + 82 + 76 + 34 + FEAT_H + 34,
    BAR_TOP - 40,
)
slot = (W - 2 * BORDER - 120) // 3
for i, (n, a, b) in enumerate(feats):
    x = BORDER + 60 + i * slot
    cx = x + 70
    cy = y0 + 30
    d.ellipse([cx - 32, cy - 32, cx + 32, cy + 32], fill=(239, 246, 255), outline=BLUE, width=2)
    nf = get_font(28, bold=True)
    iw = d.textlength(n, font=nf)
    d.text((cx - iw // 2, cy - 16), n, fill=BLUE, font=nf)
    af = get_font(28, bold=True)
    aw = d.textlength(a, font=af)
    d.text((cx - aw // 2, cy + 44), a, fill=DARK, font=af)
    sf = get_font(18)
    bw2 = d.textlength(b, font=sf)
    d.text((cx - bw2 // 2, cy + 78), b, fill=GRAY, font=sf)
d.rounded_rectangle([BORDER + 40, fmt_y, W - BORDER - 40, fmt_y + 110], radius=18, fill=(239, 246, 255))
d.text((BORDER + 60, fmt_y + 14), "全格式通吃", fill=DARK, font=get_font(22, bold=True))
sx = BORDER + 60
ff = get_font(20)
for s in ["RAR", "ZIP", "7Z", "CAB", "ISO"]:
    w = d.textlength(s, font=ff) + 28
    d.rounded_rectangle([sx, fmt_y + 48, sx + w, fmt_y + 82], radius=14, fill="white", outline=BLUE, width=1)
    d.text((sx + 14, fmt_y + 52), s, fill=BLUE, font=ff)
    sx += w + 12
d.rounded_rectangle([BORDER + 40, info_y, W - BORDER - 40, info_y + INFO_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
cols = [("拍后提供链接", "拍后发夸克链接"), ("即装即用", "双击安装右键即用"), ("小白友好", "下载就会用")]
for j, (h, s) in enumerate(cols):
    ix = BORDER + 60 + j * ((W - 2 * BORDER - 80) // 3)
    d.text((ix, info_y + 20), h, fill=BLUE, font=get_font(22, bold=True))
    d.text((ix, info_y + 62), s, fill=GRAY, font=get_font(18))
    d.text((ix, info_y + 90), "无需等待" if j == 0 else ("Win10/11亲测" if j == 1 else "装机必备"), fill=GRAY, font=get_font(18))
d.text((BORDER + 40, foot_y), "WinRAR " + VER_PREFIX + "64位 单文件安装包 " + SIZE_LABEL, fill=GRAY, font=get_font(22))
d.text((BORDER + 40, foot_y + 30), "下载exe 双击安装 右键即见解压菜单", fill=GRAY, font=get_font(20))
bottom_bar(d, "只发夸克", "虚拟资料 拍后发网盘链接 无需物流")
im.save(out / "01.png", "PNG")
print("01 saved", (out / "01.png").stat().st_size)

# ---------- 02 file detail ----------
im, d = draw_board()
d.text((BORDER + 40, BORDER + 28), "文件详情", fill=DARK, font=get_font(44, bold=True))
d.text((BORDER + 40, BORDER + 28 + 56), "1个安装包 " + SIZE_SHORT + " Win10/11 64位", fill=GRAY, font=get_font(24))
BADGE2_DEFAULT = "64位"
BADGE2 = VER if VER else BADGE2_DEFAULT
bf2 = get_font(26, bold=True)
bw2 = d.textlength(BADGE2, font=bf2) + 44
d.rounded_rectangle([W - BORDER - 40 - bw2, BORDER + 36, W - BORDER - 40, BORDER + 36 + 42], radius=21, fill=BLUE)
d.text((W - BORDER - 40 - bw2 + 22, BORDER + 45), BADGE2, fill="white", font=bf2)
cards = [("文件名", "WinRAR " + VER_PREFIX + "64位 单文件版"), ("大小", SIZE_LABEL + " 单文件"), ("系统", "Win10 / Win11 64位"), ("格式", "RAR ZIP 7Z CAB ISO全解")]
cw = (W - 2 * BORDER - 80) // 2
INFO_CARD_H = 110
GRID_H = INFO_CARD_H * 2 + 20
BOX_H = 130
grid_y, fmt_y, step_y, pure_y, foot_y = stack(
    [GRID_H, 124, BOX_H, BOX_H, 34],
    BORDER + 130,
    BAR_TOP - 40,
)
for i, (k, v) in enumerate(cards):
    x = BORDER + 40 + (i % 2) * (cw + 20)
    y = grid_y + (i // 2) * (INFO_CARD_H + 20)
    d.rounded_rectangle([x, y, x + cw, y + INFO_CARD_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    d.text((x + 16, y + 12), k, fill=BLUE, font=get_font(20, bold=True))
    info_font = get_font(22, bold=True)
    for j, ln in enumerate(wrap_text_fit(v, info_font, cw - 32, 2, d, label=f"要点 {k}")):
        d.text((x + 16, y + 46 + j * 28), ln, fill=DARK, font=info_font)
d.rounded_rectangle([BORDER + 40, fmt_y, W - BORDER - 40, fmt_y + 124], radius=18, fill=(239, 246, 255))
d.text((BORDER + 60, fmt_y + 14), "解压全支持", fill=DARK, font=get_font(22, bold=True))
sx = BORDER + 60
ff = get_font(20)
for s in ["RAR", "ZIP", "7Z", "CAB", "ISO", "TAR", "GZ"]:
    w = d.textlength(s, font=ff) + 28
    d.rounded_rectangle([sx, fmt_y + 50, sx + w, fmt_y + 84], radius=14, fill="white", outline=BLUE, width=1)
    d.text((sx + 14, fmt_y + 54), s, fill=BLUE, font=ff)
    sx += w + 12
d.rounded_rectangle([BORDER + 40, step_y, W - BORDER - 40, step_y + BOX_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
d.text((BORDER + 60, step_y + 20), "安装3步", fill=DARK, font=get_font(22, bold=True))
d.text((BORDER + 60, step_y + 62), "下载exe 双击安装 右键即见解压菜单", fill=GRAY, font=get_font(20))
d.rounded_rectangle([BORDER + 40, pure_y, W - BORDER - 40, pure_y + BOX_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
d.text((BORDER + 60, pure_y + 20), "单文件纯净包", fill=DARK, font=get_font(22, bold=True))
d.text((BORDER + 60, pure_y + 62), SIZE_SHORT + " 下载快 不捆绑 到手即装即用", fill=GRAY, font=get_font(20))
d.text((BORDER + 40, foot_y + 4), "右键菜单集成 选中文件即压即解 无需开软件", fill=GRAY, font=get_font(20))
bottom_bar(d, "只发夸克", "虚拟资料 拍后发网盘链接 整理即用")
im.save(out / "02.png", "PNG")
print("02 saved", (out / "02.png").stat().st_size)

# ---------- 03 harvest ----------
im, d = draw_board()
d.text((BORDER + 40, BORDER + 28), "你将获得", fill=DARK, font=get_font(44, bold=True))
d.text((BORDER + 40, BORDER + 28 + 56), "一次入手 解压压缩长期省心", fill=GRAY, font=get_font(24))
pts = [("极速解压", "大文件秒解进度可视"), ("多格式通吃", "收到的包基本都能开"), ("分卷压缩", "大文件拆小好传输"), ("加密压缩", "设密码保护隐私文件"), ("右键集成", "选中即压无需开软件"), ("稳定兼容", "Win10/11 64位亲测可用")]
cw = (W - 2 * BORDER - 80) // 2
CARD_H = 122
SUIT_H = 112
grid_top, line_y, suit_y = stack(
    [CARD_H * 3 + 20 * 2, 30, SUIT_H],
    BORDER + 130,
    BAR_TOP - 40,
)
for i, (t, s) in enumerate(pts):
    x = BORDER + 40 + (i % 2) * (cw + 20)
    y = grid_top + (i // 2) * (CARD_H + 20)
    d.rounded_rectangle([x, y, x + cw, y + CARD_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    d.rounded_rectangle([x + 14, y + 14, x + 42, y + 42], radius=14, fill=BLUE)
    d.text((x + 22, y + 16), str(i + 1), fill="white", font=get_font(20, bold=True))
    d.text((x + 54, y + 16), t, fill=DARK, font=get_font(22, bold=True))
    df = get_font(16)
    dy = y + 52
    for ln in wrap_text_fit(s, df, cw - 32, 2, d, label=f"步骤 {t}"):
        d.text((x + 14, dy), ln, fill=GRAY, font=df)
        dy += 22
center_text(d, line_y, "右键菜单集成 选中文件即压即解 办公传文件更顺", get_font(20), GRAY)
d.rounded_rectangle([BORDER + 40, suit_y, W - BORDER - 40, suit_y + SUIT_H], radius=18, fill=(239, 246, 255))
d.text((BORDER + 60, suit_y + 18), "适合谁", fill=DARK, font=get_font(22, bold=True))
scs = ["办公白领", "学生党", "装机必备", "常收发压缩包的你"]
sx = BORDER + 60
sf = get_font(20)
for s in scs:
    w = d.textlength(s, font=sf) + 28
    if sx + w > W - BORDER - 60:
        sx = BORDER + 60
    d.rounded_rectangle([sx, suit_y + 60, sx + w, suit_y + 94], radius=14, fill="white", outline=BLUE, width=1)
    d.text((sx + 14, suit_y + 64), s, fill=BLUE, font=sf)
    sx += w + 14
bottom_bar(d, "只发夸克", "虚拟资料 无需物流 即装即用")
im.save(out / "03.png", "PNG")
print("03 saved", (out / "03.png").stat().st_size)

# ---------- 04 guide ----------
im, d = draw_board()
d.text((BORDER + 40, BORDER + 28), "发货指南", fill=DARK, font=get_font(44, bold=True))
d.text((BORDER + 40, BORDER + 28 + 56), "虚拟资料 只发夸克网盘 不发实物", fill=GRAY, font=get_font(24))
steps = [("1", "拍后提供链接", "夸克网盘链接发货 无需等待"), ("2", "不限时需提取码", "带文件名 永久有效反复下"), ("3", "即装即用", "exe双击安装右键即用"), ("4", "售后说明", "虚拟资料按需拍不包退换")]
STEP_H = 124
step_y, warn_y = stack([STEP_H * len(steps) + 22 * (len(steps) - 1), WARN_H], BORDER + 130, BAR_TOP - 40)
yy = step_y
for n, t, s in steps:
    d.rounded_rectangle([BORDER + 40, yy, W - BORDER - 40, yy + STEP_H], radius=18, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
    ncy = yy + (STEP_H - 48) // 2
    d.ellipse([BORDER + 60, ncy, BORDER + 108, ncy + 48], fill=BLUE)
    nf = get_font(28, bold=True)
    tw = d.textlength(n, font=nf)
    d.text((BORDER + 84 - tw // 2, ncy + 6), n, fill="white", font=nf)
    ty = yy + (STEP_H - 66) // 2
    d.text((BORDER + 130, ty), t, fill=DARK, font=get_font(26, bold=True))
    d.text((BORDER + 130, ty + 36), s, fill=GRAY, font=get_font(22))
    yy += STEP_H + 22
wy = warn_y
d.rounded_rectangle([BORDER + 40, wy, W - BORDER - 40, wy + WARN_H], radius=14, fill=(255, 251, 235), outline=(253, 230, 138), width=1)
d.text((BORDER + 60, wy + 12), "提醒", fill=(146, 64, 14), font=get_font(22, bold=True))
warn_font = get_font(16)
for j, ln in enumerate(wrap_text_fit("虚拟资料一经发货不退不换 请确认需要WinRAR再拍", warn_font, W - 2 * BORDER - 120, 2, d, label="提醒")):
    d.text((BORDER + 60, wy + 44 + j * 20), ln, fill=(120, 113, 108), font=warn_font)
# 底栏两行用 BAR_TOP 相对定位并留足行距。早先按 H-BORDER-68/-38 硬写，
# 24px 与 18px 两行的真实墨迹只差 3px，几乎连成一片。
d.rounded_rectangle([BORDER, BAR_TOP, W - BORDER, H - BORDER], radius=22, fill=(30, 41, 59))
d.text((BORDER + 40, BAR_TOP + 12), "只发夸克网盘", fill="white", font=get_font(24, bold=True))
d.text((BORDER + 40, BAR_TOP + 48), "不发其他盘 不发实物", fill=(203, 213, 225), font=get_font(18))
im.save(out / "04.png", "PNG")
print("04 saved", (out / "04.png").stat().st_size)
print("done", str(out))

