// ==UserScript==
// @name         咸鱼助手-页面隔离绝对安全版(v16)
// @namespace    http://tampermonkey.net/
// @version      16.0
// @description  仅在可见的“自动发货”页面生效，只操作与标签关联的可见开关，开启后自动停止监听
// @match        *://44.81938193.xyz/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    const SWITCH_SELECTOR = '.el-switch, [role="switch"], input[type="checkbox"], [class*="switch"]';
    const SIDEBAR_SELECTOR = 'aside, nav, [class*="menu"], [class*="sidebar"], [class*="nav"]';
    const CLICK_COOLDOWN_MS = 3000;
    const MAX_LABEL_ANCESTORS = 4;

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

    function isInSidebar(el) {
        return Boolean(el.closest(SIDEBAR_SELECTOR));
    }

    function getVisibleLeafTextNodes(labelText) {
        return Array.from(document.querySelectorAll('div, span, p, label, h3')).filter(el => (
            el.children.length === 0 &&
            el.textContent.trim() === labelText &&
            !isInSidebar(el) &&
            isElementVisible(el)
        ));
    }

    function isAutoDeliveryPage() {
        return getVisibleLeafTextNodes('发货内容').length > 0;
    }

    function isSwitchCandidateVisible(sw) {
        if (sw.tagName === 'INPUT') {
            return isElementVisible(sw.closest('.el-switch, label') || sw);
        }
        return isElementVisible(sw);
    }

    function isSwitchDisabled(sw) {
        if (!sw) return false;
        if (sw.tagName === 'INPUT' && sw.disabled) return true;
        if (sw.getAttribute('aria-disabled') === 'true') return true;
        if (sw.classList.contains('is-disabled')) return true;
        return false;
    }

    function isSwitchOn(sw) {
        if (!sw) return false;

        if (sw.classList.contains('is-checked')) return true;
        if (sw.getAttribute('aria-checked') === 'true') return true;

        const input = sw.tagName === 'INPUT' ? sw : sw.querySelector('input[type="checkbox"]');
        if (input && input.checked) return true;

        const core = sw.querySelector('.el-switch__core') || (sw.classList.contains('el-switch') ? sw : null);
        if (core) {
            const bg = window.getComputedStyle(core).backgroundColor;
            const rgb = bg.match(/\d+/g);
            if (rgb && rgb.length >= 3) {
                const [r, g, b] = rgb.map(Number);
                const spread = Math.max(r, g, b) - Math.min(r, g, b);
                if (spread > 40 && (g > 100 || b > 100) && g > r + 20) {
                    return true;
                }
            }
        }

        return false;
    }

    function domDistance(a, b) {
        const aPath = [];
        for (let n = a; n; n = n.parentElement) aPath.push(n);

        const bPath = [];
        for (let n = b; n; n = n.parentElement) bPath.push(n);

        const aSet = new Set(aPath);
        const common = bPath.find(n => aSet.has(n));
        if (!common) return Number.POSITIVE_INFINITY;

        return aPath.indexOf(common) + bPath.indexOf(common);
    }

    function switchScore(sw, labelEl) {
        const labelRect = labelEl.getBoundingClientRect();
        const swHost = sw.tagName === 'INPUT' ? (sw.closest('.el-switch, label') || sw) : sw;
        const swRect = swHost.getBoundingClientRect();
        const horizontalGap = Math.abs(swRect.left - labelRect.right);
        const verticalGap = Math.abs(swRect.top - labelRect.top);
        return domDistance(sw, labelEl) * 1000 + horizontalGap + verticalGap;
    }

    function findSwitchesForLabel(labelEl) {
        const seen = new Set();
        const candidates = [];
        let scope = labelEl;

        for (let depth = 0; scope && scope !== document.body && depth < MAX_LABEL_ANCESTORS; depth += 1) {
            const found = scope.querySelectorAll(SWITCH_SELECTOR);
            for (const sw of found) {
                if (!seen.has(sw) && isSwitchCandidateVisible(sw)) {
                    seen.add(sw);
                    candidates.push(sw);
                }
            }
            scope = scope.parentElement;
        }

        candidates.sort((a, b) => switchScore(a, labelEl) - switchScore(b, labelEl));
        return candidates;
    }

    function ensureSwitchOn(labelText) {
        const labels = getVisibleLeafTextNodes(labelText);
        let sawDisabled = false;
        let sawWaiting = false;

        for (const labelEl of labels) {
            const switches = findSwitchesForLabel(labelEl);
            for (const sw of switches) {
                if (isSwitchDisabled(sw)) {
                    sawDisabled = true;
                    continue;
                }

                if (isSwitchOn(sw)) return { status: 'on' };

                const now = Date.now();
                const lastClick = Number(sw._lastClickTime || 0);
                if (now - lastClick < CLICK_COOLDOWN_MS) {
                    sawWaiting = true;
                    continue;
                }

                sw._lastClickTime = now;
                console.log(`[咸鱼助手] 开启【${labelText}】开关`);

                const target = sw.tagName === 'INPUT'
                    ? sw
                    : (sw.querySelector('input[type="checkbox"]') || sw.querySelector('.el-switch__core') || sw);
                target.click();
                return { status: 'clicked' };
            }
        }

        if (sawDisabled) return { status: 'disabled' };
        if (sawWaiting) return { status: 'waiting' };
        return { status: 'missing' };
    }

    function autoEnable() {
        if (!isAutoDeliveryPage()) return;

        const first = ensureSwitchOn('自动发货');
        if (first.status === 'disabled') {
            console.warn('[咸鱼助手] “自动发货”开关不可用，停止重试');
            clearInterval(timer);
            return;
        }
        if (first.status !== 'on') return;

        const second = ensureSwitchOn('自动确认发货');
        if (second.status === 'disabled') {
            console.warn('[咸鱼助手] “自动确认发货”开关不可用，停止重试');
            clearInterval(timer);
            return;
        }
        if (second.status === 'on') {
            console.log('[咸鱼助手] “自动发货”和“自动确认发货”均已开启，停止监听');
            clearInterval(timer);
        }
    }

    const timer = setInterval(autoEnable, 800);
    autoEnable();
})();
