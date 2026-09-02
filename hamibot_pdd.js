auto.waitFor();
console.show();
console.log("pdd v1.6 - 月卡广域匹配+比例坐标兜底");

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
        try { launch("com.xunmeng.pinduoduo"); } catch(e) {}
        try { app.launchApp("拼多多"); } catch(e) {}
        try { app.launchPackage("com.xunmeng.pinduoduo"); } catch(e) {}
        sleep(4000);
    }
    sleep(800);
}
function isHome() {
    return textContains("省钱月卡").exists() || textContains("月卡").exists();
}
function goHome() {
    console.log("goHome...");
    for (let i = 0; i < 8; i++) {
        if (isHome()) { console.log("已在首页"); swipeToTop(); sleep(600); return true; }
        let homeTab = text("首页").findOne(300) || desc("首页").findOne(300);
        if (homeTab) { homeTab.click(); sleep(1800); if (isHome()) { swipeToTop(); return true; } }
        console.log("back " + (i+1) + "/8"); back(); sleep(1100);
    }
    if (isHome()) { swipeToTop(); return true; }
    let w=device.width,h=device.height; click(w*0.12,h*0.93); sleep(1800);
    return isHome();
}

function findMonthCard() {
    // 广域匹配：按优先级试
    let cands = [
        () => text("省钱月卡").findOne(500),
        () => desc("省钱月卡").findOne(400),
        () => textContains("省钱月卡").findOne(400),
        () => descContains("省钱月卡").findOne(400),
        () => textContains("月卡").findOne(400),
        () => descContains("月卡").findOne(400),
        () => textMatches(/.*月卡.*/).findOne(400),
    ];
    for (let f of cands) {
        let e = f();
        if (e) return e;
    }
    return null;
}

function s1() {
    console.log("=== s1 省钱月卡 ===");
    if (!isInPdd()) { console.log("不在拼多多跳过"); return; }
    if (!isHome()) { console.log("不在首页 goHome"); goHome(); }
    // 打印当前可见含月/卡的文本用于排错
    try {
        let all = textContains("月").find();
        console.log("含月文本数: " + (all?all.length:0));
        if (all) for(let i=0;i<Math.min(5,all.length);i++) console.log("  - "+all[i].text());
    } catch(e) { console.log("遍历含月文本异常 "+e); }

    let found = null;
    for (let k=0;k<4;k++) {
        found = findMonthCard();
        if (found) { console.log("找到月卡 k="+k+" text="+found.text()); break; }
        console.log("未找到 月卡，下滑 "+(k+1)+"/4");
        swipe(600, 1300, 600, 650, 600); sleep(1200);
    }
    let w=device.width, h=device.height;
    console.log("屏幕 "+w+"x"+h+" 当前包 "+currentPackage());
    if (found) {
        console.log("点击文本月卡 bounds="+found.bounds());
        found.click(); sleep(2600);
        back(); sleep(1800);
        console.log("s1 完成已back");
    } else {
        console.log("4次均未找到，比例坐标兜底");
        swipeToTop(); sleep(700);
        // 比例兜底：原始 896,784 在 1080x2400 约 0.83,0.327；用比例兼容不同分辨率
        // 同时保留绝对坐标双击
        let x1 = Math.round(w*0.83), y1 = Math.round(h*0.285);
        console.log("点击比例坐标 "+x1+","+y1+" (回退绝对 896,784)");
        click(x1, y1); sleep(800);
        // 若比例点未进，再试绝对坐标
        if (!textContains("点亮").exists() && !textContains("月卡").exists()) {
            console.log("比例点击后未进月卡，补绝对坐标 896,784");
            click(896, 784);
        }
        sleep(2500); back(); sleep(1800);
        console.log("s1 坐标兜底完成");
    }
}
function s2() {
    console.log("=== s2 百亿补贴 ===");
    let e = text("百亿补贴").findOne(1200) || desc("百亿补贴").findOne(600) || textContains("百亿补贴").findOne(600);
    if (e) { console.log("点击 百亿补贴"); e.click(); }
    else { let w=device.width,h=device.height; let x=Math.round(w*0.126),y=Math.round(h*0.53); console.log("兜底 "+x+","+y); click(x,y); }
    sleep(3000);
}
function s3() {
    console.log("=== s3 会员 ===");
    let e = text("会员").findOne(1200) || desc("会员").findOne(600);
    if (e) e.click(); else click(1130,165);
    sleep(2500);
}
function s4() {
    console.log("=== s4 打卡 ===");
    let e = text("打卡").findOne(1200) || desc("打卡").findOne(600);
    if (e) e.click(); else click(385,1180);
    sleep(2000);
}
function s5(){ console.log("=== s5 back ==="); back(); sleep(1500); }
function s6(){
    console.log("=== s6 去抢购 ===");
    let e=text("去抢购").findOne(1200);
    if(e) e.click(); else click(640,770);
    sleep(3000);
}
function s7(){
    console.log("=== s7 立即领取 ===");
    let els=text("立即领取").find();
    if(els&&els.length>0) els[0].click(); else click(180,860);
    sleep(2000);
}
function s8(){
    console.log("=== s8 立即点亮/滑动 ===");
    let light=text("立即点亮").findOne(1200);
    if(light){ light.click(); sleep(2000);
        let go=text("去看看").findOne(2000)||textContains("去看看").findOne(800);
        if(go) go.click(); else click(640,1360);
        sleep(2500); swipeEdgeUp(5,2000);
        let tip=textContains("还剩").findOne(800);
        if(tip){ swipe(1150,1400,1150,700,600); sleep(2500); }
        swipeToTop();
    } else { swipeToTop(); }
}
function main(){
    sleep(800); ensurePdd(); goHome(); s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("v1.6完成");
}
main();