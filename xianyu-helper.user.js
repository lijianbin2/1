// ==UserScript==
// @name         咸鱼助手-页面隔离绝对安全版(v17)
// @namespace    http://tampermonkey.net/
// @version      17.0
// @description  仅在“自动发货”页面生效，按容器精确定位开关，支持文本/卡密两种发货模式，持续轮询自动开启
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

    const timer = setInterval(autoEnable, POLL_INTERVAL_MS);
    autoEnable();

    window.addEventListener('beforeunload', () => {
        clearInterval(timer);
    });
})();
