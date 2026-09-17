# Sub-Store 三合一合并脚本 · substore-combined.js

[![Sub-Store](https://img.shields.io/badge/Sub--Store-覆写脚本-1f6feb)](https://github.com/sub-store-org/Sub-Store)
[![Mihomo](https://img.shields.io/badge/Mihomo-Clash-ff6b35)](https://github.com/MetaCubeX/mihomo)
[![Snapshot](https://img.shields.io/badge/快照-2026--08--26-4caf50)](./substore-combined.js)
[![License](https://img.shields.io/badge/license-MIT-informational)](#-许可)

> 由 `build-substore-combined.js` 生成的 **自动更新版** 三合一覆写脚本，执行流程等价于 `0.js → convert.min.js#grouptype=1 → 1.js`，开箱即用、零维护。

---

## 📌 简介

`substore-combined.js` 是为 [Sub-Store](https://github.com/sub-store-org/Sub-Store) 定制的 Clash / Mihomo 配置覆写脚本，整合三段逻辑于一体：

1. **0.js** — 备份原始 `dns` / `hosts`
2. **convert.min.js**（[powerfullz/override-rules](https://github.com/powerfullz/override-rules)）— 全量重写：节点分组、规则集、DNS、嗅探等
3. **1.js** — 还原 DNS / Hosts + 追加自定义后处理与分流规则

与传统三段式引用不同，本脚本 **运行时自动拉取最新版 `convert.min.js`**，失败时无缝回退到文件尾部的内联快照 `CONVERT_SNAPSHOT`，兼顾「始终最新」与「离线可用」。

> ⚠️ **请勿直接编辑生成物** `substore-combined.js`，应修改源码 `src/*.ts` 后重新执行构建脚本生成。

---

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 🔄 自动更新 | 运行时从 `cdn.jsdelivr.net/gh/powerfullz/override-rules/convert.min.js` 拉取最新版，6 h 本地内存缓存 `globalThis.__CONVERT_CACHE__`，避免每次生成配置都触发网络请求 |
| 🛡️ 兜底快照 | 远程拉取失败自动回退到文件尾部的 `CONVERT_SNAPSHOT` 内联快照（快照日期：2026-08-26） |
| 🔒 作用域隔离 | 通过 `new Function` 在隔离的 `globalThis` 中执行中间脚本，防止覆盖本脚本的 `main` |
| 💾 DNS / Hosts 保护 | 执行前后完整备份 / 还原用户原始 `dns` 与 `hosts`，中间脚本的重写不会污染自定义 DNS |
| 🎯 精细后处理 | 剔除「选择代理」中的「自动选择」、删除「非香港节点」组、「AI服务」摘除「选择代理/香港节点」并转故障转移、「谷歌服务」前插「AI服务」、「javdb」地区手动选择组 |
| 📏 幂等规则插入 | 自定义分流规则去重插入，重复生成不堆积（`customRules + oldRules.filter`） |

---

## 📂 文件结构

```
H:/Codex/1/
├── substore-combined.js   # 生成物 — Sub-Store 中直接引用（30066 B，Snapshot 2026-08-26）
└── README.md              # 本文档

# 源码仓库侧（未包含在本目录）：
# ├── build-substore-combined.js  # 构建脚本：拉取最新 convert.min.js 并拼接 0/1.js
# └── src/*.ts                    # 逻辑源码（已迁移至 TypeScript）
```

---

## ⚙️ 工作原理

```mermaid
flowchart LR
  A[Sub-Store 调用 main(config)] --> B[备份 dns/hosts]
  B --> C{缓存命中? < 6h}
  C -->|是| D[复用缓存 main]
  C -->|否| E[fetch CONVERT_URL]
  E -->|成功| F[隔离执行取出 main + 更新缓存]
  E -->|失败| G[回退 CONVERT_SNAPSHOT]
  D & F & G --> H[convertMain(config) 全量重写]
  H --> I[还原 dns/hosts]
  I --> J[后处理 proxy-groups]
  J --> K[追加 customRules]
  K --> L[return config]
```

### 关键实现

- **缓存键**：`globalThis.__CONVERT_CACHE__ = { main, time }` ，TTL = `6 * 60 * 60 * 1000`
- **下载**：优先 `fetch`（Node 18+ Sub-Store 后端自带），降级 `$substore.http.get`（15 s 超时）
- **隔离执行**：`new Function("globalThis","$arguments", code + ";return globalThis.main;")({}, args)`
- **参数透传**：Sub-Store URL 上的 `#` 参数优先于默认值，见下表

---

## 🎛️ 支持参数（URL Hash）

在 Sub-Store 脚本引用 URL 后追加 `#key=value&...` 即可覆盖默认值。例：

```
https://cdn.jsdelivr.net/gh/<user>/<repo>/main/substore-combined.js#grouptype=2&threshold=5&regex=true
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `grouptype` | `0 / 1 / 2` | `1` | 地区分组类型：`0` = select 手动选择、`1` = url-test 自动测速、`2` = load-balance 负载均衡。兼容旧参 `loadbalance=true→2 / false→1` |
| `ipv6` | boolean | `false` | 启用 IPv6 |
| `tun` | boolean | `false` | 启用 TUN（gVisor + route-exclude + dns-hijack） |
| `full` | boolean | `false` | 输出完整 Mihomo 配置（含 mixed-port、external-controller 等，适合纯内核启动） |
| `keepalive` | boolean | `false` | 启用 `tcp-keep-alive` |
| `fakeip` | boolean | `true` | DNS 使用 FakeIP；`false` 时为 RedirHost |
| `quic` | boolean | `false` | 放行 QUIC（UDP 443） |
| `threshold` | number | `0` | 地区节点数 < 阈值时不显示该分组 |
| `regex` | boolean | `false` | 正则过滤模式：用 `include-all + filter` 而非枚举节点名写入地区组 |
| `landing` | — | 自动 | 根据节点 `dialer-proxy` 字段自动识别落地节点，无需传参 |

> 源码已迁移至 `src/*.ts`，参数解析见 `G(ce())`。

---

## 🔧 后处理逻辑（1.js 部分）

### 1. 清理「选择代理」

```js
// 从「选择代理」中排除「自动选择」，避免与 url-test 组重复调度
g.proxies = g.proxies.filter(p => p !== "自动选择");
```

### 2. 收集地区节点组（动态，不硬编码）

地区组统一命名为 `<国家/地区>节点`（如 `香港节点`、`台湾节点`、`美国节点`），以 `节点` 结尾。
后处理先排除功能组（`自动选择 / 手动选择 / 落地节点 / 低倍率节点 / 前置代理 / 非香港节点 / javdb`），
剩下的即为**每一个地区的节点组**，天然兼容 `grouptype=0/1/2` 与 `threshold` 过滤：

```js
// 模块级常量 + 单次遍历：一次循环同时收集地区组并定位 选择代理/AI服务/谷歌服务
const __EXCLUDED_NODE_GROUPS = new Set(["自动选择", "手动选择", "落地节点", "低倍率节点", "前置代理", "非香港节点", "javdb", "javdb手动选择"]); // 旧名仅升级兼容
const __NODE_SUFFIX = /节点$/;
const regionGroups = [];
for (const g of groups) {
  if (__NODE_SUFFIX.test(g.name) && !__EXCLUDED_NODE_GROUPS.has(g.name)) regionGroups.push(g.name);
}
```

### 3. 已删除「非香港节点」组

不再创建该组；同时清理旧配置中的残留（幂等），并从 `AI服务` 的引用中摘除：

```js
config["proxy-groups"] = config["proxy-groups"].filter(g => g.name !== "非香港节点");
```

### 4. 新增「javdb」手动选择组（包含每一个地区的节点组）

javdb 专用 `select` 组，`proxies = __regionGroups`（**含香港节点在内的全量地区组**，动态取值）：

```js
{ name: "javdb", type: "select", proxies: __regionGroups }
```

同样幂等：已存在则只更新 `proxies`，重复生成不堆积。切换节点时在客户端手动点选即可，无需改规则。

### 5. 注入服务链

- `AI服务`：摘除 `选择代理` / `香港节点` / `非香港节点` 引用，类型由 `select` 改为 `fallback`（`url / interval / tolerance` 缺失时自动补齐）
- `谷歌服务` 组保留原有成员并最前插入 `AI服务`（去重幂等）

### 6. 自定义分流规则（幂等）

```js
const customRules = [
  "DOMAIN,cpa.wisdamsatan.de,DIRECT",
  "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
  "DOMAIN-SUFFIX,opencode.ai,AI服务",               // opencode.ai 走 AI 服务
  "DOMAIN-KEYWORD,javdb,javdb",         // 含 javdb 的域名走 javdb 组（含主站，已覆盖 SUFFIX 场景）
];
const customRuleSet = new Set(customRules); // O(1) 去重，原 includes 版为 O(n*m)
config.rules = customRules.concat(oldRules.filter(r => !customRuleSet.has(r)));
```

> javdb 仅保留 `DOMAIN-KEYWORD,javdb` 一条：KEYWORD 已覆盖主站 `javdb.com`，无需再写 SUFFIX。
> javdb 规则指向 `javdb` 组，组内再手动选择具体地区（香港/台湾/美国/日本…）。

---

## 🚀 在 Sub-Store 中使用

1. Sub-Store → `脚本操作` → 新建脚本，粘贴本文件内容或引用远程 URL
2. 订阅 → `脚本` 列选择本脚本，参数示例：`#grouptype=1&regex=false`
3. 保存并生成订阅，客户端（Clash Verge / Mihomo Party / Stash 等）导入即可

#### 本地引用示例

```
脚本路径: H:/Codex/1/substore-combined.js
参数: grouptype=1
```

#### 远程引用示例

```
https://raw.githubusercontent.com/lijianbin2/1/main/substore-combined.js#grouptype=1
https://cdn.jsdelivr.net/gh/lijianbin2/1@main/substore-combined.js#grouptype=1
```

---

## 🛠️ 刷新内联快照

当上游 `convert.min.js` 有重大更新且希望离线快照也同步时：

```bash
node build-substore-combined.js
# 输出: 已拉取最新 convert.min.js，快照日期: YYYY-MM-DD
# 生成: substore-combined.js
```

构建脚本会自动下载最新 `convert.min.js` 并重新拼接 `0.js + 快照 + 1.js`。

---

## 📝 来源与致谢

- 覆写核心：[powerfullz/override-rules](https://github.com/powerfullz/override-rules) — `convert.min.js`
- 图标 CDN：`cdn.jsdelivr.net/gh/Koolson/Qure`
- 规则数据：`MetaCubeX/meta-rules-dat` (geoip/geosite/mmdb/asn)

---

## 📄 许可

遵循上游 `powerfullz/override-rules` 的开源许可。自定义后处理部分可按需自由使用。

---

*README 重写于 2026-09-13，代码优化于 2026-09-17（后处理单次遍历 + Set 查找，行为零变化） · 组改名：javdb手动选择 → javdb（旧名已改名并自动清理） · 生成物 30066 B / 快照 2026-08-26 · 代理推送 `lijianbin2/1@main` · 维护：改 `src/*.ts` 后重跑 `build-substore-combined.js`*
