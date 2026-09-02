auto.waitFor();
console.show();
console.log("pdd 省钱月卡百亿补贴会员打卡 v1");
// 边缘滑动防误点商品，底部→中部
function swipeEdgeUp(t, interval) {
    t = t || 5; interval = interval || 2000;
    for (let n = 0; n < t; n++) { swipe(1150, 1400, 1150, 700, 600); sleep(interval); }
}
function swipeToTop() { swipe(600, 700, 600, 1400, 600); sleep(1000); }

// 1 省钱月卡 896,784 -> 立即返回
function s1() {
    let f = text("省钱月卡").findOne(2000);
    if (f) f.click(); else click(896, 784);
    sleep(2500); back(); sleep(2000);
}
// 2 百亿补贴 136,1470
function s2() {
    let e = text("百亿补贴").findOne(2000);
    if (e) e.click(); else click(136, 1470);
    sleep(3000);
}
// 3 会员 1130,165
function s3() {
    let e = text("会员").findOne(2000);
    if (e) e.click(); else click(1130, 165);
    sleep(2500);
}
// 4 打卡 385,1180
function s4() {
    let e = text("打卡").findOne(2000);
    if (e) e.click(); else click(385, 1180);
    sleep(2000);
}
// 5 返回上一页
function s5() { back(); sleep(1500); }
// 6 去抢购 640,770 (百亿消费券下方)
function s6() {
    let e = text("去抢购").findOne(2000);
    if (e) e.click(); else click(640, 770);
    sleep(3000);
}
// 7 立即领取 180,860 三选一
function s7() {
    let els = text("立即领取").find();
    if (els && els.length > 0) els[0].click(); else click(180, 860);
    sleep(2000);
}
// 8 条件：立即点亮 1070,410 -> 去看看 640,1360 -> 边缘滑动10秒(5次+补2秒) -> 回顶部
function s8() {
    let light = text("立即点亮").findOne(1500);
    if (light) {
        light.click(); sleep(2000);
        let go = text("去看看").findOne(3000) || textContains("去看看").findOne(2000);
        if (go) go.click(); else click(640, 1360);
        sleep(2500);
        swipeEdgeUp(5, 2000);
        // 提示还剩2秒则补1次
        let tip = textContains("还剩").findOne(1000);
        if (tip) { swipe(1150, 1400, 1150, 700, 600); sleep(2500); }
        swipeToTop();
    } else {
        // 无点亮按钮，直接回顶部 (你撤回了返回首页，改为回顶部)
        swipeToTop();
    }
}
function main() {
    sleep(1500);
    s1(); s2(); s3(); s4(); s5(); s6(); s7(); s8();
    toast("拼多多流程完成 v1");
    // 以后扩展：在此追加 s9() s10() ...
    // function s9(){ /* 下一步 */ }
}
main();