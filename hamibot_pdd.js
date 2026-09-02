auto.waitFor();
console.show();
console.log("pdd start v1");
function swipeEdgeUp(t,i){t=t||5;i=i||2000;for(let n=0;n<t;n++){swipe(1150,1400,1150,700,600);sleep(i);}}
function swipeToTop(){swipe(600,700,600,1400,600);sleep(1000);}
function s1(){let f=text("省钱月卡").findOne(2000);if(f)f.click();else click(896,784);sleep(2500);back();sleep(2000);}
function s2(){let e=text("百亿补贴").findOne(2000);if(e)e.click();else click(136,1470);sleep(3000);}
function s3(){let e=text("会员").findOne(2000);if(e)e.click();else click(1130,165);sleep(2500);}
function s4(){let e=text("打卡").findOne(2000);if(e)e.click();else click(385,1180);sleep(2000);}
function s5(){back();sleep(1500);}
function s6(){let e=text("去抢购").findOne(2000);if(e)e.click();else click(640,770);sleep(3000);}
function s7(){let els=text("立即领取").find();if(els&&els.length>0)els[0].click();else click(180,860);sleep(2000);}
function s8(){let l=text("立即点亮").findOne(1500);if(l){l.click();sleep(2000);let g=text("去看看").findOne(3000)||textContains("去看看").findOne(2000);if(g)g.click();else click(640,1360);sleep(2500);swipeEdgeUp(5,2000);let tip=textContains("还剩").findOne(1000);if(tip){swipe(1150,1400,1150,700,600);sleep(2500);}else{swipe(1150,1400,1150,700,600);sleep(2000);}swipeToTop();}else{swipeToTop();}}
function main(){sleep(1500);s1();s2();s3();s4();s5();s6();s7();s8();toast("done");}
main();
