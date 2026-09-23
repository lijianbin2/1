"""desc.txt + one-copy text generator (README section 3)."""
import pathlib, re

MARKER = '只发夸克'
DESC_NAME = 'desc.txt'
COPY_NAME = '闲鱼发布文案_直接复制.txt'
EX_DESC = 'Codex职场高效办公实战 55集 AI自动化赋能日常办公 只发夸克\n\n本套为55集完整视频教程，覆盖从模型配置到办公全场景自动化。\n\n内容简介：\n1. 基础入门 5节：课程介绍、软件安装登录、CCSwitch切国产/第三方模型、图片与音视频模型配置\n2. 模型实战 5节：gpt-image2/Seedream生图、Seedance生视频、豆包/edge语音生成\n3. 办公提效 6节：快速上手、批量整理文件、智能分析数据、商业文档与市场调研撰写\n4. 行业报表 10节：行业数据分析、电商周报/年报、降本增效洞察、研发交付报告与多行业PPT制作\n5. 视频与电商 15节：自动化剪辑、批量加字幕音乐、切片混剪、文稿生视频、产品套图流水线与数字人带货\n6. 飞书与知识库 14节：飞书多场景办公、CLI上手、云文档/会议/多维表、项目任务管理、Obsidian企业知识库与资讯归档\n\n适合职场办公、运营/产品/研发、电商视频创作者等希望用AI提效的人群，跟着实操即学即用。\n\n【说明】虚拟资料，只发夸克网盘，不发百度/实物，无需物流，拍后发网盘链接。\n'
EX_QUARK = '文件夹名：Codex职场高效办公实战，AI自动化赋能日常办公\n链接：https://pan.quark.cn/s/98d130a1f067\n提取码：UkmA\n'
QUARK_LABELS = ['文件夹名', '链接', '提取码']
FORBIDDEN = ['百度', '价格', '价钱', '实物', '快递', '物流', '元', '试看', '私聊']
REQUIRED = [MARKER] + QUARK_LABELS

def check_copy(title, body):
    NEG = tuple(chr(c) for c in (0x4E0D, 0x65E0, 0x975E, 0x6CA1, 0x52FF))
    STOP = tuple(chr(c) for c in (0x3002, 0xFF01, 0xFF1F)) + ("!", "?")
    def negated(text, k):
        j = k - 1
        while j >= 0 and j >= k - 8:
            c = text[j]
            if c in STOP:
                return False
            if c in NEG:
                return True
            j -= 1
        return False
    def hits(text, word):
        out = []
        s = 0
        while True:
            k = text.find(word, s)
            if k < 0:
                return out
            if not negated(text, k):
                out.append(k)
            s = k + len(word)
    bad = []
    for i, w in enumerate(FORBIDDEN):
        if hits(title, w):
            bad.append("forbidden[%d]-in-title" % i)
        if hits(body, w):
            bad.append("forbidden[%d]-in-body" % i)
    for i, w in enumerate(REQUIRED):
        if w not in title and w not in body:
            bad.append("required[%d]-missing" % i)
    return bad

def build_title(core, count_str):
    return core.strip() + " " + count_str.strip() + " " + MARKER

def build_body(title, intro, modules, audience):
    lines = EX_DESC.splitlines()
    hi = next(i for i, l in enumerate(lines)
              if l.strip().endswith(chr(0xFF1A)) and len(l.strip()) <= 8)
    ai = next(i for i, l in enumerate(lines) if l.startswith(chr(0x9002)))
    out = [title, '', intro, ''] + [lines[hi]] + list(modules) + ['', audience, '']
    out = out + lines[ai:]
    return chr(10).join(out)

def build_quark(folder, link, code):
    vals = [folder, link, code]
    out = []
    for i, l in enumerate(EX_QUARK.splitlines()):
        lab = re.split(r'[:\uFF1A]', l, maxsplit=1)[0]
        out.append(lab + chr(0xFF1A) + vals[i] if i < len(vals) else l)
    return chr(10).join(out)

def write_project(out_dir, title, body, quark_block):
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    full = title + chr(10) + chr(10) + body + chr(10) + chr(10) + quark_block + chr(10)
    (p / DESC_NAME).write_text(full, encoding='utf-8')
    (p / COPY_NAME).write_text(full, encoding='utf-8')
    bad = check_copy(title, body + chr(10) + quark_block)
    print("wrote %s violations=%s" % (str(p), bad))
    return bad

