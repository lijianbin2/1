// ==UserScript==
// @name         JavDB 万能磁链提取器
// @namespace    http://tampermonkey.net/
// @version      5.7.2
// @description  JavDB 磁链提取器：在 JavDB 页面提取磁力链接并导出为 TXT，可筛选字幕版、按番号或女优抓取。
// @author       Assistant
// @license      MIT
// @match        *://*.javdb574.com/*
// @match        *://javdb574.com/*
// @match        *://*.javdb*.*/*
// @match        *://javdb*.*/*
// @include      /^https?:\/\/(www\.)?javdb\d*\.(com|org|net)\/.*$/
// @grant        GM_xmlhttpRequest
// @connect      t.me
// ==/UserScript==

(function () {
  'use strict';

  const origTitle = document.title;

  function autoCheckRememberMe() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
      const parentText = cb.closest('label')?.textContent || cb.parentElement?.textContent || '';
      if (
        parentText.includes('七天') ||
        parentText.includes('保持') ||
        cb.name?.includes('remember') ||
        cb.id?.includes('remember')
      ) {
        if (!cb.checked) cb.checked = true;
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoCheckRememberMe);
  } else {
    autoCheckRememberMe();
  }

  // 🔒 独立时间戳分布式并发排队锁
  const QUEUE_PREFIX = 'javdb_q_';
  const LOCK_KEY = 'javdb_scraper_active_tab';
  const LOCK_TIME_KEY = LOCK_KEY + '_time';
  const LOCK_EXPIRY_MS = 20000; // 超过这个时间视为锁失效（20s）
  const TAB_ID = Math.random().toString(36).substring(2, 9);
  const MY_Q_KEY = QUEUE_PREFIX + TAB_ID;

  function registerInQueue() {
    try {
      if (!localStorage.getItem(MY_Q_KEY)) {
        localStorage.setItem(MY_Q_KEY, Date.now().toString());
      }
      localStorage.setItem(MY_Q_KEY + '_time', Date.now().toString());
    } catch (e) {
      // ignore storage errors
    }
  }

  function removeFromQueue() {
    try {
      localStorage.removeItem(MY_Q_KEY);
      localStorage.removeItem(MY_Q_KEY + '_time');
      if (localStorage.getItem(LOCK_KEY) === TAB_ID) {
        localStorage.removeItem(LOCK_KEY);
        localStorage.removeItem(LOCK_TIME_KEY);
      }
    } catch (e) {}
  }

  function isLockExpired() {
    try {
      const t = parseInt(localStorage.getItem(LOCK_TIME_KEY) || '0', 10);
      if (!t) return true;
      return (Date.now() - t) > LOCK_EXPIRY_MS;
    } catch (e) {
      return true;
    }
  }

  function getQueuePosition() {
    registerInQueue();
    const now = Date.now();
    const entries = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(QUEUE_PREFIX) && !key.endsWith('_time')) {
        const id = key.replace(QUEUE_PREFIX, '');
        const lastTime = parseInt(localStorage.getItem(key + '_time') || '0', 10);

        if (now - lastTime < 12000) {
          const regTime = parseInt(localStorage.getItem(key) || '0', 10);
          entries.push({ id, regTime });
        } else {
          // 清理过期队列项
          try {
            localStorage.removeItem(key);
            localStorage.removeItem(key + '_time');
          } catch (e) {}
        }
      }
    }

    entries.sort((a, b) => a.regTime - b.regTime);
    const myIdx = entries.findIndex(e => e.id === TAB_ID);
    if (myIdx === -1) return { pos: 1, total: entries.length + 1 };
    return { pos: myIdx + 1, total: entries.length };
  }

  async function acquireLock() {
    const statusEl = document.getElementById('scraper-status');
    const logEl = document.getElementById('scraper-log');

    while (true) {
      if (shouldStop) {
        removeFromQueue();
        return false;
      }

      // 如果已有锁但超过过期时间，则回收它
      const currentLock = localStorage.getItem(LOCK_KEY);
      if (currentLock && currentLock !== TAB_ID && isLockExpired()) {
        try {
          localStorage.removeItem(LOCK_KEY);
          localStorage.removeItem(LOCK_TIME_KEY);
          if (logEl) {
            logEl.innerHTML += `🔧 发现过期锁（${currentLock}），已回收。<br>`;
            logEl.scrollTop = logEl.scrollHeight;
          }
        } catch (e) {}
      }

      const { pos } = getQueuePosition();

      if (pos === 1) {
        try {
          localStorage.setItem(LOCK_KEY, TAB_ID);
          localStorage.setItem(LOCK_TIME_KEY, Date.now().toString());
        } catch (e) {}

        await sleep(100);

        if (localStorage.getItem(LOCK_KEY) === TAB_ID) return true;
      }

      const aheadCount = pos - 1;
      if (statusEl) statusEl.innerText = `⏳ 排队中 (前面还有 ${aheadCount} 个任务)...`;
      document.title = `⏳[排队第${pos}位] ${origTitle}`;

      if (logEl && !logEl.innerText.includes('排队等待')) {
        logEl.innerHTML += `⏳ 前方有 ${aheadCount} 个任务正在抓取，排队等待中...<br>`;
        logEl.scrollTop = logEl.scrollHeight;
      }

      await sleep(1500);
    }
  }

  function updateLockHeartbeat() {
    registerInQueue();
    try {
      if (localStorage.getItem(LOCK_KEY) === TAB_ID) {
        localStorage.setItem(LOCK_TIME_KEY, Date.now().toString());
      }
    } catch (e) {}
  }

  window.addEventListener('beforeunload', (e) => {
    if (isRunning) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  window.addEventListener('pagehide', () => {
    document.title = origTitle;
    removeFromQueue();
  });

  // 纯数字备用域名列表
  const STATIC_BACKUP_DOMAINS = [
    'javdb574.com', 'javdb573.com', 'javdb572.com',
    'javdb571.com', 'javdb570.com', 'javdb569.com'
  ];

  function isBannedPage(status, textStr) {
    if (status === 403) return true;
    if (textStr) {
      if (
        textStr.includes('banned your access') ||
        textStr.includes('基于你的异常行为') ||
        textStr.includes('基於你的異常行為') ||
        textStr.includes('禁止了你的访问') ||
        textStr.includes('禁止了你的訪問')
      ) {
        return true;
      }
    }
    return false;
  }

  function fetchLatestDomainFromTG() {
    return new Promise((resolve) => {
      if (typeof GM_xmlhttpRequest === 'undefined') {
        resolve(null);
        return;
      }
      GM_xmlhttpRequest({
        method: 'GET',
        url: 'https://t.me/s/javdbnews',
        timeout: 3000,
        onload: function (response) {
          if (response.status === 200) {
            const html = response.responseText;
            const matches = html.match(/javdb\d+\.com/gi);
            if (matches && matches.length > 0) {
              const domainObjList = matches.map(d => {
                const numMatch = d.match(/\d+/);
                return {
                  domain: d.toLowerCase(),
                  num: numMatch ? parseInt(numMatch[0], 10) : 0
                };
              });
              domainObjList.sort((a, b) => b.num - a.num);
              if (domainObjList.length > 0 && domainObjList[0].num > 0) {
                resolve(domainObjList[0].domain);
                return;
              }
            }
          }
          resolve(null);
        },
        onerror: function () { resolve(null); },
        ontimeout: function () { resolve(null); }
      });
    });
  }

  async function triggerDomainJump(reason = '检测到拦截封禁') {
    removeFromQueue();
    document.title = origTitle;
    const currentHost = window.location.hostname.toLowerCase();
    const statusEl = document.getElementById('scraper-status');
    const logEl = document.getElementById('scraper-log');

    if (logEl) {
      logEl.innerHTML += `<br><span style="color:#ffcc00; font-weight:bold;">🚨 [${reason}] 触发封禁，立即自动切域名...</span><br>`;
      logEl.scrollTop = logEl.scrollHeight;
    }
    if (statusEl) {
      statusEl.innerText = `🚨 正在切号复活中...`;
      statusEl.style.color = '#ffcc00';
    }

    // 优先从 TG 获取
    let targetDomain = await fetchLatestDomainFromTG();

    // 算号退回策略：向下递减 (574 ➔ 573 ➔ 572)
    if (!targetDomain || targetDomain === currentHost) {
      const match = currentHost.match(/javdb(\d+)\.com/);
      if (match) {
        const currNum = parseInt(match[1], 10);
        targetDomain = `javdb${Math.max(currNum - 1, 1)}.com`;
      } else {
        let currIdx = STATIC_BACKUP_DOMAINS.findIndex(d => currentHost.includes(d));
        let nextIdx = (currIdx + 1) % STATIC_BACKUP_DOMAINS.length;
        targetDomain = STATIC_BACKUP_DOMAINS[nextIdx];
      }
    }

    if (logEl) {
      logEl.innerHTML += `✅ 锁定新域名: <b>${targetDomain}</b>，3秒后自动跳转复活...<br>`;
      logEl.scrollTop = logEl.scrollHeight;
    }
    if (statusEl) {
      statusEl.innerText = `🔄 3秒后跳转至: ${targetDomain}`;
    }

    setTimeout(() => {
      try {
        const url = new URL(window.location.href);
        url.hostname = targetDomain;
        window.location.href = url.toString();
      } catch (e) {
        // fallback: try build origin + pathname
        window.location.href = `${window.location.protocol}//${targetDomain}${window.location.pathname}${window.location.search}${window.location.hash}`;
      }
    }, 2500);
  }

  // 页面入口即检查：若打开网页本身就是封禁页，立即触发切域名
  if (isBannedPage(200, document.body ? document.body.innerText : '')) {
    triggerDomainJump('访问被拦截');
    return;
  }

  const oldPanel = document.getElementById('javdb-scraper-panel');
  if (oldPanel) oldPanel.remove();

  let isRunning = false;
  let shouldStop = false;
  let currentMode = 'current';

  const panel = document.createElement('div');
  panel.id = 'javdb-scraper-panel';
  panel.innerHTML = `
    <div id="scraper-header" style="font-weight: bold; margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #444; padding-bottom: 4px; cursor: move; user-select: none; display: flex; justify-content: space-between; align-items: center;">
      <span>⚡ JavDB 磁链提取器 v5.7.2 (极速版)</span>
      <span style="font-size: 10px; color: #888;">(按住拖动)</span>
    </div>

    <div style="display: flex; gap: 6px; margin-bottom: 10px; font-size: 11px; justify-content: center; background: #2a2a2a; padding: 4px; border-radius: 4px;">
      <label style="cursor: pointer;"><input type="radio" name="scraper-mode" value="current" checked> 当前列表</label>
      <label style="cursor: pointer;"><input type="radio" name="scraper-mode" value="code"> 按番号段</label>
      <label style="cursor: pointer;"><input type="radio" name="scraper-mode" value="actor"> 女优/组合</label>
    </div>

    <div id="section-current" style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; font-size: 12px;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label>抓取页数:</label>
        <div style="display: flex; gap: 4px; align-items: center;">
          <input id="scraper-curr-start" type="number" value="1" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
          <span>~</span>
          <input id="scraper-curr-end" type="number" value="1" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
        </div>
      </div>

{