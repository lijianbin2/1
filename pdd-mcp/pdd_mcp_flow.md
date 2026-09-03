# 拼多多 MCP 全流程 - 存档 v1.29 (2026-09-03)

> 用 MCP 边看边改验证通过：15:53:30-15:55:19 109s 完整跑通 === all done v1.29 ===
> Hamibot 已删除，本存档为唯一真源。以后直接说 执行拼多多MCP流程 即可复跑。

## 设备与环境
- 手机：25053RT47C (onyx) 1280x2772 520dpi
- ADB：C:\\platform-tools\\adb.exe -s adb-41db6aed-hUrFEI._adb-tls-connect._tcp
- 包名：com.xunmeng.pinduoduo 主Activity com.xunmeng.pinduoduo.ui.activity.MainFrameActivity 消费券/商品 NewPageActivity
- Hamibot：已删除 H:\\Codex\\1\\hamibot_pdd.js (git 03bc70a)，不再使用 hamibot.cn

## 8步不变流程
| 步骤 | 动作 | 坐标/文本 | 成功标志 |
|------|------|-----------|----------|
| ensurePdd | 拉起拼多多 | monkey -p com.xunmeng.pinduoduo -c android.intent.category.LAUNCHER 1 + 轮询 dumpsys window | grep mCurrentFocus | inPdd=true |
| goHome | 回首页 | 严格MainFrameActivity，NewPageActivity必须back，否则tap 30,380/128,2640 | MainFrameActivity |
| s1 省钱月卡 | 直点优先 | 896,750 896,784 640,650 依次点，离首页即成功→立即pressBack返回首页 | s1 直点 已离开首页 成功，立即返回 |
| s2 百亿补贴 | banner直点 | 640,1450 | s2 banner直点成功 |
| s3 会员 | 坐标优先 | 1130,165 优先，过滤cy>1700的会员专享价卡片 | s3 坐标已离开首页 成功 |
| s4 打卡 | 居中点 | 385,1180 (Rect 78,1095-357,1153) | s4 打卡 bounds |
| s5 back | 回退 | pressBack | 回首页 |
| s6 消费券 | 底栏兼容 | 开学消费券 Rect560,2664-720,2707 (text空，必须坐标) -> 640,2630 双次；再 去抢购/红块640,810 | s6 底栏已进入消费券页 |
| s7 立即领取 | 坐标兜底 | 立即领取 找不到则 227,1048 640,1048 940,1048 180,860 400,900 800,900 | s7 领取坐标 |
| s8 点亮/滑动 | 滑动10秒 | 立即点亮 -> 去看看 640,1360 -> swipe 1150,1400->700 *5 -> 还剩 补滑 -> swipeToTop 600,700->1400*2 | all done |
| 结束 | 回顶部 | swipeToTop | === all done v1.29 === |

## 核心坐标
省钱月卡 896,750  百亿 640,1450  会员 1130,165  打卡 385,1180
首页tab 128,2640 推荐tab 30,380 消费券底栏 640,2630 红块640,810
滑动 1150,1400->700 回顶部600,700->1400 返回71,177

## 关键判断
isInPdd = currentPackage==com.xunmeng.pinduoduo || dumpsys mCurrentFocus contains pinduoduo
isHome = 严格 dumpsys MainFrameActivity (底栏文字在省钱月卡页也会含首页，不能用文本判)
isCommodity = 加入购物车/立即购买/收藏/直接拼成/限时直降/退货包运费

## MCP监控模板 (20轮*2-3s)
C:\\platform-tools\\adb.exe -s xxx shell dumpsys window | grep mCurrentFocus; dumpsys power | grep mWakefulness; logcat -d | grep GlobalConsole | tail -n 300
日志标志：pdd v1.29, s1 直点, s3 坐标已离开首页, s6 开学消费券, all done

## 坑点
1. NotificationShade 卡住 -> cmd statusbar collapse + CLOSE_SYSTEM_DIALOGS + tap 640,2000，极端 reboot
2. window_dump.xml 底栏开学消费券 text空，只能坐标
3. su true 禁用，用 getShellOut
4. dump超时用 screencap -p

## 扩展
保持s1-s8模块化，追加s9直接在main后加，本文档追加一行。
