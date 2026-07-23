// 脚本 1：备份原始 DNS 和 Hosts 配置
function main(config) {
  // 初始化全局备份对象
  globalThis.__CONFIG_BACKUP__ = globalThis.__CONFIG_BACKUP__ || {};

  // 1. 备份 DNS
  if (config && config["dns"]) {
    globalThis.__CONFIG_BACKUP__["dns"] = JSON.parse(JSON.stringify(config["dns"]));
  } else {
    globalThis.__CONFIG_BACKUP__["dns"] = null;
  }

  // 2. 备份 Hosts
  if (config && config["hosts"]) {
    globalThis.__CONFIG_BACKUP__["hosts"] = JSON.parse(JSON.stringify(config["hosts"]));
  } else {
    globalThis.__CONFIG_BACKUP__["hosts"] = null;
  }

  // 原样返回，继续传递给中间脚本
  return config;
}
