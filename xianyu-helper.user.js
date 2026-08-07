// ==UserScript==
// @name         咸鱼助手-页面隔离绝对安全版(v19)
// @namespace    http://tampermonkey.net/
// @version      19.0
// @description  打开仪表板后自动跳转商品页并点击同步闲鱼商品；在“自动发货”页面按容器精确定位开关，支持文本/卡密两种发货模式，持续轮询自动开启
// @match        *://44.81938193.xyz/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

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
    let lastDashboardRedirectAt = 0;
    let syncClicked = false;
    let syncSuccessObserver = null;
    let navigatedToAutoDelivery = false;

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
    }, POLL_INTERVAL_MS);
    autoSyncFromDashboard();
    autoClickSync();
    autoEnable();

    window.addEventListener('beforeunload', () => {
        clearInterval(timer);
    });
})();
