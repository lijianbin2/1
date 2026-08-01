// ==UserScript==
// @name         JavDB 万能磁链提取器
// @namespace    http://tampermonkey.net/
// @version      5.7.2
// @description  JavDB 磁链批量提取：支持按当前列表、番号段、女优/组合三种模式抓取磁力链接；自动优先字幕版并选择最小体积，去重后导出迅雷专用 TXT；内置 429/封禁重试、备用域名自动切换与多标签排队保护。
// @author       Assistant
// @license      MIT
// @match        *://*.javdb574.com/*
// @match        *://javdb574.com/*
// @match        *://*.javdb*.*/*
// @match        *://javdb*.*/*
// @include      /^https?:\/\/(www\.)?javdb\d*\.(com|org|net)\/.*$/
// @grant        GM_xmlhttpRequest
// @grant        GM.xmlHttpRequest
// @connect      t.me
// @run-at       document-idle
// @noframes
// @downloadURL https://update.greasyfork.org/scripts/588177/JavDB%20%E4%B8%87%E8%83%BD%E7%A3%81%E9%93%BE%E6%8F%90%E5%8F%96%E5%99%A8.user.js
// @updateURL https://update.greasyfork.org/scripts/588177/JavDB%20%E4%B8%87%E8%83%BD%E7%A3%81%E9%93%BE%E6%8F%90%E5%8F%96%E5%99%A8.meta.js
// ==/UserScript==

(function () {
  'use strict';

  const origTitle = document.title;

  let isRunning = false;
  let shouldStop = false;
  let currentMode = 'current';

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

    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(QUEUE_PREFIX)) keys.push(key);
    }

    for (const key of keys) {
      if (key.endsWith('_time')) continue;
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
            logEl.innerHTML += `🔧 发现过期锁（${escapeHtml(currentLock)}），已回收。<br>`;
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
      const text = String(textStr).toLowerCase();
      if (
        text.includes('banned your access') ||
        text.includes('access denied') ||
        text.includes('ip banned') ||
        text.includes('ip blocked') ||
        text.includes('访问被拒绝') ||
        text.includes('訪問被拒絕') ||
        text.includes('已被封禁') ||
        text.includes('基于你的异常行为') ||
        text.includes('基於你的異常行為') ||
        text.includes('禁止了你的访问') ||
        text.includes('禁止了你的訪問')
      ) {
        return true;
      }
    }
    return false;
  }

  function gmGet(url) {
    return new Promise((resolve) => {
      const request = (typeof GM_xmlhttpRequest !== 'undefined' && GM_xmlhttpRequest) ||
        (typeof GM !== 'undefined' && GM.xmlHttpRequest) || null;
      if (!request) {
        resolve(null);
        return;
      }
      try {
        request({
          method: 'GET',
          url: url,
          timeout: 3000,
          onload: function (response) { resolve(response); },
          onerror: function () { resolve(null); },
          ontimeout: function () { resolve(null); }
        });
      } catch (e) {
        resolve(null);
      }
    });
  }

  async function fetchLatestDomainFromTG() {
    const response = await gmGet('https://t.me/s/javdbnews');
    if (!response || response.status !== 200) return null;
    const html = response.responseText || '';
    const matches = html.match(/javdb\d+\.com/gi);
    if (!matches || matches.length === 0) return null;
    const domainObjList = matches.map(d => {
      const numMatch = d.match(/\d+/);
      return {
        domain: d.toLowerCase(),
        num: numMatch ? parseInt(numMatch[0], 10) : 0
      };
    });
    domainObjList.sort((a, b) => b.num - a.num);
    return domainObjList[0].num > 0 ? domainObjList[0].domain : null;
  }

  async function triggerDomainJump(reason = '检测到拦截封禁') {
    removeFromQueue();
    document.title = origTitle;
    const currentHost = window.location.hostname.toLowerCase();
    const statusEl = document.getElementById('scraper-status');
    const logEl = document.getElementById('scraper-log');

    if (logEl) {
      logEl.innerHTML += `<br><span style="color:#ffcc00; font-weight:bold;">🚨 [${escapeHtml(reason)}] 触发封禁，立即自动切域名...</span><br>`;
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
      logEl.innerHTML += `✅ 锁定新域名: <b>${escapeHtml(targetDomain)}</b>，3秒后自动跳转复活...<br>`;
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
  const pageBodyText = document.body
    ? document.body.innerText
    : (document.documentElement ? document.documentElement.innerText : '');
  if (isBannedPage(200, pageBodyText)) {
    triggerDomainJump('访问被拦截');
    return;
  }

  const oldPanel = document.getElementById('javdb-scraper-panel');
  if (oldPanel) oldPanel.remove();

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
      <div style="font-size: 11px; color: #00ff66; line-height: 1.3;">
        🚀 极速冲刺模式：无休眠等待，遭遇封禁自动切号复活。
      </div>
    </div>

    <div id="section-code" style="display: none; flex-direction: column; gap: 6px; margin-bottom: 10px; font-size: 12px;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label for="scraper-prefix">番号前缀:</label>
        <input id="scraper-prefix" type="text" value="" style="width: 110px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 5px; border-radius: 3px;">
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label>数字范围:</label>
        <div style="display: flex; gap: 4px; align-items: center;">
          <input id="scraper-start" type="number" value="1" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
          <span>~</span>
          <input id="scraper-end" type="number" value="100" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
        </div>
      </div>
    </div>

    <div id="section-actor" style="display: none; flex-direction: column; gap: 6px; margin-bottom: 10px; font-size: 12px;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label for="scraper-actor">女优姓名:</label>
        <input id="scraper-actor" type="text" value="" style="width: 110px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 5px; border-radius: 3px;">
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label for="scraper-genre">类型/标签(选填):</label>
        <input id="scraper-genre" type="text" value="業餘" style="width: 110px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 5px; border-radius: 3px;">
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label>抓取页数:</label>
        <div style="display: flex; gap: 4px; align-items: center;">
          <input id="scraper-start-page" type="number" value="1" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
          <span>~</span>
          <input id="scraper-end-page" type="number" value="3" min="1" style="width: 48px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 4px; border-radius: 3px;">
        </div>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <label for="scraper-order">抓取顺序:</label>
        <select id="scraper-order" style="width: 110px; background: #333; color: #fff; border: 1px solid #555; padding: 2px 5px; border-radius: 3px;">
          <option value="new">新 ➔ 旧 (最新优先)</option>
          <option value="old">旧 ➔ 新 (早期优先)</option>
        </select>
      </div>
    </div>

    <div id="scraper-status" style="margin-bottom: 6px; color: #aaa; font-size: 12px;">状态: 准备就绪</div>
    <div id="scraper-progress" style="margin-bottom: 8px; font-weight: bold; color: #00d26a; font-size: 13px;">进度: - / -</div>

    <div style="display: flex; gap: 8px;">
      <button id="btn-start" style="flex: 1; padding: 6px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">开始抓取</button>
      <button id="btn-stop" style="flex: 1; padding: 6px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;" disabled>停止</button>
    </div>

    <div id="scraper-log" style="margin-top: 8px; height: 90px; overflow-y: auto; background: #1e1e1e; color: #00ff66; padding: 6px; font-family: monospace; font-size: 11px; border-radius: 4px;">
      🔥 极速版已就绪：延迟压缩至毫秒级...
    </div>
  `;

  Object.assign(panel.style, {
    position: 'fixed', bottom: '40px', right: '20px', zIndex: '999999', width: '260px',
    backgroundColor: '#222', color: '#fff', padding: '12px', borderRadius: '8px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.5)', fontFamily: 'sans-serif'
  });

  document.body.appendChild(panel);

  const header = document.getElementById('scraper-header');
  let isDragging = false, offsetX = 0, offsetY = 0;
  header.addEventListener('mousedown', (e) => {
    isDragging = true;
    offsetX = e.clientX - panel.offsetLeft; offsetY = e.clientY - panel.offsetTop;
    panel.style.bottom = 'auto'; panel.style.right = 'auto';
  });
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    panel.style.left = `${e.clientX - offsetX}px`; panel.style.top = `${e.clientY - offsetY}px`;
  });
  document.addEventListener('mouseup', () => { isDragging = false; });

  const secCurrent = document.getElementById('section-current');
  const secCode = document.getElementById('section-code');
  const secActor = document.getElementById('section-actor');
  document.querySelectorAll('input[name="scraper-mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      currentMode = e.target.value;
      secCurrent.style.display = currentMode === 'current' ? 'flex' : 'none';
      secCode.style.display = currentMode === 'code' ? 'flex' : 'none';
      secActor.style.display = currentMode === 'actor' ? 'flex' : 'none';
    });
  });

  const statusEl = document.getElementById('scraper-status');
  const progressEl = document.getElementById('scraper-progress');
  const logEl = document.getElementById('scraper-log');
  const btnStart = document.getElementById('btn-start');
  const btnStop = document.getElementById('btn-stop');

  function log(msg) {
    const time = new Date().toLocaleTimeString();
    logEl.innerHTML += `[${escapeHtml(time)}] ${escapeHtml(msg)}<br>`;
    logEl.scrollTop = logEl.scrollHeight;
  }

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const getRandomDelay = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  async function fetchWithRetry(url, label = '请求') {
    let lastStatus = 0;
    for (let attempt = 0; attempt <= 3; attempt++) {
      if (shouldStop) return null;
      updateLockHeartbeat();
      try {
        const res = await fetch(url);
        if (res.status !== 429) return res;
        lastStatus = 429;
      } catch (e) {
        lastStatus = -1;
      }
      if (attempt < 3) {
        const delay = Math.min(1500 * Math.pow(2, attempt), 15000) + getRandomDelay(0, 500);
        log(`⚠️ ${label}${lastStatus === 429 ? '触发限流' : '网络错误'}，约 ${Math.round(delay / 1000)} 秒后重试 (${attempt + 1}/3)...`);
        await sleep(delay);
      }
    }
    log(`⚠️ ${label}重试 3 次仍失败，已跳过`);
    return null;
  }

  function parseSizeToMB(sizeStr) {
    if (!sizeStr) return Infinity;
    const match = sizeStr.toUpperCase().match(/([\d\.]+)\s*(GB|MB|KB)/);
    if (!match) return Infinity;
    const num = parseFloat(match[1]);
    const unit = match[2];
    if (unit === 'GB') return num * 1024;
    if (unit === 'MB') return num;
    if (unit === 'KB') return num / 1024;
    return Infinity;
  }

  // resolve relative hrefs to absolute
  function toAbsoluteUrl(href) {
    try {
      return new URL(href, window.location.origin).toString();
    } catch (e) {
      return href;
    }
  }

  async function processDetailPage(movieHref, movieCode, genreTarget = '') {
    try {
      updateLockHeartbeat();
      const detailUrl = toAbsoluteUrl(movieHref);
      const detailRes = await fetchWithRetry(detailUrl, `详情页 ${movieCode} `);
      if (!detailRes) return null;

      const detailHtml = await detailRes.text();

      if (isBannedPage(detailRes.status, detailHtml)) {
        return 'IP_BANNED';
      }

      const parser = new DOMParser();
      const detailDoc = parser.parseFromString(detailHtml, 'text/html');

      if (genreTarget) {
        const genreLower = genreTarget.toLowerCase();
        const tagElements = detailDoc.querySelectorAll('a[href*="/tags/"], a[href*="/genres/"], .tags .button, .meta-value a, .panel-block a');
        let matched = false;
        tagElements.forEach(el => {
          const tagText = (el.textContent || '').trim().toLowerCase();
          if (tagText === genreLower || tagText.includes(genreLower)) matched = true;
        });

        if (!matched) {
          const infoPanel = detailDoc.querySelector('.movie-panel-info') || detailDoc.body;
          if (!(infoPanel.textContent || '').toLowerCase().includes(genreLower)) {
            log(`[-] ${movieCode} 不含标签 [${genreTarget}]，跳过`);
            return null;
          }
        }
      }

      const magnetItems = detailDoc.querySelectorAll('#magnets-content .item, #magnets-content tr');
      const magnetsData = [];

      magnetItems.forEach((mItem) => {
        const linkTag = mItem.querySelector('a[href^="magnet:?"]');
        if (!linkTag) return;

        const sizeTag = mItem.querySelector('.meta, .size') || mItem;
        const sizeText = sizeTag.textContent.trim();
        const fullText = (mItem.textContent || '').toUpperCase();

        const isSubbed = fullText.includes('字幕') || fullText.includes('-C.') || fullText.includes('-C-') || fullText.includes('中文');

        magnetsData.push({
          magnet: linkTag.getAttribute('href'),
          sizeText: sizeText,
          sizeMB: parseSizeToMB(sizeText),
          isSubbed: isSubbed
        });
      });

      if (magnetsData.length === 0) {
        log(`[-] ${movieCode} 无可用磁链`);
        return null;
      } else {
        const subbedList = magnetsData.filter(m => m.isSubbed);
        let targetList = subbedList.length > 0 ? subbedList : magnetsData;
        targetList.sort((a, b) => a.sizeMB - b.sizeMB);
        const chosen = targetList[0];

        if (subbedList.length > 0) {
          log(`[✓] ${movieCode} | 字幕版: ${chosen.sizeText}`);
        } else {
          log(`[✓] ${movieCode} | 无字幕: ${chosen.sizeText}`);
        }
        return chosen.magnet;
      }
    } catch (err) {
      log(`[!] ${movieCode} 详情页读取失败`);
      return null;
    }
  }

  // sanitize filename, trim length
  function sanitizeFileName(name) {
    try {
      let s = String(name || '')
        .replace(/[\/\\:\*\?"<>\|\u0000-\u001f]/g, '_')
        .replace(/\s+/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_+|_+$/g, '')
        .replace(/[. ]+$/g, '')
        .substring(0, 120);
      return s || 'javdb_export';
    } catch (e) {
      return 'javdb_export';
    }
  }

  async function runScraper() {
    isRunning = true; shouldStop = false;
    btnStart.disabled = true; btnStop.disabled = false;

    const lockAcquired = await acquireLock();
    if (!lockAcquired || shouldStop) {
      document.title = origTitle;
      statusEl.innerText = '状态: 已取消';
      btnStart.disabled = false; btnStop.disabled = true;
      isRunning = false;
      return;
    }

    document.title = `⚡[极速抓取中...] ${origTitle}`;
    statusEl.innerText = '状态: 正在极速抓取中...';
    const results = [];
    const parser = new DOMParser();

    try {
      if (currentMode === 'current') {
        const startPage = parseInt(document.getElementById('scraper-curr-start').value, 10) || 1;
        const endPage = parseInt(document.getElementById('scraper-curr-end').value, 10) || 1;
        const minPage = Math.min(startPage, endPage);
        const maxPage = Math.max(startPage, endPage);

        const baseObj = new URL(window.location.href);

        let domainJumped = false;
        for (let p = minPage; p <= maxPage; p++) {
          if (shouldStop || domainJumped) break;
          log(`提取当前列表 第 ${p} 页...`);

          baseObj.searchParams.set('page', p);
          const pageUrl = baseObj.toString();

          try {
            updateLockHeartbeat();
            const searchRes = await fetchWithRetry(pageUrl, `列表页 ${p} `);
            if (!searchRes) {
              if (shouldStop) break;
              continue;
            }

            const searchHtml = await searchRes.text();
            if (isBannedPage(searchRes.status, searchHtml)) {
              await triggerDomainJump('当前域名已遭封禁');
              domainJumped = true;
              break;
            }

            const searchDoc = parser.parseFromString(searchHtml, 'text/html');
            const movieNodeList = searchDoc.querySelectorAll('.movie-list .item');

            if (!movieNodeList || movieNodeList.length === 0) {
              log(`[-] 第 ${p} 页无作品或已到末尾`);
              continue;
            }

            const movieItems = Array.from(movieNodeList);

            for (let idx = 0; idx < movieItems.length; idx++) {
              if (shouldStop) break;
              const item = movieItems[idx];
              const aTag = item.querySelector('a');
              if (!aTag) continue;

              const movieHref = aTag.getAttribute('href');
              const codeEl = item.querySelector('.uid') || item.querySelector('strong');
              const movieCode = codeEl ? codeEl.textContent.trim() : `作品${idx + 1}`;

              progressEl.innerText = `进度: 页 ${p} (${idx + 1}/${movieItems.length})`;
              document.title = `⚡[抓取 ${p}页 ${idx + 1}/${movieItems.length}] ${origTitle}`;
              log(`提取中: ${movieCode}...`);

              await sleep(getRandomDelay(200, 400));
              const magnet = await processDetailPage(movieHref, movieCode);

              if (magnet === 'IP_BANNED') {
                await triggerDomainJump('抓取中遭遇域名拦截');
                domainJumped = true;
                break;
              }

              if (magnet) results.push(magnet);
              await sleep(getRandomDelay(300, 600)); // 极速抓取间隔
            }
          } catch (e) {
            log(`[!] 第 ${p} 页提取失败`);
          }
        }

        const pageTitle = sanitizeFileName(origTitle || 'JavDB_列表');
        if (results.length > 0) downloadTXT(results, sanitizeFileName(`${pageTitle}_当前列表_第${minPage}-${maxPage}页`));

      } else if (currentMode === 'code') {
        const rawPrefix = document.getElementById('scraper-prefix').value.trim().toUpperCase();
        const startNum = parseInt(document.getElementById('scraper-start').value, 10);
        const endNum = parseInt(document.getElementById('scraper-end').value, 10);

        if (!rawPrefix) { alert('请输入番号前缀！'); btnStart.disabled = false; btnStop.disabled = true; isRunning = false; removeFromQueue(); document.title = origTitle; return; }
        if (isNaN(startNum) || isNaN(endNum) || startNum > endNum) { alert('请检查正确的数字范围！'); btnStart.disabled = false; btnStop.disabled = true; isRunning = false; removeFromQueue(); document.title = origTitle; return; }

        const totalCount = endNum - startNum + 1;
        const purePrefix = rawPrefix.replace(/^\d+/, '');

        let domainJumped = false;
        for (let i = startNum; i <= endNum; i++) {
          if (shouldStop || domainJumped) break;

          const rawNumStr = String(i);
          const pad3Str = rawNumStr.padStart(3, '0');

          const searchTerms = [
            `${rawPrefix}-${pad3Str}`,
            `${rawPrefix}-${rawNumStr}`,
            `${rawPrefix}${pad3Str}`
          ];
          if (purePrefix && purePrefix !== rawPrefix) {
            searchTerms.push(`${purePrefix}-${pad3Str}`);
            searchTerms.push(`${purePrefix}-${rawNumStr}`);
          }

          const currentIdx = i - startNum + 1;
          progressEl.innerText = `进度: ${currentIdx} / ${totalCount} (${rawPrefix}-${pad3Str})`;
          document.title = `⚡[抓取 ${currentIdx}/${totalCount}] ${origTitle}`;
          log(`检索中: ${rawPrefix}-${pad3Str}...`);

          let targetMovieLink = null;

          for (const term of searchTerms) {
            if (shouldStop) break;
            try {
              updateLockHeartbeat();
              const searchRes = await fetchWithRetry(`/search?q=${encodeURIComponent(term)}&f=all`, '搜索 ');
              if (!searchRes) {
                if (shouldStop) break;
                continue;
              }

              const searchHtml = await searchRes.text();

              if (isBannedPage(searchRes.status, searchHtml)) {
                await triggerDomainJump('检索过程遭遇域名拦截');
                domainJumped = true;
                break;
              }

              const searchDoc = parser.parseFromString(searchHtml, 'text/html');
              const movieItems = searchDoc.querySelectorAll('.movie-list .item a');

              if (movieItems && movieItems.length > 0) {
                for (const item of movieItems) {
                  const text = ((item.textContent || '') + ' ' + (item.getAttribute('title') || '')).toUpperCase();
                  if (text.includes(term.toUpperCase()) || text.includes(`${rawPrefix}-${pad3Str}`)) {
                    targetMovieLink = item.getAttribute('href');
                    break;
                  }
                }
                if (!targetMovieLink && movieItems.length === 1) {
                  targetMovieLink = movieItems[0].getAttribute('href');
                }
              }

              if (targetMovieLink) break;
              await sleep(getRandomDelay(200, 400));
            } catch (e) {}
          }

          if (shouldStop || domainJumped) break;

          if (!targetMovieLink) {
            log(`[-] ${rawPrefix}-${pad3Str} 不存在/未录入`);
          } else {
            await sleep(getRandomDelay(200, 400));
            const absLink = toAbsoluteUrl(targetMovieLink);
            const magnet = await processDetailPage(absLink, `${rawPrefix}-${pad3Str}`);

            if (magnet === 'IP_BANNED') {
              await triggerDomainJump('抓取详情遭遇域名拦截');
              domainJumped = true;
              break;
            }

            if (magnet) results.push(magnet);
            await sleep(getRandomDelay(300, 600)); // 极速抓取间隔
          }
        }
        if (results.length > 0) downloadTXT(results, sanitizeFileName(`${rawPrefix}_${startNum}-${endNum}`));

      } else {
        const actorName = document.getElementById('scraper-actor').value.trim();
        const genreName = document.getElementById('scraper-genre').value.trim();
        let inputStartPage = parseInt(document.getElementById('scraper-start-page').value, 10);
        let inputEndPage = parseInt(document.getElementById('scraper-end-page').value, 10);
        const orderMode = document.getElementById('scraper-order').value;

        if (!actorName) { alert('请输入女优姓名！'); btnStart.disabled = false; btnStop.disabled = true; isRunning = false; removeFromQueue(); document.title = origTitle; return; }
        if (isNaN(inputStartPage) || isNaN(inputEndPage)) { alert('请检查正确的页码范围！'); btnStart.disabled = false; btnStop.disabled = true; isRunning = false; removeFromQueue(); document.title = origTitle; return; }

        const minPage = Math.min(inputStartPage, inputEndPage);
        const maxPage = Math.max(inputStartPage, inputEndPage);

        const pagesToVisit = [];
        if (orderMode === 'new') {
          for (let p = minPage; p <= maxPage; p++) pagesToVisit.push(p);
        } else {
          for (let p = maxPage; p >= minPage; p--) pagesToVisit.push(p);
        }

        let domainJumped = false;
        for (let pIdx = 0; pIdx < pagesToVisit.length; pIdx++) {
          if (shouldStop || domainJumped) break;
          const page = pagesToVisit[pIdx];
          log(`检索女优 [${actorName}] 第 ${page} 页...`);

          try {
            updateLockHeartbeat();
            const searchRes = await fetchWithRetry(`/search?q=${encodeURIComponent(actorName)}&page=${page}&f=all`, '检索 ');
            if (!searchRes) {
              if (shouldStop) break;
              continue;
            }

            const searchHtml = await searchRes.text();

            if (isBannedPage(searchRes.status, searchHtml)) {
              await triggerDomainJump('检索过程遭遇域名拦截');
              domainJumped = true;
              break;
            }

            const searchDoc = parser.parseFromString(searchHtml, 'text/html');
            const movieNodeList = searchDoc.querySelectorAll('.movie-list .item');

            if (!movieNodeList || movieNodeList.length === 0) { log(`[-] 第 ${page} 页无作品，跳过`); continue; }

            let movieItems = Array.from(movieNodeList);
            if (orderMode === 'old') movieItems.reverse();

            for (let idx = 0; idx < movieItems.length; idx++) {
              if (shouldStop) break;
              const item = movieItems[idx];
              const aTag = item.querySelector('a');
              if (!aTag) continue;

              const movieHref = aTag.getAttribute('href');
              const codeEl = item.querySelector('.uid') || item.querySelector('strong');
              const movieCode = codeEl ? codeEl.textContent.trim() : `作品${idx + 1}`;

              progressEl.innerText = `进度: 页 ${page} (${idx + 1}/${movieItems.length})`;
              document.title = `⚡[抓取 ${page}页 ${idx + 1}/${movieItems.length}] ${origTitle}`;
              log(`检查标签中: ${movieCode}...`);

              await sleep(getRandomDelay(200, 400));
              const magnet = await processDetailPage(movieHref, movieCode, genreName);

              if (magnet === 'IP_BANNED') {
                await triggerDomainJump('抓取详情遭遇域名拦截');
                domainJumped = true;
                break;
              }

              if (magnet) results.push(magnet);
              await sleep(getRandomDelay(300, 600)); // 极速抓取间隔
            }
          } catch (e) { log(`[!] 第 ${page} 页抓取失败`); }
        }

        const orderLabel = orderMode === 'new' ? '新到旧' : '旧到新';
        const fileLabel = genreName ? `${actorName}_${genreName}` : actorName;
        if (results.length > 0) downloadTXT(results, sanitizeFileName(`${fileLabel}_第${minPage}-${maxPage}页_${orderLabel}`));
      }
    } finally {
      document.title = origTitle;
      isRunning = false;
      removeFromQueue();
    }

    statusEl.style.color = '';
    statusEl.innerText = shouldStop ? '状态: 已手动停止' : '状态: 完成！';
    btnStart.disabled = false; btnStop.disabled = true;
  }

  function downloadTXT(magnets, fileNameTag) {
    const valid = [...new Set(magnets.filter(m => m && m.startsWith('magnet:?')))];
    if (valid.length === 0) { log('⚠️ 未抓取到有效磁链'); return; }

    const blob = new Blob([valid.join('\n')], { type: 'text/plain;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${fileNameTag}_迅雷专用.txt`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    log(`📁 导出成功：${fileNameTag}_迅雷专用.txt`);
  }

  btnStart.onclick = () => { if (!isRunning) runScraper(); };
  btnStop.onclick = () => { if (isRunning) { shouldStop = true; statusEl.innerText = '状态: 正在停止...'; } };

  const handleEnterKey = (e) => { if (e.key === 'Enter' && !isRunning) { e.preventDefault(); runScraper(); } };
  document.querySelectorAll('#javdb-scraper-panel input').forEach(input => {
    input.addEventListener('keydown', handleEnterKey);
  });
})();
