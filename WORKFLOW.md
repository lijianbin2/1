# 闲鱼图文项目工作流程

这份文档是项目唯一的发布流程说明。目标是让任何一个新项目都能按照同一套步骤完成素材核验、四张商品图生成、闲鱼正文生成、夸克分享信息交付和发布前复核。

## 1. 不可违反的规则

1. 闲鱼商品正文不能出现网盘 URL、分享 ID、提取码或密码。
2. 夸克链接和提取码只作为独立交付信息，不能提交到 Git，也不能粘贴到闲鱼正文。
3. 最终点击“发布”前必须得到用户明确确认。
4. 登录、扫码、短信验证码和账号安全操作由用户本人完成。
5. 没有核验过的文件数量、体积、格式不能写进正文。
6. 四张商品图必须先通过尺寸和文件完整性校验，再上传闲鱼。
7. 商品图和文案里的每一个数量都必须来自 `verify_source.py` 的实测结果，
   不允许手打，也不允许沿用上一轮的数字。

## 2. 项目状态

每个项目只维护以下状态，状态变化必须同步记录：

```text
待核验
素材已核验
数量已核验
图片已生成
文案已生成
分享信息已准备
表单已填写
待用户确认
已发布
已交付
```

“图片已上传”不等于“已发布”，“分享信息已准备”不等于“已交付”。
“数量已核验”要求 `verify_source.py` 退出码为 0，且商品图和正文使用同一份
统计结果。

## 3. 开始前收集信息

开始前一次性确认：

| 信息 | 用途 | 来源 |
| --- | --- | --- |
| 项目名称 | 标题、正文、输出目录、分享标题 | 用户或素材目录名 |
| 素材源目录 | 统计文件和生成预览图 | 用户 |
| 商品图数量 | 通常为 4 张 | 项目约定 |
| 闲鱼价格 | 页面价格字段 | 用户 |
| 闲鱼分类 | 页面分类字段 | 页面实际选项 |
| 发货方式 | 虚拟资料通常选择“无需邮寄” | 页面实际选项 |

已经存在于源目录、输出目录或本地交付文件中的信息，不要要求用户再次提供。

## 4. 核验源素材

### 用 `verify_source.py` 统计

这是唯一权威的统计入口，不要用 PowerShell 手数，也不要凭目录名推断：

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名"
```

输出包含文件总数、总体积、一级分类数量和扩展名分布，并标出目录名标注与
实际文件数不一致的分类。

### 同时核对文案

文案写好后再跑一次，把数量声明一起校验：

```powershell
python verify_source.py `
  --root "M:\WebDAV\夸克\软件\项目名" `
  --copy "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt"
```

退出码非 0 表示存在问题，必须先改正文或源素材，不能继续发布。工具会分别
报告标题数量、正文数量、明细合计、文件总数和体积的偏差。

### 需要人工确认的差异

工具退出码非 0 有两种情况，处理方式不同：

| 情况 | 处理方式 |
| --- | --- |
| 目录名标注与实际文件数不符 | 以实际文件数为准，并在正文写实际数量 |
| 文案数量与实际文件数不符 | 以实际文件数为准，改文案和商品图 |

如果实际文件数明显少于预期，先检查是否有文件同步失败或被误删，再决定
文案怎么写。不要为了对上目录名而虚报数量。

### 手工复核（可选）

需要交叉验证时再执行：

```powershell
$root = "M:\WebDAV\夸克\软件\项目名"
$files = Get-ChildItem -LiteralPath $root -File -Recurse
$files.Count
($files | Measure-Object -Property Length -Sum).Sum
$files | Group-Object Extension | Sort-Object Count -Descending
```

同时确认：

- 至少有可用于预览的 JPG、PNG 或其他可读图片。
- 文件数量和体积与准备写入正文的内容一致。
- 源文件格式与项目实际内容一致。
- 源目录中的敏感文件、网盘凭据和无关文件不会被上传。

统计结果没有确认前，不进入图片生成和文案写作。

## 5. 生成商品图

### 标准入口

所有公开入口都支持 `--out`，导入时不会创建目录或写入图片：

```text
render_map_collection.py
render_promo_music.py
render_camera_basics.py
render_codex55.py
render_workbuddy.py
render_winrar_unified.py
cover_v2.py
```

地图项目：

```powershell
python render_map_collection.py `
  --root "M:\WebDAV\夸克\软件\项目名" `
  --out "D:\闲鱼\项目名"
```

宣传片背景音乐项目：

```powershell
python render_promo_music.py --out "D:\闲鱼\项目名"
```

相机基础课程项目：

```powershell
python render_camera_basics.py --out "D:\闲鱼\项目名"
```

历史课程和 WinRAR 项目：

```powershell
python render_codex55.py --out "D:\闲鱼\项目名"
python render_workbuddy.py --out "D:\闲鱼\项目名"
python render_winrar_unified.py --version "v7.23" --out "D:\闲鱼\项目名"
python cover_v2.py --out "D:\闲鱼\项目名"
```

### 输出约定

每套图文使用固定文件名：

```text
01.png  封面和核心卖点
02.png  目录、分类或文件详情
03.png  使用收获和适用场景
04.png  购买前说明和交付方式
```

脚本生成后必须检查：

```powershell
$out = "D:\闲鱼\项目名"
Get-ChildItem -LiteralPath $out -Filter "*.png" |
    Select-Object Name, Length
```

必须同时满足：

- 文件名为 `01.png` 至 `04.png`。
- 每张图片都是 PNG。
- 每张图片都是 `1080 × 1080`。
- 图片可以完整解码，不是损坏或截断文件。
- 文字没有出框、重叠或被裁切。
- 图片预览没有明显拉伸、黑边或比例失真。

公共校验函数为：

```python
from xianyu_common import validate_png_files

problems = validate_png_files(r"D:\闲鱼\项目名", size=(1080, 1080))
if problems:
    raise RuntimeError("商品图校验失败")
```

### 图上数量必须可推导

渲染脚本里不允许出现手打的数量。分类数量集中在数据表里，总数由它求和得出：

```python
import render_promo_music as promo

assert promo.TOTAL_TRACKS == sum(
    int(count.rstrip("首")) for _, count, _ in promo.CATEGORIES
)
```

`tests/test_render_promo_music.py` 会扫描渲染脚本源码，发现 `CATEGORIES`
数据表以外的硬编码"数字+首"就让测试失败。修改分类数量时只改数据表，
不要在文案字符串里单独写数字。

### 历史实现说明

原课程和 WinRAR 绘图代码已移动到 `legacy/` 目录，由对应的公开入口通过 `legacy_runner.py` 显式调用。公开入口负责命令行参数、输出目录和导入安全；旧实现仍存在代码重复，后续可以逐个迁移到 `xianyu_common.py`，但不能绕过公开入口直接运行 `legacy/` 下的文件。

## 6. 生成闲鱼正文

正文只描述项目内容、适合人群、使用方式和交付方式，不包含真实分享信息。

推荐结构：

```text
项目名称

一句话介绍

内容简介：
1. 内容分类
2. 文件格式
3. 已核验的数量和体积

适合人群和使用场景。

【说明】虚拟资料，拍后提供网盘链接。
```

正文禁止出现：

- `pan.quark.cn` 或其他 URL。
- “分享 ID”“提取码”“密码”等交付字段。
- 价格、货币金额或未确认的优惠信息。
- 百度网盘、自动发货、实物、快递、物流等不符合项目实际的说法。

### 使用 `make_desc.py`

`make_desc.py` 只负责文本生成、校验和写入，不负责浏览器操作。

```python
from make_desc import build_quark, build_title, check_public_copy, write_project

title = build_title("项目名称", "10集")
body = "只发夸克网盘\n\n内容简介：\n1. 已核验内容"
quark_block = build_quark(
    "项目名称",
    "https://pan.quark.cn/s/REPLACE_ME",
    "abcd",
)

violations = check_public_copy(title, title + "\n\n" + body)
if violations:
    raise RuntimeError("闲鱼正文校验失败")

write_project(r"D:\闲鱼\项目名", title, body, quark_block)
```

输出文件语义：

```text
desc.txt
  完整交付包：标题 + 闲鱼正文 + 夸克分享块

闲鱼发布文案_直接复制.txt
  公开正文：标题 + 闲鱼正文，不含链接、提取码和分享字段
```

因此：

- 上传闲鱼时只使用 `闲鱼发布文案_直接复制.txt`。
- `desc.txt` 只能作为本地完整交付记录。
- 不能因为两个文件都存在，就把 `desc.txt` 整段复制到闲鱼。

### 本地正文检查

```powershell
$copy = Get-Content -Raw "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt"
$copy | Select-String -Pattern "https?://|pan\.quark\.cn|提取码|分享\s*ID|密码|百度|自动发货|实物|快递|物流|价格|价钱"
```

没有输出，才表示没有命中这些禁止内容。

## 7. 准备夸克分享信息

在夸克网盘中找到同名文件夹，确认分享类型为私密永久分享后，单独整理以下三项：

```text
标题：项目名称
分享链接：实际链接
提取码：四位提取码
```

交付规则：

1. 标题、链接和提取码一次性复制到剪贴板或本地临时文件。
2. 分享信息可以和商品交付一起发给用户，但不能进入闲鱼正文。
3. 不把真实链接、提取码、网盘 Cookie 或登录态写入代码、测试、工作流和 Git 历史。
4. 分享创建失败、链接过期或提取码不匹配时，重新核验分享状态，不继续声称已经准备完成。

## 8. Playwright 发布

### 打开和登录

1. 打开闲鱼发布页。
2. 确认当前浏览器已经登录正确账号。
3. 如果出现扫码、短信验证码或安全验证，暂停并请用户本人完成。

### 上传前

1. 确认输出目录存在四张 PNG。
2. 运行 `validate_png_files()`。
3. 确认正文文件是 `闲鱼发布文案_直接复制.txt`。
4. 确认正文检查无输出。
5. 确认分享信息独立保存，但不要把它带入正文。

如果浏览器拒绝访问 D 盘或其他外部目录，将四张图片复制到当前工作区内的临时目录后重新选择。只复制文件，不修改图片内容。

### 填写表单

1. 上传 `01.png`、`02.png`、`03.png`、`04.png`。
2. 确认页面显示四张图片均已上传。
3. 填写标题，不加入价格。
4. 填写正文，只使用公开正文文件内容。
5. 填写用户确认的价格。
6. 选择页面实际提供的匹配分类。
7. 虚拟资料选择“无需邮寄”（页面提供时）。
8. 不填写夸克链接、提取码或其他网盘凭据。

### 页面复核

```text
账号：当前登录账号
标题：项目名称
图片：4 张
分类：页面允许的匹配分类
价格：用户确认的价格
发货：无需邮寄（如适用）
正文：不含 URL、分享 ID、提取码
```

## 9. 最终确认与发布

点击“发布”会代表用户向第三方平台公开发布商品。点击前必须展示摘要并等待明确确认：

```text
即将以当前闲鱼账号发布：
标题：项目名称
分类：电子资料
价格：用户确认价格
图片：4 张
发货：无需邮寄
正文：不包含夸克链接和提取码
```

用户确认后：

1. 点击“发布”。
2. 等待成功提示、商品管理页或商品详情链接。
3. 记录实际成功提示或商品链接。
4. 再单独交付夸克分享标题、链接和提取码。

如果用户没有明确确认，停在“待用户确认”，不得点击“发布”。

## 10. 故障处理

| 问题 | 处理方式 |
| --- | --- |
| 源素材不存在 | 停止生成，回到素材核验 |
| `verify_source.py` 退出码非 0 | 按报告逐项改正文或源素材，改完重跑，不带着偏差发布 |
| 目录名标注与实际文件数不符 | 以实际文件数为准，不为了对上目录名而虚报数量 |
| 文件统计与正文不一致 | 重新统计并改正文，不猜测 |
| 图片缺失、损坏或尺寸错误 | 修复生成脚本或重新生成四张图 |
| 文字重叠或出框 | 调整布局后重新生成并目视检查 |
| 浏览器拒绝外部路径 | 复制到工作区临时目录后重新上传 |
| 页面要求扫码或验证码 | 暂停，请用户本人完成 |
| 页面没有合适分类 | 选择页面实际允许的分类，不虚构选项 |
| 正文出现链接或提取码 | 清空正文，改用公开正文文件重新填写 |
| 未得到发布确认 | 停在“待用户确认” |
| 发布后没有成功提示 | 保留当前页面，报告实际状态，不声称发布成功 |
| 夸克分享无法访问 | 重新核验私密永久分享状态 |

## 11. 代码验证和 Git

提交前运行：

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
git diff --check
```

确认没有把浏览器 profile 或凭据带进版本库：

```powershell
git ls-files | Select-String "chrome-profile|Cookie|playwright"
rg -n -i "pan\.quark\.cn/s/[0-9a-zA-Z]{10,}|提取码[:：]\s*[0-9a-zA-Z]{4}" --glob "*.py" --glob "*.md" .
```

两条命令都应该没有输出。`.gitignore` 已覆盖 `.chrome-profile-*`，但浏览器
profile 体积很大且含登录态，不要留在项目目录里，用完删掉或移到别处。

如果本机安装了 Ruff，再运行：

```powershell
python -m ruff check .
```

提交时只加入：

- 源代码。
- 测试。
- `WORKFLOW.md`。

不要加入：

- 真实夸克链接、提取码和网盘凭据。
- 交付图片、浏览器 profile、Cookie、登录态和验证码。
- Playwright 临时目录、日志、缓存和本地输出目录。

当前分支为 `xianyu`：

```powershell
git switch xianyu
git pull --rebase origin xianyu
git status --short
git add <本次修改的源码和测试> WORKFLOW.md
git commit -m "refactor: audit project and rewrite workflow"
git push origin xianyu
```

提交后确认：

```powershell
git status --short
git log -1 --oneline
```

预期状态是工作区干净，最新提交已经出现在 `origin/xianyu`。
