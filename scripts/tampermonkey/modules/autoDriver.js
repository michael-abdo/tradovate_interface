// ==UserScript==
// @name         Auto Order
// @namespace    http://tampermonkey.net/
// @version      5.3
// @description  Tampermonkey UI for bracket auto trades with TP/SL checkboxes
// @author       You
// @match        https://trader.tradovate.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/AutoOrder.user.js
// @downloadURL  http://localhost:8080/AutoOrder.user.js
// ==/UserScript==

import { createDriverStore } from './driverState.js';

(function () {
    const driverStore = window.TradoAutoState && typeof window.TradoAutoState.getState === 'function'
        ? window.TradoAutoState
        : createDriverStore();
    window.TradoAutoState = driverStore;
    const { getState: getDriverState, applyUpdate: updateDriverState, subscribe: subscribeDriverState } = driverStore;

    function coerceNumber(value, fallback = null) {
        const num = typeof value === 'string' ? parseFloat(value) : value;
        return Number.isFinite(num) ? num : fallback;
    }

    function readLegacyUiConfig() {
        const byId = (id) => {
            const el = document.getElementById(id);
            return el ? el.value : undefined;
        };
        const checked = (id) => {
            const el = document.getElementById(id);
            return el ? !!el.checked : undefined;
        };
        return {
            symbol: byId('symbolInput'),
            quantity: coerceNumber(byId('qtyInput')),
            tpTicks: coerceNumber(byId('tpInput')),
            slTicks: coerceNumber(byId('slInput')),
            tickSize: coerceNumber(byId('tickInput')),
            entryPrice: coerceNumber(byId('entryPriceInput')),
            tpPrice: coerceNumber(byId('tpPriceInput')),
            slPrice: coerceNumber(byId('slPriceInput')),
            tpEnabled: checked('tpCheckbox'),
            slEnabled: checked('slCheckbox')
        };
    }

    function resolveTradeConfig(overrides = {}, source = 'autoTrade-call') {
        const state = typeof getDriverState === 'function' ? getDriverState() : {};
        const legacy = readLegacyUiConfig();
        const merged = {
            ...legacy,
            ...state
        };

        const normalized = { ...merged };

        if (overrides.symbol) normalized.symbol = overrides.symbol;
        if (typeof overrides.quantity === 'number') normalized.quantity = overrides.quantity;
        if (typeof overrides.tpTicks === 'number') normalized.tpTicks = overrides.tpTicks;
        if (typeof overrides.slTicks === 'number') normalized.slTicks = overrides.slTicks;
        if (typeof overrides.tickSize === 'number') normalized.tickSize = overrides.tickSize;
        if (overrides.entryPrice != null) normalized.entryPrice = overrides.entryPrice;
        if (overrides.tpEnabled != null) normalized.tpEnabled = overrides.tpEnabled;
        if (overrides.slEnabled != null) normalized.slEnabled = overrides.slEnabled;
        if (overrides.tpPrice != null) normalized.tpPrice = overrides.tpPrice;
        if (overrides.slPrice != null) normalized.slPrice = overrides.slPrice;

        normalized.symbol = (normalized.symbol || 'NQ').toUpperCase();
        normalized.quantity = coerceNumber(normalized.quantity, 1);
        normalized.tpTicks = coerceNumber(normalized.tpTicks, 120);
        normalized.slTicks = coerceNumber(normalized.slTicks, 40);
        normalized.tickSize = coerceNumber(normalized.tickSize, 0.25);
        normalized.entryPrice = normalized.entryPrice != null ? coerceNumber(normalized.entryPrice) : null;
        normalized.tpPrice = normalized.tpPrice != null ? coerceNumber(normalized.tpPrice) : null;
        normalized.slPrice = normalized.slPrice != null ? coerceNumber(normalized.slPrice) : null;
        normalized.tpEnabled = typeof normalized.tpEnabled === 'boolean' ? normalized.tpEnabled : true;
        normalized.slEnabled = typeof normalized.slEnabled === 'boolean' ? normalized.slEnabled : true;
        normalized.lastSource = source;

        if (typeof updateDriverState === 'function') {
            updateDriverState(normalized, source);
        }

        return normalized;
    }

    function syncUiFromState(state) {
        if (!state) return;
        const assignValue = (id, value) => {
            const el = document.getElementById(id);
            if (!el) return;
            const next = value == null ? '' : value;
            if (el.value !== String(next)) {
                el.value = next;
            }
        };
        const assignChecked = (id, checked) => {
            const el = document.getElementById(id);
            if (!el || typeof checked !== 'boolean') return;
            if (el.checked !== checked) {
                el.checked = checked;
            }
        };
        assignValue('symbolInput', state.symbol);
        assignValue('qtyInput', state.quantity);
        assignValue('tpInput', state.tpTicks);
        assignValue('slInput', state.slTicks);
        assignValue('tickInput', state.tickSize);
        assignValue('entryPriceInput', state.entryPrice);
        assignValue('tpPriceInput', state.tpPrice);
        assignValue('slPriceInput', state.slPrice);
        assignChecked('tpCheckbox', state.tpEnabled);
        assignChecked('slCheckbox', state.slEnabled);
    }

    if (typeof subscribeDriverState === 'function') {
        subscribeDriverState(syncUiFromState);
    }


    const { createDriverStore } = window.TradoAutoState || {};

    'use strict';
    console.log('Auto Order script initialized');
    var debug = false;

    function delay(ms) {
        console.log(`Delaying for ${ms}ms`);
        return new Promise(resolve => setTimeout(resolve, ms));
    }

function createUI() {
    console.log('Creating UI');
    const storedTP   = localStorage.getItem('bracketTrade_tp')  || '120';
    const storedSL   = localStorage.getItem('bracketTrade_sl')  || '40';
    const storedQty  = localStorage.getItem('bracketTrade_qty') || '9';
    const storedTick = localStorage.getItem('bracketTrade_tick')|| '0.25';
    const storedSym  = localStorage.getItem('bracketTrade_symbol') || 'NQ';
    console.log(`Stored values: TP=${storedTP}, SL=${storedSL}, Qty=${storedQty}, Tick=${storedTick}, Symbol=${storedSym}`);

    const container = document.createElement('div');
    container.id = 'bracket-trade-box';
    Object.assign(container.style, {
        position: 'fixed',
        background: '#1e1e1e',
        border: '1px solid #444',
        padding: '12px',
        zIndex: '99999',
        boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
        borderRadius: '8px',
        color: '#fff',
        cursor: 'move',
        fontFamily: 'sans-serif',
        textAlign: 'center',
        width: '200px'
    });

    // restore box position
    const savedLeft = 0; //localStorage.getItem('bracketTradeBoxLeft') || 0;
    const savedTop  = 0; //localStorage.getItem('bracketTradeBoxTop') || 0;
    if (savedLeft && savedTop) { container.style.left = savedLeft; container.style.top = savedTop; }
    else { container.style.top = '20px'; container.style.right = '20px'; }

    container.innerHTML = `
    <!-- Header with Symbol -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-weight:bold;cursor:grab;">⠿ Bracket</span>
        <input type="text" id="symbolInput" value="${storedSym}"
            style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;"
            placeholder="Symbol" />
    </div>

    <!-- Hidden Tick Size Input -->
    <div id="tickContainer" style="display:none;margin-bottom:8px;">
        <label style="display:block;margin-bottom:4px;font-size:11px;">Tick Size</label>
        <input type="number" id="tickInput" step="0.01" value="${storedTick}"
            style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
    </div>

    <!-- Main Controls -->
    <div id="mainControls">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <input type="checkbox" id="tpCheckbox" checked />
            <div style="display:flex;gap:4px;flex:1;">
                <input type="number" id="tpInput" value="${storedTP}" step="1"
                    style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;"
                    placeholder="TP Ticks" />
                <input type="number" id="tpPriceInput" step="0.01"
                    style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;"
                    placeholder="TP Price" />
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <input type="checkbox" id="slCheckbox" checked />
            <div style="display:flex;gap:4px;flex:1;">
                <input type="number" id="slInput" value="${storedSL}" step="1"
                    style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;"
                    placeholder="SL Ticks" />
                <input type="number" id="slPriceInput" step="0.01"
                    style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;"
                    placeholder="SL Price" />
            </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:12px;">
            <button id="buyBtn"  style="padding:6px 10px;background:#2ecc71;color:#fff;border:none;border-radius:4px;font-weight:bold;">Buy</button>
            <div style="display:flex;flex-direction:column;gap:4px;">
                <input type="number" id="entryPriceInput" placeholder="Entry" step="1"
                    style="width:80px;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
                <input type="number" id="qtyInput" value="${storedQty}" min="1"
                    style="width:80px;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
            </div>
            <button id="sellBtn" style="padding:6px 10px;background:#e74c3c;color:#fff;border:none;border-radius:4px;font-weight:bold;">Sell</button>
        </div>
        <div style="display:flex;gap:10px;margin-bottom:2px;">
            <button id="cancelAllBtn" style="flex:1;padding:12px 8px;background:#e6b800;color:#000;border:none;border-radius:4px;font-weight:bold;">Cancel</button>
            <button id="closeAllBtn" style="flex:3;padding:12px 8px;background:#e74c3c;color:#fff;border:none;border-radius:4px;font-weight:bold;">Close All</button>
        </div>

        <!-- NEW: Breakeven button above Reverse -->
        <div style="display:flex;gap:10px;margin-top:6px;">
            <button id="breakevenBtn" style="flex:1;padding:12px 8px;background:#6c5ce7;color:#fff;border:none;border-radius:4px;font-weight:bold;">Breakeven</button>
        </div>

        <div style="display:flex;gap:10px;margin-top:6px;">
            <button id="reverseBtn" style="flex:1;padding:12px 8px;background:#ff6600;color:#fff;border:none;border-radius:4px;font-weight:bold;">Reverse</button>
        </div>
    </div>`;

    document.body.appendChild(container);
    console.log('UI container added to DOM');

    // === TRAY: Price quick-set (O / L / H / C / M) ===
    const tray = document.createElement('div');
    tray.id = 'bracket-trade-tray';
    Object.assign(tray.style, {
        position: 'fixed',
        top: container.style.top || '20px',
        left: '0px',
        background: '#24262b',
        border: '1px solid #444',
        padding: '10px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.4)',
        color: '#fff',
        width: '140px',
        zIndex: '99999',
        display: 'none'
    });

    tray.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div style="font-weight:600;">Price Tray</div>
        <button id="trayCloseBtn" title="Hide"
          style="background:#333;border:1px solid #555;color:#fff;border-radius:4px;padding:2px 6px;cursor:pointer;">×</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <button id="tray-btn-high"  style="padding:6px;border:1px solid #555;background:#2a2d34;color:#fff;border-radius:6px;text-align:left;">High</button>
        <button id="tray-btn-low"   style="padding:6px;border:1px solid #555;background:#2a2d34;color:#fff;border-radius:6px;text-align:left;">Low</button>
        <button id="tray-btn-open"  style="padding:6px;border:1px solid #555;background:#2a2d34;color:#fff;border-radius:6px;text-align:left;">Open</button>
        <button id="tray-btn-close" style="padding:6px;border:1px solid #555;background:#2a2d34;color:#fff;border-radius:6px;text-align:left;">Close</button>
        <button id="tray-btn-mid"   style="padding:6px;border:1px solid #555;background:#2a2d34;color:#fff;border-radius:6px;text-align:left;">Middle</button>
      </div>
    `;
    document.body.appendChild(tray);

    // Toggle tab on the right edge of the main container
    const trayTab = document.createElement('button');
    trayTab.id = 'trayToggle';
    trayTab.textContent = '◂ O/L/H/C/M';
    Object.assign(trayTab.style, {
        position: 'absolute',
        right: '-92px',
        top: '0',
        height: '32px',
        background: '#30343b',
        color: '#fff',
        border: '1px solid #444',
        borderRadius: '0 8px 8px 0',
        padding: '4px 8px',
        cursor: 'pointer'
    });
    container.appendChild(trayTab);

    function positionTray() {
        const r = container.getBoundingClientRect();
        tray.style.top = `${r.top}px`;
        tray.style.left = `${r.right + 8}px`;
    }
    positionTray();
    window.addEventListener('resize', positionTray);

    trayTab.addEventListener('click', () => {
        positionTray();
        tray.style.display = (tray.style.display === 'none') ? 'block' : 'none';
    });
    tray.querySelector('#trayCloseBtn')?.addEventListener('click', () => {
        tray.style.display = 'none';
    });

    // Cache for latest databox values (refreshed every 500ms)
    let latestBox = null;

    // helper: decimals based on tick input (e.g., 0.25 -> 2)
    function getTickDecimals() {
        const tick = (document.getElementById('tickInput')?.value || '').toString();
        const p = tick.indexOf('.');
        return p === -1 ? 0 : (tick.length - p - 1);
    }

    // Poll every 0.5s, keep labels simple; expose values via tooltip (including Mid)
    setInterval(() => {
        try {
            if (typeof extractTradovateDataBox === 'function') {
                latestBox = extractTradovateDataBox();
                if (latestBox) {
                    const map = {
                        open: ['tray-btn-open',  'Open'],
                        low:  ['tray-btn-low',   'Low'],
                        high: ['tray-btn-high',  'High'],
                        close:['tray-btn-close', 'Close']
                    };
                    for (const [k, [id, label]] of Object.entries(map)) {
                        const btn = document.getElementById(id);
                        if (!btn) continue;
                        const v = latestBox[k];
                        btn.title = v != null ? `${label}: ${v}` : `${label}: —`;
                    }

                    // Mid (O+C)/2 tooltip
                    const midBtn = document.getElementById('tray-btn-mid');
                    if (midBtn) {
                        const o = latestBox.open, c = latestBox.close;
                        if (typeof o === 'number' && typeof c === 'number') {
                            const dec = getTickDecimals();
                            const mid = ((o + c) / 2).toFixed(dec);
                            midBtn.title = `Mid (O+C)/2: ${mid}`;
                        } else {
                            midBtn.title = 'Mid (O+C)/2: —';
                        }
                    }
                }
                positionTray();
            }
        } catch(e) {
            console.warn('extractTradovateDataBox polling error:', e);
        }
    }, 500);

    function setEntry(value) {
        const input = document.getElementById('entryPriceInput');
        if (!input || value == null) return;
        const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setVal.call(input, value);
        ['input','change','blur'].forEach(ev =>
            input.dispatchEvent(new Event(ev, { bubbles: true }))
        );
    }

    function setEntryFromKey(key) {
        if (!latestBox || latestBox[key] == null) {
            console.warn(`No ${key} available from databox`);
            return;
        }
        setEntry(latestBox[key]);
    }

    function setEntryFromMidOC() {
        if (!latestBox || typeof latestBox.open !== 'number' || typeof latestBox.close !== 'number') {
            console.warn('Mid price unavailable (need open & close)');
            return;
        }
        const dec = getTickDecimals();
        const mid = ((latestBox.high + latestBox.low) / 2).toFixed(dec);
        setEntry(mid);
    }

    // Button bindings
    document.getElementById('tray-btn-open') ?.addEventListener('click', () => setEntryFromKey('open'));
    document.getElementById('tray-btn-low')  ?.addEventListener('click', () => setEntryFromKey('low'));
    document.getElementById('tray-btn-high') ?.addEventListener('click', () => setEntryFromKey('high'));
    document.getElementById('tray-btn-close')?.addEventListener('click', () => setEntryFromKey('close'));
    document.getElementById('tray-btn-mid')  ?.addEventListener('click', setEntryFromMidOC);

    // --- UI events ---
    console.log('Setting up UI event handlers');
    const slInput  = document.getElementById('slInput');
    const tpInput  = document.getElementById('tpInput');
    const qtyInput = document.getElementById('qtyInput');
    document.getElementById('slInput').addEventListener('input', () => {
        console.log(`SL input changed to: ${slInput.value}`);
        const slVal = parseFloat(slInput.value);
        if (!isNaN(slVal)) {
            tpInput.value = slVal * 3;
            console.log(`Calculated TP: ${tpInput.value} (SL × 3)`);
        }
        localStorage.setItem('bracketTrade_sl', slInput.value);
        localStorage.setItem('bracketTrade_tp', tpInput.value);
        if (typeof updateDriverState === 'function') {
            updateDriverState({
                slTicks: coerceNumber(slInput.value),
                tpTicks: coerceNumber(tpInput.value)
            }, 'floating-ui');
        }
    });
    tpInput.addEventListener('input', () => {
        console.log(`TP input changed to: ${tpInput.value}`);
        localStorage.setItem('bracketTrade_tp', tpInput.value);
        if (typeof updateDriverState === 'function') {
            updateDriverState({ tpTicks: coerceNumber(tpInput.value) }, 'floating-ui');
        }
    });
    document.getElementById('qtyInput').addEventListener('input', e => {
        console.log(`Quantity input changed to: ${e.target.value}`);
        localStorage.setItem('bracketTrade_qty', e.target.value);
        if (typeof updateDriverState === 'function') {
            updateDriverState({ quantity: coerceNumber(e.target.value, 1) }, 'floating-ui');
        }
    });

    const tpCheckbox = document.getElementById('tpCheckbox');
    tpCheckbox?.addEventListener('change', e => {
        if (typeof updateDriverState === 'function') {
            updateDriverState({ tpEnabled: !!e.target.checked }, 'floating-ui');
        }
    });

    const slCheckbox = document.getElementById('slCheckbox');
    slCheckbox?.addEventListener('change', e => {
        if (typeof updateDriverState === 'function') {
            updateDriverState({ slEnabled: !!e.target.checked }, 'floating-ui');
        }
    });

    const entryInput = document.getElementById('entryPriceInput');
    entryInput?.addEventListener('input', e => {
        if (typeof updateDriverState === 'function') {
            updateDriverState({ entryPrice: coerceNumber(e.target.value) }, 'floating-ui');
        }
    });

    const tpPriceInputEl = document.getElementById('tpPriceInput');
    tpPriceInputEl?.addEventListener('input', e => {
        if (typeof updateDriverState === 'function') {
            updateDriverState({ tpPrice: coerceNumber(e.target.value) }, 'floating-ui');
        }
    });

    const slPriceInputEl = document.getElementById('slPriceInput');
    slPriceInputEl?.addEventListener('input', e => {
        if (typeof updateDriverState === 'function') {
            updateDriverState({ slPrice: coerceNumber(e.target.value) }, 'floating-ui');
        }
    });
    document.getElementById('closeAllBtn').addEventListener('click', () => {
        console.log('Close All button clicked');
        try {
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const normalizedSymbol = normalizeSymbol(symbol);
            console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Exit at Mkt & Cxl option`);
            clickExitForSymbol(normalizedSymbol, 'cancel-option-Exit-at-Mkt-Cxl');
            console.log('Exit action triggered for symbol:', normalizedSymbol);
        } catch (err) {
            console.error("Close All operation failed:", err);
            try {
                console.log('Attempting fallback close method with danger buttons');
                document.getElementsByClassName("btn btn-danger")[0]?.click();
                setTimeout(() => {
                    document.getElementsByClassName("btn btn-danger")[1]?.click();
                    document.getElementsByClassName("btn btn-danger")[2]?.click();
                }, 200);
            } catch (fallbackErr) {
                console.error("Fallback close method also failed:", fallbackErr);
            }
        }
    });

    document.getElementById('cancelAllBtn').addEventListener('click', () => {
        console.log('Cancel All button clicked');
        try {
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const normalizedSymbol = normalizeSymbol(symbol);
            console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Cancel All option`);
            clickExitForSymbol(normalizedSymbol, 'cancel-option-Cancel-All');
            console.log('Cancel All action triggered for symbol:', normalizedSymbol);
        } catch (err) {
            console.error("Cancel All operation failed:", err);
        }
    });

    document.getElementById('reverseBtn').addEventListener('click', () => {
        console.log('Reverse Position button clicked');
        try {
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const normalizedSymbol = normalizeSymbol(symbol);
            console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Reverse & Cxl option`);
            clickExitForSymbol(normalizedSymbol, 'cancel-option-Reverse-Cxl');
            console.log('Reverse Position action triggered for symbol:', normalizedSymbol);
        } catch (err) {
            console.error("Reverse Position operation failed:", err);
        }
    });

    // --- NEW: Breakeven button handler ---
    document.getElementById('breakevenBtn').addEventListener('click', async () => {
        console.log('Breakeven button clicked');
        try {
            const symbolValue = document.getElementById('symbolInput').value || 'NQ';
            const normalizedSymbol = normalizeSymbol(symbolValue);
            console.log(`Breakeven for symbol: ${normalizedSymbol}`);

            // Find the module/header that matches this symbol
            const norm = s => (s||'').replace(/\s+/g,' ').trim().toUpperCase();
            const span = [...document.querySelectorAll('.contract-symbol span')]
              .find(s => {
                  const got = norm(s.textContent);
                  const want = norm(normalizedSymbol);
                  // allow root match (e.g., NQ* matches NQU5)
                  return got === want || got.startsWith(norm(symbolValue));
              });
            if (!span) return console.error('Breakeven: contract header not found');

            const rootContainer = span.closest('.gm-scroll-view') || span.closest('.header') || document;

            // Locate the "Position" column within this module
            const posCol = [...rootContainer.querySelectorAll('.info-column')]
              .find(col => /position/i.test(col.querySelector('small')?.textContent || ''));
            if (!posCol) {
                console.error('Breakeven: Position column not found');
                return;
            }

            // Extract qty and entry price like "1@23995.75"
            const numberEl = posCol.querySelector('.number');
            const qtySpan = numberEl?.querySelector('span');
            const rawText = (numberEl?.textContent || '').trim();
            const mPrice = rawText.match(/@([\d.,]+)/);
            if (!mPrice) {
                console.error('Breakeven: could not parse entry price from Position');
                return;
            }
            const entryPrice = parseFloat(mPrice[1].replace(/,/g,''));
            let qty = 1;
            if (qtySpan) {
                const q = parseFloat(qtySpan.textContent.replace(/[^\d.-]/g,''));
                if (!isNaN(q) && q !== 0) qty = Math.abs(q);
            }

            // Detect side: green (text-success) -> LONG, red (text-danger) -> SHORT
            let side = 'LONG';
            const cl = qtySpan?.classList || numberEl?.classList || { contains: ()=>false };
            if (cl.contains('text-danger')) side = 'SHORT';
            if (cl.contains('text-success')) side = 'LONG';

            const opposite = side === 'LONG' ? 'Sell' : 'Buy';
            console.log(`Breakeven detected: side=${side}, qty=${qty}, entry=${entryPrice}. Placing ${opposite} LIMIT at entry.`);

            // Temporarily disable TP/SL so we place ONLY a closing order
            const tpCb = document.getElementById('tpCheckbox');
            const slCb = document.getElementById('slCheckbox');
            const prevTP = tpCb.checked, prevSL = slCb.checked;
            tpCb.checked = false; slCb.checked = false;

            // Seed entry price + qty into our UI so autoTrade turns it into a LIMIT at that price
            const dec = (() => {
                const tick = parseFloat(document.getElementById('tickInput').value) || 0.25;
                const s = tick.toString();
                return s.includes('.') ? (s.length - s.indexOf('.') - 1) : 0;
            })();
            document.getElementById('entryPriceInput').value = entryPrice.toFixed(dec);
            document.getElementById('qtyInput').value = qty.toString();
            ['input','change','blur'].forEach(ev => {
                document.getElementById('entryPriceInput').dispatchEvent(new Event(ev,{bubbles:true}));
                document.getElementById('qtyInput').dispatchEvent(new Event(ev,{bubbles:true}));
            });

            // Execute opposite order at the same price (LIMIT/STOP chosen automatically by autoTrade)
            await autoTrade(symbolValue, qty, opposite, null, null, parseFloat(document.getElementById('tickInput').value)||0.25);

            // Restore TP/SL states and clear entry field
            tpCb.checked = prevTP; slCb.checked = prevSL;
            document.getElementById('entryPriceInput').value = '';
            ['input','change','blur'].forEach(ev =>
                document.getElementById('entryPriceInput').dispatchEvent(new Event(ev,{bubbles:true}))
            );
        } catch (err) {
            console.error('Breakeven action failed:', err);
        }
    });

    // Persist settings inputs
    console.log('Setting up persistent settings');
    document.getElementById('symbolInput').value = localStorage.getItem('bracketTrade_symbol') || 'NQ';
    document.getElementById('symbolInput').addEventListener('input', e => {
        const value = e.target.value;
        console.log(`Symbol input changed to: ${value}`);
        localStorage.setItem('bracketTrade_symbol', value);
        if (typeof updateDriverState === 'function') {
            updateDriverState({ symbol: value }, 'floating-ui');
        }
    });

    document.getElementById('symbolInput').addEventListener('change', e => {
        const symbolValue = e.target.value;
        const normalizedSymbol = normalizeSymbol(symbolValue);
        console.log(`Symbol changed to: ${symbolValue}, normalized: ${normalizedSymbol}`);

        const rootSymbol = symbolValue.replace(/[A-Z]\d+$/, '');
        const symbolDefaults = futuresTickData[rootSymbol];

        if (symbolDefaults) {
            console.log(`Found default values for ${rootSymbol}: SL=${symbolDefaults.defaultSL}, TP=${symbolDefaults.defaultTP}`);
            const slInput = document.getElementById('slInput');
            const tpInput = document.getElementById('tpInput');
            const tickInput = document.getElementById('tickInput');
            slInput.value = symbolDefaults.defaultSL;
            tpInput.value = symbolDefaults.defaultTP;
            if (typeof symbolDefaults.tickSize === 'number') {
                tickInput.value = symbolDefaults.tickSize;
                localStorage.setItem('bracketTrade_tick', symbolDefaults.tickSize);
                console.log(`Updated tick size to ${symbolDefaults.tickSize} for ${rootSymbol}`);
            }
            localStorage.setItem('bracketTrade_sl', symbolDefaults.defaultSL);
            localStorage.setItem('bracketTrade_tp', symbolDefaults.defaultTP);
            console.log(`Updated SL/TP to default values for ${rootSymbol}: SL=${slInput.value}, TP=${tpInput.value}`);
        }
        updateSymbol('.search-box--input', normalizedSymbol);
        if (typeof updateDriverState === 'function') {
            updateDriverState({
                symbol: normalizedSymbol,
                slTicks: symbolDefaults?.defaultSL,
                tpTicks: symbolDefaults?.defaultTP,
                tickSize: symbolDefaults?.tickSize
            }, 'floating-ui');
        }
    });

    document.getElementById('tickInput').value = localStorage.getItem('bracketTrade_tick') || '0.25';
    document.getElementById('tickInput').addEventListener('input', e => {
        console.log(`Tick size input changed to: ${e.target.value}`);
        localStorage.setItem('bracketTrade_tick', e.target.value);
        if (typeof updateDriverState === 'function') {
            updateDriverState({ tickSize: coerceNumber(e.target.value, 0.25) }, 'floating-ui');
        }
    });

    // --- Drag logic ---
    console.log('Setting up drag functionality');
    let isDragging = false, offsetX, offsetY;
    container.addEventListener('mousedown', e => {
        console.log('Container mousedown event detected');
        isDragging = true;
        offsetX = e.clientX - container.getBoundingClientRect().left;
        offsetY = e.clientY - container.getBoundingClientRect().top;
        console.log(`Drag started at offset X:${offsetX}, Y:${offsetY}`);
        container.style.cursor = 'grabbing';
    });
    document.addEventListener('mousemove', e => {
        if (isDragging) {
            const newLeft = `${e.clientX - offsetX}px`;
            const newTop = `${e.clientY - offsetY}px`;
            if (e.clientX % 20 === 0) {
                console.log(`Dragging panel to X:${newLeft}, Y:${newTop}`);
            }
            container.style.left = newLeft;
            container.style.top = newTop;
            container.style.right = 'unset';
            positionTray(); // keep tray aligned while dragging
        }
    });
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            console.log(`Container drop position: Left:${container.style.left}, Top:${container.style.top}`);
            localStorage.setItem('bracketTradeBoxLeft', container.style.left);
            localStorage.setItem('bracketTradeBoxTop', container.style.top);
        }
        isDragging = false;
        container.style.cursor = 'grab';
    });

    // Trade buttons
    console.log('Setting up trade buttons');
    document.getElementById('buyBtn').addEventListener('click', () => {
        console.log('BUY button clicked');
        const symbol = document.getElementById('symbolInput').value || 'NQ';
        const qty = +qtyInput.value;
        const tp = +tpInput.value;
        const sl = +slInput.value;
        const tickSize = +document.getElementById('tickInput').value;
        console.log(`Initiating BUY order: Symbol=${symbol}, Qty=${qty}, TP=${tp}, SL=${sl}, TickSize=${tickSize}`);
        autoTrade(symbol, qty, 'Buy', tp, sl, tickSize).finally(() => {
            document.getElementById('entryPriceInput').value = '';
            document.getElementById('tpPriceInput').value = '';
            document.getElementById('slPriceInput').value = '';
            console.log('Price inputs reset after BUY order');
        });
    });
    document.getElementById('sellBtn').addEventListener('click', () => {
        console.log('SELL button clicked');
        const symbol = document.getElementById('symbolInput').value || 'NQ';
        const qty = +qtyInput.value;
        const tp = +tpInput.value;
        const sl = +slInput.value;
        const tickSize = +document.getElementById('tickInput').value;
        console.log(`Initiating SELL order: Symbol=${symbol}, Qty=${qty}, TP=${tp}, SL=${sl}, TickSize=${tickSize}`);
        autoTrade(symbol, qty, 'Sell', tp, sl, tickSize).finally(() => {
            document.getElementById('entryPriceInput').value = '';
            document.getElementById('tpPriceInput').value = '';
            document.getElementById('slPriceInput').value = '';
            console.log('Price inputs reset after SELL order');
        });
    });
}





    async function clickExitForSymbol(symbol, actionIdOrAlias = 'cancel-option-Exit-at-Mkt-Cxl') {
        // Aliases supported for convenience
        const ALIAS_TO_ID = {
            exit:          'cancel-option-Exit-at-Mkt-Cxl',
            reverse:       'cancel-option-Reverse-Cxl',
            'cancel-all':  'cancel-option-Cancel-All',
            'cancel-bids': 'cancel-option-Cancel-Bids',
            'cancel-offers':'cancel-option-Cancel-Offers',
        };
        const ID_TO_LABEL_RE = {
            'cancel-option-Exit-at-Mkt-Cxl': /EXIT\s*AT\s*MKT/i,
            'cancel-option-Reverse-Cxl':     /REVERSE\s*&\s*CXL/i,
            'cancel-option-Cancel-All':      /CANCEL\s*ALL/i,
            'cancel-option-Cancel-Bids':     /CANCEL\s*BIDS/i,
            'cancel-option-Cancel-Offers':   /CANCEL\s*OFFERS/i,
        };

        const normalize = s => (s||'')
        .replace(/[\u2000-\u200F\u2028\u2029\u202F\u00A0]/g,' ')
        .replace(/\s+/g,' ')
        .trim()
        .toUpperCase();

        const wait = ms => new Promise(r => setTimeout(r, ms));
        async function waitFor(fn, {timeout=1200, interval=50}={}) {
            const t0 = performance.now();
            while (performance.now() - t0 < timeout) {
                const v = fn();
                if (v) return v;
                await wait(interval);
            }
            return null;
        }

        // Resolve target id
        const alias = actionIdOrAlias.toLowerCase();
        const wantId = ALIAS_TO_ID[alias] || actionIdOrAlias; // allow raw id
        const wantRe = ID_TO_LABEL_RE[wantId] || null;

        const wantSym = normalize(symbol);
        const isRoot  = /^[A-Z]{1,3}$/.test(wantSym);

        // Find the correct header/module
        const span = [...document.querySelectorAll('.header .contract-symbol span')]
        .find(s => {
            const got = normalize(s.textContent);
            return got === wantSym || (isRoot && got.startsWith(wantSym));
        });
        if (!span) { console.error('clickExitForSymbol: contract header not found'); return false; }
        const header  = span.closest('.header');
        const split   = header?.querySelector('.dropdown.btn-group.btn-split.btn-group-default');
        const primary = split?.querySelector('.btn.btn-default:not(.dropdown-toggle)');
        const toggle  = split?.querySelector('.dropdown-toggle.btn.btn-default');
        if (!split || !primary || !toggle) { console.error('clickExitForSymbol: split button not found'); return false; }

        const primaryMatches = () => wantRe ? wantRe.test(normalize(primary.textContent)) : false;

        // 1) If primary already shows desired action → click and done
        if (primaryMatches()) { primary.click(); return true; }

        // 2) Open dropdown
        toggle.dispatchEvent(new MouseEvent('click', {bubbles:true}));

        // 2a) Wait for ANY visible dropdown menu
        const getVisibleMenus = () => [...document.querySelectorAll('.dropdown-menu')]
        .filter(m => m.offsetParent !== null ||
                /display\s*:\s*block/i.test(m.getAttribute('style')||'') ||
                !!m.closest('.open'));
        let menus = await waitFor(getVisibleMenus, {timeout: 900, interval: 40});
        if (!menus || !menus.length) { console.error('clickExitForSymbol: dropdown menu not visible'); return false; }

        // 2b) Prefer the menu nearest the toggle button
        const tb = toggle.getBoundingClientRect();
        menus.sort((a,b)=>{
            const ar=a.getBoundingClientRect(), br=b.getBoundingClientRect();
            const da=Math.hypot(ar.left-tb.left, ar.top-tb.bottom);
            const db=Math.hypot(br.left-tb.left, br.top-tb.bottom);
            return da-db;
        });
        let menu = menus[0];

        // 2c) Try to find the item by ID *globally* (Tradovate may attach menus to portals)
        let item = document.getElementById(wantId);

        // If not found by ID, try by text inside any visible menu
        if (!item && wantRe) {
            for (const m of menus) {
                item = [...m.querySelectorAll('a[role="menuitem"], a, button, li, span')]
                    .find(el => wantRe.test(normalize(el.textContent)));
                if (item) { menu = m; break; }
            }
        }
        if (!item) { console.error('clickExitForSymbol: desired menu item not found'); return false; }

        // 2d) Click the menu item
        const clickable = item.tagName ? (item.matches('a,button') ? item : (item.querySelector('a,button') || item)) : item;
        ['mousedown','mouseup','click'].forEach(type =>
                                                clickable.dispatchEvent(new MouseEvent(type, {bubbles:true}))
                                               );


        // Fallback: brief re-open & re-select once
        toggle.click();
        await wait(120);
        menus = getVisibleMenus();
        item = document.getElementById(wantId) ||
            (wantRe ? menus?.flatMap(m=>[...m.querySelectorAll('a[role="menuitem"], a, button, li, span')])
             .find(el => wantRe.test(normalize(el.textContent))) : null);
        if (item) {
            ['mousedown','mouseup','click'].forEach(type =>
                                                    (item.querySelector('a,button')||item).dispatchEvent(new MouseEvent(type, {bubbles:true}))
                                                   );
            await wait(80);
            primary.click();
            return true;
        }

        console.error('clickExitForSymbol: primary did not update; giving up');
        return false;
    }

function extractTradovateDataBox(doc = document) {
  // Finds the first visible Tradovate "databox" and returns a parsed object of its values.
  const box = [...doc.querySelectorAll('.databox.react-draggable.react-resizable')]
    .find(el => el.offsetParent !== null);
  if (!box) return null;

  const getText = (sel, el = box) => {
    const n = el.querySelector(sel);
    return n ? n.textContent.trim() : null;
  };

  const title = getText('.header .title'); // e.g., "09/11/2025 08:41"
  const out = { timestamp: title || null };

  // Map <li> label -> desc
  const items = box.querySelectorAll('.gm-scroll-view .entries li');
  items.forEach(li => {
    const labelEl = li.querySelector('.label');
    const valEl = li.querySelector('.desc');
    if (!labelEl || !valEl) return;

    // Robustly extract pure label text (e.g., "low" even if the "❚" indicator span exists)
    const labelClone = labelEl.cloneNode(true);
    labelClone.querySelectorAll('span').forEach(s => s.remove());
    const keyRaw = (labelClone.textContent || '')
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]/g, ''); // strip any non-alphanumerics like "❚"

    const valRaw = (valEl.textContent || '').trim();

    // normalize keys
    const keyMap = {
      open: 'open',
      high: 'high',
      low: 'low',
      close: 'close',
      volume: 'volume',
      atr: 'atr',
      vwap: 'vwap',
      upperband1: 'upperBand1',
      lowerband1: 'lowerBand1',
      upperband2: 'upperBand2',
      lowerband2: 'lowerBand2'
    };
    const key = keyMap[keyRaw] || keyRaw;

    // parse numbers (volume integer, others float)
    let v = valRaw.replace(/,/g, '');
    if (key === 'volume') {
      v = Number.parseInt(v, 10);
    } else {
      v = Number.parseFloat(v);
    }
    out[key] = Number.isNaN(v) ? valRaw : v;
  });

  return out;
}






    document.querySelectorAll('#bracket-trade-box, #bracket-trade-tray').forEach(el => el.remove());
createUI();
console.log('UI creation complete');

async function updateSymbol(selector, value) {
            console.log(`updateSymbol called with selector: "${selector}", value: "${value}"`);
            const inputs = document.querySelectorAll(selector);
            console.log(`Found ${inputs.length} matching inputs`);
            const input = inputs[1] || inputs[0];
            if (!input) {
                console.error('No matching input elements found!');
                return;
            }
            console.log('Selected input:', input);

            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            const fireKey = type =>
                input.dispatchEvent(new KeyboardEvent(type, {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
                    bubbles: true, cancelable: true
                }));

            console.log('Clearing input field');
            /* clear */
            setVal.call(input, '');
            input.focus();
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await delay(400);

            console.log(`Setting input value to: "${value}"`);
            /* set new text */
            setVal.call(input, value);
            input.focus();                      // Tradovate needs focus for key events
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await delay(900);

            console.log('Simulating Enter key press');
            /* simulate Enter */
            ['keydown', 'keypress', 'keyup'].forEach(fireKey);
            input.dispatchEvent(new Event('change', { bubbles: true }));  // fallback
            console.log('Symbol update complete');
    }

    async function updatePrice(value) {
        // wait for the visible price box
        const selector = 'input.form-control';   // unique to the price field
        for (let i = 0; i < 20; i++) {                           // ~2 s timeout
            const input = document.querySelector(selector);
            if (input && input.offsetParent) {                   // visible?
                const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
                setVal.call(input, value);
                ['input','change','blur'].forEach(ev =>
                    input.dispatchEvent(new Event(ev,{bubbles:true})));
                await delay(300);                                // give Tradovate time to bind
                return;
            }
            await delay(100);
        }
        console.error('Price input not found');
    }

    // ── NEW: root-symbol → front-quarter (uses MONTH_CODES helpers you added) ──
    function normalizeSymbol(s) {
        console.log(`normalizeSymbol called with: "${s}"`);
        const isRootSymbol = /^[A-Z]{1,3}$/.test(s);
        console.log(`Is root symbol: ${isRootSymbol}`);
        const result = isRootSymbol ? getFrontQuarter(s) : s.toUpperCase();
        console.log(`Normalized symbol: "${result}"`);
        return result;
    }


    async function createBracketOrdersManual(tradeData) {
        console.log('Creating bracket orders with data:', tradeData);
        const enableTP = typeof tradeData.tpEnabled === 'boolean'
            ? tradeData.tpEnabled
            : (document.getElementById('tpCheckbox')?.checked ?? true);
        const enableSL = typeof tradeData.slEnabled === 'boolean'
            ? tradeData.slEnabled
            : (document.getElementById('slCheckbox')?.checked ?? true);
        console.log(`TP enabled: ${enableTP}, SL enabled: ${enableSL}`);

        // DO NOT UNDER ANY CIRCUMSTANCES UPDATE THIS FUNCTION
        async function updateInputValue(selector, value) {
            // scope to the visible, active trading ticket
            const ticket = [...document.querySelectorAll('.trading-ticket')]
            .find(t => t.offsetParent);
            if (!ticket) return console.error('No visible trading ticket');

            // find a live, enabled input matching selector inside this ticket
            let input;
            for (let i = 0; i < 25; i++) {
                input = [...ticket.querySelectorAll(selector)]
                    .find(el => el.offsetParent && !el.disabled);
                if (input) break;
                await delay(100);
            }
            if (!input) return console.error(`No live input for ${selector}`);

            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;

            // Special handling for Tradovate combobox: seed when empty so it accepts typing
            const isCombo = input.closest('.select-input.combobox');
            if (isCombo && !input.value) {
                // open dropdown and click the first item to "activate" the field
                const btn = isCombo.querySelector('.btn');
                btn?.click();
                await delay(150);
                const first = isCombo.querySelector('.dropdown-menu li');
                first?.click();
                await delay(150);
            }

            // write-verify loop with Enter to commit
            for (let tries = 0; tries < 3; tries++) {
                input.focus();
                setVal.call(input, value);
                input.dispatchEvent(new Event('input',  { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                }));
                input.blur();
                await delay(250);
                if (`${input.value}`.trim() === `${value}`) break;
            }
        }



        async function setCommonFields() {
            console.log('Setting common order fields');
            //if (tradeData.symbol) await updateSymbol('.search-box--input', normalizeSymbol(tradeData.symbol));
            if (tradeData.action) {
                console.log(`Setting action to: ${tradeData.action}`);
                const actionLabels = document.querySelectorAll('.radio-group.btn-group label');
                console.log(`Found ${actionLabels.length} action labels`);
                actionLabels.forEach(lbl => {
                    if (lbl.textContent.trim() === tradeData.action) {
                        console.log(`Clicking ${tradeData.action} label`);
                        lbl.click();
                    }
                });
            }
            if (tradeData.qty) {
                console.log(`Setting quantity to: ${tradeData.qty}`);
                await updateInputValue('.select-input.combobox input', tradeData.qty);
            }
        }

        function clickPriceArrow(direction = 'up') {
          const wrapper = document.querySelector('.numeric-input-value-controls');
          if (!wrapper) return;

          const target = wrapper.querySelector(
            direction === 'up' ? '.numeric-input-increment' : '.numeric-input-decrement'
          );
          target?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }

        async function submitOrder(orderType, priceValue) {
            await setCommonFields();

            const typeSel = document.querySelector('.group.order-type .select-input div[tabindex]');
            typeSel?.click();
            [...document.querySelectorAll('ul.dropdown-menu li')]
                .find(li => li.textContent.trim() === orderType)
                ?.click();

            //await delay(400);               // NEW - let Tradovate draw the price box

            if (priceValue) {
                await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);
            }

            document.querySelector('.btn-group .btn-primary')?.click();
            await delay(200);
            console.log(getOrderEvents());
            document.querySelector('.icon.icon-back')?.click();
            await delay(200);
        }

        console.log(`Submitting initial ${tradeData.orderType || 'MARKET'} order`);
        await submitOrder(tradeData.orderType || 'MARKET', tradeData.entryPrice);

        if (tradeData.action === 'Buy') {
            console.log('Flipping action to Sell for TP/SL orders');
            tradeData.action = 'Sell';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                await submitOrder('LIMIT', tradeData.takeProfit);
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                await submitOrder('STOP', tradeData.stopLoss);
            }
        } else {
            console.log('Flipping action to Buy for TP/SL orders');
            tradeData.action = 'Buy';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                await submitOrder('LIMIT', tradeData.takeProfit);
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                await submitOrder('STOP', tradeData.stopLoss);
            }
        }
        console.log('Bracket order creation complete');
        return Promise.resolve();
    }

    // returns an array like [{timestamp,id,event,comment,fillPrice}, …]
    function getOrderEvents(container = document) {
      const host =
        container.querySelector('.order-history-content') ||
        container.querySelector('.module.orders');

      if (!host) {
        return [];
      }

      const rows = host.querySelectorAll('.public_fixedDataTable_bodyRow');

      return Array.from(rows, row => {
        const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
        if (!cells.length) return null;
        const timestamp = cells[0]?.textContent.trim() || '';
        const id = cells[1]?.textContent.trim() || '';
        const eventTxt = cells[2]?.textContent.trim() || '';
        const comment = cells[3]?.textContent.trim() || '';
        let fillPrice = null;
        const m = eventTxt.match(/@([\d.]+)/);
        if (m) fillPrice = Number(m[1]);
        if (!eventTxt) return null;
        return { timestamp, id, event: eventTxt, comment, fillPrice };
      }).filter(Boolean);
    }


    // Futures tick data dictionary with default SL/TP settings for each instrument
    const futuresTickData = {
      // Symbol: { tickSize, tickValue, defaultSL (ticks), defaultTP (ticks), precision (decimal places) }
      MNQ: { tickSize: 0.25, tickValue: 0.5,  defaultSL: 40,  defaultTP: 100, precision: 2 },  // Micro E-mini Nasdaq-100
      NQ:  { tickSize: 0.25, tickValue: 5.0,  defaultSL: 40,  defaultTP: 100, precision: 2 },  // E-mini Nasdaq-100
      ES:  { tickSize: 0.25, tickValue: 12.5, defaultSL: 40,  defaultTP: 100, precision: 2 },  // E-mini S&P 500
      RTY: { tickSize: 0.1,  tickValue: 5.0,  defaultSL: 90,  defaultTP: 225, precision: 1 },  // E-mini Russell 2000
      YM:  { tickSize: 1.0,  tickValue: 5.0,  defaultSL: 10,  defaultTP: 25,  precision: 0 },  // E-mini Dow Jones
      CL:  { tickSize: 0.01, tickValue: 10.0, defaultSL: 50,  defaultTP: 100, precision: 2 },  // Crude Oil
      GC:  { tickSize: 0.1,  tickValue: 10.0, defaultSL: 15,  defaultTP: 30,  precision: 1 },  // Gold (15 ticks = $150 risk)
      MGC: { tickSize: 0.1,  tickValue: 1.0,  defaultSL: 15,  defaultTP: 30,  precision: 1 }   // Micro Gold
    };

function autoTrade(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, _tickSize = 0.25) {
        console.log(`autoTrade called with: symbol=${inputSymbol}, qty=${quantity}, action=${action}, TP=${takeProfitTicks}, SL=${stopLossTicks}, tickSize=${_tickSize}`);

        const overrides = {};
        if (inputSymbol) overrides.symbol = inputSymbol;
        if (typeof quantity === 'number' && !Number.isNaN(quantity)) overrides.quantity = quantity;
        if (takeProfitTicks !== null && takeProfitTicks !== undefined) overrides.tpTicks = takeProfitTicks;
        if (stopLossTicks !== null && stopLossTicks !== undefined) overrides.slTicks = stopLossTicks;
        if (_tickSize !== null && _tickSize !== undefined) overrides.tickSize = _tickSize;

        const config = resolveTradeConfig(overrides, 'autoTrade');
        const {
            symbol,
            quantity: qty,
            tpTicks,
            slTicks,
            tickSize: configTickSize,
            entryPrice: configuredEntryPrice,
            tpPrice: configuredTpPrice,
            slPrice: configuredSlPrice,
            tpEnabled,
            slEnabled
        } = config;

        const symbolInput = symbol || 'NQ';
        console.log(`Using symbol: ${symbolInput}`);

        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '') || symbolInput;
        console.log(`Root symbol: ${rootSymbol}`);

        const symbolData = futuresTickData[rootSymbol] || {};

        let tickSize = Number.isFinite(configTickSize)
            ? configTickSize
            : (typeof symbolData.tickSize === 'number' ? symbolData.tickSize : coerceNumber(_tickSize, 0.25));

        if (!Number.isFinite(tickSize)) {
            tickSize = 0.25;
        }

        const actualStopLossTicks = slEnabled
            ? coerceNumber(slTicks, symbolData.defaultSL ?? 40)
            : 0;
        const actualTakeProfitTicks = tpEnabled
            ? coerceNumber(tpTicks, symbolData.defaultTP ?? 100)
            : 0;

        const resolvedQty = coerceNumber(qty, 1);

        console.log(`Using tick size ${tickSize}`);
        console.log(`Effective SL: ${actualStopLossTicks} ticks, TP: ${actualTakeProfitTicks} ticks`);

        console.log(`Getting market data for ${symbolInput}`);
        const marketData = getMarketData(symbolInput);
        if (!marketData) {
            console.error(`No market data for ${symbolInput}`);
            return;
        }
        console.log('Market data:', marketData);

        const marketPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
        console.log(`Market price: ${marketPrice} (${action === 'Buy' ? 'offer' : 'bid'} price)`);

        const customEntryPrice = Number.isFinite(configuredEntryPrice) ? configuredEntryPrice : null;
        let entryPrice = marketPrice;
        let orderType = 'MARKET';

        if (customEntryPrice !== null) {
            console.log(`Custom entry price provided: ${customEntryPrice}`);
            entryPrice = customEntryPrice;
            if (action === 'Buy') {
                orderType = customEntryPrice < marketPrice ? 'LIMIT' : 'STOP';
            } else {
                orderType = customEntryPrice > marketPrice ? 'LIMIT' : 'STOP';
            }
            console.log(`Order type determined to be: ${orderType}`);
        } else {
            console.log(`No custom entry price provided, using market order at ${marketPrice}`);
        }

        const decimalPrecision = Number.isFinite(symbolData.precision) ? symbolData.precision : 2;
        console.log(`Using price precision: ${decimalPrecision} decimal places`);

        const slPriceValue = slEnabled
            ? (Number.isFinite(configuredSlPrice)
                ? configuredSlPrice
                : (action === 'Buy'
                    ? entryPrice - actualStopLossTicks * tickSize
                    : entryPrice + actualStopLossTicks * tickSize))
            : null;

        const tpPriceValue = tpEnabled
            ? (Number.isFinite(configuredTpPrice)
                ? configuredTpPrice
                : (action === 'Buy'
                    ? entryPrice + actualTakeProfitTicks * tickSize
                    : entryPrice - actualTakeProfitTicks * tickSize))
            : null;

        const stopLossPrice = slPriceValue != null ? slPriceValue.toFixed(decimalPrecision) : null;
        const takeProfitPrice = tpPriceValue != null ? tpPriceValue.toFixed(decimalPrecision) : null;

        if (typeof updateDriverState === 'function') {
            updateDriverState({
                symbol: symbolInput,
                quantity: resolvedQty,
                tpTicks: actualTakeProfitTicks,
                slTicks: actualStopLossTicks,
                tickSize,
                entryPrice: customEntryPrice,
                tpPrice: tpPriceValue != null ? tpPriceValue : null,
                slPrice: slPriceValue,
                tpEnabled,
                slEnabled
            }, 'autoTrade-final');
        }

        const tradeData = {
            symbol: marketData.symbol,
            action,
            qty: String(resolvedQty),
            takeProfit: takeProfitPrice,
            stopLoss: stopLossPrice,
            orderType,
            entryPrice: orderType !== 'MARKET' && entryPrice != null ? entryPrice.toFixed(decimalPrecision) : null,
            tpEnabled,
            slEnabled
        };
        console.log('Trade data prepared:', tradeData);

        console.log('Submitting bracket orders');
        return createBracketOrdersManual(tradeData).finally(() => {});
    }


    // helper – builds the front-quarter code for any root (e.g. 'NQ' → 'NQM5')
    function getFrontQuarter(root) {
        console.log(`getFrontQuarter called for root: "${root}"`);
        const { letter, yearDigit } = getQuarterlyCode();  // uses MONTH_CODES internally
        console.log(`Got quarterly code: letter=${letter}, yearDigit=${yearDigit}`);
        const result = `${root.toUpperCase()}${letter}${yearDigit}`;
        console.log(`Returning front quarter symbol: "${result}"`);
        return result;
    }

    function getMarketData(inputSymbol) {
        console.log(`getMarketData called for: "${inputSymbol}"`);

        const symbol = /^[A-Z]{1,3}$/.test(inputSymbol) ? normalizeSymbol(inputSymbol) : inputSymbol.toUpperCase();
        const row = findQuoteRow(symbol);
        if (!row) {
            console.log(`Cannot Find ${inputSymbol}`);
            return null;
        }
        // columns: [0]=Symbol,[1]=Last,[2]=Change,[3]=%Change,[4]=Bid,[5]=Offer,[6]=Open,[7]=High,[8]=Low,[9]=Total Vol.
        const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
        const bidPrice   = cells[4]?.textContent.trim();
        const offerPrice = cells[5]?.textContent.trim();
        return { symbol, bidPrice, offerPrice };
    }

    // Find the visible quote-table row for a given symbol or root (e.g., "NQZ5" or "NQ")
    function findQuoteRow(inputSymbol) {
        // If they pass a root like "NQ", allow prefix match; if "NQZ5", require exact.
        const isRoot = /^[A-Z]{1,3}$/.test((inputSymbol || '').trim());
        const wantExact = isRoot ? null : normalize(inputSymbol);
        const wantRoot  = isRoot ? normalize(inputSymbol) : null;

        // Support a few possible roots; fall back to document if not present.
        const rootCandidates = document.querySelectorAll(
            '.quoteboard.module.data-table, .data-table, .quoteboard'
        );
        const roots = rootCandidates.length ? rootCandidates : [document];

        for (const root of roots) {
            const rows = root.querySelectorAll('.public_fixedDataTable_bodyRow');
            for (const row of rows) {
                // Skip non-visible (virtualized) rows
                if (row.offsetParent === null) continue;

                // First cell is the Symbol column in Tradovate’s fixed-data-table
                const firstCell = row.querySelector('.public_fixedDataTableCell_cellContent');
                if (!firstCell) continue;

                const got = normalize(firstCell.textContent);

                // Exact contract match (e.g., "NQZ5")
                if (wantExact && got === wantExact) return row;

                // Root match (e.g., "NQ" should match "NQZ5", "NQM6", etc.)
                if (wantRoot && got.startsWith(wantRoot)) return row;
            }
        }

        // Not found: log a helpful error and return null (caller can handle gracefully)
        console.error(`findQuoteRow: row for "${inputSymbol}" not found (visible area).`);
        return null;

        // ---- helpers ----
        function normalize(s) {
            return String(s || '')
                .replace(/[\u2000-\u200F\u2028\u2029\u202F\u00A0]/g, ' ') // unicode spaces
                .replace(/\s+/g, ' ')
                .trim()
                .toUpperCase();
        }
    }


    // --- FUTURES MONTH LETTERS (Jan-Dec) ---
    const MONTH_CODES = ['F','G','H','J','K','M','N','Q','U','V','X','Z'];

    /**
 * Returns { letter, yearDigit } for the given date.
 * Example: 2025-04-23  →  { letter:'J', yearDigit:'5' }
 */
    function getMonthlyCode(date = new Date()) {
        console.log(`getMonthlyCode called with date: ${date.toISOString()}`);
        const letter = MONTH_CODES[date.getUTCMonth()];      // 0-11 → F … Z
        const yearDigit = (date.getUTCFullYear() % 10) + ''; // 2025 → "5"
        console.log(`Calculated monthly code: letter=${letter}, yearDigit=${yearDigit}`);
        return { letter, yearDigit };
    }

    /**
     * CME-compliant NQ futures front month calculator
     * Based on official CME rules:
     * - Rollover Date: Monday before 3rd Friday of expiration month
     * - Expiration Months: March (H), June (M), September (U), December (Z)
     * - Expiration Time: 9:30 AM EST on 3rd Friday
     */
    function getNQFrontMonth(date = new Date()) {
        console.log(`getNQFrontMonth called with date: ${date.toISOString()}`);

        // Contract months: March, June, September, December
        const months = [3, 6, 9, 12];  // 1-based months
        const codes = ['H', 'M', 'U', 'Z'];

        const year = date.getFullYear();
        const currentMonth = date.getMonth() + 1; // Convert to 1-based
        const currentDay = date.getDate();

        console.log(`Current date: ${year}-${currentMonth}-${currentDay}`);

        // Find current or next expiration month
        for (let i = 0; i < months.length; i++) {
            const expiryMonth = months[i];

            // Calculate third Friday of expiration month
            const thirdFriday = getThirdFriday(year, expiryMonth);

            // Roll date is Monday before third Friday (Friday minus 4 days)
            const rollDate = new Date(thirdFriday);
            rollDate.setDate(thirdFriday.getDate() - 4);

            console.log(`Checking ${codes[i]} contract: expiry=${thirdFriday.toISOString()}, roll=${rollDate.toISOString()}`);

            if (date < rollDate) {
                // Current contract is still active
                const contractCode = `NQ${codes[i]}${String(year).slice(-2)}`;
                console.log(`Current front month: ${contractCode} (before roll date)`);
                return {
                    symbol: contractCode,
                    letter: codes[i],
                    yearDigit: String(year).slice(-2),
                    expiry: thirdFriday,
                    rollDate: rollDate,
                    isRollPeriod: false
                };
            } else if (date < thirdFriday) {
                // In roll period, next contract becomes front month
                const nextIndex = (i + 1) % 4;
                const nextYear = nextIndex > i ? year : year + 1;
                const contractCode = `NQ${codes[nextIndex]}${String(nextYear).slice(-2)}`;
                console.log(`Front month during roll period: ${contractCode}`);
                return {
                    symbol: contractCode,
                    letter: codes[nextIndex],
                    yearDigit: String(nextYear).slice(-2),
                    expiry: getThirdFriday(nextYear, months[nextIndex]),
                    rollDate: rollDate,
                    isRollPeriod: true
                };
            }
        }

        // If we get here, move to next year
        const nextYear = year + 1;
        const contractCode = `NQ${codes[0]}${String(nextYear).slice(-2)}`;
        console.log(`Moving to next year: ${contractCode}`);
        return {
            symbol: contractCode,
            letter: codes[0],
            yearDigit: String(nextYear).slice(-2),
            expiry: getThirdFriday(nextYear, months[0]),
            rollDate: null,
            isRollPeriod: false
        };
    }

    /**
     * Calculate third Friday of a given month
     * @param {number} year - Full year (e.g., 2025)
     * @param {number} month - Month (1-12)
     * @returns {Date} Third Friday of the month
     */
    function getThirdFriday(year, month) {
        // Start with first day of month
        const firstDay = new Date(year, month - 1, 1);

        // Find first Friday (day 5 = Friday, 0 = Sunday)
        const daysUntilFriday = (5 - firstDay.getDay() + 7) % 7;
        const firstFriday = new Date(year, month - 1, 1 + daysUntilFriday);

        // Add 14 days to get third Friday
        const thirdFriday = new Date(firstFriday);
        thirdFriday.setDate(firstFriday.getDate() + 14);

        return thirdFriday;
    }

    /**
     * Legacy function for backward compatibility
     * Returns the next quarterly contract based on CME rollover rules
     */
    function getQuarterlyCode(date = new Date()) {
        console.log(`getQuarterlyCode called (legacy) with date: ${date.toISOString()}`);
        const frontMonth = getNQFrontMonth(date);
        console.log(`Legacy getQuarterlyCode returning: letter=${frontMonth.letter}, yearDigit=${frontMonth.yearDigit}`);
        return { letter: frontMonth.letter, yearDigit: String(frontMonth.yearDigit).slice(-1) }; // "5"

    }

    // --- CME-COMPLIANT NQ FRONT MONTH CALCULATION ---
    console.log('Calculating current NQ front month using CME rules...');
    const frontMonthInfo = getNQFrontMonth();
    console.log(`Current NQ front month: ${frontMonthInfo.symbol}`);
    console.log(`Expiry date: ${frontMonthInfo.expiry.toISOString()}`);
    console.log(`Roll date: ${frontMonthInfo.rollDate ? frontMonthInfo.rollDate.toISOString() : 'N/A'}`);
    console.log(`Is in roll period: ${frontMonthInfo.isRollPeriod}`);

    // Legacy compatibility - build front-quarter symbol
    const { letter, yearDigit } = getQuarterlyCode();
    const nqFront = `NQ${letter}${yearDigit}`;
    console.log(`Legacy front-quarter symbol: ${nqFront}`);

    // Expose front month calculator globally
    window.getNQFrontMonth = getNQFrontMonth;
    window.getThirdFriday = getThirdFriday;

    function moveStopLossToBreakeven() {
        console.warn('[TradoAuto] moveStopLossToBreakeven is not implemented in this build');
    }

    const TradoAuto = {
        init: () => {
            console.log('[TradoAuto] legacy driver init');
        },
        autoTrade,
        clickExitForSymbol,
        moveStopLossToBreakeven,
        createUI,
        getNQFrontMonth,
        getThirdFriday,
        getState: () => (typeof getDriverState === 'function' ? getDriverState() : {}),
        applyConfig: (patch = {}, source = 'external') => {
            if (typeof updateDriverState === 'function') {
                return updateDriverState(patch, source);
            }
            return {};
        },
        subscribeState: (listener) => {
            if (typeof subscribeDriverState === 'function') {
                return subscribeDriverState(listener);
            }
            return () => {};
        },
        getOrderEvents
    };

    const targetWindow = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;
    console.log('[TradoAuto] installing legacy driver onto window/unsafeWindow');
    window.TradoAuto = TradoAuto;
    targetWindow.TradoAuto = TradoAuto;
    targetWindow.TradovateAutoDriverBundle = { default: TradoAuto, autoTrade, clickExitForSymbol, moveStopLossToBreakeven, createUI, getNQFrontMonth, getThirdFriday };
    if (!targetWindow.__tradoAutoInterval) {
        targetWindow.__tradoAutoInterval = setInterval(() => {
            if (!targetWindow.TradoAuto || typeof targetWindow.TradoAuto.autoTrade !== 'function') {
                console.warn('[TradoAuto] Reasserting driver on targetWindow');
                targetWindow.TradoAuto = TradoAuto;
            }
            if (!window.TradoAuto || typeof window.TradoAuto.autoTrade !== 'function') {
                console.warn('[TradoAuto] Reasserting driver on window');
                window.TradoAuto = TradoAuto;
            }
        }, 250);
        console.log('[TradoAuto] watchdog interval started');
    }

})();

export function createAutoDriver() {
    return (typeof window !== 'undefined' && window.TradoAuto) ? window.TradoAuto : TradoAuto;
}

export default (typeof window !== 'undefined' && window.TradoAuto) ? window.TradoAuto : TradoAuto;
