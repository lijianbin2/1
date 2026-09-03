# MCP 一键运行脚本说明

本文件夹是方案2的本地直跑版：不依赖 Hamibot，直接用 ADB 操作手机。

## 文件清单
- pdd_mcp_flow.md        本文档，8步流程+坐标+坑点，全量存档
- mcp_pdd_runner.ps1     一键运行脚本 (PowerShell + ADB)
- prompt_pdd_mcp.md      给 Codex 的提示词模板，下次你说 执行拼多多MCP流程 我直接按此跑
- .agent_id              手机 ADB 序列号记录

## 快速使用

### 方式A：让我跑 (推荐)
你只需说：
  执行拼多多MCP流程
或
  连上手机 192.168.1.x:xxxxx 跑拼多多
我会自动：
  adb devices -> dumpsys window -> tap/shell input -> 截图验证 -> 边看边改

### 方式B：你自己双击跑
1. 手机连电脑，开启 USB调试/无线调试
2. 双击 mcp_pdd_runner.ps1 (或右键 PowerShell 运行)
3. 看控制台日志，直到 all done

### 自定义新增步骤
在 pdd_mcp_flow.md 底部追加一行，同步在 mcp_pdd_runner.ps1 的 main() 里追加函数 s9() 即可

---
生成时间：2026-09-03  Hamibot已清理  v1.27 封存
