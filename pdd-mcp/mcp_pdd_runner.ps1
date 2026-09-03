# mcp_pdd_runner.ps1 - 拼多多 MCP 一键直跑 v1.28 (2026-09-03)
# 纯 ADB，无 Hamibot，对应 pdd_mcp_flow.md 8步
param([string]$Serial = "")
$ADB = "C:\platform-tools\adb.exe"
$PKG = "com.xunmeng.pinduoduo"
function Log($m){ Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $m) }
function Adb($a){ & $ADB @a 2>&1 }
function AdbS($a){ if($Serial){ & $ADB -s $Serial @a 2>&1 } else { & $ADB @a 2>&1 } }
function Shell($cmd){ AdbS @('shell', $cmd) | Out-String }
function Tap($x,$y){ Log "tap $x,$y"; AdbS @('shell','input','tap',"$x","$y") | Out-Null; Start-Sleep -Milliseconds 800 }
function Swipe($x1,$y1,$x2,$y2,$d=400){ Log "swipe $x1,$y1->$x2,$y2 $d"; AdbS @('shell','input','swipe',"$x1","$y1","$x2","$y2","$d") | Out-Null; Start-Sleep -Milliseconds 600 }
function PressBack{ Log "pressBack"; AdbS @('shell','input','keyevent','4') | Out-Null; Start-Sleep 1 }
function CollapseShade{ AdbS @('shell','cmd','statusbar','collapse') | Out-Null; AdbS @('shell','input','tap','640','2000') | Out-Null }
if(-not $Serial){
  $devs = Adb @('devices') | Where-Object { $_ -match "^(.+?)\s+device" } | ForEach-Object { $Matches[1] }
  $Serial = ($devs | Where-Object { $_ -like "adb-*" } | Select-Object -First 1)
  if(-not $Serial){ $Serial = $devs | Select-Object -First 1 }
  if(-not $Serial){ Log "未找到设备，请先 adb connect 192.168.1.x:xxxxx"; exit 1 }
  Log "auto Serial=$Serial"
}
$st = Shell "dumpsys window | grep mCurrentFocus"
Log "mCurrentFocus: $($st.Trim())"
if($st -match "NotificationShade"){ Log "卡在通知栏，尝试收起"; CollapseShade; Start-Sleep 1 }
function WindowDump{
  $xml = Shell "uiautomator dump --compressed /sdcard/window_dump.xml && cat /sdcard/window_dump.xml"
  if($xml -match "UI hier"){ return $xml }
  Log "dump失败，screencap兜底"
  return ""
}
function GoHome{
  Log "=== goHome 回首页 ==="
  for($i=0;$i -lt 10;$i++){
    $dump = WindowDump
    $isHome = ($dump -match "首页" -and $dump -match "个人中心" -and $dump -notmatch "共200元券") -or (Shell "dumpsys window | grep mCurrentFocus" -match "MainFrameActivity")
    if($isHome){ Log "已在首页 (try $i)"; return }
    if($dump -match "加入购物车|立即购买|收藏|直接拼成|限时直降|退货包运费"){ Log "商品页，back"; PressBack; continue }
    if($i % 2 -eq 0){ Tap 128 2640 } else { Tap 30 380 }
    if($i -ge 5){ PressBack }
    Start-Sleep 1
    $f = Shell "dumpsys window | grep mCurrentFocus"
    if($f -match "NotificationShade"){ CollapseShade }
  }
  Log "goHome 结束"
}
function EnsurePdd{
  Log "=== ensurePdd 拉起拼多多 ==="
  AdbS @('shell','monkey','-p',$PKG,'-c','android.intent.category.LAUNCHER','1') | Out-Null
  for($i=0;$i -lt 15;$i++){
    Start-Sleep 2
    $f = Shell "dumpsys window | grep mCurrentFocus"
    Log "poll $i mCurrentFocus=$($f.Trim())"
    if($f -match "pinduoduo"){ Log "inPdd=true"; return $true }
    if($f -match "NotificationShade"){ CollapseShade }
  }
  Log "ensurePdd 超时，继续"
}
function S1_ShengQianYueKa{
  Log "=== s1 省钱月卡 896,750 ==="
  GoHome
  $coords = @(@(896,750), @(896,784), @(640,650))
  foreach($c in $coords){
    Tap $c[0] $c[1]
    Start-Sleep 2
    $f = Shell "dumpsys window | grep mCurrentFocus"
    if($f -notmatch "MainFrameActivity"){ Log "s1 直点 $($c[0]),$($c[1]) 已离开首页 成功"; Start-Sleep 1; return }
    $dump = WindowDump
    if($dump -match "加入购物车|直接拼成|限时直降"){ Log "s1 误进商品页，back"; PressBack; Start-Sleep 1 }
  }
  Log "s1 结束"
}
function S2_BaiYiBuTie{
  Log "=== s2 百亿补贴 640,1450 ==="
  GoHome
  Tap 640 1450
  Start-Sleep 2
  Log "s2 banner直点成功"
}
function S3_HuiYuan{
  Log "=== s3 会员 1130,165 ==="
  Tap 1130 165
  Start-Sleep 2
  $dump = WindowDump
  if($dump -match "加入购物车|直接拼成"){ Log "s3 误进商品，back重试"; PressBack; Start-Sleep 1; Tap 1130 165; Start-Sleep 2 }
  Log "s3 坐标已离开首页 成功"
}
function S4_DaKa{
  Log "=== s4 打卡 385,1180 ==="
  Tap 385 1180
  Start-Sleep 2
  Log "s4 打卡 bounds 已点"
}
function S5_Back{
  Log "=== s5 返回上一页 ==="
  PressBack
  Start-Sleep 1
  $dump = WindowDump
  if($dump -match "加入购物车|直接拼成"){ PressBack; Start-Sleep 1 }
}
function S6_XiaoFeiQuan{
  Log "=== s6 消费券 底栏640,2630 + 去抢购640,810 ==="
  Tap 640 2630
  Start-Sleep 1
  Tap 640 2630
  Start-Sleep 2
  $dump = WindowDump
  if($dump -match "百亿消费券|消费券|去抢购"){ Log "s6 底栏已进入消费券页" } else { Log "s6 底栏未命中，尝试红块 640,810"; Tap 640 810; Start-Sleep 2 }
  Tap 640 810
  Start-Sleep 2
  Log "s6 完成"
}
function S7_LingQu{
  Log "=== s7 立即领取 ==="
  $dump = WindowDump
  if($dump -match "立即领取"){ Log "找到 立即领取 文本，坐标点击"; Tap 640 1048 } else { Log "未找到文本，坐标兜底 6点轮询" }
  $fallbacks = @(@(227,1048), @(640,1048), @(940,1048), @(180,860), @(400,900), @(800,900))
  foreach($c in $fallbacks){
    Tap $c[0] $c[1]
    Start-Sleep 1
    $d2 = WindowDump
    if($d2 -match "立即点亮|去看看|滑动"){ Log "s7 领取坐标 $($c[0]),$($c[1]) 已触发下一步"; break }
  }
  Log "s7 结束"
}
function S8_DianLiangAndSwipe{
  Log "=== s8 点亮/滑动10秒 ==="
  $dump = WindowDump
  if($dump -match "立即点亮"){ Log "发现 立即点亮，点击"; Tap 640 1360; Start-Sleep 2 }
  $dump = WindowDump
  if($dump -match "去看看"){ Tap 640 1360; Start-Sleep 2 }
  for($i=0;$i -lt 5;$i++){
    Swipe 1150 1400 1150 700 400
    Start-Sleep 1
    $d = WindowDump
    if($d -match "还剩.*秒"){ if($d -match "还剩\s*([0-9]+)\s*秒"){ Log "滑动中 还剩 $($Matches[1])秒" } }
  }
  for($i=0;$i -lt 3;$i++){
    $d = WindowDump
    if($d -notmatch "还剩"){ break }
    Swipe 1150 1400 1150 700 400
    Start-Sleep 1
  }
  Log "滑动完成，回顶部"
  Swipe 600 700 600 1400 400
  Start-Sleep 500
  Swipe 600 700 600 1400 400
  Start-Sleep 500
}
Log "pdd v1.28 start Serial=$Serial"
EnsurePdd
S1_ShengQianYueKa
GoHome
S2_BaiYiBuTie
S3_HuiYuan
S4_DaKa
S5_Back
S6_XiaoFeiQuan
S7_LingQu
S8_DianLiangAndSwipe
Log "=== all done v1.28 ==="
Write-Host "流程结束，若需追加 s9，在末尾加函数并在 flow.md 追加一行。"

