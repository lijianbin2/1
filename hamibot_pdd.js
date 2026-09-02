auto.waitFor();
console.show();
console.log("pdd v1.3 - 商品页强制back回首页");
// 边缘滑动防误点商品，底部→中部
function swipeEdgeUp(t, interval) {
    t = t || 5; interval = interval || 2000;
    for (let n = 0; n < t; n++) { swipe(1150, 1400, 1150, 700, 600); sleep(interval); }
}
function swipeToTop() { swipe(600, 700, 600, 1400, 600); sleep(1000); }
function isInPdd() { return currentPackage() === "com.xunmeng.pinduoduo"; }

function ensurePdd() {
    let pkg = currentPackage();
    console.log("当前包: " + pkg);
    if (pkg !== "com.xunmeng.pinduoduo") {
        console.log("拉起拼多多...");
        try { launch("com.xunmeng.pinduoduo"); } catch(e) {}
        try { app.launchApp("拼多多"); } catch(e) {}
        try { app.launchPackage("com.xunmeng.pinduoduo"); } catch(e) {}
        sleep(4000);
    } else {
        console.log("已在拼多多，直接进回首页流程");
    }
    // 不再长时间等待首页文本，商品页本来就无省钱月卡，等待只会卡住
    sleep(800);
}

function goHome() {
    console.log("goHome: 从商品页强制回首页...");
    // 关键修复：商品页底部首页tab被隐藏，文本检测不到，所以先无条件back多次
    for (let i = 0; i < 7; i++) {
        if (text("省钱月卡").exists() || text("百亿补贴").findOne(300)) {
            console.log("已回到首页，提前结束 back");
            return;
        }
        // 每次back前尝试点底部首页tab（文本或坐标）
        let homeTab = text("首页").findOne(300) || desc("首页").findOne(300);
        if (homeTab) {
            console.log("发现 首页 tab，点击");
            homeTab.click(); sleep(1500);
            if (text("省钱月卡").exists() || text("百亿补贴").exists()) return;
        }
        console.log("back " + (i+1) + "/7");
        back(); sleep(1000);
        // 给页面加载一点时间
        if (i==2 || i==4) sleep(500);
    }
    // 最后兜底：按比例点首页tab + 检查
    if (text("省钱月卡").exists()) { console.log("最终已在首页"); return; }
    console.log("兜底坐标点击首页");
    let w = device.width, h = device.height;
    // 底部导航第一个tab
    click(w * 0.12, h * 0.93); sleep(1500);
    // 若还是商品页，再补一次back
    if (!text("省钱月卡").exists() && !text("百亿补贴").exists()) {
        console.log("兜底后仍不在首页，再back一次");
        back(); sleep(1200);
    }
    console.log("goHome 结束，当前是否首页: " + (text("省钱月卡").exists() || text("百亿补贴").exists()));
}

// 1 省钱月卡 896,784 -> 立即返回
function s1() {
    if (!isInPdd()) { console.log("s1 跳过：不在拼多多"); return; }
    let f = text("省钱月卡").findOne(800) || desc("省钱月卡").findOne(500) || textContains("省钱月卡").findOne(500);
    if (f) { console.log("点击 省钱月卡"); f.click(); }
    else {
        console.log("文本未找到，坐标兜底 896,784");
        if (isInPdd()) click(896, 784); else console.log("已不在拼多多，取消点击");
    }
    sleep(2500); back(); sleep(1800);
}
// 2 百亿补贴 136,1470
function s2() {
    let e = text("百亿补贴").findOne(1500) || desc("百亿补贴").findOne(500);
    if (e) { console.log("点击 百亿补贴"); e.click(); }
    else if (isInPdd()) { console.log("百亿补贴文本未找到，坐标 136,1470"); click(136, 1470); }
    sleep(3000);
}
// 3 会员 1130,165
function s3() {
    let e = text("会员").findOne(1500) || desc("会员").findOne(500);
    if (e) e.click(); else if (isInPdd()) click(1130, 165);
    sleep(2500);
}
// 4 打卡 385,1180
function s4() {
    let e = text("打卡").findOne(1500) || desc("打卡").findOne(500);
    if (e) e.click(); else if (isInPdd()) click(385, 1180);
    sleep(2000);
}
function s5() { console.log("back 回上一页"); back(); sleep(1500); }
function s6() {
    let e = text("去抢购").findOne(1500);
    if (e) e.click(); else if (isInPdd()) click(640, 770);
    sleep(3000);
}
function s7() {
    let els = text("立即领取").find();
    if (els && els.length > 0) els[0].click(); else if (isInPdd()) click(180, 860);
    sleep(2000);
}
function s8() {
    let light = text("立即点亮").findOne(1500);
    if (light) {
        light.click(); sleep(2000);
        let go = text("去看看").findOne(3000) || textContains("去看看").findOne(1000);
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
    sleep(800);
    ensurePdd();
    goHome();
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1.3");
}
main();