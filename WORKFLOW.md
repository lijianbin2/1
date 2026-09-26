# 闲鱼图文发布工作流程

这份文档是本项目唯一的发布流程说明。目标是任何一个新项目都能按同一套步骤
走完：核验素材 → 生成四张图 → 生成正文 → 备好分享信息 → 填表 → 确认发布。

核心原则：**数字必须实测，文案必须可复制，发布必须先确认。**

## 1. 硬规则

1. 闲鱼正文不能出现网盘 URL、分享 ID、提取码或密码。
2. 夸克链接和提取码只作为独立交付信息，不进正文、不进 Git、不进代码和测试。
3. 点击"发布"前必须得到用户明确确认。
4. 登录、扫码、短信验证码、安全验证由用户本人完成。
5. 没核验过的文件数量、体积、格式不能写进正文和商品图。
6. 四张图必须通过尺寸和完整性校验才能上传。
7. 用户已经给过的信息（项目名、源目录、价格、素材统计）不要重复索要。

## 2. 项目状态

```text
待核验 → 素材已核验 → 图片已生成 → 文案已生成
      → 分享信息已准备 → 表单已填写 → 待用户确认 → 已发布 → 已交付
```

"图片已上传"不等于"已发布"，"分享信息已准备"不等于"已交付"。

## 3. 收集信息

开工前一次性确认，缺项才问：

| 信息 | 来源 |
| --- | --- |
| 项目名称 | 用户或素材目录名 |
| 素材源目录 | 用户 |
| 闲鱼价格 | 用户 |
| 闲鱼分类 | 页面实际选项 |
| 发货方式 | 虚拟资料通常"无需邮寄" |

## 4. 核验素材（唯一统计入口）

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名"
```

输出文件总数、总体积、一级分类数量、扩展名分布。**不要用 PowerShell 手数，
不要凭目录名推断。** 退出码非 0 表示目录名标注与实际文件数不符，以实际为准。

文案写好后再连同数量声明一起校验：

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名" --copy "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt"
```

非 0 退出就按报告改正文或源素材，不带着偏差往下走。实际文件数明显少于预期时，
先查同步是否失败，不要为了对上目录名而虚报数量。

## 5. 生成四张图

七个公开入口都支持 `--out`，导入时不产生任何副作用：

```text
render_map_collection.py   地图素材（自动读取源目录统计文件数和体积）
render_promo_music.py      宣传片背景音乐
render_camera_basics.py    相机基础课程
render_codex55.py          Codex 办公课程
render_workbuddy.py        WorkBuddy 智能体课程
render_winrar_unified.py   WinRAR 工具
cover_v2.py                WorkBuddy 双封面
```

```powershell
python render_map_collection.py --root "M:\WebDAV\夸克\软件\项目名" --out "D:\闲鱼\项目名"
python render_promo_music.py --out "D:\闲鱼\项目名"
python render_camera_basics.py --out "D:\闲鱼\项目名"
python render_winrar_unified.py --version "v7.23" --out "D:\闲鱼\项目名"
```

输出固定为 `01.png` 封面卖点、`02.png` 目录详情、`03.png` 使用收获、
`04.png` 购买说明，全部 `1080 × 1080`。

### 图上数量怎么来

数量永远不允许手打：

- 地图项目：`render_map_collection.py` 调 `scan_source()` 实测源目录，
  文件数和体积直接进图。
- 宣传片音乐：改 `CATEGORIES` 数据表，总数由它求和。
- 相机课程：改 `LESSONS` / `CHAPTERS` 常量，文案用 `LESSON_LABEL` 推导。

`tests/test_render_promo_music.py` 和 `tests/test_render_camera_basics.py`
会扫描源码，发现数据表和常量之外的手打数量就让测试失败。

### 版式怎么调

纵向区块用 `xianyu_common` 里的版式工具，不要写死坐标：

```python
from xianyu_common import stack_layout, assert_no_overlap

(cards_y, meta_y), (card_h, _) = stack_layout(
    [150, 76], top, bottom, grow=[0], max_grow=110, max_gap=90
)
assert_no_overlap([(cards_y, cards_y + card_h), (meta_y, meta_y + 76)], "封面")
```

- `stack_layout` 返回起始 y 和实际高度，`grow` 里的下标会吸收剩余空间，
  避免内容少时底部留大片空白。
- `stack_blocks` 只返回起始 y，兼容只需要位置的场景。
- 总高度超出可用区域会直接抛错，不会静默溢出画布。
- 卡片被拉高时，卡内文字要相对卡片高度居中，否则会挤在顶部。

### 校验

每个脚本结束时会自己校验，也可单独调用：

```python
from xianyu_common import validate_png_files

problems = validate_png_files(r"D:\闲鱼\项目名", size=(1080, 1080))
```

除程序校验外，**每张图都要目视看过**：文字不出框、不重叠、不被裁切，
预览图不拉伸变形。

## 6. 生成正文

一条命令产出标题、正文和交付文件：

```powershell
python make_desc.py --out "D:\闲鱼\项目名" --core "项目名称" --count "10集" --intro "一句话介绍" --module "内容明细一" --module "内容明细二" --audience "摄影新手"
```

产出两个文件，语义严格分离：

```text
闲鱼发布文案_直接复制.txt   公开正文，粘贴到闲鱼的就是它
desc.txt                    完整交付包，含分享信息，只作本地记录
```

正文禁止出现：`pan.quark.cn` 等 URL、"分享 ID""提取码""密码"等交付字段、
价格金额、百度网盘、自动发货、实物快递物流等不符实际的说法。

拿分享信息之前也可以先只生成公开正文；等链接有了再执行第 7 步补齐 `desc.txt`。

## 7. 准备夸克分享信息

在夸克网盘找到同名文件夹，确认是**私密永久分享**，然后一条命令写入并
**一键复制**到剪贴板：

```powershell
python make_desc.py --out "D:\闲鱼\项目名" --core "项目名称" --count "10集" --intro "一句话介绍" --module "内容明细一" --audience "摄影新手" --folder "项目名称" --link "https://pan.quark.cn/s/真实ID" --code "a1b2" --copy
```

`--copy` 会把严格三行放进系统剪贴板：

```text
文件夹名：项目名称
链接：https://pan.quark.cn/s/真实ID
提取码：a1b2
```

输出 `clipboard=ok` 才算复制成功；失败会打印 `clipboard=failed` 并把三行
打到终端，此时手动复制，不要谎称已复制。

交付纪律：

1. 分享信息只发给用户，不写进闲鱼正文。
2. 不把真实链接、提取码、Cookie 或登录态写进代码、测试、文档和 Git 历史。
3. 分享失效、过期或提取码不匹配时，重新核验，不继续声称已备好。

## 8. Playwright 填表

1. 打开闲鱼发布页，确认已登录正确账号。
2. 出现扫码、验证码或安全验证就停下，请用户本人完成。
3. 上传 `01.png` ~ `04.png`，确认页面显示四张都已上传。
4. 标题、正文取自 `闲鱼发布文案_直接复制.txt`，不手敲。
5. 填用户确认的价格，选择页面实际提供的分类，虚拟资料选"无需邮寄"。
6. 任何一步都不要把夸克链接或提取码填进表单。

浏览器拒绝访问 D 盘时，把四张图复制到工作区内的临时目录再选，
只复制文件，不改图片内容。

## 9. 确认与发布

点击"发布"等于替用户向第三方平台公开商品，**必须先展示摘要并等待明确确认**：

```text
即将以当前闲鱼账号发布：
标题：项目名称
分类：电子资料
价格：用户确认价格
图片：4 张
发货：无需邮寄
正文：不含夸克链接和提取码
```

确认后再点发布，等待成功提示或商品链接，记录真实结果。
发布成功后再单独交付剪贴板里的分享信息。

## 10. 故障处理

| 问题 | 处理方式 |
| --- | --- |
| 源素材不存在 | 停止生成，回到核验 |
| `verify_source.py` 退出码非 0 | 按报告改正文或素材，改完重跑 |
| 目录名标注与实际不符 | 以实际文件数为准，不虚报 |
| 图片缺失、损坏、尺寸错 | 修脚本或重新生成 |
| 文字重叠或出框 | 用 `stack_layout` 重排后重新生成并目视检查 |
| 浏览器拒绝外部路径 | 复制到工作区临时目录再上传 |
| 页面要扫码或验证码 | 暂停，请用户本人完成 |
| 页面没有合适分类 | 选页面实际允许的，不虚构 |
| 正文出现链接或提取码 | 清空正文，用公开正文文件重填 |
| `clipboard=failed` | 手动复制终端打印的三行 |
| 未得到发布确认 | 停在"待用户确认" |
| 发布后无成功提示 | 保留页面，报实际状态，不谎称成功 |

## 11. 提交前检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
git diff --check
```

确认没有把凭据和浏览器数据带进版本库，两条命令都应无输出：

```powershell
git ls-files | Select-String "chrome-profile|Cookie|playwright"
rg -n -i "pan\.quark\.cn/s/[0-9a-zA-Z]{10,}" --glob "*.py" --glob "*.md" .
rg -n "提取码[:：]\s*[0-9a-zA-Z]{4}" --glob "*.py" --glob "!tests/**" --glob "!WORKFLOW.md" .
```

第二条刻意排除了 `tests/` 和本文件：`tests/` 里的假提取码是校验用例的输入，
本文件第 7 节的示例值是占位符，两者都不是真实凭据。除这两处外必须无输出，
说明真实链接和提取码没有泄漏进源码。

装了 Ruff 再跑 `python -m ruff check .`。

提交只加源码、测试和 `WORKFLOW.md`；不加真实链接、提取码、商品图、
浏览器 profile、Cookie、日志和本地输出目录。

```powershell
git add <本次修改的源码和测试> WORKFLOW.md
git commit -m "refactor: audit project and rewrite workflow"
git push origin xianyu
```

## 12. 代码结构

```text
xianyu_common.py     版式与校验公共库：字体、画板、文本换行、区块排布、PNG 校验
verify_source.py     素材统计与数量声明校验，唯一统计入口
make_desc.py         正文生成、校验、写入、剪贴板复制（库 + CLI）
legacy_runner.py     以显式环境变量执行 legacy 脚本，负责恢复环境
render_*.py          公开入口，只做参数解析和调度，导入无副作用
cover_v2.py          WorkBuddy 双封面入口
legacy/              历史绘图实现，由对应入口经 legacy_runner 调用，不是死代码
tests/               unittest 测试
```

`legacy/` 里的实现仍在实际运行，改动前先跑对应公开入口验证。
后续迁移到 `xianyu_common.py` 时，保持公开入口签名不变。
