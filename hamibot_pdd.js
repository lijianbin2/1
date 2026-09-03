auto.waitFor();
console.show();
console.log("pdd v1.18 - MCP边看边改 推荐tab强制+省钱月卡896,750+百亿banner640,1450");
function tapShell(x,y){ try{ shell("input tap "+x+" "+y, true); }catch(e){} try{ click(x,y);}catch(e){} }
function pressBack(){ try{ shell("input keyevent 4", true); }catch(e){} }
function hideConsoleSoon(){ try{ console.hide(); }catch(e){} sleep(800); }
function showConsoleSoon(){ try{ console.show(); }catch(e){} sleep(300); }
function swipeEdgeUp(t, interval) { t=t||5; interval=interval||2000; for(let n=0;n<t;n++){ swipe(1150,1400,1150,700,600); sleep(interval);} }
function swipeToTop(){ for(let i=0;i<2;i++){ swipe(600,700,600,1400,600); sleep(900);} sleep(300); }
function isInPdd(){ return currentPackage()==="com.xunmeng.pinduoduo"; }
function isHome(){
    let hasHome = text("首页").exists()||desc("首页").exists();
    let hasMe = text("个人中心").exists()||desc("个人中心").exists();
    if(hasHome && hasMe && isInPdd()){
        if(textContains("共200元券").exists()) return false;
        return true;
    }
    return false;
}
function isCommodityPage(){
    return text("加入购物车").exists() || textContains("立即购买").exists() || text("收藏").exists() || descContains("购物车").exists();
}
function clickViaParent(selectorText){
    let node=text(selectorText).findOne(800)||desc(selectorText).findOne(500)||textContains(selectorText).findOne(500)||descContains(selectorText).findOne(500);
    if(!node){ console.log("clickViaParent 未找到 "+selectorText); return false; }
    console.log("找到 "+selectorText+" text="+node.text()+" desc="+node.desc()+" bounds="+node.bounds()+" clickable="+node.clickable());
    let cur=node;
    for(let i=0;i<5;i++){
        if(cur.clickable()){ console.log("点击可点击节点层级"+i+" "+cur.bounds()); try{cur.click();}catch(e){} sleep(200);
            try{ let b=cur.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){}
            return true; 
        }
        let p=cur.parent(); if(!p) break; cur=p;
    }
    console.log("未找到可点击父容器，尝试直接点原节点 + bounds中心兜底");
    let b=node.bounds();
    try{ node.click(); }catch(e){}
    sleep(300);
    try{ click(b.centerX(), b.centerY()); }catch(e){}
    try{ shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){ console.log("shell tap失败 "+e); }
    try{ let pb=cur.bounds(); shell("input tap "+pb.centerX()+" "+pb.centerY(), true);}catch(e){}
    return true;
}
function clickRedBlockByConsumption(){
    let cands=textContains("消费券").find();
    if(cands && cands.length>0){
        for(let i=0;i<cands.length;i++){
            let nd=cands[i]; let txt=nd.text()||""; let b=nd.bounds(); let cy=b.centerY();
            if(txt.indexOf("开学")>=0) continue;
            if(cy>2500) continue;
            if(txt.indexOf("消费券")<0) continue;
            console.log("红块候选 "+txt+" "+b+" cy="+cy);
            let cur=nd;
            for(let j=0;j<5;j++){
                if(cur.clickable()){
                    console.log("红块可点击祖先层级"+j+" "+cur.bounds());
                    try{ cur.click(); }catch(e){}
                    sleep(200);
                    try{ let bb=cur.bounds(); shell("input tap "+bb.centerX()+" "+bb.centerY(), true); }catch(e){}
                    return true;
                }
                let p=cur.parent(); if(!p) break; cur=p;
            }
            console.log("红块无clickable祖先，bounds兜底 "+b);
            try{ nd.click(); }catch(e){}
            sleep(200);
            try{ click(b.centerX(), b.centerY()); }catch(e){}
            try{ shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){}
            try{ let pb=cur.bounds(); shell("input tap "+pb.centerX()+" "+pb.centerY(), true); }catch(e){}
            return true;
        }
    }
    return false;
}
function ensurePdd(){
    let pkg=currentPackage();
    console.log("当前包: "+pkg+" 尺寸 "+device.width+"x"+device.height);
    if(pkg!=="com.xunmeng.pinduoduo"){
        console.log("拉起拼多多 com.xunmeng.pinduoduo ...");
        try{ shell("am start -n com.xunmeng.pinduoduo/com.xunmeng.pinduoduo.ui.activity.MainFrameActivity", true);}catch(e){
            try{ launch("com.xunmeng.pinduoduo"); }catch(e2){ console.log("launch失败 "+e2); }
        }
        sleep(4500);
        pkg=currentPackage();
        console.log("拉起后包: "+pkg);
        if(pkg!=="com.xunmeng.pinduoduo"){
            console.log("再次尝试 monkey");
            try{ shell("monkey -p com.xunmeng.pinduoduo -c android.intent.category.LAUNCHER 1", true);}catch(e){}
            sleep(4000);
            pkg=currentPackage();
            console.log("monkey后包: "+pkg);
        }
        if(pkg!=="com.xunmeng.pinduoduo"){
            console.log("再次尝试 launch");
            try{ launch("com.xunmeng.pinduoduo"); }catch(e){}
            sleep(3500);
        }
        for(let k=0;k<6;k++){
            pkg=currentPackage();
            console.log("轮询 "+k+" 包:"+pkg+" inPdd="+isInPdd());
            if(pkg==="com.xunmeng.pinduoduo") break;
            sleep(1500);
        }
    }
    try{ shell("svc power stayon true", true); shell("input keyevent 224", true); }catch(e){}
    sleep(800);
}
function goHome(){
    console.log("goHome 开始 isHome="+isHome()+" pkg="+currentPackage()+" isCommodity="+isCommodityPage());
    try{ shell("svc power stayon true", true); shell("input keyevent 224", true); }catch(e){}
    hideConsoleSoon();
    for(let i=0;i<10;i++){
        if(isHome()){ console.log("已在首页"); try{ tapShell(30,380); sleep(900); }catch(e){} showConsoleSoon(); swipeToTop(); sleep(500); return true; } // v1.18
        if(isCommodityPage()){
            console.log("检测到商品页 优先back "+(i+1)+"/10");
            pressBack(); sleep(1500);
            if(isHome()){ swipeToTop(); showConsoleSoon(); return true; }
            continue;
        }
        let tab=text("首页").findOne(500)||desc("首页").findOne(500);
        if(tab){ console.log("点 首页tab "+tab.bounds()); try{tab.click();}catch(e){} 
            try{ let b=tab.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){}
            sleep(1800); if(isHome()){ swipeToTop(); showConsoleSoon(); return true; } 
            if(isCommodityPage()){ console.log("点tab后进商品页 回退"); pressBack(); sleep(1300); continue; }
        }
        console.log("back "+(i+1)+"/10");
        pressBack(); sleep(1300);
        if(isHome()){ swipeToTop(); showConsoleSoon(); return true; }
    }
    if(isHome()){ swipeToTop(); showConsoleSoon(); return true; }
    let w=device.width,h=device.height;
    console.log("兜底点首页 "+Math.round(w*0.12)+","+Math.round(h*0.93));
    try{ click(w*0.12,h*0.93); }catch(e){}
    try{ shell("input tap "+Math.round(w*0.12)+" "+Math.round(h*0.93), true);}catch(e){}
    sleep(1800);
    try{ tapShell(128,2640); sleep(700); tapShell(30,380); sleep(1000);}catch(e){} if(!isHome()){ console.log("goHome后仍不在首页，再back"); pressBack(); sleep(1300); }
    showConsoleSoon();
    return isHome();
}
function s1(){
    console.log("=== s1 省钱月卡 直点优先防误触 ===");
    if(!isInPdd()){ console.log("不在pdd，跳过s1"); return; }
    if(!isHome()) goHome();
    hideConsoleSoon();
    swipeToTop(); sleep(600);
    let ptsDirect=[[896,750],[896,784],[640,650],[895,766],[640,520],[1062,790]]; // v1.18
    for(let pt of ptsDirect){
        console.log("s1 直点 "+pt[0]+","+pt[1]);
        tapShell(pt[0],pt[1]);
        sleep(600);
        try{ shell("input tap "+pt[0]+" "+pt[1], true);}catch(e){}
        sleep(1600);
        if(!isHome()){
            if(isCommodityPage()){
                console.log("s1 误进商品页 回退继续 "+pt);
                pressBack(); sleep(1800);
                if(!isHome()){ pressBack(); sleep(1200); goHome(); }
                else { swipeToTop(); sleep(400); }
                continue;
            }
            console.log("s1 直点 "+pt+" 已离开首页 成功");
            sleep(1200);
            pressBack(); sleep(2000);
            if(!isHome()){ pressBack(); sleep(1500); if(!isHome()) goHome(); }
            swipeToTop(); sleep(500);
            console.log("s1直点成功结束 isHome="+isHome());
            showConsoleSoon();
            return;
        }
        if(textContains("月卡").exists() && !textContains("省钱月卡").exists()){
            console.log("s1 可能已进入月卡内页");
            pressBack(); sleep(2000); showConsoleSoon(); return;
        }
    }
    let ok=false;
    for(let k=0;k<4;k++){
        let n=text("省钱月卡").findOne(700)||desc("省钱月卡").findOne(500);
        if(n){
            console.log("s1 精准找到省钱月卡 k="+k+" "+n.bounds()+" clickable="+n.clickable());
            let cur=n;
            for(let i=0;i<5;i++){
                if(cur.clickable()){ try{cur.click();}catch(e){} try{ let b=cur.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){} ok=true; break; }
                let p=cur.parent(); if(!p) break; cur=p;
            }
            if(!ok){ try{n.click();}catch(e){} try{ let b=n.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){} ok=true; }
            sleep(2800);
            if(!isHome()) break;
        }
        if(ok && !isHome()) break;
        console.log("省钱月卡未找到，下滑 "+(k+1)+"/4");
        swipe(600,1350,600,750,600); sleep(1300);
    }
    sleep(800);
    if(isHome()){
        console.log("仍在首页，二次坐标兜底 isHome="+isHome()+" ok="+ok);
        let w=device.width,h=device.height;
        let pts2=[[640,427],[640,520],[896,784],[895,766]];
        for(let pt of pts2){
            console.log("s1 二次坐标 "+pt[0]+","+pt[1]);
            tapShell(pt[0],pt[1]); sleep(1800);
            if(!isHome()){
                if(isCommodityPage()){
                    console.log("二次误进商品页回退");
                    pressBack(); sleep(1500); if(!isHome()) goHome();
                    continue;
                }
                console.log("s1 二次坐标 "+pt+" 成功"); break;
            }
        }
        if(isHome()){
            try{ let n=text("省钱月卡").findOne(500)||descContains("省钱月卡").findOne(500); if(n){ let bb=n.bounds(); console.log("最后bounds中心 "+bb.centerX()+","+bb.centerY()); shell("input tap "+bb.centerX()+" "+bb.centerY(), true); sleep(2200); } }catch(e){}
        }
    } else { console.log("已离开首页，说明已进入月卡页 s1成功"); }
    sleep(1000);
    console.log("s1后 back 当前isHome="+isHome()+" 当前包="+currentPackage()+" isCommodity="+isCommodityPage());
    showConsoleSoon();
    if(isCommodityPage()){ console.log("s1后在商品页 回退"); pressBack(); sleep(1500); if(!isHome()) goHome(); }
    else { pressBack(); sleep(2000); if(!isHome()){ console.log("back后不在首页，再back"); pressBack(); sleep(1500); if(!isHome()) goHome(); } }
    swipeToTop(); sleep(500); console.log("s1结束 isHome="+isHome());
}
function s2(){
    console.log("=== s2 百亿补贴 ===");
    hideConsoleSoon();
    if(!isHome()) goHome();
    swipeToTop(); sleep(600);
    try{ tapShell(640,1450); sleep(2500); if(!isHome() && !isCommodityPage()){ console.log("s2 banner直点成功"); showConsoleSoon(); return; } if(isCommodityPage()){ console.log("s2 banner误进商品回退"); pressBack(); sleep(1500); if(!isHome()) goHome(); } else { if(!isHome()){ pressBack(); sleep(1500); if(!isHome()) goHome(); swipeToTop(); sleep(600); } } }catch(e){}
    let ok=false;
    for(let k=0;k<6;k++){
        if(clickViaParent("百亿补贴")){ ok=true; console.log("百亿补贴点击 k="+k); sleep(3000); break; }
        let n=textContains("百亿").findOne(400);
        if(n){ console.log("百亿模糊 "+n.text()+" "+n.bounds()); try{n.click();}catch(e){} try{shell("input tap "+n.bounds().centerX()+" "+n.bounds().centerY(), true);}catch(e){} ok=true; sleep(3000); break; }
        console.log("百亿补贴未找到，下滑 "+(k+1)+"/6");
        swipe(600,1350,600,750,600); sleep(1300);
    }
    if(!ok){
        let w=device.width,h=device.height;
        let x=640,y=1450; // v1.18
        console.log("百亿兜底 "+x+","+y); tapShell(x,y); sleep(3000);
    }
    showConsoleSoon();
    if(isCommodityPage()){ console.log("s2后误进商品页 回退"); pressBack(); sleep(1500); if(!isHome()) goHome(); }
}
function s3(){
    console.log("=== s3 会员 1130,165 ==="); hideConsoleSoon();
    let ok=clickViaParent("会员");
    if(!ok){ console.log("会员文本未找到，坐标兜底"); tapShell(1130,165); }
    sleep(2800); showConsoleSoon();
}
function s4(){
    console.log("=== s4 打卡 385,1180 ==="); hideConsoleSoon(); swipeToTop(); sleep(500);
    let d=text("打卡").findOne(800)||desc("打卡").findOne(500)||textContains("打卡送积分").findOne(500);
    if(d){
        let b=d.bounds(); console.log("s4 打卡 bounds "+b);
        try{ shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){}
        sleep(300);
        try{ click(b.centerX(), b.centerY()); }catch(e){}
        sleep(400);
        try{ shell("input tap 385 1180", true);}catch(e){}
        sleep(3000);
    } else if(clickViaParent("打卡")){ sleep(3000); } else { console.log("打卡未找到，坐标兜底 385,1180"); tapShell(385,1180); sleep(2500); }
    showConsoleSoon();
}
function s5(){ console.log("=== s5 back ==="); hideConsoleSoon(); pressBack(); sleep(1700); showConsoleSoon(); }
function s6(){
    console.log("=== s6 百亿消费券/去抢购 红块整体可进 过滤开学 cy<=2500 ===");
    hideConsoleSoon();
    if(!isHome()) goHome(); swipeToTop(); sleep(600);
    for(let k=0;k<5;k++){
        if(clickViaParent("去抢购")){ console.log("s6 去抢购点击 k="+k); sleep(3200); if(isCommodityPage()){ console.log("s6去抢购后进商品页回退"); pressBack(); sleep(1500); continue; } showConsoleSoon(); return; }
        if(text("百亿消费券").exists()){
            let n=text("百亿消费券").findOne(300);
            if(n && n.bounds().centerY()<=2500 && n.text().indexOf("开学")<0){
                console.log("s6 精准百亿消费券 "+n.bounds());
                let cur=n; let clicked=false;
                for(let i=0;i<5;i++){ if(cur.clickable()){ try{cur.click();}catch(e){} clicked=true; try{ let b=cur.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){} break; } let pp=cur.parent(); if(!pp) break; cur=pp; }
                if(!clicked) try{n.click();}catch(e){}
                try{ let b=n.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){}
                sleep(3200);
                if(isCommodityPage()){ console.log("s6精准后进商品页回退"); pressBack(); sleep(1500); continue; }
                showConsoleSoon(); return;
            }
        }
        if(clickRedBlockByConsumption()){ console.log("s6 红块整体点击成功 k="+k); sleep(3200); if(isCommodityPage()){ console.log("s6红块后进商品页回退"); pressBack(); sleep(1500); continue; } showConsoleSoon(); return; }
        if(clickViaParent("百亿消费券")){ console.log("s6 百亿消费券模糊点击 k="+k); sleep(3200); if(isCommodityPage()){ pressBack(); sleep(1500); continue; } showConsoleSoon(); return; }
        console.log("s6 未找到，下滑 "+(k+1)+"/5");
        swipe(600,1350,600,750,600); sleep(1300);
    }
    let n2=textContains("消费券").findOne(800);
    if(n2 && n2.text().indexOf("开学")<0 && n2.bounds().centerY()<=2500){
        console.log("s6 兜底文本 "+n2.text()+" "+n2.bounds());
        let cur=n2; let clicked=false;
        for(let i=0;i<5;i++){ if(cur.clickable()){ try{cur.click();}catch(e){} clicked=true; try{ let b=cur.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(e){} break; } let pp=cur.parent(); if(!pp) break; cur=pp; }
        if(!clicked) try{n2.click();}catch(e){}
        try{ let b=n2.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true); }catch(e){}
        sleep(3200);
        if(isCommodityPage()){ console.log("s6兜底后商品页回退"); pressBack(); sleep(1500); goHome(); }
        showConsoleSoon(); return;
    }
    console.log("s6 文本均未找到，坐标兜底红块 isCommodity="+isCommodityPage());
    let pts=[[640,750],[640,850],[900,700],[640,770],[640,650],[700,900],[500,800]];
    for(let pt of pts){
        console.log("尝试坐标 "+pt[0]+","+pt[1]);
        tapShell(pt[0],pt[1]); sleep(1000);
        if(isCommodityPage()){ console.log("坐标误进商品页 回退"); pressBack(); sleep(1200); continue; }
        if(textContains("共200元券").exists() || text("立即领取").exists() || (textContains("消费券").exists() && !isHome())){ console.log("坐标 "+pt+" 似乎已进入"); break; }
        if(text("消费券").exists()){ console.log("检测到消费券标题，进入成功"); break; }
    }
    sleep(2000); showConsoleSoon();
}
function s7(){
    console.log("=== s7 立即领取 ==="); hideConsoleSoon();
    let els=text("立即领取").find();
    if(els&&els.length>0){ 
        console.log("领取数 "+els.length+" 尝试全部点击");
        for(let i=0;i<Math.min(3, els.length); i++){
            let e=els[i]; console.log("领取 "+i+" "+e.bounds());
            try{ let p=e.parent(); if(p && p.clickable()) p.click(); else e.click(); }catch(err){}
            try{ let b=e.bounds(); shell("input tap "+b.centerX()+" "+b.centerY(), true);}catch(err){}
            sleep(1200);
        }
    } else { 
        console.log("未找到立即领取文本，坐标兜底 WebView卡片");
        let pts=[[227,1048],[640,1048],[940,1048],[180,860],[400,900],[800,900]];
        for(let pt of pts){
            console.log("s7 领取坐标 "+pt[0]+","+pt[1]);
            tapShell(pt[0],pt[1]); sleep(1000);
            if(text("立即点亮").exists()||desc("立即点亮").exists()||textContains("还剩").exists()){ console.log("检测到点亮/还剩，已触发领取"); break; }
        }
    }
    sleep(2200); showConsoleSoon();
}
function s8(){
    console.log("=== s8 立即点亮/滑动 ==="); hideConsoleSoon();
    let light=text("立即点亮").findOne(1200)||desc("立即点亮").findOne(800);
    if(light){
        console.log("发现立即点亮 "+light.bounds());
        let cur=light; for(let i=0;i<4;i++){ if(cur.clickable()){try{cur.click();}catch(e){} try{shell("input tap "+cur.bounds().centerX()+" "+cur.bounds().centerY(), true);}catch(e){} break;} cur=cur.parent(); if(!cur) break; }
        if(!light.clickable()) try{ light.click(); click(light.bounds().centerX(), light.bounds().centerY()); }catch(e){}
        sleep(2200);
        let go=text("去看看").findOne(2000)||textContains("去看看").findOne(800);
        if(go){ 
            console.log("去看看 "+go.bounds());
            let c=go; for(let i=0;i<3;i++){ if(c.clickable()){try{c.click();}catch(e){} try{shell("input tap "+c.bounds().centerX()+" "+c.bounds().centerY(), true);}catch(e){} break;} c=c.parent(); if(!c) break; }
            if(!go.clickable()) try{go.click();}catch(e){}
        } else { console.log("未找到去看看，坐标 640,1360"); tapShell(640,1360); }
        sleep(2800); swipeEdgeUp(5,2000);
        let tip=textContains("还剩").findOne(800);
        if(tip){ console.log("发现还剩提示 "+tip.text()+" 补滑一次"); swipe(1150,1400,1150,700,600); sleep(2500); }
        swipeToTop();
    } else { console.log("无点亮，直接回顶部"); swipeToTop(); }
    showConsoleSoon();
}
function main(){
    console.log("=== main 开始 v1.18 ==="); sleep(800); ensurePdd(); 
    let inPdd=isInPdd(); console.log("ensure后 inPdd="+inPdd+" isHome="+isHome()+" isCommodity="+isCommodityPage());
    if(!inPdd){ console.log("不在pdd，终止"); toast("不在拼多多"); return; }
    goHome(); console.log("goHome后 isHome="+isHome());
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("v1.18 完成"); console.log("=== all done v1.18 ===");
}
main();