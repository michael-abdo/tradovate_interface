// ==UserScript==
// @name         Auto Order
// @namespace    http://tampermonkey.net/
// @version      5.4
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
    const savedLeft = localStorage.getItem('bracketTradeBoxLeft');
    const savedTop  = localStorage.getItem('bracketTradeBoxTop');
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
                    <input type="number" id="tpInput" value="${storedTP}"
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
                    <input type="number" id="slInput" value="${storedSL}"
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
                    <input type="number" id="entryPriceInput" placeholder="Entry" step="0.01"
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
            <div style="display:flex;gap:10px;margin-top:6px;">
                <button id="reverseBtn" style="flex:1;padding:12px 8px;background:#ff6600;color:#fff;border:none;border-radius:4px;font-weight:bold;">Reverse</button>
            </div>
        </div>`;

        document.body.appendChild(container);
        console.log('UI container added to DOM');

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
                
                // Call the clickExitForSymbol function with the normalized symbol and Exit at Mkt option
                clickExitForSymbol(normalizedSymbol, 'cancel-option-Exit-at-Mkt-Cxl');
                console.log('Exit action triggered for symbol:', normalizedSymbol);
            } catch (err) {
                console.error("Close All operation failed:", err);
                
                // Fallback to old method if the new method fails
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
                
                // Call the clickExitForSymbol function with the normalized symbol and Cancel All option
                clickExitForSymbol(normalizedSymbol, 'cancel-option-Cancel-All');
                console.log('Cancel All action triggered for symbol:', normalizedSymbol);
            } catch (err) {
                console.error("Cancel All operation failed:", err);
            }
        });
        
        // Add event listener for the Reverse button
        document.getElementById('reverseBtn').addEventListener('click', () => {
            console.log('Reverse Position button clicked');
            try {
                const symbol = document.getElementById('symbolInput').value || 'NQ';
                const normalizedSymbol = normalizeSymbol(symbol);
                console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Reverse & Cxl option`);
                
                // Call the clickExitForSymbol function with the normalized symbol and Reverse option
                clickExitForSymbol(normalizedSymbol, 'cancel-option-Reverse-Cxl');
                console.log('Reverse Position action triggered for symbol:', normalizedSymbol);
            } catch (err) {
                console.error("Reverse Position operation failed:", err);
            }
        });

        // No toggle for tick container - it remains permanently hidden

        // Persist settings inputs
        console.log('Setting up persistent settings');
        document.getElementById('symbolInput').value = localStorage.getItem('bracketTrade_symbol') || 'NQ';
        document.getElementById('symbolInput').addEventListener('input', e => {
            console.log(`Symbol input changed to: ${e.target.value}`);
            localStorage.setItem('bracketTrade_symbol', e.target.value);
        });

        // 👉 automatically push change into Tradovate ticket
        document.getElementById('symbolInput').addEventListener('change', e => {
            const symbolValue = e.target.value;
            const normalizedSymbol = normalizeSymbol(symbolValue);
            console.log(`Symbol changed to: ${symbolValue}, normalized: ${normalizedSymbol}`);

            // Update TP and SL based on the symbol's default values
            const rootSymbol = symbolValue.replace(/[A-Z]\d+$/, '');
            const symbolDefaults = futuresTickData[rootSymbol];

            if (symbolDefaults) {
                console.log(`Found default values for ${rootSymbol}: SL=${symbolDefaults.defaultSL}, TP=${symbolDefaults.defaultTP}`);

                // Update SL/TP inputs with default values for the selected symbol
                const slInput = document.getElementById('slInput');
                const tpInput = document.getElementById('tpInput');
                const tickInput = document.getElementById('tickInput');

                slInput.value = symbolDefaults.defaultSL;
                tpInput.value = symbolDefaults.defaultTP;

                // Update tick size if available
                if (typeof symbolDefaults.tickSize === 'number') {
                    tickInput.value = symbolDefaults.tickSize;
                    localStorage.setItem('bracketTrade_tick', symbolDefaults.tickSize);
                    console.log(`Updated tick size to ${symbolDefaults.tickSize} for ${rootSymbol}`);
                }

                // Save to localStorage
                localStorage.setItem('bracketTrade_sl', symbolDefaults.defaultSL);
                localStorage.setItem('bracketTrade_tp', symbolDefaults.defaultTP);

                console.log(`Updated SL/TP to default values for ${rootSymbol}: SL=${slInput.value}, TP=${tpInput.value}`);
            }

            // Update the symbol in Tradovate's interface
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
                // Limit logging to reduce console spam
                if (e.clientX % 20 === 0) {
                    console.log(`Dragging panel to X:${newLeft}, Y:${newTop}`);
                }
                container.style.left = newLeft;
                container.style.top = newTop;
                container.style.right = 'unset';
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
                // Reset price inputs after order is placed
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
                // Reset price inputs after order is placed
                document.getElementById('entryPriceInput').value = '';
                document.getElementById('tpPriceInput').value = '';
                document.getElementById('slPriceInput').value = '';
                console.log('Price inputs reset after SELL order');
            });
        });
    }


    // Function to click dropdown option for a specific symbol
    function clickExitForSymbol(symbol, optionId = 'cancel-option-Exit-at-Mkt-Cxl') {
        console.log(`clickExitForSymbol called for symbol: ${symbol}, option: ${optionId}`);
        const modules = document.querySelectorAll('.module.module-dom');
        for (const module of modules) {
            const symEl = module.querySelector('.contract-symbol span');
            if (symEl && symEl.textContent.trim() === symbol) {
                console.log(`Found matching module for symbol: ${symbol}`);
                
                // First, click the dropdown button to open the menu
                const dropdownBtn = module.querySelector('button.btn.dropdown-toggle');
                if (dropdownBtn) {
                    console.log('Clicking dropdown button');
                    dropdownBtn.click();
                    
                    // Give the dropdown menu time to appear
                    setTimeout(() => {
                        // Look for visible dropdown menu WITHIN this module or closest to it
                        const dropdownMenu = module.querySelector('.dropdown-menu') || 
                                            document.querySelector('.dropdown-menu[style*="display: block"]');
                        
                        if (dropdownMenu) {
                            console.log('Found dropdown menu');
                            // Find the option within the dropdown menu by ID
                            const option = dropdownMenu.querySelector(`#${optionId}`);
                            
                            if (option) {
                                console.log(`Found and clicking option: ${optionId} within the correct dropdown`);
                                option.click();
                            } else {
                                console.error(`Option ${optionId} not found in this module's dropdown`);
                                
                                // Try finding by option text if ID doesn't work
                                const optionByText = Array.from(dropdownMenu.querySelectorAll('a[role="menuitem"]'))
                                    .find(link => link.textContent.includes('Exit at Mkt'));
                                
                                if (optionByText) {
                                    console.log('Found option by text: Exit at Mkt');
                                    optionByText.click();
                                } else {
                                    // Fallback to Exit at Mkt button if dropdown option not found
                                    const exitBtn = Array.from(module.querySelectorAll('button.btn.btn-default'))
                                        .find(btn => btn.textContent.replace(/\s+/g, ' ').includes('Exit at Mkt'));
                                    if (exitBtn) {
                                        console.log('Fallback to Exit at Mkt button');
                                        exitBtn.click();
                                    } else {
                                        console.error('No Exit at Mkt button found either');
                                    }
                                }
                            }
                        } else {
                            console.error('Dropdown menu not found or not visible');
                            
                            // Fallback to Exit at Mkt button
                            const exitBtn = Array.from(module.querySelectorAll('button.btn.btn-default'))
                                .find(btn => btn.textContent.replace(/\s+/g, ' ').includes('Exit at Mkt'));
                            if (exitBtn) {
                                console.log('Fallback to Exit at Mkt button');
                                exitBtn.click();
                            } else {
                                console.error('No Exit at Mkt button found either');
                            }
                        }
                    }, 200); // Increased delay to ensure dropdown is visible
                } else {
                    console.error('Dropdown button not found');
                    
                    // Fallback to original behavior
                    const exitBtn = Array.from(module.querySelectorAll('button.btn.btn-default'))
                        .find(btn => btn.textContent.replace(/\s+/g, ' ').includes('Exit at Mkt'));
                    if (exitBtn) {
                        console.log('Fallback to Exit at Mkt button');
                        exitBtn.click();
                    } else {
                        console.error('No Exit at Mkt button found either');
                    }
                }
                break; // stop after first match
            }
        }
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

        async function submitOrder(orderType, priceValue) {
            await setCommonFields();

            const typeSel = document.querySelector('.group.order-type .select-input div[tabindex]');
            typeSel?.click();
            [...document.querySelectorAll('ul.dropdown-menu li')]
                .find(li => li.textContent.trim() === orderType)
                ?.click();

            //await delay(400);               // NEW - let Tradovate draw the price box

            if (priceValue)
                await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);
            clickPriceArrow();

            document.querySelector('.btn-group .btn-primary')?.click();
            await delay(200);
            console.log(getOrderEvents());
            
            // 🔄 CAPTURE ORDER FEEDBACK BEFORE CLICKING BACK BUTTON
            await captureOrderFeedback();
            
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
      const rows = container.querySelectorAll(
        '.order-history-content .public_fixedDataTable_bodyRow'
      );

      return Array.from(rows, row => {
        const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
        const timestamp = cells[0]?.textContent.trim() || '';
        const id        = cells[1]?.textContent.trim() || '';
        const eventTxt  = cells[2]?.textContent.trim() || '';
        const comment   = cells[3]?.textContent.trim() || '';

        // extract fill price patterns like "1@18747.25 NQM5"
        let fillPrice = null;
        const m = eventTxt.match(/@([\d.]+)/);
        if (m) fillPrice = Number(m[1]);

        return { timestamp, id, event: eventTxt, comment, fillPrice };
      });
    }

    // 🔄 CAPTURE TRADOVATE ORDER FEEDBACK SYSTEM
    async function captureOrderFeedback() {
        console.log('🔄 CAPTURING TRADOVATE ORDER FEEDBACK...');
        
        // Wait a moment for order feedback to load
        await delay(500);
        
        // Look for the order history container
        const orderHistoryDiv = document.querySelector('.order-history');
        if (!orderHistoryDiv) {
            console.log('❌ Order history div not found - no feedback to capture');
            return;
        }
        
        console.log('✅ Found order history div - capturing feedback...');
        
        // Extract the trading ticket header information
        const ticketHeader = orderHistoryDiv.querySelector('.trading-ticket-header');
        if (ticketHeader) {
            // Extract symbol info
            const symbolDiv = ticketHeader.querySelector('div[style*="font-size: 160%"]');
            const symbol = symbolDiv ? symbolDiv.textContent.trim() : 'UNKNOWN';
            
            // Extract order summary
            const orderSummaryDiv = ticketHeader.querySelector('div:last-child');
            const orderSummary = orderSummaryDiv ? orderSummaryDiv.textContent.trim() : 'No summary';
            
            console.log(`📊 ORDER FEEDBACK - Symbol: ${symbol}`);
            console.log(`📊 ORDER FEEDBACK - Summary: ${orderSummary}`);
        }
        
        // Extract detailed order events from the data table
        const orderEvents = getOrderEvents(orderHistoryDiv);
        console.log(`📊 ORDER FEEDBACK - Events (${orderEvents.length} found):`);
        
        orderEvents.forEach((event, index) => {
            console.log(`📊 EVENT ${index + 1}:`, {
                timestamp: event.timestamp,
                id: event.id,
                event: event.event,
                comment: event.comment,
                fillPrice: event.fillPrice
            });
        });
        
        // Extract the entire order history HTML for complete analysis
        console.log('📊 ORDER FEEDBACK - Full HTML Structure:');
        console.log(orderHistoryDiv.outerHTML);
        
        // Check for specific rejection reasons or success indicators
        const rejectionText = orderHistoryDiv.textContent;
        if (rejectionText.includes('Rejected')) {
            console.log('❌ ORDER REJECTED - checking rejection reason...');
            if (rejectionText.includes('outside of market hours')) {
                console.log('❌ REJECTION REASON: Order placed outside market hours');
            } else if (rejectionText.includes('Risk')) {
                console.log('❌ REJECTION REASON: Risk management violation');
            } else {
                console.log('❌ REJECTION REASON: Other - check full feedback above');
            }
        } else if (rejectionText.includes('Risk Passed')) {
            console.log('✅ RISK MANAGEMENT: Order passed risk checks');
        }
        
        console.log('🔄 ORDER FEEDBACK CAPTURE COMPLETE');
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

        const symbolInput = document.getElementById('symbolInput').value || 'NQ';
        console.log(`Using symbol: ${symbolInput}`);

        // Get root symbol (e.g., 'NQH5' -> 'NQ')
        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '');
        console.log(`Root symbol: ${rootSymbol}`);

        // Get tick size and default values from dictionary or fallback
        const symbolData = futuresTickData[rootSymbol];

        // Keep track of the last symbol to handle symbol changes
        if (rootSymbol !== autoTrade.lastRootSymbol) {
           document.getElementById('tickInput').value = symbolData?.tickSize ?? '';
        }
        autoTrade.lastRootSymbol = rootSymbol;
        const tickSize = (symbolData && typeof symbolData.tickSize === 'number')
               ? symbolData.tickSize
               : parseFloat(document.getElementById('tickInput').value) || _tickSize;

        // right after tickSize is determined
        tickInput.value = tickSize;           // shows the real value
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
            console.log(`No custom entry price provided, using market order at ${marketPrice}`);
        }

        // Get the correct decimal precision for this instrument
        const decimalPrecision = symbolData?.precision ?? 2; // Default to 2 if not specified
        console.log(`Using price precision: ${decimalPrecision} decimal places`);

        // Check if hardcoded SL/TP prices are provided
        const slPriceInput = document.getElementById('slPriceInput');
        const tpPriceInput = document.getElementById('tpPriceInput');
        
        // Get hardcoded prices if they exist
        const hardcodedSLPrice = slPriceInput && slPriceInput.value ? parseFloat(slPriceInput.value) : null;
        const hardcodedTPPrice = tpPriceInput && tpPriceInput.value ? parseFloat(tpPriceInput.value) : null;
        
        // Determine SL price - use hardcoded if available, otherwise calculate based on ticks
        let stopLossPrice;
        if (hardcodedSLPrice !== null) {
            stopLossPrice = hardcodedSLPrice.toFixed(decimalPrecision);
            console.log(`Using hardcoded SL price: ${stopLossPrice}`);
        } else {
            stopLossPrice = (action === 'Buy'
                ? entryPrice - actualStopLossTicks * tickSize
                : entryPrice + actualStopLossTicks * tickSize).toFixed(decimalPrecision);
            console.log(`Calculated SL price: ${stopLossPrice} (${action === 'Buy' ? 'entry - ' : 'entry + '}${actualStopLossTicks} ticks)`);
        }

        // Determine TP price - use hardcoded if available, otherwise calculate based on ticks
        let takeProfitPrice;
        if (hardcodedTPPrice !== null) {
            takeProfitPrice = hardcodedTPPrice.toFixed(decimalPrecision);
            console.log(`Using hardcoded TP price: ${takeProfitPrice}`);
        } else {
            takeProfitPrice = (action === 'Buy'
                ? entryPrice + actualTakeProfitTicks * tickSize
                : entryPrice - actualTakeProfitTicks * tickSize).toFixed(decimalPrecision);
            console.log(`Calculated TP price: ${takeProfitPrice} (${action === 'Buy' ? 'entry + ' : 'entry - '}${actualTakeProfitTicks} ticks)`);
        }

        const tradeData = {
            symbol: marketData.symbol,
            action,
            qty: quantity.toString(),
            takeProfit: takeProfitPrice,
            stopLoss: stopLossPrice,
            orderType: orderType,
            entryPrice: orderType !== 'MARKET' ? entryPrice.toFixed(decimalPrecision) : null
        };
        console.log('Trade data prepared:', tradeData);

        console.log('Submitting bracket orders');
        return createBracketOrdersManual(tradeData).finally(() => {
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
        });
    }


    // helper – builds the front-quarter code for any root (e.g. 'NQ' → 'NQU5' or 'NQZ5' post-roll)
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

        const symbol = /^[A-Z]{1,3}$/.test(inputSymbol)
        ? getFrontQuarter(inputSymbol)
        : inputSymbol.toUpperCase();
        console.log(`Using symbol: "${symbol}" for market data lookup`);

        // Walk the fixedDataTable rows and match the Symbol column (first cell)
        const root = document.querySelector('.quoteboard.module.data-table') || document;
        const rows = root.querySelectorAll('.public_fixedDataTable_bodyRow');

        let targetRow = null;
        for (const row of rows) {
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            if (!cells.length) continue;

            const symCell = cells[0];
            const cellText = (symCell.textContent || '').trim().toUpperCase();
            if (cellText === symbol) {
                targetRow = row;
                break;
            }
        }

        if (!targetRow) {
            console.error(`Row for symbol "${symbol}" not found in data table`);
            alert(`Cannot Find ${inputSymbol}`);
            return null;
        }

        // Column order: [0]=Symbol, [1]=Last, [2]=Change, [3]=%Change, [4]=Bid, [5]=Offer, [6]=Open, [7]=High, [8]=Low, [9]=Total Vol.
        const cells = targetRow.querySelectorAll('.public_fixedDataTableCell_cellContent');
        const bidPrice   = cells[4]?.textContent.trim();
        const offerPrice = cells[5]?.textContent.trim();

        console.log(`Extracted prices for ${symbol}: bid=${bidPrice}, offer=${offerPrice}`);
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
     * Returns ACTIVE quarterly contract code honoring CME roll (Mon before 3rd Fri).
     * We approximate with UTC date flip on the 3rd Friday; CT session flip occurs the evening prior.
     * Example: On/after 2025-09-19 UTC → { letter:'Z', yearDigit:'5' }
     */
    function getQuarterlyCode(date = new Date()) {
        console.log(`getQuarterlyCode called with date: ${date.toISOString()}`);
        const QUARTER_MONTHS = [2, 5, 8, 11];            // Mar, Jun, Sep, Dec
        const LETTERS = { 2:'H', 5:'M', 8:'U', 11:'Z' };

        function thirdFridayUTC(y, m) {
            const d1 = new Date(Date.UTC(y, m, 1));
            const firstDow = d1.getUTCDay();             // 0=Sun..5=Fri..6=Sat
            const offsetToFri = (5 - firstDow + 7) % 7;  // days to first Friday
            const day = 1 + offsetToFri + 14;            // 3rd Friday
            return new Date(Date.UTC(y, m, day, 0, 0, 0));
        }

        let y = date.getUTCFullYear();
        let m = date.getUTCMonth();
        console.log(`Current month index: ${m}`);
        console.log(`Starting calculation with year=${y}, month=${m}`);

        // bump forward until we land on a quarter month
        let iter = 0;
        while (!QUARTER_MONTHS.includes(m)) {
            m++;
            if (m > 11) { m = 0; y++; }
            if (++iter > 12) break;
        }

        const rollDate = thirdFridayUTC(y, m);
        // If we've reached/passed the UTC roll date, advance to next quarter
        if (date.getTime() >= rollDate.getTime()) {
            m += 3;
            if (m > 11) { m -= 12; y++; }
        }

        const result = { letter: LETTERS[m], yearDigit: (y % 10) + '' };
        console.log(`Calculated quarterly code: letter=${result.letter}, yearDigit=${result.yearDigit}`);
        return result;
    }

    // --- EXAMPLE: build an NQ front-quarter symbol ---
    console.log('Creating example front-quarter symbol');
    const { letter, yearDigit } = getQuarterlyCode();
    const nqFront = `NQ${letter}${yearDigit}`;
    console.log(`Example front-quarter symbol created: ${nqFront}`);

})();