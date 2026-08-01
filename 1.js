// 脚本 2（改进版）：还原 DNS & Hosts 并创建 JavDB 自动测速策略组（强行置底）
// 改进点：没有非日本节点时不再创建 url-test 组，javdb.com 直接走 DIRECT
function main(config) {
  const backup = globalThis.__SUBSTORE_CONFIG_BACKUP__ || {};

  // ----------------------------------------------------
  // 1. 还原初始备份的 DNS 设置
  // ----------------------------------------------------
  if (backup["dns"]) {
    config["dns"] = JSON.parse(JSON.stringify(backup["dns"]));
  } else {
    delete config["dns"];
  }

  // ----------------------------------------------------
  // 2. 还原初始备份的 Hosts 设置
  // ----------------------------------------------------
  if (backup["hosts"]) {
    config["hosts"] = JSON.parse(JSON.stringify(backup["hosts"]));
  } else {
    delete config["hosts"];
  }

  // ----------------------------------------------------
  // 3. 构建 JavDB 自动测速策略组 (排除所有日本节点)
  // ----------------------------------------------------
  if (!config["proxy-groups"]) {
    config["proxy-groups"] = [];
  }

  // 先移除可能残留/旧的 JavDB 分组，防止位置被占用
  config["proxy-groups"] = config["proxy-groups"].filter(g => g.name !== "JavDB");

  // 更健壮地提取订阅中所有的【单个节点名称】，兼容字符串或对象
  const allProxies = (config["proxies"] || [])
    .map(p => (typeof p === 'string' ? p : (p && p.name) || ''))
    .filter(Boolean);

  // 过滤掉所有名称中带有日本/Japan/JP 标识的节点
  const nonJpProxies = allProxies.filter(
    name => !/日本|Japan|🇯🇵|\bJP\b/i.test(name)
  );

  // 默认 javdb.com 直接连接（当没有可用非日本节点时）
  let javdbTarget = "DIRECT";

  // 仅当存在非日本节点时创建自动测速组，避免 url-test 对 DIRECT 做无意义测速
  if (nonJpProxies.length > 0) {
    const javdbGroup = {
      name: "JavDB",
      type: "url-test",
      url: "https://www.gstatic.com/generate_204", // 已更新测速 URL（Google），可根据需要替换
      interval: 300,                                 // 300秒测速一次
      tolerance: 50,                                 // 容忍延迟差 50ms 避免频繁切节点
      proxies: nonJpProxies
    };

    // 强行追加到数组的最末尾
    config["proxy-groups"].push(javdbGroup);
    javdbTarget = "JavDB";
  }

  // ----------------------------------------------------
  // 4. 自定义分流规则（确保幂等，不重复追加）
  // 注意：DOMAIN-SUFFIX,javdb.com 必须排在 DOMAIN-KEYWORD,javdb 之前
  // ----------------------------------------------------
  const customRules = [
    "DOMAIN,cpa.wisdamsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com," + javdbTarget, // javdb.com 主站走 JavDB 自动测速组（无可用节点时直连）
    "DOMAIN-KEYWORD,javdb,DIRECT"             // 其他 javdb 镜像一律直连
  ];

  const oldRules = config["rules"] || [];
  // 移除老规则里与 customRules 完全相同的行，保证 idempotent
  const filteredOldRules = oldRules.filter(r => !customRules.includes(r));
  config["rules"] = customRules.concat(filteredOldRules);

  return config;
}
