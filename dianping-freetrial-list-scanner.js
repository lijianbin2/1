// ============================================================
// 大众点评「免费试」列表扫描筛选（Hamibot 版）
// 版本：v1.45.6-fix-card-center-丽人-early-stop
//
// 运行环境：Hamibot 手机客户端
// 目标 App：大众点评（com.dianping.v1）
//
// 说明：
//   1. 不使用 Auto.js 的 "auto"; 指令，改用 auto.waitFor()。
//   2. 每个环节都有 try/catch，不会因为找不到控件直接退出。
//   3. 关键状态同时输出 console.log 和 toast。
//   4. 进入列表后边扫描边处理符合条件的活动，并按 美食/价值>=100 筛选。
//      地区固定使用「全部地区」，地区字段只解析展示，不参与筛选。
//   5. 首页「免费试」入口使用全节点扫描 + 父节点/祖先链点击，
//      不再依赖单一 text("免费试").findOne()。
//   6. 全脚本使用 ES5 兼容语法（var/function），避免旧引擎解析失败。
//   7. 活动字段以「单张卡片容器」为单位解析：从「免费抽」按钮向上
//      找到只包含 1 个「免费抽」的祖先容器，只在该容器内部提取
//      活动名/商户/价值/区域/距离/类目，避免相邻卡片字段串位。
//   8. 价值支持被拆成多个节点的情况（如「价值」「3 0 4」「元」），
//      会自动合并解析；商户优先取信息行候选，且排除位置/数字文本，
//      取不到时从「商户 | 套餐」活动名前缀提取，仍取不到才输出未知。
//   9. v1.7：按活动唯一键定位卡片内部的「免费抽」并点击（沿用
//      v1.6.1 验证成功的 4 种方式级联，以页面文本签名真实变化为唯一
//      成功标准，不信 click() 返回值），进入详情后校验目标活动名/商户名，
//      再判断并记录报名状态，返回列表继续扫描。
//  10. v1.7.1：处理阶段定位目标卡片不再只认唯一键精确相等——卡片半加载
//      （价值节点缺失）或长标题省略号截断会让重建键失配。改为唯一键优先 +
//      名称归一化（去空白/分隔符/结尾省略号，相等或互相包含且短者>=8字符）
//      + 价值/商户均解析出时不得冲突的交叉校验；起点已在列表顶部时一趟
//      扫到底即判失败，不再重复回顶部空跑，失败时输出沿途见过的活动。
//  11. v1.7.2：修复处理阶段「无限翻页」。根因：回顶部用 15 次快速上滑，
//      触发大众点评下拉刷新，整个列表被换成另一批活动，目标卡片永远找
//      不到。改为优先点击右下角「回顶部」箭头按钮，滑动回顶最多 8 次并
//      用扫描首屏样本确认到顶；定位失败时统计沿途活动与扫描结果的重合
//      度，完全无交集判定列表已整体刷新，重新确认美食分类后重试一次，
//      仍无交集则停止处理剩余活动；连续 5 个定位失败同样安全停止。
//  12. v1.8：自动报名。进入验证通过的详情页后，先做明确状态预检
//      （已报名/名额已满/活动已结束/不符合报名条件，命中即记录返回，
//      不点任何按钮）；可报名时精确匹配报名按钮文字白名单
//      （我要报名/立即报名/免费报名/立即参与/参加活动/报名，精确匹配，
//      免费抽/领取/兑换/购买等黑名单包含即排除）， clickable 自身或
//      5 层内祖先优先，bounds 中心兜底；点击后以「报名成功/已报名」
//      正则标识（排除「N 人已报名」统计文本误判）+ 页面仍在目标活动
//      双重验证；出现确认弹窗时仅在报名上下文点一次确认；无法确认
//      绝不盲点第二次。最终按 成功/已报名/不可报名/失败 汇总。
//  13. v1.8.8：默认改为手动入口模式。脚本不再自动从首页点击「免费试」，
//      请先把大众点评手动停在「免费试」列表页再运行；脚本只检测列表标记，
//      检测到后继续执行 全部地区/美食分类/扫描/自动报名。旧的自动入口逻辑
//      保留在 CONFIG.MANUAL_ENTRY=false 时使用。
//  14. v1.9.0：从流程结构上修复「扫描到底后仍无限上下翻页」。扫描阶段新增
//      明确的列表到底检测（底部提示文本 / 连续多轮无新活动 / 当前屏卡片签名
//      连续不变 / MAX_SCAN_SCROLLS / MAX_SCAN_TIME_MS 硬安全阀），结束即
//      scanFinished=true 且任何代码不得把它置回 false。自动报名阶段只消费
//      扫描阶段保存的 qualifiedActivities[]，禁止调用完整扫描函数；定位失败
//      只从当前位置向下做有限滚动，失败立即跳过，不回顶、不重复扫描。
//  15. v1.9.1：扫描阶段只在单张活动卡片内部识别严格的「已报名」/「报名成功」，
//      不使用全页面文本判断，避免「N 人已报名」等统计文案误判。该活动进入
//      处理队列但只记录「已报名」，不点击免费抽或报名按钮。普通到底仍直接
//      结束，处理阶段的有限回顶部逻辑保持不变。
//  16. v1.9.2：修复自动报名阶段定位失败后重复回顶并再次翻页的问题。扫描
//      完成后仍只回顶部一次；每个活动定位从当前列表位置开始，最多有限次单向
//      下滑，页面无进展立即停止，找不到就跳过并交给现有安全熔断。
//  17. v1.9.3：曾尝试使用多个已报名卡片作为列表尾部标志。
//  18. v1.9.4：按真实业务规则改为任意一个明确的已报名卡片作为当前批次
//      尾部标志，发现后立即停止扫描；
//      已报名活动只保留在全量诊断结果，不进入自动报名队列。扫描到底或该
//      尾部标志触发后，统一进入自动报名阶段，处理阶段不重新扫描。
//  19. v1.9.5：修复「已报名」后不真正点击右下角「↑ 回到顶部」按钮。
//      根因：原 scrollListToTop 在 clickBackToTopButton 失败后用最多
//      8 次 scrollListUpOnce 上滑替代，实际手机上没有真正触发按钮。
//      修复：clickBackToTopButton 增加第4层坐标兜底（x=width*0.91,
//      y=height*0.84）；scrollListToTop 移除上滑循环，只依赖按钮点击
//      和一次坐标兜底；所有日志前缀改为 [回顶]。
//  20. v1.21.0：处理路径全面加速。单个活动处理耗时从 ~5-6 秒降至
//      ~2-3 秒。修改位置：diagnoseFreeDrawClick（800->350ms）、
//      findSignupButton（800->350ms / 600->250ms）、attemptSignup
//      （500->250ms / 400->200ms）、returnToList（600->350ms /
//      400->250ms）、scrollListToTop（800->400ms）、
//      findCardButtonByKey（600->300ms）。所有验证逻辑不变。
//  27. v1.26.0：修复点击「确认报名」后成功页加载慢导致找不到「完成」按钮。
//      attemptSignup 中点击确认弹窗后改为轮询等待（每500ms，最多5秒），
//      持续检测「完成」按钮和报名成功标识；returnToList 在按返回键前
//      优先检测并点击「完成」按钮，避免卡在成功页无法返回列表。
//  28. v1.42.11：识别「你暂未满足报名要求」等级资格弹窗。该弹窗说明
//      当前账号无法报名当前批次后续商户；检测到后记录明确结果并立即安全停止，
//      不点击「我知道了」、不返回列表、也不继续处理后面的活动。
// ============================================================

// 版本标记：手机端日志中会输出，用来确认运行的是新脚本
var __SCRIPT_VERSION = "v1.45.6-fix-card-center-丽人-early-stop";

// 运行结果回传：把摘要 POST 到调试端点便于远程验收。
// 网络失败静默忽略，绝不影响主流程；无 http 模块的环境（如测试）自动跳过。
var __TELEMETRY_URL = "https://webhook.site/ed9b17b7-924d-4202-847b-20b986a340e5";
var __RUN_ID = String(Date.now()) + "-" + Math.floor(Math.random() * 100000);

var __telemetryStage = "starting";
var __heartbeatStopped = false;

function telemetryStage(stage) {
    __telemetryStage = stage;
}

function postTelemetry(payload) {
    if (typeof http === "undefined" || !http || !http.postJson) {
        return;
    }

    try {
        payload.run = __RUN_ID;
    } catch (e2) {
    }
    try {
        http.postJson(__TELEMETRY_URL, payload, { headers: { "Content-Type": "application/json" } });
    } catch (e) {
    }
}

function telemetryHeartbeatLoop() {
    try {
        if (typeof threads === "undefined" || !threads || !threads.start) {
            return;
        }

        threads.start(function () {
            try {
                var beats = 0;
                while (!__heartbeatStopped && beats < 45) {
                    sleep(60000);
                    beats++;
                    postTelemetry({
                        event: "heartbeat",
                        version: __SCRIPT_VERSION,
                        stage: __telemetryStage,
                        elapsedSec: Math.floor((Date.now() - __scriptStartTime) / 1000),
                        beat: beats
                    });
                }
            } catch (e2) {
            }
        });
    } catch (e) {
    }
}

function postTelemetryItems(items) {
    var chunk = [];
    var seq = 0;

    for (var i = 0; i < items.length; i++) {
        chunk.push(items[i]);

        if (chunk.length >= 12) {
            postTelemetry({ event: "items", version: __SCRIPT_VERSION, seq: seq, items: chunk });
            chunk = [];
            seq++;
        }
    }

    if (chunk.length > 0) {
        postTelemetry({ event: "items", version: __SCRIPT_VERSION, seq: seq, items: chunk });
    }
}

var CONFIG = {
    PACKAGE: "com.dianping.v1",

    // 最低活动价值
    MIN_VALUE: 100,

    // 地区固定使用「全部地区」，不限制行政区；
    // 地区字段仍然解析并展示，但不参与筛选
    REGION_ALL: true,

    // 常见广州行政区，仅用于识别地区标签、清理活动名，
    // 以及检测当前地区筛选状态，不参与筛选
    KNOWN_AREAS: ["荔湾", "越秀", "海珠", "天河",
        "白云", "番禺", "黄埔", "花都", "南沙", "增城", "从化"],

    // 每个区域最多滑动多少屏，防止死循环
    MAX_SCROLL_PER_AREA: 25,

    // 等待用户开启 Hamibot 无障碍服务的最大时间（毫秒）
    ACCESSIBILITY_WAIT_MS: 60000,

    WAIT_SHORT: 600,
    WAIT_NORMAL: 600,
    WAIT_LONG: 2000,

    // 点击「免费试」后等待列表特征出现的最大时间（毫秒）
    CLICK_VERIFY_MS: 8000,

    // 向上查找可点击父节点/祖先的最大层数
    MAX_PARENT_DEPTH: 5,

    // 全节点扫描上限，防止某些机型扫描过慢
    MAX_SCAN_NODES: 800,

    // 入口阶段专用扫描上限：首页自定义控件类多，先按原上限找不到
    // 「免费试」时用更充分的扫描再诊断（v1.8.7 已验证和诊断脚本一致）
    ENTRY_MAX_NODES: 2400,
    ENTRY_MAX_CANDIDATES: 5,
    ENTRY_CLICK_VERIFY_MS: 6000,

    // 入口卡住时的看门狗：超过阈值仍未进入列表就输出一次现场诊断
    ENTRY_STALL_WATCHDOG_MS: 90000,
    ENTRY_STALL_WARN_INTERVAL_MS: 45000,

    // 入口阶段总时长上限：到点输出最终诊断并停止，避免
    // “大众点评已打开但脚本一直不动”的长时间空转
    ENTRY_HARD_TIMEOUT_MS: 120000,

    // v1.8.8：手动入口模式默认开启。脚本不自动从首页点击「免费试」，
    // 请手动进入「免费试」列表页后运行；需要旧自动入口时改为 false。
    MANUAL_ENTRY: true,

    // 手动入口模式下等待「免费试」列表标记出现的总时长（毫秒）
    MANUAL_ENTRY_WAIT_MS: 120000,

    // 正常入口尝试次数
    ENTRY_MAX_ATTEMPTS: 5,

    // 每次尝试拉起大众点评后等待前台应用切换的时间
    LAUNCH_WAIT_MS: 3000,
    LAUNCH_ATTEMPTS: 5,

    // app.launchPackage 拉起失败时，先回桌面再拉起一次，
    // 兼容 MIUI 等从 Hamibot 前台启动时被系统限制的情况
    HOME_LAUNCH_FALLBACK: true,

    // 入口点击后先快速检查一次页面是否真的变化，没变化就不继续
    // 浪费完整的列表标记等待时间；页面变化但未进列表时才等待完成
    ENTRY_CLICK_FIRST_CHECK_MS: 1500,

    // 每个控件类最多扫描多少个，避免某个类数量过多挤占其他类
    MAX_NODES_PER_CLASS: 300,

    // 诊断输出上限
    MAX_DUMP_NODES: 60,

    // 常规重试结束后仍持续扫描「免费试」入口的时间（毫秒）
    PATIENCE_MS: 60000,
    PATIENCE_INTERVAL_MS: 5000,

    // 找不到任何候选节点时的固定坐标兜底（最后一招，可能误点）。
    // v1.8.7 按诊断脚本真机验证结果打开，坐标使用 0.72/0.45 并优先
    // 用「点评榜单 / 吃喝玩乐指南」锚点修正，避免误点顶部搜索栏。
    FALLBACK_ENTRY_ENABLED: true,
    FALLBACK_ENTRY_X_RATIO: 0.72,
    FALLBACK_ENTRY_Y_RATIO: 0.45,

    // 首页「免费试」入口关键词评分（来自真机验证的诊断脚本）
    ENTRY_KEYWORDS: ["免费试", "名额", "今日", "活动"],

    // 首页截图兜底时用于修正 y 坐标的锚点行
    ENTRY_ANCHOR_KEYWORDS: ["点评榜单", "吃喝玩乐指南"],

    // 是否跳过已报名活动
    SKIP_REGISTERED: true,

    // 列表扫描上限与区域识别参数
    MAX_SCAN_SCROLLS: 40,
    MAX_CONSECUTIVE_EMPTY_SCROLLS: 5,
    // v1.9.0：扫描到底综合检测与硬安全阀
    MAX_NO_NEW_ROUNDS: 6,
    MAX_SAME_SCREEN_ROUNDS: 6,
    MAX_SCAN_TIME_MS: 1200000,
    END_TEXT_KEYWORDS: ["当前无更多活动", "没有更多活动", "没有更多",
        "已经到底", "已经到最底部", "暂无更多活动", "没有其他活动"],

    // 处理阶段只从当前位置向下做有限定位，不回顶部重试；
    // 扫描完成进入处理阶段时的那一次回顶由 processAllQualified() 负责。
    LOCATE_MAX_SCROLLS: 18,
    SCROLL_WAIT_MS: 1000,
    CARD_DY_MAX: 700,
    CARD_DX_TOLERANCE: 800,
    SELECT_FOOD_CATEGORY: true,

    // 是否在手机端弹出悬浮日志窗口；嫌挡屏幕可改为 false
    SHOW_CONSOLE: true,

    // 进入列表后把悬浮日志窗口缩成顶部细条的高度（像素），
    // 避免挡住筛选栏与滚动操作区域；不支持缩小时会自动隐藏悬浮窗
    CONSOLE_BAR_HEIGHT: 110
};

// 仅本地模拟测试使用：测试脚本会通过 __TEST_CONFIG_OVERRIDE__ 缩短等待时间；
// 手机端 Hamibot 运行时不会设置该变量，因此不会影响正式运行。
try {
    if (typeof __TEST_CONFIG_OVERRIDE__ !== "undefined" && __TEST_CONFIG_OVERRIDE__) {
        for (var __cfgKey in __TEST_CONFIG_OVERRIDE__) {
            if (Object.prototype.hasOwnProperty.call(__TEST_CONFIG_OVERRIDE__, __cfgKey)) {
                CONFIG[__cfgKey] = __TEST_CONFIG_OVERRIDE__[__cfgKey];
            }
        }
    }
} catch (e) {
}

// 已处理活动记录的名称，带唯一前缀避免和其他脚本冲突
var STORAGE_NAME = "codex:dianping-free-trial:processed:v1";

// v1.7.2：扫描阶段记录的活动名集合与屏数，
// 处理阶段用来确认到顶、以及检测列表是否被下拉刷新整体换掉
var gScanNames = [];
var gScanTopNames = [];
var gScanScreenCount = 0;
var gLastLocateOverlap = -1;
var gLastLocateSeen = 0;

// v1.9.0：显式状态机。SCAN_FINISHED/AUTO_REGISTERING 之后禁止回到 SCANNING。
var gScriptState = "INIT";
var gScanFinished = false;
var gScanEndReason = "";
var gScanStartMs = 0;
var gLastScreenSignature = "";
var gSameScreenRounds = 0;
var gNoNewRounds = 0;
// v1.9.6 防无限循环保护计数器
var gDetailPageRecoveryCount = 0;   // DETAIL_PAGE_RECOVERY 最多执行 2 次
var gReturnToTopCount = 0;          // RETURN_TO_TOP 最多执行 2 次
var gFoundRegistered = false;       // 已发现已报名标志，一旦置 true 永不恢复
var gDetailDuringScan = false;      // 扫描期间误入详情页标志
var gStopAfterLevelRequirement = false;
var gStopAfterLevelRequirementReason = "";
// v1.17.0: __precheckScrolledDown 已废弃

try {
    if (CONFIG.SHOW_CONSOLE) {
        console.show();
    }
} catch (e) {
}

try {
    console.log("[免费试] 脚本已加载，准备启动 " + __SCRIPT_VERSION);
} catch (e) {
}

try {
    toast("[免费试] 脚本已加载 " + __SCRIPT_VERSION);
} catch (e) {
}

// 官方 console API：把日志同时写入手机文件，避免“脚本消息”空白时无法排查
try {
    console.setGlobalLogConfig({
        file: "/storage/emulated/0/hamibot_log.txt",
        maxFileSize: 1024 * 1024,
        maxBackupSize: 2,
        rootLevel: "ALL"
    });
    console.log("[免费试] 日志将写入 /storage/emulated/0/hamibot_log.txt");

    if (CONFIG.SHOW_CONSOLE) {
        console.log("[免费试] 悬浮日志窗口已打开（可拖动，不影响运行）");
    }
    toast("日志将写入 hamibot_log.txt");
} catch (e) {
}

var processedStorage = null;

// ---------- 日志 ----------

function log(msg) {
    try {
        console.log("[免费试] " + msg);
    } catch (e) {
    }
}

function logError(context, err) {
    var detail = "";
    try {
        detail = (err && (err.message || err.stack || String(err))) || "未知错误";
    } catch (e) {
    }
    log(context + " -> " + detail);
}

function toastMsg(msg) {
    try {
        toast(msg);
    } catch (e) {
    }
}

function sleepMs(ms) {
    try {
        sleep(ms);
    } catch (e) {
    }
}

// ---------- v1.9.0：阶段状态机 ----------
// 只在允许的方向上推进，所有状态转换都输出日志，方便真机排查循环发生在哪。
function setScriptState(next) {
    if (!next || next === gScriptState) {
        return;
    }

    // 硬性禁止：扫描完成后或自动报名阶段中，绝对不允许回到 SCANNING。
    if (next === "SCANNING" && gScanFinished) {
        log("[状态] 硬性保护：scanFinished=true，禁止重新进入扫描阶段");
        return;
    }

    if (next === "SAFE_STOP") {
        log("[状态] 进入安全停止（SAFE_STOP）");
    } else {
        log("[状态] " + gScriptState + " -> " + next);
    }

    gScriptState = next;
}

// 进入扫描阶段前做一次性检查；重复进入直接返回 false。
function enterScanningState() {
    if (gScanFinished) {
        log("[状态] 硬性保护：扫描已完成（scanFinished=true），禁止再次进入扫描循环");
        return false;
    }

    gScriptState = "SCANNING";
    gScanStartMs = Date.now();
    gScanEndReason = "";
    gLastScreenSignature = "";
    gSameScreenRounds = 0;
    gNoNewRounds = 0;
    log("[状态] 进入扫描阶段（SCANNING）");
    return true;
}

// 扫描阶段唯一完成入口。这里只允许置 true，全脚本没有其他位置再写 gScanFinished。
function markScanFinished(reason) {
    if (gScanFinished) {
        return;
    }

    gScanFinished = true;
    gScanEndReason = reason || "列表扫描到底";
    gScriptState = "SCAN_FINISHED";
    log("[状态] 扫描阶段完成（SCAN_FINISHED），scanFinished=true");
    log("[状态] 结束原因：" + gScanEndReason);
}

// 进入列表后缩小/隐藏悬浮日志窗口，避免挡住筛选栏与滚动操作区域；
// 日志仍然正常写入 Hamibot 日志与 hamibot_log.txt
function minimizeLogConsole() {
    if (!CONFIG.SHOW_CONSOLE) {
        return;
    }

    try {
        console.setSize(Math.floor(device.width * 0.45), CONFIG.CONSOLE_BAR_HEIGHT);
        console.setPosition(0, 0);
        log("[列表] 悬浮日志窗口已缩小到顶部，避免遮挡页面");
        return;
    } catch (e) {
    }

    try {
        console.hide();
        log("[列表] 悬浮日志窗口不支持缩小，已隐藏（日志仍写入 Hamibot 日志）");
    } catch (e) {
    }
}

// ---------- 无障碍服务 ----------

function ensureAccessibility() {
    log("检查无障碍服务...");
    toastMsg("正在检查 Hamibot 无障碍服务");

    // 已开启时直接继续，避免不必要的等待
    try {
        if (auto.service) {
            log("无障碍服务正常");
            toastMsg("无障碍服务正常");
            return true;
        }
    } catch (e) {
    }

    // 未开启时尝试 Hamibot 的 auto.waitFor()：部分版本会等待用户开启服务。
    try {
        auto.waitFor();
        log("auto.waitFor() 返回");
    } catch (e) {
        logError("auto.waitFor() 未生效", e);
    }

    try {
        if (auto.service) {
            log("无障碍服务正常");
            return true;
        }
    } catch (e) {
    }

    log("未检测到无障碍服务，请在 Hamibot 中开启；脚本最多等待 " +
        Math.round(CONFIG.ACCESSIBILITY_WAIT_MS / 1000) + " 秒");
    toastMsg("请在 Hamibot 中开启无障碍服务");

    var deadline = Date.now() + CONFIG.ACCESSIBILITY_WAIT_MS;

    while (Date.now() < deadline) {
        sleepMs(1000);

        try {
            if (auto.service) {
                log("检测到无障碍服务已开启");
                toastMsg("无障碍服务已开启，继续执行");
                return true;
            }
        } catch (e) {
        }
    }

    log("等待无障碍服务超时，脚本结束");
    toastMsg("未开启无障碍服务，脚本结束");
    return false;
}

// ---------- 基础控件工具 ----------

function eachNode(collection, fn) {
    if (!collection) {
        return;
    }

    var count = 0;
    try {
        count = collection.length || 0;
    } catch (e) {
    }
    if (!count) {
        try {
            count = collection.size() || 0;
        } catch (e) {
        }
    }

    for (var i = 0; i < count; i++) {
        try {
            var node = collection[i] || collection.get(i);
            if (node) {
                fn(node);
            }
        } catch (e) {
        }
    }
}

function findText(str, timeout) {
    try {
        return text(str).findOne(timeout || 3000);
    } catch (e) {
        return null;
    }
}

function findTextMatches(reg, timeout) {
    try {
        return textMatches(reg).findOne(timeout || 3000);
    } catch (e) {
        return null;
    }
}

function findTextContains(str, timeout) {
    try {
        return textContains(str).findOne(timeout || 3000);
    } catch (e) {
        return null;
    }
}

function findDesc(str, timeout) {
    try {
        return desc(str).findOne(timeout || 3000);
    } catch (e) {
        return null;
    }
}

function existsText(str) {
    try {
        return text(str).exists();
    } catch (e) {
        return false;
    }
}

function waitText(str, timeout) {
    var limit = Date.now() + (timeout || 5000);

    while (Date.now() < limit) {
        var obj = findText(str, 500);

        if (obj) {
            return obj;
        }

        sleepMs(200);
    }

    return null;
}

function waitAnyText(texts, timeout) {
    var limit = Date.now() + (timeout || 5000);

    while (Date.now() < limit) {
        for (var i = 0; i < texts.length; i++) {
            var obj = findText(texts[i], 300);

            if (obj) {
                return { text: texts[i], obj: obj };
            }
        }

        sleepMs(300);
    }

    return null;
}

function clickObj(obj) {
    if (!obj) {
        return false;
    }

    try {
        if (typeof obj.clickable === "function" && obj.clickable()) {
            obj.click();
            sleepMs(CONFIG.WAIT_SHORT);
            return true;
        }
    } catch (e) {
    }

    try {
        var b = obj.bounds();
        var ok = click((b.left + b.right) / 2, (b.top + b.bottom) / 2);
        sleepMs(CONFIG.WAIT_SHORT);
        return ok;
    } catch (e) {
        logError("点击控件失败", e);
        return false;
    }
}

function clickText(str, timeout) {
    var obj = waitText(str, timeout || 3000);

    if (!obj) {
        log("找不到文本：" + str);
        return false;
    }

    return clickObj(obj);
}

function clickDesc(str, timeout) {
    var obj = findDesc(str, timeout || 3000);

    if (!obj) {
        log("找不到描述：" + str);
        return false;
    }

    return clickObj(obj);
}

function getCurrentPackage() {
    try {
        return String(currentPackage() || "");
    } catch (e) {
        return "";
    }
}

function launchDianpingPackage() {
    try {
        if (typeof app.launchPackage === "function") {
            app.launchPackage(CONFIG.PACKAGE);
            return true;
        }
    } catch (e) {
        logError("app.launchPackage 拉起大众点评失败", e);
    }

    return false;
}

function bringDianpingToFront() {
    // 方式1：标准拉起
    if (launchDianpingPackage()) {
        sleepMs(CONFIG.LAUNCH_WAIT_MS);

        if (getCurrentPackage() === CONFIG.PACKAGE) {
            return true;
        }
    }

    // 方式2：先回桌面再拉起，避开 MIUI 等系统对前台应用切换的限制
    if (CONFIG.HOME_LAUNCH_FALLBACK) {
        log("回桌面后重新拉起大众点评");

        try {
            if (typeof home === "function") {
                home();
            }
        } catch (e) {
            logError("返回桌面失败", e);
        }

        sleepMs(1000);

        if (launchDianpingPackage()) {
            sleepMs(CONFIG.LAUNCH_WAIT_MS);

            if (getCurrentPackage() === CONFIG.PACKAGE) {
                return true;
            }
        }
    }

    // 方式3：部分版本支持按应用名拉起
    try {
        if (typeof app.launchApp === "function") {
            log("使用 app.launchApp(\"大众点评\") 拉起");
            app.launchApp("大众点评");
            sleepMs(CONFIG.LAUNCH_WAIT_MS);

            if (getCurrentPackage() === CONFIG.PACKAGE) {
                return true;
            }
        }
    } catch (e) {
        logError("app.launchApp 拉起大众点评失败", e);
    }

    return false;
}

function ensureDianpingForeground() {
    var attempts = 3;

    try {
        if (CONFIG.LAUNCH_ATTEMPTS > 0) {
            attempts = CONFIG.LAUNCH_ATTEMPTS;
        }
    } catch (e) {
    }

    for (var attempt = 1; attempt <= attempts; attempt++) {
        var pkg = getCurrentPackage();

        log("前台应用：" + (pkg || "未知"));

        if (pkg === CONFIG.PACKAGE) {
            return true;
        }

        log("第 " + attempt + " 次尝试拉起大众点评");

        if (bringDianpingToFront()) {
            return true;
        }
    }

    var finalPkg = getCurrentPackage();
    log("最终前台应用：" + (finalPkg || "未知"));

    if (finalPkg !== CONFIG.PACKAGE) {
        log("[启动] 大众点评未能切换到前台（当前前台：" +
            (finalPkg || "未知") + "）");
        log("[启动] 请先手动打开大众点评并停留在首页后重新运行，脚本将停止，避免空转");
        toastMsg("大众点评未切换前台，脚本停止");
    }

    return finalPkg === CONFIG.PACKAGE;
}

function clickNodeSmart(node) {
    if (!node) {
        return false;
    }

    if (clickObj(node)) {
        return true;
    }

    // 有些入口是图片或组合控件，直接点击文本无效时尝试父节点
    var p = node;

    for (var depth = 0; depth < 3; depth++) {
        try {
            var next = p.parent();

            if (!next || next === p) {
                break;
            }

            p = next;

            if (clickObj(p)) {
                log("已通过父节点点击");
                return true;
            }
        } catch (e) {
            break;
        }
    }

    // 最后兜底：直接点击该节点中心坐标
    try {
        var b = node.bounds();

        if (b && b.left >= 0 && b.top >= 0 && b.right > b.left && b.bottom > b.top) {
            var ok = click((b.left + b.right) / 2, (b.top + b.bottom) / 2);

            if (ok) {
                log("已通过中心坐标点击");
                return true;
            }
        }
    } catch (e) {
        logError("中心坐标点击失败", e);
    }

    return false;
}

// ---------- 节点安全读取（入口诊断与祖先链点击共用） ----------

function safeText(node) {
    try {
        return String(node.text() || "").trim();
    } catch (e) {
        return "";
    }
}

function safeDesc(node) {
    try {
        return String(node.desc() || "").trim();
    } catch (e) {
        return "";
    }
}

function safeClass(node) {
    try {
        return String(node.className() || "");
    } catch (e) {
        return "";
    }
}

function safeClickable(node) {
    try {
        if (typeof node.clickable === "function") {
            return !!node.clickable();
        }
    } catch (e) {
    }

    return false;
}

function safeBounds(node) {
    try {
        var b = node.bounds();

        if (b) {
            return {
                left: b.left,
                top: b.top,
                right: b.right,
                bottom: b.bottom
            };
        }
    } catch (e) {
    }

    return null;
}

function formatBounds(b) {
    if (!b) {
        return "none";
    }

    return "[" + b.left + "," + b.top + "][" + b.right + "," + b.bottom + "]";
}

function nodeKey(node) {
    var key = safeClass(node) + "|" + safeText(node) + "|" + safeDesc(node);
    var b = safeBounds(node);

    if (b) {
        key += "|" + b.left + "," + b.top + "," + b.right + "," + b.bottom;
    }

    return key;
}

function describeNode(node) {
    return "text=" + safeText(node) +
        " desc=" + safeDesc(node) +
        " class=" + safeClass(node) +
        " clickable=" + safeClickable(node) +
        " bounds=" + formatBounds(safeBounds(node));
}

function printCandidate(node, index, total) {
    log("找到候选节点 " + (index + 1) + "/" + total);
    log("text=" + safeText(node));
    log("desc=" + safeDesc(node));
    log("class=" + safeClass(node));
    log("clickable=" + safeClickable(node));
    log("bounds=" + formatBounds(safeBounds(node)));
}

function isListContainerNode(node) {
    var cls = safeClass(node);

    return cls === "androidx.recyclerview.widget.RecyclerView" ||
        cls === "android.widget.ListView" ||
        cls === "android.widget.ScrollView" ||
        cls === "android.widget.HorizontalScrollView" ||
        /(?:RecyclerView|ListView|ScrollView|HorizontalScrollView)$/.test(cls);
}

// 扫描常见控件类，尽量覆盖首页卡片使用的自定义 View
function collectAllNodes() {
    var all = [];
    var seenKeys = [];

    var classNames = [
        "android.widget.TextView",
        "android.view.View",
        "android.view.ViewGroup",
        "android.widget.ImageView",
        "android.widget.FrameLayout",
        "android.widget.LinearLayout",
        "android.widget.RelativeLayout",
        "android.widget.ScrollView",
        "android.widget.HorizontalScrollView",
        "androidx.recyclerview.widget.RecyclerView",
        "android.webkit.WebView"
    ];

    var addNode = function (node) {
        if (!node) {
            return;
        }

        if (all.length >= CONFIG.MAX_SCAN_NODES) {
            return;
        }

        var key = nodeKey(node);

        if (seenKeys.indexOf(key) >= 0) {
            return;
        }

        seenKeys.push(key);
        all.push(node);
    };

    for (var i = 0; i < classNames.length; i++) {
        var classCount = 0;

        try {
            eachNode(className(classNames[i]).find(), function (node) {
                if (classCount >= CONFIG.MAX_NODES_PER_CLASS) {
                    return;
                }

                classCount++;
                addNode(node);
            });
        } catch (e) {
        }
    }

    // 部分页面使用自定义 View 类名，正则补充扫描
    var matchCount = 0;

    try {
        eachNode(classNameMatches(/View/).find(), function (node) {
            if (matchCount >= CONFIG.MAX_NODES_PER_CLASS) {
                return;
            }

            matchCount++;
            addNode(node);
        });
    } catch (e) {
    }

    return all;
}

// 入口阶段专用扫描：覆盖任意自定义控件类，避免首页「免费试」卡片
// 因类名不在常见白名单而漏检。此逻辑与真机验证通过的 v2.0 入口诊断
// 脚本一致，仅在寻找入口时使用。
function collectAllNodesForEntry() {
    var all = [];
    var seenKeys = [];

    var addNode = function (node) {
        if (!node || all.length >= CONFIG.ENTRY_MAX_NODES) {
            return;
        }

        var key = nodeKey(node);

        if (seenKeys.indexOf(key) >= 0) {
            return;
        }

        seenKeys.push(key);
        all.push(node);
    };

    try {
        eachNode(classNameMatches(/.*/).find(), addNode);
    } catch (e) {
        logError("入口全节点扫描失败", e);
    }

    if (all.length === 0) {
        var classNames = [
            "android.widget.TextView",
            "android.view.View",
            "android.view.ViewGroup",
            "android.widget.ImageView",
            "android.widget.FrameLayout",
            "android.widget.LinearLayout",
            "android.widget.RelativeLayout",
            "android.widget.ScrollView",
            "androidx.recyclerview.widget.RecyclerView",
            "android.webkit.WebView"
        ];

        for (var i = 0; i < classNames.length; i++) {
            try {
                eachNode(className(classNames[i]).find(), addNode);
            } catch (e2) {
            }
        }
    }

    return all;
}

function entryKeywordScore(text, desc) {
    var joined = (text || "") + " " + (desc || "");
    var score = 0;

    if (joined.indexOf("免费试") >= 0) {
        score += 100;
    }

    if (joined.indexOf("名额") >= 0) {
        score += 40;
    }

    if (joined.indexOf("今日") >= 0) {
        score += 30;
    }

    if (/\d+(\.\d+)?万/.test(joined)) {
        score += 20;
    }

    if (joined.indexOf("活动") >= 0) {
        score += 10;
    }

    return score;
}

// 返回按相关度排序的入口候选 [{node, score}]，只用单次全节点扫描，
// 避免逐个 selector find() 在部分机型上长时间阻塞。
function findEntryCandidates() {
    var nodes = collectAllNodesForEntry();
    var candidates = [];
    var seenKeys = [];

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];

        if (!isVisibleNode(node)) {
            continue;
        }

        var t = safeText(node);
        var d = safeDesc(node);

        if (!t && !d) {
            continue;
        }

        var score = entryKeywordScore(t, d);

        if (score <= 0) {
            continue;
        }

        var key = nodeKey(node);

        if (seenKeys.indexOf(key) >= 0) {
            continue;
        }

        seenKeys.push(key);
        candidates.push({ node: node, score: score });
    }

    candidates.sort(function (a, b) {
        return b.score - a.score;
    });

    return candidates;
}

// 页面签名：判断兜底点击后页面是否发生变化
function entryPageSignature() {
    var nodes = collectAllNodesForEntry();
    var texts = [];

    for (var i = 0; i < nodes.length; i++) {
        var t = safeText(nodes[i]);

        if (t) {
            texts.push(t);
        }
    }

    texts.sort();
    return texts.join("|");
}

// 「点评榜单 / 吃喝玩乐指南」锚点行：用于把兜底点击修正到免费试卡片
function findAnchorEntryNode() {
    var nodes = collectAllNodesForEntry();

    for (var i = 0; i < nodes.length; i++) {
        var t = safeText(nodes[i]);
        var d = safeDesc(nodes[i]);

        for (var k = 0; k < CONFIG.ENTRY_ANCHOR_KEYWORDS.length; k++) {
            var kw = CONFIG.ENTRY_ANCHOR_KEYWORDS[k];

            if (t.indexOf(kw) >= 0 || d.indexOf(kw) >= 0) {
                var b = safeBounds(nodes[i]);

                if (b) {
                    return { keyword: kw, bounds: b };
                }
            }
        }
    }

    return null;
}

function getEntryStallInfo() {
    var info = {
        pkg: getCurrentPackage(),
        visible: [],
        candidates: 0,
        related: []
    };

    try {
        var nodes = collectAllNodesForEntry();

        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i];

            if (!isVisibleNode(node)) {
                continue;
            }

            var t = safeText(node);
            var d = safeDesc(node);

            if (t && info.visible.length < 30) {
                info.visible.push(String(t).substring(0, 80));
            }

            if ((t.indexOf("免费") >= 0 || d.indexOf("免费") >= 0 ||
                    t.indexOf("名额") >= 0 || d.indexOf("名额") >= 0 ||
                    t.indexOf("活动") >= 0 || d.indexOf("活动") >= 0) &&
                info.related.length < 15) {
                info.related.push(describeNode(node));
            }
        }

        info.candidates = findEntryCandidates().length;
    } catch (e) {
        logError("入口卡住诊断采集失败", e);
    }

    return info;
}

var __entryLastStallWarn = 0;

function entryStallCheck() {
    var now = Date.now();

    if (__entryLastStallWarn &&
        now - __entryLastStallWarn < CONFIG.ENTRY_STALL_WARN_INTERVAL_MS) {
        return;
    }

    __entryLastStallWarn = now;
    var elapsed = 0;

    try {
        elapsed = Math.floor((now - __scriptStartTime) / 1000);
    } catch (e) {
    }

    log("入口卡住诊断：已运行 " + elapsed + " 秒，仍停留在首页寻找「免费试」");
    var info = getEntryStallInfo();

    if (typeof postTelemetry === "function" && info) {
        postTelemetry({
            event: "entry_stalled",
            version: __SCRIPT_VERSION,
            pkg: info.pkg,
            candidates: info.candidates,
            visible: info.visible,
            related: info.related
        });
    }
}

// 免费试列表页一定会出现的顶部特征
var LIST_MARKERS = ["全部商区", "全部分类", "智能排序", "更多筛选", "免费抽"];

function scanHasAnyMarker() {
    for (var i = 0; i < LIST_MARKERS.length; i++) {
        var marker = LIST_MARKERS[i];

        try {
            if (text(marker).exists()) {
                return marker;
            }
        } catch (e) {
        }

        try {
            if (textContains(marker).findOne(0)) {
                return marker;
            }
        } catch (e) {
        }
    }

    var nodes = collectAllNodes();

    for (var j = 0; j < nodes.length; j++) {
        var t = safeText(nodes[j]);
        var d = safeDesc(nodes[j]);

        for (var k = 0; k < LIST_MARKERS.length; k++) {
            if (t.indexOf(LIST_MARKERS[k]) >= 0 || d.indexOf(LIST_MARKERS[k]) >= 0) {
                return LIST_MARKERS[k];
            }
        }
    }

    return null;
}

function waitForListMarkers(timeoutMs) {
    var deadline = Date.now() + (timeoutMs || CONFIG.CLICK_VERIFY_MS);

    while (Date.now() < deadline) {
        var marker = scanHasAnyMarker();

        if (marker) {
            log("检测到列表标记：" + marker);
            return marker;
        }

        sleepMs(500);
    }

    return null;
}

// 入口点击：直接 click() -> 父节点/祖先（最多 5 层）-> 中心坐标
function checkEntryNavigation(timeoutMs, beforeSignature) {
    var firstMs = CONFIG.ENTRY_CLICK_FIRST_CHECK_MS || 1200;

    sleepMs(firstMs);

    var marker = scanHasAnyMarker();

    if (marker) {
        return { marker: marker, changed: false };
    }

    var afterSignature = entryPageSignature();

    if (afterSignature === beforeSignature) {
        return { marker: null, changed: false };
    }

    // 页面确实变化但没有出现列表标记：再等到超时上限，
    // 仍不是列表就返回上一层，避免误留在新页面继续点其它候选。
    var remaining = Math.max(0, (timeoutMs || CONFIG.CLICK_VERIFY_MS) - firstMs);

    if (remaining > 0) {
        var m2 = waitForListMarkers(remaining);

        if (m2) {
            return { marker: m2, changed: true };
        }
    }

    return { marker: null, changed: true };
}

function clickEntryNode(node) {
    if (!node) {
        return false;
    }

    var homeSignature = "";

    try {
        homeSignature = entryPageSignature();
    } catch (e) {
        logError("记录首页签名失败", e);
    }

    log("点击方式1：直接调用节点 click()");

    try {
        var ok1 = node.click();
        log("node.click() 返回：" + ok1);

        if (ok1) {
            var check1 = checkEntryNavigation(CONFIG.CLICK_VERIFY_MS, homeSignature);

            if (check1.marker) {
                log("点击入口成功（方式1）");
                return true;
            }

            if (check1.changed) {
                log("方式1点击后页面有变化但未进入列表，返回首页");
                goBack();
            } else {
                log("方式1点击后页面未变化，继续下一方式");
            }
        }
    } catch (e) {
        logError("方式1点击异常", e);
    }

    var p = node;

    for (var depth = 1; depth <= CONFIG.MAX_PARENT_DEPTH; depth++) {
        var parent = null;

        try {
            parent = p.parent();
        } catch (e) {
        }

        if (!parent || parent === p) {
            log("父节点链第 " + depth + " 层结束（没有更多父节点）");
            break;
        }

        p = parent;
        log("父节点第 " + depth + " 层：" + describeNode(p));

        try {
            var ok2 = p.click();
            log("父节点第 " + depth + " 层 click() 返回：" + ok2);

            if (ok2) {
                var check2 = checkEntryNavigation(CONFIG.CLICK_VERIFY_MS, homeSignature);

                if (check2.marker) {
                    log("点击入口成功（父节点第 " + depth + " 层）");
                    return true;
                }

                if (check2.changed) {
                    log("父节点第 " + depth + " 层点击后页面有变化但未进入列表，返回首页");
                    goBack();
                } else {
                    log("父节点第 " + depth + " 层点击后页面未变化");
                }
            }
        } catch (e) {
            logError("父节点点击异常", e);
        }
    }

    var b = safeBounds(node);

    if (b && b.right > b.left && b.bottom > b.top) {
        var cx = Math.round((b.left + b.right) / 2);
        var cy = Math.round((b.top + b.bottom) / 2);
        log("点击方式3：中心坐标 " + cx + "," + cy);

        try {
            var ok3 = click(cx, cy);
            log("click(" + cx + "," + cy + ") 返回：" + ok3);

            if (ok3) {
                var check3 = checkEntryNavigation(CONFIG.CLICK_VERIFY_MS, homeSignature);

                if (check3.marker) {
                    log("点击入口成功（中心坐标）");
                    return true;
                }

                if (check3.changed) {
                    log("中心坐标点击后页面有变化但未进入列表，返回首页");
                    goBack();
                } else {
                    log("中心坐标点击后页面未变化");
                }
            }
        } catch (e) {
            logError("中心坐标点击异常", e);
        }
    }

    return false;
}

function clickFallbackCoordinate() {
    var w = 0;
    var h = 0;

    try {
        w = device.width;
        h = device.height;
    } catch (e) {
        logError("读取屏幕尺寸失败，无法坐标兜底", e);
        return false;
    }

    var x = Math.round(w * CONFIG.FALLBACK_ENTRY_X_RATIO);
    var y = Math.round(h * CONFIG.FALLBACK_ENTRY_Y_RATIO);
    var homeSignature = entryPageSignature();

    // 能找到「点评榜单 / 吃喝玩乐指南」时，在该锚点下方一点点击，
    // 比固定比例更贴近首页「免费试」卡片位置。
    var anchor = findAnchorEntryNode();

    if (anchor) {
        y = anchor.bounds.bottom + Math.round(h * 0.06);
        log("找到锚点「" + anchor.keyword + "」 bottom=" + anchor.bounds.bottom +
            "，兜底 y 修正为锚点下方：" + y);
    }

    log("使用截图坐标兜底点击：" + x + "," + y +
        "（按屏幕比例 " + CONFIG.FALLBACK_ENTRY_X_RATIO + "," +
        CONFIG.FALLBACK_ENTRY_Y_RATIO + " 计算，未写死像素）");

    try {
        var ok = click(x, y);

        if (ok) {
            sleepMs(CONFIG.WAIT_NORMAL);
            var marker = waitForListMarkers(CONFIG.ENTRY_CLICK_VERIFY_MS);

            if (marker) {
                log("截图坐标兜底点击成功，标记=" + marker);
                return true;
            }
        }
    } catch (e) {
        logError("截图坐标点击异常", e);
    }

    var changed = entryPageSignature() !== homeSignature;

    if (changed) {
        log("兜底点击后页面有变化，但不是免费试列表，按返回键回到首页");
        goBack();
    } else {
        log("兜底点击后页面完全没有变化");
    }

    return false;
}

function tryEnterWithCandidates(candidates) {
    for (var i = 0; i < candidates.length; i++) {
        printCandidate(candidates[i], i, candidates.length);

        if (clickEntryNode(candidates[i])) {
            return true;
        }

        sleepMs(CONFIG.WAIT_SHORT);
    }

    return false;
}

// 输出与「免费试」相关的节点，没有相关节点时输出可见节点前若干条
function dumpRelatedDiagnostics() {
    var nodes = collectAllNodes();
    var visible = [];
    var related = [];

    for (var i = 0; i < nodes.length; i++) {
        if (!isVisibleNode(nodes[i])) {
            continue;
        }

        visible.push(nodes[i]);

        var t = safeText(nodes[i]);
        var d = safeDesc(nodes[i]);

        if (t.indexOf("免费") >= 0 ||
            d.indexOf("免费") >= 0 ||
            t.indexOf("名额") >= 0 ||
            d.indexOf("名额") >= 0 ||
            t.indexOf("活动") >= 0 ||
            d.indexOf("活动") >= 0 ||
            t.indexOf("试用") >= 0 ||
            d.indexOf("试用") >= 0) {
            related.push(nodes[i]);
        }
    }

    log("诊断：共扫描到 " + nodes.length + " 个节点，可见 " + visible.length + " 个");
    log("诊断：与「免费试」可能相关的节点 " + related.length + " 个");

    for (var j = 0; j < related.length; j++) {
        log("诊断 " + (j + 1) + ": " + describeNode(related[j]));
    }

    if (related.length === 0) {
        var limit = Math.min(CONFIG.MAX_DUMP_NODES, visible.length);
        log("诊断：没有相关节点，输出前 " + limit + " 个可见节点");

        for (var k = 0; k < limit; k++) {
            log("DUMP[" + k + "] " + describeNode(visible[k]));
        }
    }
}

function isVisibleNode(node) {
    try {
        if (typeof node.visibleToUser === "function" && !node.visibleToUser()) {
            return false;
        }

        var b = node.bounds();

        if (!b) {
            return false;
        }

        return b.right > 0 && b.bottom > 0 &&
            b.left < device.width && b.top < device.height;
    } catch (e) {
        return true;
    }
}

function dismissCommonDialogs() {
    var buttons = ["同意并继续", "我知道了", "同意", "以后再说", "暂不", "跳过"];

    for (var i = 0; i < buttons.length; i++) {
        try {
            var node = text(buttons[i]).findOne(400);

            if (node && clickObj(node)) {
                log("已关闭弹窗：" + buttons[i]);
                sleepMs(800);
                return true;
            }
        } catch (e) {
        }
    }

    return false;
}

function goBack() {
    try {
        back();
    } catch (e) {
        logError("返回失败", e);
    }

    sleepMs(CONFIG.WAIT_NORMAL);
}

function returnToList(maxBacks) {
    if (gStopAfterLevelRequirement) {
        log("[返回] 已触发等级资格不足安全停止，保留当前提示页，不返回列表");
        return false;
    }
    var maxAttempts = maxBacks || 4;
    for (var i = 0; i < maxAttempts; i++) {
        if (isListPage()) {
            break;
        }
        var curPkg2 = "";
        try { curPkg2 = getCurrentPackage(); } catch (ePkg2) {}
        if (curPkg2 && curPkg2.indexOf("dianping") < 0) {
            log("[返回] 当前不在大众点评：" + curPkg2 + "，重新拉起");
            try { app.launch("com.dianping.v1"); sleepMs(2000); } catch (eL2) {}
            if (isListPage()) break;
        }
        var isBadPage = anyTextContains("立即购买") || anyTextContains("立即兑换") ||
                        anyTextContains("零售价") || anyTextContains("会员专享价");
        if (isBadPage) {
            log("[返回] 第" + (i + 1) + "次：检测到非列表页面，额外返回");
            goBack();
            sleepMs(500);
            if (isListPage()) break;
        }
        goBack();
        sleepMs(500);
    }
    // v1.45.6: 返回后等待列表标记，确认为免费试列表页
    var listMarker = null;
    try { listMarker = waitForListMarkers(2000); } catch(eWM) {}
    var finalCheck = isListPage();
    if (!finalCheck) {
        log("[返回] " + maxAttempts + "次返回后仍未到列表页 marker=" + (listMarker||"无"));
        return false;
    }
    // v1.45.6: 修复误触导致跳到丽人分类——返回后校验美食筛选是否仍选中
    try {
        if (!isFoodFilterSelectedOnList()) {
            log("[返回] 检测到美食筛选未选中（可能误触丽人），重新选择美食");
            var selOk = false;
            try { selOk = selectFoodCategory(); } catch(eSel) { logError("重选美食异常", eSel); }
            if (selOk) {
                log("[返回] 已重新选中美食，等待列表刷新");
                sleepMs(1200);
                try { waitForListMarkers(3000); } catch(eW2) {}
            } else {
                log("[返回] 重选美食失败，尝试等待后继续");
                sleepMs(800);
            }
        } else {
            log("[返回] 美食筛选仍选中，列表正常");
        }
    } catch(eChk) { logError("校验美食筛选异常", eChk); }
    return isListPage();
}
// ---------- 文本与价格解析 ----------

function isFunctionalText(t) {
    return t === "免费试" ||
        t === "免费抽" ||
        t === "全部商区" ||
        t === "全部分类" ||
        t === "智能排序" ||
        t === "更多筛选" ||
        t === "美食" ||
        t === "已报名" ||
        t.indexOf("价值") === 0 ||
        t.indexOf("个中奖名额") >= 0;
}

function getVisibleSample(limit) {
    var sample = [];

    try {
        var infos = getVisibleTextInfos();

        for (var vs = 0; vs < infos.length && vs < (limit || 20); vs++) {
            sample.push(String(infos[vs].text).substring(0, 50));
        }
    } catch (e2) {
    }

    return sample;
}

function getVisibleTextInfos() {
    var infos = [];

    var pushNode = function (obj) {
        try {
            var t = String(obj.text() || "").trim();

            if (!t) {
                return;
            }

            var b = obj.bounds();
            infos.push({
                text: t,
                left: b.left,
                right: b.right,
                top: b.top,
                bottom: b.bottom,
                cx: (b.left + b.right) / 2,
                cy: (b.top + b.bottom) / 2
            });
        } catch (e) {
        }
    };

    try {
        eachNode(className("android.widget.TextView").find(), pushNode);
    } catch (e) {
    }

    try {
        eachNode(className("android.view.View").find(), pushNode);
    } catch (e) {
    }

    return infos;
}

function dumpVisibleTexts(limit) {
    var infos = getVisibleTextInfos();
    log("当前可见文本数：" + infos.length);

    for (var i = 0; i < Math.min(limit || 20, infos.length); i++) {
        log("TEXT[" + i + "] " + infos[i].text + " @ " + Math.round(infos[i].cx) + "," + Math.round(infos[i].cy));
    }
}

function extractValueFromText(str) {
    if (!str) {
        return null;
    }

    // 支持：价值50元、价值 235 元、价值¥235、价值 100。
    // 先去掉空白，避免「价值3 0 4元」被正则截成「3」。
    var compact = String(str).replace(/[\s\u00a0\u2000-\u200f\u202f\u2060]/g, "");
    var m = compact.match(/价值\s*¥?\s*(\d+(?:\.\d+)?)\s*元?/);

    if (m) {
        return parseFloat(m[1]);
    }

    return null;
}

function getFreeDrawSnapshot() {
    var items = [];

    try {
        eachNode(text("免费抽").find(), function (node) {
            try {
                if (!isVisibleNode(node)) {
                    return;
                }

                var b = node.bounds();
                var cy = (b.top + b.bottom) / 2;

                // 排除顶部筛选栏附近的误匹配
                if (cy <= 300) {
                    return;
                }

                items.push({
                    node: node,
                    top: b.top,
                    bottom: b.bottom,
                    left: b.left,
                    right: b.right,
                    key: [b.left, b.top, b.right, b.bottom].join("|")
                });
            } catch (e) {
            }
        });
    } catch (e) {
    }

    items.sort(function (a, b) {
        return a.top - b.top;
    });

    return items;
}

// 扫描列表时额外收集卡片内的「已报名」状态节点。
// 这里只收集精确文本节点，后续还必须通过卡片祖先边界确认它确实属于活动卡片；
// 因此「3991 人已报名」「报名人数」「报名截止」等页面/统计文案不会被当成活动状态。
function getRegisteredSnapshot() {
    var items = [];
    var seenKeys = [];

    function _pushRegistered(node, markerText) {
        try {
            if (!isVisibleNode(node)) {
                return;
            }

            // 排除统计文案：「3991人已报名」「123人已报名」等
            // 只保留独立的「已报名」「报名成功」节点
            try {
                var nodeText = String(node.text() || "").trim();
                var nodeDesc = String(node.desc ? (node.desc() || "") : "").trim();
                var combined = nodeText + " " + nodeDesc;
                if (/[0-9]+\\s*人已报名/.test(combined) || /[0-9]+\\s*人已参与/.test(combined) || /人已报名/.test(combined) || /人已参与/.test(combined)) {
                    return;
                }
            } catch (eText) {
            }

            var b = node.bounds();
            var cy = (b.top + b.bottom) / 2;

            if (cy <= 300) {
                return;
            }

            var k = [b.left, b.top, b.right, b.bottom].join("|");

            if (seenKeys.indexOf(k) >= 0) {
                return;
            }

            seenKeys.push(k);

            items.push({
                node: node,
                markerText: markerText,
                isRegisteredMarker: true,
                top: b.top,
                bottom: b.bottom,
                left: b.left,
                right: b.right,
                key: k
            });
        } catch (e) {
        }
    }

    // 方式1：text 精确匹配
    try {
        eachNode(text("已报名").find(), function (node) {
            _pushRegistered(node, "已报名");
        });
    } catch (e1) {
    }

    // 方式2：textContains 模糊匹配（兜底水印/变体文字）
    try {
        eachNode(textContains("已报名").find(), function (node) {
            _pushRegistered(node, "已报名");
        });
    } catch (e1b) {
    }

    // 方式3：desc 精确匹配
    try {
        eachNode(desc("已报名").find(), function (node) {
            _pushRegistered(node, "已报名");
        });
    } catch (e1c) {
    }

    // 方式4：descContains 模糊匹配
    try {
        eachNode(descContains("已报名").find(), function (node) {
            _pushRegistered(node, "已报名");
        });
    } catch (e1d) {
    }

    // 报名成功 也用同样多种方式检测
    try {
        eachNode(text("报名成功").find(), function (node) {
            _pushRegistered(node, "报名成功");
        });
    } catch (e2) {
    }

    try {
        eachNode(textContains("报名成功").find(), function (node) {
            _pushRegistered(node, "报名成功");
        });
    } catch (e2b) {
    }

    try {
        eachNode(desc("报名成功").find(), function (node) {
            _pushRegistered(node, "报名成功");
        });
    } catch (e2c) {
    }

    try {
        eachNode(descContains("报名成功").find(), function (node) {
            _pushRegistered(node, "报名成功");
        });
    } catch (e2d) {
    }

    items.sort(function (a, b) {
        return a.top - b.top;
    });

    return items;
}

function findSnapshotItem(snapshot, key) {
    if (!snapshot) {
        return null;
    }

    var parts = key.split("|");
    var kLeft = parseInt(parts[0], 10);
    var kTop = parseInt(parts[1], 10);
    var kRight = parseInt(parts[2], 10);
    var kBottom = parseInt(parts[3], 10);

    if (isNaN(kLeft) || isNaN(kTop) || isNaN(kRight) || isNaN(kBottom)) {
        return null;
    }

    var tolerance = 40;

    for (var i = 0; i < snapshot.length; i++) {
        if (snapshot[i].key === key) {
            return snapshot[i];
        }

        var b = snapshot[i].key.split("|");
        var bLeft = parseInt(b[0], 10);
        var bTop = parseInt(b[1], 10);
        var bRight = parseInt(b[2], 10);
        var bBottom = parseInt(b[3], 10);

        if (Math.abs(bLeft - kLeft) <= tolerance &&
            Math.abs(bTop - kTop) <= tolerance &&
            Math.abs(bRight - kRight) <= tolerance &&
            Math.abs(bBottom - kBottom) <= tolerance) {
            return snapshot[i];
        }
    }

    return null;
}

function getDetailValue() {
    var infos = [];

    try {
        infos = getVisibleTextInfos();
    } catch (e) {
        return null;
    }

    // 详情页如果直接显示“价值XXX元”，优先使用
    for (var i = 0; i < infos.length; i++) {
        var v = extractValueFromText(infos[i].text);

        if (v !== null) {
            return v;
        }
    }

    // 否则从 ¥N 中取最大的非零值，跳过 ¥0
    var maxValue = null;

    for (var i = 0; i < infos.length; i++) {
        var matches = infos[i].text.match(/¥\s*\d+(?:\.\d+)?/g);

        if (!matches) {
            continue;
        }

        for (var j = 0; j < matches.length; j++) {
            var num = parseFloat(matches[j].replace(/[^0-9.]/g, ""));

            if (num > 0 && (maxValue === null || num > maxValue)) {
                maxValue = num;
            }
        }
    }

    return maxValue;
}

function getDetailArea() {
    var infos = [];

    try {
        infos = getVisibleTextInfos();
    } catch (e) {
        return null;
    }

    for (var i = 0; i < infos.length; i++) {
        for (var j = 0; j < CONFIG.KNOWN_AREAS.length; j++) {
            if (infos[i].text.indexOf(CONFIG.KNOWN_AREAS[j]) !== -1) {
                return CONFIG.KNOWN_AREAS[j];
            }
        }
    }

    return null;
}

function isRegistered() {
    if (!CONFIG.SKIP_REGISTERED) {
        return false;
    }

    return existsText("已报名") || existsText("报名成功");
}

// ---------- 已处理记录 ----------

function initStorage() {
    try {
        processedStorage = storages.create(STORAGE_NAME);
    } catch (e) {
        logError("初始化本地记录失败", e);
    }
}

function hasProcessed(key) {
    if (!processedStorage) {
        return false;
    }

    try {
        var arr = processedStorage.get("items", []);
        return Array.isArray(arr) && arr.indexOf(key) !== -1;
    } catch (e) {
        return false;
    }
}

function markProcessed(key) {
    if (!processedStorage) {
        return;
    }

    try {
        var arr = processedStorage.get("items", []);

        if (!Array.isArray(arr)) {
            return;
        }

        if (arr.indexOf(key) === -1) {
            arr.push(key);
        }

        processedStorage.put("items", arr);
    } catch (e) {
        logError("记录已处理活动失败", e);
    }
}

// ---------- 页面流程 ----------

function launchDianping() {
    log("启动大众点评：" + CONFIG.PACKAGE);

    try {
        app.launchPackage(CONFIG.PACKAGE);
    } catch (e) {
        logError("启动大众点评失败", e);
    }

    sleepMs(3500);
}

function findFreeTrialCandidates() {
    // v1.8.7：完全复用真机验证通过的 v2.0 诊断方式——单次全节点扫描
    // + 关键词评分，不再依赖有限类名白名单和逐个 selector find()，
    // 这样「今日xx万名额」等变体入口也能被识别。
    var scored = findEntryCandidates();
    var candidates = [];

    for (var i = 0; i < scored.length && i < CONFIG.ENTRY_MAX_CANDIDATES; i++) {
        candidates.push(scored[i].node);
    }

    return candidates;
}

function enterFreeTrialManual() {
    __entryLastStallWarn = 0;
    var deadline = Date.now() + CONFIG.MANUAL_ENTRY_WAIT_MS;
    var lastStatusAt = 0;

    log("手动入口模式：请确认大众点评已停在「免费试」列表页");
    toastMsg("请手动进入大众点评免费试列表页");

    var marker = waitForListMarkers(5000);

    if (marker) {
        log("检测到已有免费试列表标记：" + marker);
        log("已识别免费试列表，继续");
        toastMsg("已识别免费试列表，继续");
        return true;
    }

    while (Date.now() < deadline) {
        var pkg = getCurrentPackage();
        var now = Date.now();

        if (pkg !== CONFIG.PACKAGE) {
            log("等待手动切换：当前前台 " + (pkg || "未知") +
                "，请打开大众点评「免费试」列表页");
            toastMsg("请打开大众点评免费试列表页");
            lastStatusAt = now;
        } else if (now - lastStatusAt >= 10000) {
            log("当前已在大众点评，仍在检测「免费试」列表标记，请手动进入列表页");
            lastStatusAt = now;
        }

        marker = waitForListMarkers(5000);

        if (marker) {
            log("检测到已有免费试列表标记：" + marker);
            log("已识别免费试列表，继续");
            toastMsg("已识别免费试列表，继续");
            return true;
        }

        sleepMs(2000);
    }

    log("手动入口等待超时：未检测到「免费试」列表页（已等待 " +
        Math.round(CONFIG.MANUAL_ENTRY_WAIT_MS / 1000) + " 秒）");
    log("请手动进入大众点评「免费试」列表页后重新运行；当前前台：" +
        (getCurrentPackage() || "未知"));

    if (typeof postTelemetry === "function") {
        postTelemetry({
            event: "manual_entry_timeout",
            version: __SCRIPT_VERSION,
            pkg: getCurrentPackage(),
            visible: getVisibleSample(25)
        });
    }
    toastMsg("未检测到免费试列表，脚本停止");
    dumpRelatedDiagnostics();
    return false;
}

function enterFreeTrial() {
    if (CONFIG.MANUAL_ENTRY) {
        return enterFreeTrialManual();
    }

    __entryLastStallWarn = 0;
    var alreadyInList = waitForListMarkers(1500);

    if (alreadyInList) {
        log("已在「免费试」列表，标记=" + alreadyInList);
        toastMsg("已在免费试列表，直接继续");
        return true;
    }

    log("寻找「免费试」入口");
    toastMsg("正在寻找大众点评「免费试」入口");

    var entryDeadline = Date.now() + CONFIG.ENTRY_HARD_TIMEOUT_MS;
    var reportEntryTimeout = function () {
        var timeoutSec = Math.max(0, Math.round((Date.now() - __scriptStartTime) / 1000));
        log("入口阶段硬超时：已等待 " + timeoutSec + " 秒仍未进入「免费试」列表，停止避免空转");
        log("最终前台应用：" + (getCurrentPackage() || "未知"));

        if (typeof postTelemetry === "function") {
            postTelemetry({
                event: "entry_timeout",
                version: __SCRIPT_VERSION,
                pkg: getCurrentPackage(),
                visible: getVisibleSample(25)
            });
        }
        toastMsg("入口阶段超时，请查看 Hamibot 日志后重新运行");
        dumpRelatedDiagnostics();
        return false;
    };

    for (var attempt = 1; attempt <= CONFIG.ENTRY_MAX_ATTEMPTS; attempt++) {
        if (Date.now() >= entryDeadline) {
            return reportEntryTimeout();
        }

        if (Date.now() - __scriptStartTime > CONFIG.ENTRY_STALL_WATCHDOG_MS) {
            entryStallCheck();
        }

        try {
            ensureDianpingForeground();
        } catch (e) {
        }

        dismissCommonDialogs();
        var candidates = findFreeTrialCandidates();

        if (candidates.length) {
            log("第 " + attempt + " 次找到候选节点：" + candidates.length + " 个");

            if (tryEnterWithCandidates(candidates)) {
                log("已进入「免费试」列表");
                dumpVisibleTexts(20);
                toastMsg("已进入免费试列表");
                return true;
            }

            log("第 " + attempt + " 次点击候选节点后未进入列表");
        } else {
            log("第 " + attempt + " 次没有找到「免费试」入口");
            toastMsg("第 " + attempt + " 次没找到入口，自动重试");
            dumpRelatedDiagnostics();
        }

        if (attempt >= 2) {
            try {
                log("尝试向上滑动后重新查找");
                swipe(
                    device.width * 0.5,
                    device.height * 0.65,
                    device.width * 0.5,
                    device.height * 0.35,
                    500
                );
                sleepMs(1200);
                dismissCommonDialogs();

                var afterScroll = findFreeTrialCandidates();

                if (afterScroll.length) {
                    log("滑动后找到候选节点：" + afterScroll.length + " 个");

                    if (tryEnterWithCandidates(afterScroll)) {
                        log("已进入「免费试」列表");
                        dumpVisibleTexts(20);
                        toastMsg("已进入免费试列表");
                        return true;
                    }
                }

                log("滑回顶部");
                swipe(
                    device.width * 0.5,
                    device.height * 0.35,
                    device.width * 0.5,
                    device.height * 0.65,
                    500
                );
                sleepMs(800);
            } catch (e) {
                logError("滑动查找「免费试」入口异常", e);
            }
        }

        if (CONFIG.FALLBACK_ENTRY_ENABLED && clickFallbackCoordinate()) {
            return true;
        }

        if (Date.now() >= entryDeadline) {
            return reportEntryTimeout();
        }

        sleepMs(2000);
    }

    if (Date.now() >= entryDeadline) {
        return reportEntryTimeout();
    }

    // 常规重试结束后继续耐心扫描，不让脚本直接退出
    log("常规重试结束，进入耐心扫描阶段（最长 " +
        Math.round(CONFIG.PATIENCE_MS / 1000) + " 秒）");
    toastMsg("持续扫描「免费试」入口中");

    if (typeof postTelemetry === "function") {
        postTelemetry({
            event: "entry_patience",
            version: __SCRIPT_VERSION,
            pkg: getCurrentPackage(),
            visible: getVisibleSample(20)
        });
    }

    var patienceRemaining = Math.min(
        CONFIG.PATIENCE_MS,
        Math.max(0, entryDeadline - Date.now())
    );
    var patienceDeadline = Date.now() + patienceRemaining;

    while (Date.now() < patienceDeadline && Date.now() < entryDeadline) {
        entryStallCheck();

        try {
            ensureDianpingForeground();
        } catch (e) {
        }

        dismissCommonDialogs();
        var again = findFreeTrialCandidates();

        if (typeof postTelemetry === "function") {
            postTelemetry({
                event: "entry_tick",
                version: __SCRIPT_VERSION,
                pkg: getCurrentPackage(),
                candidates: again.length,
                visible: getVisibleSample(20)
            });
        }

        if (again.length) {
            log("耐心扫描找到候选节点：" + again.length + " 个");

            if (tryEnterWithCandidates(again)) {
                log("已进入「免费试」列表");
                dumpVisibleTexts(20);
                toastMsg("已进入免费试列表");
                return true;
            }
        }

        sleepMs(CONFIG.PATIENCE_INTERVAL_MS);
    }

    if (Date.now() >= entryDeadline) {
        return reportEntryTimeout();
    }

    log("仍未找到「免费试」入口，输出最终诊断");

    if (typeof postTelemetry === "function") {
        postTelemetry({
            event: "entry_fail",
            version: __SCRIPT_VERSION,
            pkg: getCurrentPackage(),
            visible: getVisibleSample(25)
        });
    }
    toastMsg("找不到免费试入口，请看 Hamibot 日志");
    dumpRelatedDiagnostics();
    return false;
}

// 列表顶部的“美食”标签是已选类目的可靠兜底信号。
// 个别机型点击分类后 selector 返回失败，但页面实际已经切到美食，
// 此时若仍把 __foodCategorySelected 置为 false，会把没有“美食”字样的
// 粤菜/茶点卡片（包括价值100元卡片）全部误判为“无法确认类目”。
function isFoodFilterSelectedOnList() {
    try {
        var infos = getVisibleTextInfos();
        for (var i = 0; i < infos.length; i++) {
            if (infos[i].text === "美食" && infos[i].cy < 420) {
                return true;
            }
        }
    } catch (e) {
    }
    return false;
}

function selectFoodCategory() {
    log("选择「全部分类」");

    if (!clickText("全部分类", 3000)) {
        if (existsText("美食")) {
            log("未找到「全部分类」，但页面已有「美食」，继续");
            return true;
        }

        log("找不到「全部分类」");
        return false;
    }

    sleepMs(800);

    var food = waitText("美食", 3000);

    if (!food) {
        log("分类中没有「美食」");
        goBack();
        return false;
    }

    if (!clickObj(food) && !clickNodeSmart(food)) {
        log("点击「美食」失败");
        goBack();
        return false;
    }

    sleepMs(1200);
    log("已选择「美食」");
    dumpVisibleTexts(15);
    return true;
}

// 地区固定使用「全部地区」：
// 页面默认显示「全部商区/全部地区」时不做任何点击；
// 只有检测到顶部筛选栏被设为具体行政区/商圈时，
// 才点开地区面板并切回「全部地区」，等待列表刷新后再扫描
function ensureAllRegions() {
    log("[地区] 检查地区筛选，目标：全部地区");

    try {
        if (existsText("全部地区") || existsText("全部商区")) {
            log("[地区] 当前已是全部地区，无需切换");
            return true;
        }
    } catch (e) {
    }

    // 在顶部筛选栏（y 较小）寻找当前选中的地区标签
    var tab = null;

    try {
        var infos = getVisibleTextInfos();

        for (var i = 0; i < infos.length; i++) {
            var t = infos[i].text;

            if (infos[i].cy > 350) {
                continue;
            }

            var isDistrict = false;

            for (var k = 0; k < CONFIG.KNOWN_AREAS.length; k++) {
                if (t === CONFIG.KNOWN_AREAS[k] ||
                    t === CONFIG.KNOWN_AREAS[k] + "区") {
                    isDistrict = true;
                    break;
                }
            }

            if (!isDistrict &&
                /^[一-龥]{2,4}(区|商圈)$/.test(t) &&
                t.indexOf("全部") < 0) {
                isDistrict = true;
            }

            if (isDistrict) {
                tab = t;
                break;
            }
        }
    } catch (e) {
    }

    if (!tab) {
        log("[地区] 未识别到地区筛选状态，按全部地区继续扫描");
        return true;
    }

    log("[地区] 当前地区筛选为「" + tab + "」，切换为全部地区");

    if (!clickText(tab, 3000)) {
        log("[地区] 点击地区筛选失败，按当前页面继续扫描");
        return false;
    }

    sleepMs(1000);

    var allLabels = ["全部地区", "全部商区", "全部", "不限"];
    var clicked = false;

    for (var j = 0; j < allLabels.length; j++) {
        var opt = findText(allLabels[j], 800);

        if (opt && clickObj(opt)) {
            log("[地区] 已点击「" + allLabels[j] + "」");
            clicked = true;
            break;
        }
    }

    if (!clicked) {
        log("[地区] 没找到「全部地区」选项，返回列表按当前页面继续");
        goBack();
        return false;
    }

    sleepMs(2000);
    log("[地区] 已切换为全部地区");
    return true;
}

// ============================================================
// 免费试列表扫描筛选（测试版）
// 扫描完成后：只对第1个符合条件活动点击其卡片内的「免费抽」并验证详情，不报名。
// 保留上方 v2.4 已验证的「免费试」入口代码。
// ============================================================

var __foodCategorySelected = false;

function formatRect(left, top, right, bottom) {
    return "[" + left + "," + top + "][" + right + "," + bottom + "]";
}

// 取一张活动卡片内、免费抽按钮上方的文本节点
function getCardRegionTexts(item, lowerY) {
    var infos = [];

    try {
        infos = getVisibleTextInfos();
    } catch (e) {
    }

    var by = (item.top + item.bottom) / 2;
    var bx = (item.left + item.right) / 2;
    var result = [];

    for (var i = 0; i < infos.length; i++) {
        if (infos[i].cy < lowerY) {
            continue;
        }

        var dy = by - infos[i].cy;

        if (dy > 0 &&
            dy < CONFIG.CARD_DY_MAX &&
            Math.abs(infos[i].cx - bx) < CONFIG.CARD_DX_TOLERANCE) {
            result.push(infos[i]);
        }
    }

    return result;
}

// 从一个卡片标记节点向上查找只属于本张卡片的容器：
// 依次取父节点，统计其内部同类标记数量，最后一个只包含 1 个标记的祖先
// 即为卡片边界。免费抽和已报名都走同一套边界规则，避免相邻卡片串位。
function getSingleCardRootByMarker(markerNode, markerText) {
    var root = null;
    var p = markerNode;

    for (var depth = 0; depth < 12; depth++) {
        var parent = null;

        try {
            parent = p.parent();
        } catch (e) {
        }

        if (!parent || parent === p) {
            break;
        }

        // 列表容器是所有活动卡片的公共祖先，不能把它当成单张卡片根节点。
        // 保留上一次已确认的卡片容器，避免单卡/单标记场景把相邻卡片合并。
        if (isListContainerNode(parent)) {
            break;
        }

        var count = -1;

        try {
            var bs = parent.find(text(markerText));

            if (bs) {
                if (typeof bs.size === "function") {
                    count = bs.size();
                } else if (typeof bs.length === "number") {
                    count = bs.length;
                }
            }
        } catch (e) {
        }

        // 父容器里出现 0 个或多个同类标记，说明已经越出本卡片
        if (count !== 1) {
            break;
        }

        root = parent;
        p = parent;
    }

    return root;
}

function getSingleCardRoot(btnNode) {
    return getSingleCardRootByMarker(btnNode, "免费抽");
}

// 收集卡片容器内部的全部文本节点（含位置信息），只用于本卡片解析
function getCardTextInfos(root) {
    var infos = [];

    var pushNode = function (obj) {
        try {
            var t = String(obj.text() || "").trim();

            if (!t) {
                return;
            }

            var b = obj.bounds();

            infos.push({
                text: t,
                left: b.left,
                right: b.right,
                top: b.top,
                bottom: b.bottom,
                cx: (b.left + b.right) / 2,
                cy: (b.top + b.bottom) / 2
            });
        } catch (e) {
        }
    };

    try {
        eachNode(root.find(className("android.widget.TextView")), pushNode);
    } catch (e) {
    }

    try {
        eachNode(root.find(className("android.view.View")), pushNode);
    } catch (e) {
    }

    // 去重（同一文本同一位置可能被两类选择器重复收集）
    var seen = [];
    var result = [];

    for (var i = 0; i < infos.length; i++) {
        var key = infos[i].text + "|" + infos[i].left + "|" + infos[i].top;

        if (seen.indexOf(key) >= 0) {
            continue;
        }

        seen.push(key);
        result.push(infos[i]);
    }

    result.sort(function (a, b) {
        if (a.top !== b.top) {
            return a.top - b.top;
        }

        return a.left - b.left;
    });

    return result;
}

// 取一张卡片的全部文本：优先用卡片容器边界；
// 容器识别失败时退回旧的按位置窗口收集方式
function collectCardTexts(item, lowerY) {
    var root = null;

    try {
        if (item && item.isRegisteredMarker) {
            root = getSingleCardRootByMarker(item.node, item.markerText || "已报名");
        } else {
            root = getSingleCardRoot(item.node);
        }
    } catch (e) {
    }

    if (root) {
        var infos = getCardTextInfos(root);

        // 某些版本的点评无障碍树会把卡片根节点错误收窄到
        // 「免费抽」按钮自身（或只剩按钮 + 一个空壳 View）。
        // 这种结果虽然 length > 0，但不含活动名/价值，直接返回会让
        // 整张卡片被解析成“未知活动”，并可能与其他未知卡片合并，
        // 从而漏掉真实的 100 元活动。只有至少 2 条非按钮文本时才
        // 信任容器结果，否则退回按按钮位置收集整张卡片。
        var usefulCount = 0;
        for (var ui = 0; ui < infos.length; ui++) {
            if (infos[ui].text !== "免费抽") {
                usefulCount++;
            }
        }

        if (usefulCount >= 2) {
            return infos;
        }
    }

    return getCardRegionTexts(item, lowerY);
}

function extractAreaFromText(str) {
    if (!str) {
        return null;
    }

    var knownAreas = [
        "荔湾", "越秀", "海珠", "天河",
        "白云", "番禺", "黄埔", "花都", "南沙", "增城", "从化"
    ];

    for (var i = 0; i < knownAreas.length; i++) {
        if (str.indexOf(knownAreas[i]) >= 0) {
            return knownAreas[i];
        }
    }

    var m = str.match(/^([\u4e00-\u9fa5]{2,3})区$/);

    if (m && m[1].indexOf("开发") < 0 &&
        m[1].indexOf("工业") < 0 &&
        m[1].indexOf("科技") < 0 &&
        m[1].indexOf("商") < 0 &&
        m[1].indexOf("全") < 0) {
        return m[1];
    }

    return null;
}

// 广州「商圈/地标 → 行政区」人工映射表（v1.5）。
// 只收无歧义项；命中才返回区名，未命中保持 null（区域显示为未知，绝不猜）。
// 修正项排最前：海珠广场属越秀、黄埔大道主线属天河、白云路属越秀。
var DISTRICT_LANDMARK_MAP = [
    ["海珠广场", "越秀"],
    ["黄埔大道", "天河"],
    ["白云路", "越秀"],
    ["北京路", "越秀"], ["东风东", "越秀"], ["杨箕", "越秀"],
    ["火车站", "越秀"], ["人民北", "越秀"], ["流花", "越秀"],
    ["淘金", "越秀"], ["环市东", "越秀"], ["东山口", "越秀"],
    ["农林下", "越秀"], ["中华广场", "越秀"], ["公园前", "越秀"],
    ["一德路", "越秀"], ["五羊新城", "越秀"], ["二沙岛", "越秀"],
    ["珠江新城", "天河"], ["体育西", "天河"], ["体育中心", "天河"],
    ["天河北", "天河"], ["岗顶", "天河"], ["龙口", "天河"],
    ["石牌", "天河"], ["太古汇", "天河"], ["正佳", "天河"],
    ["万菱汇", "天河"], ["时尚天河", "天河"], ["天河城", "天河"],
    ["车陂", "天河"], ["东圃", "天河"], ["棠下", "天河"],
    ["员村", "天河"], ["金融城", "天河"], ["龙洞", "天河"],
    ["岑村", "天河"], ["智慧城", "天河"], ["五山", "天河"],
    ["粤垦", "天河"], ["燕塘", "天河"], ["猎德", "天河"],
    ["科韵路", "天河"], ["华景新城", "天河"], ["冼村", "天河"],
    ["江南西", "海珠"], ["昌岗", "海珠"], ["客村", "海珠"],
    ["赤岗", "海珠"], ["琶洲", "海珠"], ["工业大道", "海珠"],
    ["东晓南", "海珠"], ["太古仓", "海珠"], ["滨江东", "海珠"],
    ["宝业路", "海珠"], ["南洲", "海珠"], ["沥滘", "海珠"],
    ["沙园", "海珠"], ["凤凰新村", "海珠"], ["新港东", "海珠"],
    ["新港西", "海珠"], ["磨碟沙", "海珠"], ["万胜围", "海珠"],
    ["广州塔", "海珠"],
    ["上下九", "荔湾"], ["中山七", "荔湾"], ["中山八", "荔湾"],
    ["芳村", "荔湾"], ["陈家祠", "荔湾"], ["西关", "荔湾"],
    ["黄沙", "荔湾"], ["长寿路", "荔湾"], ["康王路", "荔湾"],
    ["沙面", "荔湾"], ["滘口", "荔湾"], ["花地湾", "荔湾"],
    ["坑口", "荔湾"], ["西塱", "荔湾"], ["广钢新城", "荔湾"],
    ["嘉禾", "白云"], ["人和", "白云"], ["江高", "白云"],
    ["石井", "白云"], ["永泰", "白云"], ["夏良", "白云"],
    ["同和", "白云"], ["京溪", "白云"], ["梅花园", "白云"],
    ["白云新城", "白云"], ["三元里", "白云"], ["机场路", "白云"],
    ["黄石", "白云"], ["太和镇", "白云"], ["钟落潭", "白云"],
    ["金沙洲", "白云"], ["黄边", "白云"], ["龙归", "白云"],
    ["夏茅", "白云"], ["设计之都", "白云"], ["白云湖", "白云"],
    ["市桥", "番禺"], ["大石", "番禺"], ["洛溪", "番禺"],
    ["长隆", "番禺"], ["南村", "番禺"], ["万博", "番禺"],
    ["汉溪", "番禺"], ["钟村", "番禺"], ["石碁", "番禺"],
    ["沙湾", "番禺"], ["桥南", "番禺"], ["祈福", "番禺"],
    ["亚运城", "番禺"], ["石楼", "番禺"], ["南浦", "番禺"],
    ["厦滘", "番禺"], ["大学城", "番禺"], ["广州南站", "番禺"],
    ["萝岗", "黄埔"], ["科学城", "黄埔"], ["开发区", "黄埔"],
    ["大沙地", "黄埔"], ["文冲", "黄埔"], ["鱼珠", "黄埔"],
    ["南岗", "黄埔"], ["香雪", "黄埔"], ["永和", "黄埔"],
    ["知识城", "黄埔"], ["夏园", "黄埔"], ["庙头", "黄埔"],
    ["狮岭", "花都"], ["融创", "花都"], ["花山", "花都"],
    ["花东", "花都"], ["炭步", "花都"], ["赤坭", "花都"],
    ["雅瑶", "花都"], ["雅居乐锦城", "花都"], ["保利花城", "花都"],
    ["金洲", "南沙"], ["金州", "南沙"], ["蕉门", "南沙"],
    ["黄阁", "南沙"], ["榄核", "南沙"], ["大岗", "南沙"],
    ["东涌", "南沙"], ["万顷沙", "南沙"],
    ["新塘", "增城"], ["荔城", "增城"], ["挂绿", "增城"],
    ["东汇城", "增城"]
];

// 按人工映射表查行政区；未命中返回 null（保持未知，绝不猜）
function lookupDistrictByLandmark(str) {
    if (!str) {
        return null;
    }

    for (var i = 0; i < DISTRICT_LANDMARK_MAP.length; i++) {
        if (str.indexOf(DISTRICT_LANDMARK_MAP[i][0]) >= 0) {
            return DISTRICT_LANDMARK_MAP[i][1];
        }
    }

    return null;
}

// 按文本内容识别距离（如 19.7km、距离5.8km），只作展示，不参与筛选
function extractDistanceFromText(str) {
    if (!str) {
        return null;
    }

    var m = str.match(/(\d+(?:\.\d+)?)\s*km/i);

    return m ? m[1] + "km" : null;
}

// 判断文本是否就是行政区域标签本身（如「越秀」「天河区」），
// 用来区分区域字段和「名称里恰好包含区名」的情况（如「时尚天河西区店」）
function isAreaLabel(str) {
    if (!str) {
        return false;
    }

    var t = String(str).replace(/\s/g, "");

    var knownAreas = [
        "荔湾", "越秀", "海珠", "天河",
        "白云", "番禺", "黄埔", "花都", "南沙", "增城", "从化"
    ];

    for (var i = 0; i < knownAreas.length; i++) {
        if (t === knownAreas[i] || t === knownAreas[i] + "区") {
            return true;
        }
    }

    // 其他「XX区」形式（排除开发区/工业区等非行政区，与 extractAreaFromText 一致）
    return /^[一-龥]{2,3}区$/.test(t) && extractAreaFromText(t) !== null;
}

// 平台标签类文案（非活动名、非商户名）
function isTagText(t) {
    if (!t) {
        return false;
    }

    return t.indexOf("多门店") >= 0 ||
        t.indexOf("多商圈") >= 0 ||
        t.indexOf("中奖名额") >= 0 ||
        /人报名/.test(t) ||
        /^剩余/.test(t);
}

function cleanCardName(name) {
    if (!name) {
        return name;
    }

    var parts = name.split("|");
    var cleaned = [];

    for (var i = 0; i < parts.length; i++) {
        var p = String(parts[i] || "").replace(/[\uFFFC\u200B\u200C\u200D\uFEFF\s]+/g, " ").trim();

        if (!p) {
            continue;
        }

        var cleanPart = p.replace(/[\s\u00a0\u2000-\u200f\u202f\u2060]/g, "");
        var partArea = extractAreaFromText(cleanPart);

        if (partArea &&
            (CONFIG.KNOWN_AREAS.indexOf(cleanPart) >= 0 ||
                /^[\u4e00-\u9fa5]{2,4}区$/.test(cleanPart))) {
            continue;
        }

        if (/^(价值|¥|￥)/.test(cleanPart)) {
            continue;
        }

        cleaned.push(p);
    }

    return cleaned.join("|");
}

// 以「单张卡片」为单位解析全部字段。
// texts 必须只属于同一张卡片（来自 collectCardTexts），
// 所有字段都只在这个集合内部按文本内容判断：
//   含「元 / ¥ / 价值」→ 价值；含「km」→ 距离；
//   区名/区名+区 → 区域标签；含「美食」→ 类目；
// 商户只从信息行上的候选文本里取，且排除「xx店/xx路/xx中心」等
// 位置性结尾文本（它们多是分店/地址而非商户品牌），取不到就是 null，
// 绝不用距离、区域等其他字段顶替
// 合并被拆分的价值节点：如「价值」+「3 0 4」+「元」→ 304。
// 只处理 价值/¥/￥ 起始或「元」结束的连续数字片段，避免把距离、名额等数字混入。
function extractSplitValue(texts) {
    var i;
    var normalized = [];

    for (i = 0; i < texts.length; i++) {
        normalized.push(String(texts[i].text || "").replace(/[\s\u00a0\u2000-\u200f\u202f\u2060]/g, ""));
    }

    var start = -1;

    for (i = 0; i < normalized.length; i++) {
        if (normalized[i].indexOf("价值") === 0 ||
            normalized[i].indexOf("¥") === 0 ||
            normalized[i].indexOf("￥") === 0) {
            start = i;
            break;
        }
    }

    if (start >= 0) {
        var compact = normalized[start];
        var j = start + 1;

        while (j < normalized.length) {
            var n = normalized[j];

            if (/^\d+$/.test(n) || n === "元" ||
                n.indexOf("¥") >= 0 || n.indexOf("￥") >= 0) {
                compact += n;

                if (n === "元") {
                    break;
                }

                j++;
            } else {
                break;
            }
        }

        if (compact.indexOf("元") >= 0 ||
            compact.indexOf("¥") >= 0 ||
            compact.indexOf("￥") >= 0) {
            var v = extractValueFromText(compact);

            if (v !== null) {
                return v;
            }

            var m = compact.match(/[¥￥]\s*(\d+(?:\.\d+)?)/);

            if (!m) {
                m = compact.match(/(\d+(?:\.\d+)?)\s*元/);
            }

            if (m) {
                return parseFloat(m[1]);
            }
        }
    }

    // 没有「价值/¥」前缀时，找单独的「元」节点并向前合并数字
    var yuanIdx = -1;

    for (i = 0; i < normalized.length; i++) {
        if (normalized[i] === "元") {
            yuanIdx = i;
            break;
        }
    }

    if (yuanIdx >= 0) {
        var digits = "";
        var k = yuanIdx - 1;

        while (k >= 0 && /^\d+$/.test(normalized[k])) {
            digits = normalized[k] + digits;
            k--;
        }

        if (digits) {
            return parseFloat(digits);
        }
    }

    // v1.45.1：部分机型的无障碍树会把“价值100元”拆成
    // 「价值」+「100」+「60个中奖名额」，甚至不暴露独立的“元”节点。
    // 原实现要求后续必须出现“元”，因此这类卡片会被判定为价值未知。
    // “价值”后的第一个纯数字节点就是活动价值；只在价值前缀上下文中
    // 使用该兜底，避免把中奖名额/距离数字误当价值。
    for (i = 0; i < normalized.length; i++) {
        var prefix = normalized[i];
        if (prefix === "价值" || prefix === "价值¥" || prefix === "价值￥") {
            for (var vi = i + 1; vi < normalized.length && vi <= i + 3; vi++) {
                var valueToken = normalized[vi];
                var valueMatch = valueToken.match(/^(?:¥|￥)?(\d+(?:\.\d+)?)(?:元)?$/);
                if (valueMatch) {
                    return parseFloat(valueMatch[1]);
                }
                // 遇到标题、商户、距离等非价格文本就停止，避免跨卡片串值。
                if (valueToken && !/^元$/.test(valueToken)) {
                    break;
                }
            }
        }
    }

    // 最后处理“价值”与数字在同一个合并文本节点中的变体。
    var allCompact = normalized.join("");
    var allValueMatch = allCompact.match(/价值(?:¥|￥)?(\d+(?:\.\d+)?)/);
    if (allValueMatch) {
        return parseFloat(allValueMatch[1]);
    }

    return null;
}

// 只有卡片内部出现完整、独立的状态文案才算已报名。
// 归一化空白后仍必须等于整个文本，避免把「3991 人已报名」、
// 「报名人数」或「报名截止」等统计/提示文案误判为本人已报名。
function isRegisteredCardText(str) {
    var compact = String(str || "")
        .replace(/[\uFFFC\u200B\u200C\u200D\uFEFF\s\u00a0\u2000-\u200f\u202f\u2060]/g, "");

    return compact === "已报名" || compact === "报名成功";
}

function hasRegisteredCardStatus(texts) {
    for (var i = 0; i < (texts || []).length; i++) {
        if (isRegisteredCardText(texts[i].text)) {
            return true;
        }
    }

    return false;
}

function parseCardFields(texts) {
    var card = {
        name: "",
        merchant: null,
        value: null,
        area: null,
        distance: null,
        category: null,
        registered: false,
        raw: ""
    };

    var i;
    var t;
    var rawParts = [];

    for (i = 0; i < texts.length; i++) {
        rawParts.push(texts[i].text);
    }

    card.raw = rawParts.join(" | ");
    card.registered = hasRegisteredCardStatus(texts);

    // 价值：扫遍卡片内所有文本，优先「价值X元」，其次 ¥X，最后 X元。
    // 只要卡片里任何节点带价格就能解析出来，
    // 不会因为某个节点没有「元」就判断整个活动价值未知
    for (i = 0; i < texts.length && card.value === null; i++) {
        card.value = extractValueFromText(texts[i].text);
    }

    if (card.value === null) {
        for (i = 0; i < texts.length; i++) {
            var compactText = String(texts[i].text || "").replace(/[\s\u00a0\u2000-\u200f\u202f\u2060]/g, "");
            var m = compactText.match(/[¥￥]\s*(\d+(?:\.\d+)?)/);

            if (!m) {
                m = compactText.match(/(\d+(?:\.\d+)?)\s*元/);
            }

            if (m) {
                card.value = parseFloat(m[1]);
                break;
            }
        }
    }

    // 价值可能被拆成多个节点：「价值」「3 0 4」「元」，按顺序合并后重新解析
    if (card.value === null) {
        card.value = extractSplitValue(texts);
    }

    // 区域：仅解析展示，不参与筛选。
    // 优先取「本身就是区域标签」的文本（如「越秀区」「天河」），
    // 其次才用包含区名的文本（如「时尚天河」「天河路」），
    // 避免商户名里包含区名（如「天河城百货」）造成字段错位
    for (i = 0; i < texts.length && card.area === null; i++) {
        if (isAreaLabel(texts[i].text)) {
            card.area = extractAreaFromText(texts[i].text);
        }
    }

    // 商圈/地标映射（v1.5）：优先于宽松子串，只在「距离所在行」查表
    // （分店/商圈都在这一行），避免商户名/活动名里的通用词误伤；
    // 没有距离文本的卡片才放开到全部文本。查不到保持未知。
    if (card.area === null) {
        var mapRowYs = [];

        for (i = 0; i < texts.length; i++) {
            if (extractDistanceFromText(texts[i].text)) {
                mapRowYs.push(texts[i].cy);
            }
        }

        for (i = 0; i < texts.length && card.area === null; i++) {
            var onMapRow = mapRowYs.length === 0;

            if (!onMapRow) {
                for (var ry = 0; ry < mapRowYs.length; ry++) {
                    if (Math.abs(texts[i].cy - mapRowYs[ry]) < 20) {
                        onMapRow = true;
                        break;
                    }
                }
            }

            if (onMapRow) {
                card.area = lookupDistrictByLandmark(texts[i].text);
            }
        }
    }

    if (card.area === null) {
        for (i = 0; i < texts.length; i++) {
            var a = extractAreaFromText(texts[i].text);

            if (a) {
                card.area = a;
                break;
            }
        }
    }

    // 距离：只认 xxkm，仅展示
    for (i = 0; i < texts.length; i++) {
        var d = extractDistanceFromText(texts[i].text);

        if (d) {
            card.distance = d;
            break;
        }
    }

    // 类目：已选「美食」分类时直接记为美食，否则在卡片内找「美食」
    if (__foodCategorySelected) {
        card.category = "美食";
    } else {
        for (i = 0; i < texts.length; i++) {
            if (texts[i].text.indexOf("美食") >= 0) {
                card.category = "美食";
                break;
            }
        }
    }

    // 名称与商户：按「信息行」区分。
    // 信息行 = 价值/距离/区域标签/平台标签/功能文案所在的行；
    // 活动名只取非信息行的文本，避免混入「多门店多商圈 12.8km」；
    // 商户只从信息行候选里取，且排除位置性结尾文本。
    // 注意：点评的实际节点可能把“分店 | 商圈/商户 | 距离”拆成
    // 三个同一行节点；不能因为候选与距离同一行就全部排除，否则
    // “来又来/大润发”会被误丢掉。
    var LOCATION_SUFFIX = /(店|路|街|中心|城|广场|大厦|站|号|区|商圈)$/;
    var infoRowYs = [];

    var isInfoText = function (str) {
        return isFunctionalText(str) ||
            isTagText(str) ||
            extractValueFromText(str) !== null ||
            /[¥￥]\s*\d/.test(str) ||
            /\d+(?:\.\d+)?\s*元/.test(str) ||
            !!extractDistanceFromText(str) ||
            isAreaLabel(str);
    };

    for (i = 0; i < texts.length; i++) {
        if (isInfoText(texts[i].text)) {
            infoRowYs.push(texts[i].cy);
        }
    }

    var isOnInfoRow = function (info) {
        for (var r = 0; r < infoRowYs.length; r++) {
            if (Math.abs(info.cy - infoRowYs[r]) < 20) {
                return true;
            }
        }

        return false;
    };

    var nameParts = [];

    for (i = 0; i < texts.length; i++) {
        t = texts[i].text;

        if (isInfoText(t) || isOnInfoRow(texts[i])) {
            continue;
        }

        nameParts.push(t);
    }

    card.name = cleanCardName(nameParts.slice(0, 3).join("|"));

    // 距离所在行通常是「分店 + 商圈 + km」，这些不是商户品牌
    var distanceRowYs = [];

    for (i = 0; i < texts.length; i++) {
        if (extractDistanceFromText(texts[i].text)) {
            distanceRowYs.push(texts[i].cy);
        }
    }

    var isOnDistanceRow = function (info) {
        for (var r = 0; r < distanceRowYs.length; r++) {
            if (Math.abs(info.cy - distanceRowYs[r]) < 20) {
                return true;
            }
        }

        return false;
    };

    var isPlausibleMerchant = function (str) {
        if (!str || str.length < 2 || str.length > 30) {
            return false;
        }

        if (/\d/.test(str)) {
            return false;
        }

        // 商户名可能包含“品牌/商圈”或“品牌/商场”形式，
        // 例如“来又来/大润发”，不能再按斜杠一律排除。

        if (LOCATION_SUFFIX.test(str)) {
            return false;
        }

        return true;
    };

    for (i = 0; i < texts.length; i++) {
        t = String(texts[i].text || "").replace(/[\uFFFC\u200B\u200C\u200D\uFEFF\s]+/g, " ").trim();

        if (isInfoText(t) || !isOnInfoRow(texts[i])) {
            continue;
        }

        if (card.name && card.name.indexOf(t) >= 0) {
            continue;
        }

        if (isPlausibleMerchant(t)) {
            card.merchant = t;
            break;
        }
    }

    // 某些机型把信息行的 y 坐标拆得略开，导致上面的“同一行”判断
    // 没命中。若卡片里存在带斜杠的明确商户候选（如“来又来/大润发”），
    // 再做一次内容兜底；活动名本身已在 card.name 中，排除后不会串名。
    if (card.merchant === null) {
        for (i = 0; i < texts.length; i++) {
            var slashMerchant = String(texts[i].text || "")
                .replace(/[\uFFFC\u200B\u200C\u200D\uFEFF\s]+/g, " ").trim();
            if (slashMerchant.indexOf("/") >= 0 &&
                (!card.name || card.name.indexOf(slashMerchant) < 0) &&
                isPlausibleMerchant(slashMerchant)) {
                card.merchant = slashMerchant;
                break;
            }
        }
    }

    // 信息行取不到商户时，活动名「商户 | 套餐」里的第一段通常就是商户
    if (card.merchant === null && card.name) {
        var firstSeg = String(card.name).split("|")[0].replace(/[\uFFFC\u200B\u200C\u200D\uFEFF\s]+/g, " ").trim();

        if (firstSeg && firstSeg.length >= 2 && firstSeg.length <= 30 &&
            firstSeg.indexOf("/") < 0 &&
            !/\d/.test(firstSeg) &&
            !LOCATION_SUFFIX.test(firstSeg) &&
            !/套餐$/.test(firstSeg)) {
            card.merchant = firstSeg;
        }
    }

    return card;
}

function classifyActivity(activity) {
    var reasons = [];

    if (!activity.name) {
        reasons.push("名称未知");
    }

    // 已报名是卡片的终态标记，不再要求卡片仍保留「免费抽」按钮；
    // 它会进入结果队列，但处理阶段只记录状态，绝不点击。
    if (!activity.hasFreeDraw && !activity.registered) {
        reasons.push("没有免费抽");
    }

    if (activity.value === null || typeof activity.value === "undefined") {
        reasons.push("无法解析价值");
    } else if (activity.value <= 0) {
        reasons.push("价值为0");
    } else if (activity.value < CONFIG.MIN_VALUE) {
        reasons.push("价值<" + CONFIG.MIN_VALUE);
    }

    if (!activity.category) {
        reasons.push("无法确认类目");
    }

    if (activity.registered) {
        activity.qualified = reasons.length === 0;
        activity.reason = activity.qualified ? "已报名" : reasons.join("，");
        return activity;
    }

    // 地区固定为「全部地区」，区域字段只展示，不参与筛选

    activity.qualified = reasons.length === 0;
    activity.reason = reasons.join("，");
    return activity;
}

function scanCurrentScreen(seenKeys) {
    var snapshot = [];

    try {
        snapshot = getFreeDrawSnapshot();
    } catch (e) {
        logError("获取「免费抽」按钮失败", e);
    }

    // 「已报名」卡片可能已经没有「免费抽」按钮，必须单独收集状态节点；
    // 合并后按屏幕位置排序，保证先处理上方卡片。明确的卡片状态会由
    // scanFreeTrialList() 作为当前批次尾部标志处理。
    try {
        var registeredSnapshot = getRegisteredSnapshot();

        for (var rs = 0; rs < registeredSnapshot.length; rs++) {
            var registeredItem = registeredSnapshot[rs];
            var duplicate = false;

            for (var ds = 0; ds < snapshot.length; ds++) {
                if (Math.abs(snapshot[ds].top - registeredItem.top) <= 40 &&
                    Math.abs(snapshot[ds].left - registeredItem.left) <= 120) {
                    duplicate = true;
                    break;
                }
            }

            if (!duplicate) {
                snapshot.push(registeredItem);
            }
        }
    } catch (e2) {
        logError("获取卡片已报名状态失败", e2);
    }

    snapshot.sort(function (a, b) {
        return a.top - b.top;
    });

    log("[列表] 当前屏可见文本数：" + getVisibleTextInfos().length);
    log("[列表] 本屏发现「免费抽」按钮：" + snapshot.length);

    var newItems = [];
    var visibleItems = [];
    var registeredActivities = [];
    var screenRecords = [];
    var screenKeys = [];

    // 同一活动可能同时匹配到「免费抽」和「已报名」两个节点。
    // 先在当前屏按活动唯一键合并，再统计状态，避免一个卡片被算成两张，
    // 也避免把相邻卡片的状态混在一起。
    for (var si = 0; si < snapshot.length; si++) {
        var screenItem = snapshot[si];
        var screenLowerY = si === 0 ? 0 : snapshot[si - 1].bottom;
        var screenParsed = parseCardFields(collectCardTexts(screenItem, screenLowerY));
        var screenName = screenParsed.name;
        var screenValue = screenParsed.value;
        var screenArea = screenParsed.area;
        var screenCategory = screenParsed.category;
        var screenDistance = screenParsed.distance;
        var screenMerchant = screenParsed.merchant;
        var screenKey = buildActivityKey(screenName, screenValue, screenMerchant, screenArea, screenItem.key);
        // 免费抽节点的卡片容器偶尔会串入相邻卡片的「已报名」水印。
        // 已报名状态只接受独立收集到的当前标记节点，避免把免费活动误跳过。
        var screenRegistered = !!screenItem.isRegisteredMarker;
        var screenIndex = screenKeys.indexOf(screenKey);

        if (screenIndex >= 0) {
            if (screenRegistered) {
                screenRecords[screenIndex].registered = true;
            }
            continue;
        }

        screenKeys.push(screenKey);
        screenRecords.push({
            item: screenItem,
            parsed: screenParsed,
            name: screenName,
            value: screenValue,
            area: screenArea,
            category: screenCategory,
            distance: screenDistance,
            merchant: screenMerchant,
            key: screenKey,
            registered: screenRegistered
        });
    }

    var registeredCount = 0;
    var nonRegisteredCount = 0;

    for (var i = 0; i < screenRecords.length; i++) {
        var record = screenRecords[i];
        var item = record.item;
        var parsed = record.parsed;
        var name = record.name;
        var value = record.value;
        var area = record.area;
        var category = record.category;
        var distance = record.distance;
        var merchant = record.merchant;
        var key = record.key;
        var registered = record.registered;

        if (registered) {
            registeredCount++;
        } else {
            nonRegisteredCount++;
        }

        if (seenKeys.indexOf(key) >= 0) {
            log("[列表] 已扫描过，跳过：" + (name || "未知活动"));

            var visibleActivity = classifyActivity({
                name: name,
                value: value,
                area: area,
                category: category,
                merchant: merchant,
                distance: distance,
                registered: registered,
                hasFreeDraw: !registered,
                key: key,
                node: item.node,
                bounds: formatRect(item.left, item.top, item.right, item.bottom)
            });
            visibleItems.push(visibleActivity);

            if (registered) {
                registeredActivities.push({
                    name: name,
                    merchant: merchant,
                    value: value,
                    area: area,
                    distance: distance,
                    category: category,
                    registered: true,
                    key: key
                });
            }

            continue;
        }

        seenKeys.push(key);

        var activity = classifyActivity({
            name: name,
            value: value,
            area: area,
            category: category,
            merchant: merchant,
            distance: distance,
            registered: registered,
            hasFreeDraw: !registered,
            key: key,
            node: item.node,
            bounds: formatRect(item.left, item.top, item.right, item.bottom)
        });

        newItems.push(activity);
        visibleItems.push(activity);

        log("[解析] 活动：" + (name || "未知"));
        log("[解析] 商户：" + (merchant || "未知"));
        log("[解析] 价值：" + (value === null ? "未知" : value + "元"));
        log("[解析] 区域：" + (area || "未知"));
        log("[解析] 距离：" + (distance || "未知"));
        log("[解析] 类目：" + (category || "未知"));

        if (registered) {
            log("[列表] 当前活动卡片状态：已报名");
            registeredActivities.push({
                name: activity.name,
                merchant: activity.merchant,
                value: activity.value,
                area: activity.area,
                distance: activity.distance,
                category: activity.category,
                registered: true,
                key: activity.key
            });
        }

        // 价值是筛选必需字段；区域只展示、不参与筛选，未知区域不应
        // 被标成“解析失败”，否则会掩盖“价值100元且符合”的真实结果。
        if (value === null) {
            log("[解析失败] 当前活动卡片原始文本：");
            log(parsed.raw || "（卡片内无文本）");
            log("[解析失败] 价值：未知");
        } else if (area === null) {
            log("[解析提示] 区域未知（不参与筛选），价值：" + value + "元");
        }

        if (activity.qualified && !registered) {
            log("[筛选] 符合");
        } else if (activity.qualified && registered) {
            log("[筛选] 已报名，作为扫描终止标志，不进入自动报名队列");
        } else {
            log("[筛选] 跳过");
            log("[筛选] 原因：" + activity.reason);
        }
    }

    var qualifiedCount = 0;

    for (var j = 0; j < newItems.length; j++) {
        if (newItems[j].qualified) {
            qualifiedCount++;
        }
    }

    return {
        newCount: newItems.length,
        qualifiedCount: qualifiedCount,
        items: visibleItems,
        freeDrawCount: snapshot.length - registeredCount,
        registeredFound: registeredCount > 0,
        registeredCount: registeredCount,
        nonRegisteredCount: nonRegisteredCount,
        registeredActivities: registeredActivities,
        registeredActivity: registeredActivities.length > 0 ? registeredActivities[0] : null
    };
}

function scrollListOnce() {
    // v1.34.0：页面守卫——如果当前在「我的」页面，绝对禁止继续滚动
    if (isMyPage()) {
        log("[页面守卫] scrollListOnce 检测到「我的」页面，禁止向下滚动");
        return;
    }
    try {
        swipe(
            device.width * 0.5,
            device.height * 0.8,
            device.width * 0.5,
            device.height * 0.3,
            600
        );
    } catch (e) {
        logError("向下滚动列表失败", e);
    }

    sleepMs(CONFIG.SCROLL_WAIT_MS);
}

// v1.9.0：当前屏可见活动卡片签名（活动名+价值），用于判断滚动是否把
// 页面推进；头部筛选栏文本固定不动，不能用它判断页面是否到底。
function currentScreenCardKeys() {
    var keys = [];
    var snapshot = [];

    try {
        snapshot = getFreeDrawSnapshot();
    } catch (e) {
    }

    for (var i = 0; i < snapshot.length; i++) {
        var item = snapshot[i];
        var lowerY = i === 0 ? 0 : snapshot[i - 1].bottom;

        try {
            var parsed = parseCardFields(collectCardTexts(item, lowerY));

            if (parsed.name) {
                keys.push(String(parsed.name) + "|" +
                    (parsed.value === null ? "?" : parsed.value));
            }
        } catch (e2) {
        }
    }

    return keys;
}

// 扫描到底综合判定：
// 1. 页面出现明确的底部提示；2. 当前屏卡片签名连续不变；
// 3. 连续多轮没有新活动。返回空字符串表示继续扫描。
function detectListEnd(newCount, page) {
    for (var i = 0; i < CONFIG.END_TEXT_KEYWORDS.length; i++) {
        try {
            if (anyTextContains(CONFIG.END_TEXT_KEYWORDS[i])) {
                return "出现底部提示：" + CONFIG.END_TEXT_KEYWORDS[i];
            }
        } catch (e) {
        }
    }

    if (page === 0) {
        gSameScreenRounds = 0;
        gNoNewRounds = 0;
        return "";
    }

    var keys = currentScreenCardKeys();
    var sig = keys.join("|");

    if (sig && sig === gLastScreenSignature) {
        gSameScreenRounds++;

        if (gSameScreenRounds >= CONFIG.MAX_SAME_SCREEN_ROUNDS) {
            return "当前屏卡片签名连续 " + gSameScreenRounds + " 轮未变化，判定已经到底";
        }
    } else {
        gSameScreenRounds = 0;
    }

    gLastScreenSignature = sig;

    if (newCount === 0) {
        gNoNewRounds++;

        if (gNoNewRounds >= CONFIG.MAX_NO_NEW_ROUNDS) {
            return "连续 " + gNoNewRounds + " 轮没有发现新活动，判定已经到底";
        }
    } else {
        gNoNewRounds = 0;
    }

    return "";
}

// v1.9.6：列表页 vs 详情页识别
// 返回 true 表示当前是「免费试列表页」，false 表示可能是详情页
function isListPage() {
    var listIndicators = ["全部商区", "全部分类", "美食", "智能排序", "更多筛选"];
    var detailIndicators = ["免费试活动详情", "活动流程", "活动内容", "活动规则", "我要报名", "橙V专享", "会员专享价", "购买", "立即购买"]; // v1.45.0: 删除"橙V专享价"——底部导航栏常驻，不能用来判断详情页
    var listScore = 0;
    var detailScore = 0;

    for (var i = 0; i < listIndicators.length; i++) {
        try {
            if (anyTextContains(listIndicators[i])) {
                listScore++;
            }
        } catch (e) {
        }
    }

    for (var j = 0; j < detailIndicators.length; j++) {
        try {
            if (anyTextContains(detailIndicators[j])) {
                detailScore++;
            }
        } catch (e) {
        }
    }

    // 详情页特征 >= 1 且没有列表页特征时，判定为详情页
    // 修复：原来只在 detailScore >= 2 时才返回 false，
    // 导致只有一个详情页特征（如「我要报名」）但无列表页特征时
    // 误判为列表页，进而把详情页底部当扫描完成。
    if (detailScore >= 1 && listScore === 0) {
        return false;
    }

    // 如果列表页特征出现 1 个以上，判定为列表页
    if (listScore >= 1) {
        return true;
    }

    // 模糊情况：尝试检查是否有活动卡片（免费抽按钮）
    try {
        var snapshot = getFreeDrawSnapshot();
        if (snapshot.length > 0) {
            return true;
        }
    } catch (e) {
    }

    // 默认认为是列表页（宁可误判为列表页，后续会再次检测）
    return true;
}

// v1.9.6：检测当前是否在活动详情页
function detectDetailPage() {
    return !isListPage();
}

// v1.33.0：检测当前是否在大众点评「我的」页面
// 如果在「我的」页面，绝不能继续执行免费试列表逻辑（滚动、定位、点击活动）
function isMyPage() {
    var myPageIndicators = [
        "我的订单", "我的收藏", "我的评价", "个人信息",
        "我的优惠", "我的积分", "会员中心", "我的关注",
        "我的评论", "我的足迹", "我的卡包"
    ];
    var myPageScore = 0;
    for (var i = 0; i < myPageIndicators.length; i++) {
        try {
            if (anyTextContains(myPageIndicators[i])) {
                myPageScore++;
            }
        } catch (e) {}
    }
    if (myPageScore >= 2) {
        return true;
    }
    try {
        if (anyTextContains("我的") && !anyTextContains("免费试") && !anyTextContains("全部商区")) {
            var listScore = 0;
            var detailScore = 0;
            var checkIndicators = ["全部商区", "全部分类", "美食", "智能排序", "更多筛选"];
            for (var j = 0; j < checkIndicators.length; j++) {
                try { if (anyTextContains(checkIndicators[j])) listScore++; } catch (e) {}
            }
            var detailCheckIndicators = ["免费试活动详情", "活动流程", "活动内容", "活动规则", "我要报名"];
            for (var k = 0; k < detailCheckIndicators.length; k++) {
                try { if (anyTextContains(detailCheckIndicators[k])) detailScore++; } catch (e) {}
            }
            if (listScore === 0 && detailScore === 0) {
                return true;
            }
        }
    } catch (e) {}
    return false;
}

// v1.33.0：综合判断当前是否仍在免费试列表页
function isFreeTrialListPage() {
    if (isMyPage()) return false;
    return isListPage();
}

// v1.33.0：返回列表后验证页面状态，如果发现不是免费试列表则尝试恢复（最多1次）
function verifyAndRecoverListPage() {
    if (isFreeTrialListPage()) {
        return true;
    }
    log("[页面状态] 当前页面不是免费试列表");
    if (isMyPage()) {
        log("[页面异常] 检测到「我的」页面，禁止继续列表操作");
    } else {
        log("[页面异常] 当前页面类型不确定");
    }
    log("[页面恢复] 尝试按返回键恢复到免费试列表");
    goBack();
    sleepMs(1000);
    if (isFreeTrialListPage()) {
        log("[页面恢复] 返回后已恢复到免费试列表");
        return true;
    }
    log("[页面恢复] 返回键未恢复，尝试寻找免费试入口");
    try {
        var candidates = findFreeTrialCandidates();
        if (candidates.length > 0) {
            log("[页面恢复] 找到免费试入口节点，尝试点击");
            for (var i = 0; i < candidates.length; i++) {
                try {
                    clickNodeCenter(candidates[i]);
                    sleepMs(2000);
                    var marker = waitForListMarkers(3000);
                    if (marker) {
                        log("[页面恢复] 已成功重新进入免费试列表");
                        return true;
                    }
                } catch (e) {}
            }
        }
    } catch (e) {}
    log("[安全停止] 无法恢复到免费试列表，停止列表操作");
    return false;
}
function scanFreeTrialList() {
    if (!enterScanningState()) {
        return {
            allScanned: [],
            qualifiedList: [],
            endReason: "禁止重新扫描",
            totalScanned: 0,
            blocked: true
        };
    }

    log("[列表] 开始扫描活动");
    log("[筛选] 地区：全部地区");
    log("[筛选] 类目：美食");
    log("[筛选] 最低价值：" + CONFIG.MIN_VALUE + "元");
    log("[处理] 模式：边扫描边报名，每个活动只进入一次");
    toastMsg("正在扫描免费试列表");

    // v1.7.2：清空上一轮扫描记录，处理阶段用它们检测列表是否被刷新
    gScanNames = [];
    gScanTopNames = [];
    gScanScreenCount = 0;
    gLastLocateOverlap = -1;
    gLastLocateSeen = 0;
    gStopAfterLevelRequirement = false;
    gStopAfterLevelRequirementReason = "";

    // v1.13.0：选完分类后已在列表顶部，「↑ 回到顶部」按钮此时尚未出现，
    // 调用 scrollListToTop 会触发坐标兜底误点右下角商户卡片，直接跳过。
    log("[列表] 选完分类后已在顶部，跳过回顶部，直接开始扫描");

    var seenKeys = [];
    var allScannedList = [];
    var qualifiedList = [];
    var totalNew = 0;
    var consecutiveEmpty = 0;
    var consecutiveNoFreeDraw = 0;
    var endReason = "";
    // v1.42.0：边扫边报——立即处理，不再等全部扫描完
    var processedKeys = {};
    var queuedKeys = {};
    // 卡片点击偶发失败时不能永久标记为已处理，否则活动会被漏掉。
    // 允许同一活动最多重试 2 次；成功进入详情后即永久标记，
    // 连续两次点击失败才安全放弃，避免无限重试。
    var failedProcessAttempts = {};
    var MAX_FAILED_PROCESS_ATTEMPTS = 2;
    var results = [];
    var processedCount = 0;
    // v1.42.2：处理完一个活动后重新扫描当前屏，而不是用过期 node 继续
    var rescanCurrentScreen = false;

    for (var page = 0; page < CONFIG.MAX_SCAN_SCROLLS; page++) {
        // v1.42.2：如果刚处理完一个活动，重新扫描当前屏而不是滚动
        if (rescanCurrentScreen) {
            log("[边扫边报] 重新扫描当前屏，寻找下一个合格活动");
            rescanCurrentScreen = false;
            // v1.43.0：重建 seenKeys 仅保留已处理的活动，
            // 避免同一屏内已扫描但未处理的合格活动被误跳过
            var rebuiltSeen = [];
            for (var pk in processedKeys) {
                if (Object.prototype.hasOwnProperty.call(processedKeys, pk) && processedKeys[pk]) {
                    rebuiltSeen.push(pk);
                }
            }
            seenKeys.length = 0;
            for (var rs = 0; rs < rebuiltSeen.length; rs++) {
                seenKeys.push(rebuiltSeen[rs]);
            }
            log("[边扫边报] seenKeys 已重建，保留 " + seenKeys.length + " 条已处理记录");
        }

        // v1.9.6：每屏扫描前先检查是否误入详情页
        if (detectDetailPage()) {
            log("[异常] 检测到活动详情页，当前不是免费试列表页");
            log("[异常] 停止列表扫描，准备恢复");
            gDetailDuringScan = true;

            if (gDetailPageRecoveryCount >= 2) {
                log("[异常] 详情页恢复已达上限（2次），停止扫描");
                endReason = "详情页恢复失败";
                break;
            }

            gDetailPageRecoveryCount++;
            setScriptState("DETAIL_PAGE_RECOVERY");
            log("[状态] DETAIL_PAGE_RECOVERY（第 " + gDetailPageRecoveryCount + " 次）");

            try {
                back();
                sleepMs(2000);
            } catch (e) {
                logError("返回列表页失败", e);
            }

            // 验证是否回到列表页
            if (isListPage()) {
                log("[异常] 已返回免费试列表页");
            } else {
                log("[异常] 返回后仍未检测到列表页特征，再试一次");
                try {
                    back();
                    sleepMs(2000);
                } catch (e2) {}
            }

            // 如果之前已发现已报名，直接进入回顶部流程
            if (gFoundRegistered) {
                log("[状态] 此前已发现已报名，跳过继续扫描，直接回顶部");
                break;
            }

            // 否则继续扫描
            continue;
        }

        log("[列表] 扫描第" + (page + 1) + "屏");
        var result = scanCurrentScreen(seenKeys);

        totalNew += result.newCount;
        gScanScreenCount = page + 1;

        // v1.11.0：「已报名」是图片水印，无障碍文字无法检测。
        // 启发式：如果当前屏没有任何「免费抽」按钮且已找到活动，
        // 连续2屏即判定已进入「已报名」区域，提前停止扫描。
                // v1.45.6: 修复过早判定已报名区域——加载中/返回列表瞬间可能出现 0 按钮，需同时满足可见文本充足且已扫一定数量才计数
        var visibleCountForGate = 0;
        try { visibleCountForGate = getVisibleTextInfos().length; } catch(eVG) {}
        if (result.freeDrawCount <= 0 && totalNew > 0 && totalNew >= 6 && visibleCountForGate >= 80) {
            consecutiveNoFreeDraw++;
            log("[列表] 当前屏「免费抽」按钮数：0（连续第 " + consecutiveNoFreeDraw + " 屏，visible=" + visibleCountForGate + " totalNew=" + totalNew + "）");
            if (consecutiveNoFreeDraw >= 2) {
                endReason = "连续2屏无免费抽按钮，判定已进入已报名区域";
                log("[扫描] " + endReason + "，提前停止扫描");
                break;
            }
        } else if (result.freeDrawCount <= 0 && totalNew > 0) {
            log("[列表] 当前屏「免费抽」按钮数：0（visible=" + visibleCountForGate + " totalNew=" + totalNew + " 未达阈值，暂不计入连续计数）");
        } else {
            consecutiveNoFreeDraw = 0;
        }
        if (page % 10 === 9) {
            postTelemetry({ event: "scan_page", version: __SCRIPT_VERSION, page: page + 1, found: totalNew });
        }

        // 记录扫描阶段见过的全部活动名（归一化），首屏单独留样，
        // 供处理阶段确认到顶 / 判断列表是否被整体刷新
        for (var sn = 0; sn < result.items.length; sn++) {
            var scanName = normalizeNameForMatch(result.items[sn].name);

            if (scanName && gScanNames.indexOf(scanName) < 0) {
                gScanNames.push(scanName);
            }

            if (page === 0 && scanName && gScanTopNames.indexOf(scanName) < 0) {
                gScanTopNames.push(scanName);
            }
        }

        // 先完整扫描：本屏只收集符合条件且未报名的活动，不点击；
        // v1.42.0：边扫边报——遇到第一个符合条件且未报名的活动立即处理
        var inlineProcessedThisScreen = false;
        for (var i = 0; i < result.items.length; i++) {
            var it = result.items[i];

            var scannedAlready = false;
            for (var asi = 0; asi < allScannedList.length; asi++) {
                if (allScannedList[asi].key === it.key) {
                    scannedAlready = true;
                    break;
                }
            }
            if (!scannedAlready) {
                allScannedList.push({
                    name: it.name,
                    merchant: it.merchant,
                    value: it.value,
                    area: it.area,
                    distance: it.distance,
                    category: it.category,
                    registered: !!it.registered,
                    key: it.key
                });
            }

            // v1.42.7：重新扫描时价值/区域可能暂时解析不同，使用活动名+商户稳定去重，
            // 避免同一活动再次进入详情页。
            var processKey = buildActivityProcessKey(it);
            var failedAttempts = failedProcessAttempts[processKey] || 0;
            if (it.qualified && !it.registered &&
                !processedKeys[it.key] && !processedKeys[processKey] &&
                failedAttempts < MAX_FAILED_PROCESS_ATTEMPTS) {
                if (!queuedKeys[processKey]) {
                    qualifiedList.push({
                        name: it.name, merchant: it.merchant, value: it.value,
                        area: it.area, distance: it.distance, category: it.category,
                        registered: false, key: it.key
                    });
                    queuedKeys[processKey] = true;
                }
                processedCount++;
                log("[边扫边报] ===== 第 " + processedCount + " 次处理 =====");
                log("[边扫边报] 活动：" + (it.name || "未知"));
                log("[边扫边报] 商户：" + (it.merchant || "未知"));
                log("[边扫边报] 价值：" + (it.value === null ? "未知" : it.value + "元"));
                log("[边扫边报] 区域：" + (it.area || "未知"));
                log("[边扫边报] 距离：" + (it.distance || "未知"));
                var inlineStatus = "";
                var clickOkResult = null;
                try {
                    clickOkResult = diagnoseFreeDrawClick({
                        name: it.name, merchant: it.merchant, value: it.value,
                        area: it.area, distance: it.distance, key: it.key,
                        node: it.node
                    });
                    if (clickOkResult && clickOkResult.ok) {
                        log("[边扫边报] 卡片点击成功，进入详情页");
                        inlineStatus = handleSignupInDetail(it);
                    } else {
                        inlineStatus = "卡片点击失败：" + (clickOkResult && clickOkResult.reason || "未知原因");
                        log("[边扫边报] " + inlineStatus);
                    }
                } catch (eClick) {
                    inlineStatus = "处理异常：" + String(eClick);
                    logError("[边扫边报] 处理异常", eClick);
                }

                // 只有真正进入详情页才标记为已处理。此前在点击前标记，
                // 一旦定位/点击偶发失败，后续重扫会直接跳过这张卡片。
                if (clickOkResult && clickOkResult.ok) {
                    processedKeys[it.key] = true;
                    processedKeys[processKey] = true;
                } else {
                    failedProcessAttempts[processKey] = failedAttempts + 1;
                    if (failedProcessAttempts[processKey] < MAX_FAILED_PROCESS_ATTEMPTS) {
                        log("[边扫边报] 点击失败，第" + failedProcessAttempts[processKey] +
                            "次失败，当前屏重扫后重试");
                    } else {
                        // 达到上限后才标记，防止卡片永久阻塞后续活动。
                        processedKeys[it.key] = true;
                        processedKeys[processKey] = true;
                        log("[边扫边报] 点击连续失败" + MAX_FAILED_PROCESS_ATTEMPTS +
                            "次，跳过该活动避免循环");
                    }
                }

                results.push({ activity: it, status: inlineStatus });
                logAutoSignupResult(it, inlineStatus, results.length - 1, qualifiedList.length);
                if (typeof postTelemetry === "function") {
                    postTelemetry({ event: "progress", version: __SCRIPT_VERSION, n: results.length, total: qualifiedList.length, name: String(it.name || "").substring(0, 30), status: String(inlineStatus).substring(0, 60) });
                }
                // 等级资格弹窗表示当前账号无法报名后续同批次活动；停在详情页结束，
                // 避免关闭弹窗后继续点下一家。
                if (gStopAfterLevelRequirement) {
                    endReason = gStopAfterLevelRequirementReason || "等级资格不足，停止后续报名";
                    inlineProcessedThisScreen = true;
                    log("[边扫边报] " + endReason);
                    break;
                }

                // 返回列表，继续扫描
                log("[边扫边报] 返回免费试列表");
                try { returnToList(4); } catch (eRet) { logError("[边扫边报] 返回列表异常", eRet); }
                sleepMs(1000);

                // v1.42.1：如果返回后不在大众点评前台（如被短信通知拉走），重新拉起
                if (!isListPage()) {
                    var curPkg = "";
                    try { curPkg = getCurrentPackage(); } catch (ePkg) {}
                    if (curPkg && curPkg.indexOf("dianping") < 0) {
                        log("[边扫边报] 已跳转到其他应用：" + curPkg + "，重新拉起大众点评");
                        try {
                            app.launch("com.dianping.v1");
                            sleepMs(2000);
                        } catch (eLaunch) {}
                    }
                }

                if (!isListPage()) {
                    log("[边扫边报] 返回后不在列表页，尝试恢复");
                    try { goBack(); sleepMs(1000); } catch (eBk) {}
                    if (!isListPage()) {
                        try { goBack(); sleepMs(1000); } catch (eBk2) {}
                    }
                    if (!isListPage()) {
                        log("[边扫边报] 恢复失败，停止扫描");
                        inlineProcessedThisScreen = true;
                        break;
                    }
                }
                inlineProcessedThisScreen = true;
                // v1.42.2：处理完一个，break 内层循环，外层重新扫描当前屏
                rescanCurrentScreen = true;
                break;
            }

            if (!it.registered && !it.qualified && !processedKeys[it.key]) {
                log("[边扫边报] 当前活动未进入报名队列：" + (it.name || "未知") +
                    "，原因=" + (it.reason || "未知"));
            }
        }

        if (gStopAfterLevelRequirement) {
            endReason = gStopAfterLevelRequirementReason || "等级资格不足，停止后续报名";
            break;
        }

        // 同屏重扫是为了继续处理剩余卡片；此时不能让同屏已报名卡片
        // 提前触发列表尾部判断，否则它下面的活动会被漏掉。
        if (rescanCurrentScreen) {
            continue;
        }

        // 已报名活动可能已经没有「免费抽」按钮。它只保留在全量诊断
        // 结果中，绝不补入自动报名队列。
        if (result.registeredFound) {
            for (var rsi = 0; rsi < result.registeredActivities.length; rsi++) {
                var registered = result.registeredActivities[rsi];
                var registeredAllExists = false;

                for (var rai = 0; rai < allScannedList.length; rai++) {
                    if (allScannedList[rai].key === registered.key) {
                        registeredAllExists = true;
                        break;
                    }
                }

                if (!registeredAllExists) {
                    allScannedList.push({
                        name: registered.name,
                        merchant: registered.merchant,
                        value: registered.value,
                        area: registered.area,
                        distance: registered.distance,
                        category: registered.category,
                        registered: true,
                        key: registered.key
                    });
                }
            }

            // 明确的「已报名」卡片就是当前列表批次的尾部标志。
            // 不再继续滑动，不回顶，不把它加入自动报名队列。
            var registeredName = result.registeredActivity && result.registeredActivity.name;
            endReason = "发现已报名活动";
            gFoundRegistered = true;
            setScriptState("FOUND_REGISTERED");
            log("[状态] FOUND_REGISTERED");
            log("[列表] 发现已报名项目，停止向下扫描");
            log("[列表] 不再扫描后续页面");
            log("[列表] 准备点击回到顶部");
            log("[扫描] 发现已报名活动：" + (registeredName || "未知活动"));
            log("[扫描] 已到达当前列表尾部");
            log("[扫描] 停止继续扫描");
            break;
        }

        if (result.newCount === 0) {
            consecutiveEmpty++;
            log("[列表] 本屏没有发现新活动（连续 " + consecutiveEmpty + " 次）");
        } else {
            consecutiveEmpty = 0;
        }

        var end = detectListEnd(result.newCount, page);

        if (end) {
            log("[扫描] 到底检测：" + end);
            endReason = end;
            break;
        }

        if (consecutiveEmpty >= CONFIG.MAX_CONSECUTIVE_EMPTY_SCROLLS) {
            endReason = "连续 " + consecutiveEmpty + " 次滚动未发现新活动";
            log("[扫描] " + endReason + "，安全结束扫描");
            break;
        }

        if (page + 1 >= CONFIG.MAX_SCAN_SCROLLS) {
            endReason = "达到最大扫描轮数 " + CONFIG.MAX_SCAN_SCROLLS;
            log("[扫描] 达到最大扫描轮数，安全结束扫描");
            break;
        }

        if (Date.now() - gScanStartMs > CONFIG.MAX_SCAN_TIME_MS) {
            endReason = "达到最大扫描时间 " + Math.round(CONFIG.MAX_SCAN_TIME_MS / 60000) + " 分钟";
            log("[扫描] 达到最大扫描时间，安全结束扫描");
            break;
        }

        // v1.42.2：rescanCurrentScreen 时跳过滚动，由外层循环顶部重新扫描
        if (!rescanCurrentScreen) {
            scrollListOnce();
        }
    }

    // v1.9.8：定位阶段每次滚动后检查是否仍在列表页
    // 如果误点进入详情页（如橙V专享价等），立即返回避免在错误页面翻页
    // （此检查在 scrollListOnce 之后、下一轮 snapshot 之前执行）

    markScanFinished(endReason || "列表已扫描到底");

    log("[扫描] ========================================");
    log("[扫描] 扫描阶段完成");
    log("[扫描] 共扫描活动：" + totalNew);
    log("[扫描] 符合条件活动：" + qualifiedList.length);
    log("[扫描] 结束原因：" + gScanEndReason);
    log("[扫描] ========================================");
    log("[筛选] 扫描完成");
    log("[筛选] 共扫描到 " + totalNew + " 个不同活动");
    log("[筛选] 符合条件活动：" + qualifiedList.length + " 个");
    if (gStopAfterLevelRequirement) {
        log("[安全停止] 检测到等级资格不足，已停止后续商户报名");
        toastMsg("等级不足，脚本已停止");
    }

    if (qualifiedList.length === 0) {
        log("[边扫边报] 没有需要报名的活动");
        setScriptState("DONE");
        toastMsg("免费试列表扫描完成");
        return {
            allScanned: allScannedList,
            qualifiedList: qualifiedList,
            endReason: gScanEndReason,
            totalScanned: totalNew
        };
    }

    // v1.42.0：边扫边报已完成，输出汇总
    log("[边扫边报] ========================================");
    log("[边扫边报] 全部处理完成，共处理 " + results.length + " 个");
    for (var ri = 0; ri < results.length; ri++) {
        var rit = results[ri].activity;
        log("[边扫边报] " + (ri + 1) + ". " + (rit.name || "未知活动") +
            " | " + (rit.value === null ? "?" : rit.value) + "元" +
            " | " + (rit.area || "未知区域") +
            " | " + results[ri].status);
    }
    var cntSuccess = 0, cntAlready = 0, cntUnavailable = 0, cntFailed = 0;
    for (var ci = 0; ci < results.length; ci++) {
        var cat = categorizeSignupStatus(results[ci].status);
        if (cat === "success") cntSuccess++;
        else if (cat === "already") cntAlready++;
        else if (cat === "unavailable") cntUnavailable++;
        else cntFailed++;
    }
    log("========================================");
    log("扫描及自动报名完成");
    log("========================================");
    log("共发现符合条件活动：" + qualifiedList.length);
    log("成功报名：" + cntSuccess);
    log("已报名：" + cntAlready);
    log("不可报名：" + cntUnavailable);
    log("失败/无法确认：" + cntFailed);
    if (typeof postTelemetry === "function") {
        var tItems = [];
        for (var ti = 0; ti < results.length; ti++) {
            var tt = results[ti].activity;
            tItems.push({ n: ti + 1, name: String(tt.name || "").substring(0, 40), value: tt.value, area: tt.area || "", status: String(results[ti].status).substring(0, 60) });
        }
        postTelemetry({ event: "summary", version: __SCRIPT_VERSION, qualifiedTotal: qualifiedList.length, processed: results.length, success: cntSuccess, already: cntAlready, unavailable: cntUnavailable, failed: cntFailed });
        postTelemetryItems(tItems);
    }
    toastMsg("扫描及自动报名完成");
    setScriptState("DONE");

    return {
        allScanned: allScannedList,
        qualifiedList: qualifiedList,
        endReason: gScanEndReason,
        totalScanned: totalNew
    };
}

// ---------- v1.7：逐个处理符合条件活动 ----------

// 与扫描阶段一致的活动唯一键：名称 + 价值 + 商户/区域
function buildActivityKey(name, value, merchant, area, positionKey) {
    var base = (name || "未知活动") + "|" +
        (value === null ? "?" : value) + "|" +
        (merchant || area || "未知");

    // 解析失败时不能让同屏多张卡片都使用同一个
    // “未知活动|?|未知”键，否则后一张（可能正是100元卡）会被去重掉。
    if (!name && value === null && !merchant && !area && positionKey) {
        return base + "|pos:" + String(positionKey);
    }

    return base;
}

function buildActivityProcessKey(activity) {
    var name = normalizeNameForMatch(activity && activity.name);
    var merchant = normalizeNameForMatch(activity && activity.merchant);

    if (name && merchant) {
        return "activity|" + name + "|" + merchant;
    }

    if (name) {
        return "activity|" + name;
    }

    if (merchant) {
        return "merchant|" + merchant;
    }

    return "raw|" + String(activity && activity.key || "");
}

function screenSignature() {
    var infos = getVisibleTextInfos();
    var parts = [];

    for (var i = 0; i < infos.length && i < 20; i++) {
        parts.push(infos[i].text);
    }

    return parts.join("|");
}

function scrollListUpOnce() {
    // v1.34.0：页面守卫——如果当前在「我的」页面，绝对禁止继续滚动
    if (isMyPage()) {
        log("[页面守卫] scrollListUpOnce 检测到「我的」页面，禁止向上滚动");
        return;
    }
    try {
        swipe(
            device.width * 0.5,
            device.height * 0.3,
            device.width * 0.5,
            device.height * 0.8,
            600
        );
    } catch (e) {
        logError("向上滚动列表失败", e);
    }

    sleepMs(CONFIG.SCROLL_WAIT_MS);
}

// 当前屏幕解析出的活动名（归一化），用于判断是否回到扫描时的首屏
function currentScreenNames() {
    var names = [];
    var snapshot = [];

    try {
        snapshot = getFreeDrawSnapshot();
    } catch (e) {
    }

    for (var i = 0; i < snapshot.length; i++) {
        var item = snapshot[i];
        var lowerY = i === 0 ? 0 : snapshot[i - 1].bottom;
        var parsed = parseCardFields(collectCardTexts(item, lowerY));
        var nn = normalizeNameForMatch(parsed.name);

        if (nn && names.indexOf(nn) < 0) {
            names.push(nn);
        }
    }

    return names;
}

// 当前屏是否出现扫描阶段记录的首屏活动；
// 没有首屏样本时返回 null，调用方按旧的签名稳定性逻辑处理
function isScanTopVisible() {
    if (!gScanTopNames.length) {
        return null;
    }

    var names = currentScreenNames();

    for (var i = 0; i < names.length; i++) {
        if (gScanTopNames.indexOf(names[i]) >= 0) {
            return true;
        }
    }

    return false;
}

// 列表右下角「回顶部」箭头按钮：优先用它回顶，
// 避免连续快速上滑触发大众点评的下拉刷新（会把整个列表换成另一批活动）
function clickBackToTopButton() {
    log("[回顶] 开始定位右下角「↑ 回到顶部」按钮");
    var re = /回.{0,2}顶部/;
    var candidates = [];

    // 方式1：无障碍 desc 匹配「回到顶部」
    try {
        eachNode(descMatches(re).find(), function (n) {
            candidates.push(n);
        });
    } catch (e) {
    }

    // 方式2：无障碍 text 匹配「回到顶部」
    if (!candidates.length) {
        try {
            eachNode(textMatches(re).find(), function (n) {
                candidates.push(n);
            });
        } catch (e) {
        }
    }

    // 方式3（v1.35.1 新增）：短文本/箭头字符匹配
    // ↑ 按钮可能携带 1~3 字符的短文本（如 "↑"、"▲" 等），
    // 之前方式4（图标识别）会因为 safeText(safeDesc) 过滤掉它。
    // 这里专门在右下角区域搜索含箭头类字符的小尺寸节点。
    if (!candidates.length) {
        log("[回顶] 文字/描述均未匹配，尝试箭头短文本识别");
        var arrowRe = /^[↑▲△^<]{1,3}$/;
        try {
            eachNode(classNameMatches(/./).find(), function (n) {
                try {
                    var txt = safeText(n);
                    var dsc = safeDesc(n);
                    // 只接受极短的文本（1-3 字符）且含箭头类字符
                    var combined = (txt || '') + (dsc || '');
                    if (!combined || combined.length > 4) { return; }
                    if (!arrowRe.test(combined)) { return; }
                    var b = n.bounds();
                    if (!b) { return; }
                    var w = b.right - b.left;
                    var h = b.bottom - b.top;
                    if (w < 30 || w > 300 || h < 30 || h > 300) { return; }
                    if (Math.abs(w - h) > 80) { return; }
                    if (b.left < device.width * 0.65) { return; }
                    if (b.top < device.height * 0.45 || b.top > device.height * 0.95) { return; }
                    log("[回顶] 箭头短文本候选: text='" + txt + "' desc='" + dsc + "' bounds=" + b.left + "," + b.top + "," + b.right + "," + b.bottom);
                    candidates.push(n);
                } catch (e2) {}
            });
        } catch (e) {}
    }

    // 方式4：右下角无文字的小尺寸图标兜底
    if (!candidates.length) {
        log("[回顶] 尝试宽松图标定位（放宽边界条件）");
        try {
            eachNode(classNameMatches(/./).find(), function (n) {
                try {
                    if (safeText(n) || safeDesc(n)) {
                        return;
                    }
                    var b = n.bounds();
                    if (!b) { return; }
                    var w = b.right - b.left;
                    var h = b.bottom - b.top;
                    if (w < 20 || w > 350 || h < 20 || h > 350) { return; }
                    if (Math.abs(w - h) > 100) { return; }
                    if (b.left < device.width * 0.55) { return; }
                    if (b.top < device.height * 0.6 || b.top > device.height * 0.96) { return; }
                    log("[回顶] 宽松图标候选: class=" + safeClass(n) + " bounds=" + b.left + "," + b.top + "," + b.right + "," + b.bottom);
                    candidates.push(n);
                } catch (e) {
                }
            });
        } catch (e) {
        }
    }

    // 所有无障碍方式均失败 → 不使用坐标兜底（v1.34.0：避免误点「我的」）
    if (!candidates.length) {
        log("[回顶] 所有无障碍方式均未找到回顶部节点，不使用坐标兜底");
        return false;
    }

    log("[回顶] 找到回顶部按钮节点，正在点击");
    var before = screenSignature();
    if (!clickNodeSmart(candidates[0])) {
        log("[回顶] clickNodeSmart 返回 false");
        return false;
    }
    sleepMs(CONFIG.WAIT_NORMAL);
    // 点击后校验：页面必须仍然是免费试列表
    var stillList = existsText("全部商区") || existsText("全部分类");
    if (!stillList) {
        try { stillList = getFreeDrawSnapshot().length > 0; } catch (e) {}
    }
    if (!stillList) {
        log("[回顶] 点击后页面不像免费试列表，已返回上一页恢复");
        goBack();
        return false;
    }
    if (screenSignature() === before) {
        log("[回顶] 页面签名未变化，无法确认是否已到顶");
        return false;
    }
    log("[回顶] 已点击回顶部按钮，页面已变化");
    return true;
}
// 扫描结束后列表停在底部，先回到顶部再从头定位目标卡片。
// 优先点击右下角「回顶部」箭头按钮；找不到按钮时才向上滑动，
// 且最多 8 次（原来 15 次快速上滑容易触发下拉刷新，把整个列表换掉）
function scrollListToTop() {
    log("[回顶] 正在回到列表顶部");
    // v1.34.0：先检查是否在「我的」页面，如果是则绝对不能继续操作
    if (isMyPage()) {
        log("[安全停止] 检测到「我的」页面，禁止执行回顶部操作");
        return false;
    }
    // v1.38.0：简化回顶部逻辑
    // 尝试点击无障碍节点找到的回顶部按钮
    var clicked = clickBackToTopButton();
    if (clicked) {
        log("[回顶] 已点击回顶部按钮，等待生效");
        sleepMs(1500);
        if (isListPage()) {
            log("[回顶] 按钮点击成功，已确认回到顶部");
            return true;
        }
        log("[回顶] 按钮点击后不在列表页，尝试返回");
        try { goBack(); sleepMs(500); } catch (e) {}
    }

    // 按钮找不到或点击无效，用swipe上滑回到顶部
    // v1.41.0：修正swipe方向 + 删除吸顶筛选栏误判 + 用顶部横幅检测到顶
    log("[回顶] 使用 swipe 上滑回到顶部");
    var maxSwipe = 30;
    var prevSig = "";
    for (var s = 0; s < maxSwipe; s++) {
        // v1.41.0：顶部横幅检测（"霸气"/"去兑换免费试"只在列表最顶部出现）
        if (existsText("霸气") || existsText("去兑换免费试")) {
            log("[回顶] swipe第" + (s + 1) + "次后检测到顶部横幅，已到顶");
            return true;
        }
        // 检测到扫描首屏活动 = 到顶（旧数据可能过期，仅作辅助）
        if (isScanTopVisible() === true) {
            log("[回顶] swipe第" + (s + 1) + "次后检测到顶部活动，已到顶");
            return true;
        }
        // v1.41.0：swipe后签名连续不变 = 已到顶（列表无法继续上滚）
        var curSig = screenSignature();
        if (s > 0 && curSig === prevSig && curSig !== "") {
            log("[回顶] swipe第" + (s + 1) + "次后签名不变，判定已到顶");
            return true;
        }
        prevSig = curSig;
        // 安全检查：是否误入「我的」
        if (isMyPage()) {
            log("[安全停止] swipe 过程中检测到「我的」页面，立即停止");
            return false;
        }
        try {
            // v1.41.0：修正方向——手指从y=0.3滑到y=0.7 = 手指向下 = 列表向上滚动 = 回顶部
            swipe(device.width * 0.5, device.height * 0.3, device.width * 0.5, device.height * 0.7, 600);
            sleepMs(400);
        } catch (e) {}
    }
    log("[回顶] swipe " + maxSwipe + " 次后仍未确认到达顶部");
    log("[安全停止] 无法确认回到列表顶部");
    return false;
}


function logClickDiagNode(tag, node) {
    log(tag +
        " text=" + safeText(node) +
        " desc=" + safeDesc(node) +
        " class=" + safeClass(node) +
        " clickable=" + safeClickable(node) +
        " enabled=" + safeEnabled(node) +
        " visible=" + safeVisible(node) +
        " bounds=" + formatBounds(safeBounds(node)));
}

function countNodesByClass(re) {
    var n = 0;

    try {
        eachNode(classNameMatches(re), function () {
            n++;
        });
    } catch (e) {
    }

    return n;
}

// 页面签名：前台包名 + 可见文本集合 + Dialog/WebView 节点数
function capturePageSignature() {
    var sig = { pkg: "", count: 0, texts: {}, dialogs: 0, webviews: 0 };

    try {
        sig.pkg = String(currentPackage() || "");
    } catch (e) {
    }

    var infos = [];

    try {
        infos = getVisibleTextInfos();
    } catch (e) {
    }

    sig.count = infos.length;

    for (var i = 0; i < infos.length; i++) {
        var t = infos[i].text;

        if (t) {
            sig.texts[t] = true;
        }
    }

    sig.dialogs = countNodesByClass(/Dialog/);
    sig.webviews = countNodesByClass(/WebView/);

    return sig;
}

// 新增+消失文本 >= 4 才算页面变化，避免倒计时等单条文本刷新造成误判
function diffPageSignature(before, after) {
    var diff = {
        pkgChanged: before.pkg !== after.pkg,
        newTexts: [],
        missingCount: 0,
        changed: false
    };
    var t;

    for (t in after.texts) {
        if (after.texts.hasOwnProperty(t) && !before.texts[t]) {
            diff.newTexts.push(t);
        }
    }

    for (t in before.texts) {
        if (before.texts.hasOwnProperty(t) && !after.texts[t]) {
            diff.missingCount++;
        }
    }

    diff.changed = diff.pkgChanged || (diff.newTexts.length + diff.missingCount) >= 4;

    return diff;
}

function normalizePlainText(s) {
    return String(s || "").replace(/[\s\uFFFC]/g, "");
}

function signatureContains(sig, keyword) {
    for (var t in sig.texts) {
        if (sig.texts.hasOwnProperty(t) && t.indexOf(keyword) >= 0) {
            return true;
        }
    }

    return false;
}

function signatureContainsNormalized(sig, keyword) {
    var target = normalizePlainText(keyword);

    if (!target) {
        return false;
    }

    for (var t in sig.texts) {
        if (sig.texts.hasOwnProperty(t) && normalizePlainText(t).indexOf(target) >= 0) {
            return true;
        }
    }

    return false;
}

// 全节点文本/描述搜索（Button 等控件的文本不在 getVisibleTextInfos 里）
function anyTextContains(keyword) {
    var found = false;

    try {
        eachNode(textContains(keyword).find(), function () {
            found = true;
        });
    } catch (e) {
    }

    if (!found) {
        try {
            eachNode(descContains(keyword).find(), function () {
                found = true;
            });
        } catch (e) {
        }
    }

    return found;
}

// 点击后页面状态 dump + 目标活动匹配检查
// v1.45.4：部分活动详情页由 WebView/分段文本渲染，标题和商户名
// 不一定出现在无障碍文本中，导致名称匹配失败。此时只有在页面已发生明显切换，
// 且出现详情页专属结构（报名按钮或多个详情字段）时才允许确认，避免把普通列表变化
// 当成详情页。
function detectDetailPageStructure(after, diff) {
    var signupSignals = ["我要报名", "立即报名", "免费报名", "立即参与", "参加活动"];
    var detailSignals = ["活动详情", "活动流程", "活动内容", "活动规则", "报名须知", "抽奖规则"];
    var signupHit = false;
    var detailHitCount = 0;
    var i;

    for (i = 0; i < signupSignals.length; i++) {
        if (signatureContainsNormalized(after, signupSignals[i]) || anyTextContains(signupSignals[i])) {
            signupHit = true;
            break;
        }
    }

    for (i = 0; i < detailSignals.length; i++) {
        if (signatureContainsNormalized(after, detailSignals[i]) || anyTextContains(detailSignals[i])) {
            detailHitCount++;
        }
    }

    // 出现报名按钮是最强确认；页面变化后列表入口消失时即可接受。
    var freeDrawGone = !signatureContainsNormalized(after, "免费抽") && !anyTextContains("免费抽");
    var listFilterGone = !signatureContainsNormalized(after, "全部分类") && !anyTextContains("全部分类");
    if (signupHit && (freeDrawGone || listFilterGone)) {
        return "DETAIL_PAGE_STRUCTURE_SIGNUP";
    }

    // 没有暴露报名按钮时，至少要求两个详情字段 + 列表内容消失 + 明显页面变化。
    if (detailHitCount >= 2 && freeDrawGone && diff.missingCount >= 4) {
        return "DETAIL_PAGE_STRUCTURE";
    }

    return null;
}
function dumpPostClickState(before, after, diff, activity) {
    log("[点击诊断] 点击后前台包名：" + after.pkg);
    log("[点击诊断] 点击后文本数量：" + after.count);

    var fullName = normalizePlainText(activity.name);
    var stillThere = false;

    if (fullName) {
        for (var t in after.texts) {
            if (after.texts.hasOwnProperty(t) && normalizePlainText(t).indexOf(fullName) >= 0) {
                stillThere = true;
                break;
            }
        }
    }

    log("[点击诊断] 原活动是否仍存在：" + (stillThere ? "是" : "否"));
    log("[点击诊断] 是否出现「我要报名」：" + (anyTextContains("我要报名") ? "是" : "否"));
    log("[点击诊断] 是否出现「免费抽」：" + (anyTextContains("免费抽") ? "是" : "否"));
    log("[点击诊断] 是否出现「活动详情」：" + (anyTextContains("活动详情") ? "是" : "否"));
    log("[点击诊断] 是否出现新的Dialog：" + (after.dialogs > before.dialogs ? "是（" + after.dialogs + "个）" : "否"));
    log("[点击诊断] 是否出现WebView相关节点：" + (after.webviews > 0 ? "是（" + after.webviews + "个）" : "否"));

    log("[点击诊断] 新出现的文本（最多20条）：");

    for (var i = 0; i < Math.min(20, diff.newTexts.length); i++) {
        log("[点击诊断] 新文本[" + i + "] " + diff.newTexts[i]);
    }

    // 匹配候选：商户名 + 活动名品牌段，不用「双人套餐」这类通用词
    var probes = [];

    if (activity.merchant && activity.merchant.length >= 2) {
        probes.push(activity.merchant);
    }

    if (activity.name) {
        var fp = String(activity.name).split(/[|｜·•]/)[0].replace(/[\s\uFFFC]/g, "");

        if (fp.length >= 3 && probes.indexOf(fp) < 0) {
            probes.push(fp);
        }
    }

    var matched = null;

    for (var pIdx = 0; pIdx < probes.length; pIdx++) {
        if (signatureContainsNormalized(after, probes[pIdx]) || anyTextContains(probes[pIdx])) {
            matched = probes[pIdx];
            break;
        }
    }

    if (matched) {
        // v1.28.0: 橙V专享/零售价特征检测——页面进入错误页面（橙V专享推荐区）时
        // 商户名会出现在推荐区域，必须拒绝匹配
        var wrongPageHits = 0;
        // v1.31.0: only detect 橙V专享价 tab page, not 橙V专享 badge on detail page
        if (anyTextContains("橙V专享价")) wrongPageHits++;
        if (anyTextContains("零售价")) wrongPageHits++;
        if (anyTextContains("橙V立减")) wrongPageHits++;

        if (wrongPageHits >= 2) {
            log("[v1.28.0] 名称匹配「" + matched + "」，但页面含" + wrongPageHits + "个橙V特征，判定为错误页面（橙V专享推荐区），拒绝匹配");
            matched = null;
        } else if (anyTextContains("零售价") && anyTextContains("免费抽")) {
            log("[v1.28.0] 名称匹配「" + matched + "」，但页面同时有「零售价」和「免费抽」，判定为橙V专享推荐区，拒绝匹配");
            matched = null;
        }
    }

    if (matched) {
        log("[v1.6.1] 详情内容与目标活动匹配：" + matched);
        return matched;
    }

    // v1.32.0: 精确名称未匹配 → 视为失败（TARGET_DETAIL_UNCONFIRMED）
    // 不再返回 _page_changed_uncertain 让调用方继续报名流程。
    // 原则：无法确认目标活动就禁止进入报名。
    var listTextsGone = diff.missingCount >= 20;
    var freeDrawGone = !anyTextContains("免费抽");
    var stillOnDianping = after.pkg.indexOf("dianping") >= 0;

    if (listTextsGone && freeDrawGone && stillOnDianping) {
        log("[v1.32.0] 精确名称未匹配，页面已离开列表但无法确认目标活动，拒绝报名");
        log("[v1.32.0] 消失文本" + diff.missingCount + "条，免费抽消失，仍在大众点评");
    }

    // v1.45.4：标题可能在 WebView 中不可见，使用详情页结构作为安全兜底。
    // 该兜底要求出现报名/详情专属信号，且列表入口已消失，不接受普通页面变化。
    var structureMatched = detectDetailPageStructure(after, diff);
    if (structureMatched) {
        log("[v1.45.4] " + structureMatched + "：标题无障碍文本不可见，但详情页结构已确认");
        return structureMatched;
    }

    log("[v1.32.0] TARGET_DETAIL_UNCONFIRMED：页面变化后的内容与目标活动不匹配");
    return null;
}

function clickNodeCenter(node) {
    var b = safeBounds(node);

    if (!b || b.right <= b.left || b.bottom <= b.top) {
        log("[点击诊断] 节点 bounds 无效，无法坐标点击");
        return false;
    }

    return click((b.left + b.right) / 2, (b.top + b.bottom) / 2);
}

// v1.32.0：重写「免费抽」按钮点击诊断。
// 核心修复：只允许点击按钮自身的 bounds 中心，
// 禁止任何偏移点击（上方1/3、祖先bounds等），防止误点附近元素（如向上箭头）。
// 新增：按钮必须属于目标活动卡片的边界验证。
// 返回：{ ok, matched } 或 { ok: false, reason }
// v1.39.0：简化卡片点击策略
// 用户确认：整个卡片矩形区域都可以点击进入商户/详情页，
// 不需要精确点击「免费抽」按钮。
// 策略：找到卡片根节点 → 点击卡片中心坐标 → 验证页面变化 → 确认目标活动
function diagnoseFreeDrawClick(activity) {
    var btn = activity.node;
    log("[免费试定位] ========== v1.45.6 卡片点击 ==========");
    log("[免费试定位] 目标活动：" + (activity.name || "未知"));
    log("[免费试定位] 目标商户：" + (activity.merchant || "未知"));
    var before = capturePageSignature();
    function tryClickFreeDrawButton() {
        var cur = btn;
        for (var depth = 0; depth < 6; depth++) {
            if (!cur) break;
            try {
                var t = "";
                try { t = String(cur.text() || "").trim(); } catch(e) {}
                var clickable = false;
                try { clickable = cur.clickable && cur.clickable(); } catch(e2) {}
                if (t === "免费抽" && clickable) {
                    log("[免费试定位] 尝试点击「免费抽」按钮自身 depth=" + depth);
                    try { cur.click(); sleepMs(400); return true; } catch(e3) { logError("点击免费抽自身失败", e3); }
                }
                if (t === "免费抽") {
                    try {
                        var b = safeBounds(cur);
                        if (b && b.right > b.left && b.bottom > b.top) {
                            var cx = (b.left + b.right)/2;
                            var cy = (b.top + b.bottom)/2;
                            log("[免费试定位] 尝试坐标点击「免费抽」 bounds 中心 (" + Math.round(cx) + "," + Math.round(cy) + ")");
                            click(cx, cy);
                            sleepMs(400);
                            return true;
                        }
                    } catch(e4) {}
                }
                if (clickable) {
                    var hasFreeDrawChild = false;
                    try {
                        var kids = cur.find(text("免费抽"));
                        if (kids && ( (typeof kids.size==="function" && kids.size()>0) || (typeof kids.length==="number" && kids.length>0) )) hasFreeDrawChild = true;
                    } catch(e6) {}
                    if (hasFreeDrawChild || t === "免费抽") {
                        log("[免费试定位] 尝试点击祖先 depth=" + depth + " clickable=" + clickable + " text=" + t);
                        try { cur.click(); sleepMs(400); return true; } catch(e7) {}
                    }
                }
            } catch(e) {}
            try { cur = cur.parent(); } catch(e8) { break; }
            if (!cur) break;
        }
        return false;
    }
    var clickedFreeDraw = tryClickFreeDrawButton();
    if (clickedFreeDraw) {
        log("[免费试定位] 已尝试「免费抽」按钮点击，验证页面变化");
        sleepMs(800);
        var afterBtn = capturePageSignature();
        var diffBtn = diffPageSignature(before, afterBtn);
        log("[点击后] 页面差异：新增文本 " + diffBtn.newTexts.length + " 条，消失文本 " + diffBtn.missingCount + " 条，包名变化：" + diffBtn.pkgChanged);
        if (diffBtn.changed) {
            log("[点击后] 页面已变化（免费抽按钮触发）");
            if (afterBtn.count < 10) {
                for (var w=0; w<6; w++) { sleepMs(500); afterBtn = capturePageSignature(); if (afterBtn.count>=10) break; }
                diffBtn = diffPageSignature(before, afterBtn);
            }
            var isWrongPageBtn = anyTextContains("零售价");
            if (isWrongPageBtn) {
                log("[点击后] 进入了零售价错误页面，判定为点击失败（免费抽路径）");
            } else {
                var matchedBtn = dumpPostClickState(before, afterBtn, diffBtn, activity);
                if (matchedBtn) {
                    log("[v1.45.6] TARGET_DETAIL_CONFIRMED(免费抽)：" + matchedBtn);
                    return { ok: true, matched: matchedBtn };
                }
                log("[v1.45.6] 免费抽点击后页面变化但标题未精确匹配，继续尝试卡片兜底前先判断是否已进入详情");
            }
            log("[免费试定位] 免费抽路径未确认，尝试返回列表后重试卡片点击");
            try { returnToList(2); sleepMs(800); } catch(eRet) {}
            before = capturePageSignature();
        } else {
            log("[点击后] 免费抽点击后页面未变化，降级到卡片点击");
        }
    } else {
        log("[免费试定位] 未能通过「免费抽」按钮直接点击，降级到卡片点击");
    }
    var cardRoot = null;
    try { cardRoot = getSingleCardRoot(btn); } catch(e) {}
    if (!cardRoot) {
        log("[免费试定位] 未找到卡片根节点，使用免费抽按钮节点作为点击目标");
        cardRoot = btn;
    }
    var cardBounds = safeBounds(cardRoot);
    if (!cardBounds || cardBounds.right <= cardBounds.left || cardBounds.bottom <= cardBounds.top) {
        log("[免费试定位] 卡片 bounds 无效，尝试免费抽按钮 bounds");
        cardBounds = safeBounds(btn);
        cardRoot = btn;
    }
    if (!cardBounds || cardBounds.right <= cardBounds.left || cardBounds.bottom <= cardBounds.top) {
        log("[免费试定位] 无法获取有效的 bounds，无法点击");
        return { ok: false, reason: "bounds无效" };
    }
    var clickX = (cardBounds.left + cardBounds.right) / 2;
    var cardHeight = cardBounds.bottom - cardBounds.top;
    var clickY = cardBounds.top + cardHeight * 0.72;
    if (clickY > device.height * 0.88) {
        clickY = Math.min(cardBounds.bottom - 30, device.height * 0.88 - 10);
    }
    var bottomThreshold = device.height * 0.90;
    var bottomSafeY = bottomThreshold - 35;
    if (clickY > bottomThreshold) {
        var upperClickY = cardBounds.top + Math.min(cardHeight * 0.35, 140);
        upperClickY = Math.min(upperClickY, bottomSafeY);
        log("[免费试定位] 卡片下半部在底部区域，尝试点击卡片上部：(" + Math.round(clickX) + "," + Math.round(upperClickY) + ")");
        if (cardBounds.top >= bottomSafeY || upperClickY <= cardBounds.top || upperClickY >= cardBounds.bottom) {
            log("[免费试定位] 卡片上部也进入底部导航区域，拒绝点击（防止误点底部导航）");
            return { ok: false, reason: "卡片在底部导航区域" };
        }
        clickY = upperClickY;
    }
    log("[免费试定位] 卡片 bounds：[" + cardBounds.left + "," + cardBounds.top + "," + cardBounds.right + "," + cardBounds.bottom + "]");
    log("[免费试定位] 点击坐标：(" + Math.round(clickX) + "," + Math.round(clickY) + ")");
    log("[免费试定位] 点击目标：卡片下半部（非卡片中心，避免误点商户图）");
    log("[点击] click attempt");
    log("[点击] 点击前前台包名：" + before.pkg);
    log("[点击] 点击前文本数量：" + before.count);
    var rawRet = "异常";
    try { rawRet = String(click(clickX, clickY)); } catch(e) { logError("点击执行异常", e); rawRet = "异常"; }
    log("[点击] click 返回值：" + rawRet + "（仅参考）");
    sleepMs(1500);
    var after = capturePageSignature();
    var diff = diffPageSignature(before, after);
    log("[点击后] 页面差异：新增文本 " + diff.newTexts.length + " 条，消失文本 " + diff.missingCount + " 条，包名变化：" + diff.pkgChanged);
    if (!diff.changed) {
        log("[点击后] 页面未发生变化，点击无效");
        return { ok: false, reason: "点击未触发页面变化" };
    }
    log("[点击后] 页面已变化");
    if (after.count < 10) {
        log("[点击后] 点击后文本数仅 " + after.count + " 条，等待加载...");
        for (var w2=0; w2<10; w2++) { sleepMs(1000); after = capturePageSignature(); if (after.count >= 10) { log("[点击后] 页面已加载（" + after.count + " 条文本）"); break; } }
        diff = diffPageSignature(before, after);
    }
    var isWrongPage = anyTextContains("零售价");
    if (isWrongPage) {
        log("[点击后] 进入了零售价错误页面，判定为点击失败");
        return { ok: false, reason: "进入了零售价错误页面" };
    }
    var matched = dumpPostClickState(before, after, diff, activity);
    if (matched) {
        log("[v1.45.6] TARGET_DETAIL_CONFIRMED：" + matched);
        return { ok: true, matched: matched };
    }
    log("[v1.45.6] TARGET_DETAIL_UNCONFIRMED：页面变化但无法确认目标活动");
    return { ok: false, reason: "TARGET_DETAIL_UNCONFIRMED" };
}
function normalizeNameForMatch(name) {
    return String(name || "")
        .replace(/[\s\uFFFC\u200B-\u200D\uFEFF]/g, "")
        .replace(/[|｜]/g, "")
        .replace(/(\u2026|\.{3})+$/g, "");
}

function activityMatchesCard(target, parsed) {
    var targetKey = target && target.key ? target.key : String(target || "");
    var cardKey = buildActivityKey(parsed.name, parsed.value, parsed.merchant, parsed.area);

    if (cardKey === targetKey) {
        return true;
    }

    var tn = normalizeNameForMatch(target && target.name);
    var pn = normalizeNameForMatch(parsed.name);

    if (!tn || !pn) {
        return false;
    }

    var nameOk = tn === pn ||
        (tn.length >= 8 && pn.length >= 8 &&
            (tn.indexOf(pn) >= 0 || pn.indexOf(tn) >= 0));

    if (!nameOk) {
        return false;
    }

    if (target && target.value !== null && typeof target.value !== "undefined" &&
        parsed.value !== null && parsed.value !== target.value) {
        return false;
    }

    var tm = normalizeNameForMatch(target && target.merchant);
    var pm = normalizeNameForMatch(parsed.merchant);

    if (tm && tm !== "未知" && pm && pm !== "未知" &&
        tm !== pm && tm.indexOf(pm) < 0 && pm.indexOf(tm) < 0) {
        return false;
    }

    return true;
}


// ---------- v1.8：自动报名 ----------

// 允许识别为报名按钮的明确文字（精确匹配，不做模糊猜测）
var SIGNUP_BUTTON_TEXTS = ["我要报名", "立即报名", "免费报名", "立即参与", "参加活动", "报名"];

// 绝不能当作报名按钮的文字（包含即排除）
var SIGNUP_FORBIDDEN_TEXTS = ["免费抽", "立即抽", "去看看", "立即查看", "领取", "兑换", "购买", "立即开宝箱", "取消", "返回", "关闭", "分享", "收藏"];

function isSignupButtonText(t) {
    // v1.40.0：先去除零宽字符、全角空格等不可见字符，再精确匹配
    t = String(t || "")
        .replace(/[\u200B-\u200D\uFEFF\u2060\u00A0]/g, " ")
        .replace(/\s+/g, " ")
        .trim();

    if (!t) {
        return false;
    }

    for (var f = 0; f < SIGNUP_FORBIDDEN_TEXTS.length; f++) {
        if (t.indexOf(SIGNUP_FORBIDDEN_TEXTS[f]) >= 0) {
            return false;
        }
    }

    for (var i = 0; i < SIGNUP_BUTTON_TEXTS.length; i++) {
        // v1.40.0：用 indexOf 替代严格相等，兼容带前后缀的按钮文本
        if (t === SIGNUP_BUTTON_TEXTS[i] || t.indexOf(SIGNUP_BUTTON_TEXTS[i]) >= 0) {
            return true;
        }
    }

    return false;
}

function safeEnabled(node) {
    try {
        if (typeof node.enabled === "function") {
            return !!node.enabled();
        }
    } catch (e) {
    }

    return true;
}

function safeVisible(node) {
    try {
        if (typeof node.visibleToUser === "function") {
            return !!node.visibleToUser();
        }
    } catch (e) {
    }

    return true;
}

// 详情页常有「3991 人已报名」这类统计文本，contains 匹配会把它
// 误判成本人已报名，这里用正则排除「人」前缀
function hasSignedUpIndicator() {
    // v1.14.0：使用精确匹配避免「人已报名」统计文字的干扰
    // 只匹配：单独的"已报名"文本节点、"已参与"文本节点、"报名成功"文本节点
    var patterns = [/^已报名$/, /^已参与$/, /报名成功/];
    // 也接受包含「您已报名」「已成功报名」等个人状态文本
    var loosePatterns = [/您已报名/, /已成功报名/, /您已参与/, /已成功参与/];

    for (var i = 0; i < patterns.length; i++) {
        try {
            if (textMatches(patterns[i]).exists()) {
                return true;
            }
        } catch (e) {}

        try {
            if (descMatches(patterns[i]).exists()) {
                return true;
            }
        } catch (e) {}
    }

    for (var j = 0; j < loosePatterns.length; j++) {
        try { if (textMatches(loosePatterns[j]).exists()) return true; } catch (e) {}
        try { if (descMatches(loosePatterns[j]).exists()) return true; } catch (e) {}
    }

    return false;
}
// 检查页面中是否存在包含 keyword 但不包含 excludeKeyword 的文本节点。
// 用于区分「名额已满」和「PASS卡兑换名额已满」等旁路状态。
function hasNodeContaining(keyword, excludeKeyword) {
    var found = false;
    try {
        eachNode(textContains(keyword).find(), function (n) {
            var t = safeText(n) || "";
            if (t.indexOf(keyword) >= 0) {
                if (excludeKeyword && t.indexOf(excludeKeyword) >= 0) {
                    return;
                }
                // v1.15.0: also check parent node text for exclusion keyword
                // prevents "PASS card quota full" child nodes from bypassing exclusion
                if (excludeKeyword) {
                    try {
                        var p = n.parent();
                        if (p) {
                            var pt = safeText(p) || "";
                            if (pt.indexOf(excludeKeyword) >= 0) {
                                return;
                            }
                        }
                    } catch (ep) {}
                }
                found = true;
            }
        });
    } catch (e) {}
    return found;
}

// 进入详情后先判断明确的不可报名/已报名状态，命中则直接记录返回，
// 不点击任何按钮
function precheckSignupState() {
    log("[预检] ===== 开始报名状态预检（仅检查状态，不滚动） =====");
    // v1.17.0: 不再下滑页面寻找按钮——按钮由 findSignupButton 独立处理。
    // 这里只检查不可报名的明确状态（已报名/名额已满/已结束等）。

    log("[预检] 检查不可报名状态...");

    if (anyTextContains("活动已结束") || anyTextContains("报名已结束") || existsText("已结束")) {
        log("[预检] 命中：活动已结束");
        return "活动已结束";
    }

    // v1.14.0：名额已满检测，排除PASS卡兑换渠道
    var isQuotaFull = hasNodeContaining("名额已满", "PASS");
    var isSoldOut = anyTextContains("已抢光") || anyTextContains("已抢完");
    if (isQuotaFull || isSoldOut) {
        log("[预检] 命中名额已满（quotaFull=" + isQuotaFull + ",soldOut=" + isSoldOut + "）");
        try {
            eachNode(textContains("名额已满").find(), function (n) {
                log("[预检]   名额已满节点text=\"" + safeText(n) + "\"");
            });
        } catch (e) {}
        return "名额已满";
    }
    log("[预检] 名额未满");

    if (anyTextContains("不符合报名条件") || anyTextContains("暂不支持报名")) {
        log("[预检] 命中：不符合报名条件");
        return "不符合报名条件";
    }

    if (anyTextContains("已过期") || anyTextContains("已下架")) {
        log("[预检] 命中：已过期/已下架");
        return "活动已结束";
    }

    if (hasSignedUpIndicator()) {
        log("[预检] 命中：已报名");
        return "已报名";
    }

    log("[预检] ===== 预检通过，可报名 =====");
    return "";
}

// 在当前详情页寻找明确的报名按钮：精确文本 + 可见可用，
// 找不到宁可跳过也不猜
// v1.9.9：增强按钮发现逻辑，增加等待/重试 + 可点击祖先验证 + 边界过滤
function findSignupButton() {
    // v1.44.0：减少等待时间——详情页已在 handleSignupInDetail 中等待过，
    // 这里只需短暂等待后直接搜索报名按钮
    sleepMs(500);

    log("[自动报名] 直接搜索报名按钮");

    for (var attempt = 0; attempt < 4; attempt++) {
        if (attempt > 0) {
            log("[自动报名] 第" + attempt + "次未找到报名按钮，等待1秒后重试（" + attempt + "/3）");
            sleepMs(1000);
        }

        for (var i = 0; i < SIGNUP_BUTTON_TEXTS.length; i++) {
            var label = SIGNUP_BUTTON_TEXTS[i];
            var nodes = [];

            // 优先使用 text() 精确匹配
            try {
                eachNode(text(label).find(), function (n) {
                    nodes.push(n);
                });
            } catch (e) {
            }

            // text() 未命中时用 textContains() 兜底
            if (!nodes.length) {
                try {
                    eachNode(textContains(label).find(), function (n) {
                        nodes.push(n);
                    });
                } catch (e) {
                }
            }

            for (var j = 0; j < nodes.length; j++) {
                var n = nodes[j];

                if (!isSignupButtonText(safeText(n))) {
                    continue;
                }

                if (!safeEnabled(n) || !safeVisible(n)) {
                    log("[自动报名] 找到「" + label + "」但节点不可用，跳过");
                    continue;
                }

                try {
                    var b = n.bounds();
                    if (b) {
                        var w = b.right - b.left;
                        var h = b.bottom - b.top;
                        if (h > device.height * 0.25 || w > device.width * 0.95) {
                            log("[自动报名] 找到「" + label + "」但尺寸过大（" + w + "x" + h + "），可能是标题，跳过");
                            continue;
                        }
                    }
                } catch (e) {
                }

                var clickableFound = false;
                if (safeClickable(n)) {
                    clickableFound = true;
                } else {
                    var p = n;
                    for (var d = 1; d <= 5; d++) {
                        try { p = p.parent(); } catch (ep) { p = null; }
                        if (!p) break;
                        if (safeClickable(p)) {
                            clickableFound = true;
                            break;
                        }
                    }
                }

                if (!clickableFound) {
                    var fallbackBounds = safeBounds(n);
                    if (!fallbackBounds || fallbackBounds.right <= fallbackBounds.left ||
                        fallbackBounds.bottom <= fallbackBounds.top) {
                        log("[自动报名] 找到「" + label + "」但无可用bounds，跳过");
                        continue;
                    }
                    log("[自动报名] 找到「" + label + "」但无clickable元数据，改用bounds坐标点击");
                }

                log("[自动报名] 报名按钮候选：「" + label + "」（attempt=" + attempt + "）");
                return { node: n, label: label };
            }
        }
    }

    log("[自动报名] 4次尝试均未找到可点击报名按钮，输出页面诊断：");
    try {
        eachNode(textContains("报名").find(), function (n) {
            try {
                var t = safeText(n);
                var c = safeClickable(n);
                var e = safeEnabled(n);
                var v = safeVisible(n);
                log("[自动报名] 诊断节点：text=\"" + t + "\" clickable=" + c + " enabled=" + e + " visible=" + v);
            } catch (e2) {}
        });
    } catch (e3) {}

    return null;
}

// 返回实际使用的点击方式描述；全部不可点击返回 null（调用方可再试 bounds）
function clickSignupButtonOnce(node) {
    if (safeClickable(node)) {
        try {
            node.click();
            return "按钮自身click";
        } catch (e) {
        }
    }

    var p = node;

    for (var d = 1; d <= 5; d++) {
        try {
            p = p.parent();
        } catch (e) {
            p = null;
        }

        if (!p) {
            break;
        }

        if (safeClickable(p)) {
            try {
                p.click();
                return "第" + d + "层clickable祖先click";
            } catch (e2) {
            }
        }
    }

    return null;
}

// 与 dumpPostClickState 相同的探针规则：商户名 + 活动名品牌段
function detailMatchesTarget(activity) {
    var probes = [];

    if (activity.merchant && activity.merchant.length >= 2) {
        probes.push(activity.merchant);
    }

    if (activity.name) {
        var fp = String(activity.name).split(/[|｜·•]/)[0].replace(/[\s\uFFFC]/g, "");

        if (fp.length >= 3 && probes.indexOf(fp) < 0) {
            probes.push(fp);
        }
    }

    for (var i = 0; i < probes.length; i++) {
        if (anyTextContains(probes[i])) {
            return true;
        }
    }

    return false;
}

// 点击报名后验证结果。返回明确结果字符串；无法确认返回 null 让调用方继续判断
// v1.20.0: 增强成功检测——确认弹窗后页面跳转到成功页（含"完成"按钮），
// 此时 hasSignedUpIndicator 可能找不到"已报名"文本，但页面已离开详情页，
// 需要区分"报名成功离开"和"真正的未知状态"。
function verifySignupResult(activity) {
    if (hasLevelRequirementPrompt()) {
        return requestLevelRequirementStop();
    }

    // 确认报名弹窗中的「已参与」不是最终结果，必须先点击确认报名。
    if (hasSignupConfirmationPrompt()) {
        return null;
    }

    if (hasSignedUpIndicator()) {
        log("[自动报名] 检测到已报名/报名成功标识");
        return "报名成功";
    }

    // v1.20.0: 检测成功页特征——页面离开详情但出现"完成"按钮，
    // 说明已进入报名完成/确认页面，视为报名已处理
    var hasDoneButton = false;
    try {
        eachNode(text("完成").find(), function (n) {
            if (safeEnabled(n) && safeVisible(n)) {
                hasDoneButton = true;
            }
        });
    } catch (e) {}

    if (hasDoneButton) {
        log("[自动报名] 检测到「完成」按钮，视为报名已处理（成功页）");
        return "报名成功";
    }

    if (!detailMatchesTarget(activity)) {
        var hasAnySignupContext = anyTextContains("报名成功") || anyTextContains("已报名");
        if (hasAnySignupContext) {
            log("[自动报名] 页面包含报名成功相关文本，视为报名已处理");
            return "报名成功";
        }
        log("[自动报名] 页面已离开目标活动详情，停止操作");
        return "报名结果无法确认（页面离开目标活动）";
    }

    return null;
}


// 确认弹窗：只有页面处于报名上下文（含「报名」字样）才允许点击确认类按钮，
// 且只点一次
function clickSignupConfirmIfPresent() {
    if (!anyTextContains("报名")) {
        return false;
    }

    var confirmTexts = ["确认报名", "立即报名", "确定", "确认"];

    for (var i = 0; i < confirmTexts.length; i++) {
        var label = confirmTexts[i];
        var nodes = findSignupConfirmNodes(label);

        for (var j = 0; j < nodes.length; j++) {
            var n = nodes[j];

            if (normalizeSignupConfirmText(safeText(n)) !== label &&
                normalizeSignupConfirmText(safeDesc(n)) !== label) {
                continue;
            }

            if (!safeEnabled(n) || !safeVisible(n)) {
                continue;
            }

            log("[自动报名] 检测到报名确认弹窗，点击「" + label + "」");

            // v1.18.1: 优先使用 bounds 中心坐标点击——大众点评上 node.click() 无效
            var way = clickNodeCenter(n) ? "bounds中心坐标" : null;

            if (!way) {
                way = clickSignupButtonOnce(n);
            }

            if (way) {
                log("[自动报名] 确认弹窗点击成功（" + way + "）");
                return true;
            }
        }
    }

    return false;
}

function normalizeSignupConfirmText(value) {
    return String(value || "")
        .replace(/[\u200B-\u200D\uFEFF\u2060\u00A0]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function findSignupConfirmNodes(label) {
    var nodes = [];
    var queries = [];

    try { queries.push(text(label)); } catch (e) {}
    try { queries.push(textContains(label)); } catch (e2) {}
    try { queries.push(desc(label)); } catch (e3) {}
    try { queries.push(descContains(label)); } catch (e4) {}

    for (var i = 0; i < queries.length; i++) {
        try {
            eachNode(queries[i].find(), function (n) {
                if (nodes.indexOf(n) < 0) {
                    nodes.push(n);
                }
            });
        } catch (e5) {}
    }

    return nodes;
}

// 大众点评在账号等级不满足时会显示独立弹窗，例如：
// 「你暂未满足报名要求」+「该活动仅Lv6-Lv8且是橙V的用户可报名」。
// 标题是稳定信号，等级/橙V文案作为无标题时的兜底；不要只匹配「等级」，
// 避免把普通活动规则或页面标签误判为全局终止条件。
function hasLevelRequirementPrompt() {
    var titleHints = [
        "你暂未满足报名要求",
        "暂未满足报名要求",
        "未满足报名要求",
        "暂未满足报名条件",
        "未满足报名条件"
    ];

    for (var i = 0; i < titleHints.length; i++) {
        if (anyTextContains(titleHints[i])) {
            return true;
        }
    }

    var hasLv6 = anyTextContains("Lv6") || anyTextContains("LV6") || anyTextContains("lv6");
    var hasLv8 = anyTextContains("Lv8") || anyTextContains("LV8") || anyTextContains("lv8");
    var hasOrangeV = anyTextContains("橙V") || anyTextContains("橙 V");
    return hasLv6 && hasLv8 && hasOrangeV && anyTextContains("可报名");
}

function requestLevelRequirementStop() {
    if (!gStopAfterLevelRequirement) {
        gStopAfterLevelRequirement = true;
        gStopAfterLevelRequirementReason = "等级资格不足，停止后续报名";
        log("[安全停止] 检测到「你暂未满足报名要求」弹窗");
        log("[安全停止] 当前账号等级不满足该批次报名条件，不点击「我知道了」，立即停止脚本");
        setScriptState("SAFE_STOP");
        toastMsg("等级不足，脚本已停止");
    }
    return "等级不足，停止脚本";
}

function hasSignupConfirmationPrompt() {
    return anyTextContains("确认报名");
}

// 报名成功后点击右上角「完成」按钮返回免费试列表
// 大众点评上 node.click() 无效，使用 bounds 中心坐标
function clickDoneButton() {
    var nodes = [];
    try {
        eachNode(text("完成").find(), function (n) { nodes.push(n); });
    } catch (e) {}
    if (!nodes.length) {
        try {
            eachNode(textContains("完成").find(), function (n) { nodes.push(n); });
        } catch (e) {}
    }
    for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        if (!safeEnabled(n) || !safeVisible(n)) continue;
        // 排除尺寸过大的节点（可能是页面标题）
        try {
            var b = n.bounds();
            if (b) {
                var w = b.right - b.left;
                var h = b.bottom - b.top;
                if (h > device.height * 0.25 || w > device.width * 0.95) continue;
            }
        } catch (e) {}
        log("[自动报名] 找到「完成」按钮");
        var way = clickNodeCenter(n) ? "bounds中心坐标" : null;
        if (!way) way = clickSignupButtonOnce(n);
        if (way) {
            log("[自动报名] 已点击「完成」按钮（" + way + "）");
            return true;
        }
    }
    log("[自动报名] 未找到「完成」按钮");
    return false;
}

// 自动报名主流程：精确识别按钮 → 点击 → 验证 → 确认弹窗（最多一次） →
// 仍无法确认则记录并停止，绝不盲点第二次
// v1.16.0: 接受 precheckButtonNode 参数，直接使用预检找到的按钮
function attemptSignup(activity) {
    var found = null;
    // v1.17.0: 不再接受外部传入的按钮节点（可能已失效），始终自己搜索
    found = findSignupButton();

    if (!found) {
        log("[自动报名] 报名按钮无法可靠识别，不点击任何其他按钮");
        return "报名按钮无法可靠识别";
    }

    log("[自动报名] 找到报名按钮：「" + found.label + "」");
    logClickDiagNode("[自动报名] 报名按钮节点", found.node);

    // v1.25.0: 记录点击前页面状态，用于检测点击后页面是否发生变化
    var sigBefore = capturePageSignature();

    // v1.18.1: 优先使用 bounds 中心坐标点击——大众点评上 node.click() 对所有按钮均无效，
    // 与"免费抽"按钮同样的问题，只有 bounds 中心坐标能真正触发点击
    var way = clickNodeCenter(found.node) ? "按钮bounds中心坐标" : null;

    if (!way) {
        log("[自动报名] bounds坐标点击失败，尝试node.click()");
        way = clickSignupButtonOnce(found.node);
    }

    if (!way) {
        log("[自动报名] 报名按钮无法点击，跳过");
        return "报名按钮无法点击";
    }

    log("[自动报名] 已点击报名按钮（" + way + "），等待页面反馈");

    // 确认弹窗和报名成功状态可能晚于首次点击出现，连续等待并优先处理确认。
    var result = null;
    var confirmClicked = false;
    for (var fw = 0; fw < 8; fw++) {
        sleepMs(500);
        if (hasLevelRequirementPrompt()) {
            return requestLevelRequirementStop();
        }
        if (hasSignupConfirmationPrompt()) {
            if (clickSignupConfirmIfPresent()) {
                confirmClicked = true;
                break;
            }
            log("[自动报名] 已检测到确认报名弹窗，等待确认按钮可点击...");
            continue;
        }
        result = verifySignupResult(activity);
        if (result) {
            return result;
        }
    }

    if (confirmClicked) {
        // v1.26.0: 确认弹窗点击后，成功页需要时间加载，轮询等待「完成」按钮（最多5秒）
        log("[自动报名] 确认弹窗已点击，等待成功页加载...");
        for (var cw = 0; cw < 10; cw++) {
            sleepMs(500);
            if (hasLevelRequirementPrompt()) {
                return requestLevelRequirementStop();
            }
            result = verifySignupResult(activity);
            if (result) {
                log("[自动报名] 第" + (cw + 1) + "轮检测到结果：" + result);
                if (result === "报名成功") {
                    // v1.43.0：报名成功后直接按返回键，避免点击「完成」时
                    // 被短信/通知抢走前台导致误入其他应用
                    log("[自动报名] 报名成功，按返回键离开");
                    goBack();
                    sleepMs(300);
                }
                return result;
            }
            log("[自动报名] 第" + (cw + 1) + "轮未检测到完成按钮，继续等待...");
        }
        log("[自动报名] 轮询5秒结束，未检测到完成按钮，尝试兜底");
    }

    // v1.20.0: 简化兜底——再做一次最终确认
    result = verifySignupResult(activity);
    if (result) {
        if (result === "报名成功") {
            // v1.43.0：按返回键代替点击「完成」
            log("[自动报名] 报名成功（兜底），按返回键离开");
            goBack();
            sleepMs(300);
        }
        return result;
    }

    // v1.25.0: 检测页面是否因点击而发生变化
    var sigAfter = capturePageSignature();
    var sigChanged = diffPageSignature(sigBefore, sigAfter).changed;

    if (!sigChanged) {
        log("[自动报名] 点击后页面无变化，无法确认报名结果");
        return "报名结果无法确认（点击后页面无变化）";
    }

    log("[自动报名] 点击后页面已变化但无法确认报名结果");
    return "报名结果无法确认";
}

// 详情页报名入口：先做明确状态预检，可报名时再走自动报名
// v1.16.0: precheckSignupState 返回对象 {status, buttonNode, buttonLabel}
function handleSignupInDetail(activity) {
    // v1.44.0：简化详情页处理
    // - 不再检测"橙V专享价"底部导航栏（它在所有页面都存在，会导致误判）
    // - 不做严格的页面类型判断
    // - 直接等待短暂加载后尝试寻找"我要报名"按钮
    // - 用户反馈：进入商户页面后应直接点"我要报名"，无需判断其他
    log("[详情] 等待详情页加载...");
    var detailReady = false;
    for (var w = 0; w < 8; w++) {
        sleepMs(500);
        var hasDetailHeader = anyTextContains("免费试活动详情") || anyTextContains("我要报名");
        if (hasDetailHeader) {
            detailReady = true;
            log("[详情] 详情页已加载（" + ((w + 1) * 500) + "ms），检测到活动标题或报名按钮");
            break;
        }
    }
    var sig = capturePageSignature();
    log("[详情] 当前页面文本数：" + sig.count);
    if (!detailReady) {
        // v1.44.0：不再因"橙V专享价"（底部导航栏常驻文字）而跳过
        // 直接继续尝试寻找报名按钮
        log("[详情] 等待4秒后未检测到详情标题，继续尝试寻找报名按钮");
    }
    // v1.44.0：不再做严格名称匹配——直接尝试找"我要报名"按钮
    // 如果按钮存在就说明在正确页面，不存在则跳过
    if (hasLevelRequirementPrompt()) {
        return requestLevelRequirementStop();
    }

    var pre = precheckSignupState();

    if (pre && typeof pre === "string") {
        log("[详情] 报名状态判断：" + pre + "，不点击任何按钮");
        return pre;
    }

    // pre 为空字符串 = 预检通过，可报名
    log("[详情] 报名状态判断：可报名，尝试自动报名");
    return attemptSignup(activity);
}
// 最终汇总归类
function categorizeSignupStatus(status) {
    if (status === "报名成功") {
        return "success";
    }

    if (status === "已报名") {
        return "already";
    }

    if (status === "名额已满" || status === "活动已结束" || status === "不符合报名条件" ||
        status === "等级不足，停止脚本") {
        return "unavailable";
    }

    return "failed";
}

// 每个活动处理完立即输出统一格式结果
function logAutoSignupResult(a, status, idx, total) {
    log("[自动报名] " + (idx + 1) + "/" + total);
    log("活动：" + (a.name || "未知"));
    log("商户：" + (a.merchant || "未知"));
    log("价值：" + (a.value === null || typeof a.value === "undefined" ? "未知" : a.value + "元"));
    log("区域：" + (a.area || "未知"));
    log("距离：" + (a.distance || "未知"));
    log("报名结果：" + status);
}


// ---------- 主流程 ----------

function main() {
    log("========================================");
    log("大众点评「免费试」列表扫描 + 自动报名");
    log("脚本：大众点评免费试-扫描自动报名");
    log("版本：" + __SCRIPT_VERSION);
    log("最低价值：" + CONFIG.MIN_VALUE + " 元");
    log("地区：全部地区（区域仅展示，不参与筛选）");
    log(__SCRIPT_VERSION + "：手动入口模式，边扫描边处理符合条件活动并汇总");
    log("========================================");
    toastMsg("免费试列表扫描脚本启动");

    if (!ensureAccessibility()) {
        log("未获得无障碍服务权限，脚本结束");
        return;
    }

    telemetryStage("accessibility_ok");

    if (typeof postTelemetry === "function") {
        postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "accessibility_ok" });
    }

    try {
        log("屏幕尺寸：" + device.width + "x" + device.height);
    } catch (e) {
        logError("读取屏幕尺寸失败", e);
    }

    if (CONFIG.MANUAL_ENTRY) {
        // v1.8.8：不自动拉起/点击首页，只等用户手动停在「免费试」列表页。
        log("启动模式：手动入口（请确认已手动进入大众点评「免费试」列表页）");
        telemetryStage("manual_entry_wait");

        if (typeof postTelemetry === "function") {
            postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "manual_entry_wait" });
        }
    } else {
        launchDianping();
        dismissCommonDialogs();
        telemetryStage("launched");

        if (typeof postTelemetry === "function") {
            postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "launched" });
        }

        var foregroundOk = false;

        try {
            foregroundOk = ensureDianpingForeground();
        } catch (e) {
            logError("确认大众点评前台状态异常", e);
        }

        if (!foregroundOk) {
            // 自动入口模式下启动阶段没抢到前台时不立刻退出；进入入口阶段后
            // 每一轮仍会重新拉起大众点评，并由 ENTRY_HARD_TIMEOUT_MS 兜底停止。
            log("[启动] 大众点评未能在启动阶段切换到前台，进入入口阶段有界重试（最长 " +
                Math.round(CONFIG.ENTRY_HARD_TIMEOUT_MS / 1000) + " 秒）");
        }
    }

    try {
        if (!enterFreeTrial()) {
            if (CONFIG.MANUAL_ENTRY) {
                log("未能识别「免费试」列表页，请确认已手动停在「免费试」列表页后重试");
            } else {
                log("无法进入「免费试」，请确认已在大众点评首页后重试");
            }
            log("入口阶段已结束，脚本不再空转");
            return;
        }

        // 只有真实进入列表才标记 trials_entered；v1.8.7 之前入口卡住时
        // 该阶段永远不出现，便于按日志区分「已进列表」和「仍在找入口」。
        telemetryStage("trials_entered");
        __heartbeatStopped = true;

        if (typeof postTelemetry === "function") {
            postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "trials_entered" });
        }
    } catch (e) {
        logError("进入「免费试」异常", e);
        return;
    }

    // 已成功进入免费试列表：等待页面稳定后重新获取当前页面节点，
    // 不再使用进入首页时保存的节点对象
    log("[列表] 已进入免费试列表");
    log("[列表] 等待页面稳定");
    sleepMs(2500);
    minimizeLogConsole();

    var freshNodeCount = 0;

    try {
        freshNodeCount = getVisibleTextInfos().length;
    } catch (e) {
    }

    log("[列表] 页面节点已重新获取（可见文本 " + freshNodeCount + " 条）");

    try {
        ensureAllRegions();
    } catch (e) {
        logError("确认全部地区异常", e);
    }
    telemetryStage("regions_ok");

    if (typeof postTelemetry === "function") {
        postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "regions_ok" });
    }

    if (CONFIG.SELECT_FOOD_CATEGORY) {
        try {
            var foodClickConfirmed = selectFoodCategory();
            // 点击结果不可靠时，以列表顶部实际显示的“美食”筛选标签兜底。
            __foodCategorySelected = foodClickConfirmed || isFoodFilterSelectedOnList();
            log("[列表] 美食分类筛选：" +
                (__foodCategorySelected ? "已选择" : "未确认，按页面实际文案继续扫描"));
        } catch (e) {
            logError("选择「美食」分类异常", e);
        }
    }

    // v1.28.0：选完分类后短暂等待，然后立即验证是否仍在列表页，
    // 避免在等待期间误点右下角商户卡片
    log("[列表] 等待列表稳定...");
    sleepMs(800);
    if (!isListPage()) {
        log("[列表] 选完分类后离开了列表页，尝试返回");
        try { goBack(); sleepMs(1000); } catch (e) {}
        if (!isListPage()) {
            try { goBack(); sleepMs(1000); } catch (e2) {}
        }
    }
    log("[列表] 等待完成，开始扫描");

    try {
    telemetryStage("scanning");

    if (typeof postTelemetry === "function") {
        postTelemetry({ event: "stage", version: __SCRIPT_VERSION, stage: "scanning" });
    }

        scanFreeTrialList();
    } catch (e) {
        logError("扫描免费试列表异常", e);
    }

    log("========================================");
    log("列表扫描完成，脚本结束");
    log("========================================");
    toastMsg("免费试列表扫描完成");
}

var __scriptStartTime = Date.now();

if (typeof postTelemetry === "function") {
    postTelemetry({ event: "start", version: __SCRIPT_VERSION });
}

if (typeof telemetryHeartbeatLoop === "function") {
    telemetryHeartbeatLoop();
}

try {
    main();
} catch (e) {
    logError("脚本异常", e);

    if (typeof postTelemetry === "function") {
        postTelemetry({ event: "fatal", version: __SCRIPT_VERSION, error: String(e) });
    }
}

__heartbeatStopped = true;

if (typeof postTelemetry === "function") {
    postTelemetry({ event: "end", version: __SCRIPT_VERSION });
}
if (Date.now() - __scriptStartTime < 5000) {
    log("脚本在 5 秒内提前结束，请把上方所有日志发给开发者排查");
    toastMsg("脚本提前结束，请查看 Hamibot 日志");
}




