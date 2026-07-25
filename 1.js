// 脚本 2：还原 DNS & Hosts 并应用分流规则
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
  // 3. 自动获取订阅中的主代理组（通常是第 1 个策略组，如"节点选择"）
  // ----------------------------------------------------
  const mainProxyGroup = (config["proxy-groups"] && config["proxy-groups"][0]) 
    ? config["proxy-groups"][0].name 
    : "节点选择";

  // ----------------------------------------------------
  // 4. 自定义分流规则（置顶插入，注意优先顺序！）
  // ----------------------------------------------------
  const customRules = [
    "DOMAIN,cpa.wisdomsatan.de,DIRECT",
    "DOMAIN-SUFFIX,bingosoft.net,DIRECT",
    `DOMAIN-SUFFIX,javdb.com,${mainProxyGroup}`, // 1. javdb.com 主站走默认主代理组
    "DOMAIN-KEYWORD,javdb,DIRECT"                // 2. 其他 javdb 变体/镜像（如 javdb573.com）一律直连
  ];

  const oldRules = config["rules"] || [];
  config["rules"] = customRules.concat(oldRules);

  return config;
}
