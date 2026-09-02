auto.waitFor();
console.show();
console.log("pdd v1.4 - 严格首页判定修复百亿消费券误进");
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
        console.log("已在拼多多");
    }
    sleep(800);
}

function isHome() {
    // 严格：只有首页才有 省钱月卡，百亿补贴在频道页也有，不能作为首页标志
    return text("省钱月卡").exists() || textContains("省钱月卡").exists();
}

function goHome() {
    console.log("goHome: 强制回首页 (严格判定 省钱月卡)...");
    for (let i = 0; i < 8; i++) {
        if (isHome()) {
            console.log("已回到首页，结束 back");
            sleep(800);
            return true;
        }
        // 尝试点底部 首页 tab
        let homeTab = text("首页").findOne(300) || desc("首页").findOne(300);
        if (homeTab) {
            console.log("发现 首页 tab，点击");
            homeTab.click(); sleep(1800);
            if (isHome()) return true;
        }
        console.log("back " + (i+1) + "/8");
        back(); sleep(1100);
    }
    // 兜底坐标
    if (isHome()) return true;
    console.log("兜底坐标点击首页");
    let w = device.width, h = device.height;
    click(w * 0.12, h * 0.93); sleep(1800);
    if (isHome()) return true;
    // 最后再 back 一次防止卡在频道页
    console.log("兜底后仍不在首页，再back");
    back(); sleep(1200);
    console.log("goHome 结束 isHome=" + isHome());
    return isHome();
}

// 1 省钱月卡 896,784 -> 立即返回
function s1() {
    if (!isInPdd()) { console.log("s1 跳过：不在拼多多"); return; }
    if (!isHome()) {
        console.log("s1 不在首页，先 goHome");
        goHome();
    }
    let f = text("省钱月卡").findOne(1000) || desc("省钱月卡").findOne(500) || textContains("省钱月卡").findOne(500);
    if (f) { console.log("点击 省钱月卡"); f.click(); }
    else {
        console.log("文本未找到，坐标兜底 896,784");
        if (isInPdd()) click(896, 784);
    }
    sleep(2500); back(); sleep(1800);
}
// 2 百亿补贴 136,1470
function s2() {
    // s2 必须从首页进，若已在频道页先回首页再进
    if (!isHome()) { console.log("s2 不在首页，先 goHome 再进百亿补贴"); goHome(); }
    let e = text("百亿补贴").findOne(1500) || desc("百亿补贴").findOne(500);
    if (e) { console.log("点击 百亿补贴"); e.click(); }
    else if (isInPdd()) { console.log("百亿补贴文本未找到，坐标 136,1470"); click(136, 1470); }
    sleep(3000);
}
// 3 会员 1130,165
function s3() {
    let e = text("会员").findOne(1500) || desc("会员").findOne(500);
    if (e) { console.log("点击 会员"); e.click(); }
    else if (isInPdd()) click(1130, 165);
    sleep(2500);
}
// 4 打卡 385,1180
function s4() {
    let e = text("打卡").findOne(1500) || desc("打卡").findOne(500);
    if (e) { console.log("点击 打卡"); e.click(); }
    else if (isInPdd()) click(385, 1180);
    sleep(2000);
}
function s5() { console.log("s5 back"); back(); sleep(1500); }
function s6() {
    let e = text("去抢购").findOne(1500);
    if (e) { console.log("点击 去抢购"); e.click(); }
    else if (isInPdd()) click(640, 770);
    sleep(3000);
}
function s7() {
    let els = text("立即领取").find();
    if (els && els.length > 0) { console.log("点击 立即领取 1/"+els.length); els[0].click(); }
    else if (isInPdd()) click(180, 860);
    sleep(2000);
}
function s8() {
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
    // 关键：s1执行后若已正确回到首页，s2才会从首页正确进入百亿补贴
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1.4");
}
main();