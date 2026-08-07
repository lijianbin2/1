// ==UserScript==
// @name         全网 Cloudflare Error1015 自动重试（改进版）
// @namespace    http://tampermonkey.net/
// @version      2.8
// @description  全网生效：检测到 Cloudflare Error 1015 限速时自动每 10 秒重试 2 次并刷新页面（带暂停/立即重试/重置计数）
// @author       You
// @match        *://*/*
// @grant        none
// @run-at       document-end
// @noframes
// ==/UserScript==

(function () {
    'use strict';

    // ---------- Configuration ----------
    // 每次重试前固定等待 10 秒，共重试 2 次
    const WAIT_TIMES = [10, 10];
    const MAX_RETRIES = WAIT_TIMES.length;
    const RETRY_WINDOW = 60 * 60 * 1000;   // 重试窗口（毫秒），例如 1 小时
    const OBSERVE_DURATION = 5000;         // 对动态插入错误页观察的时长（毫秒）
    // 域名白名单：跳过（例如源码托管和开发站点，避免误报）
    const DOMAIN_SKIP = [
        'github.com',
        'raw.githubusercontent.com',
        'gist.github.com',
        'gitee.com',
        'gitlab.com',
        'stackoverflow.com',
    ];
    // 页面正文超过该阈值则视为"长页面"，通常是代码/文档页，仅凭限速短语不触发
    const LONG_PAGE_LENGTH = 5000;
    // -----------------------------------

    const HOST_KEY = `cf1015_retry_${location.hostname}`;
    const PAUSE_KEY = `${HOST_KEY}_paused`;
    const NOTICE_ID = 'cf1015-auto-retry-notice';

    const RATE_LIMIT_PHRASES = [
        'you are being rate limited',
        'rate limited',
        '您已被限速',
        '已被限速',
        '访问被限速',
    ];

    const active = {
        el: null,
        textEl: null,
        timeoutId: null,
        intervalId: null,
    };

    function now() {
        return Date.now();
    }

    function getRetryState() {
        try {
            const raw = sessionStorage.getItem(HOST_KEY);
            if (!raw) return { count: 0, first: 0 };
            const obj = JSON.parse(raw);
            if (!obj || typeof obj.count !== 'number' || typeof obj.first !== 'number') return { count: 0, first: 0 };
            // 超过重试窗口后重新计数
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
            if (Number.isNaN(ts)) return false;
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

    function unpauseRetries() {
        try {
            sessionStorage.removeItem(PAUSE_KEY);
        } catch (e) {
            console.warn('[Auto-Retry] 取消暂停失败', e);
        }
    }

    function resetRetries() {
        try {
            sessionStorage.removeItem(HOST_KEY);
        } catch (e) {
            /* ignore */
        }
    }

    function clearTimers() {
        if (active.timeoutId) {
            clearTimeout(active.timeoutId);
            active.timeoutId = null;
        }
        if (active.intervalId) {
            clearInterval(active.intervalId);
            active.intervalId = null;
        }
    }

    function removeNotice() {
        if (active.el && active.el.parentNode) {
            active.el.parentNode.removeChild(active.el);
        }
        active.el = null;
        active.textEl = null;
    }

    function showNotice({ title, message, buttons = [] }) {
        if (!document.body) return null;
        removeNotice();

        const notice = document.createElement('div');
        notice.id = NOTICE_ID;
        notice.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            box-sizing: border-box;
            background-color: #ff4d4f;
            color: #ffffff;
            padding: 10px 14px;
            font-size: 14px;
            font-weight: 600;
            z-index: 2147483647;
            box-shadow: 0 2px 12px rgba(0,0,0,0.35);
            text-align: center;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            max-width: 1200px;
            margin: 0 auto;
        `;

        const titleEl = document.createElement('strong');
        titleEl.textContent = title;
        titleEl.style.flexShrink = '0';

        const textEl = document.createElement('span');
        textEl.textContent = message;
        textEl.style.cssText = 'flex: 1 1 320px; min-width: 0; text-align: left;';

        const actions = document.createElement('span');
        actions.style.cssText = 'display: flex; gap: 8px; flex-shrink: 0;';

        for (const btn of buttons) {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = btn.label;
            button.title = btn.title || btn.label;
            button.style.cssText = `
                background: rgba(0,0,0,0.12);
                border: 1px solid rgba(255,255,255,0.35);
                color: #fff;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 700;
                line-height: 1.2;
            `;
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof btn.onClick === 'function') btn.onClick();
            });
            actions.appendChild(button);
        }

        content.appendChild(titleEl);
        content.appendChild(textEl);
        content.appendChild(actions);
        notice.appendChild(content);

        // 点击非按钮区域可关闭提示，但不停止倒计时
        notice.addEventListener('click', removeNotice);

        document.body.appendChild(notice);
        active.el = notice;
        active.textEl = textEl;
        return notice;
    }

    function reloadPage() {
        try {
            location.reload();
        } catch (e) {
            console.warn('[Auto-Retry] 刷新失败，尝试设置 href', e);
            location.href = location.href;
        }
    }

    function getElementText(selector) {
        const el = document.querySelector(selector);
        if (!el) return '';
        return (el.innerText || el.textContent || '').trim();
    }

    function isRateLimitedContent() {
        try {
            const hostname = (location.hostname || '').toLowerCase();
            if (DOMAIN_SKIP.includes(hostname)) return false;

            const title = (document.title || '').toLowerCase();
            const bodyText = document.body && document.body.innerText
                ? document.body.innerText
                : (document.documentElement ? document.documentElement.innerText || '' : '');
            const docText = bodyText.toLowerCase();
            const combined = `${title} ${docText}`;
            const cfCodeText = getElementText('.cf-error-code').toLowerCase();

            const hasExplicitError = /error\s*1015\b/.test(combined);
            const hasCodeElement = cfCodeText === '1015';
            const hasRatePhrase = RATE_LIMIT_PHRASES.some((phrase) => combined.includes(phrase));
            const hasAny1015 = /\b1015\b/.test(combined) || cfCodeText === '1015';
            const hasCfErrorDom = !!document.querySelector(
                '.cf-error-details, #cf-error-details, .cf-error-title, [class*="cf-error"]'
            );
            const isAttentionPage = title.includes('attention required') || hasCfErrorDom;
            const isShortPage = docText.length <= LONG_PAGE_LENGTH;

            // 明确出现 Error 1015 或 Cloudflare 错误码元素，直接判定
            if (hasExplicitError || hasCodeElement) return true;

            // 标准 CF 拦截页（Attention Required / cf-error 结构）
            if (isAttentionPage && (hasRatePhrase || hasAny1015)) return true;

            // 短页面出现明确的限速短语，且带有错误页特征
            if (
                hasRatePhrase &&
                isShortPage &&
                (isAttentionPage || title.includes('error') || title.includes('cloudflare') || hasAny1015)
            ) {
                return true;
            }

            // 长页面/代码文档页必须出现明确 Error 1015，避免误报
            return false;
        } catch (e) {
            console.warn('[Auto-Retry] 检测内容时出错', e);
        }
        return false;
    }

    function attemptAutoRefresh() {
        if (isPaused()) {
            console.info('[Auto-Retry] 本标签页处于暂停状态，跳过自动刷新');
            return;
        }

        // 同一页面已有提示时不再重复计数，避免多个脚本实例叠加
        if (document.getElementById(NOTICE_ID)) {
            console.info('[Auto-Retry] 已存在重试提示，避免重复计数');
            return;
        }

        const state = getRetryState();
        if (state.count >= MAX_RETRIES && state.first && now() - state.first < RETRY_WINDOW) {
            console.warn('[Auto-Retry] 已达到最大重试次数，停止自动刷新');
            clearTimers();
            showNotice({
                title: `已达到最大重试次数（${state.count}/${MAX_RETRIES}）`,
                message: '检测到 IP 限速（Cloudflare Error 1015），已停止自动刷新。可稍后手动重试。',
                buttons: [
                    {
                        label: '重置并重试',
                        title: '清除重试计数并立即刷新页面',
                        onClick: () => {
                            resetRetries();
                            unpauseRetries();
                            removeNotice();
                            reloadPage();
                        },
                    },
                    {
                        label: '暂停 1 小时',
                        title: '本标签页 1 小时内不再自动重试',
                        onClick: () => {
                            pauseRetries();
                            clearTimers();
                            removeNotice();
                        },
                    },
                ],
            });
            return;
        }

        const nextAttempt = state.count + 1;
        const waitMs = WAIT_TIMES[Math.min(nextAttempt - 1, WAIT_TIMES.length - 1)] * 1000;
        recordRetry();
        clearTimers();

        let remainingSeconds = Math.ceil(waitMs / 1000);
        const countdownText = (seconds) =>
            `检测到 IP 限速（Cloudflare Error 1015），将在 ${Math.max(seconds, 0)} 秒后自动刷新。`;

        showNotice({
            title: `第 ${nextAttempt}/${MAX_RETRIES} 次重试`,
            message: countdownText(remainingSeconds),
            buttons: [
                {
                    label: '立即重试',
                    title: '跳过等待，立即刷新页面',
                    onClick: () => {
                        clearTimers();
                        removeNotice();
                        reloadPage();
                    },
                },
                {
                    label: '暂停 1 小时',
                    title: '本标签页 1 小时内不再自动重试',
                    onClick: () => {
                        pauseRetries();
                        clearTimers();
                        removeNotice();
                    },
                },
            ],
        });

        active.intervalId = setInterval(() => {
            remainingSeconds -= 1;
            if (active.textEl) active.textEl.textContent = countdownText(remainingSeconds);
            if (remainingSeconds <= 0) clearInterval(active.intervalId);
        }, 1000);

        active.timeoutId = setTimeout(() => {
            console.info('[Auto-Retry] 时间到，刷新页面');
            clearTimers();
            removeNotice();
            reloadPage();
        }, waitMs);
    }

    function handleRateLimitWithObserver() {
        try {
            if (isRateLimitedContent()) {
                console.warn('[Auto-Retry] 检测到疑似 Cloudflare 1015 页面');
                attemptAutoRefresh();
                return;
            }

            // 页面可能是 SPA/动态插入错误内容，短暂观察 DOM 变化
            const start = now();
            const observer = new MutationObserver(() => {
                if (isRateLimitedContent()) {
                    observer.disconnect();
                    console.warn('[Auto-Retry] 在动态内容中检测到 Cloudflare 1015 页面');
                    attemptAutoRefresh();
                } else if (now() - start > OBSERVE_DURATION) {
                    observer.disconnect();
                }
            });

            if (document.body) {
                observer.observe(document.body, { childList: true, subtree: true });
                setTimeout(() => observer.disconnect(), OBSERVE_DURATION);
            }
        } catch (e) {
            console.error('[Auto-Retry] 处理限速检测时异常', e);
        }
    }

    function clearStateIfPageNormal() {
        try {
            if (!isRateLimitedContent()) {
                resetRetries();
                removeNotice();
            }
        } catch {
            /* ignore */
        }
    }

    // Main
    try {
        // 只处理顶层窗口
        if (window.top !== window.self) {
            return;
        }

        // 同一页面只允许一个脚本实例处理限速重试
        if (window.__cf1015AutoRetryHandled) {
            return;
        }
        window.__cf1015AutoRetryHandled = true;

        handleRateLimitWithObserver();

        // 正常页面短暂延迟后清除上一次的重试状态，避免污染下次访问
        setTimeout(clearStateIfPageNormal, 2000);
    } catch (e) {
        console.error('[Auto-Retry] 脚本执行失败', e);
    }
})();
