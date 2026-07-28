// 脚本 2：还原 DNS & Hosts 并创建 JavDB 自动测速策略组（强行置底）
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
  // 3. 构建 JavDB 自动测速策略组 (排除所有日本节点)
  // ----------------------------------------------------
  if (!config["proxy-groups"]) {
    config["proxy-groups"] = [];
  }

  // 💥 先强行剔除可能残留/旧的的 JavDB 分组，防止位置被占用
  config["proxy-groups"] = config["proxy-groups"].filter(g => g.name !== "JavDB");

  // 获取订阅中所有的【单个节点名称】
  const allProxies = (config["proxies"] || []).map(p => p.name);

  // 过滤掉所有名称中带有日本/Japan/JP 标识的节点
  const nonJpProxies = allProxies.filter(
    name => !/日本|Japan|🇯🇵|\bJP\b/i.test(name)
  );

  // 防错兜底：若过滤后没有剩余节点，默认回退到 DIRECT
  const finalProxies = nonJpProxies.length > 0 ? nonJpProxies : ["DIRECT"];

  // 构建 url-test（自动测速）策略组
  const javdbGroup = {
    name: "JavDB",
    type: "url-test",
    url: "https://cp.cloudflare.com/generate_204", // 测速 URL
    interval: 300,                                 // 300秒测速一次
    tolerance: 50,                                 // 容忍延迟差 50ms 避免频繁切节点
    proxies: finalProxies
  };

  // 👈 强行追加到数组的最末尾
  config["proxy-groups"].push(javdbGroup);

  // ----------------------------------------------------
  // 4. 自定义分流规则
  // ----------------------------------------------------
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    "DOMAIN-SUFFIX,javdb.com,JavDB",     // 1. javdb.com 主站走 JavDB 自动测速组
    "DOMAIN-KEYWORD,javdb,DIRECT"        // 2. 其他 javdb 镜像（如 javdb573.com）一律直连
  ];

  const oldRules = config["rules"] || [];
  config["rules"] = customRules.concat(oldRules);

  return config;
}
