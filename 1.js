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

  // 提取订阅中已存在的【策略组名称】与【节点名称】
  const existingGroups = (config["proxy-groups"] || []).map(g => g.name);
  const existingProxies = (config["proxies"] || []).map(p => p.name);

  // 地区智能匹配规则（精确定位，排除 Twitch / Twitter）
  const regionRules = [
    { name: "香港", regex: /香港|Hong\s*Kong|🇭🇰|\bHK\b/i },
    { name: "台湾", regex: /台湾|臺灣|Taiwan|🇹🇼|\bTW\b/i },
    { name: "新加坡", regex: /新加坡|Singapore|狮城|🇸🇬|\bSG\b/i },
    { name: "韩国", regex: /韩国|韓國|Korea|🇰🇷|\bKR\b/i },
    { name: "美国", regex: /美国|美國|United\s*States|America|🇺🇸|\bUS\b/i }
  ];

  const matchedItems = [];

  // 遍历各个地区进行智能匹配
  regionRules.forEach(rule => {
    const matchedGroups = existingGroups.filter(name => rule.regex.test(name));

    if (matchedGroups.length > 0) {
      matchedItems.push(...matchedGroups);
    } else {
      const matchedNodes = existingProxies.filter(name => rule.regex.test(name));
      matchedItems.push(...matchedNodes);
    }
  });

  // 数组去重
  let validProxies = Array.from(new Set(matchedItems));

  // 防错兜底
  if (validProxies.length === 0) {
    const fallbackGroup = config["proxy-groups"][0]?.name || "DIRECT";
    validProxies = [fallbackGroup];
  }

  // 构建 JavDB 策略组
  const javdbGroup = {
    name: "JavDB",
    type: "select",
    proxies: validProxies
  };

  // 插入到策略组的第 2 行（索引位置为 1）
  config["proxy-groups"].splice(1, 0, javdbGroup);

  // ----------------------------------------------------
  // 4. 将自定义分流规则插入到规则集最前端
  // ----------------------------------------------------
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com,JavDB"
  ];

  // 合并规则：自定义规则置顶 + 订阅自带规则
  const oldRules = config["rules"] || [];
  config["rules"] = customRules.concat(oldRules);

  // 返回修改后的配置
  return config;
}
