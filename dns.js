// 脚本 1：备份原始 DNS 配置
function main(config) {
  // 使用 globalThis 作为全局跨脚本传递数据的容器
  if (config && config["dns"]) {
    globalThis.__ORIGINAL_DNS_BACKUP__ = JSON.parse(JSON.stringify(config["dns"]));
  } else {
    globalThis.__ORIGINAL_DNS_BACKUP__ = null;
  }

  // 不修改 config，原样返回传递给下一个脚本
  return config;
}
