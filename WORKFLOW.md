# 闲鱼图文发布工作流程

本项目唯一的流程说明。照第 2 节的七步走完即可发布；改代码前看第 5 节。

## 0. 暂停公告（2026-09-30 起，14 天）

**闲鱼账号被禁止发布，批量线整体暂停，2026-10-14 之前不要发任何商品。**

暂停期间的工作流规则：

1. 用户说"跑一次""发布""继续发"**不解除暂停**。批量线的触发词失效，
   一律先回"账号还在暂停期"，并给出剩余天数。
2. 解除暂停只能由用户明确说一句"解封了""可以发了""恢复发布"之类的话，
   且这句话要在 2026-10-14 当天或之后说。日期没到就当作仍在暂停。
3. 暂停期间可以做且不碰发布接口的活：核验素材、出图、写文案、建夸克分享
   链接、改代码、跑测试。
4. 暂停期间**禁止**调用 `ydisk_publish.py`（含 `--dry-run`）和
   `ydisk_delivery.py`。写规则等于挂发货，不属于"不碰发布"。

暂停原因：账号被禁止发布（用户 2026-09-30 告知，具体是账号级封禁还是
虚拟资料类目被限流尚未确认）。这一条不要自己推测结论，问用户。

**2026-10-14 之后的计划：全部商品重跑一遍。** 用户 2026-09-30 确认所有商品
都已下架，包括之前那批在线的 32 条。所以恢复时不是"补发剩下的"，而是
从头再走一遍全量。

重跑时要注意的两件事：

1. `_online.txt` / `_online_folders.tsv` 会变成空的或只剩零星几条，
   差集就等于 M 盘全量目录，这是符合预期的，不要因为"清单为空"而报警。
2. 上面"不再重发"清单里的两条（WorkBuddy `1088181725474`、
   40 组指令 `1089348944231`）**仍然不重发**，它们的源目录已经不在 M 盘，
   差集自然扫不到，不要试图把它们补回来。

暂停开始时手上已备好、但没发的资源（私密永久链接，未进任何闲鱼商品，
也未配发货规则）：

| 文件夹 | 提取码 |
|---|---|
| AI小说搞钱项目教程，从AI生成到多渠道变现 | u2qn |
| AI小说漫画3.0项目，零基础一键洗稿原创，轻松开启赚钱新模式 | Uz8i |
| AI智能体实战课，零基础做出专属智能体 | TpRn |
| DeepSeek短视频制作教程提示词即梦AI可灵动画剪映豆包动画教程3d(178GB) | udNN |
| Seedance2.0保姆级教程5套合集，从入门到精通的最全攻略 | nPz4 |

链接本身不入库，需要时用 `quarkclouddrive` 的 `search` 按文件夹名找回，
或问用户。对应的渲染数据在 `specs/ai_novel_story.json`、
`specs/ai_comic_30.json`、`specs/coze_agent_course.json`、
`specs/deepseek_animation.json`、`specs/seedance_five_sets.json`，
出图产物在 `D:\闲鱼\` 下对应目录，恢复时不用重做。

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

明细行本身不参与正文计数检查，数量只由明细累加这一条校验兜底。累加对**一条
明细同样生效**：整份文案只在 `内容简介：` 下写了一行时，那一行就是全篇唯一的
数量声明；早先的校验要求明细多于一条才比对，这种文案里的错数会整个漏过去。
解析不出数量的明细不报，不存在误伤。

**明细不写 `1. ` 编号也照样认。** 早先只按序号前缀认明细，但 `make_desc` 把
`--module` 原样拼进 `内容简介：` 下面，实际发布时常常不编号。宣传片音乐那份
文案就是七行 `汽车宣传片 37首`…`大气企业宣传片 487首`，一条编号都没有，于是
七行全落进正文检查，每个分类数量都被拿去和 970 首的**总数**比一遍，报出七条
`body-count-mismatch`——数量全是对的，发布却被校验器挡下来。现在按结构认：
`内容简介` 标题下面那一整块连续非空行都是明细，编不编号都算；找不到标题时才
退回按序号前缀认，`内容简介` 块**外面**的行仍然照常走正文检查。
`test_unnumbered_detail_lines_are_not_compared_against_the_total`、
`test_unnumbered_detail_wrong_count_is_still_caught`、
`test_detail_block_is_scoped_to_its_own_heading` 三条分别守住不误报、仍能拦错数、
以及不越界吞掉正文。

**明细行里不能出现 `个文件`，也不能用 `第N-M集` 这类集号区间。** 这两条不是
校验器的 bug，是它按设计工作的必然结果，写文案时要绕开：

- `个文件` 是**总数声明**。明细写"基础教学 11个文件"，那个 11 会被拿去和
  整个目录的文件总数比。影视解说那份文案 969 个文件，明细里 6 行各带一个
  `11个文件`/`32个文件`……于是报出 6 条 `total-files-mismatch`，数量本身全是对的。
  总数只在标题出现一次，明细改用 `｜` 分隔且不带数字：
  `基础教学｜电影解说入门与完整流程讲解`。
- 集号区间会被 `_COUNT_CLAIM` 拆出来累加。AI 漫剧 36 个 mp4，明细按
  `第1-2集`/`第3-9集`/…分成 6 段，累加成 99，报 `item-sum-mismatch`。
  集号 1-36 本来是连续的，分段只是为了排版好看，不是目录的划分。
  改成不带单位的 `01-02｜漫剧发展定位与AI的变现全部方式`。

同理，**正文（非明细）里任何 `7套`/`238集` 都会和文件总数比**。合集课说
"7套课程"是课程套数，不是文件数，会报 `body-count-mismatch`；换成
`7门课程`（`门` 不在受检单位里）就过了。合法做法是把这类数量改写成非受检
单位，或者干脆让标题里的总数独当一面。

### ② 生成四张图

八个公开入口都支持 `--out`，导入时不产生任何副作用：

```text
render_map_collection.py   地图素材（自动读取源目录统计文件数和体积）
render_promo_music.py      宣传片背景音乐
render_jianying_templates.py 剪映企业宣传片模板（分类数量按文件名关键词实测派生）
render_camera_basics.py    相机基础课程
render_codex55.py          Codex 办公课程
render_workbuddy.py        WorkBuddy 智能体课程
render_winrar_unified.py   WinRAR 工具
render_collection_course.py 合集课程（读 specs/*.json，通用四页）
cover_v2.py                WorkBuddy 双封面
```

新增出图脚本时，把它登记进 `tests/test_entrypoints.py` 的 `CLI_ENTRYPOINTS`，
并在 `scan_zones.py` 的 `ENTRYPOINTS`（参与扫描）或 `SKIPPED`（写明跳过原因）
里二选一。漏登记会被测试直接拦下：早先这两份清单纯手写，实测放一个不做产物
校验、也不参与死区扫描的脚本进根目录，相关测试全部照样通过。

```powershell
python render_map_collection.py --root "M:\WebDAV\夸克\软件\项目名" --out "D:\闲鱼\项目名"
python render_promo_music.py --out "D:\闲鱼\项目名"
python render_jianying_templates.py --root "M:\WebDAV\夸克\软件\项目名" --out "D:\闲鱼\项目名"
python render_camera_basics.py --out "D:\闲鱼\项目名"
python render_winrar_unified.py --version "v7.23" --out "D:\闲鱼\项目名"
python render_collection_course.py --spec specs\keep_fitness.json
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
只让图看起来没排完。当前七个入口最差的一页是 163px（`codex55/01` 与
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

#### 标题规则（2026-09-30 审查 28 个教程目录后固化）

标题不是把夸克文件夹名抄过来。文件夹名是给卖家自己看的，可以带体积、批次号
和"合集/大全"这类堆料后缀；标题是给平台审核看的，标准更严。四条硬规则：

1. **不超过 30 字。** `ydisk_publish.py:73` 会直接 `raise DeliveryError`，不是
   截断。目录名普遍超限（28 个里 7 个超，最长的 63 字），正文首行必须另写。
2. **数字必须实测。** 不准沿用文件夹名里的节数、集数、GB。`少儿编程课程集合
   【48(1).8GB】` 目录名写 1.8GB，实测 51.75GB；`15天进阶CAD高手（126节课程）`
   实测 126 个视频对得上，但那是巧合不是保证。体积数字一律不进标题——买家按
   体积比价，标错就是货不对板。
3. **不写收益承诺。** "轻松开启赚钱新模式""搞钱项目""变现"这类表述在虚拟资料
   类目属于虚假宣传高发区，且平台常据此判定诱导交易。改为讲**教什么**，
   不讲**能赚多少**。
4. **不带政务/盗版/洗稿关联词。** "公文"是账号实锤踩过的词，"标书/投标/招标"
   同属政务关联，"洗稿"是抄袭引导词，"破解/注册机/绿色版/免安装"是盗版词。
   这类词出现在标题、正文、图片内文字任一处都算违规，标题首当其冲。

另外三条软规则：去掉"最全""大全""终结"这类绝对化用语（平台广告法口径）；
去掉 `mp4`、`[8.7GB]`、`(1)` 这类文件格式和批次后缀（`(1)` 是下载重名残留，
`(1).8GB` 是 Windows 自动加的副本后缀，混进标题只会显得像盗录）；同一批标题
不要连着几个都以"AI"开头，避免被判同质化批量铺货。

28 条的逐条结论、实测数字和改好的标题都在 `TITLES.md`，机器可读版本是
`titles_reviewed.json`。这份台账**由数据生成，不要手改表格**：

```powershell
python audit_titles.py validate   # 校验标题能不能发出去（默认）
python audit_titles.py doc        # 从 JSON 重新生成 TITLES.md
python audit_titles.py measure    # 重新实测 M 盘目录（慢，会回写 JSON）
```

改标题的顺序永远是：改 `titles_reviewed.json` → `doc` → `validate`。
`tests/test_titles_reviewed.py` 会守住 30 字上限、风险词、实测数据和文档一致性，
词表只有 `audit_titles.py` 一份，测试从那里引用，改词只改一处。

**统计目录必须逐字匹配路径。** PowerShell 会把名字里的 `[8.7GB]` 当通配符，
用 `Get-ChildItem` 直接统计会返回 0 个文件，`AI视频制作全攻略` 曾因此被误判成
空目录。`audit_titles.py measure` 用 `rglob` 按 `Path` 拼路径，绕开这个问题。

链接按 **host** 拦，不限定 `pan.` 前缀——复制分享地址时 `pan.` 和 `www.` 都
经常被顺手丢掉，只认完整 host 的话，掉了前缀的地址能原样写进公开正文。
正文里写"夸克网盘"是中文，不含该域名，不会被误伤。

交付字段（"提取码""分享 ID"等）**必须带冒号**才判违规，这样"拍后提供提取码"
"下单后发送网盘链接与提取码"这类正常表述能放行，而 `提取码：abcd` 会被拦下。

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

### ydisk 批量线（当前实际在用）

第 2 节那套是 Playwright 手填的基线。实际批量发布走 ydisk 系统，接口和
发货规则都由脚本管，**一次跑 5 个未发布资源**。

用户说"跑脚本""继续发"就是触发这条线，不需要重新交代数量、目录或流程。

#### 每轮固定 5 个

用户不用再说"发几个"。规则已经定死：

1. 只从 `M:\WebDAV\夸克\教程` 里挑**尚未发布**的资源（`软件` 目录已于
   2026-09-30 停用并清空，见上面“软件目录已停用”一节）。
2. 每轮**恰好 5 个**，按目录名字母序，取最靠前的 5 个未发布项。
3. 上一轮发过、被用户手动删掉、或源目录已不存在的都算"已处理"，跳过不再重发。
4. 用户单独点名某个资源时按点名的来，不受 5 个限制。

已经跑完的记录不要重新发布。`_online.txt` 是从 ydisk 拉下来的线上清单
（`item_id<TAB>标题`），它不算源码也不进版本库，选资源时拿它和
`M:\WebDAV\夸克` 的目录名做差集。

10 月 14 日全量重跑时，每轮仍然是 5 个，按目录名字母序往前推，
一轮一轮往下走，不一次性铺完。

```text
1077538597531  2026AI漫剧短剧全流程教学
1073788412201  AI 人工智能 2.0：人工智能课
1076529893006  AI 全场景创作实战汇总课
1081135248514  AI+自媒体工业化实战课｜21集视频课 终结低效创作模式
1074654958339  AI创作全赛道｜小说、短剧、漫剧剧本
1073256138756  AI古风人物设计素材包
1086973605321  AI处理制作表格技巧，小白都能学会的智能办公术
1081042450608  AI智能体提效实战课，零基础打造自动化工作助手 61集 只发
1073429144673  AI标书写作实战课程
1081975253958  AI漫剧制作全流程60集｜剧本分镜+AI生成+剪映发布+模板
1075005868053  AI短视频创作实战课
1086433493202  AI视频制作全攻略 （豆包+即梦+剪映）从入门到精通实战课程
1082549793713  Adobe+达芬奇官方音效库合集 影视级音效素材包 27大类
1073283257411  CAD零基础126节精讲教程
1081120061300  Internet Download Manager (IDM
1081344564586  PLC编程入门精通73节全套教程｜从电工基础到人机精通
1084918353725  WinRAR解压工具64位分享
1077898771367  主流 AI 工具全解实战合集
1077883548301  亚马逊全流程体系课
1086220239494  从安装WorkBuddy到定时简报周报自动推送，文件文档数据
1086347310437  企业宣传视频剪映模板合集 41套 只发夸克剪映专业版企业宣传
1077886150143  剪映高级感封面预设
1075709168926  即梦 Seedance 动漫短剧教程
1079697958331  即梦Seedance2.0动漫短剧视频教程大合集｜10合集1
1079028030252  大白话带你入门AI｜19集视频课 零基础玩转人工智能
1085782690886  宣传片背景音乐合集1072首
1082128048488  少儿编程课程集合 | Scratch3.0全套214节 +
1087743400092  相机基础入门课，光圈快门曝光度一次搞懂 41集 只发夸克
1081199169816  达芬奇调色剪辑软件资源分享
1071630263884  闲鱼运营指南实操技巧
1076142525102  零基础 AI 视频变现全套课程
1088015828158  高清一亿像素地图矢量图合集，超精细地理素材
1088303341686  keep健身课程合集 238集 只发夸克
1086340095973  影视解说零基础教程套装合集 969个文件 只发夸克
1087235362610  最全家电维修大全视频教程 22大类 只发夸克
1087235326864  AI漫剧全流程实操 36集 只发夸克
```

`1088181725474`（WorkBuddy 智能体实战）违规下架且源文件已被用户删除，不重发。
`1089348944231`（40组AI高质量指令合集）文案含“公文”字眼被判违规，用户已删除，
源目录 `M:\WebDAV\夸克\教程\最新40组Ai高质量指令合集+教程(2)` 也已不在，不重发。
“公文”属于闲鱼违规词，标题、正文、图片内文字都不许出现，改用“写作与长文”这类表述；
`specs/ai_prompts.json` 中的措辞已同步改掉。`D:\闲鱼` 下还留着旧的 4 张图和文案
（目录名“40组AI高质量指令合集，指令加教程直接套用”），里面仍有“公文”，别再拿去用。
`Blackmagic Design DaVinci Resolve Studio 21` 含盗版 patcher，明确不发布。

### 高风险排除清单（2026-09-30 用户确认）

下面四个目录**一律不发布**，源文件即使还在 `M:\WebDAV\夸克\软件` 里也不碰。
选资源时直接跳过，不要因为它们还没被发过就捡起来。

| 目录 | 排除原因 |
|---|---|
| `IDM` | 内含 `IDM_6.4x_Crack_v20.7.exe`，破解版软件，机器扫关键词直接命中 |
| `Winrar` | 软件安装包，虚拟类目对这类整体收紧（文件本身是官方未破解版） |
| `Adobe+达芬奇官方音效库合集，影视级音效素材包` | 目录名带“官方”，内容为 Adobe 商业音效库，侵权素材 |
| `宣传片背景音乐合集，一键提升影片质感与感染力` | 无授权 BGM 二次分发 |

注意 `M:\WebDAV\夸克` 是夸克网盘的 WebDAV 挂载，在那里删文件等于删网盘上的真实文件，
不可逆。排除靠上表，不靠删目录。

另有一条需要改标题而不是删：`AI标书方案写作课程，用AI产出高质量投标文件`
（线上 `1073429144673`）。“投标/招标/标书”和之前踩过的“公文”属同类政务关联词，
重发时标题与正文都要改成“AI 商业方案写作课程，用 AI 产出高质量方案文档”这类中性表述。

`AI小说漫画3.0项目，零基础一键洗稿原创…` 目录名里的“洗稿”是抄袭引导词，
重发时标题必须删掉这三个字，别直接沿用目录名。

### 软件目录已停用（2026-09-30 用户决定）

用户选择 B 方案：整个 `软件` 目录停用。原先挂在 `M:\WebDAV\夸克\软件` 下的
六个目录（IDM、Winrar、Adobe+达芬奇官方音效库合集、宣传片背景音乐合集、
企业宣传视频剪映模板合集、高清一亿像素地图矢量图合集）已全部移到夸克网盘
根目录 `已归档_不再发布_20260930`，`软件` 目录已空。

因此以下两条线上商品**永久不重发**，即使它们曾经在线、曾经合规：

| 商品 | 原线上 ID | 归档原因 |
|---|---|---|
| 企业宣传视频剪映模板合集 | 1086347310437 | 随软件目录整体停用 |
| 高清一亿像素地图矢量图合集 | 1088015828158 | 地图素材涉审图号合规，且曾违规下架 |

10 月 14 日全量重跑**只扫 `M:\WebDAV\夸克\教程`**。`软件` 已不存在，
选资源时不要再去 `软件` 里找，也不要尝试从 `已归档_不再发布_20260930` 里恢复。
`[TikTok]玩法教程全攻略[27套课]` 源目录同步不全只剩 1 个 mp4，暂缓。

链接归档在 `C:\Users\1\Documents\Codex\xianyu-quark-archive\quark-links.txt`，
格式 `title|code|link`。这个路径在仓库外，且每次跑都用同一个，
不要按会话目录另起新文件——之前每轮换目录，链接归档早就断链了。

#### 一轮的动作顺序

每个资源按第 2 节的 ① ② ③ ④ 走完出图出文案，再走 ydisk 发布，两条命令：

```powershell
$env:YDISK_BASE_URL="https://44.81938193.xyz"; $env:YDISK_USER="<user>"; $env:YDISK_PASSWORD="<pass>"

python ydisk_publish.py --desc "D:\闲鱼\项目名\闲鱼发布文案_直接复制.txt" --images "01.png,02.png,04.png" --image-dir "D:\闲鱼\项目名" --price 1 --quantity 1111 --dry-run

python ydisk_delivery.py --title "<确认后的标题>" --link "<链接>" --code "<提取码>" --archive "<归档文件>"
```

先跑 `--dry-run` 过一遍 `check_body`，确认没有禁词再实发。5 个都发完再逐个配
发货规则，规则脚本幂等，标题对不上会直接报错。

**价格默认 1 元**，除非用户指定。分类用 `电子资料 50023914` / 渠道
`202036301`，`postage_mode=none`。

#### 批量线的三条特殊约束

这些是批量踩出来的坑，Playwright 线没有：

1. **标题就是正文第一行，不要拆开传。** ydisk 的 `description` 必须保留标题在
   首行。拆成独立的 `title` 字段，平台会把正文里的第二行当成标题——已发过的
   2 个商品标题都因此错成副标题。
2. **库存只能在发布那一刻设，发布后改不了。** 发布接口
   `POST /api/v1/items/publish` 的 multipart 里**有** `quantity` 字段，前端发布
   弹窗那个"库存数量"输入框绑的就是它（扒 `ItemList-*.js` 确认）。所以
   `ydisk_publish.py --quantity 1111` 直接生效，别再让用户手设。

   但 `PUT /api/v1/items/{cookie_id}/{item_id}` 的 body 里**没有** `quantity`——
   同一个文件里那个更新函数只传 `item_title`/`item_description`/`item_category`/
   `item_price`/`item_detail`。往里加 `quantity` 会被**静默忽略**：返回
   `{"success":true}`，库存纹丝不动。实测两次（quantity 放 `item_detail` 里、
   放 PUT body 顶层）都是 HTTP 200 但库存仍为 1。

   写进 `publish_raw` 也没用：商品 2 被用户手设 1111 之后，ydisk 同步回来的
   `item_detail` 已被闲鱼真实响应替换成 `detail_params`，里面只有
   `imageInfos`/`itemId`/`picUrl`/`soldPrice`/`title`，压根没有数量。

   结论：**数量必须在发布前定好**。已经上线的商品只能用户在闲鱼端手改，
   发完要提醒用户去改。
3. **`PUT` 改单会整块回传 `item_detail`，会覆盖用户手改的数据**（比如小刀后的
   0.80 价、1111 库存）。对线上商品做任何写入前，先跟用户确认。

`get-all-from-account` 是只读同步，安全，可以用它查真实在架状态。

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
xianyu_common.py     版式与校验公共库：字体、画板、文本换行、标签行排布、区块排布、真实文字占位、PNG 校验、控制台 UTF-8
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
test_xianyu_common.py          版式工具、区块不重叠、标签行越界报错、PNG 校验、真实文字占位、控制台编码、底栏行距测量工具
test_verify_source.py          统计扫描、数量声明违规能被抓到、根下散文件不算一级分类
test_make_desc.py              正文生成、build_body 组装规则、链接/提取码拦截、剪贴板
test_render_map_collection.py  地图统计标签来自实测；底栏两行不粘连；04 页提示框由步数推导，放不下报错
test_render_promo_music.py     分类数据表等于实测 970 首；底栏两行不粘连
test_render_jianying_templates.py  七个分类数量等于实测 8/6/5/5/7/3/7，合计 41 无遗漏；四页网格由条目数推导，放不下报错
test_render_camera_basics.py   课时/章节等于实测 41/12，源码无手打数量
test_legacy_constants.py       legacy 数量只在常量处声明，可被环境变量覆盖
test_legacy_layout.py          legacy 版式回归：底栏行距、提醒框高度、codex55/workbuddy 箭头都不出框
test_layout_zones.py           七个入口每一页都不能有 >170px 死区；扫描器自检 + 跨目录可运行
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
| 剪映企业宣传片模板 | 41 个 zip，3.74GB，7 类 8/6/5/5/7/3/7 | `render_jianying_templates.py` `CATEGORY_RULES` |
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
- 关键词实测：`render_jianying_templates.py` 的 `CATEGORY_RULES`，扫源目录时
  按文件名归类，数量由 `category_table()` 统计，不手打。

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

**关键词规则是有序的，调换顺序等于改分类。** 剪映模板的源目录是一堆散 zip，
分类完全靠文件名里的主题词，命中即归类不再往下看。同一个文件名经常同时命中
两组词，此时归到先命中的那一组：

```text
"13-70秒红底金边企业励志文化"  含"励志"+"文化"  → 表彰励志年会（励志在前）
"25-企业活动宣传高级卡点视频"  含"高级"+"卡点"  → 卡点快闪电商（卡点在前）
"29-46秒高级感企业文化介绍"    含"高级"+"文化"  → 企业文化介绍（文化在前）
"41-15秒竖屏动画黑黄促销电商"  含"促销"+"电商"  → 卡点快闪电商（同组内）
```

`test_classify_matches_the_real_source_directory` 会实跑源目录把 8/6/5/5/7/3/7
七个数字钉死，`test_every_source_file_lands_in_exactly_one_category` 断言合计
等于实测文件数。所以调换规则顺序、往里加词，都会立刻因为数字对不上而变红，
不会悄悄出一份分类错了的图。`categorize()` 认不出关键词时直接抛错并带上文件名，
不允许静默丢文件。

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

这条规则已经固化进 `tests/test_layout_zones.py`，七个入口的每一页都会被扫。
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

### 标签行用 chip_positions，不要手写 `sx += 宽度 + 间距`

各页那排圆角标签（"RAR ZIP 7Z…"、"适合谁"后面的几个）统一走
`chip_positions()`，它在坐标阶段就算完并校验，放不下直接抛错：

```python
for text, x, width in chip_positions(
    d, labels, font=font, left=BORDER + 60, right=W - BORDER - 60, label="03 页适合谁"
):
    ...
```

早先各脚本是手写 `sx += w + 14` 一路排下去，越界不报错，图照常生成，只是最后
一个标签被画到卡片外面。winrar 03 页的换行守卫更糟：溢出时只把 `sx` 重置回起点、
**不改 y**，新标签就压在同一个位置，两块圆角框叠在一起。两种都是"渲染成功、
成品是错的"，肉眼在缩略图上还看不出来。`test_no_renderer_accumulates_chip_x_by_hand`
扫源码禁掉手写累加，`test_chip_row_rejects_overflow_instead_of_wrapping` 守住报错行为。

改标签文案时如果报"放不下"，正确做法是删一项、缩短文案或加大容器，不是把 `right`
改大硬塞。

### 竖向区块必须由内容推导位置

一页里如果有多块纵向排布的区块（步骤卡、提示框、说明条），位置不能各自写死，
要由前面的内容推出来，并在越到底栏时报错。地图合集 04 页早先把卡片起始位置、
每步增量、提示框位置三个数字各自写死（190 / +132 / 750），彼此之间没有任何
约束。实测加到第 5 步时，第 5 张卡（718-830）直接压在提示框上，而脚本仍然
退出码 0、图片照常生成，缩略图上根本看不出来。现在统一走 `guide_layout(步数)`，
由步数算出卡片顶边和提示框上下沿，越过 `FOOTER_TOP` 直接抛错：

```python
step_tops, warn_top, warn_bottom = guide_layout(len(steps))
```

`test_guide_tip_block_follows_the_step_count` 守住推导和报错，
`test_guide_layout_constants_stay_in_one_place` 防止版式数字又回到绘制代码里。

两段间距不同时不要硬套 `stack_blocks`：04 页卡片之间是 20，卡片到提示框是 52，
统一成一个间距会把现有 4 步的版式改掉（4 步时版式必须保持 `94d928e0` 那张哈希）。

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

八个公开入口结束时都会自己调用 `require_valid_pngs()`，产物缺失、尺寸不对或
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
rg -n -i "pan\.quark\.cn/s/[0-9a-zA-Z]{10,}" --glob "*.py" --glob "*.md" --glob "!tests/**" --glob "!WORKFLOW.md" .
rg -n "提取码[:：]\s*[0-9a-zA-Z]{4}" --glob "*.py" --glob "*.md" --glob "!tests/**" --glob "!WORKFLOW.md" .
```

后两条刻意排除了 `tests/` 和本文件：`tests/` 里的假链接、假提取码是校验用例的
输入（比如 `check_body` 就是靠它们证明能拦住 URL），本文件第 ④ 节的示例值是
占位符，两者都不是真实凭据。**不要为了让扫描干净去改测试里的假数据**，那会把
拦截规则的用例改成空转。之前就出过凭据扫描看着干净、实际有输出的情况，所以这三条
也要真跑。

行尾也要查。`git diff --check` 报出一整份文件"trailing whitespace"时，先看是不是
行尾被整份改写了：

```powershell
git diff --stat        # 明明只加了一行，却显示几百行改动 = 行尾变了
```

本仓库除 `scan_zones.py` 外统一是 LF。Windows 上编辑 `.py` 容易被写成 CRLF，
`git diff` 会把整份文件重写，`git diff --check` 于是逐行报 trailing whitespace。
按下面还原，再确认 `--stat` 回到几行：

```powershell
$text = [System.IO.File]::ReadAllText("scan_zones.py") -replace "`r`n", "`n"
[System.IO.File]::WriteAllText("scan_zones.py", $text, (New-Object System.Text.UTF8Encoding($false)))
```

提交只加源码、测试、`requirements.txt` 和 `WORKFLOW.md`；不加真实链接、提取码、
商品图、浏览器 profile、Cookie、日志和本地输出目录。

```powershell
git add <本次修改的源码和测试> WORKFLOW.md requirements.txt
git commit -m "refactor: audit project and rewrite workflow"
git push newrepo xianyu:main
```

**推的是 `newrepo`，不是 `origin`。** 这个仓库配了两个远端：

```text
newrepo   https://github.com/lijianbin2/xianyu-tuwen-fabu.git   正式仓库，推这里
origin    https://github.com/lijianbin2/1.git                   另一个远端，别推
```

早先文档里写的是 `git push origin xianyu`，照着做会把成果推进 `1.git`，
而 `xianyu-tuwen-fabu` 上的 `main` 一直停在旧提交。改用 `newrepo` 后，
`main` 与 `xianyu` 保持同一位置（快进推送，`main` 原本是 `xianyu` 的祖先，
不存在只在一侧有的提交）。提交前用 `git remote -v` 确认远端名字。
