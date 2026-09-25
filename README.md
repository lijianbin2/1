# 闲鱼图文发布工具

这是一个面向虚拟资料项目的图文生产与闲鱼发布辅助工具。它负责：

- 核验项目素材和文件规模。
- 生成 4 张 `1080 × 1080` 的闲鱼商品图。
- 生成、校验和保存商品文案。
- 记录夸克私密分享的标题、链接和提取码。
- 配合 Playwright 完成浏览器中的上传和表单填写。

工具不会保存账号密码、验证码、Cookie 或网盘凭据，也不会自动点击闲鱼最终“发布”按钮。

## 不可违反的发布规则

1. 闲鱼正文只写商品内容、文件规模、适用人群和“拍后提供网盘链接”。
2. 闲鱼正文不能出现夸克链接、分享 ID、提取码、其他网盘链接或密码。
3. 标题和正文不写价格。价格只在闲鱼表单的“价格”字段填写。
4. 虚拟资料优先选择“无需邮寄”；不写“自动发货”、实物、快递或物流承诺。
5. 夸克分享信息单独交付，优先复制到剪贴板或单独发给买家。
6. 最终点击“发布”前，必须先向用户展示标题、价格、图片数量、分类和正文检查结果，并等待用户确认。

## 环境要求

- Windows
- Python 3.10+
- Pillow 10+
- Playwright 浏览器控制工具

安装和基础检查：

```powershell
cd "H:\Codex\闲鱼图文发布"
python -m pip install Pillow
python -m unittest discover -s tests -v
python -m py_compile cover_v2.py make_desc.py render_camera_basics.py render_codex55.py render_map_collection.py render_promo_music.py render_winrar_unified.py render_workbuddy.py xianyu_common.py
```

## 固定发布 SOP

每次任务严格按以下顺序执行，状态和交付物不要混在一起。

### 1. 核验源素材

确认项目名称、源目录、代表图片、文件总数和总体积。地图项目至少应有可读取的代表图片，例如：

```text
超高清晰世界地图.jpg
一亿像素中国地图.jpg
中国各省高清晰巨幅地图/中国.jpg
```

### 2. 生成四张商品图

地图素材合集使用：

```powershell
python render_map_collection.py `
  --root "M:\WebDAV\夸克\软件\高清一亿像素地图矢量图合集，超精细地理素材" `
  --out "D:\闲鱼\高清一亿像素地图矢量图合集，超精细地理素材"
```

脚本会生成：

```text
01.png  封面与项目卖点
02.png  目录与分类
03.png  使用收获与适合场景
04.png  购买前说明与交付方式
```

每张图都应通过 `1080 × 1080`、PNG 格式和视觉检查。目视检查重点是：文字没有出框、图片没有拉伸、四张图风格一致。

其他项目分别使用对应的 `render_*.py` 脚本。脚本列表见下方“脚本索引”。

### 3. 生成闲鱼正文

正文应包含：

- 项目名称和一句话介绍。
- 内容分类、文件格式、文件数量和体积等可核对信息。
- 适合人群和使用场景。
- `【说明】虚拟资料，拍后提供网盘链接。` 或同等准确表述。

正文示例：

```text
高清一亿像素地图矢量图合集，超精细地理素材

一套高清地图与地理设计素材合集，包含中国地图、世界地图、各省及区域地图、专题地图和多种可编辑源文件。

内容简介：
1. 高清地图：中国地图、世界地图、各省高清图及区域地图。
2. 专题素材：交通、自然、旅游、区域等地图分类。
3. 源文件格式：CDR、AI、PSD、EPS、PDF、PPT等。
4. 资料规模：共468个文件，约7.24GB，按目录分类整理。

适合需要地图素材、矢量源文件和地理设计参考的用户。

【说明】虚拟资料，拍后提供网盘链接。
```

正文文件只保存上述内容，不混入网盘分享块。

### 4. 单独制作夸克分享信息

分享信息必须独立保存或复制，格式固定为：

```text
标题：项目名称
夸克私密永久分享链接：https://pan.quark.cn/s/分享ID
提取码：四位提取码
```

注意：`make_desc.py` 的 `write_project()` 会把 `quark_block` 拼进 `desc.txt` 和 `闲鱼发布文案_直接复制.txt`。因此该文件是“完整交付包”，不能整段粘贴到闲鱼正文。实际发布时只复制正文中“拍后提供网盘链接”之前的商品内容；分享块单独交付。

### 5. Playwright 上传和填写

1. 打开闲鱼发布页并确认账号已登录。
2. 将四张图片复制到 Playwright 允许访问的工作区临时目录。
3. 点击“添加首图”，在文件选择器中一次选择 `01.png` 至 `04.png`。
4. 确认四张图都已出现在商品图区域。
5. 选择与项目匹配的可用分类。地图/电子资料项目优先选择平台允许网页发布的“电子资料”分类。
6. 填写正文和价格，例如 `1` 元。
7. 选择“无需邮寄”（页面提供时）。
8. 不在表单中输入夸克链接或提取码。

Playwright 上传器可能拒绝工作区之外的绝对路径。遇到 `File access denied` 时，不要改素材内容，只需把待上传文件复制到当前任务工作区内的临时目录，再重新选择文件。

### 6. 发布前复核

点击发布前逐项确认：

```text
标题：项目名称，不含价格
分类：电子资料或页面允许的匹配分类
图片：4 张，均为 01.png 至 04.png
价格：按用户要求填写
发货：无需邮寄（如适用）
正文：不含 pan.quark.cn、分享 ID、提取码
正文：不含百度、其他网盘、实物、快递、物流、自动发货
```

可以用以下命令检查正文关键词：

```powershell
$copy = Get-Content -Raw "D:\闲鱼\项目名\闲鱼正文_直接复制.txt"
$copy | Select-String -Pattern "pan\.quark\.cn|提取码|分享ID|百度|实物|快递|物流|自动发货"
```

没有输出才表示未命中这些禁止项。

### 7. 最终确认和发布

点击“发布”是代表用户向第三方平台公开发布商品的动作，必须在点击前再次确认：

> 即将以当前闲鱼账号发布该商品：标题为……，价格为……，共 4 张图片，分类为……。正文不包含夸克链接和提取码。

用户明确确认后：

1. 点击“发布”。
2. 等待成功提示、商品管理页或商品详情链接。
3. 记录商品链接或成功提示。
4. 将夸克链接和提取码作为独立交付信息发送，不回填到闲鱼正文。

状态定义：

| 状态 | 含义 |
| --- | --- |
| 已准备 | 图片、正文、分享信息已生成，尚未上传或发布 |
| 已上传 | 图片已传入闲鱼页面，尚未点击发布 |
| 已发布 | 页面出现成功提示或商品链接 |

## 脚本索引

| 脚本 | 用途 |
| --- | --- |
| `render_map_collection.py` | 高清地图矢量素材合集四张图 |
| `render_promo_music.py` | 宣传片背景音乐合集四张图 |
| `render_camera_basics.py` | 相机基础课程四张图 |
| `render_codex55.py` | Codex 办公课程四张图 |
| `render_workbuddy.py` | WorkBuddy 课程四张图 |
| `render_winrar_unified.py` | WinRAR 资料四张图 |
| `xianyu_common.py` | 字体、画板、换行、保存和图片校验公共函数 |
| `make_desc.py` | 标题、正文、分享块生成与规则校验 |
| `cover_v2.py` | 历史封面方案，仅供追溯 |

## 文案工具说明

`make_desc.py` 提供的常用 API：

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
```

`check_copy()` 会检查必需字段、禁止词和价格格式。`build_quark()` 只接受 `https://pan.quark.cn/s/` 开头的分享链接。

## 验证

```powershell
python -m unittest discover -s tests -v
python -m py_compile cover_v2.py make_desc.py render_camera_basics.py render_codex55.py render_map_collection.py render_promo_music.py render_winrar_unified.py render_workbuddy.py xianyu_common.py
```

检查输出图片：

```powershell
Get-ChildItem -LiteralPath "D:\闲鱼\项目名" -File |
    Where-Object { $_.Extension -eq ".png" } |
    Select-Object Name, Length
```

## Git 规则

当前工作分支为 `xianyu`：

```powershell
git switch xianyu
git pull --rebase origin xianyu
git status --short
git add README.md
git commit -m "docs: rewrite publishing workflow"
git push origin xianyu
```

不要提交以下内容：

- 夸克分享链接、提取码和网盘凭据。
- 浏览器用户目录、Cookie、登录态和验证码。
- 交付图片、Playwright 临时上传目录和本地缓存。
- 用户账号信息或订单信息。

`.gitignore` 已覆盖常见缓存、浏览器 profile、Playwright 临时文件和日志。

## 维护约定

- 新项目优先复用 `xianyu_common.py`，不要重复实现字体加载、画板绘制和换行。
- 新渲染脚本统一输出 `01.png` 至 `04.png`，并使用 `validate_png_files()` 校验。
- 任何新增文案都要同时更新“正文规则”和对应测试。
- 任何新增发布工具都要更新“固定发布 SOP”，尤其是文件上传、登录、最终发布确认和外部分享信息边界。
