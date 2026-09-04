# 任务记录：MangoDisk 小红书图文发布

日期：2026-09-03 夜到 2026-09-04 凌晨
目标：MangoDisk 深度清理工具的小红书图文，私发先行，半小时后公发。

## 一、做完的事

1. 图文已就绪：C:/Users/1/Documents/Codex/2026-09-03/MangoDisk outputs/cover.png + card_1到7共8图，配图已嵌卡2大图，逐张校验无溢出。
2. D盘落盘：D:/小红书/MangoDisk_深度清理_20250903 图文 原图 MD 发布文案 zip 说明全套。
3. 私发成功：note_id 6a99a2bd00000000260229f4，仅自己可见，链接见第四节。
4. 工作流程沉淀为 H:/Codex/1/工作流程_小红书发布.md，查笔记脚本 H:/Codex/1/check_notes.py。
5. 技能目录垃圾已清，H:/Codex/1 已 git push 到 GitHub main（d834690）。

## 二、发布过程排障
1. publish_xhs.py 的 --topics 参数必崩：话题接口返回缺 msg 字段导致 KeyError，图传完但笔记不提交。改用话题标签写进正文一次成功。
2. 发布必须以技能目录为 workdir，否则缺 crypto-js：H:/Codex/.codex/skills/Auto-Redbook-Skills-main，里面有 node_modules 才能调 cookie 生成 x-s 等参数。
3. 发布命令超 10 秒会转后台：一律重定向到日志文件再 Get-Content 轮询；write_stdin 不可用，有会话 id 浮点解析 bug。
4. 防重发铁律：post_note 无去重，成功后绝不重试。Dashi 曾重发 5 篇一样的内容，用户手动删过。成功后写 outputs/published_mango.txt 标记。

## 三、文件位置清单
- 图文源：C:/Users/1/Documents/Codex/2026-09-03/MangoDisk/
- D 盘：D:/小红书/MangoDisk_深度清理_20250903/
- 流程文档：H:/Codex/1/工作流程_小红书发布.md
- 查笔记：python -X utf8 H:/Codex/1/check_notes.py
- 仓库：H:/Codex/1，GitHub lijianbin2/1.git，main 分支

## 四、笔记链接与待办公发
- 私发链接：https://www.xiaohongshu.com/explore/6a99a2bd00000000260229f4
- 状态：仅自己可见，创作平台已确认为最新单篇，2026-09-04 00:39，无重发。
- 待办：半小时后若用户说公开，需用 --public 重新发一篇公开版，私发篇改不了可见性，发前先查平台确认再发，避免重复。

## 五、用户偏好备忘
- 流程偏好：私发加半小时后加公发，图文必带配图，D 盘落盘，预览用绝对路径。
- exec 约束：workdir 填真实存在目录，命令禁 $ 开头词，中文用单引号包裹，路径用正斜杠。
