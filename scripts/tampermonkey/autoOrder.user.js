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
    console.log('Auto Order script initialized - AUTOMATIC HOT RELOAD SUCCESS!');
    var debug = false;

    function delay(ms) {
        console.log(`Delaying for ${ms}ms`);
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Scale-in utility functions
    function updateQuantitySplit() {
        const quantitySplitDiv = document.getElementById('quantitySplit');
        if (!quantitySplitDiv) return;
        
        const scaleEnabled = document.getElementById('scaleInCheckbox')?.checked;
        if (!scaleEnabled) {
            quantitySplitDiv.textContent = '';
            return;
        }
        
        const quantity = parseInt(document.getElementById('qtyInput')?.value || '0');
        const levels = parseInt(document.getElementById('scaleLevelsInput')?.value || '4');
        
        if (quantity > 0 && levels > 0) {
            const qtyPerLevel = quantity / levels;
            quantitySplitDiv.textContent = `${quantity} ÷ ${levels} = ${qtyPerLevel.toFixed(1)} per level`;
        } else {
            quantitySplitDiv.textContent = '';
        }
    }
    
    function updateTickValue() {
        const tickValueDiv = document.getElementById('tickValue');
        if (!tickValueDiv) return;
        
        const scaleEnabled = document.getElementById('scaleInCheckbox')?.checked;
        if (!scaleEnabled) {
            tickValueDiv.textContent = '';
            return;
        }
        
        const spacing = parseInt(document.getElementById('scaleSpacingInput')?.value || '0');
        const symbol = document.getElementById('symbolInput')?.value || 'NQ';
        
        // Get tick value from futuresTickData or default values
        const tickData = window.futuresTickData[symbol] || { tickValue: 5.0 };
        const tickValue = tickData.tickValue || 5.0;
        const dollarValue = spacing * tickValue;
        
        if (spacing > 0) {
            tickValueDiv.textContent = `${spacing} ticks = $${dollarValue.toFixed(2)} for ${symbol}`;
        } else {
            tickValueDiv.textContent = '';
        }
    }

    function createUI(visible = false) {
        console.log(`Creating UI (visible=${visible})`);
        const storedTP   = localStorage.getItem('bracketTrade_tp')  || '53';
        const storedSL   = localStorage.getItem('bracketTrade_sl')  || '15';
        const storedQty  = localStorage.getItem('bracketTrade_qty') || '10';
        const storedTick = localStorage.getItem('bracketTrade_tick')|| '0.25';
        const storedSym  = localStorage.getItem('bracketTrade_symbol') || 'NQ';
        const storedScaleEnabled = localStorage.getItem('bracketTrade_scaleEnabled') === 'true';
        const storedScaleLevels = localStorage.getItem('bracketTrade_scaleLevels') || '4';
        const storedScaleSpacing = localStorage.getItem('bracketTrade_scaleSpacing') || '20';
        console.log(`Stored values: TP=${storedTP}, SL=${storedSL}, Qty=${storedQty}, Tick=${storedTick}, Symbol=${storedSym}`);

        const container = document.createElement('div');
        container.id = visible ? 'bracket-trade-box' : 'invisible-trade-inputs';
        
        if (visible) {
            // Visible UI styling
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
        } else {
            // Invisible UI - off-screen
            Object.assign(container.style, {
                position: 'fixed',
                top: '-9999px',
                left: '-9999px',
                visibility: 'hidden',
                opacity: '0',
                pointerEvents: 'none'
            });
        }

        // Create different HTML based on visibility
        if (visible) {
            // Full visible UI with all controls
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
                
                <!-- Scale In Controls -->
                <div style="margin-bottom:12px;border-top:1px solid #444;padding-top:8px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <input type="checkbox" id="scaleInCheckbox" ${storedScaleEnabled ? 'checked' : ''}
                            style="cursor:pointer;" />
                        <label for="scaleInCheckbox" style="font-size:12px;cursor:pointer;">Scale In</label>
                        <div id="quantitySplit" style="font-size:10px;color:#999;margin-left:auto;"></div>
                    </div>
                    <div id="scaleControls" style="display:${storedScaleEnabled ? 'block' : 'none'};">
                        <div style="display:flex;gap:4px;margin-bottom:4px;">
                            <div style="flex:1;">
                                <label style="display:block;font-size:10px;color:#999;margin-bottom:2px;">Levels</label>
                                <input type="number" id="scaleLevelsInput" value="${storedScaleLevels}" min="1" max="8"
                                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;font-size:12px;" />
                            </div>
                            <div style="flex:1;">
                                <label style="display:block;font-size:10px;color:#999;margin-bottom:2px;">Spacing</label>
                                <input type="number" id="scaleSpacingInput" value="${storedScaleSpacing}" min="1"
                                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;font-size:12px;" />
                            </div>
                        </div>
                        <div id="tickValue" style="font-size:10px;color:#999;text-align:center;"></div>
                    </div>
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
        } else {
            // Invisible UI - only essential inputs
            container.innerHTML = `
                <input type="text" id="symbolInput" value="${storedSym}" />
                <input type="number" id="tickInput" value="${storedTick}" />
                <input type="number" id="tpInput" value="${storedTP}" />
                <input type="number" id="slInput" value="${storedSL}" />
                <input type="number" id="qtyInput" value="${storedQty}" />
                <input type="number" id="entryPriceInput" />
                <input type="number" id="tpPriceInput" />
                <input type="number" id="slPriceInput" />
                <input type="checkbox" id="tpCheckbox" checked />
                <input type="checkbox" id="slCheckbox" checked />
                <input type="checkbox" id="scaleInCheckbox" ${storedScaleEnabled ? 'checked' : ''} />
                <input type="number" id="scaleLevelsInput" value="${storedScaleLevels}" />
                <input type="number" id="scaleSpacingInput" value="${storedScaleSpacing}" />
                <div id="scaleControls"></div>
                <div id="quantitySplit"></div>
                <div id="tickValue"></div>
            `;
        }

        // Don't create if it already exists
        const existingId = visible ? 'bracket-trade-box' : 'invisible-trade-inputs';
        if (document.getElementById(existingId)) {
            console.log(`${existingId} already exists, skipping creation`);
            return;
        }
        
        document.body.appendChild(container);
        console.log('UI container added to DOM');

        // --- UI events (only for visible UI) ---
        if (visible) {
            console.log('Setting up UI event handlers');
        const slInput  = document.getElementById('slInput');
        const tpInput  = document.getElementById('tpInput');
        const qtyInput = document.getElementById('qtyInput');
        document.getElementById('slInput').addEventListener('input', () => {
            console.log(`SL input changed to: ${slInput.value}`);
            const slVal = parseFloat(slInput.value);
            if (!isNaN(slVal)) {
                tpInput.value = Math.round(slVal * 3.5);
                console.log(`Calculated TP: ${tpInput.value} (SL × 3.5)`);
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
            updateQuantitySplit(); // Update scale quantity display
        });
        
        // Scale In Controls Event Handlers
        document.getElementById('scaleInCheckbox').addEventListener('change', e => {
            console.log(`Scale In checkbox changed to: ${e.target.checked}`);
            localStorage.setItem('bracketTrade_scaleEnabled', e.target.checked);
            
            const scaleControls = document.getElementById('scaleControls');
            if (scaleControls) {
                scaleControls.style.display = e.target.checked ? 'block' : 'none';
            }
            updateQuantitySplit();
        });
        
        document.getElementById('scaleLevelsInput').addEventListener('input', e => {
            console.log(`Scale levels input changed to: ${e.target.value}`);
            localStorage.setItem('bracketTrade_scaleLevels', e.target.value);
            updateQuantitySplit();
        });
        
        document.getElementById('scaleSpacingInput').addEventListener('input', e => {
            console.log(`Scale spacing input changed to: ${e.target.value}`);
            localStorage.setItem('bracketTrade_scaleSpacing', e.target.value);
            updateTickValue();
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
        
        // Add event listener for the Breakeven button
        document.getElementById('breakevenBtn').addEventListener('click', () => {
            console.log('Breakeven button clicked');
            try {
                const symbol = document.getElementById('symbolInput').value || 'NQ';
                const normalizedSymbol = normalizeSymbol(symbol);
                console.log(`Processing breakeven for symbol: ${normalizedSymbol}`);
                
                // Call the breakeven function
                moveStopLossToBreakeven(normalizedSymbol);
                console.log('Breakeven action triggered for symbol:', normalizedSymbol);
            } catch (err) {
                console.error("Breakeven operation failed:", err);
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
            const symbolDefaults = window.futuresTickData[rootSymbol];

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
                
                // Update scale-in defaults for the selected symbol
                const scaleLevelsInput = document.getElementById('scaleLevelsInput');
                const scaleSpacingInput = document.getElementById('scaleSpacingInput');
                
                if (scaleLevelsInput && scaleSpacingInput) {
                    // Get scale defaults from symbol configuration
                    const scaleInLevels = symbolDefaults.scale_in_levels || 4;
                    const scaleInTicks = symbolDefaults.scale_in_ticks || 20;
                    
                    // Update the input fields
                    scaleLevelsInput.value = scaleInLevels;
                    scaleSpacingInput.value = scaleInTicks;
                    
                    // Save to localStorage
                    localStorage.setItem('bracketTrade_scaleLevels', scaleInLevels);
                    localStorage.setItem('bracketTrade_scaleSpacing', scaleInTicks);
                    
                    console.log(`Updated scale defaults for ${rootSymbol}: Levels=${scaleInLevels}, Spacing=${scaleInTicks}`);
                    
                    // Update displays
                    updateQuantitySplit();
                    updateTickValue();
                }
            }

            // Update the symbol in Tradovate's interface
            // FIXED: Use more specific selector for order ticket instead of market analyzer
            // Old selector '.search-box--input' was too generic and hit market analyzer first
            updateSymbol('.trading-ticket.module-placement.width-1-3 .search-box--input', normalizedSymbol);
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

        // Initialize scale displays on UI creation
        console.log('Initializing scale displays');
        updateQuantitySplit();
        updateTickValue();

        // Trade buttons
        console.log('Setting up trade buttons');
        document.getElementById('buyBtn').addEventListener('click', () => {
            console.log('[BUTTON] 🟢 ========== BUY BUTTON CLICKED ==========');
            console.log('[BUTTON] 📍 STEP 1: Button click event triggered');
            
            // Gather all input values with detailed logging
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const qty = +qtyInput.value;
            const tp = +tpInput.value;
            const sl = +slInput.value;
            const tickSize = +document.getElementById('tickInput').value;
            const entryPrice = document.getElementById('entryPriceInput').value;
            const scaleEnabled = document.getElementById('scaleInCheckbox')?.checked;
            
            console.log('[BUTTON] 📍 STEP 2: Input values gathered:');
            console.log(`[BUTTON]   Symbol: "${symbol}"`);
            console.log(`[BUTTON]   Quantity: ${qty} (type: ${typeof qty})`);
            console.log(`[BUTTON]   Take Profit: ${tp} ticks (type: ${typeof tp})`);
            console.log(`[BUTTON]   Stop Loss: ${sl} ticks (type: ${typeof sl})`);
            console.log(`[BUTTON]   Tick Size: ${tickSize} (type: ${typeof tickSize})`);
            console.log(`[BUTTON]   Entry Price: "${entryPrice}" (${entryPrice ? 'LIMIT/STOP ORDER' : 'MARKET ORDER'})`);
            console.log(`[BUTTON]   Scale-In Enabled: ${scaleEnabled}`);
            
            // Validate inputs before proceeding
            console.log('[BUTTON] 📍 STEP 3: Validating inputs...');
            if (!symbol || symbol.trim() === '') {
                console.error('[BUTTON] ❌ VALIDATION FAILED: Symbol is empty');
                alert('Error: Symbol cannot be empty');
                return;
            }
            if (!qty || qty <= 0 || isNaN(qty)) {
                console.error('[BUTTON] ❌ VALIDATION FAILED: Invalid quantity');
                alert('Error: Quantity must be a positive number');
                return;
            }
            if (!tickSize || tickSize <= 0 || isNaN(tickSize)) {
                console.error('[BUTTON] ❌ VALIDATION FAILED: Invalid tick size');
                alert('Error: Tick size must be a positive number');
                return;
            }
            console.log('[BUTTON] ✅ VALIDATION PASSED: All inputs are valid');
            
            console.log('[BUTTON] 📍 STEP 4: Checking scale-in before calling autoTrade...');
            console.log(`[BUTTON]   Scale-In Enabled: ${scaleEnabled}`);
            if (scaleEnabled) {
                const scaleLevels = document.getElementById('scaleLevelsInput')?.value || '4';
                const scaleSpacing = document.getElementById('scaleSpacingInput')?.value || '20';
                console.log(`[BUTTON]   Scale Levels: ${scaleLevels}, Scale Spacing: ${scaleSpacing}`);
            }
            console.log(`[BUTTON]   Parameters: autoTrade("${symbol}", ${qty}, "Buy", ${tp}, ${sl}, ${tickSize})`);
            
            // Call autoTrade and handle the result
            try {
                const result = autoTrade(symbol, qty, 'Buy', tp, sl, tickSize);
                if (result && typeof result.finally === 'function') {
                    result.finally(() => {
                        // Reset price inputs after order is placed
                        document.getElementById('entryPriceInput').value = '';
                        document.getElementById('tpPriceInput').value = '';
                        document.getElementById('slPriceInput').value = '';
                        console.log('[BUTTON] 📍 STEP 5: Price inputs reset after BUY order');
                        console.log('[BUTTON] 🟢 ========== BUY PIPELINE COMPLETE ==========');
                    });
                } else {
                    // Reset inputs immediately if no promise returned
                    document.getElementById('entryPriceInput').value = '';
                    document.getElementById('tpPriceInput').value = '';
                    document.getElementById('slPriceInput').value = '';
                    console.log('[BUTTON] 📍 STEP 5: Price inputs reset after BUY order (synchronous)');
                    console.log('[BUTTON] 🟢 ========== BUY PIPELINE COMPLETE ==========');
                }
            } catch (err) {
                console.error('[BUTTON] ❌ BUY autoTrade threw exception:', err);
                console.log('[BUTTON] 🔴 ========== BUY PIPELINE FAILED ==========');
            }
        });
        document.getElementById('sellBtn').addEventListener('click', () => {
            console.log('[BUTTON] 🔴 ========== SELL BUTTON CLICKED ==========');
            console.log('[BUTTON] 📍 STEP 1: Button click event triggered');
            
            // Gather all input values with detailed logging
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const qty = +qtyInput.value;
            const tp = +tpInput.value;
            const sl = +slInput.value;
            const tickSize = +document.getElementById('tickInput').value;
            const entryPrice = document.getElementById('entryPriceInput').value;
            const scaleEnabled = document.getElementById('scaleInCheckbox')?.checked;
            
            console.log('[BUTTON] 📍 STEP 2: Input values gathered:');
            console.log(`[BUTTON]   Symbol: "${symbol}"`);
            console.log(`[BUTTON]   Quantity: ${qty} (type: ${typeof qty})`);
            console.log(`[BUTTON]   Take Profit: ${tp} ticks (type: ${typeof tp})`);
            console.log(`[BUTTON]   Stop Loss: ${sl} ticks (type: ${typeof sl})`);
            console.log(`[BUTTON]   Tick Size: ${tickSize} (type: ${typeof tickSize})`);
            console.log(`[BUTTON]   Entry Price: "${entryPrice}" (${entryPrice ? 'LIMIT/STOP ORDER' : 'MARKET ORDER'})`);
            console.log(`[BUTTON]   Scale-In Enabled: ${scaleEnabled}`);
            
            // Validate inputs before proceeding
            console.log('📍 STEP 3: Validating inputs...');
            if (!symbol || symbol.trim() === '') {
                console.error('❌ VALIDATION FAILED: Symbol is empty');
                alert('Error: Symbol cannot be empty');
                return;
            }
            if (!qty || qty <= 0 || isNaN(qty)) {
                console.error('❌ VALIDATION FAILED: Invalid quantity');
                alert('Error: Quantity must be a positive number');
                return;
            }
            if (!tickSize || tickSize <= 0 || isNaN(tickSize)) {
                console.error('❌ VALIDATION FAILED: Invalid tick size');
                alert('Error: Tick size must be a positive number');
                return;
            }
            console.log('✅ VALIDATION PASSED: All inputs are valid');
            
            console.log('[BUTTON] 📍 STEP 4: Checking scale-in before calling autoTrade...');
            console.log(`[BUTTON]   Scale-In Enabled: ${scaleEnabled}`);
            if (scaleEnabled) {
                const scaleLevels = document.getElementById('scaleLevelsInput')?.value || '4';
                const scaleSpacing = document.getElementById('scaleSpacingInput')?.value || '20';
                console.log(`[BUTTON]   Scale Levels: ${scaleLevels}, Scale Spacing: ${scaleSpacing}`);
            }
            console.log(`[BUTTON]   Parameters: autoTrade("${symbol}", ${qty}, "Sell", ${tp}, ${sl}, ${tickSize})`);
            
            // Call autoTrade and handle the result
            try {
                const result = autoTrade(symbol, qty, 'Sell', tp, sl, tickSize);
                if (result && typeof result.finally === 'function') {
                    result.finally(() => {
                        // Reset price inputs after order is placed
                        document.getElementById('entryPriceInput').value = '';
                        document.getElementById('tpPriceInput').value = '';
                        document.getElementById('slPriceInput').value = '';
                        console.log('📍 STEP 5: Price inputs reset after SELL order');
                        console.log('🔴 ========== SELL PIPELINE COMPLETE ==========');
                    });
                } else {
                    // Reset inputs immediately if no promise returned
                    document.getElementById('entryPriceInput').value = '';
                    document.getElementById('tpPriceInput').value = '';
                    document.getElementById('slPriceInput').value = '';
                    console.log('📍 STEP 5: Price inputs reset after SELL order (synchronous)');
                    console.log('🔴 ========== SELL PIPELINE COMPLETE ==========');
                }
            } catch (err) {
                console.error('❌ SELL autoTrade threw exception:', err);
                console.log('🔴 ========== SELL PIPELINE FAILED ==========');
            }
        });
        } // End of visible-only event handlers
        
        // Set up localStorage persistence for key inputs (both visible and invisible)
        console.log('Setting up localStorage persistence');
        ['symbolInput', 'tpInput', 'slInput', 'qtyInput', 'tickInput'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', (e) => {
                    const storageKey = 'bracketTrade_' + id.replace('Input', '');
                    localStorage.setItem(storageKey, e.target.value);
                    console.log(`Saved ${storageKey} = ${e.target.value}`);
                });
            }
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
            // Exact match always wins
            if (got === wantSym) return true;
            
            // For root symbols (e.g., "NQ"), match futures contracts properly
            if (isRoot && got.startsWith(wantSym)) {
                // Check if this is a valid futures symbol (root + month/year code)
                // and not a different product (like MNQ which ends with NQ)
                const afterRoot = got.substring(wantSym.length);
                // Futures symbols have month (letter) and year (number) after root
                // e.g., NQZ5, ESH6, etc.
                const isFuturesFormat = /^[FGHJKMNQUVXZ]\d+$/.test(afterRoot);
                return isFuturesFormat;
            }
            return false;
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
    
    // Function to move stop loss to breakeven for a specific symbol
    function moveStopLossToBreakeven(symbol) {
        console.log(`moveStopLossToBreakeven called for symbol: ${symbol}`);
        
        // First, get current position data to find entry price
        const positionData = getCurrentPosition(symbol);
        if (!positionData) {
            console.log(`No open position found for ${symbol}`);
            return;
        }
        
        console.log(`Found position for ${symbol}:`, positionData);
        
        // Calculate breakeven price (entry price with small buffer for commissions)
        const entryPrice = positionData.entryPrice;
        const isLong = positionData.quantity > 0;
        
        // Get tick size for the symbol
        const rootSymbol = symbol.replace(/[A-Z]\d+$/, '');
        const symbolData = window.futuresTickData[rootSymbol];
        const tickSize = symbolData?.tickSize || 0.25;
        
        // Add small buffer (1-2 ticks) to account for commissions
        const breakevenBuffer = tickSize * 2;
        const breakevenPrice = isLong 
            ? (entryPrice + breakevenBuffer).toFixed(symbolData?.precision || 2)
            : (entryPrice - breakevenBuffer).toFixed(symbolData?.precision || 2);
        
        console.log(`Calculated breakeven price: ${breakevenPrice} (entry: ${entryPrice}, isLong: ${isLong}, buffer: ${breakevenBuffer})`);
        
        // Find and update stop loss orders
        const modules = document.querySelectorAll('.module.module-dom');
        let stopOrdersUpdated = 0;
        
        for (const module of modules) {
            const symEl = module.querySelector('.contract-symbol span');
            const symText = symEl ? symEl.textContent.trim().toUpperCase() : '';
            const symbolUpper = symbol.toUpperCase();
            const isRootSymbol = /^[A-Z]{1,3}$/.test(symbolUpper);
            
            if (symText === symbolUpper || 
                (isRootSymbol && symText.startsWith(symbolUpper) && 
                 /^[FGHJKMNQUVXZ]\d+$/.test(symText.substring(symbolUpper.length)))) {
                // Check if this is a stop order
                const orderTypeEl = module.querySelector('.order-type');
                if (orderTypeEl && orderTypeEl.textContent.includes('STOP')) {
                    console.log(`Found stop order for ${symbol}, updating to breakeven`);
                    
                    // Click on the price field to edit it
                    const priceInput = module.querySelector('input[type="number"], .numeric-input input');
                    if (priceInput) {
                        console.log(`Updating stop price from ${priceInput.value} to ${breakevenPrice}`);
                        
                        // Focus and update the price
                        priceInput.focus();
                        priceInput.value = breakevenPrice;
                        
                        // Trigger change events
                        priceInput.dispatchEvent(new Event('input', { bubbles: true }));
                        priceInput.dispatchEvent(new Event('change', { bubbles: true }));
                        priceInput.dispatchEvent(new KeyboardEvent('keydown', {
                            key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                        }));
                        
                        stopOrdersUpdated++;
                        console.log(`Stop order ${stopOrdersUpdated} updated to breakeven`);
                    } else {
                        console.log('Price input not found for stop order');
                    }
                }
            }
        }
        
        if (stopOrdersUpdated > 0) {
            console.log(`✅ Successfully moved ${stopOrdersUpdated} stop order(s) to breakeven for ${symbol}`);
        } else {
            console.log(`⚠️ No stop orders found to update for ${symbol}`);
        }
    }
    
    // Helper function to get current position data for a symbol
    function getCurrentPosition(symbol) {
        console.log(`getCurrentPosition called for symbol: ${symbol}`);
        
        // Look for position information in the trading interface
        const positionModules = document.querySelectorAll('.module.module-dom');
        
        for (const module of positionModules) {
            const symEl = module.querySelector('.contract-symbol span');
            const symText = symEl ? symEl.textContent.trim().toUpperCase() : '';
            const symbolUpper = symbol.toUpperCase();
            const isRootSymbol = /^[A-Z]{1,3}$/.test(symbolUpper);
            
            if (symText === symbolUpper || 
                (isRootSymbol && symText.startsWith(symbolUpper) && 
                 /^[FGHJKMNQUVXZ]\d+$/.test(symText.substring(symbolUpper.length)))) {
                // Check if this shows position info (not just orders)
                const qtyEl = module.querySelector('.position-quantity, .quantity');
                const priceEl = module.querySelector('.avg-price, .entry-price, .price');
                
                if (qtyEl && priceEl) {
                    const quantity = parseFloat(qtyEl.textContent.replace(/[^\d.-]/g, ''));
                    const entryPrice = parseFloat(priceEl.textContent.replace(/[^\d.-]/g, ''));
                    
                    if (!isNaN(quantity) && !isNaN(entryPrice) && quantity !== 0) {
                        console.log(`Found position: qty=${quantity}, entry=${entryPrice}`);
                        return { quantity, entryPrice };
                    }
                }
            }
        }
        
        // Fallback: try to get position from portfolio/account view
        const portfolioRows = document.querySelectorAll('.portfolio-row, .position-row');
        for (const row of portfolioRows) {
            const symbolCell = row.querySelector('.symbol, .contract-symbol');
            const cellText = symbolCell ? symbolCell.textContent.trim().toUpperCase() : '';
            const symbolUpper = symbol.toUpperCase();
            const isRootSymbol = /^[A-Z]{1,3}$/.test(symbolUpper);
            
            if (cellText === symbolUpper || 
                (isRootSymbol && cellText.startsWith(symbolUpper) && 
                 /^[FGHJKMNQUVXZ]\d+$/.test(cellText.substring(symbolUpper.length)))) {
                const cells = row.querySelectorAll('td, .cell');
                // Try to extract quantity and price from table cells
                for (let i = 0; i < cells.length; i++) {
                    const text = cells[i].textContent.trim();
                    const qty = parseFloat(text.replace(/[^\d.-]/g, ''));
                    if (!isNaN(qty) && qty !== 0) {
                        // Look for price in nearby cells
                        for (let j = i + 1; j < Math.min(i + 4, cells.length); j++) {
                            const priceText = cells[j].textContent.trim();
                            const price = parseFloat(priceText.replace(/[^\d.-]/g, ''));
                            if (!isNaN(price) && price > 0) {
                                console.log(`Found position from portfolio: qty=${qty}, entry=${price}`);
                                return { quantity: qty, entryPrice: price };
                            }
                        }
                    }
                }
            }
        }
        
        console.log(`No position data found for ${symbol}`);
        return null;
    }
    
    // Initialize UI (defaults to invisible inputs only - no visible popup)
    // Create invisible UI elements for backend functionality
    console.log('🔧 Creating invisible UI elements for backend functionality...');
    createUI(false); // false = invisible mode
    console.log('🔧 Invisible UI initialization complete');
    
    // Verify UI elements were created
    console.log('🔧 Verifying UI elements exist:');
    console.log(`  symbolInput: ${document.getElementById('symbolInput') ? 'EXISTS' : 'MISSING'}`);
    console.log(`  qtyInput: ${document.getElementById('qtyInput') ? 'EXISTS' : 'MISSING'}`);
    console.log(`  tickInput: ${document.getElementById('tickInput') ? 'EXISTS' : 'MISSING'}`);
    console.log(`  tpInput: ${document.getElementById('tpInput') ? 'EXISTS' : 'MISSING'}`);
    console.log(`  slInput: ${document.getElementById('slInput') ? 'EXISTS' : 'MISSING'}`);

    async function updateSymbol(selector, value) {
            console.log(`updateSymbol called with selector: "${selector}", value: "${value}"`);
            let inputs = document.querySelectorAll(selector);
            console.log(`Found ${inputs.length} matching inputs with selector: ${selector}`);
            
            // If no inputs found with primary selector, try fallback selectors
            if (inputs.length === 0) {
                const fallbackSelectors = [
                    '.trading-ticket.module-placement.width-1-3 .search-box--input',  // Specific trading ticket module
                    '.trading-ticket input[type="text"]',  // First text input in trading ticket
                    '.order-entry .search-box--input',      // Order entry search box
                    '.order-ticket .search-box--input',     // Order ticket search box  
                    '.search-box--input'                    // Generic fallback (old behavior)
                ];
                
                for (const fallbackSelector of fallbackSelectors) {
                    inputs = document.querySelectorAll(fallbackSelector);
                    if (inputs.length > 0) {
                        console.log(`Using fallback selector: ${fallbackSelector}, found ${inputs.length} inputs`);
                        break;
                    }
                }
            }
            
            // Select the appropriate input - prefer first one now since we're using specific selectors
            const input = inputs[0] || inputs[1];  // Changed order - first is now preferred
            if (!input) {
                console.error('No matching input elements found with any selector!');
                console.error('Tried selectors:', selector, 'and fallbacks');
                return;
            }
            
            // Log which element we're updating for debugging
            console.log('Selected input:', input);
            console.log('Input location:', {
                inTradingTicket: !!input.closest('.trading-ticket'),
                inSpecificTicketModule: !!input.closest('.trading-ticket.module-placement.width-1-3'),
                inMarketAnalyzer: !!input.closest('.market-analyzer, .market-watchlist'),
                parentClasses: input.parentElement?.className,
                placeholder: input.placeholder
            });

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
        console.log(`\n📋 ========== CREATE BRACKET ORDERS MANUAL ==========`);
        console.log(`📍 BRACKET STEP 1: Function called with trade data:`, tradeData);
        
        // CRITICAL FIX: Add null checks for TP/SL checkboxes (may not exist)
        const tpCheckbox = document.getElementById('tpCheckbox');
        const slCheckbox = document.getElementById('slCheckbox');
        const enableTP = tpCheckbox?.checked ?? false; // Default to false if checkbox doesn't exist
        const enableSL = slCheckbox?.checked ?? false; // Default to false if checkbox doesn't exist
        console.log(`📍 BRACKET STEP 2: Bracket settings:`);
        console.log(`  Take Profit enabled: ${enableTP}`);
        console.log(`  Stop Loss enabled: ${enableSL}`);

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
            // CRITICAL FIX: Enable symbol update
            if (tradeData.symbol) {
                console.log(`🎯 Setting symbol to: ${tradeData.symbol}`);
                await updateSymbol('.trading-ticket.module-placement.width-1-3 .search-box--input', normalizeSymbol(tradeData.symbol));
                await delay(500); // Allow symbol to load and stabilize
            }
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
            console.log(`🔧 Starting submitOrder for ${orderType} order`);
            
            await setCommonFields();

            // CRITICAL FIX: Add validation before DOM interactions
            const typeSel = document.querySelector('.group.order-type .select-input div[tabindex]');
            if (!typeSel) {
                console.error('❌ Order type dropdown not found!');
                return {
                    success: false,
                    error: 'Order type dropdown not found',
                    orders: [],
                    symbol: null,
                    summary: null,
                    rejectionReason: 'UI validation error',
                    filledCount: 0,
                    rejectedCount: 1
                };
            }
            
            console.log(`📋 Setting order type to: ${orderType}`);
            typeSel.click();
            await delay(200); // Allow dropdown to open
            
            const orderTypeOption = [...document.querySelectorAll('ul.dropdown-menu li')]
                .find(li => li.textContent.trim() === orderType);
            if (!orderTypeOption) {
                console.error(`❌ Order type option '${orderType}' not found!`);
                return {
                    success: false,
                    error: `Order type option '${orderType}' not found`,
                    orders: [],
                    symbol: null,
                    summary: null,
                    rejectionReason: 'UI validation error',
                    filledCount: 0,
                    rejectedCount: 1
                };
            }
            orderTypeOption.click();

            // CRITICAL FIX: Restore delay to let Tradovate draw the price box
            await delay(500);               // Increased delay for UI stability

            if (priceValue) {
                console.log(`💰 Setting price to: ${priceValue}`);
                await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);
            }
            clickPriceArrow();

            // CRITICAL FIX: Validate submit button exists before clicking
            const submitButton = document.querySelector('.btn-group .btn-primary');
            if (!submitButton) {
                console.error('❌ Submit button not found!');
                return {
                    success: false,
                    error: 'Submit button not found',
                    orders: [],
                    symbol: null,
                    summary: null,
                    rejectionReason: 'UI validation error',
                    filledCount: 0,
                    rejectedCount: 1
                };
            }
            
            console.log('🚀 Clicking submit button...');
            submitButton.click();
            await delay(500); // Increased delay after order submission
            console.log(getOrderEvents());
            
            // CRITICAL FIX: Wait longer for order to appear in history
            console.log('⏳ Waiting for order to appear in history...');
            await delay(1000); // Additional delay for order processing
            
            // 🔄 CAPTURE ORDER FEEDBACK BEFORE CLICKING BACK BUTTON
            console.log('📊 Capturing order feedback from submitOrder...');
            const feedbackResult = await captureOrderFeedback();
            
            // Log the feedback capture result
            if (feedbackResult?.rejectionReason) {
                console.log(`✅ submitOrder captured REJECTION: ${feedbackResult.rejectionReason}`);
            } else if (feedbackResult?.success && feedbackResult?.orders?.length > 0) {
                console.log(`✅ submitOrder captured SUCCESS: ${feedbackResult.orders.length} orders`);
            } else if (feedbackResult?.error) {
                console.log(`⚠️ submitOrder captured ERROR: ${feedbackResult.error}`);
            } else {
                console.log('⚠️ submitOrder captured UNKNOWN result:', feedbackResult);
            }
            
            document.querySelector('.icon.icon-back')?.click();
            await delay(200);
            
            // Return the captured feedback result
            return feedbackResult;
        }

        console.log(`📍 BRACKET STEP 3: Submitting initial ${tradeData.orderType || 'MARKET'} order...`);
        console.log(`  Order type: ${tradeData.orderType || 'MARKET'}`);
        console.log(`  Entry price: ${tradeData.entryPrice || 'Market price'}`);
        console.log(`  Action: ${tradeData.action}`);
        console.log(`  Quantity: ${tradeData.qty}`);
        
        // Capture feedback from the main entry order
        const mainOrderResult = await submitOrder(tradeData.orderType || 'MARKET', tradeData.entryPrice);
        console.log(`📊 Main order result:`, mainOrderResult);
        
        // Initialize bracket feedback aggregation
        const bracketFeedback = {
            success: mainOrderResult?.success || false,
            orders: mainOrderResult?.orders || [],
            symbol: mainOrderResult?.symbol || null,
            summary: mainOrderResult?.summary || null,
            rejectionReason: mainOrderResult?.rejectionReason || null,
            filledCount: mainOrderResult?.filledCount || 0,
            rejectedCount: mainOrderResult?.rejectedCount || 0,
            error: mainOrderResult?.error || null,
            mainOrder: mainOrderResult,
            tpOrder: null,
            slOrder: null
        };

        // Check if main order was rejected - if so, don't place TP/SL orders
        if (mainOrderResult?.rejectionReason || mainOrderResult?.error || !mainOrderResult?.success) {
            console.log(`❌ Main order rejected/failed - skipping TP/SL orders`);
            console.log(`   Rejection reason: ${mainOrderResult?.rejectionReason || mainOrderResult?.error || 'Unknown'}`);
            
            // Return immediately with main order feedback
            console.log('Bracket order creation complete (main order rejected)');
            return bracketFeedback;
        }
        
        console.log(`✅ Main order successful - proceeding with TP/SL orders`);

        if (tradeData.action === 'Buy') {
            console.log('Flipping action to Sell for TP/SL orders');
            tradeData.action = 'Sell';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                const tpResult = await submitOrder('LIMIT', tradeData.takeProfit);
                bracketFeedback.tpOrder = tpResult;
                
                // Aggregate TP results
                if (tpResult?.orders?.length) {
                    bracketFeedback.orders = [...bracketFeedback.orders, ...tpResult.orders];
                }
                if (tpResult?.filledCount) bracketFeedback.filledCount += tpResult.filledCount;
                if (tpResult?.rejectedCount) bracketFeedback.rejectedCount += tpResult.rejectedCount;
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                const slResult = await submitOrder('STOP', tradeData.stopLoss);
                bracketFeedback.slOrder = slResult;
                
                // Aggregate SL results  
                if (slResult?.orders?.length) {
                    bracketFeedback.orders = [...bracketFeedback.orders, ...slResult.orders];
                }
                if (slResult?.filledCount) bracketFeedback.filledCount += slResult.filledCount;
                if (slResult?.rejectedCount) bracketFeedback.rejectedCount += slResult.rejectedCount;
            }
        } else {
            console.log('Flipping action to Buy for TP/SL orders');
            tradeData.action = 'Buy';
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                const tpResult = await submitOrder('LIMIT', tradeData.takeProfit);
                bracketFeedback.tpOrder = tpResult;
                
                // Aggregate TP results
                if (tpResult?.orders?.length) {
                    bracketFeedback.orders = [...bracketFeedback.orders, ...tpResult.orders];
                }
                if (tpResult?.filledCount) bracketFeedback.filledCount += tpResult.filledCount;
                if (tpResult?.rejectedCount) bracketFeedback.rejectedCount += tpResult.rejectedCount;
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                const slResult = await submitOrder('STOP', tradeData.stopLoss);
                bracketFeedback.slOrder = slResult;
                
                // Aggregate SL results  
                if (slResult?.orders?.length) {
                    bracketFeedback.orders = [...bracketFeedback.orders, ...slResult.orders];
                }
                if (slResult?.filledCount) bracketFeedback.filledCount += slResult.filledCount;
                if (slResult?.rejectedCount) bracketFeedback.rejectedCount += slResult.rejectedCount;
            }
        }
        
        // Final aggregated feedback logging
        console.log('📊 Final bracket feedback aggregation:');
        console.log(`   Overall success: ${bracketFeedback.success}`);
        console.log(`   Total orders: ${bracketFeedback.orders.length}`);
        console.log(`   Filled count: ${bracketFeedback.filledCount}`);
        console.log(`   Rejected count: ${bracketFeedback.rejectedCount}`);
        if (bracketFeedback.rejectionReason) {
            console.log(`   Rejection reason: ${bracketFeedback.rejectionReason}`);
        }
        
        console.log('Bracket order creation complete');
        return bracketFeedback;
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

    // 🔄 WAIT FOR ORDER FEEDBACK WITH RETRY LOGIC
    window.waitForOrderFeedback = async function(maxWaitTime = 10000, checkInterval = 500) {
        console.log(`⏳ Waiting for order feedback (max ${maxWaitTime/1000}s)...`);
        
        const startTime = Date.now();
        let lastResult = null;
        let attempts = 0;
        
        while (Date.now() - startTime < maxWaitTime) {
            attempts++;
            console.log(`⏳ Attempt ${attempts}: Checking for order feedback...`);
            
            // Try to capture order feedback
            const result = await captureOrderFeedback();
            
            // If we found order history with events, return it
            if (result.success && result.orders.length > 0) {
                console.log(`✅ Order feedback found after ${attempts} attempts`);
                return result;
            }
            
            // If we found a rejection, return immediately
            if (result.rejectionReason) {
                console.log(`❌ Order rejected after ${attempts} attempts`);
                return result;
            }
            
            // Store last result for timeout return
            lastResult = result;
            
            // Wait before next check
            await delay(checkInterval);
        }
        
        // Timeout reached
        console.log(`⏱️ Timeout reached after ${attempts} attempts (${maxWaitTime/1000}s)`);
        return lastResult || {
            success: false,
            error: 'Timeout waiting for order feedback',
            orders: [],
            symbol: null,
            summary: null
        };
    };

    // 🔄 CAPTURE TRADOVATE ORDER FEEDBACK SYSTEM
    window.captureOrderFeedback = async function() {
        console.log('🔄 CAPTURING TRADOVATE ORDER FEEDBACK...');
        
        // Wait a moment for order feedback to load
        await delay(500);
        
        // Look for the order history container
        const orderHistoryDiv = document.querySelector('.order-history');
        if (!orderHistoryDiv) {
            console.log('❌ Order history div not found - no feedback to capture');
            return {
                success: false,
                error: 'Order history not found',
                orders: [],
                symbol: null,
                summary: null
            };
        }
        
        console.log('✅ Found order history div - capturing feedback...');
        
        // Initialize result object
        const result = {
            success: true,
            orders: [],
            symbol: null,
            summary: null,
            rejectionReason: null,
            filledCount: 0,
            rejectedCount: 0
        };
        
        // Extract the trading ticket header information
        const ticketHeader = orderHistoryDiv.querySelector('.trading-ticket-header');
        if (ticketHeader) {
            // Extract symbol info
            const symbolDiv = ticketHeader.querySelector('div[style*="font-size: 160%"]');
            result.symbol = symbolDiv ? symbolDiv.textContent.trim() : 'UNKNOWN';
            
            // Extract order summary
            const orderSummaryDiv = ticketHeader.querySelector('div:last-child');
            result.summary = orderSummaryDiv ? orderSummaryDiv.textContent.trim() : 'No summary';
            
            console.log(`📊 ORDER FEEDBACK - Symbol: ${result.symbol}`);
            console.log(`📊 ORDER FEEDBACK - Summary: ${result.summary}`);
        }
        
        // Extract detailed order events from the data table
        const orderEvents = getOrderEvents(orderHistoryDiv);
        result.orders = orderEvents;
        console.log(`📊 ORDER FEEDBACK - Events (${orderEvents.length} found)`);
        
        // Check for specific rejection reasons or success indicators
        const rejectionText = orderHistoryDiv.textContent;
        if (rejectionText.includes('Rejected')) {
            result.success = false;
            result.rejectedCount++;
            console.log('❌ ORDER REJECTED - checking rejection reason...');
            if (rejectionText.includes('outside of market hours')) {
                result.rejectionReason = 'Outside market hours';
                console.log('❌ REJECTION REASON: Order placed outside market hours');
            } else if (rejectionText.includes('Risk')) {
                result.rejectionReason = 'Risk management violation';
                console.log('❌ REJECTION REASON: Risk management violation');
            } else {
                result.rejectionReason = 'Unknown rejection';
                console.log('❌ REJECTION REASON: Other - check full feedback above');
            }
        } else if (rejectionText.includes('Risk Passed')) {
            console.log('✅ RISK MANAGEMENT: Order passed risk checks');
        }
        
        // Count filled orders
        const filledOrders = orderEvents.filter(event => 
            event.event.includes('Fill') || event.event.includes('@')
        );
        result.filledCount = filledOrders.length;
        if (result.filledCount > 0) {
            console.log(`✅ Found ${result.filledCount} filled orders`);
        }
        
        console.log('🔄 ORDER FEEDBACK CAPTURE COMPLETE');
        return result;
    };


    // Futures tick data dictionary with default SL/TP settings for each instrument
    // Use window property to avoid redeclaration errors on script reinjection
    if (!window.futuresTickData) {
        window.futuresTickData = {
      // Symbol: { tickSize, tickValue, defaultSL (ticks), defaultTP (ticks), precision (decimal places) }
      MNQ: { tickSize: 0.25, tickValue: 0.5,  defaultSL: 15,  defaultTP: 53, precision: 2 },  // Micro E-mini Nasdaq-100
      NQ:  { tickSize: 0.25, tickValue: 5.0,  defaultSL: 15,  defaultTP: 53, precision: 2 },  // E-mini Nasdaq-100
      ES:  { tickSize: 0.25, tickValue: 12.5, defaultSL: 40,  defaultTP: 100, precision: 2 },  // E-mini S&P 500
      RTY: { tickSize: 0.1,  tickValue: 5.0,  defaultSL: 90,  defaultTP: 225, precision: 1 },  // E-mini Russell 2000
      YM:  { tickSize: 1.0,  tickValue: 5.0,  defaultSL: 10,  defaultTP: 25,  precision: 0 },  // E-mini Dow Jones
      CL:  { tickSize: 0.01, tickValue: 10.0, defaultSL: 50,  defaultTP: 100, precision: 2 },  // Crude Oil
      GC:  { tickSize: 0.1,  tickValue: 10.0, defaultSL: 15,  defaultTP: 30,  precision: 1 },  // Gold (15 ticks = $150 risk)
      MGC: { tickSize: 0.1,  tickValue: 1.0,  defaultSL: 15,  defaultTP: 30,  precision: 1 }   // Micro Gold
        };
    }

// Make function declaration safe for reinjection
window.autoTrade = async function(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, _tickSize = 0.25, explicitOrderType = null, isScaleOrder = false, explicitEntryPrice = null) {
        console.log(`\n[TRADE] 🔵🔵🔵 AUTOTRADE FUNCTION (NOT SCALE) 🔵🔵🔵`);
        console.log(`\n[TRADE] 🚀 ========== AUTOTRADE FUNCTION ENTRY ==========`);
        console.log(`[TRADE] 📍 AUTOTRADE STEP 1: Function called with parameters:`);
        console.log(`  inputSymbol: "${inputSymbol}"`);
        console.log(`  quantity: ${quantity} (type: ${typeof quantity})`);
        console.log(`  action: "${action}"`);
        console.log(`  takeProfitTicks: ${takeProfitTicks}`);
        console.log(`  stopLossTicks: ${stopLossTicks}`);
        console.log(`  _tickSize: ${_tickSize}`);
        console.log(`  explicitOrderType: ${explicitOrderType}`);
        console.log(`  explicitEntryPrice: ${explicitEntryPrice}`);

        console.log(`📍 AUTOTRADE STEP 2: Getting symbol from UI...`);
        
        // Declare symbolInput outside the try-catch block
        let symbolInput = inputSymbol || 'NQ'; // Default fallback
        
        try {
            console.log(`🔴🔴🔴 IMMEDIATE DEBUG: Reached line after STEP 2 🔴🔴🔴`);
            
            console.log(`🔍 DEBUG: Checking if symbolInput element exists...`);
            const symbolInputElement = document.getElementById('symbolInput');
            console.log(`🔍 DEBUG: symbolInputElement = ${symbolInputElement}`);
            
            if (symbolInputElement && symbolInputElement.value) {
                symbolInput = symbolInputElement.value;
                console.log(`  ✅ UI Symbol Input element: FOUND`);
                console.log(`  UI Symbol value: "${symbolInputElement.value}"`);
                console.log(`  Final symbol to use: "${symbolInput}" (from UI input field)`);
            } else {
                console.log(`  ❌ UI Symbol Input element: NOT FOUND or empty`);
                console.log(`  Final symbol to use: "${symbolInput}" (from function parameter)`);
            }
        } catch (error) {
            console.error(`🚨 ERROR in STEP 2: ${error.message}`);
            console.error(`🚨 ERROR stack: ${error.stack}`);
            // symbolInput already has fallback value
            console.log(`🚨 Using fallback symbol: "${symbolInput}"`);
        }

        console.log(`🔥🔥🔥 CRITICAL DEBUG: Reached end of STEP 2 try-catch block`);
        console.log(`🔥🔥🔥 symbolInput = "${symbolInput}"`);
        console.log(`🔥🔥🔥 About to proceed to STEP 3...`);

        console.log(`📍 AUTOTRADE STEP 3: Processing symbol data...`);
        // Get root symbol (e.g., 'NQH5' -> 'NQ')
        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '');
        console.log(`  Input symbol: "${symbolInput}"`);
        console.log(`  Root symbol extracted: "${rootSymbol}"`);

        // Get tick size and default values from dictionary or fallback
        console.log(`📍 AUTOTRADE STEP 4: Looking up symbol configuration...`);
        const symbolData = window.futuresTickData[rootSymbol];
        if (symbolData) {
            console.log(`  ✅ Found symbol data for ${rootSymbol}:`, symbolData);
        } else {
            console.log(`  ⚠️ No symbol data found for ${rootSymbol}, will use fallbacks`);
        }

        // Keep track of the last symbol to handle symbol changes
        const tickInputElement = document.getElementById('tickInput');
        if (rootSymbol !== autoTrade.lastRootSymbol && tickInputElement) {
           tickInputElement.value = symbolData?.tickSize ?? '';
        }
        autoTrade.lastRootSymbol = rootSymbol;
        const tickSize = (symbolData && typeof symbolData.tickSize === 'number')
               ? symbolData.tickSize
               : parseFloat(tickInputElement?.value) || _tickSize;

        // right after tickSize is determined - only if UI element exists
        if (tickInputElement) {
            tickInputElement.value = tickSize;           // shows the real value
            localStorage.setItem('bracketTrade_tick', tickSize);
        }

        // Use provided values or defaults from dictionary or UI
        const slInputElement = document.getElementById('slInput');
        const actualStopLossTicks = stopLossTicks ||
                                   symbolData?.defaultSL ||
                                   parseInt(slInputElement?.value) ||
                                   40;

        const tpInputElement = document.getElementById('tpInput');
        const actualTakeProfitTicks = takeProfitTicks ||
                                     symbolData?.defaultTP ||
                                     parseInt(tpInputElement?.value) ||
                                     100;

        const from = symbolData?.tickSize ? 'dictionary'
          : tickInputElement?.value ? 'input field'
          : 'default parameter';
        console.log(`Using tick size ${tickSize} (from ${from})`);
        console.log(`  Final TP/SL values: SL=${actualStopLossTicks} ticks, TP=${actualTakeProfitTicks} ticks`);

        console.log(`📍 AUTOTRADE STEP 6: Getting market data...`);
        console.log(`  Calling getMarketData("${symbolInput}")`);
        const marketData = getMarketData(symbolInput);
        if (!marketData) {
            console.error(`❌ AUTOTRADE FAILED: No market data available for ${symbolInput}`);
            console.error(`  This usually means the symbol is not found in the trading interface`);
            console.error(`  Check that the symbol exists in the quoteboard/market data table`);
            return;
        }
        console.log(`  ✅ Market data retrieved successfully:`, marketData);
        console.log(`    Symbol: ${marketData.symbol}`);
        console.log(`    Bid: ${marketData.bidPrice}`);
        console.log(`    Offer: ${marketData.offerPrice}`);

        console.log(`📍 AUTOTRADE STEP 7: Checking scale-in mode...`);
        // Check if scale-in is enabled (skip this check if we're already processing a scale order)
        const scaleCheckbox = document.getElementById('scaleInCheckbox');
        const scaleInEnabled = !isScaleOrder && scaleCheckbox?.checked;
        console.log(`  Scale-in checkbox element: ${scaleCheckbox ? 'FOUND' : 'NOT FOUND'}`);
        console.log(`  Scale-in checkbox checked: ${scaleCheckbox?.checked}`);
        console.log(`  Is scale order: ${isScaleOrder}`);
        console.log(`  Final scale-in enabled: ${scaleInEnabled}`);
        
        if (scaleInEnabled) {
            console.log(`🔀 SCALE-IN MODE DETECTED - Delegating to auto_trade_scale function`);
            
            // Get scale parameters
            console.log(`📍 SCALE-IN STEP 1: Getting scale parameters...`);
            const scaleLevels = parseInt(document.getElementById('scaleLevelsInput')?.value || '4');
            const scaleSpacing = parseInt(document.getElementById('scaleSpacingInput')?.value || '20');
            
            console.log(`  Scale levels: ${scaleLevels}`);
            console.log(`  Scale spacing: ${scaleSpacing} ticks`);
            console.log(`  Total quantity to split: ${quantity} contracts`);
            
            // Get entry price for scale calculation
            const entryPriceInput = document.getElementById('entryPriceInput');
            const customEntryPrice = entryPriceInput && entryPriceInput.value ? parseFloat(entryPriceInput.value) : null;
            const entryPrice = customEntryPrice || parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
            
            // Calculate scale orders using backend logic
            const scaleOrdersData = {
                symbol: inputSymbol,
                quantity: quantity,
                action: action,
                entry_price: customEntryPrice, // null for market orders
                scale_levels: scaleLevels,
                scale_ticks: scaleSpacing,
                tick_size: tickSize
            };
            
            console.log('Calculating scale orders with data:', scaleOrdersData);
            
            // Calculate scale orders (mimic backend calculation)
            const scaleOrders = [];
            const qtyPerLevel = Math.floor(quantity / scaleLevels);
            const remainingQty = quantity % scaleLevels;
            
            for (let i = 0; i < scaleLevels; i++) {
                const levelQty = qtyPerLevel + (i < remainingQty ? 1 : 0);
                let levelPrice = null;
                
                if (customEntryPrice !== null) {
                    // For limit/stop orders, calculate scaled entry prices
                    const priceOffset = i * scaleSpacing * tickSize;
                    // For both Buy and Sell: scale down from entry price
                    // This creates orders at: entry, entry-20, entry-40, entry-60, etc.
                    levelPrice = entryPrice - priceOffset;
                }
                
                scaleOrders.push({
                    quantity: levelQty,
                    entry_price: levelPrice
                });
            }
            
            console.log(`📍 SCALE-IN STEP 3: Generated ${scaleOrders.length} scale orders:`, scaleOrders);
            
            // Call auto_trade_scale with calculated orders
            console.log(`📍 SCALE-IN STEP 4: Calling auto_trade_scale function...`);
            console.log(`  Parameters: auto_trade_scale("${inputSymbol}", scaleOrders, "${action}", ${actualTakeProfitTicks}, ${actualStopLossTicks}, ${tickSize})`);
            auto_trade_scale(inputSymbol, scaleOrders, action, actualTakeProfitTicks, actualStopLossTicks, tickSize);
            console.log(`🔀 AUTOTRADE DELEGATED TO SCALE-IN - Exiting autoTrade function`);
            return; // Exit early, scale handling is complete
        }

        // Continue with single order logic if scale-in is disabled
        console.log(`📍 AUTOTRADE STEP 8: Scale-in disabled, proceeding with single order logic...`);

        // Check if an entry price was provided - prioritize explicit parameter over UI field
        let customEntryPrice = null;
        if (explicitEntryPrice !== null) {
            console.log(`🔥 USING EXPLICIT ENTRY PRICE: ${explicitEntryPrice}`);
            customEntryPrice = parseFloat(explicitEntryPrice);
        } else {
            const entryPriceInput = document.getElementById('entryPriceInput');
            customEntryPrice = entryPriceInput && entryPriceInput.value ? parseFloat(entryPriceInput.value) : null;
            console.log(`🔥 USING UI ENTRY PRICE: ${customEntryPrice}`);
        }
        
        // Determine market price (used when no entry price is specified or for SL/TP calculations)
        const marketPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
        console.log(`Market price: ${marketPrice} (${action === 'Buy' ? 'offer' : 'bid'} price)`);
        
        // Determine entry order type and price
        console.log(`🔥 REACHED ORDER TYPE DETERMINATION SECTION`);
        console.log(`🔥 Initial values: customEntryPrice=${customEntryPrice}, marketPrice=${marketPrice}, explicitOrderType=${explicitOrderType}`);
        let orderType = 'MARKET';
        let entryPrice = marketPrice;
        
        // Use explicit order type if provided, otherwise fall back to entry price logic
        console.log(`🔥 Checking explicitOrderType: ${explicitOrderType}`);
        if (explicitOrderType) {
            console.log(`🔥 EXPLICIT ORDER TYPE BRANCH`);
        
            // Validate order type
            const validOrderTypes = ['MARKET', 'LIMIT', 'STOP', 'STOP LIMIT', 'TRL STOP', 'TRL STP LMT'];
            if (!validOrderTypes.includes(explicitOrderType)) {
                console.error(`Invalid order type: ${explicitOrderType}. Valid types: ${validOrderTypes.join(', ')}`);
                return;
            }
            
            orderType = explicitOrderType;
            console.log(`Using explicit order type: ${orderType}`);
            
            // For non-market orders, use custom entry price if available, otherwise use market price
            if (orderType !== 'MARKET' && customEntryPrice !== null) {
                entryPrice = customEntryPrice;
                console.log(`Using custom entry price: ${entryPrice} for ${orderType} order`);
            } else if (orderType !== 'MARKET') {
                // For non-market orders without custom price, use market price
                entryPrice = marketPrice;
                console.log(`Using market price: ${entryPrice} for ${orderType} order`);
            }
        } else if (customEntryPrice !== null) {
            console.log(`🔥 AUTO-DETECTION BRANCH REACHED!`);
            console.log(`Custom entry price provided: ${customEntryPrice}`);
            console.log(`Market price: ${marketPrice}`);
            console.log(`Action: ${action}`);
            entryPrice = customEntryPrice;
            
            // Determine if this should be a LIMIT or STOP order based on price comparison
            console.log(`🔥 STARTING AUTO-DETECTION LOGIC...`);
            if (action === 'Buy') {
                // For Buy: LIMIT if entry below market, STOP if entry above market
                console.log(`🔥 Buy order: comparing ${customEntryPrice} < ${marketPrice}`);
                orderType = customEntryPrice < marketPrice ? 'LIMIT' : 'STOP';
                console.log(`🔥 Buy result: ${customEntryPrice < marketPrice ? 'BELOW market → LIMIT' : 'ABOVE market → STOP'}`);
            } else {
                // For Sell: LIMIT if entry above market, STOP if entry below market
                console.log(`🔥 Sell order: comparing ${customEntryPrice} > ${marketPrice}`);
                orderType = customEntryPrice > marketPrice ? 'LIMIT' : 'STOP';
                console.log(`🔥 Sell result: ${customEntryPrice > marketPrice ? 'ABOVE market → LIMIT' : 'BELOW market → STOP'}`);
            }
            console.log(`🔥 Order type determined to be: ${orderType}`);
            console.log(`🔥 AUTO-DETECTION LOGIC COMPLETED!`);
        } else {
            console.log(`🔥 NO CUSTOM ENTRY PRICE - Market order branch`);
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
        console.log(`📍 AUTOTRADE STEP 9: Trade data prepared for submission:`, tradeData);

        console.log(`📍 AUTOTRADE STEP 10: Calling createBracketOrdersManual...`);
        console.log(`  This will handle the actual DOM manipulation and order submission`);
        
        try {
            // Execute the trade and capture feedback
            console.log(`📍 AUTOTRADE STEP 10: Executing bracket orders...`);
            const bracketResult = await createBracketOrdersManual(tradeData);
            console.log(`📊 Bracket execution result:`, bracketResult);
            
            // Check if we already have valid feedback from bracket execution
            const hasFeedback = bracketResult && (
                bracketResult.rejectionReason || 
                (bracketResult.success && bracketResult.orders?.length > 0) ||
                bracketResult.error
            );
            
            let orderResult;
            if (hasFeedback) {
                console.log(`📍 AUTOTRADE STEP 11: Using feedback from bracket execution (no waitForOrderFeedback needed)`);
                orderResult = bracketResult;
            } else {
                console.log(`📍 AUTOTRADE STEP 11: No feedback from bracket execution - falling back to waitForOrderFeedback...`);
                orderResult = await waitForOrderFeedback();
            }
            
            // Log the result
            console.log(`📍 AUTOTRADE STEP 12: Order verification complete`);
            console.log(`  Success: ${orderResult.success}`);
            console.log(`  Orders placed: ${orderResult.orders.length}`);
            if (orderResult.error) {
                console.log(`  Error: ${orderResult.error}`);
            }
            
            return orderResult;
            
        } catch (error) {
            console.error(`❌ AUTOTRADE ERROR: ${error.message}`);
            return {
                success: false,
                error: error.message,
                orders: []
            };
        } finally {
            const d = window.futuresTickData[rootSymbol];      // or rootSymbol
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
    }; // End of window.autoTrade function

    // Scale order function to handle multiple entry levels
    // Make function declaration safe for reinjection
    window.auto_trade_scale = async function(symbol, scaleOrders, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, tickSize = 0.25) {
        console.log(`\n🚨🚨🚨🚨🚨🚨🚨 AUTO_TRADE_SCALE FUNCTION CALLED! 🚨🚨🚨🚨🚨🚨🚨`);
        console.log(`🚨🚨🚨 THIS IS THE SCALE FUNCTION - NOT autoTrade 🚨🚨🚨`);
        console.log(`\n=== AUTO_TRADE_SCALE DEBUG ===`);
        console.log(`Called with parameters:`);
        console.log(`  symbol: ${symbol}`);
        console.log(`  scaleOrders:`, scaleOrders);
        console.log(`  action: ${action}`);
        console.log(`  takeProfitTicks: ${takeProfitTicks}`);
        console.log(`  stopLossTicks: ${stopLossTicks}`);
        console.log(`  tickSize: ${tickSize}`);
        
        // Validate inputs
        if (!scaleOrders || !Array.isArray(scaleOrders) || scaleOrders.length === 0) {
            console.error('ERROR: Invalid scale orders - empty or not an array');
            console.error('scaleOrders value:', scaleOrders);
            return {
                success: false,
                error: 'Invalid scale orders configuration',
                orders: []
            };
        }
        
        console.log(`Scale orders array length: ${scaleOrders.length}`);
        
        // Validate each order
        console.log(`Validating ${scaleOrders.length} scale orders:`);
        for (let i = 0; i < scaleOrders.length; i++) {
            const order = scaleOrders[i];
            console.log(`  Order ${i+1}:`, order);
            
            if (!order || typeof order.quantity !== 'number' || order.quantity <= 0) {
                console.error(`ERROR: Invalid scale order at index ${i}: invalid quantity`);
                console.error(`Order details:`, order);
                return {
                    success: false,
                    error: `Invalid quantity in scale order ${i + 1}`,
                    orders: []
                };
            }
            
            console.log(`    ✓ Valid: ${order.quantity} contracts @ ${order.entry_price || 'Market'}`);
        }
        
        console.log(`All orders validated successfully`);
        
        // Execute each scale order with a delay between them
        const delayBetweenOrders = 500; // 500ms between orders
        const orderResults = [];
        
        // Show initial progress message in console instead of popup
        console.log(`[SCALE] 📊 Placing ${scaleOrders.length} scaled orders...`);
        
        async function placeNextOrder(orderIndex) {
            console.log(`\n--- placeNextOrder() called ---`);
            console.log(`Current orderIndex: ${orderIndex}, Total orders: ${scaleOrders.length}`);
            
            if (orderIndex >= scaleOrders.length) {
                const successfulOrders = orderResults.filter(r => r.success).length;
                const failedOrders = orderResults.filter(r => !r.success).length;
                
                console.log(`=== SCALE ORDER EXECUTION COMPLETED ===`);
                console.log(`Successful: ${successfulOrders}, Failed: ${failedOrders}`);
                console.log(`=== END AUTO_TRADE_SCALE DEBUG ===`);
                
                // Show completion message in console instead of popup
                if (failedOrders === 0) {
                    console.log(`[SCALE] ✅ ${successfulOrders} scale orders placed successfully`);
                } else if (successfulOrders > 0) {
                    console.log(`[SCALE] ⚠️ Scale orders completed: ${successfulOrders} successful, ${failedOrders} failed.`);
                } else {
                    console.log(`[SCALE] ❌ All ${failedOrders} scale orders failed.`);
                }
                
                return {
                    success: failedOrders === 0,
                    orders: orderResults,
                    summary: {
                        total: scaleOrders.length,
                        successful: successfulOrders,
                        failed: failedOrders
                    }
                };
            }
            
            const order = scaleOrders[orderIndex];
            
            // Show progress indicator 
            console.log(`\n🔄 Placing order ${orderIndex + 1} of ${scaleOrders.length}...`);
            console.log(`  Order details:`, order);
            console.log(`  Quantity: ${order.quantity}`);
            console.log(`  Entry Price: ${order.entry_price}`);
            
            try {
                console.log(`Calling autoTrade with:`);
                console.log(`  symbol: ${symbol}`);
                console.log(`  quantity: ${order.quantity}`);
                console.log(`  action: ${action}`);
                console.log(`  takeProfitTicks: ${takeProfitTicks}`);
                console.log(`  stopLossTicks: ${stopLossTicks}`);
                console.log(`  tickSize: ${tickSize}`);
                console.log(`  explicitEntryPrice: ${order.entry_price} (passed directly)`);
                
                // Call autoTrade for this scale level
                // IMPORTANT: Pass 0 for TP/SL to prevent bracket orders that interfere with scale levels
                // We'll add TP/SL only to the final consolidated position if needed
                // Pass isScaleOrder=true to prevent recursive scale-in checks
                // Pass order.entry_price directly as explicitEntryPrice to bypass UI timing issues
                const orderResult = await autoTrade(symbol, order.quantity, action, 0, 0, tickSize, null, true, order.entry_price);
                
                // Add scale order metadata to result
                orderResult.scaleLevel = orderIndex + 1;
                orderResult.requestedPrice = order.entry_price;
                orderResult.requestedQuantity = order.quantity;
                
                orderResults.push(orderResult);
                
                if (orderResult.success) {
                    console.log(`✅ Order ${orderIndex + 1}/${scaleOrders.length} verified successfully (${order.quantity} contracts @ ${order.entry_price || 'Market'})`);
                } else {
                    console.log(`❌ Order ${orderIndex + 1}/${scaleOrders.length} failed: ${orderResult.error}`);
                }
                
            } catch (error) {
                console.error(`❌ ERROR placing scale order ${orderIndex + 1}/${scaleOrders.length}:`, error);
                orderResults.push({
                    success: false,
                    error: error.message,
                    scaleLevel: orderIndex + 1,
                    requestedPrice: order.entry_price,
                    requestedQuantity: order.quantity,
                    orders: []
                });
            }
            
            // Wait before placing next order
            if (orderIndex + 1 < scaleOrders.length) {
                await new Promise(resolve => setTimeout(resolve, delayBetweenOrders));
                return placeNextOrder(orderIndex + 1);
            } else {
                // This was the last order, return the results
                const successfulOrders = orderResults.filter(r => r.success).length;
                const failedOrders = orderResults.filter(r => !r.success).length;
                
                return {
                    success: failedOrders === 0,
                    orders: orderResults,
                    summary: {
                        total: scaleOrders.length,
                        successful: successfulOrders,
                        failed: failedOrders
                    }
                };
            }
        }
        
        // Start placing orders and return the promise
        return placeNextOrder(0);
    }; // End of window.auto_trade_scale function

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
    // Use var to allow redeclaration on script reinjection
    if (!window.MONTH_CODES) {
        window.MONTH_CODES = ['F','G','H','J','K','M','N','Q','U','V','X','Z'];
    }

    /**
 * Returns { letter, yearDigit } for the given date.
 * Example: 2025-04-23  →  { letter:'J', yearDigit:'5' }
 */
    function getMonthlyCode(date = new Date()) {
        console.log(`getMonthlyCode called with date: ${date.toISOString()}`);
        const letter = window.MONTH_CODES[date.getUTCMonth()];      // 0-11 → F … Z
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