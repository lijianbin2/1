auto.waitFor();
console.show();
console.log("pdd v1.5 - s1滚动查找省钱月卡修复滑动进错页");
// 边缘滑动防误点商品，底部→中部 (用于s8的10秒任务)
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
        console.log("已在拼多多");
    }
    sleep(800);
}

function isHome() {
    return text("省钱月卡").exists() || textContains("省钱月卡").exists();
}

function goHome() {
    console.log("goHome: 强制回首页 (严格 省钱月卡)...");
    for (let i = 0; i < 8; i++) {
        if (isHome()) {
            console.log("已回到首页，结束 back，置顶一下");
            // 确保在顶部，省钱月卡在首屏可见
            swipeToTop(); sleep(800);
            return true;
        }
        let homeTab = text("首页").findOne(300) || desc("首页").findOne(300);
        if (homeTab) {
            console.log("发现 首页 tab，点击");
            homeTab.click(); sleep(1800);
            if (isHome()) { swipeToTop(); sleep(600); return true; }
        }
        console.log("back " + (i+1) + "/8");
        back(); sleep(1100);
    }
    if (isHome()) { swipeToTop(); return true; }
    console.log("兜底坐标点击首页");
    let w = device.width, h = device.height;
    click(w * 0.12, h * 0.93); sleep(1800);
    if (isHome()) { swipeToTop(); return true; }
    console.log("兜底后仍不在首页，再back");
    back(); sleep(1200);
    console.log("goHome 结束 isHome=" + isHome());
    return isHome();
}

// 1 省钱月卡 896,784 -> 立即返回 (增加滚动查找，解决首页首屏外找不到)
function s1() {
    console.log("=== s1 省钱月卡 ===");
    if (!isInPdd()) { console.log("s1 跳过：不在拼多多"); return; }
    if (!isHome()) {
        console.log("s1 不在首页，先 goHome");
        goHome();
    }
    // 滚动查找最多3次，省钱月卡可能在首页下滑后才出现
    let found = null;
    for (let k = 0; k < 3; k++) {
        found = text("省钱月卡").findOne(800) || desc("省钱月卡").findOne(500) || textContains("省钱月卡").findOne(500);
        if (found) { console.log("找到 省钱月卡 第"+(k+1)+"次"); break; }
        console.log("未找到 省钱月卡，下滑查找 "+(k+1)+"/3");
        swipe(600, 1200, 600, 600, 600); sleep(1200);
    }
    if (found) {
        console.log("点击 省钱月卡");
        found.click();
        sleep(2500);
        // 验证是否真的进入月卡页 (特征：立即点亮/去看看/月卡)
        let entered = text("立即点亮").findOne(1200) || textContains("月卡").findOne(800);
        if (!entered) console.log("警告：点击后未检测到月卡页，可能坐标偏差");
        back(); sleep(1800);
    } else {
        console.log("滚动3次仍未找到文本，坐标兜底 896,784");
        // 先回到顶部再点坐标，避免滚到了底部点错
        swipeToTop(); sleep(800);
        if (isInPdd()) click(896, 784);
        sleep(2500); back(); sleep(1800);
    }
}
// 2 百亿补贴 136,1470
function s2() {
    console.log("=== s2 百亿补贴 ===");
    if (!isHome()) { console.log("s2 不在首页，先 goHome 再进"); goHome(); }
    let e = text("百亿补贴").findOne(1500) || desc("百亿补贴").findOne(500);
    if (e) { console.log("点击 百亿补贴"); e.click(); }
    else if (isInPdd()) { console.log("百亿补贴文本未找到，坐标 136,1470"); click(136, 1470); }
    sleep(3000);
}
// 3 会员 1130,165
function s3() {
    console.log("=== s3 会员 ===");
    let e = text("会员").findOne(1500) || desc("会员").findOne(500);
    if (e) { console.log("点击 会员"); e.click(); }
    else if (isInPdd()) click(1130, 165);
    sleep(2500);
}
// 4 打卡 385,1180
function s4() {
    console.log("=== s4 打卡 ===");
    let e = text("打卡").findOne(1500) || desc("打卡").findOne(500);
    if (e) { console.log("点击 打卡"); e.click(); }
    else if (isInPdd()) click(385, 1180);
    sleep(2000);
}
function s5() { console.log("=== s5 back ==="); back(); sleep(1500); }
function s6() {
    console.log("=== s6 去抢购 ===");
    let e = text("去抢购").findOne(1500);
    if (e) { console.log("点击 去抢购"); e.click(); }
    else if (isInPdd()) click(640, 770);
    sleep(3000);
}
function s7() {
    console.log("=== s7 立即领取 ===");
    let els = text("立即领取").find();
    if (els && els.length > 0) { console.log("点击 立即领取 1/"+els.length); els[0].click(); }
    else if (isInPdd()) click(180, 860);
    sleep(2000);
}
function s8() {
    console.log("=== s8 立即点亮/滑动 ===");
    let light = text("立即点亮").findOne(1500);
    if (light) {
        console.log("发现 立即点亮");
        light.click(); sleep(2000);
        let go = text("去看看").findOne(3000) || textContains("去看看").findOne(1000);
        if (go) go.click(); else if (isInPdd()) click(640, 1360);
        sleep(2500);
        swipeEdgeUp(5, 2000);
        let tip = textContains("还剩").findOne(1000);
        if (tip) { swipe(1150, 1400, 1150, 700, 600); sleep(2500); }
        swipeToTop();
    } else {
        console.log("无 立即点亮，直接回顶部");
        swipeToTop();
    }
}
function main() {
    sleep(800);
    ensurePdd();
    goHome();
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1.5");
}
main();