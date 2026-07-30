// ==UserScript==
// @name         全网 Cloudflare Error1015 自动重试（改进版）
// @namespace    http://tampermonkey.net/
// @version      2.3
// @description  全网生效：检测到 Cloudflare Error 1015 限速时自动倒计时并刷新页面（带重试限制与取消按钮）
// @author       You
// @match        *://*/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    // ---------- Configuration ----------
    const WAIT_TIME = 10_000;              // 等待时间（毫秒）在刷新前倒计时
    const MAX_RETRIES = 5;                 // 在 RETRY_WINDOW 时间内允许的最大重试次数
    const RETRY_WINDOW = 60 * 60 * 1000;   // 重试窗口（毫秒），例如 1 小时
    const OBSERVE_DURATION = 5000;         // 对动态插入错误页观察的时长（毫秒）
    // 域名白名单/跳过（例如源码托管和开发站点，避免误报）
    const DOMAIN_SKIP = [
        'github.com',
        'raw.githubusercontent.com',
        'gist.github.com',
        'gitee.com',
        'gitlab.com',
        'stackoverflow.com',
    ];
    // 页面正文超过该阈值则视为“长页面”，常为代码/文档页面，跳过检测
    const LONG_PAGE_LENGTH = 5000;
    // -----------------------------------

    const HOST_KEY = `cf1015_retry_${location.hostname}`;
    const PAUSE_KEY = `${HOST_KEY}_paused`;
    const NOTICE_ID = 'cf1015-auto-retry-notice';

    function now() { return Date.now(); }

    function getRetryState() {
        try {
            const raw = sessionStorage.getItem(HOST_KEY);
            if (!raw) return { count: 0, first: 0 };
            const obj = JSON.parse(raw);
            if (!obj || typeof obj.count !== 'number' || typeof obj.first !== 'number') return { count: 0, first: 0 };
            // If first is too old, reset
            if (now() - obj.first > RETRY_WINDOW) return { count: 0, first: 0 };
            return obj;
        } catch (e) {
            console.warn('[Auto-Retry] 读取重试状态失败', e);
            return { count: 0, first: 0 };
        }
    }

    function recordRetry() {
        const s = getRetryState();
        if (s.count === 0) {
            s.count = 1;
            s.first = now();
        } else {
            s.count += 1;
        }
        try {
            sessionStorage.setItem(HOST_KEY, JSON.stringify(s));
        } catch (e) {
            console.warn('[Auto-Retry] 保存重试状态失败', e);
        }
    }

    function isPaused() {
        try {
            const raw = sessionStorage.getItem(PAUSE_KEY);
            if (!raw) return false;
            const ts = parseInt(raw, 10);
            if (isNaN(ts)) return false;
            // 如果被标记为暂停，暂停 1 小时（可按需修改）
            return now() - ts < RETRY_WINDOW;
        } catch {
            return false;
        }
    }

    function pauseRetries() {
        try {
            sessionStorage.setItem(PAUSE_KEY, String(now()));
        } catch (e) {
            console.warn('[Auto-Retry] 标记暂停失败', e);
        }
    }

    function resetRetries() {
        try {
            sessionStorage.removeItem(HOST_KEY);
        } catch (e) {
            /* ignore */
        }
    }

    function alreadyHasNotice() {
        return !!document.getElementById(NOTICE_ID);
    }

    function createNotice(text, remainingSeconds, onCancel) {
        if (!document.body) return null;
        // 如果已有提示，不重复创建
        if (alreadyHasNotice()) return document.getElementById(NOTICE_ID);

        const notice = document.createElement('div');
        notice.id = NOTICE_ID;
        notice.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #ff4d4f;
            color: #ffffff;
            text-align: center;
            padding: 12px 8px;
            font-size: 15px;
            font-weight: 600;
            z-index: 999999;
            box-shadow: 0 2px 12px rgba(0,0,0,0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        `;

        const span = document.createElement('span');
        span.style.flex = '1';
        span.innerText = `${text}，将在 ${remainingSeconds} 秒后自动刷新...`;

        const btn = document.createElement('button');
        btn.innerText = '取消';
        btn.title = '取消自动刷新并在本标签页暂停一段时间';
        btn.style.cssText = `
            background: rgba(0,0,0,0.08);
            border: none;
            color: #fff;
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 700;
        `;
        btn.addEventListener('click', () => {
            pauseRetries();
            if (typeof onCancel === 'function') onCancel();
            removeNotice();
            console.info('[Auto-Retry] 用户取消了自动刷新，本标签页已暂停重试。');
        });

        notice.appendChild(span);
        notice.appendChild(btn);

        // allow clicking the notice to dismiss quickly (but not pause)
        notice.addEventListener('click', (e) => {
            // avoid interfering with button click
            if (e.target === btn) return;
            removeNotice();
        });

        document.body.appendChild(notice);
        return notice;

        function removeNotice() {
            const n = document.getElementById(NOTICE_ID);
            if (n && n.parentNode) n.parentNode.removeChild(n);
        }
    }

    function removeNoticeIfExists() {
        const n = document.getElementById(NOTICE_ID);
        if (n && n.parentNode) n.parentNode.removeChild(n);
    }

    function isRateLimitedContent() {
        // 更严格的检测逻辑：
        // - 跳过已知的源码托管/开发域名（DOMAIN_SKIP）
        // - 跳过明显的代码/文档查看页或过长页面
        // - 仅在页面包含明确的“Error 1015”或明确表述限速（"you are being rate limited" / 中文短语）时认定为限速
        // 注意：不再把通用的 Cloudflare + Ray ID 作为自动判定的后备条件，避免把其他 Cloudflare 错误误判为 1015。
        try {
            const hostname = location.hostname || '';
            const lowerHost = hostname.toLowerCase();
            if (DOMAIN_SKIP.includes(lowerHost)) return false;

            const title = (document.title || '').toLowerCase();
            const docText = (document.body && document.body.innerText) ? document.body.innerText.toLowerCase() : (document.documentElement && document.documentElement.innerText ? document.documentElement.innerText.toLowerCase() : '');

            if (!title && !docText) return false;

            // 如果页面非常长，通常是代码/文档，不应触发（除非明确包含 Error 1015）
            if (docText.length > LONG_PAGE_LENGTH) {
                if (title.includes('error 1015') || docText.includes('error 1015') || docText.includes('you are being rate limited') || docText.includes('您已被限速') || docText.includes('已被限速')) {
                    return true;
                }
                return false;
            }

            // 如果页面包含代码查看器的标识，默认跳过（除非明确包含 Error 1015）
            if (document.querySelector('pre') || document.querySelector('.blob') || document.querySelector('.repository-content') || document.querySelector('.file')) {
                if (title.includes('error 1015') || docText.includes('error 1015') || docText.includes('you are being rate limited') || docText.includes('您已被限速') || docText.includes('已被限速')) {
                    return true;
                }
                return false;
            }

            // 解析页面中明确的错误代码（例如 "Error 1033"）并仅在遇到 1015 时触发
            const errCodeMatch = docText.match(/error\s*([0-9]{3,4})/i) || title.match(/error\s*([0-9]{3,4})/i);
            if (errCodeMatch && errCodeMatch[1]) {
                const code = errCodeMatch[1].trim();
                if (code === '1015') return true;
                // 不是 1015 则不是限速触发
                return false;
            }

            // 明确的限速短语（无错误码也可触发）
            if (docText.includes('you are being rate limited') || docText.includes('rate limited') || docText.includes('您已被限速') || docText.includes('已被限速')) {
                return true;
            }

            // 经典的 "Attention Required" 页面样式，但排除并非限速的其他 Cloudflare 错误
            if (title.includes('attention required') || docText.includes('please enable javascript and cookies') || docText.includes('are you human')) {
                // 这些通常用于挑战/验证码页，不一定表示 1015；只有当文本显式表明限速才触发
                if (docText.includes('rate limited') || docText.includes('you are being rate limited') || docText.includes('1015')) {
                    return true;
                }
            }
        } catch (e) {
            console.warn('[Auto-Retry] 检测内容时出错', e);
        }
        return false;
    }

    function attemptAutoRefresh() {
        if (isPaused()) {
            console.info('[Auto-Retry] 本标签页处于暂停状态，跳过自动刷新。');
            return;
        }

        const state = getRetryState();
        if (state.count >= MAX_RETRIES && state.first && (now() - state.first) < RETRY_WINDOW) {
            console.warn('[Auto-Retry] 达到最大重试次数，停止自动刷新。');
            createNotice('检测到 IP 限速 (Error 1015)，但已达到最大自动重试次数', 0, null);
            return;
        }

        let remainingSeconds = Math.ceil(WAIT_TIME / 1000);
        let timerId = null;
        let countdownId = null;

        const notice = createNotice('检测到 IP 限速 (Error 1015)', remainingSeconds, () => {
            // onCancel callback - clear timers
            if (timerId) clearTimeout(timerId);
            if (countdownId) clearInterval(countdownId);
        });

        // update countdown element
        const span = notice ? notice.querySelector('span') : null;
        countdownId = setInterval(() => {
            remainingSeconds--;
            if (span) span.innerText = `检测到 IP 限速 (Error 1015)，将在 ${remainingSeconds} 秒后自动刷新...`;
            if (remainingSeconds <= 0) {
                clearInterval(countdownId);
            }
        }, 1000);

        // Before we actually reload, record retry state (so reload loop protection works even if page refreshes right away)
        recordRetry();

        timerId = setTimeout(() => {
            console.info('[Auto-Retry] 时间到，刷新页面');
            try {
                location.reload();
            } catch (e) {
                console.warn('[Auto-Retry] 刷新失败，尝试设置 href', e);
                location.href = location.href;
            }
        }, WAIT_TIME);
    }

    // Run detection once, and also observe DOM changes for a short time for SPAs / dynamic content
    function handleRateLimitWithObserver() {
        try {
            if (isRateLimitedContent()) {
                console.warn('[Auto-Retry] 检测到疑似 Cloudflare 1015 页面');
                attemptAutoRefresh();
                return;
            }

            // Not detected now — set up MutationObserver for a short time in case the page is dynamic
            const start = now();
            const obs = new MutationObserver(() => {
                if (isRateLimitedContent()) {
                    obs.disconnect();
                    console.warn('[Auto-Retry] 在动态内容中检测到 Cloudflare 1015 页面');
                    attemptAutoRefresh();
                } else if (now() - start > OBSERVE_DURATION) {
                    // stop observing after the duration
                    obs.disconnect();
                }
            });

            if (document.body) {
                obs.observe(document.body, { childList: true, subtree: true });
                // stop observing after OBSERVE_DURATION
                setTimeout(() => obs.disconnect(), OBSERVE_DURATION);
            }
        } catch (e) {
            console.error('[Auto-Retry] 处理限速检测时异常', e);
        }
    }

    // Clear retry state if page looks normal (so future non-rate-limited visits can start fresh)
    function clearStateIfPageNormal() {
        try {
            if (!isRateLimitedContent()) {
                resetRetries();
                removeNoticeIfExists();
            }
        } catch {
            // ignore
        }
    }

    // Main
    try {
        // Only run on top-level window
        if (window.top !== window.self) {
            // in iframe - skip
            return;
        }

        // If page appears rate limited now, handle it
        handleRateLimitWithObserver();

        // On normal pages, clear previous retry state (optional)
        // Run once shortly after load to avoid clearing state if dynamic error shows up later (observer handles that)
        setTimeout(clearStateIfPageNormal, 1500);
    } catch (e) {
        console.error('[Auto-Retry] 脚本执行失败', e);
    }
})();
