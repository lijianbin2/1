auto.waitFor();
console.show();
console.log("pdd 省钱月卡百亿补贴会员打卡 v1.1 - 修复桌面误点知乎");
// 边缘滑动防误点商品，底部→中部
function swipeEdgeUp(t, interval) {
    t = t || 5; interval = interval || 2000;
    for (let n = 0; n < t; n++) { swipe(1150, 1400, 1150, 700, 600); sleep(interval); }
}
function swipeToTop() { swipe(600, 700, 600, 1400, 600); sleep(1000); }

function ensurePdd() {
    // 1. 如不在拼多多，主动拉起
    let pkg = currentPackage();
    console.log("当前包: " + pkg);
    if (pkg !== "com.xunmeng.pinduoduo") {
        console.log("拉起拼多多...");
        // Hamibot 兼容两种API
        try { launch("com.xunmeng.pinduoduo"); } catch(e) {}
        try { app.launchApp("拼多多"); } catch(e) {}
        try { app.launchPackage("com.xunmeng.pinduoduo"); } catch(e) {}
        sleep(4000);
    }
    // 2. 等待首页关键文本出现，最多等8秒
    let waited = 0;
    while (waited < 8) {
        if (text("省钱月卡").exists() || text("百亿补贴").exists() || text("个人中心").exists() || desc("省钱月卡").exists()) {
            console.log("拼多多首页已就绪");
            break;
        }
        sleep(1000); waited++;
        console.log("等待拼多多加载... " + waited);
    }
    // 3. 通知栏误展开收起 (Hamibot常见)
    if (waited >= 8) {
        console.log("未检测到首页文本，可能还在桌面，尝试收起通知栏并重试拉起");
        try { swipe(600, 200, 600, 1000, 500); sleep(1000); } catch(e) {}
        try { launch("com.xunmeng.pinduoduo"); sleep(3500); } catch(e) {}
    }
}

function isInPdd() { return currentPackage() === "com.xunmeng.pinduoduo"; }

// 1 省钱月卡 896,784 -> 立即返回 (增加包名保护，防止在桌面点到知乎)
function s1() {
    if (!isInPdd()) { console.log("s1 跳过：不在拼多多"); return; }
    let f = text("省钱月卡").findOne(2000) || desc("省钱月卡").findOne(1000) || textContains("省钱月卡").findOne(1000);
    if (f) { console.log("点击文本 省钱月卡"); f.click(); }
    else {
        console.log("文本未找到，坐标兜底 896,784");
        if (isInPdd()) click(896, 784); else console.log("已不在拼多多，取消坐标点击防误点知乎");
    }
    sleep(2500); back(); sleep(2000);
}
// 2 百亿补贴 136,1470
function s2() {
    let e = text("百亿补贴").findOne(2000) || desc("百亿补贴").findOne(1000);
    if (e) e.click(); else if (isInPdd()) click(136, 1470);
    sleep(3000);
}
// 3 会员 1130,165
function s3() {
    let e = text("会员").findOne(2000) || desc("会员").findOne(1000);
    if (e) e.click(); else if (isInPdd()) click(1130, 165);
    sleep(2500);
}
// 4 打卡 385,1180
function s4() {
    let e = text("打卡").findOne(2000) || desc("打卡").findOne(1000);
    if (e) e.click(); else if (isInPdd()) click(385, 1180);
    sleep(2000);
}
// 5 返回上一页
function s5() { back(); sleep(1500); }
// 6 去抢购 640,770 (百亿消费券下方)
function s6() {
    let e = text("去抢购").findOne(2000);
    if (e) e.click(); else if (isInPdd()) click(640, 770);
    sleep(3000);
}
// 7 立即领取 180,860 三选一
function s7() {
    let els = text("立即领取").find();
    if (els && els.length > 0) els[0].click(); else if (isInPdd()) click(180, 860);
    sleep(2000);
}
// 8 条件：立即点亮 1070,410 -> 去看看 640,1360 -> 边缘滑动10秒(5次+补2秒) -> 回顶部
function s8() {
    let light = text("立即点亮").findOne(1500);
    if (light) {
        light.click(); sleep(2000);
        let go = text("去看看").findOne(3000) || textContains("去看看").findOne(2000);
        if (go) go.click(); else if (isInPdd()) click(640, 1360);
        sleep(2500);
        swipeEdgeUp(5, 2000);
        let tip = textContains("还剩").findOne(1000);
        if (tip) { swipe(1150, 1400, 1150, 700, 600); sleep(2500); }
        swipeToTop();
    } else {
        swipeToTop();
    }
}
function main() {
    sleep(1500);
    ensurePdd();
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1.1");
    // 以后扩展：在此追加 s9() s10() ...
}
main();