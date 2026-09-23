const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const scriptPath = path.join(__dirname, "..", "substore-combined.js");
const scriptSource = fs.readFileSync(scriptPath, "utf8");

function makeConfig() {
  return {
    proxies: [
      { name: "Hong Kong 01", type: "ss", server: "example.com", port: 443, cipher: "aes-128-gcm", password: "test" },
      { name: "Tokyo 01", type: "ss", server: "example.com", port: 443, cipher: "aes-128-gcm", password: "test" },
      { name: "Los Angeles 01", type: "ss", server: "example.com", port: 443, cipher: "aes-128-gcm", password: "test" }
    ]
  };
}

function createRuntime(overrides = {}) {
  const logs = [];
  const runtime = {
    console: {
      log: (message) => logs.push({ level: "log", message: String(message) }),
      error: (message) => logs.push({ level: "error", message: String(message) })
    },
    setTimeout,
    clearTimeout,
    AbortController,
    ...overrides
  };
  vm.createContext(runtime);
  vm.runInContext(
    scriptSource + "\nglobalThis.__test = { main, snapshot: CONVERT_SNAPSHOT };",
    runtime
  );
  runtime.logs = logs;
  return runtime;
}

function findGroup(config, name) {
  return config["proxy-groups"].find((group) => group.name === name);
}

test("源码缓存不会锁死首次调用的 grouptype", async () => {
  let fetchCount = 0;
  const runtime = createRuntime({
    fetch: async () => {
      fetchCount += 1;
      return { ok: true, text: async () => runtime.__test.snapshot };
    }
  });

  runtime.$arguments = { grouptype: 0, threshold: 0 };
  const first = await runtime.__test.main(makeConfig());
  runtime.$arguments = { grouptype: 2, threshold: 0 };
  const second = await runtime.__test.main(makeConfig());

  assert.equal(findGroup(first, "香港节点").type, "select");
  assert.equal(findGroup(second, "香港节点").type, "load-balance");
  assert.equal(fetchCount, 1);
  assert.equal(typeof runtime.__SUBSTORE_COMBINED_CONVERT_V2__.code, "string");
  assert.equal(runtime.__SUBSTORE_COMBINED_CONVERT_V2__.main, undefined);
});

test("远程入口运行失败时回退到内联快照", async () => {
  const runtime = createRuntime({
    fetch: async () => ({
      ok: true,
      text: async () => "globalThis.main = () => { throw new Error('remote boom'); };"
    })
  });
  runtime.$arguments = { threshold: 0 };

  const config = await runtime.__test.main(makeConfig());

  assert.ok(findGroup(config, "香港节点"));
  assert.ok(runtime.logs.some(({ message }) => message.includes("运行失败，使用内联快照")));
  assert.equal(runtime.__SUBSTORE_COMBINED_CONVERT_V2__.code, undefined);
});

test("远程入口返回无效对象时回退到内联快照", async () => {
  const runtime = createRuntime({
    fetch: async () => ({ ok: true, text: async () => "globalThis.main = () => null;" })
  });
  runtime.$arguments = { threshold: 0 };

  const config = await runtime.__test.main(makeConfig());

  assert.ok(findGroup(config, "香港节点"));
  assert.ok(runtime.logs.some(({ message }) => message.includes("返回了无效配置")));
});

test("fetch 悬挂时触发硬超时并使用内联快照", async () => {
  const runtime = createRuntime({
    fetch: () => new Promise(() => {}),
    setTimeout: (callback) => {
      queueMicrotask(callback);
      return 1;
    },
    clearTimeout: () => {}
  });
  runtime.$arguments = { threshold: 0 };

  const config = await runtime.__test.main(makeConfig());

  assert.ok(findGroup(config, "香港节点"));
  assert.ok(runtime.logs.some(({ message }) => message.includes("fetch 超时")));
});

test("fetch 失败时尝试 Sub-Store HTTP 客户端", async () => {
  const runtime = createRuntime({
    fetch: async () => {
      throw new Error("fetch boom");
    },
    $substore: {
      http: {
        get: async () => ({ body: runtime.__test.snapshot })
      }
    }
  });
  runtime.$arguments = { threshold: 0 };

  const config = await runtime.__test.main(makeConfig());

  assert.ok(findGroup(config, "香港节点"));
});

test("fetch 响应正文悬挂时也触发硬超时", async () => {
  const runtime = createRuntime({
    fetch: async () => ({ ok: true, text: () => new Promise(() => {}) }),
    setTimeout: (callback) => {
      queueMicrotask(callback);
      return 1;
    },
    clearTimeout: () => {}
  });
  runtime.$arguments = { threshold: 0 };

  const config = await runtime.__test.main(makeConfig());

  assert.ok(findGroup(config, "香港节点"));
  assert.ok(runtime.logs.some(({ message }) => message.includes("fetch 超时")));
});

test("DNS 与 hosts 保留原始存在性和空值", async () => {
  const runtime = createRuntime({
    fetch: async () => ({ ok: true, text: async () => runtime.__test.snapshot })
  });
  runtime.$arguments = { threshold: 0 };
  const source = makeConfig();
  source.dns = false;
  source.hosts = null;

  const config = await runtime.__test.main(source);

  assert.equal(config.dns, false);
  assert.equal(config.hosts, null);
});

test("后处理保持幂等", async () => {
  const runtime = createRuntime({
    fetch: async () => ({ ok: true, text: async () => runtime.__test.snapshot })
  });
  runtime.$arguments = { threshold: 0 };

  const first = await runtime.__test.main(makeConfig());
  const second = await runtime.__test.main(first);

  for (const config of [first, second]) {
    assert.equal(config["proxy-groups"].filter((group) => group.name === "javdb").length, 1);
    assert.equal(config["proxy-groups"].filter((group) => group.name === "非香港节点").length, 0);
    assert.equal(config.rules.filter((rule) => rule === "DOMAIN-KEYWORD,javdb,javdb").length, 1);
    assert.equal(findGroup(config, "谷歌服务").proxies.filter((name) => name === "AI服务").length, 1);
    assert.equal(findGroup(config, "AI服务").type, "fallback");
  }
});

test("threshold 未显式传入时采用文档约定的 0", async () => {
  const runtime = createRuntime({
    fetch: async () => ({ ok: true, text: async () => runtime.__test.snapshot })
  });
  runtime.$arguments = {};

  const config = await runtime.__test.main({
    proxies: [{ name: "Hong Kong Only", type: "ss", server: "example.com", port: 443, cipher: "aes-128-gcm", password: "test" }]
  });

  assert.ok(findGroup(config, "香港节点"));
});
