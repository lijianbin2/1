# 闲鱼图文发布工作流程

这是本项目唯一的流程说明。新项目照这七步走完即可发布：

```text
① 核验素材 → ② 生成四张图 → ③ 生成正文 → ④ 备好分享信息
        → ⑤ 填表 → ⑥ 展示摘要等确认 → ⑦ 发布并交付
```

三条底线：**数字来自实测，文案可一键复制，发布必须先确认。**

## 1. 硬规则

1. 闲鱼正文不能出现网盘 URL、分享 ID、提取码或密码。
2. 夸克链接和提取码只作独立交付信息，不进正文、不进 Git、不进代码和测试。
3. 点"发布"前必须拿到用户明确确认。
4. 登录、扫码、验证码、安全验证由用户本人完成。
5. 没实测过的数量、体积、格式不准写进正文和商品图。
6. 四张图通过尺寸和完整性校验才能上传，且每张都要目视看过。
7. 用户已给过的信息（项目名、源目录、价格、素材统计）不要重复索要。

## 2. 项目状态

```text
待核验 → 素材已核验 → 图片已生成 → 文案已生成 → 分享信息已准备
      → 表单已填写 → 待用户确认 → 已发布 → 已交付
```

"图片已上传"不等于"已发布"，"链接已备好"不等于"已交付"。

## 3. 收集信息

开工时一次性确认，只问缺的：

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
不要凭目录名猜。** 退出码非 0 表示目录名标注和实际文件数对不上，以实际为准。

文案写好后再连同数量声明一起校验：

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名" --copy "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt"
```

非 0 退出就按报告改正文或素材，改完重跑。实际文件数明显少于预期时先查同步是否
失败，不要为了对上目录名而虚报数量。

### 已核验基准值

改数据表或常量前先核验，别凭记忆。以下是 2026-09-26 对真实源目录的实测结果，
对应测试里钉住的值：

| 项目 | 源目录实测 | 代码位置 |
| --- | --- | --- |
| 高清一亿像素地图矢量图 | 468 个文件 / 7.24GB | 自动读取，无需改代码 |
| 宣传片背景音乐合集 | 970 首，7 类 37/67/69/88/111/111/487 | `render_promo_music.py` `CATEGORIES` |
| 相机基础入门课 | 41 个视频，12 个章节 | `render_camera_basics.py` `LESSONS` / `CHAPTERS` |
| WorkBuddy 智能体实战 | 37 个视频 | `legacy/render_workbuddy_legacy.py` `LESSONS` |
| WinRAR 单文件安装包 | 4,102,490 字节 ≈ 4.1MB | `legacy/render_winrar_unified_legacy.py` `PACKAGE_MB` |

Codex 办公课的源目录当前不在素材盘上，55 这个数字暂时无法复核，
用 `XIANYU_CODEX_LESSONS` 覆盖前请先跑一次 `verify_source.py`。

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

数量永远不允许手打，只允许来自三个地方之一：

- 实测：`render_map_collection.py` 调 `scan_source()` 扫源目录，文件数和体积直接进图。
- 数据表：`render_promo_music.py` 的 `CATEGORIES`，总数由它求和。
- 常量：`render_camera_basics.py` 的 `LESSONS` / `CHAPTERS`，文案用
  `LESSON_LABEL` / `CHAPTER_LABEL` 推导。

`legacy/` 下的四个脚本同样遵守：数量集中在 `LESSONS` / `MODULES` / `PACKAGE_MB`，
并且能用环境变量覆盖，换课不用改代码：

```powershell
$env:XIANYU_WORKBUDDY_LESSONS = "37"
$env:XIANYU_CODEX_LESSONS      = "55"
$env:XIANYU_WINRAR_MB          = "4.1"
```

`tests/test_render_promo_music.py`、`tests/test_render_camera_basics.py`、
`tests/test_legacy_constants.py` 会扫描源码，发现常量和数据表之外的手打数量就让
测试失败；前两个还把实测值钉死，数据表过期会立刻红。

**同一个数量在图上出现几次，就得有几次派生。** 历史踩过的坑：徽章已经走
`LESSONS` 了，课程目录末行还写着 `"29-37"`、正文还写着"37个实战视频"、副标题
还写着"6步"。改一次课时数，四处数字会互相打架，而买家一眼就能看出目录止于
第 37 课、商品却卖 55 课。

所以这三种写法都必须派生，不能抄字面量：

```python
# 课程目录末个模块：结束课时跟 LESSONS 走
('模块6 办公实战', f'29-{LESSONS}', [...], (225, 29, 72)),
# 正文说明：数量跟 LESSONS 走
("3", "即学即用", f"{LESSONS}个实战视频，按顺序学习即可复刻"),
# 副标题步数：跟列表长度走（要把 points 定义挪到副标题之前）
draw.text((BORDER + 40, BORDER + 28 + 56), f'从入门到实战，{len(points)}步...', ...)
```

`test_legacy_constants.py` 里的 `test_codex_module_ranges_chain_to_lesson_count`
会解析模块区间，断言它们从第 1 课首尾相接排到 `LESSONS`；区间断档或止于旧数字
都会失败。`test_step_counts_are_derived_from_lists` 拦截手打的"N步"。

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
- **留白别靠拉高卡片来填。** 实测 codex55 封面原本在特色块和底栏之间
  空出约 380px，把卡片拉伸到 460px 之后内容仍只占 180px，底部又空一片，
  反而更难看。正确做法是往卡里补实质内容（每张卡加一行"跟着课能做出
  什么"），再让 `stack_layout` 把整块居中。改完用 `assert_text_above`
  守住文字不越框。
- **`max_grow` 限制的是增长量，不是总高度。** `max_grow=100` 配
  `base_h=380` 得到的是 480px 高的卡片，不是 100px。要压住总高就直接
  调小 `base_h`。
- **文字按卡片自身内边距裁剪，不能按画布边界。** 居中后向左溢出时，
  用 `max(BORDER+10, ...)` 挡不住，文字会跑到卡片边框外面。codex55 封面
  的副标题就是这么漏出卡片的。

### 文案不要被静默截断

换行后要限制行数时用 `wrap_text_fit`，不要写 `wrap_text(...)[:2]`：

```python
lines = wrap_text_fit(text, font, max_w, 2, draw, label="04 页提示")
```

`wrap_text(...)[:N]` 在文案变长时会**悄悄丢掉末行** —— 图照常渲染成功，
只是少了半句话，既不报错也没人能从成品里看出来。实测地图合集 03 页的
前两张卡片已经正好占满 2 行，稍微改几个字就会触发。
`wrap_text_fit` 放不下直接抛错并带上 `label`，让问题在渲染阶段暴露。
`tests/test_xianyu_common.py` 里有一条源码扫描用例禁止这个写法回归。

### 符号必须确认字体里有字形

正文和图标里用到的符号，必须确认 msyh 字体真的有那个字形，否则渲染成
豆腐块（□）。实测 msyh **缺**这些字形：`◉ ▣ ✓ ✔ ✕ ▶ ◀`；
可用的是：`◆ ● ○ ■ □ ▲ △ ▼ ▽ ★ ☆ × · — ◇`。

codex55 封面早先用了 `◉` 和 `▣`，页面上直接出现两个方框。已换成
`● ◆ ▲`。`tests/test_xianyu_common.py` 的
`test_symbols_in_source_exist_in_font` 会扫描所有渲染器源码里的字符串
字面量，用私用区字符（必定缺字）做指纹比对，新增符号时自动拦截。

### 校验

七个公开入口（`cover_v2.py`、`render_promo_music.py`、`render_camera_basics.py`、
`render_map_collection.py`、`render_codex55.py`、`render_workbuddy.py`、
`render_winrar_unified.py`）结束时都会自己调用 `require_valid_pngs()`，
产物缺失、尺寸不对或打不开就抛 `RuntimeError` 并非 0 退出。
"打印了 generated" 不等于"图能用"——校验不过就不算生成成功，别手动绕过。

`cover_v2.py` 出的是两张封面（`cover_A.png` / `cover_B.png`），
其余入口出四张 1080×1080 图，所以封面走 `names=` 单独指定文件名。

需要脱离入口单独校验时：

```python
from xianyu_common import validate_png_files

problems = validate_png_files(r"D:\闲鱼\项目名", size=(1080, 1080))
```

文字间距不要用 `y + 字号` 估算：`draw.text` 的 y 是顶部锚点，真实墨迹由
`textbbox` 决定，msyh 30px 实测占 `y+6` 到 `y+36`，按锚点算会低估文字底部
并把字压到下一个图框上。改版式时用 `text_extent()` 量真实范围，或直接
`assert_text_above()` 让越界在渲染时抛错。

文字宽度同理，不要自己手写"while 太宽就缩小"的循环：漏掉下限时会静默
溢出卡片，而溢出在渲染时看不出、在买家手里才暴露。统一用 `fit_font()`，
它缩到 `min_size` 仍放不下就直接抛 `ValueError`：

```python
from xianyu_common import fit_font

font, width = fit_font(draw, subtitle, card_w - 24, 30, bold=True, min_size=20)
```

多行区块用 `stack_layout()` 分配位置，不要手写 `yy = BORDER + 120` 这类
固定起点：上游标题或卡片一变高度，下游就会压字。

除程序校验外，**每张图都要目视看过**：文字不出框、不重叠、不被裁切，
预览图不拉伸变形。

纯重构（比如把硬编码数字换成常量）必须证明版式没变，用临时 worktree 对比哈希：

```powershell
git worktree add D:\tmp\xb_head HEAD
python render_workbuddy.py --out D:\tmp\xb_old\workbuddy
python render_workbuddy.py --out D:\tmp\xb_new\workbuddy   # 改完的代码
git worktree remove D:\tmp\xb_head --force
```

两目录同名 PNG 哈希应完全一致。哈希变了说明改常量时手滑动了别的地方。

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

校验不过就非 0 退出并列出违规项，改正文重跑，不要带着违规往下走。

## 7. 准备夸克分享信息

在夸克网盘找到同名文件夹，确认是**私密永久分享**，然后一条命令写入并
**一键复制**到剪贴板：

```powershell
python make_desc.py --out "D:\闲鱼\项目名" --core "项目名称" --count "10集" --intro "一句话介绍" --module "内容明细一" --audience "摄影新手" --folder "项目名称" --link "https://pan.quark.cn/s/真实ID" --code "a1b2" --copy
```

`--copy` 走 Windows `clip`（UTF-16LE），中文不会乱码，会把严格三行放进剪贴板：

```text
文件夹名：项目名称
链接：https://pan.quark.cn/s/真实ID
提取码：a1b2
```

输出 `clipboard=ok` 才算复制成功；失败会打印 `clipboard=failed` 并把三行
打到终端，此时手动复制，不要谎称已复制。**这一步做完就不要再问用户要链接，
用户只需要粘一次。**

交付纪律：

1. 分享信息只发给用户，不写进闲鱼正文。
2. 不把真实链接、提取码、Cookie 或登录态写进代码、测试、文档和 Git 历史。
3. 分享失效、过期或提取码不匹配时，重新核验，不继续声称已备好。

## 8. Playwright 填表

1. 打开闲鱼发布页，确认已登录正确账号。
2. 出现扫码、验证码或安全验证就停下，请用户本人完成。
3. 上传 `01.png` ~ `04.png`，确认页面显示四张都已上传（"图片已上传"≠"已发布"）。
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

没拿到确认就停在"待用户确认"，不要自己点。

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
| 改常量后图片哈希变了 | 查是不是手滑改了坐标或尺寸，重来 |
| 测试报"实测值"不匹配 | 素材同步可能变了，重跑 `verify_source.py` 再更新数据表 |

## 11. 提交前检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
git diff --check
```

确认没有把凭据和浏览器数据带进版本库，三条命令都应无输出：

```powershell
git ls-files | Select-String "chrome-profile|Cookie|playwright"
rg -n -i "pan\.quark\.cn/s/[0-9a-zA-Z]{10,}" --glob "*.py" --glob "*.md" .
rg -n "提取码[:：]\s*[0-9a-zA-Z]{4}" --glob "*.py" --glob "!tests/**" --glob "!WORKFLOW.md" .
```

第三条刻意排除了 `tests/` 和本文件：`tests/` 里的假提取码是校验用例的输入，
本文件第 7 节的示例值是占位符，两者都不是真实凭据。

这三条必须真的跑，不能凭印象说"检查过了"——之前就出过凭据扫描看着干净、
实际有输出的情况。

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
xianyu_common.py     版式与校验公共库：字体、画板、文本换行、区块排布、真实文字占位、PNG 校验、控制台 UTF-8
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

### 测试分工

```text
test_entrypoints.py            七个入口导入无副作用、legacy 环境变量能恢复、缺图时报错
test_xianyu_common.py          版式工具、区块不重叠、PNG 校验、真实文字占位、控制台编码
test_verify_source.py          统计扫描、数量声明违规能被抓到
test_make_desc.py              正文生成、链接/提取码拦截、剪贴板
test_render_map_collection.py  地图统计标签来自实测
test_render_promo_music.py     分类数据表等于实测 970 首
test_render_camera_basics.py   课时/章节等于实测 41/12，源码无手打数量
test_legacy_constants.py       legacy 数量只在常量处声明，可被环境变量覆盖
test_legacy_layout.py          legacy 版式回归：底栏行距、提醒框高度、箭头不出框
```

渲染类测试会真的往临时目录出图，字体缺失会直接失败，这是有意的。
