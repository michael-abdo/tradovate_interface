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

(function () {
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
    });
    tpInput.addEventListener('input', () => {
        console.log(`TP input changed to: ${tpInput.value}`);
        localStorage.setItem('bracketTrade_tp', tpInput.value);
    });
    document.getElementById('qtyInput').addEventListener('input', e => {
        console.log(`Quantity input changed to: ${e.target.value}`);
        localStorage.setItem('bracketTrade_qty', e.target.value);
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
        console.log(`Symbol input changed to: ${e.target.value}`);
        localStorage.setItem('bracketTrade_symbol', e.target.value);
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
    });

    document.getElementById('tickInput').value = localStorage.getItem('bracketTrade_tick') || '0.25';
    document.getElementById('tickInput').addEventListener('input', e => {
        console.log(`Tick size input changed to: ${e.target.value}`);
        localStorage.setItem('bracketTrade_tick', e.target.value);
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






    console.log('Creating UI...');
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
        const enableTP = document.getElementById('tpCheckbox').checked;
        const enableSL = document.getElementById('slCheckbox').checked;
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



        async function setCommonFields(quantityValue) {
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
            if (quantityValue != null) {
                const qtyString = `${quantityValue}`;
                console.log(`Setting quantity to: ${qtyString}`);
                await updateInputValue('.select-input.combobox input', qtyString);
            }
        }

        // returns an array like [{timestamp,id,event,comment,fillPrice}, …]
        function getOrderEvents(container = document) {
            const rows = container.querySelectorAll(
                '.order-history-content .public_fixedDataTable_bodyRow'
            );

            return Array.from(rows, row => {
                const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
                const timestamp = cells[0]?.textContent.trim() || '';
                const id        = cells[1]?.textContent.trim() || '';
                const eventTxt  = cells[2]?.textContent.trim() || '';
                const comment   = cells[3]?.textContent.trim() || '';

                // extract fill price patterns like “1@18747.25 NQM5”
                let fillPrice = null;
                const m = eventTxt.match(/@([\d.]+)/);
                if (m) fillPrice = Number(m[1]);

                return { timestamp, id, event: eventTxt, comment, fillPrice };
            });
        }

        function clickPriceArrow(direction = 'up') {
            const wrapper = document.querySelector('.numeric-input-value-controls');
            if (!wrapper) return;

            const target = wrapper.querySelector(
                direction === 'up' ? '.numeric-input-increment' : '.numeric-input-decrement'
            );
            target?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }

        async function submitOrder(orderType, priceValue, quantityValue) {
            await setCommonFields(quantityValue ?? tradeData.qty);

            const typeSel = document.querySelector('.group.order-type .select-input div[tabindex]');
            typeSel?.click();
            [...document.querySelectorAll('ul.dropdown-menu li')]
                .find(li => li.textContent.trim() === orderType)
                ?.click();

            //await delay(400);               // NEW - let Tradovate draw the price box

            if (priceValue)
                await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);
            // clickPriceArrow();

            document.querySelector('.btn-group .btn-primary')?.click();
            await delay(200);
            console.log(getOrderEvents());
            document.querySelector('.icon.icon-back')?.click();
            await delay(200);
        }

        const entryQty = tradeData.entryQty ?? tradeData.qty;
        console.log(`Submitting initial ${tradeData.orderType || 'MARKET'} order with qty ${entryQty ?? tradeData.qty}`);
        await submitOrder(tradeData.orderType || 'MARKET', tradeData.entryPrice, entryQty);

        const bracketQtyRaw = tradeData.bracketQty ?? tradeData.qty;
        const shouldCreateBracket = !tradeData.skipBracket &&
              (enableTP || enableSL) &&
              bracketQtyRaw != null &&
              Number(bracketQtyRaw) > 0;

        if (!shouldCreateBracket) {
            console.log('Skipping bracket legs for this order');
            return Promise.resolve();
        }

        const bracketQty = `${bracketQtyRaw}`;
        console.log(`Using bracket quantity ${bracketQty}`);

        if (tradeData.action === 'Buy') {
            console.log('Flipping action to Sell for TP/SL orders');
            tradeData.action = 'Sell';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                await submitOrder('LIMIT', tradeData.takeProfit, bracketQty);
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                await submitOrder('STOP', tradeData.stopLoss, bracketQty);
            }
        } else {
            console.log('Flipping action to Buy for TP/SL orders');
            tradeData.action = 'Buy';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                await submitOrder('LIMIT', tradeData.takeProfit, bracketQty);
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                await submitOrder('STOP', tradeData.stopLoss, bracketQty);
            }
        }
        console.log('Bracket order creation complete');
        return Promise.resolve();
    }

    // returns an array like [{timestamp,id,event,comment,fillPrice}, …]
    function getOrderEvents(container = document) {
        const rows = container.querySelectorAll(
            '.order-history-content .public_fixedDataTable_bodyRow'
        );

        return Array.from(rows, row => {
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            const timestamp = cells[0]?.textContent.trim() || '';
            const id        = cells[1]?.textContent.trim() || '';
            const eventTxt  = cells[2]?.textContent.trim() || '';
            const comment   = cells[3]?.textContent.trim() || '';

            // extract fill price patterns like “1@18747.25 NQM5”
            let fillPrice = null;
            const m = eventTxt.match(/@([\d.]+)/);
            if (m) fillPrice = Number(m[1]);

            return { timestamp, id, event: eventTxt, comment, fillPrice };
        });
    }


    function extractFixedTableRows(tableRoot = document) {
        if (debug) console.log('extractFixedTableRows: scanning for fixed data table');
        let table = null;
        const selector = '.fixedDataTableLayout_main.public_fixedDataTable_main[role="grid"]';
        if (tableRoot.matches && tableRoot.matches(selector)) {
            table = tableRoot;
        } else {
            table = tableRoot.querySelector(selector);
        }
        if (!table) {
            if (debug) console.warn('extractFixedTableRows: table not found');
            return [];
        }

        const headerCells = table.querySelectorAll('.fixedDataTableLayout_header [role="columnheader"] .public_fixedDataTableCell_cellContent');
        const headers = [...headerCells].map(cell => (cell.textContent || '').trim().toLowerCase());
        const headerIndex = name => headers.indexOf(name);

        const idxTimestamp = headerIndex('timestamp');
        const idxPrice = headerIndex('price');
        const idxSize = headerIndex('size');
        const idxAcc = headerIndex('acc.');

        const rows = [...table.querySelectorAll('.public_fixedDataTable_bodyRow')];
        return rows.map(row => {
            const cells = row.querySelectorAll('[role="gridcell"]');
            let inferredDirection = 0;

            const getCell = idx => {
                const cell = cells[idx];
                if (!cell) return { text: null, value: null, classes: '' };
                const wrapper = cell.querySelector('.public_fixedDataTableCell_wrap1');
                const valueAttr = wrapper?.getAttribute('value') ?? null;
                const text = wrapper?.querySelector('.public_fixedDataTableCell_cellContent')?.textContent?.trim() ?? null;
                const classes = wrapper?.className ?? '';
                if (inferredDirection === 0) {
                    if (/tick-(?:flip|cont)-up/.test(classes)) inferredDirection = 1;
                    else if (/tick-(?:flip|cont)-down/.test(classes)) inferredDirection = -1;
                }
                return { text, value: valueAttr, classes };
            };

            const tsCell = getCell(idxTimestamp);
            const priceCell = getCell(idxPrice);
            const sizeCell = getCell(idxSize);
            const accCell = getCell(idxAcc);

            const parseNumber = v => {
                if (v == null) return null;
                const num = Number(v);
                return Number.isFinite(num) ? num : null;
            };

            const timestampText = tsCell.text;
            const timestampValue = tsCell.value ? new Date(tsCell.value) : null;

            return {
                direction: inferredDirection,
                timestampText,
                timestamp: timestampValue,
                priceText: priceCell.text,
                price: parseNumber(priceCell.value ?? priceCell.text),
                sizeText: sizeCell.text,
                size: parseNumber(sizeCell.value ?? sizeCell.text),
                accumulatedText: accCell.text,
                accumulated: parseNumber(accCell.value ?? accCell.text)
            };
        });
    }

    function attachDraggable(element, handle, storageKeyPrefix, onMove) {
        if (!element) return;
        const dragHandle = handle || element;
        if (!dragHandle) return;

        const state = { dragging: false, offsetX: 0, offsetY: 0 };

        const onMouseDown = e => {
            if (e.button !== 0) return;
            state.dragging = true;
            const rect = element.getBoundingClientRect();
            state.offsetX = e.clientX - rect.left;
            state.offsetY = e.clientY - rect.top;
            element.style.cursor = 'grabbing';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        };

        const onMouseMove = e => {
            if (!state.dragging) return;
            const left = `${e.clientX - state.offsetX}px`;
            const top = `${e.clientY - state.offsetY}px`;
            element.style.left = left;
            element.style.top = top;
            element.style.right = 'unset';
            if (typeof onMove === 'function') onMove(left, top);
        };

        const onMouseUp = () => {
            if (!state.dragging) return;
            state.dragging = false;
            element.style.cursor = 'grab';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            if (storageKeyPrefix) {
                localStorage.setItem(`${storageKeyPrefix}Left`, element.style.left || '');
                localStorage.setItem(`${storageKeyPrefix}Top`, element.style.top || '');
            }
        };

        dragHandle.style.cursor = 'grab';
        dragHandle.addEventListener('mousedown', onMouseDown);
    }


    const orderAnalyticsState = {
        container: null,
        ratioEl: null,
        canvas: null,
        ctx: null,
        intervalId: null,
        refreshId: null,
        history: new Map()
    };

    function createOrderAnalyticsPanel() {
        if (orderAnalyticsState.container && document.body.contains(orderAnalyticsState.container)) {
            return;
        }
        let existing = document.getElementById('order-analytics-panel');
        if (existing) {
            orderAnalyticsState.container = existing;
            orderAnalyticsState.ratioEl = existing.querySelector('.order-analytics-ratio');
            orderAnalyticsState.canvas = existing.querySelector('canvas');
            orderAnalyticsState.ctx = orderAnalyticsState.canvas?.getContext('2d') ?? null;
            return;
        }

        const panel = document.createElement('div');
        panel.id = 'order-analytics-panel';
        Object.assign(panel.style, {
            position: 'fixed',
            top: '220px',
            right: '20px',
            width: '280px',
            background: '#1a1d23',
            color: '#f1f1f1',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: '0 2px 12px rgba(0,0,0,0.55)',
            zIndex: '99999',
            fontFamily: 'sans-serif'
        });

        const title = document.createElement('div');
        title.textContent = 'Order Flow Monitor';
        Object.assign(title.style, {
            fontWeight: '600',
            marginBottom: '8px',
            fontSize: '14px',
            textAlign: 'center'
        });

        const ratioEl = document.createElement('div');
        ratioEl.className = 'order-analytics-ratio';
        Object.assign(ratioEl.style, {
            fontSize: '12px',
            marginBottom: '8px',
            textAlign: 'center',
            color: '#cfd2d6'
        });
        ratioEl.textContent = 'Waiting for order data…';

        const canvas = document.createElement('canvas');
        canvas.width = 280;
        canvas.height = 150;
        Object.assign(canvas.style, {
            width: '100%',
            height: '150px',
            background: '#101218',
            borderRadius: '6px'
        });

        panel.appendChild(title);
        panel.appendChild(ratioEl);
        panel.appendChild(canvas);
        document.body.appendChild(panel);

        const savedLeft = localStorage.getItem('orderAnalyticsPanelLeft');
        const savedTop = localStorage.getItem('orderAnalyticsPanelTop');
        if (savedLeft && savedTop) {
            panel.style.left = savedLeft;
            panel.style.top = savedTop;
            panel.style.right = 'unset';
        }

        orderAnalyticsState.container = panel;
        orderAnalyticsState.ratioEl = ratioEl;
        orderAnalyticsState.canvas = canvas;
        orderAnalyticsState.ctx = canvas.getContext('2d');

        attachDraggable(panel, title, 'orderAnalyticsPanel');
    }

    function mergeOrderAnalyticsHistory(rows) {
        if (!Array.isArray(rows) || !rows.length) return;
        const history = orderAnalyticsState.history;
        const MAX_HISTORY = 4000;

        rows.forEach(row => {
            if (!row) return;
            const timestampMs = (row.timestamp instanceof Date && !Number.isNaN(row.timestamp.getTime()))
                ? row.timestamp.getTime()
                : null;
            const keyBasis = timestampMs != null ? timestampMs : (row.timestampText || row.priceText || '');
            const key = `${keyBasis}|${row.priceText}|${row.sizeText}|${row.accumulatedText}|${row.direction}`;
            if (history.has(key)) {
                const existing = history.get(key);
                if (existing && existing.direction === 0 && row.direction !== 0) {
                    existing.direction = row.direction;
                }
                return;
            }
            history.set(key, {
                ...row,
                timestampMs: timestampMs ?? Date.now()
            });
        });

        if (history.size > MAX_HISTORY) {
            const excess = history.size - MAX_HISTORY;
            const iter = history.keys();
            for (let i = 0; i < excess; i++) {
                const { value, done } = iter.next();
                if (done) break;
                history.delete(value);
            }
        }
    }

    function updateOrderAnalytics() {
        if (!orderAnalyticsState.container) return;
        if (!orderAnalyticsState.ctx || !orderAnalyticsState.canvas || !orderAnalyticsState.ratioEl) return;

        const table =
              document.querySelector('.order-history-content .fixedDataTableLayout_main.public_fixedDataTable_main[role="grid"]') ||
              document.querySelector('.module.order-history .fixedDataTableLayout_main.public_fixedDataTable_main[role="grid"]') ||
              document.querySelector('.workspace .fixedDataTableLayout_main.public_fixedDataTable_main[role="grid"][aria-rowcount]') ||
              document.querySelector('.fixedDataTableLayout_main.public_fixedDataTable_main[role="grid"]');

        if (!table) {
            orderAnalyticsState.ratioEl.textContent = 'Order history not found';
            const ctx = orderAnalyticsState.ctx;
            ctx.clearRect(0, 0, orderAnalyticsState.canvas.width, orderAnalyticsState.canvas.height);
            return;
        }

        const rows = extractFixedTableRows(table);
        mergeOrderAnalyticsHistory(rows);

        const historyRows = [...orderAnalyticsState.history.values()];
        if (!historyRows.length) {
            orderAnalyticsState.ratioEl.textContent = 'No order data available';
            const ctx = orderAnalyticsState.ctx;
            ctx.clearRect(0, 0, orderAnalyticsState.canvas.width, orderAnalyticsState.canvas.height);
            return;
        }

        let totalBuyers = 0;
        let totalSellers = 0;
        const minuteBuckets = new Map();

        historyRows.forEach(row => {
            const volume = Number(row.size) || 0;
            if (row.direction > 0) totalBuyers += volume;
            else if (row.direction < 0) totalSellers += volume;

            if (!(row.timestamp instanceof Date) || Number.isNaN(row.timestamp.getTime())) return;
            const minuteKey = new Date(row.timestamp);
            minuteKey.setSeconds(0, 0);
            const key = minuteKey.getTime();
            let bucket = minuteBuckets.get(key);
            if (!bucket) {
                bucket = {
                    key,
                    timestamp: new Date(minuteKey),
                    buyers: 0,
                    sellers: 0
                };
                minuteBuckets.set(key, bucket);
            }
            if (row.direction > 0) bucket.buyers += volume;
            else if (row.direction < 0) bucket.sellers += volume;
        });

        const totalVolume = totalBuyers + totalSellers;
        const buyerPct = totalVolume ? (totalBuyers / totalVolume) * 100 : 0;
        const sellerPct = totalVolume ? (totalSellers / totalVolume) * 100 : 0;
        orderAnalyticsState.ratioEl.textContent =
            `Buyers ${buyerPct.toFixed(1)}% (${totalBuyers}) | Sellers ${sellerPct.toFixed(1)}% (${totalSellers})`;

        const sortedBuckets = [...minuteBuckets.values()].sort((a, b) => a.key - b.key);
        drawOrderAnalyticsGraph(sortedBuckets);
    }

    function drawOrderAnalyticsGraph(buckets) {
        const canvas = orderAnalyticsState.canvas;
        const ctx = orderAnalyticsState.ctx;
        if (!canvas || !ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);

        const baseline = Math.round(height * 0.55);
        ctx.strokeStyle = '#2f3542';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, baseline);
        ctx.lineTo(width, baseline);
        ctx.stroke();

        ctx.font = '10px monospace';
        ctx.fillStyle = '#666';
        ctx.textBaseline = 'middle';
        ctx.textAlign = 'right';
        ctx.fillText('+', width - 4, baseline - 8);
        ctx.fillText('-', width - 4, baseline + 8);

        if (!buckets.length) return;

        const maxMagnitude = Math.max(
            1,
            ...buckets.map(bucket =>
                Math.max(
                    Math.abs(bucket.buyers - bucket.sellers),
                    bucket.buyers,
                    bucket.sellers
                )
            )
        );
        const usableHeight = baseline - 15;
        const step = width / Math.max(buckets.length, 1);

        buckets.forEach((bucket, index) => {
            const net = bucket.buyers - bucket.sellers;
            const magnitude = Math.abs(net);
            const direction = net >= 0 ? 1 : -1;
            const barHeight = usableHeight * (magnitude / maxMagnitude);
            const xCenter = step * index + step / 2;

            ctx.strokeStyle = direction >= 0 ? '#2ecc71' : '#e74c3c';
            ctx.lineWidth = Math.max(6, step * 0.6);
            ctx.beginPath();
            ctx.moveTo(xCenter, baseline);
            ctx.lineTo(xCenter, baseline - direction * barHeight);
            ctx.stroke();

            const label = `${String(bucket.timestamp.getHours()).padStart(2, '0')}:${String(bucket.timestamp.getMinutes()).padStart(2, '0')}`;
            ctx.fillStyle = '#b0b3ba';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(label, xCenter, height - 4);
        });
    }

    function rebuildOrderAnalyticsPanel() {
        if (orderAnalyticsState.container) {
            try {
                orderAnalyticsState.container.remove();
            } catch (err) {
                console.warn('Failed to remove analytics panel during rebuild:', err);
            }
        }
        orderAnalyticsState.container = null;
        orderAnalyticsState.ratioEl = null;
        orderAnalyticsState.canvas = null;
        orderAnalyticsState.ctx = null;

        createOrderAnalyticsPanel();
        updateOrderAnalytics();
    }


    function initOrderAnalyticsPanel() {
        createOrderAnalyticsPanel();
        if (!orderAnalyticsState.intervalId) {
            orderAnalyticsState.intervalId = setInterval(updateOrderAnalytics, 500);
            updateOrderAnalytics();
        }
        if (!orderAnalyticsState.refreshId) {
            orderAnalyticsState.refreshId = setInterval(rebuildOrderAnalyticsPanel, 60000);
        }
    }

    initOrderAnalyticsPanel();

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

    async function autoTrade(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, _tickSize = 0.25) {
        console.log(`autoTrade called with: symbol=${inputSymbol}, qty=${quantity}, action=${action}, TP=${takeProfitTicks}, SL=${stopLossTicks}, tickSize=${_tickSize}`);

        const symbolInput = document.getElementById('symbolInput').value || 'NQ';
        console.log(`Using symbol: ${symbolInput}`);

        // Get root symbol (e.g., 'NQH5' -> 'NQ')
        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '');
        console.log(`Root symbol: ${rootSymbol}`);

        // Get tick size and default values from dictionary or fallback
        const symbolData = futuresTickData[rootSymbol];
        const decimalPrecision = symbolData?.precision ?? 2; // Default to 2 if not specified

        // Keep track of the last symbol to handle symbol changes
        if (rootSymbol !== autoTrade.lastRootSymbol) {
            document.getElementById('tickInput').value = symbolData?.tickSize ?? '';
        }
        autoTrade.lastRootSymbol = rootSymbol;
        const tickSize = (symbolData && typeof symbolData.tickSize === 'number')
        ? symbolData.tickSize
        : parseFloat(document.getElementById('tickInput').value) || _tickSize;

        // right after tickSize is determined
        const tickInput = document.getElementById('tickInput');
        if (tickInput) {
            tickInput.value = tickSize;           // shows the real value
        }
        localStorage.setItem('bracketTrade_tick', tickSize);

        // Use provided values or defaults from dictionary or UI
        const actualStopLossTicks = stopLossTicks ||
              symbolData?.defaultSL ||
              parseInt(document.getElementById('slInput').value) ||
              40;

        const actualTakeProfitTicks = takeProfitTicks ||
              symbolData?.defaultTP ||
              parseInt(document.getElementById('tpInput').value) ||
              100;

        const from = symbolData?.tickSize ? 'dictionary'
        : document.getElementById('tickInput').value ? 'input field'
        : 'default parameter';
        console.log(`Using tick size ${tickSize} (from ${from})`);
        console.log(`Using SL: ${actualStopLossTicks} ticks, TP: ${actualTakeProfitTicks} ticks`);

        console.log(`Getting market data for ${symbolInput}`);
        const marketData = getMarketData(symbolInput);
        if (!marketData) {
            console.error(`No market data for ${symbolInput}`);
            return;
        }
        console.log('Market data:', marketData);

        // Check if an entry price was provided
        const entryPriceInput = document.getElementById('entryPriceInput');
        const customEntryPrice = entryPriceInput && entryPriceInput.value ? parseFloat(entryPriceInput.value) : null;

        // Determine market price (used when no entry price is specified or for SL/TP calculations)
        const marketPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
        console.log(`Market price: ${marketPrice} (${action === 'Buy' ? 'offer' : 'bid'} price)`);

        // Determine entry order type and price
        let orderType = 'MARKET';
        let entryPrice = marketPrice;

        if (customEntryPrice !== null) {
            console.log(`Custom entry price provided: ${customEntryPrice}`);
            entryPrice = customEntryPrice;

            // Determine if this should be a LIMIT or STOP order based on price comparison
            if (action === 'Buy') {
                // For Buy: LIMIT if entry below market, STOP if entry above market
                orderType = customEntryPrice < marketPrice ? 'LIMIT' : 'STOP';
            } else {
                // For Sell: LIMIT if entry above market, STOP if entry below market
                orderType = customEntryPrice > marketPrice ? 'LIMIT' : 'STOP';
            }
            console.log(`Order type determined to be: ${orderType}`);
        } else {
            const marketOffsetTicks = 15;
            const direction = action === 'Buy' ? -1 : 1;
            const adjustedPrice = parseFloat(
                (marketPrice + direction * marketOffsetTicks * tickSize).toFixed(decimalPrecision)
            );
            entryPrice = adjustedPrice;
            orderType = 'LIMIT';
            const directionLabel = action === 'Buy' ? 'below' : 'above';
            console.log(
                `No custom entry price provided; converting to LIMIT ${directionLabel} market by ${marketOffsetTicks} ticks @ ${entryPrice.toFixed(decimalPrecision)}`
            );
        }

        console.log(`Using price precision: ${decimalPrecision} decimal places`);

        // Check if hardcoded SL/TP prices are provided
        const slPriceInput = document.getElementById('slPriceInput');
        const tpPriceInput = document.getElementById('tpPriceInput');

        // Get hardcoded prices if they exist
        const hardcodedSLPrice = slPriceInput && slPriceInput.value ? parseFloat(slPriceInput.value) : null;
        const hardcodedTPPrice = tpPriceInput && tpPriceInput.value ? parseFloat(tpPriceInput.value) : null;
        const hardcodedSLString = hardcodedSLPrice !== null ? hardcodedSLPrice.toFixed(decimalPrecision) : null;
        const hardcodedTPString = hardcodedTPPrice !== null ? hardcodedTPPrice.toFixed(decimalPrecision) : null;

        const totalQty = Math.max(1, Math.trunc(Number(quantity)) || 1);
        const SCALE_STEP_TICKS = 15;
        const baseEntryPrice = entryPrice;
        const scaleDirection = orderType === 'STOP'
            ? (action === 'Buy' ? 1 : -1)
            : (action === 'Buy' ? -1 : 1);

        const orders = [];
        for (let i = 0; i < totalQty; i++) {
            const offsetTicks = i * SCALE_STEP_TICKS;
            const levelEntryPrice = Number((baseEntryPrice + scaleDirection * offsetTicks * tickSize).toFixed(decimalPrecision));
            const levelEntryPriceString = orderType !== 'MARKET' ? levelEntryPrice.toFixed(decimalPrecision) : null;

            const stopLossPrice = hardcodedSLString ?? (action === 'Buy'
                                 ? (levelEntryPrice - actualStopLossTicks * tickSize).toFixed(decimalPrecision)
                                 : (levelEntryPrice + actualStopLossTicks * tickSize).toFixed(decimalPrecision));

            const takeProfitPrice = hardcodedTPString ?? (action === 'Buy'
                                   ? (levelEntryPrice + actualTakeProfitTicks * tickSize).toFixed(decimalPrecision)
                                   : (levelEntryPrice - actualTakeProfitTicks * tickSize).toFixed(decimalPrecision));

            console.log(`Prepared scaled order ${i + 1}/${totalQty}: entry=${levelEntryPriceString ?? 'MARKET'}, TP=${takeProfitPrice}, SL=${stopLossPrice}`);

            const entryQtyString = '1';
            const isFinalOrder = (i === totalQty - 1);
            const bracketQtyString = isFinalOrder ? `${totalQty}` : '0';

            orders.push({
                symbol: marketData.symbol,
                action,
                qty: entryQtyString,
                entryQty: entryQtyString,
                bracketQty: bracketQtyString,
                skipBracket: !isFinalOrder,
                takeProfit: takeProfitPrice,
                stopLoss: stopLossPrice,
                orderType,
                entryPrice: levelEntryPriceString
            });
        }

        console.log(`Submitting ${orders.length} scaled bracket order(s)`);
        try {
            for (let i = 0; i < orders.length; i++) {
                const order = { ...orders[i] };
                console.log(`Submitting scaled order ${i + 1}/${orders.length} at entry ${order.entryPrice ?? 'MARKET'}`);
                await createBracketOrdersManual(order);
            }
        } finally {
            const d = futuresTickData[rootSymbol];      // or rootSymbol
            const slInput = document.getElementById('slInput');
            const tpInput = document.getElementById('tpInput');
            /*
            if (d && slInput && tpInput) {
                console.log(`Resetting boxes to default values for ${rootSymbol}: SL=${d.defaultSL}, TP=${d.defaultTP}`);
                slInput.value = d.defaultSL;          // 40 or 10
                tpInput.value = d.defaultTP;          // 120 or 25
                // Also update localStorage
                localStorage.setItem('bracketTrade_sl', d.defaultSL);
                localStorage.setItem('bracketTrade_tp', d.defaultTP);
            }*/
        }
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

    // ------------ helpers ------------
    const LOG_NS = 'QUOTEBOARD';
    const log = {
        t() { return new Date().toISOString(); },
        debug(msg, obj){ console.debug(`[${LOG_NS}] ${this.t()} DEBUG: ${msg}`, obj ?? ''); },
        info (msg, obj){ console.info (`[${LOG_NS}] ${this.t()}  INFO: ${msg}`, obj ?? ''); },
        warn (msg, obj){ console.warn (`[${LOG_NS}] ${this.t()}  WARN: ${msg}`, obj ?? ''); },
        error(msg, obj){ console.error(`[${LOG_NS}] ${this.t()} ERROR: ${msg}`, obj ?? ''); },
    };

    function norm(s){ return String(s||'').replace(/[\u2000-\u200F\u2028\u2029\u202F\u00A0]/g,' ').replace(/\s+/g,' ').trim(); }
    function normUpper(s){ return norm(s).toUpperCase(); }
    function isVisible(el){ if (!el) return false; const cs = getComputedStyle(el); return cs.display!=='none' && cs.visibility!=='hidden' && el.offsetParent !== null; }
    function cssPath(el){
        if (!el || !el.nodeType || el.nodeType !== 1) return '';
        const parts = [];
        while (el && el.nodeType === 1 && parts.length < 6) {
            let sel = el.tagName.toLowerCase();
            if (el.id) { sel += `#${el.id}`; parts.unshift(sel); break; }
            if (el.className) { sel += '.' + [...new Set(String(el.className).split(/\s+/).filter(Boolean))].slice(0,3).join('.'); }
            parts.unshift(sel);
            el = el.parentElement;
        }
        return parts.join(' > ');
    }
    function isPriceLike(s){
        const t = norm(s);
        if (!t) return false;
        if (/[A-Za-z]/.test(t)) return false;
        if (t.includes(':') || /sec|min|hour|am|pm/i.test(t)) return false;
        return /^-?\d{1,6}(\.\d{1,4})?$/.test(t);
    }
    function toVariants(sym){
        const s = String(sym||'').trim().toUpperCase();
        const m = s.match(/^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{1,2})$/);
        if (!m) { log.debug('toVariants: not futures pattern', {s}); return [s]; }
        const [_, root, month, yy] = m;
        const out = new Set([s]);
        if (yy.length === 2) out.add(`${root}${month}${yy.slice(-1)}`);
        else out.add(`${root}${month}2${yy}`);
        const arr = [...out];
        log.debug('toVariants: produced', {input:s, variants:arr});
        return arr;
    }

    // ------------ table discovery ------------
    function listQuoteTables(scope=document){
        // Only quoteboard modules; avoid other fixed-data-tables on the page
        const sels = [
            '.quoteboard.module.data-table.compact-data-table',
            '.quoteboard.module.data-table',
            '.quoteboard.module',
        ];
        const seen = new Set();
        const out = [];
        sels.forEach(sel=>{
            scope.querySelectorAll(sel).forEach(el=>{
                if (!isVisible(el)) return;
                if (seen.has(el)) return;
                seen.add(el); out.push(el);
            });
        });
        log.info('listQuoteTables: discovered tables', { count: out.length, paths: out.map(cssPath) });
        return out;
    }

    function rowsContainerOf(tableEl){
        const rc = tableEl.querySelector('.fixedDataTableLayout_rowsContainer');
        if (!rc) log.warn('rowsContainerOf: not found in table', { path: cssPath(tableEl) });
        return rc;
    }

    function findHeaderRow(root){
        const selList = [
            '.public_fixedDataTableRow_main.fixedDataTableLayout_header',
            '.fixedDataTableRowLayout_main.fixedDataTableLayout_header',
            '.fixedDataTable_header .public_fixedDataTableRow_main',
            '.fixedDataTable_header .fixedDataTableRowLayout_main',
            '.fixedDataTableLayout_header .public_fixedDataTableRow_main',
            '.fixedDataTableLayout_header .fixedDataTableRowLayout_main',
        ];
        for (const sel of selList){
            const el = root.querySelector(sel);
            if (el){
                const cells = el.querySelectorAll('.public_fixedDataTableCell_cellContent');
                if (cells.length){ return el; }
            }
        }
        return null;
    }

    function getHeaderMapStrict(tableEl){
        const root = tableEl; // strictly within this quoteboard
        let headerRow = findHeaderRow(root);
        if (!headerRow){
            // climb one level up (some skins wrap)
            headerRow = findHeaderRow(root.parentElement || document);
        }
        if (!headerRow){
            log.error('getHeaderMapStrict: header row NOT found', { tablePath: cssPath(tableEl) });
            return null;
        }
        const rawCells = headerRow.querySelectorAll('.public_fixedDataTableCell_cellContent');
        const headers = [...rawCells].map(el => normUpper(el.textContent));
        log.info('getHeaderMapStrict: headers', { tablePath: cssPath(tableEl), headers });

        const map = {};
        headers.forEach((txt,i)=>{ if (txt) map[txt]=i; });

        const idxFor = (names, fallback)=>{
            for (const n of names){
                const key = normUpper(n);
                if (key in map) return map[key];
            }
            return fallback;
        };

        return {
            headers,
            getIndex: (logical, fallback)=>{
                if (logical==='symbol') return idxFor(['Symbol'], 0);
                if (logical==='bid')    return idxFor(['Bid Price','Bid','BidPrice'], 4);
                if (logical==='ask')    return idxFor(['Offer Price','Ask Price','Offer','Ask','OfferPrice','AskPrice'], 5);
                return fallback;
            }
        };
    }

    // ------------ row finder ------------
    /**
 * Find the visible row for a symbol. If containerEl is provided, search only inside it.
 * Returns { row, tableEl } or null.
 */
    function findQuoteRow(inputSymbol, containerEl){
        log.info('findQuoteRow: start', { inputSymbol, scoped: !!containerEl });

        const raw = (inputSymbol || '').trim().toUpperCase();
        const isRoot = /^[A-Z]{1,3}$/.test(raw);
        const exacts = isRoot ? [] : toVariants(raw).map(normUpper);
        const rootWant = isRoot ? normUpper(raw) : null;

        const tables = containerEl ? [containerEl] : listQuoteTables(document);
        for (const table of tables){
            const rc = rowsContainerOf(table);
            if (!rc) continue;
            const rows = rc.querySelectorAll('.public_fixedDataTable_bodyRow');
            log.debug('findQuoteRow: scanning table', { tablePath: cssPath(table), rowCount: rows.length });

            for (const row of rows){
                if (!isVisible(row)) continue;
                const firstCell = row.querySelector('.public_fixedDataTableCell_cellContent');
                if (!firstCell) continue;
                const got = normUpper(firstCell.textContent);
                if (exacts.length && exacts.includes(got)){
                    log.info('findQuoteRow: exact match', { got, tablePath: cssPath(table) });
                    return { row, tableEl: table };
                }
                if (rootWant && got.startsWith(rootWant)){
                    log.info('findQuoteRow: root match', { got, tablePath: cssPath(table) });
                    return { row, tableEl: table };
                }
            }
        }
        log.error('findQuoteRow: not found', { inputSymbol, exacts, rootWant });
        return null;
    }

    // ------------ main API ------------
    /**
 * getMarketData(symbol, containerEl?)
 * If you know the exact quoteboard DOM node, pass it as containerEl to force scope.
 */
    function getMarketData(inputSymbol, containerEl){
        containerEl = document.querySelector('.quoteboard.module.data-table.compact-data-table');
        log.info('getMarketData: called', { inputSymbol, scoped: !!containerEl });

        const found = findQuoteRow(inputSymbol, containerEl);
        if (!found){ log.warn('getMarketData: row not found'); return null; }

        const { row, tableEl } = found;
        const header = getHeaderMapStrict(tableEl);
        if (!header){
            log.warn('getMarketData: header map missing; falling back to static indices {0,4,5}', { tablePath: cssPath(tableEl) });
        }

        const cells = row.querySelectorAll(':scope .public_fixedDataTableCell_cellContent');
        log.debug('getMarketData: row cell count', { count: cells.length, tablePath: cssPath(tableEl) });

        const symIdx = header?.getIndex('symbol', 0) ?? 0;
        const bidIdx = header?.getIndex('bid',    4) ?? 4;
        const askIdx = header?.getIndex('ask',    5) ?? 5;

        const at = (i)=> norm(cells[i]?.textContent);
        const symbol = at(symIdx);
        let bidPrice = at(bidIdx);
        let offerPrice = at(askIdx);

        log.info('getMarketData: initial extraction', { symIdx, bidIdx, askIdx, symbol, bidPrice, offerPrice });

        const tryNeighbor = (idx, label)=>{
            const r = at(idx+1), l = at(idx-1);
            if (isPriceLike(r)){ log.warn(`getMarketData: ${label} shifted +1`, { value:r }); return r; }
            if (isPriceLike(l)){ log.warn(`getMarketData: ${label} shifted -1`, { value:l }); return l; }
            return at(idx);
        };
        if (!isPriceLike(bidPrice))   bidPrice   = tryNeighbor(bidIdx, 'bidPrice');
        if (!isPriceLike(offerPrice)) offerPrice = tryNeighbor(askIdx, 'offerPrice');

        const ok = isPriceLike(bidPrice) && isPriceLike(offerPrice);
        if (!ok){
            log.warn('getMarketData: non price-like after fallback', {
                tablePath: cssPath(tableEl),
                headers: header?.headers, symbol, bidPrice, offerPrice
            });
        } else {
            log.info('getMarketData: success', { tablePath: cssPath(tableEl), symbol, bidPrice, offerPrice });
        }
        return { symbol, bidPrice, offerPrice };
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

})();
