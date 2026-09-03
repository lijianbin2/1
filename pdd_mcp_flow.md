# 拼多多 MCP 全流程 - 存档 v1.32 (2026-09-04 01:27)

> 用 MCP 边看边改验证通过：15:53:30-15:55:19 109s 完整跑通 === all done v1.29 ===
> Hamibot 已删除，本存档唯一真源H:\Codex\1\pdd_mcp_flow.md；pdd-mcp下不再保留副本。以后直接说 执行拼多多MCP流程 即可复跑。
> v1.32 单步验证：01:27 去领取 997,540 已验证，领取后即停，不再跳转其他页面。

## 设备与环境
- 手机：25053RT47C (onyx) 1280x2772 520dpi
- ADB：C:\Users\1\.phonemcp\platform-tools\adb.exe -s adb-41db6aed-hUrFEI._adb-tls-connect._tcp
- 包名：com.xunmeng.pinduoduo 主Activity com.xunmeng.pinduoduo.ui.activity.MainFrameActivity 消费券/商品 NewPageActivity
- Hamibot：已删除 H:\Codex\1\hamibot_pdd.js (git 03bc70a)，不再使用 hamibot.cn

## 8步不变流程
| 步骤 | 动作 | 坐标/文本 | 成功标志 |
|------|------|-----------|----------|
| ensurePdd | 拉起拼多多 | monkey -p com.xunmeng.pinduoduo -c android.intent.category.LAUNCHER 1 + 轮询 dumpsys window | grep mCurrentFocus | inPdd=true |
| goHome | 回首页 | 严格MainFrameActivity，NewPageActivity必须back，否则tap 30,380/128,2640 | MainFrameActivity |
| s1 省钱月卡 | 直点优先 | 895,766 [832,703][959,830]（回顶部600,700->1400 x2后点，旧896,750易误进商品），离首页即成功→立即pressBack返回首页 | s1 直点 已离开首页 成功，立即返回 |
| s2 百亿补贴 | 粉色logo直点 | 110,1360 [左粉色百亿补贴 官方补贴, 实测640,1450误进商品, 修正110,1360 直进白底页] | s2 banner直点成功 |
| s3 会员 | 金色会员直点 | 1120,233 [实测dump 1091,152-1280,315 TextView 会员, 中心1185,233极近...易误触, 左移至1120,233可进v3会员专享价页, 1:09已验证] | s3 已进v3会员专享价页 |
| s4 打卡 | 居中点 | 640,1280（原385,1180偏左，1:16验证积分1277→1287） | s4 打卡成功 积分+10 |
| s5 back | 回退 | pressBack | 回百亿补贴 |
| s6 消费券 | 红块直点 | 已改 640,680 [原640,810]（1:18验证进粉头 消费券 4.3折起） | s6 已进消费券页 |
| s7 去领取 | 单点即停 | 997,540 [903,503][1092,578]（dump2唯一可见，备选 191,578 / 734,578 顶部, 01:27单步验证 997,540 成功，领取后即停不再跳转） | s7 领取完成 即停 |
| s8 点亮/滑动 | 滑动10秒(可选) | 立即点亮 830,410 -> 去看看 485,1485 -> swipe 640,1700->900 x7 -> 粉条消失 -> 顶部 910,855 或 swipe 600,700->1400*2 | all done |
| 结束 | 领取后即停 | s7完成后直接结束，不进其他页面 | === all done v1.32 === |

## 核心坐标
省钱月卡 895,766（回顶部后）  百亿 110,1360  会员 1120,233  打卡 640,1280
去领取 997,540 [903,503][1092,578]（顶部备选 191,578 734,578） 消费券红块640,680
首页tab 128,2640 推荐tab 30,380 滑动 640,1700->900 回顶部600,700->1400 返回keyevent 4

## 关键判断
isInPdd = currentPackage==com.xunmeng.pinduoduo || dumpsys mCurrentFocus contains pinduoduo
isHome = 严格 dumpsys MainFrameActivity (底栏文字在省钱月卡页也会含首页，不能用文本判)
isCommodity = 加入购物车/立即购买/收藏/直接拼成/限时直降/退货包运费
isQuanPage = 粉头 消费券 + 共200元券 / 消费券 4.3折起

## MCP监控模板 (20轮*2-3s)
C:\Users\1\.phonemcp\platform-tools\adb.exe -s xxx shell dumpsys window | grep mCurrentFocus; dumpsys power | grep mWakefulness
日志标志：pdd v1.32, s3 1120,233, s4 640,1280, s6 640,680, s7 997,540 领取后即停, all done

## 坑点
1. NotificationShade 卡住 -> cmd statusbar collapse + CLOSE_SYSTEM_DIALOGS + tap 640,2000，极端 reboot
2. window_dump.xml 底栏开学消费券 text空，只能坐标；消费券页 去领取 多为 [0,0][0,0] 屏外，仅顶部 997,540 可见，需精准ET解析
3. su true 禁用，用 getShellOut
4. dump超时用 screencap -p
5. 去领取误点 191,578 会进错误券详情，需按用户要求点 997,540 并领取后即停

## 扩展
保持s1-s8模块化，追加s9直接在main后加，本文档追加一行。

## v1.30-1.32 补充（9/4 一步一步调试）
- s1 必须先 swipeToTop 600,700->1400 x2，回顶部后 tap 895,766 验证通过
- s3 1120,233 已验证进 v3会员专享价页（1:14 cur_member_try2.png）
- s4 640,1280 积分1277→1287 第4天变灰（1:16）
- s6 红块 640,680 成功进消费券页（1:18 cur_baiyi_quan2.png）
- s8 滑动 640,1700->900 x7 粉条消失 已完成10s（1:24 cur_swipe10_quan3.png），顶部按钮 910,855
- 01:27 s7 单步验证：dump2 ET解析唯一可见 去领取 [903,503][1092,578] cx997,540，tap 997,540 仍 NewPageActivity，截图 cur_after_qulingqu_correct2.png 1.47MB，确认领取后即停，不再进其他页面（用户 01:27 指令）

> 临时文件统一 C:\Users\1\AppData\Local\Temp\pdd_mcp_tmp\ (cur*.png等)，H:\Codex\1 仅留 pdd_mcp_flow.md（其他无关md保留）
