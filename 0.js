// 改进要点：使用 __SUBSTORE_CONFIG_BACKUP__ 和记录时间/来源
function main(config) {
  // 使用更独特的全局备份 key，避免与其他脚本冲突
  globalThis.__SUBSTORE_CONFIG_BACKUP__ = globalThis.__SUBSTORE_CONFIG_BACKUP__ || {};
  globalThis.__SUBSTORE_CONFIG_BACKUP__._meta = {
    saved_at: new Date().toISOString(),
    saved_by: "0.js"
  };

  if (config && config["dns"]) {
    globalThis.__SUBSTORE_CONFIG_BACKUP__["dns"] = JSON.parse(JSON.stringify(config["dns"]));
  } else {
    globalThis.__SUBSTORE_CONFIG_BACKUP__["dns"] = null;
  }

  if (config && config["hosts"]) {
    globalThis.__SUBSTORE_CONFIG_BACKUP__["hosts"] = JSON.parse(JSON.stringify(config["hosts"]));
  } else {
    globalThis.__SUBSTORE_CONFIG_BACKUP__["hosts"] = null;
  }

  return config;
}
