# 闲鱼图文发布

闲鱼虚拟资料商品的标准生产与交付手册，覆盖收料核验、文案编写、四张图文生成、质量检查、本地落盘、夸克分享和 Git 归档。

本仓库只沉淀可复用的规范与脚本。具体货源在 M 盘，交付物在 D 盘。脚本只准备和校验发布素材，不点击闲鱼最终发布；用户确认后完成手机扫码发布。

## 1. 仓库边界

- 仓库目录：`H:/Codex/闲鱼图文发布`
- 工作分支：`xianyu`
- 远端：`origin/xianyu`
- 禁止把 `main` 合并或变基到 `xianyu`
- 货源目录：`M:/WebDAV/夸克`
- 交付目录：`D:/闲鱼/<项目名>`
- 闲鱼发布页：`https://www.goofish.com/publish`

`main` 与本项目无关。开始工作前必须确认当前分支是 `xianyu`；提交前执行 `git pull --rebase origin xianyu`。

## 2. 发布铁律

以下规则适用于标题、四张图片、`desc.txt`、一键复制文案和聊天回复：

1. 只分享夸克网盘，不发百度、阿里云盘等其他网盘。
2. 标题、图文和文案不写价格；闲鱼后台价格由用户手动填写为 `1元`。
3. 不写“图1图2见图”“试看片段私聊”等占位或引流话术。
4. 商品文案只描述资料内容，不加入给自己看的操作备注。
5. 夸克分享必须带文件名、永久有效、需要提取码，并设置为私密分享。
6. 每个项目只保留 `01.png` 至 `04.png`、`desc.txt` 和 `闲鱼发布文案_直接复制.txt`。
7. 分享块固定为三行：文件夹名、链接、提取码。
8. 不得声称自动发货。脚本不点击最终发布；价格、图片上传、文案粘贴和发布确认由用户完成。

## 3. 标准流水线

### 第一步：收料与核验

- 记录用户给出的项目原名、集数或文件数、版本和截图。
- 在 M 盘查找同名货源，核对文件名、扩展名、集数和总大小。
- 教程按 `M:/WebDAV/夸克/教程` 查找，软件按 `M:/WebDAV/夸克/软件` 查找。
- 缺集、缺文件或名称不一致时先补货源，不带病制作。

### 第二步：生成文案

- 教程标题格式：`<教程原名> <集数> 只发夸克`
- 软件标题格式：`<软件名> <版本与位数> 只发夸克`
- 正文依次包含：内容简介、模块与集数分布、适合人群、虚拟资料说明。
- 夸克信息单独放在正文末尾，保持三行格式。

### 第三步：生成四张图片

每个项目固定生成四张 1080 x 1080 PNG：

| 文件 | 内容 |
|---|---|
| `01.png` | 封面：项目名、核心卖点、交付方式 |
| `02.png` | 目录：模块、章节与集数分布 |
| `03.png` | 收获与适合人群 |
| `04.png` | 购买前说明、使用方式与交付提醒 |

不添加实拍图、聊天截图、二维码、水印或未经用户确认的品牌素材。

### 第四步：质量检查

- 货源文件数、集数、版本与项目台账一致。
- 四张图片齐全，尺寸均为 1080 x 1080，顺序为 01 至 04。
- 文字无错字、乱码、出框、截断和重叠；徽章宽度随文字自适应。
- 标题、图片和文案中没有价格，也没有其他网盘或虚假发货承诺。
- `desc.txt` 与 `闲鱼发布文案_直接复制.txt` 内容一致。
- 夸克分享为私密、永久、需提取码，文件数与货源一致。

### 第五步：本地落盘

```text
D:/闲鱼/<项目名>/
  01.png
  02.png
  03.png
  04.png
  desc.txt
  闲鱼发布文案_直接复制.txt
```

同一项目使用一个扁平目录，不建日期、版本或素材子目录。重新生成前先核对现有文件，避免把旧版图片与新版文案混在一起。

### 第六步：创建夸克分享

1. 把已核验的货源上传或同步到夸克对应目录。
2. 创建私密分享，选择永久有效并设置提取码。
3. 分享标题使用完整项目名，不使用缩写或“资料合集”等模糊名称。
4. 用分享详情再次核对文件数、大小、永久状态和提取码。
5. 将结果写成三行分享块，并登记到项目台账。

### 第七步：手动发布与归档

1. 把闲鱼发布页链接发给用户。
2. 用户手动上传四张图片、填写 `1元`、粘贴一键复制文案并发布。
3. 用户拍下后，由用户把三行夸克分享块发给买家。
4. 清理临时截图和中间文件。
5. 在 `xianyu` 分支提交、拉取变基并推送。

## 4. 文案规范

### 标题

```text
Codex职场高效办公实战 55集 AI自动化赋能日常办公 只发夸克
```

标题保留用户提供的项目原名，不擅自改课程名，不添加价格或促销词。

### desc.txt

```text
<标题>

<一段简洁的课程或软件说明>

内容简介：
1. <模块名称> <数量>：<内容>
2. <模块名称> <数量>：<内容>

适合<目标人群>，适合有<具体需求>的用户。

【说明】虚拟资料，只发夸克网盘，拍后发网盘链接。

文件夹名：<完整项目名>
链接：https://pan.quark.cn/s/<share-id>
提取码：<passcode>
```

`闲鱼发布文案_直接复制.txt` 与 `desc.txt` 保持完全相同。新项目优先使用 `make_desc.py` 生成和自检，不手工维护两份内容。

### 夸克分享块

```text
文件夹名：Codex职场高效办公实战，AI自动化赋能日常办公
链接：https://pan.quark.cn/s/98d130a1f067
提取码：UkmA
```

分享块之外不再重复链接和提取码。

## 5. 图片规范

| 项目 | 规范 |
|---|---|
| 尺寸 | 1080 x 1080 |
| 格式 | PNG，RGB |
| 主色 | `#2F5DFF` |
| 深色文字 | `#1E293B` |
| 次级文字 | `#64748B` |
| 浅色卡片 | `#F1F5F9` |
| 外框 | 38 px |
| 内圆角 | 32 px |
| 正文字体 | `C:/Windows/Fonts/msyh.ttc` |
| 粗体字体 | `C:/Windows/Fonts/msyhbd.ttc` |

版式以清晰、可信、可扫描为先。文字必须留在安全区内，徽章按实际文字宽度加内边距，模块卡片之间保持固定间距。缺少微软雅黑字体时应直接报错，不允许静默降级为无法显示中文的默认字体。

## 6. 脚本说明

### 可直接运行的脚本

| 脚本 | 用途 | 输出 |
|---|---|---|
| `render_codex55.py` | 生成 Codex 55 集项目的 01 至 04 | `D:/闲鱼/Codex职场高效办公实战，AI自动化赋能日常办公` |
| `render_workbuddy.py` | 生成 WorkBuddy 37 集项目的 01 至 04 | `D:/闲鱼/WorkBuddy智能体实战，打造个人AI效率系统` |
| `render_winrar_unified.py` | 生成 WinRAR 项目的 01 至 04 | `D:/闲鱼/WinRAR <版本>解压缩工具` |
| `render_camera_basics.py` | 生成相机基础课程 41 集的 01 至 04 | `D:/闲鱼/相机基础入门课，光圈快门曝光度一次搞懂` |

在仓库目录运行：

```powershell
python render_codex55.py
python render_workbuddy.py
python render_winrar_unified.py
python render_winrar_unified.py --version=v7.23
python render_winrar_unified.py --version=
```

`render_winrar_unified.py` 默认版本为 `v7.23`；传入空的 `--version=` 可隐藏版本号并使用不带版本号的输出目录。

上述脚本是项目专用脚本，历史脚本的默认输出路径写在代码中。运行前必须确认目标目录；`render_camera_basics.py` 支持 `--out` 指定临时或交付目录。

### 公共库

`xianyu_common.py` 为新项目提供公共能力：

- `get_font`：加载微软雅黑字体，可选择严格失败。
- `draw_board`：生成蓝框白底画板。
- `wrap_text`：按像素宽度逐字换行。
- `badge_geometry`：计算徽章宽度和高度。
- `save_png`：创建目录、保存 PNG 并输出文件大小。
- `check_text_rules`：执行禁用词和必需词检查。

新渲染脚本应导入该公共库，不再复制字体、画板和换行样板。

### 文案生成器

`make_desc.py` 提供：

- `build_title`：生成标准标题。
- `build_body`：组装不含标题的简介、模块、人群和说明，标题由 `write_project` 统一写入。
- `build_quark`：生成三行夸克分享块。
- `check_copy`：检查价格词、错误交付词和必需字段。
- `write_project`：同时写入 `desc.txt` 与 `闲鱼发布文案_直接复制.txt`。

示例：

```python
from make_desc import build_body, build_quark, build_title, write_project

title = build_title("Codex职场高效办公实战", "55集 AI自动化赋能日常办公")
body = build_body(
    title,
    "本套为55集完整视频教程，覆盖从模型配置到办公全场景自动化。",
    [
        "1. 基础入门 5节：课程介绍、软件安装与模型配置",
        "2. 模型实战 5节：生图、生视频与语音生成",
    ],
    "适合职场办公、运营、产品、研发和视频创作者",
)
quark = build_quark(
    "Codex职场高效办公实战，AI自动化赋能日常办公",
    "https://pan.quark.cn/s/98d130a1f067",
    "UkmA",
)
violations = write_project(
    "D:/闲鱼/Codex职场高效办公实战，AI自动化赋能日常办公",
    title,
    body,
    quark,
)
assert violations == []
```

### 旧版参考

`cover_v2.py` 是 WorkBuddy 封面方案的历史版本，只输出 `cover_A.png` 和 `cover_B.png`，不符合当前 `01.png` 至 `04.png` 的交付规范。新项目不要运行或复制该脚本；保留它仅用于追溯旧版设计。

## 7. 验证

### Python 语法

```powershell
python -m py_compile cover_v2.py make_desc.py render_camera_basics.py render_codex55.py render_winrar_unified.py render_workbuddy.py xianyu_common.py
```

### 文案检查

调用 `make_desc.check_copy()` 时，返回值必须为空列表：

```python
from make_desc import check_copy

assert check_copy(
    "示例项目 10集 只发夸克",
    "只发夸克网盘\n文件夹名：示例项目\n链接：https://pan.quark.cn/s/example\n提取码：abcd",
) == []
```

### 图片检查

```powershell
python -c "from pathlib import Path; from PIL import Image; p=Path(r'D:/闲鱼/项目名'); files=[p/f'{i:02d}.png' for i in range(1,5)]; assert all(f.is_file() for f in files); assert all(Image.open(f).size==(1080,1080) for f in files); print('images-ok')"
```

### 文案一致性

```powershell
python -c "from pathlib import Path; p=Path(r'D:/闲鱼/项目名'); a=(p/'desc.txt').read_bytes(); b=(p/'闲鱼发布文案_直接复制.txt').read_bytes(); assert a==b; print('copy-ok')"
```

### 交付目录

```powershell
Get-ChildItem -LiteralPath "D:/闲鱼/项目名" -File | Select-Object Name, Length
```

标准交付目录中应只有四张 PNG 和两份 UTF-8 文本文件。用于比较封面的 `封面-优化版*.png` 属于临时素材，不纳入标准交付目录。

## 8. Git 工作流

### 网络代理

本仓库的 Git 网络访问使用 Windows 当前系统代理。代理地址只写入仓库级 `.git/config`，不写进远端 URL，也不修改全局 Git 配置：

```powershell
git config --local http.proxy <当前系统代理地址>
git config --local https.proxy <当前系统代理地址>
```

系统代理地址变化后，重新读取 Windows 系统代理并同步以上两个仓库级配置。推送前可用 `git config --local --get-regexp "^(http|https)\.proxy$"` 检查当前值。

开始前：

```powershell
git switch xianyu
git status --short --branch
git pull --rebase origin xianyu
```

提交时只暂存本次任务涉及的文件：

```powershell
git add README.md
git commit -m "docs: rewrite publishing workflow"
git pull --rebase origin xianyu
git push origin xianyu
```

不要提交 `D:/闲鱼` 的交付物、M 盘货源、临时截图、网盘凭据或无关文件。不要使用 `git reset --hard`，除非用户明确要求回退。

## 9. 项目台账

台账记录业务状态，不代替每次交付时的实测。`D盘状态` 以当次运行 `Get-ChildItem D:/闲鱼` 的结果为准。

| 项目 | 规格 | 分享 | 状态 |
|---|---|---|---|
| AI写作全链路教程 | 20集 | — | 历史图文已交付，D盘当前无此目录 |
| AI入门大白话教程 | 19集 | — | 历史图文已交付，D盘当前无此目录 |
| AI+自媒体工业化实战课 | 21集 | — | 历史图文已交付，D盘当前无此目录 |
| PLC编程入门精通全套教程 | 73节 | — | 历史图文已交付，D盘当前无此目录 |
| 即梦 Seedance 2.0 动漫短剧视频教程大合集 | 合集 | — | 历史图文已交付，D盘当前无此目录 |
| AI漫剧制作全流程 | 60集 | — | 历史图文已交付，D盘当前无此目录 |
| WorkBuddy多场景AI办公实战 | 36集 | `a21e9f52bcf5 / jrvt` | 历史图文已交付，D盘当前无此目录 |
| AI智能体提效实战课 | 61集 | — | 历史图文已交付，D盘当前无此目录 |
| Adobe+达芬奇官方音效库合集 | 27大类 | `f696934d9eb0 / j4Fb` | D盘图文与文案存在 |
| Codex职场高效办公实战 | 55集 | `98d130a1f067 / UkmA` | 历史图文已交付，D盘当前无此目录 |
| WorkBuddy智能体实战，打造个人AI效率系统 | 37集 | 待补 | 历史图文已交付，D盘当前无此目录 |
| WinRAR v7.23 64位单文件版 | 约 4.1 MB | 暂无 | 统一渲染脚本已入库，D盘当前无此目录 |
| AI视频制作全攻略（豆包+即梦+剪映）从入门到精通实战课程 | 79 MP4 + 1 PDF，约 8.7 GB | `10378614ce30 / 8Fsq` | M盘货源存在，永久分享已建；D盘当前无此目录 |
| 相机基础入门课，光圈快门曝光度一次搞懂 | 41 MP4，约 3.13 GB | `f48ce609b9b7 / RS2Y` | M盘货源存在，永久私密分享已建；D盘图文与文案已生成 |
| IDM下载加速器 | 软件 | — | D盘图文与文案存在 |
| DaVinci Resolve Studio 21 | 软件 | — | D盘图文与文案存在 |
| 少儿编程课程集合 | 合集 | — | D盘图文与文案存在 |

## 10. 维护记录

- 2026-09-24：全文重写；按当前仓库、货源和 D 盘实测状态重新整理规范、脚本说明、验证命令与项目台账。
- 2026-09-24：新增相机基础入门课 41 集的图文生成脚本与交付记录，生成 01 至 04 图片、两份文案并创建永久私密分享。
- 2026-09-23：合入统一版 WinRAR 渲染脚本、公共库和文案生成器；台账补充 WinRAR 与 AI 视频课程。
- 2026-09-17：重写旧版流程，修复章节编号并明确 `main` 与 `xianyu` 的分支边界。
