// 脚本 2：还原 DNS & Hosts 并应用 JavDB 规则
function main(config) {
  const backup = globalThis.__CONFIG_BACKUP__ || {};

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
  // 3. 策略组处理 (JavDB)
  // ----------------------------------------------------
  if (!config["proxy-groups"]) {
    config["proxy-groups"] = [];
  }

  const existingGroups = (config["proxy-groups"] || []).map(g => g.name);
  const existingProxies = (config["proxies"] || []).map(p => p.name);

  // 地区智能匹配规则（港、台、新、美）
  const regionRules = [
    { name: "香港", regex: /香港|Hong\s*Kong|🇭🇰|\bHK\b/i },
    { name: "台湾", regex: /台湾|臺灣|Taiwan|🇹🇼|\bTW\b/i },
    { name: "新加坡", regex: /新加坡|Singapore|狮城|🇸🇬|\bSG\b/i },
    { name: "美国", regex: /美国|美國|United\s*States|America|🇺🇸|\bUS\b/i }
  ];

  const matchedItems = [];

  regionRules.forEach(rule => {
    const matchedGroups = existingGroups.filter(name => rule.regex.test(name));

    if (matchedGroups.length > 0) {
      matchedItems.push(...matchedGroups);
    } else {
      const matchedNodes = existingProxies.filter(name => rule.regex.test(name));
      matchedItems.push(...matchedNodes);
    }
  });

  let validProxies = Array.from(new Set(matchedItems));

  if (validProxies.length === 0) {
    const fallbackGroup = config["proxy-groups"][0]?.name || "DIRECT";
    validProxies = [fallbackGroup];
  }

  const javdbGroup = {
    name: "JavDB",
    type: "select",
    proxies: validProxies
  };

  // 插入到策略组第 2 行（索引 1）
  config["proxy-groups"].splice(1, 0, javdbGroup);

  // ----------------------------------------------------
  // 4. 将自定义分流规则插入到最前端（注意顺序！）
  // ----------------------------------------------------
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com,JavDB",     // 1. 主站 javdb.com 及其子域名走 JavDB 策略组
    "DOMAIN-KEYWORD,javdb,DIRECT"        // 2. 其他所有包含 javdb 的域名（如 javdb573.com）一律直连
  ];

  const oldRules = config["rules"] || [];
  config["rules"] = customRules.concat(oldRules);

  return config;
}
