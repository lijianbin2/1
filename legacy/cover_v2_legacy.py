from PIL import Image, ImageDraw, ImageFont
import os
import pathlib

from xianyu_common import fit_font

W=H=1080
BLUE=(37,80,255); DEEP=(18,32,120); DARK=(24,32,54); GRAY=(95,110,135); WHITE=(255,255,255)

# 课时数集中声明，改数量只改这里；可用环境变量覆盖。
LESSONS = int(os.environ.get("XIANYU_WORKBUDDY_LESSONS", "37"))
LESSON_SHORT = f"{LESSONS}集"
LESSON_FULL = f"{LESSONS}课时"

def get_font(size, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    try: return ImageFont.truetype(p, size)
    except OSError: raise RuntimeError(f"无法加载字体：{p}") from None

def grad_bg(c1, c2):
    im = Image.new("RGB",(W,H),c1); d = ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; col=tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))
        d.line([(0,y),(W,y)],fill=col)
    return im

def deco(d, color):
    # translucent-look circles (solid light color, no alpha on RGB)
    for x,y,r in [(120,180,90),(960,240,130),(880,860,100),(180,900,70)]:
        d.ellipse([x-r,y-r,x+r,y+r],outline=color,width=3)

out = pathlib.Path(
    os.environ.get(
        "XIANYU_LEGACY_OUT",
        "D:/闲鱼/WorkBuddy智能体实战，打造个人AI效率系统",
    )
)
feats=[("01","智能体一站式","Skill知识库自动化"),("02","数字人全流程","形象声音口播视频"),("03","办公全场景","PPT数据剪辑飞书")]

def make(style, path):
    im = grad_bg((24,42,140),(52,110,255)) if style=="A" else grad_bg((235,242,255),(255,255,255))
    d = ImageDraw.Draw(im)
    deco(d, (120,150,255) if style=="A" else (190,210,250))
    card=[60,60,W-60,H-60]
    cardfill = WHITE if style=="B" else (246,248,255)
    d.rounded_rectangle(card,radius=36,fill=cardfill,outline=(200,212,245),width=2)
    # badge
    bf=get_font(28,True); bt=f"{LESSON_SHORT}全 · 智能体实战"
    bw=d.textlength(bt,font=bf)+56; bx=(W-bw)//2; by=120
    d.rounded_rectangle([bx,by,bx+bw,by+52],radius=26,fill=BLUE)
    d.text((bx+(bw-d.textlength(bt,font=bf))//2,by+10),bt,fill=WHITE,font=bf)
    # title
    tf=get_font(72,True); sf=get_font(38)
    t="WorkBuddy智能体实战"; s="打造个人AI效率系统"
    tw=d.textlength(t,font=tf); d.text(((W-tw)//2,200),t,fill=DARK if style=="B" else DEEP,font=tf)
    sw=d.textlength(s,font=sf); d.text(((W-sw)//2,296),s,fill=GRAY,font=sf)
    d.line([(W-220)//2,362,(W+220)//2,362],fill=BLUE,width=5)
    # 3 cards，从白色面板内边界反推宽度，避免第三张卡越出面板
    PAD=90
    GAP=20
    y0=400
    inner=(W-PAD)-PAD
    cw=(inner-GAP*2)//3
    if PAD+2*(cw+GAP)+cw > W-PAD:
        raise ValueError("特色卡片超出面板宽度")
    for i,(n,a,b) in enumerate(feats):
        x=PAD+i*(cw+GAP)
        fill=(238,243,255) if style=="B" else WHITE
        d.rounded_rectangle([x,y0,x+cw,y0+230],radius=22,fill=fill,outline=(37,80,255) if style=="A" else (205,218,250),width=3)
        nf=get_font(30,True); nw=d.textlength(n,font=nf)
        d.text((x+(cw-nw)//2,y0+22),n,fill=BLUE,font=nf)
        # 副标题和说明都用 fit_font：缩到下限仍放不下就直接报错。
        # 早先这里是手写 while，且 b 那段的 break 写在循环体里，
        # 只试一次 20px 就退出，放不下会静默溢出卡片。
        af,aw=fit_font(d,a,cw-24,30,bold=True,min_size=20)
        d.text((x+(cw-aw)//2,y0+66),a,fill=DARK,font=af)
        bs,bw2=fit_font(d,b,cw-24,22,min_size=16)
        d.text((x+(cw-bw2)//2,y0+120),b,fill=GRAY,font=bs)
        d.rounded_rectangle([x+24,y0+164,x+cw-24,y0+200],radius=18,fill=BLUE)
        mf=get_font(20,True); mt="一看就会" if i==0 else ("即学即用" if i==1 else "覆盖办公")
        mw=d.textlength(mt,font=mf); d.text((x+(cw-mw)//2,y0+172),mt,fill=WHITE,font=mf)
    # meta strip
    mtxt=f"{LESSON_FULL} · 目录实拍 · 小白可学 · 拍后提供链接"
    mf2=get_font(26); mw2=d.textlength(mtxt,font=mf2)
    d.text(((W-mw2)//2,680),mtxt,fill=GRAY,font=mf2)
    # info box fills middle blank
    d.rounded_rectangle([90,724,W-90,856],radius=22,fill=(238,243,255) if style=="B" else (232,238,255),outline=(37,80,255) if style=="A" else (205,218,250),width=2)
    il=[("拍后提供链接","拍后发夸克链接"),("多端可看","手机电脑平板随时学"),("小白友好",f"{LESSON_SHORT}从入门到实战")]
    for j,(h,s) in enumerate(il):
        ix=130+j*((W-180)//3)
        hf=get_font(26,True); d.text((ix,744),h,fill=BLUE,font=hf)
        sf2=get_font(22); d.text((ix,782),s,fill=GRAY,font=sf2)
    # bottom bar
    d.rounded_rectangle([60,H-220,W-60,H-60],radius=28,fill=(22,30,58))
    lf=get_font(34,True); d.text((110,H-190),"只发夸克",fill=WHITE,font=lf)
    rf=get_font(24); rt="虚拟资料 · 拍后发网盘链接 · 无需物流"
    rw=d.textlength(rt,font=rf); d.text((W-60-30-rw,H-140),rt,fill=(190,200,225),font=rf)
    im.save(path); print("saved",path)

make("A", str(out/"cover_A.png"))
make("B", str(out/"cover_B.png"))
