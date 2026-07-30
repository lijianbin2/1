// ==UserScript==
// @name         咸鱼助手-页面隔离绝对安全版(v15)
// @namespace    http://tampermonkey.net/
// @version      15.0
// @description  严格限制仅在“自动发货”页面和右侧主内容区生效，彻底杜绝误触侧边栏和其他页面开关
// @match        *://44.81938193.xyz/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // 1. 核心安全防护：判断当前是否真正处于“自动发货”面板
    function isAutoDeliveryPage() {
        // 检查右侧区域是否包含“自动发货”专有的“发货内容”标签
        const allTexts = document.querySelectorAll('div, span, p, label, h3');
        for (let el of allTexts) {
            if (el.children.length === 0 && el.textContent.trim() === '发货内容') {
                return true;
            }
        }
        return false;
    }

    // 2. 精准获取【右侧主内容区】指定文字右边的开关（排除侧边栏导航）
    function getSwitchAfterText(labelText) {
        // 抓取所有的文本节点，但严格排除侧边栏/导航菜单
        const allNodes = Array.from(document.querySelectorAll('div, span, label, p')).filter(el => {
            const isSidebar = el.closest('aside, nav, [class*="menu"], [class*="sidebar"], [class*="nav"]');
            return !isSidebar;
        });

        let textNode = allNodes.find(el => el.children.length === 0 && el.textContent.trim() === labelText);
        if (!textNode) return null;

        let curr = textNode;
        while (curr && curr !== document.body) {
            let sibling = curr.nextElementSibling;
            while (sibling) {
                const cls = String(sibling.className || '');
                if (cls.includes('switch') || sibling.getAttribute('role') === 'switch' || sibling.tagName === 'INPUT') {
                    return sibling;
                }
                const inner = sibling.querySelector('.el-switch, [role="switch"], input[type="checkbox"], [class*="switch"]');
                if (inner) return inner;

                sibling = sibling.nextElementSibling;
            }
            curr = curr.parentElement;
        }
        return null;
    }

    // 3. 判断开关是否变绿（已开启）
    function isSwitchOn(sw) {
        if (!sw) return false;

        if (sw.classList.contains('is-checked')) return true;
        if (sw.getAttribute('aria-checked') === 'true') return true;

        const input = sw.querySelector('input');
        if (input && input.checked) return true;

        const core = sw.querySelector('.el-switch__core') || sw;
        const bg = window.getComputedStyle(core).backgroundColor;
        const rgb = bg.match(/\d+/g);
        if (rgb && rgb.length >= 3) {
            const [r, g, b] = rgb.map(Number);
            if (g > 100 && g > r + 20) return true; // 绿色判定
        }

        return false;
    }

    // 4. 尝试开启某个开关
    function ensureSwitchOn(label) {
        const sw = getSwitchAfterText(label);
        if (!sw) return false;

        if (isSwitchOn(sw)) return true;

        const now = Date.now();
        const lastClick = Number(sw._lastClickTime || 0);

        // 3秒冷却保护，避免狂点
        if (now - lastClick > 3000) {
            sw._lastClickTime = now;
            console.log(`[咸鱼助手] 开启【${label}】开关`);

            const target = sw.querySelector('.el-switch__core') || sw.querySelector('input') || sw;
            target.click();
        }

        return false;
    }

    // 定时器
    setInterval(() => {
        // 第一道关卡：不在“自动发货”页面时直接休眠，绝不触碰任何按钮
        if (!isAutoDeliveryPage()) {
            return;
        }

        // 第二道关卡：顺序开启发货开关
        const isAutoDeliveryOn = ensureSwitchOn('自动发货');
        if (isAutoDeliveryOn) {
            ensureSwitchOn('自动确认发货');
        }
    }, 800);
})();
