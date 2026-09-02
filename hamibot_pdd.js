auto.waitFor();
console.show();
console.log("pdd 省钱月卡百亿补贴会员打卡 v1.2 - 回首页导航");
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
    }
    let waited = 0;
    while (waited < 8) {
        if (text("省钱月卡").exists() || text("百亿补贴").exists() || text("个人中心").exists() || desc("省钱月卡").exists()) {
            console.log("拼多多已就绪");
            break;
        }
        sleep(1000); waited++;
        console.log("等待加载... " + waited);
    }
    if (waited >= 8) {
        try { swipe(600, 200, 600, 1000, 500); sleep(1000); } catch(e) {}
        try { launch("com.xunmeng.pinduoduo"); sleep(3500); } catch(e) {}
    }
}

function goHome() {
    console.log("尝试回到首页...");
    // 最多按5次 back 直到出现首页特征
    for (let i = 0; i < 6; i++) {
        if (text("省钱月卡").exists() || text("百亿补贴").exists()) {
            console.log("已在首页");
            return;
        }
        let homeTab = text("首页").findOne(500) || desc("首页").findOne(500);
        // 首页tab通常在底部，如果不在首页，先点首页tab
        if (homeTab) {
            console.log("点击底部 首页 tab");
            homeTab.click(); sleep(2000);
            if (text("省钱月卡").exists() || text("百亿补贴").exists()) return;
        }
        // 还没到首页就 back
        if (i < 5) { console.log("back " + (i+1)); back(); sleep(1200); }
    }
    // 兜底：按底部首页坐标 (不同分辨率用比例，1080*2400 约 150,2200)
    console.log("兜底点击首页坐标");
    // 优先用文本，找不到再坐标
    let h = text("首页").findOne(800);
    if (h) h.click(); else { 
        // 底部导航第一个tab大概在 130, 2300 附近，按屏幕比例兜底
        let w = device.width, hh = device.height;
        click(w * 0.12, hh * 0.93); 
    }
    sleep(2000);
}

// 1 省钱月卡 896,784 -> 立即返回
function s1() {
    if (!isInPdd()) { console.log("s1 跳过：不在拼多多"); return; }
    // 确保在首页才点
    if (!text("省钱月卡").exists() && !textContains("省钱月卡").exists()) {
        console.log("s1 未在首页，尝试 goHome");
        goHome();
    }
    let f = text("省钱月卡").findOne(2000) || desc("省钱月卡").findOne(1000) || textContains("省钱月卡").findOne(1000);
    if (f) { console.log("点击 省钱月卡"); f.click(); }
    else {
        console.log("文本未找到，坐标兜底 896,784");
        if (isInPdd()) click(896, 784); else console.log("已不在拼多多，取消点击");
    }
    sleep(2500); back(); sleep(2000);
}
// 2 百亿补贴 136,1470
function s2() {
    if (!text("百亿补贴").exists()) goHome();
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
function s5() { back(); sleep(1500); }
function s6() {
    let e = text("去抢购").findOne(2000);
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
    goHome();
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1.2");
}
main();