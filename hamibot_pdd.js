auto.waitFor();
console.show();
console.log("pdd v1.7 - 父容器点击修复 (MCP联调版)");

function swipeEdgeUp(t, interval) {
    t = t || 5; interval = interval || 2000;
    for (let n = 0; n < t; n++) { swipe(1150, 1400, 1150, 700, 600); sleep(interval); }
}
function swipeToTop() { swipe(600, 700, 600, 1400, 600); sleep(1000); }
function isInPdd() { return currentPackage() === "com.xunmeng.pinduoduo"; }

function clickViaParent(selectorText) {
    // selectorText: 要找的文本
    let node = text(selectorText).findOne(800) || desc(selectorText).findOne(500) || textContains(selectorText).findOne(500) || descContains(selectorText).findOne(500);
    if (!node) {
        console.log("clickViaParent 未找到 "+selectorText);
        return false;
    }
    console.log("找到 "+selectorText+" text="+node.text()+" desc="+node.desc()+" bounds="+node.bounds()+" clickable="+node.clickable());
    // 向上找可点击父容器，最多4层
    let cur = node;
    for (let i=0;i<5;i++) {
        if (cur.clickable()) {
            console.log("点击可点击节点 "+cur.bounds()+" 层级 "+i);
            cur.click();
            return true;
        }
        let p = cur.parent();
        if (!p) break;
        cur = p;
    }
    // 兜底：点原节点中心（即使不可点击，Hamibot有时也能点）
    console.log("未找到可点击父容器，尝试直接点原节点");
    node.click();
    return true;
}

function ensurePdd() {
    let pkg = currentPackage();
    console.log("当前包: "+pkg+" 尺寸 "+device.width+"x"+device.height);
    if (pkg !== "com.xunmeng.pinduoduo") {
        console.log("拉起拼多多...");
        try { launch("com.xunmeng.pinduoduo"); } catch(e) {}
        try { app.launchApp("拼多多"); } catch(e) {}
        sleep(4000);
    }
    sleep(800);
}
function isHome() { return textContains("省钱月卡").exists() || descContains("省钱月卡").exists(); }

function goHome() {
    console.log("goHome 开始");
    for (let i=0;i<8;i++) {
        if (isHome()) { console.log("已在首页"); swipeToTop(); sleep(500); return true; }
        let tab = text("首页").findOne(300) || desc("首页").findOne(300);
        if (tab) { console.log("点 首页tab"); tab.click(); sleep(1800); if(isHome()){swipeToTop(); return true;} }
        console.log("back "+(i+1)+"/8"); back(); sleep(1100);
    }
    if(isHome()){swipeToTop(); return true;}
    let w=device.width,h=device.height;
    console.log("兜底点首页 "+Math.round(w*0.12)+","+Math.round(h*0.93));
    click(w*0.12,h*0.93); sleep(1500);
    return isHome();
}

function s1() {
    console.log("=== s1 省钱月卡 ===");
    if(!isInPdd()) return;
    if(!isHome()) goHome();
    // 滚动查找
    let ok=false;
    for(let k=0;k<4;k++){
        if(clickViaParent("省钱月卡")){ ok=true; break; }
        console.log("省钱月卡未找到，下滑 "+(k+1)+"/4");
        swipe(600,1300,600,650,600); sleep(1200);
    }
    if(!ok){
        console.log("4次未找到，比例兜底");
        swipeToTop(); sleep(600);
        let w=device.width,h=device.height;
        let x=Math.round(w*0.83),y=Math.round(h*0.285);
        console.log("点击比例 "+x+","+y);
        click(x,y); sleep(500);
        if(!isHome()) click(896,784); // 1280x2772绝对
    }
    sleep(2600);
    // 验证进入月卡页后立即back（按用户要求）
    console.log("s1后 back");
    back(); sleep(1800);
    console.log("s1结束 isHome="+isHome());
}
function s2(){
    console.log("=== s2 百亿补贴 ===");
    // 百亿补贴在首页的快捷入口里，可能需下滑才可见，但文本搜索应能找到
    let ok=clickViaParent("百亿补贴");
    if(!ok){
        // 尝试文本含百亿
        let n=textContains("百亿").findOne(600);
        if(n){ console.log("找到百亿文本 "+n.text()); n.parent().click(); ok=true; }
    }
    if(!ok){
        let w=device.width,h=device.height;
        // 原坐标 136,1470 在1280x2772 约 0.106,0.53
        let x=Math.round(w*0.106),y=Math.round(h*0.53);
        console.log("百亿兜底 "+x+","+y);
        click(x,y);
    }
    sleep(3000);
}
function s3(){
    console.log("=== s3 会员 1130,165 ===");
    let ok=clickViaParent("会员");
    if(!ok){ console.log("会员文本未找到，坐标兜底"); click(1130,165); }
    sleep(2500);
}
function s4(){
    console.log("=== s4 打卡 385,1180 ===");
    let ok=clickViaParent("打卡");
    if(!ok){ console.log("打卡未找到，坐标兜底"); click(385,1180); }
    sleep(2000);
}
function s5(){ console.log("=== s5 back ==="); back(); sleep(1500); }
function s6(){
    console.log("=== s6 去抢购 640,770 ===");
    let ok=clickViaParent("去抢购");
    if(!ok) click(640,770);
    sleep(3000);
}
function s7(){
    console.log("=== s7 立即领取 ===");
    let els=text("立即领取").find();
    if(els&&els.length>0){ console.log("领取数 "+els.length); els[0].parent().click(); } 
    else click(180,860);
    sleep(2000);
}
function s8(){
    console.log("=== s8 立即点亮/滑动 ===");
    let light=text("立即点亮").findOne(1200)||desc("立即点亮").findOne(800);
    if(light){
        console.log("发现立即点亮");
        // 同样找父容器
        let cur=light;
        for(let i=0;i<4;i++){ if(cur.clickable()){cur.click();break;} cur=cur.parent(); if(!cur) break; }
        if(!light.clickable()) light.click();
        sleep(2000);
        let go=text("去看看").findOne(2000)||textContains("去看看").findOne(800);
        if(go){ 
            let c=go; for(let i=0;i<3;i++){ if(c.clickable()){c.click();break;} c=c.parent(); if(!c) break; }
            if(!go.clickable()) go.click();
        } else click(640,1360);
        sleep(2500);
        swipeEdgeUp(5,2000);
        let tip=textContains("还剩").findOne(800);
        if(tip){ swipe(1150,1400,1150,700,600); sleep(2500); }
        swipeToTop();
    } else {
        console.log("无点亮，直接回顶部");
        swipeToTop();
    }
}
function main(){
    console.log("=== main 开始 ===");
    sleep(800); ensurePdd(); goHome();
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("v1.7 完成");
    console.log("=== all done ===");
}
main();