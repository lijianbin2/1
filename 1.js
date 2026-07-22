function main(config) {
  // 1. 完全删除 DNS 配置
  delete config["dns"];

  if (!config["proxy-groups"]) {
    config["proxy-groups"] = [];
  }

  // 提取订阅中已存在的【策略组名称】与【节点名称】
  const existingGroups = (config["proxy-groups"] || []).map(g => g.name);
  const existingProxies = (config["proxies"] || []).map(p => p.name);

  // 2. 更加精确的地区匹配规则（使用 \b 避免误触 Twitch, Twitter 等分组）
  const regionRules = [
    { name: "香港", regex: /香港|Hong\s*Kong|🇭🇰|\bHK\b/i },
    { name: "台湾", regex: /台湾|臺灣|Taiwan|🇹🇼|\bTW\b/i }, // 👈 \bTW\b 完美排除 Twitch / Twitter
    { name: "新加坡", regex: /新加坡|Singapore|狮城|🇸🇬|\bSG\b/i },
    { name: "韩国", regex: /韩国|韓國|Korea|🇰🇷|\bKR\b/i },
    { name: "美国", regex: /美国|美國|United\s*States|America|🇺🇸|\bUS\b/i }
  ];

  const matchedItems = [];

  // 遍历各个地区进行智能匹配
  regionRules.forEach(rule => {
    // 优先查找匹配的【策略组】
    const matchedGroups = existingGroups.filter(name => rule.regex.test(name));

    if (matchedGroups.length > 0) {
      matchedItems.push(...matchedGroups);
    } else {
      // 备选：若无对应策略组，查找符合该地区的【单个节点】
      const matchedNodes = existingProxies.filter(name => rule.regex.test(name));
      matchedItems.push(...matchedNodes);
    }
  });

  // 数组去重
  let validProxies = Array.from(new Set(matchedItems));

  // 防错兜底：若没有任何匹配到的节点/分组，默认使用订阅里的第 1 个策略组
  if (validProxies.length === 0) {
    const fallbackGroup = config["proxy-groups"][0]?.name || "DIRECT";
    validProxies = [fallbackGroup];
  }

  // 构建 javdb 策略组
  const javdbGroup = {
    name: "javdb",
    type: "select",
    proxies: validProxies
  };

  // 插入到策略组的第 2 行（索引位置为 1）
  config["proxy-groups"].splice(1, 0, javdbGroup);

  // 3. 将自定义分流规则插入到规则集最前端（优先匹配）
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com,javdb"
  ];

  // 合并规则：自定义规则置顶 + 订阅自带规则
  const oldRules = config["rules"] || [];
  config["rules"] = customRules.concat(oldRules);

  // 返回修改后的配置
  return config;
}
