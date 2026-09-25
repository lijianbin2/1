# 闲鱼图文发布工具

用于把虚拟资料项目整理成可交付的闲鱼商品素材：核验项目内容、生成四张 1080 × 1080 图、生成并校验文案，最后由用户在闲鱼页面完成上传和发布。

本仓库只处理素材生产和校验，不保存网盘凭据，也不会代替用户点击闲鱼最终发布按钮。

## 快速开始

环境要求：

- Windows
- Python 3.10+
- Pillow 10+

在仓库目录安装依赖并运行检查：

```powershell
python -m pip install Pillow
python -m unittest discover -s tests -v
python -m py_compile cover_v2.py make_desc.py render_camera_basics.py render_codex55.py render_promo_music.py render_winrar_unified.py render_workbuddy.py xianyu_common.py
```

生成宣传片背景音乐商品图：

```powershell
python render_promo_music.py
python render_promo_music.py --out "D:\闲鱼\宣传片背景音乐合集"
```

脚本默认输出四张 `01.png` 至 `04.png`，并校验文件存在、格式为 PNG、尺寸为 1080 × 1080。

## 项目结构

```text
.
├── xianyu_common.py             # 字体、画板、换行、保存和图片校验公共函数
├── make_desc.py                 # 文案组装、规则检查和双份文案落盘
├── render_promo_music.py        # 宣传片背景音乐合集四张图
├── render_camera_basics.py      # 相机基础课程四张图
├── render_codex55.py            # Codex 办公课程四张图
├── render_workbuddy.py          # WorkBuddy 课程四张图
├── render_winrar_unified.py     # WinRAR 商品四张图
├── cover_v2.py                  # 历史封面方案，仅供追溯
├── tests/                       # 文案工具的单元测试
└── README.md
```

## 发布流程

1. 在货源目录核对项目名称、集数、文件数量和版本。
2. 根据项目选择对应渲染脚本，生成 `01.png` 至 `04.png`。
3. 用 `make_desc.py` 组装标题、简介、适合人群和虚拟资料说明。
4. 运行 `check_copy()`，确认没有价格、其他网盘、自动发货或实物交付表述。
5. 将四张图片和经过检查的文案交给用户，由用户在闲鱼后台填写价格、发货方式并发布。
6. 用户下单后，再单独发送对应的夸克分享信息。

标准图片文件：

```text
01.png  封面与项目卖点
02.png  目录或内容分类
03.png  学习收获与适合人群
04.png  使用、交付和购买前说明
```

## 文案规则

标题和正文中不写价格。交付说明使用“拍后提供链接”一类准确表述，不写“自动发货”。本项目约定只使用夸克网盘，分享信息应在需要时单独发送给买家。

`make_desc.py` 会在写入前检查：

- 必需字段：只发夸克、文件夹名、链接、提取码
- 禁止词：百度、价格、价钱、实物、快递、物流、试看、私聊
- 货币格式：例如 `1 元`、`1.00元`、`￥1`

`write_project()` 校验通过后才会创建目录，并同时写入：

```text
desc.txt
闲鱼发布文案_直接复制.txt
```

两份文件必须保持字节一致。

## Python API

公共渲染函数位于 `xianyu_common.py`：

```python
from xianyu_common import draw_board, get_font, save_png, wrap_text

image, draw = draw_board()
font = get_font(24, bold=True)
lines = wrap_text("中文文案自动换行", font, 800, draw)
save_png(image, "output/01.png")
```

文案工具位于 `make_desc.py`：

```python
from make_desc import build_body, build_quark, build_title, check_copy

title = build_title("示例项目", "10集")
body = build_body(
    title,
    "完整视频教程，适合零基础学习。",
    ["1. 基础入门 3 节", "2. 实战应用 7 节"],
    "适合需要提升效率的用户",
)
quark = build_quark("示例项目", "https://pan.quark.cn/s/abc123", "abcd")
violations = check_copy(title, f"{body}\n\n{quark}")
assert violations == []
```

## 验证

```powershell
python -m unittest discover -s tests -v
python -m py_compile cover_v2.py make_desc.py render_camera_basics.py render_codex55.py render_promo_music.py render_winrar_unified.py render_workbuddy.py xianyu_common.py
```

生成图片后检查输出目录：

```powershell
Get-ChildItem -LiteralPath "D:\闲鱼\项目名" -File | Select-Object Name, Length
```

新生成的 WinRAR 版本可以使用空版本号隐藏版本后缀：

```powershell
python render_winrar_unified.py --version=
```

## Git

当前工作分支为 `xianyu`：

```powershell
git switch xianyu
git pull --rebase origin xianyu
git status --short
git add .gitignore README.md make_desc.py render_promo_music.py xianyu_common.py tests
git commit -m "docs: refresh tooling and README"
git push origin xianyu
```

不要提交网盘提取码、浏览器用户目录、Python 缓存、交付图片或本地临时文件。`.gitignore` 已覆盖这些常见产物。

## 维护

新项目优先复用 `xianyu_common.py`，不要再复制字体加载、画板绘制和文字换行代码。旧版 `cover_v2.py` 不符合当前四图交付规范，仅作为历史参考保留。
