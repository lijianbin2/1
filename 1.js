function main(config) {
  // 1. 完全删除 DNS 配置
  delete config["dns"];

  // 初始化 proxy-groups
  const groups = config["proxy-groups"] = config["proxy-groups"] || [];

  // 提取名称
  const existingGroups = groups.map(g => g.name);
  const existingProxies = (config["proxies"] || []).map(p => p.name);

  // 地区匹配规则
  const regionRules = [
    { regex: /香港|Hong\s*Kong|🇭🇰|\bHK\b/i },
    { regex: /台湾|臺灣|Taiwan|🇹🇼|\bTW\b/i },
    { regex: /新加坡|Singapore|狮城|🇸🇬|\bSG\b/i },
    { regex: /韩国|韓國|Korea|🇰🇷|\bKR\b/i },
    { regex: /美国|美國|United\s*States|America|🇺🇸|\bUS\b/i }
  ];

  const matchedItems = [];

  // 智能匹配：优先策略组，其次单个节点
  for (const { regex } of regionRules) {
    const matchedGroups = existingGroups.filter(name => regex.test(name));
    if (matchedGroups.length) {
      matchedItems.push(...matchedGroups);
    } else {
      const matchedNodes = existingProxies.filter(name => regex.test(name));
      matchedItems.push(...matchedNodes);
    }
  }

  // 去重 + 兜底
  let validProxies = [...new Set(matchedItems)];
  if (!validProxies.length) {
    validProxies = [groups[0]?.name || "DIRECT"];
  }

  // 构建并插入 JavDB 策略组
  groups.splice(1, 0, {
    name: "JavDB",
    type: "select",
    proxies: validProxies
  });

  // 自定义规则置顶
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com,JavDB"
  ];

  config["rules"] = [...customRules, ...(config["rules"] || [])];

  return config;
}
