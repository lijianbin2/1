auto.waitFor();
console.show();
console.log("pdd v1.11 - MCP边看边改修复版");
function swipeEdgeUp(t, interval) { t=t||5; interval=interval||2000; for(let n=0;n<t;n++){ swipe(1150,1400,1150,700,600); sleep(interval);} }
function swipeToTop(){ swipe(600,700,600,1400,600); sleep(1200); }
function isInPdd(){ return currentPackage()==="com.xunmeng.pinduoduo"; }
function clickViaParent(selectorText){
    let node=text(selectorText).findOne(800)||desc(selectorText).findOne(500)||textContains(selectorText).findOne(500)||descContains(selectorText).findOne(500);
    if(!node){ console.log("clickViaParent 未找到 "+selectorText); return false; }
    console.log("找到 "+selectorText+" text="+node.text()+" desc="+node.desc()+" bounds="+node.bounds()+" clickable="+node.clickable());
    let cur=node;
    for(let i=0;i<5;i++){
        if(cur.clickable()){ console.log("点击可点击节点层级"+i+" "+cur.bounds()); cur.click(); return true; }
        let p=cur.parent(); if(!p) break; cur=p;
    }
    console.log("未找到可点击父容器，尝试直接点原节点 + bounds中心兜底");
    let b=node.bounds();
    try{ node.click(); }catch(e){}
    sleep(300);
    try{ click(b.centerX(), b.centerY()); }catch(e){}
    try{ shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){ console.log("shell tap失败 "+e); }
    return true;
}
function ensurePdd(){
    let pkg=currentPackage();
    console.log("当前包: "+pkg+" 尺寸 "+device.width+"x"+device.height);
    if(pkg!=="com.xunmeng.pinduoduo"){
        console.log("拉起拼多多 com.xunmeng.pinduoduo ...");
        try{ launch("com.xunmeng.pinduoduo"); }catch(e){ console.log("launch失败 "+e); }
        sleep(4500);
        pkg=currentPackage();
        console.log("拉起后包: "+pkg);
        if(pkg!=="com.xunmeng.pinduoduo"){
            console.log("再次尝试 launch");
            try{ launch("com.xunmeng.pinduoduo"); }catch(e){}
            sleep(3500);
        }
    }
    sleep(800);
}
function isHome(){ return textContains("省钱月卡").exists()||descContains("省钱月卡").exists(); }
function goHome(){
    console.log("goHome 开始 isHome="+isHome()+" pkg="+currentPackage());
    for(let i=0;i<8;i++){
        if(isHome()){ console.log("已在首页"); swipeToTop(); sleep(500); return true; }
        let tab=text("首页").findOne(300)||desc("首页").findOne(300);
        if(tab){ console.log("点 首页tab "+tab.bounds()); tab.click(); sleep(1800); if(isHome()){ swipeToTop(); return true; } }
        console.log("back "+(i+1)+"/8");
        back(); sleep(1200);
    }
    if(isHome()){ swipeToTop(); return true; }
    let w=device.width,h=device.height;
    console.log("兜底点首页 "+Math.round(w*0.12)+","+Math.round(h*0.93));
    click(w*0.12,h*0.93); sleep(1800);
    if(!isHome()){ console.log("goHome后仍不在首页，再back"); back(); sleep(1200); }
    return isHome();
}
function s1(){
    console.log("=== s1 省钱月卡 ===");
    if(!isInPdd()){ console.log("不在pdd，跳过s1"); return; }
    if(!isHome()) goHome();
    swipeToTop(); sleep(600);
    let ok=false;
    for(let k=0;k<6;k++){
        if(clickViaParent("省钱月卡")){ ok=true; console.log("省钱月卡点击尝试 k="+k); sleep(2800); break; }
        console.log("省钱月卡未找到，下滑 "+(k+1)+"/6");
        swipe(600,1300,600,650,600); sleep(1300);
    }
    sleep(1000);
    if(isHome()){
        console.log("仍在首页，重试坐标兜底 isHome=true ok="+ok);
        let w=device.width,h=device.height;
        let x=Math.round(w*0.70),y=Math.round(h*0.285);
        console.log("点击比例 "+x+","+y+" (w*0.70,h*0.285)");
        click(x,y); sleep(300);
        try{ shell("input tap "+x+" "+y, true); }catch(e){}
        sleep(2200);
        if(isHome()){
            console.log("比例点击后仍在首页，再点绝对 896,784");
            click(896,784); sleep(300);
            try{ shell("input tap 896 784", true); }catch(e){}
            sleep(2200);
            // 最后再试一次按当前实际bounds中心 shell
            try{ let n=text("省钱月卡").findOne(500); if(n){ let bb=n.bounds(); shell("input tap "+bb.centerX()+" "+bb.centerY(), true); sleep(2000); } }catch(e){}
        }
    } else {
        console.log("已离开首页，说明已进入月卡页 s1成功");
    }
    sleep(1000);
    console.log("s1后 back 当前isHome="+isHome()+" 当前包="+currentPackage());
    back(); sleep(2000);
    if(!isHome()){
        console.log("back后不在首页，再back");
        back(); sleep(1500);
        if(!isHome()) goHome();
    }
    swipeToTop(); sleep(500);
    console.log("s1结束 isHome="+isHome());
}
function s2(){
    console.log("=== s2 百亿补贴 ===");
    if(!isHome()) goHome();
    let ok=clickViaParent("百亿补贴");
    if(!ok){
        let n=textContains("百亿").findOne(600);
        if(n){ console.log("找到百亿文本 "+n.text()+" "+n.bounds()); try{ n.parent().click(); ok=true; }catch(e){ n.click(); ok=true; } }
    }
    if(!ok){
        let w=device.width,h=device.height;
        let x=Math.round(w*0.106),y=Math.round(h*0.53);
        console.log("百亿兜底 "+x+","+y);
        click(x,y);
    }
    sleep(3500);
}
function s3(){
    console.log("=== s3 会员 1130,165 ===");
    let ok=clickViaParent("会员");
    if(!ok){ console.log("会员文本未找到，坐标兜底"); click(1130,165); }
    sleep(2800);
}
function s4(){
    console.log("=== s4 打卡 385,1180 ===");
    let ok=clickViaParent("打卡");
    if(!ok){ console.log("打卡未找到，坐标兜底"); click(385,1180); }
    sleep(2200);
}
function s5(){ console.log("=== s5 back ==="); back(); sleep(1700); }
function s6(){
    console.log("=== s6 百亿消费券/去抢购 (红块整体可进) ===");
    let ok=false;
    // 1. 优先点 去抢购
    ok=clickViaParent("去抢购");
    if(ok){ console.log("s6 去抢购点击完成"); sleep(3200); return; }
    // 2. 点 百亿消费券 整体
    ok=clickViaParent("百亿消费券");
    if(ok){ console.log("s6 百亿消费券点击完成"); sleep(3200); return; }
    // 3. 消费券 模糊
    let n=textContains("消费券").findOne(800) || descContains("消费券").findOne(500);
    if(n){
        console.log("找到消费券文本 "+n.text()+" "+n.bounds()+" 尝试父容器+shell");
        let cur=n; let clicked=false;
        for(let i=0;i<4;i++){ if(cur.clickable()){ try{cur.click();}catch(e){} clicked=true; break; } let pp=cur.parent(); if(!pp) break; cur=pp; }
        if(!clicked) try{n.click();}catch(e){}
        try{ let b=n.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){}
        // 再尝试父容器中心 shell
        try{ let b2=cur.bounds(); shell("input tap "+b2.centerX()+" "+b2.centerY(), true); }catch(e){}
        sleep(3200); return;
    }
    // 4. 兜底坐标：红色方块中心区域多点尝试
    console.log("s6 文本均未找到，坐标兜底红块");
    let pts=[[640,770],[640,650],[640,850],[900,700]];
    for(let pt of pts){
        console.log("尝试坐标 "+pt[0]+","+pt[1]);
        try{ click(pt[0],pt[1]); }catch(e){}
        try{ shell("input tap "+pt[0]+" "+pt[1], true); }catch(e){}
        sleep(800);
        // 检查是否已进入领取页
        if(text("立即领取").exists() || textContains("消费券").exists()){ console.log("坐标 "+pt+" 似乎已进入"); break; }
    }
    sleep(2000);
}
function s7(){
    console.log("=== s7 立即领取 ===");
    let els=text("立即领取").find();
    if(els&&els.length>0){ console.log("领取数 "+els.length+" 尝试父容器点击"); try{ els[0].parent().click(); }catch(e){ els[0].click(); } }
    else { console.log("未找到立即领取，坐标兜底 180,860"); click(180,860); }
    sleep(2200);
}
function s8(){
    console.log("=== s8 立即点亮/滑动 ===");
    let light=text("立即点亮").findOne(1200)||desc("立即点亮").findOne(800);
    if(light){
        console.log("发现立即点亮 "+light.bounds());
        let cur=light;
        for(let i=0;i<4;i++){ if(cur.clickable()){cur.click();break;} cur=cur.parent(); if(!cur) break; }
        if(!light.clickable()) try{ light.click(); click(light.bounds().centerX(), light.bounds().centerY()); }catch(e){}
        sleep(2200);
        let go=text("去看看").findOne(2000)||textContains("去看看").findOne(800);
        if(go){ 
            console.log("去看看 "+go.bounds());
            let c=go; for(let i=0;i<3;i++){ if(c.clickable()){c.click();break;} c=c.parent(); if(!c) break; }
            if(!go.clickable()) go.click();
        } else { console.log("未找到去看看，坐标 640,1360"); click(640,1360); }
        sleep(2800);
        swipeEdgeUp(5,2000);
        let tip=textContains("还剩").findOne(800);
        if(tip){ console.log("发现还剩提示 "+tip.text()+" 补滑一次"); swipe(1150,1400,1150,700,600); sleep(2500); }
        swipeToTop();
    } else {
        console.log("无点亮，直接回顶部");
        swipeToTop();
    }
}
function main(){
    console.log("=== main 开始 v1.11 ===");
    sleep(800); ensurePdd(); 
    let inPdd=isInPdd();
    console.log("ensure后 inPdd="+inPdd+" isHome="+isHome());
    if(!inPdd){ console.log("不在pdd，终止"); toast("不在拼多多"); return; }
    goHome();
    console.log("goHome后 isHome="+isHome());
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("v1.11 完成");
    console.log("=== all done v1.11 ===");
}
main();
