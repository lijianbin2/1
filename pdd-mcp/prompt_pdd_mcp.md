# 拼多多 MCP 提示词模板 - 给 Codex / 下一个 LLM 用

> 存档位置: H:\Codex\pdd-mcp\pdd_mcp_flow.md (真源) + mcp_pdd_runner.ps1 (本地直跑)
> 设备: 25053RT47C onyx 1280x2772 | ADB C:\platform-tools\adb.exe | 包 com.xunmeng.pinduoduo
> 版本: v1.29 (2026-09-03) 继承 v1.29 验证 109s

## 触发词
用户说以下任意一句，立即按本文执行，无需再问：
- 执行拼多多MCP流程
- 跑拼多多
- 连上手机 192.168.1.4:xxxxx 跑拼多多
- pdd 全流程

## 你要做的 (MCP 边看边改模式)

### 1. 连接与自检
```powershell
C:\platform-tools\adb.exe devices
C:\platform-tools\adb.exe -s <SERIAL> shell dumpsys window | grep mCurrentFocus
```
- SERIAL 自动选 adb- 开头的，无则取第一个 device
- 若 mCurrentFocus 含 NotificationShade -> cmd statusbar collapse + input tap 640,2000
- 禁止: adb kill-server, keyevent 224, su true

### 2. 按 pdd_mcp_flow.md 8步执行 (坐标不变)
| 步骤 | 操作 | 坐标 | 日志 |
|------|------|------|------|
| ensurePdd | monkey拉起 | monkey -p com.xunmeng.pinduoduo 1 | inPdd=true |
| goHome | 回首页10次循环 | tap 30,380 / 128,2640 + robustBack | MainFrameActivity |
| s1 | 省钱月卡直点 | 896,750 > 896,784 > 640,650 | s1 直点 896,750 已离开首页 |
| s2 | 百亿补贴banner | 640,1450 | s2 banner直点成功 |
| s3 | 会员右上角 | 1130,165 过滤cy>1700 | s3 坐标已离开首页 |
| s4 | 打卡居中 | 385,1180 | s4 打卡 bounds |
| s5 | 返回 | pressBack | 回补贴页 |
| s6 | 消费券底栏+红块 | 640,2630*2 -> 640,810 | s6 底栏已进入消费券页 |
| s7 | 立即领取6点兜底 | 227,1048 640,1048 ... | s7 领取坐标 |
| s8 | 点亮+滑动10秒+回顶部 | 立即点亮->640,1360->swipe1150,1400->700*5 | all done v1.29 |

### 3. 判定补丁 (必须遵守)
- isHome = 严格 MainFrameActivity (禁止用 首页+个人中心 文本，省钱月卡页底栏也会含首页导致误判)
- isCommodityPage = 含 加入购物车/立即购买/收藏/直接拼成/限时直降/退货包运费
- s6底栏 开学消费券 window_dump.xml text=""，必须用坐标 640,2630
- s6红块 640,810 整体可点，不必拘泥 已抢购 文本
- s8 滑动失败会进商品页 -> isCommodityPage 检测到立即 pressBack

### 4. 监控循环 (用户每次说 已运行 就做)
看日志关键字推进下一步，有问题立即改脚本 H:\Codex\pdd-mcp\mcp_pdd_runner.ps1 再重跑。

### 5. 本地直跑备选
```powershell
powershell -ExecutionPolicy Bypass -File H:\Codex\pdd-mcp\mcp_pdd_runner.ps1
powershell -ExecutionPolicy Bypass -File H:\Codex\pdd-mcp\mcp_pdd_runner.ps1 -Serial 192.168.1.4:xxxxx
```

## 扩展新步骤
- 在 pdd_mcp_flow.md 表格追加一行 s9
- 在 mcp_pdd_runner.ps1 末尾追加 S9_xxx 函数
- 日志统一 Log "=== s9 xxx ===" 便于 grep

## 完成标志
控制台最后打印 === all done v1.29 === 且 dumpsys 回到 MainFrameActivity 即成功。
---
生成: 2026-09-03 | 真源 pdd_mcp_flow.md | 无 Hamibot | 坐标1280x2772不变

