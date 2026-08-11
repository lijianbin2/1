// ==UserScript==
// @name         网页自动助手
// @namespace    http://tampermonkey.net/
// @version      20.5
// @description  打开仪表板后自动跳转商品页并点击同步闲鱼商品；在“自动发货”页面按容器精确定位开关，持续轮询自动开启，并自动打开最新商品；全网检测 Cloudflare Error 1015 限速并自动每 10 秒重试 2 次刷新
// @match        *://*/*
// @grant        none
// @run-at       document-idle
// @noframes
// ==/UserScript==

(function() {
    'use strict';

    // ===== 模块一：咸鱼助手自动操作（仅 44.81938193.xyz 生效） =====
    (function initXianyuHelper() {
        if (location.hostname !== '44.81938193.xyz') return;

    const PAGE_PATH = '/auto-delivery';
    const TOGGLE_CONTAINER_SELECTOR = '.ad__master-toggle, .ad__toggle-row';
    const PAGE_MARKER_SELECTOR = '.ad__master-toggles, .ad__config-panel';
    const CLICK_COOLDOWN_MS = 3000;
    const POLL_INTERVAL_MS = 800;
    const SYNC_BUTTON_SELECTOR = 'button.btn--primary.desktop-only';
    const SYNC_LABEL = '同步闲鱼商品';
    const AUTO_SYNC_QUERY = 'auto_sync';
    const SYNC_SUCCESS_TEXT = '商品数据刷新成功';
    const AUTO_DELIVERY_PATH = '/auto-delivery';
    const GOODS_ITEM_SELECTOR = '.ad__goods-item';
    const GOODS_LIST_SELECTOR = '.ad__goods-list';
    const GOODS_ACTIVE_CLASS = 'ad__goods-item--active';
    const GOODS_TOTAL_PATTERN = /^共\s*(\d+)\s*件$/;
    const GOODS_STABLE_MS = 1600;
    const GOODS_TOGGLE_SELECTOR = 'button.ad__goods-toggle';
    const GOODS_TOGGLE_EXPAND_TITLE = "展开商品列表";
    let lastDashboardRedirectAt = 0;
    let syncClicked = false;
    let syncSuccessObserver = null;
    let navigatedToAutoDelivery = false;
    let latestGoodsSelected = false;
    let lastGoodsCount = -1;
    let goodsCountStableAt = 0;

    function isElementVisible(el) {
        if (!el || !el.isConnected) return false;
        if (el.closest('[hidden], [aria-hidden="true"]')) return false;

        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) {
            return false;
        }

        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    function isAutoDeliveryPage() {
        if (location.pathname === PAGE_PATH) return true;
        return Boolean(document.querySelector(PAGE_MARKER_SELECTOR));
    }

    function isGoodsPage() {
        return location.pathname === '/goods';
    }

    function hasAutoSyncFlag() {
        return new URLSearchParams(location.search).get(AUTO_SYNC_QUERY) === '1';
    }

    function clearAutoSyncFlag() {
        const url = new URL(location.href);
        url.searchParams.delete(AUTO_SYNC_QUERY);
        history.replaceState(null, '', url.pathname + url.search + url.hash);
    }

    function getSyncButton() {
        const buttons = Array.from(document.querySelectorAll(SYNC_BUTTON_SELECTOR));
        return buttons.find(btn => isElementVisible(btn) && btn.textContent.includes(SYNC_LABEL)) || null;
    }

    function autoSyncFromDashboard() {
        if (location.pathname !== '/dashboard') return;
        if (Date.now() - lastDashboardRedirectAt < 5000) return;

        lastDashboardRedirectAt = Date.now();
        console.log('[咸鱼助手] 检测到仪表板，跳转到商品页同步闲鱼商品');
        location.href = '/goods?' + AUTO_SYNC_QUERY + '=1';
    }

    function autoClickSync() {
        if (!isGoodsPage() || !hasAutoSyncFlag() || syncClicked) return;

        const button = getSyncButton();
        if (!button) return;
        if (button.classList.contains('btn--loading')) {
            watchSyncSuccess();
            return;
        }
        if (button.disabled) return;

        syncClicked = true;
        clearAutoSyncFlag();
        console.log('[咸鱼助手] 自动点击“同步闲鱼商品”');
        button.click();
        watchSyncSuccess();
    }

    function isSyncSuccessMessage(el) {
        return el && el.children.length === 0 && el.textContent.trim() === SYNC_SUCCESS_TEXT;
    }

    function gotoAutoDelivery() {
        if (navigatedToAutoDelivery) return;
        navigatedToAutoDelivery = true;
        console.log('[咸鱼助手] 商品数据刷新成功，跳转到自动发货页面');
        location.href = AUTO_DELIVERY_PATH;
    }

    function watchSyncSuccess() {
        if (navigatedToAutoDelivery) return;

        const alreadyShown = Array.from(document.querySelectorAll('body *'))
            .some(isSyncSuccessMessage);
        if (alreadyShown) {
            gotoAutoDelivery();
            return;
        }
        if (syncSuccessObserver) return;

        syncSuccessObserver = new MutationObserver((mutations) => {
            const hit = mutations.some(mutation =>
                Array.from(mutation.addedNodes)
                    .filter(node => node.nodeType === Node.ELEMENT_NODE)
                    .flatMap(node => [node].concat(Array.from(node.querySelectorAll ? node.querySelectorAll('*') : [])))
                    .concat(mutation.target)
                    .some(isSyncSuccessMessage)
            );
            if (hit) {
                syncSuccessObserver.disconnect();
                syncSuccessObserver = null;
                gotoAutoDelivery();
            }
        });
        syncSuccessObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
    }

    function getGoodsItems() {
        return Array.from(document.querySelectorAll(GOODS_ITEM_SELECTOR)).filter(isElementVisible);
    }

    function getTotalGoodsCount() {
        const spans = Array.from(document.querySelectorAll('span'));
        for (const span of spans) {
            if (span.children.length !== 0) continue;
            const match = span.textContent.trim().match(GOODS_TOTAL_PATTERN);
            if (match) return parseInt(match[1], 10);
        }
        return 0;
    }

    function scrollGoodsListToBottom() {
        const list = document.querySelector(GOODS_LIST_SELECTOR);
        if (list) list.scrollTop = list.scrollHeight;
    }

    function expandGoodsPanelIfCollapsed() {
        const toggle = document.querySelector(GOODS_TOGGLE_SELECTOR);
        if (!toggle || !isElementVisible(toggle)) return false;
        if (toggle.title !== GOODS_TOGGLE_EXPAND_TITLE) return false;
        toggle.click();
        return true;
    }

    function autoSelectLatestGoods() {
        if (location.pathname !== AUTO_DELIVERY_PATH) {
            latestGoodsSelected = false;
            lastGoodsCount = -1;
            goodsCountStableAt = 0;
            return;
        }
        if (latestGoodsSelected) return;

        if (expandGoodsPanelIfCollapsed()) return;

        const items = getGoodsItems();
        if (items.length === 0) return;

        const total = getTotalGoodsCount();
        if (total > 0) {
            if (items.length < total) {
                scrollGoodsListToBottom();
                return;
            }
        } else {
            if (items.length !== lastGoodsCount) {
                lastGoodsCount = items.length;
                goodsCountStableAt = Date.now();
                scrollGoodsListToBottom();
                return;
            }
            if (Date.now() - goodsCountStableAt < GOODS_STABLE_MS) {
                scrollGoodsListToBottom();
                return;
            }
        }

        const last = items[items.length - 1];
        latestGoodsSelected = true;
        if (last.classList.contains(GOODS_ACTIVE_CLASS)) return;
        console.log("[咸鱼助手] 自动打开最新商品（列表最后一个）的配置");
        last.click();
    }

    function getMatchingToggleContainers(labelText) {
        const containers = Array.from(document.querySelectorAll(TOGGLE_CONTAINER_SELECTOR));
        const matches = [];

        for (const container of containers) {
            if (!isElementVisible(container)) continue;

            const label = container.querySelector('.ad__toggle-label');
            if (label && label.textContent.trim() === labelText) {
                matches.push(container);
                continue;
            }

            const ownText = Array.from(container.querySelectorAll('span, div, p'))
                .filter(el => el.children.length === 0)
                .map(el => el.textContent.trim())
                .find(text => text === labelText);
            if (ownText) matches.push(container);
        }

        return matches;
    }

    function getSwitchInput(container) {
        return container.querySelector('input[type="checkbox"]');
    }

    function isSwitchDisabled(input) {
        return Boolean(input && input.disabled);
    }

    function isSwitchOn(input) {
        return Boolean(input && input.checked);
    }

    function ensureSwitchOn(labelText) {
        const containers = getMatchingToggleContainers(labelText);
        if (containers.length === 0) return { status: 'missing' };

        let sawDisabled = false;
        let sawWaiting = false;

        for (const container of containers) {
            const input = getSwitchInput(container);
            if (!input) continue;

            if (isSwitchDisabled(input)) {
                sawDisabled = true;
                continue;
            }

            if (isSwitchOn(input)) return { status: 'on' };

            const now = Date.now();
            const lastClick = Number(input._xianyuHelperLastClick || 0);
            if (now - lastClick < CLICK_COOLDOWN_MS) {
                sawWaiting = true;
                continue;
            }

            input._xianyuHelperLastClick = now;
            console.log(`[咸鱼助手] 开启【${labelText}】开关`);
            input.click();
            return { status: 'clicked' };
        }

        if (sawDisabled) return { status: 'disabled' };
        if (sawWaiting) return { status: 'waiting' };
        return { status: 'missing' };
    }

    function autoEnable() {
        if (!isAutoDeliveryPage()) return;

        const master = ensureSwitchOn('自动发货');
        if (master.status === 'disabled') {
            console.warn('[咸鱼助手] “自动发货”开关不可用，等待重试');
            return;
        }
        if (master.status !== 'on') return;

        const confirm = ensureSwitchOn('自动确认发货');
        if (confirm.status === 'disabled') {
            console.warn('[咸鱼助手] “自动确认发货”开关不可用，等待重试');
            return;
        }
        if (confirm.status !== 'on') return;

        console.log('[咸鱼助手] “自动发货”和“自动确认发货”均已开启');
    }

    const timer = setInterval(() => {
        autoSyncFromDashboard();
        autoClickSync();
        autoEnable();
        autoSelectLatestGoods();
    }, POLL_INTERVAL_MS);
    autoSyncFromDashboard();
    autoClickSync();
    autoEnable();
    autoSelectLatestGoods();

    window.addEventListener('beforeunload', () => {
        clearInterval(timer);
    });
    })();

    // ===== 模块二：全网 Cloudflare Error 1015 自动重试 =====
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
})();
