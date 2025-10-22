// ==UserScript==
// @name         Auto Order (Modular)
// @namespace    http://tampermonkey.net/
// @version      6.0
// @description  Thin wrapper that loads the modular Tradovate automation driver and UI panel.
// @author       You
// @match        https://trader.tradovate.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const driverSource = __AUTO_DRIVER_BUNDLE__;
    const panelSource = __UI_PANEL_BUNDLE__;

    function inject(code, id) {
        if (!code) {
            console.warn(`[AutoOrder] No code supplied for ${id}, skipping injection.`);
            return;
        }

        const scriptId = `trado-${id}`;
        if (document.getElementById(scriptId)) {
            console.debug(`[AutoOrder] Script ${scriptId} already present, skipping duplicate injection.`);
            return;
        }

        const script = document.createElement('script');
        script.id = scriptId;
        script.type = 'text/javascript';
        script.textContent = code;
        document.head.appendChild(script);
        console.debug(`[AutoOrder] Injected ${id} bundle.`);
    }

    function waitForGlobal(name, timeout = 8000) {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            (function check() {
                if (window[name]) {
                    resolve(window[name]);
                    return;
                }
                if (Date.now() - start > timeout) {
                    reject(new Error(`${name} not available within ${timeout}ms`));
                    return;
                }
                requestAnimationFrame(check);
            })();
        });
    }

    inject(driverSource, 'auto-driver');
    inject(panelSource, 'ui-panel');

    Promise.all([
        waitForGlobal('TradoAuto'),
        waitForGlobal('TradoUIPanel')
    ]).then(([autoDriver, uiPanel]) => {
        try {
            autoDriver.init?.({ source: 'tampermonkey' });
        } catch (err) {
            console.error('[AutoOrder] Failed to init driver', err);
        }

        try {
            uiPanel.mount?.({ visible: true });
        } catch (err) {
            console.error('[AutoOrder] Failed to mount UI panel', err);
        }

        console.info('[AutoOrder] Driver and panel ready.');
    }).catch(err => {
        console.error('[AutoOrder] Initialization failed', err);
    });
})();
