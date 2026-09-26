# 闲鱼图文发布工作流程

本项目唯一的流程说明。照第 2 节的七步走完即可发布；改代码前看第 5 节。

## 1. 底线

1. 闲鱼正文不能出现网盘 URL、分享 ID、提取码或密码。
2. 夸克链接和提取码只作独立交付信息，不进正文、不进代码、不进测试、不进 Git 历史。
3. 点"发布"前必须拿到用户明确确认。
4. 登录、扫码、验证码、安全验证由用户本人完成。
5. 没实测过的数量、体积、格式不准写进正文和商品图。
6. 四张图通过尺寸和完整性校验才能上传，且每张都要目视看过。
7. 用户已给过的信息（项目名、源目录、价格、素材统计）不要重复索要。

三条底线概括成一句：**数字来自实测，文案可一键复制，发布必须先确认。**

### 环境

Python 3.12，只依赖 Pillow 和 numpy：

```powershell
python -m pip install -r requirements.txt
```

不钉版本：`requirements.txt` 只写包名。实测环境是 Pillow 12.3.0 / numpy 2.5.2，
但版式测试会真的出图并按像素断言，依赖大版本变化时该由测试报红，而不是由一个
钉死的版本号假装稳定。

## 2. 七步主线

```text
① 核验素材 → ② 生成四张图 → ③ 生成正文 → ④ 备好分享信息
        → ⑤ 填表 → ⑥ 展示摘要等确认 → ⑦ 发布并交付
```

状态推进：

```text
待核验 → 素材已核验 → 图片已生成 → 文案已生成 → 分享信息已准备
      → 表单已填写 → 待用户确认 → 已发布 → 已交付
```

"图片已上传"不等于"已发布"，"链接已备好"不等于"已交付"。

开工时一次性确认，只问缺的：项目名称、素材源目录、闲鱼价格、闲鱼分类
（取页面实际选项）、发货方式（虚拟资料通常"无需邮寄"）。

### ① 核验素材（唯一统计入口）

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名"
```

输出文件总数、总体积、一级分类数量、扩展名分布。**不要用 PowerShell 手数，
不要凭目录名猜。** 退出码非 0 表示目录名标注和实际文件数对不上，以实际为准。

文案写好后再连同数量声明一起校验：

```powershell
python verify_source.py --root "M:\WebDAV\夸克\软件\项目名" --copy "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt"
```

非 0 退出就按报告改正文或素材，改完重跑。实际文件数明显少于预期时先查同步
是否失败，不要为了对上目录名而虚报数量。

校验器认得的数量单位和目录名标注用的是同一套：**首、张、套、集、期**，
外加专管总数的"个文件"。写"468张""468套素材""共468集"一样会被抓出错数，
不必非写成"首"才受检。裸"个"故意不计入——正文里的"41个视频""12个章节"
数的是章节而不是文件，拿去和文件总数比必然误报。

明细行（`1. 900张…` 这种带序号的行）本身不参与正文计数检查，数量只由
明细累加这一条校验兜底。累加对**一条明细同样生效**：整份文案只在
`内容简介：` 下写了一行时，那一行就是全篇唯一的数量声明；早先的校验要求
明细多于一条才比对，这种文案里的错数会整个漏过去。解析不出数量的明细不报，
不存在误伤。

### ② 生成四张图

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

`cover_v2.py` 出的是两张封面（`cover_A.png` / `cover_B.png`），所以封面走
`names=` 单独指定文件名。

生成后跑一次纵向死区扫描：

```powershell
python scan_zones.py
```

连续空白超过 170px 是要修的死区。**这一步不要跳过**：空洞不会让程序报错，
只让图看起来没排完。当前六个入口最差的一页是 163px（`codex55/01` 与
`workbuddy/01`），都在阈值内。

图上数量怎么来、版式怎么调，见第 5 节。

### ③ 生成正文

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
价格金额、百度网盘、自动发货、实物快递物流等不符实际的说法。`包邮`、`现货`、
`秒发`同样在禁——虚拟资料写这些等于承诺实物发货。但"发货方式：无需邮寄"
这类中性说法是允许的。

这个清单不靠自觉，靠 `make_desc.py` 的 `FORBIDDEN` 常量和 `check_public_copy`
强制执行，校验不过就非 0 退出。

拿分享信息之前也可以先只生成公开正文；等链接有了再执行第 ④ 步补齐 `desc.txt`。

### ④ 备好分享信息

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

输出 `clipboard=ok` 才算复制成功；失败会打印 `clipboard=failed` 并把三行打到
终端，此时手动复制，**不要谎称已复制**。这一步做完就不要再问用户要链接，
用户只需要粘一次。

分享信息只发给用户，不写进闲鱼正文。分享失效、过期或提取码不匹配时重新核验，
不继续声称已备好。

### ⑤ 填表（Playwright）

1. 打开闲鱼发布页，确认已登录正确账号。
2. 出现扫码、验证码或安全验证就停下，请用户本人完成。
3. 上传 `01.png` ~ `04.png`，确认页面显示四张都已上传。
4. 标题、正文取自 `闲鱼发布文案_直接复制.txt`，不手敲。
5. 填用户确认的价格，选择页面实际提供的分类，虚拟资料选"无需邮寄"。
6. 任何一步都不要把夸克链接或提取码填进表单。

浏览器拒绝访问 D 盘时，把四张图复制到工作区内的临时目录再选，只复制文件，
不改图片内容。

### ⑥ 确认

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

没拿到确认就停在"待用户确认"，不要自己点。

### ⑦ 发布并交付

确认后再点发布，等待成功提示或商品链接，记录真实结果。发布成功后再单独交付
剪贴板里的分享信息。

## 3. 故障处理

| 问题 | 处理方式 |
| --- | --- |
| 源素材不存在 | 停止生成，回到 ① |
| `verify_source.py` 退出码非 0 | 按报告改正文或素材，改完重跑 |
| 目录名标注与实际不符 | 以实际文件数为准，不虚报 |
| 核验报 `folder-count-mismatch` 但素材看着完全正常 | 多半是源目录根下有以 `-5张`、`-12首` 命名的**散文件**，旧版扫描会把它当一级分类目录、读出目录名声明。先看报告里的一级分类名里有没有文件名 |
| 图片缺失、损坏、尺寸错 | 修脚本或重新生成 |
| 文字重叠或出框 | 按第 5 节重排，重新生成并目视检查 |
| 死区扫描报 >170px | 往卡里补实质内容，别拉高卡片 |
| 浏览器拒绝外部路径 | 复制到工作区临时目录再上传 |
| 页面要扫码或验证码 | 暂停，请用户本人完成 |
| 页面没有合适分类 | 选页面实际允许的，不虚构 |
| 正文出现链接或提取码 | 清空正文，用公开正文文件重填 |
| `clipboard=failed` | 手动复制终端打印的三行 |
| 未得到发布确认 | 停在"待用户确认" |
| 发布后无成功提示 | 保留页面，报实际状态，不谎称成功 |
| 改常量后图片哈希变了 | 查是不是手滑改了坐标或尺寸，重来 |
| 测试报"实测值"不匹配 | 素材同步可能变了，重跑 `verify_source.py` 再更新数据表 |

## 4. 代码结构

```text
xianyu_common.py     版式与校验公共库：字体、画板、文本换行、区块排布、真实文字占位、PNG 校验、控制台 UTF-8
verify_source.py     素材统计与数量声明校验，唯一统计入口
make_desc.py         正文生成、校验、写入、剪贴板复制（库 + CLI）
legacy_runner.py     以显式环境变量执行 legacy 脚本，恢复环境并返回其全局命名空间
render_*.py          公开入口，只做参数解析和调度，导入无副作用
cover_v2.py          WorkBuddy 双封面入口
scan_zones.py        死区扫描：库 + 命令行，报告白卡内连续空白横带
legacy/              历史绘图实现，由对应入口经 legacy_runner 调用，不是死代码
tests/               unittest 测试
requirements.txt     Pillow、numpy
```

`legacy/` 里的实现仍在实际运行，改动前先跑对应公开入口验证。后续迁移到
`xianyu_common.py` 时保持公开入口签名不变。

### 测试分工

```text
test_entrypoints.py            七个入口导入无副作用、legacy 环境变量能恢复、缺图时报错
test_xianyu_common.py          版式工具、区块不重叠、PNG 校验、真实文字占位、控制台编码、底栏行距测量工具
test_verify_source.py          统计扫描、数量声明违规能被抓到、根下散文件不算一级分类
test_make_desc.py              正文生成、build_body 组装规则、链接/提取码拦截、剪贴板
test_render_map_collection.py  地图统计标签来自实测；底栏两行不粘连
test_render_promo_music.py     分类数据表等于实测 970 首；底栏两行不粘连
test_render_camera_basics.py   课时/章节等于实测 41/12，源码无手打数量
test_legacy_constants.py       legacy 数量只在常量处声明，可被环境变量覆盖
test_legacy_layout.py          legacy 版式回归：底栏行距、提醒框高度、箭头不出框
test_layout_zones.py           六个入口每一页都不能有 >170px 死区；扫描器自检 + 跨目录可运行
```

渲染类测试会真的往临时目录出图，字体缺失会直接失败，这是有意的。

## 5. 改代码时的硬约束

这一节是给改渲染器的人看的，日常发布不需要读。

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

Codex 办公课的源目录当前不在素材盘上，55 这个数字暂时无法复核，用
`XIANYU_CODEX_LESSONS` 覆盖前请先跑一次 `verify_source.py`。

相机课目录图上那 12 个模块各带一个课号区间（`1.1`、`2.1-2.4`……`12.1-12.3`），
和文案里的 `LESSONS` 是两处独立声明。测试会从源码解析这些区间、累加各章节数并
断言等于 `LESSONS`、模块数等于 `CHAPTERS`，所以不会出现"图上目录止于第 40 课、
商品却卖 41 课"。改课数时两个地方要一起动，只改一个测试就会变红。

相机课和 AI 表格课的源目录是**一节一个散 mp4、根本没有分类文件夹**，所以实测
一级分类为 0。`verify_source.py` 只把真正的子目录算一级分类，根下散文件只计入
文件总数、体积和扩展名分布。旧版把散文件当成分类，会让每个文件报一行假的
"一级分类"，文件名里带 `-5张` 这类标注时还会凭空判出一处
`folder-count-mismatch`，让素材完全正常的目录以退出码 1 卡住发布流程。
`tests/test_verify_source.py` 里有三条用例守住这个行为。

### 数量只能派生，不能手打

数量永远不允许手打，只允许来自三个地方之一：

- 实测：`render_map_collection.py` 调 `scan_source()` 扫源目录。
- 数据表：`render_promo_music.py` 的 `CATEGORIES`，总数由它求和。
- 常量：`render_camera_basics.py` 的 `LESSONS` / `CHAPTERS`。

`legacy/` 下的四个脚本同样遵守：数量集中在 `LESSONS` / `MODULES` /
`PACKAGE_MB`，并且能用环境变量覆盖，换课不用改代码：

```powershell
$env:XIANYU_WORKBUDDY_LESSONS = "37"
$env:XIANYU_CODEX_LESSONS      = "55"
$env:XIANYU_WINRAR_MB          = "4.1"
```

`test_render_promo_music.py`、`test_render_camera_basics.py`、
`test_legacy_constants.py` 会扫描源码，发现常量和数据表之外的手打数量就让测试
失败；前两个还把实测值钉死，数据表过期会立刻红。

**同一个数量在图上出现几次，就得有几次派生。** 历史踩过的坑：徽章已经走
`LESSONS` 了，课程目录末行还写着 `"29-37"`、正文还写着"37个实战视频"、副标题
还写着"6步"。改一次课时数，四处数字会互相打架，而买家一眼就能看出目录止于
第 37 课、商品却卖 55 课。所以这三种写法都必须派生：

```python
# 课程目录末个模块：结束课时跟 LESSONS 走
('模块6 办公实战', f'29-{LESSONS}', [...], (225, 29, 72)),
# 正文说明：数量跟 LESSONS 走
("3", "即学即用", f"{LESSONS}个实战视频，按顺序学习即可复刻"),
# 副标题步数：跟列表长度走（要把 points 定义挪到副标题之前）
draw.text((BORDER + 40, BORDER + 28 + 56), f'从入门到实战，{len(points)}步...', ...)
```

`test_legacy_constants.py` 里的 `test_codex_module_ranges_chain_to_lesson_count`
会解析模块区间，断言它们从第 1 课首尾相接排到 `LESSONS`。区间断档或止于旧
数字都会失败。`test_no_hand_typed_step_counts_anywhere` 扫全部四个 legacy
渲染器的非注释行，任意位置出现"数字+步"就失败——winrar 的"安装3步"就是这样
被抓出来的，现在由 `INSTALL_STEPS` 列表派生，正文那句也改成
`" ".join(INSTALL_STEPS)`。

**断言规则本身也要用变异测试验证。** 这条检查早先只认"，N步"一种写法，在真实
源码里 `findall` 返回空列表，等于什么都没测，改成"共6步"照样放行。把派生改回
字面量，测试必须变红，否则它只是摆设。

### 版式

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
- **留白别靠拉高卡片来填。** 实测 codex55 封面原本在特色块和底栏之间空出约
  380px，把卡片拉伸到 460px 之后内容仍只占 180px，底部又空一片，反而更难看。
  正确做法是往卡里补实质内容（每张卡加一行"跟着课能做出什么"），再让
  `stack_layout` 把整块居中。改完用 `assert_text_above` 守住文字不越框。
- **`max_grow` 限制的是增长量，不是总高度。** `max_grow=100` 配 `base_h=380`
  得到的是 480px 高的卡片，不是 100px。要压住总高就直接调小 `base_h`。
- **文字按卡片自身内边距裁剪，不能按画布边界。** 居中后向左溢出时，用
  `max(BORDER+10, ...)` 挡不住，文字会跑到卡片边框外面。

### 底栏两行必须按 FOOTER_TOP 相对定位

早先底栏两行写成 `H-BORDER-68` / `H-BORDER-47`，两行墨迹在纵向上连成一片
（实测 980-1003 与 1000-1019）。因为一行左对齐、一行右对齐，横向并不相交，
所以它属于观感隐患而不是明显的错字重影，但它是脆的：`H-BORDER-68` 把底栏
高度写死成了 86，改 `FOOTER_H` 时这两行不会跟着动。相机课、地图和宣传片现已
统一成 `FOOTER_TOP + 12` 和 `FOOTER_TOP + 48`（实测 974-997 与 1009-1028，
中间留 11px）。

`tests/test_render_map_collection.py` 和 `tests/test_render_promo_music.py`
各自量渲染结果的墨迹横带守住这条规则，共用工具是
`test_xianyu_common.footer_text_bands()`——它读像素而不是读源码坐标，因为源码
扫描只能证明"写了什么"，像素才能证明"画出来叠没叠"。

同一文件里不要再出现字面量 `86`：底部横条高度和页内信息条高度是两回事，
winrar 早先两个都叫 `FOOTER`，改一个不动另一个。信息条用 `NOTE_H`。winrar 里
横条高度和 04 页"提醒"框高度都恰好是 86，但含义无关，所以分别叫 `BAR_H` 和
`WARN_H`，不要合并成一个常量。codex55 / workbuddy 的 `BAR_TOP=H-BORDER-86`
**保持原样**：那里的 `FOOTER_H` 是 01 页封面底栏，和 04 页横条不是同一块，绑
一起反而会引入新的耦合错误。

### 死区扫描

`scan_zones.py` 报告白卡底栏以上的连续无墨迹横带，超过 170px 就是要修的死区。
`cover_v2.py` 会被显式跳过并在输出里说明原因：它是整幅渐变的全出血封面，没有
白卡也没有底栏，逐行问"有没有墨"必然每行都有，扫描恒为 0px，属于空跑。

这条规则已经固化进 `tests/test_layout_zones.py`，六个入口的每一页都会被扫。
三处细节别绕过：

- **几何常量从渲染器读，不在扫描侧抄一份。** 扫描区域用 `scan_zones.geometry()`
  从渲染器的 `W` / `H` / `BORDER` / `FOOTER_TOP` 取（winrar 叫 `BAR_TOP`，
  `geometry()` 做了兜底）。抄常量的坏处是画布或底栏高度一改，扫描就落到错误
  区域，甚至落到画布外空跑——报告恒为 0px，看着全通过其实什么都没测。legacy
  三个脚本的常量靠 `legacy_runner.run_legacy()` 的返回值拿，不要为了拿常量再
  导入一次、把图重画一遍。
- **扫描区域不合法必须抛错。** `ink_bands()` 要求显式传 `top` / `bottom` /
  `left` / `right`，尺寸装不下时抛 `ValueError`，悄悄截断后报"没有空洞"比直接
  报错危险得多。负坐标和上下颠倒的区域同样要拒：numpy 的负索引会把负 `top`
  变成从末尾数，切片悄悄变空，检查等于被关掉。
- **子进程路径必须绝对，输出必须是 UTF-8。** 早先这里传的是
  `sys.executable, entry`，从项目根以外运行直接报 `can't open file`，扫描器成了
  只能在特定目录下跑一次的脚本；`main()` 也漏了 `enable_utf8_stdout()`，输出的
  中文在 GBK 控制台上变成 U+FFFD，而乱掉的恰好是"cover_v2 为什么跳过"那段唯一
  的解释。现在用 `ROOT / entry` 并在 `main()` 首行开 UTF-8，
  `test_scanner_runs_from_any_directory_with_readable_chinese` 一次性守住这两条
  （每次扫描要 20 秒以上，所以合并成一个用例而不是两个）。

`test_layout_zones.py` 还有两条自检用例：先在图上画出一条 200px 空白确认扫描器
报得出来（避免"扫描器坏了所以全通过"），再确认超区域会报错。

**修空洞的办法是往卡里补实质内容，然后让 `stack_layout` 居中整块；把卡片拉高
只会把洞做大。**

### 文案不要被静默截断

换行后要限制行数时用 `wrap_text_fit`，不要写 `wrap_text(...)[:2]`：

```python
lines = wrap_text_fit(text, font, max_w, 2, draw, label="04 页提示")
```

`wrap_text(...)[:N]` 在文案变长时会**悄悄丢掉末行**——图照常渲染成功，只是少了
半句话，既不报错也没人能从成品里看出来。实测地图合集 03 页的前两张卡片已经
正好占满 2 行，稍微改几个字就会触发。`wrap_text_fit` 放不下直接抛错并带上
`label`，让问题在渲染阶段暴露。`test_xianyu_common.py` 里有一条源码扫描用例
禁止这个写法回归。

### 符号必须确认字体里有字形

正文和图标里用到的符号，必须确认 msyh 字体真的有那个字形，否则渲染成豆腐块
（□）。实测 msyh **缺**这些字形：`◉ ▣ ✓ ✔ ✕ ▶ ◀`；可用的是：
`◆ ● ○ ■ □ ▲ △ ▼ ▽ ★ ☆ × · — ◇`。

codex55 封面早先用了 `◉` 和 `▣`，页面上直接出现两个方框。已换成 `● ◆ ▲`。
`test_xianyu_common.py` 的 `test_symbols_in_source_exist_in_font` 会扫描所有渲染器
源码里的字符串字面量，用私用区字符（必定缺字）做指纹比对，新增符号时自动拦截。

### 文字占位和校验

文字间距不要用 `y + 字号` 估算：`draw.text` 的 y 是顶部锚点，真实墨迹由
`textbbox` 决定，msyh 30px 实测占 `y+6` 到 `y+36`，按锚点算会低估文字底部并把字
压到下一个图框上。改版式时用 `text_extent()` 量真实范围，或直接
`assert_text_above()` 让越界在渲染时抛错。

文字宽度同理，不要自己手写"while 太宽就缩小"的循环：漏掉下限时会静默溢出卡片，
而溢出在渲染时看不出、在买家手里才暴露。统一用 `fit_font()`，它缩到 `min_size`
仍放不下就直接抛 `ValueError`：

```python
from xianyu_common import fit_font

font, width = fit_font(draw, subtitle, card_w - 24, 30, bold=True, min_size=20)
```

缩小按步长走到 `min_size` 为止，不会再往下掉一档。`size` 和 `min_size` 相差不到
`step` 时（比如 21 和 20）照直减会交出 19px，调用方就拿到了一个它从没要求过
的字号。放不下时报错信息里的字号是真量过的那个，不是名义下限。

七个公开入口结束时都会自己调用 `require_valid_pngs()`，产物缺失、尺寸不对或
打不开就抛 `RuntimeError` 并非 0 退出。"打印了 generated" 不等于"图能用"——
校验不过就不算生成成功，别手动绕过。`names=` 不接受空列表：`count` 拒绝小于 1，
空 `names` 却能校验零个文件后报"通过"，比不校验更糟。传空就抛 `ValueError`。

需要脱离入口单独校验时：

```python
from xianyu_common import validate_png_files

problems = validate_png_files(r"D:\闲鱼\项目名", size=(1080, 1080))
```

除程序校验外，**每张图都要目视看过**：文字不出框、不重叠、不被裁切，预览图不拉伸
变形。

### 导入不得有副作用

模块层不许改全局状态。地图素材图超过 PIL 的解压炸弹阈值，所以
`Image.MAX_IMAGE_PIXELS = None` 只在 `main()` 里、扫源目录之前打开，不放在模块层
——否则任何 `import render_map_collection` 都会把整条进程链的 PIL 防护关掉。
`scan_zones.py` 同理不在模块层 `sys.path.insert`，改用模块常量 `ROOT`；`PIL` 的
导入一律提到模块顶层，不在函数体内 `from PIL import ...`。

`test_entrypoints.py` 会真的 import 七个入口并检查这一条。

### 纯重构要证明版式没变

把硬编码数字换成常量属于纯重构，必须证明版式没变，用临时 worktree 对比哈希：

```powershell
git worktree add D:\tmp\xb_head HEAD
python render_workbuddy.py --out D:\tmp\xb_old\workbuddy
python render_workbuddy.py --out D:\tmp\xb_new\workbuddy   # 改完的代码
git worktree remove D:\tmp\xb_head --force
```

两目录同名 PNG 哈希应完全一致。哈希变了说明改常量时手滑动了别的地方。

## 6. 提交前检查

三条命令必须真的跑，不能凭印象说"检查过了"：

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
git diff --check
```

确认没有把凭据和浏览器数据带进版本库，三条都应无输出：

```powershell
git ls-files | Select-String "chrome-profile|Cookie|playwright"
rg -n -i "pan\.quark\.cn/s/[0-9a-zA-Z]{10,}" --glob "*.py" --glob "*.md" .
rg -n "提取码[:：]\s*[0-9a-zA-Z]{4}" --glob "*.py" --glob "!tests/**" --glob "!WORKFLOW.md" .
```

第三条刻意排除了 `tests/` 和本文件：`tests/` 里的假提取码是校验用例的输入，
本文件第 ④ 节的示例值是占位符，两者都不是真实凭据。之前就出过凭据扫描看着干净、
实际有输出的情况，所以这三条也要真跑。

提交只加源码、测试、`requirements.txt` 和 `WORKFLOW.md`；不加真实链接、提取码、
商品图、浏览器 profile、Cookie、日志和本地输出目录。

```powershell
git add <本次修改的源码和测试> WORKFLOW.md requirements.txt
git commit -m "refactor: audit project and rewrite workflow"
git push origin xianyu
```
