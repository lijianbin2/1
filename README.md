# Sub-Store 脚本

## substore-combined.js

Sub-Store 配置脚本，挂载这一个即可，内部按顺序完成三件事：

1. 备份原始 DNS / Hosts
2. 拉取最新版 convert.min.js（powerfullz/override-rules，grouptype=1）全量重写配置，
   拉取失败时回退到文件尾部的内联快照，6 小时内复用缓存
3. 还原 DNS / Hosts，追加 opencode.ai 专用测速组（全部非香港节点）、
   JavDB 自动测速组（排除日本节点、置底）与自定义分流规则

想改中间脚本的参数（如 `ipv6`、`tun`），改文件顶部的 `__convertArgs()` 默认值，
或者在 Sub-Store 里给脚本 URL 加 `#` 参数（URL 参数优先）。
