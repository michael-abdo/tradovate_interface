// ==UserScript==
// @name         Auto Order SL
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Tampermonkey UI for bracket trades with SL price input and dollar-based calculations
// @author       You
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/AutoOrderSL.user.js
// @downloadURL  http://localhost:8080/AutoOrderSL.user.js
// ==/UserScript==

(function () {
    'use strict';
    console.log('Auto Order SL script initialized');
    var debug = false;

    function delay(ms) {
        console.log(`Delaying for ${ms}ms`);
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function createUI() {
        console.log('Creating UI');
        const storedDollarRisk = localStorage.getItem('bracketTradeSL_dollarRisk') || '200';
        const storedRiskReward = localStorage.getItem('bracketTradeSL_riskReward') || '3';
        const storedQty = localStorage.getItem('bracketTradeSL_qty') || '9';
        const storedTick = localStorage.getItem('bracketTradeSL_tick') || '0.25';
        const storedSym = localStorage.getItem('bracketTradeSL_symbol') || 'NQ';
        console.log(`Stored values: Dollar Risk=${storedDollarRisk}, Risk/Reward=${storedRiskReward}, Qty=${storedQty}, Tick=${storedTick}, Symbol=${storedSym}`);

        const container = document.createElement('div');
        container.id = 'sl-bracket-trade-box';
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
            width: '220px'
        });

        // restore box position
        const savedLeft = localStorage.getItem('bracketTradeBoxSLLeft');
        const savedTop = localStorage.getItem('bracketTradeBoxSLTop');
        if (savedLeft && savedTop) { container.style.left = savedLeft; container.style.top = savedTop; }
        else { container.style.top = '20px'; container.style.right = '20px'; }

        container.innerHTML = `
        <!-- Header with Symbol -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-weight:bold;cursor:grab;">⠿ SL Bracket</span>
            <input type="text" id="symbolInputSL" value="${storedSym}"
                style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" 
                placeholder="Symbol" />
        </div>
        
        <!-- Hidden Tick Size Input -->
        <div id="tickContainerSL" style="margin-bottom:8px;">
            <label style="display:block;margin-bottom:4px;font-size:11px;">Tick Size</label>
            <input type="number" id="tickInputSL" step="0.01" value="${storedTick}"
                style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
        </div>

        <!-- Dollar Risk and Risk/Reward Settings -->
        <div style="display:flex;gap:8px;margin-bottom:8px;">
            <div style="flex:1;">
                <label style="display:block;margin-bottom:4px;font-size:11px;">$ Risk</label>
                <input type="number" id="dollarRiskInput" value="${storedDollarRisk}" 
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
            </div>
            <div style="flex:1;">
                <label style="display:block;margin-bottom:4px;font-size:11px;">R:R</label>
                <input type="number" id="riskRewardInput" value="${storedRiskReward}" step="0.1"
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
            </div>
        </div>

        <!-- Main Controls -->
        <div id="mainControlsSL">
            <!-- SL Price Input -->
            <div style="margin-bottom:8px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;color:#e74c3c;">Stop Loss Price</label>
                <input type="number" id="slPriceInputSL" step="0.01"
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #e74c3c;background:#2a2a2a;color:#fff;border-width:2px;" 
                    placeholder="SL Price" />
            </div>
            
            <!-- Entry Price (calculated or manual) -->
            <div style="margin-bottom:8px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;color:#f39c12;">Entry Price</label>
                <input type="number" id="entryPriceInputSL" placeholder="Entry" step="0.01"
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #f39c12;background:#2a2a2a;color:#fff;" />
            </div>

            <!-- TP Price (calculated or manual) -->
            <div style="margin-bottom:8px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;color:#2ecc71;">Take Profit Price</label>
                <input type="number" id="tpPriceInputSL" step="0.01"
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #2ecc71;background:#2a2a2a;color:#fff;"
                    placeholder="TP Price" />
            </div>
            
            <!-- Quantity Input -->
            <div style="margin-bottom:12px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;">Quantity</label>
                <input type="number" id="qtyInputSL" value="${storedQty}" min="1"
                    style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
            </div>
            
            <!-- Trade Buttons -->
            <div style="display:flex;gap:10px;margin-bottom:12px;">
                <button id="buyBtnSL" style="flex:1;padding:10px 12px;background:#2ecc71;color:#fff;border:none;border-radius:4px;font-weight:bold;">Buy</button>
                <button id="sellBtnSL" style="flex:1;padding:10px 12px;background:#e74c3c;color:#fff;border:none;border-radius:4px;font-weight:bold;">Sell</button>
            </div>
            
            <!-- Action Buttons -->
            <div style="display:flex;gap:10px;margin-bottom:2px;">
                <button id="cancelAllBtnSL" style="flex:1;padding:8px;background:#e6b800;color:#000;border:none;border-radius:4px;font-weight:bold;">Cancel</button>
                <button id="closeAllBtnSL" style="flex:3;padding:8px;background:#e74c3c;color:#fff;border:none;border-radius:4px;font-weight:bold;">Close All</button>
            </div>
            <div style="display:flex;gap:10px;margin-top:6px;">
                <button id="reverseBtnSL" style="flex:1;padding:8px;background:#ff6600;color:#fff;border:none;border-radius:4px;font-weight:bold;">Reverse</button>
            </div>
        </div>`;

        document.body.appendChild(container);
        console.log('UI container added to DOM');

        // --- UI events ---
        console.log('Setting up UI event handlers');
        const slPriceInputSL = document.getElementById('slPriceInputSL');
        const entryPriceInputSL = document.getElementById('entryPriceInputSL');
        const tpPriceInputSL = document.getElementById('tpPriceInputSL');
        const dollarRiskInput = document.getElementById('dollarRiskInput');
        const riskRewardInput = document.getElementById('riskRewardInput');
        const qtyInputSL = document.getElementById('qtyInputSL');
        const tickInputSL = document.getElementById('tickInputSL');
        const symbolInputSL = document.getElementById('symbolInputSL');

        // Function to calculate entry and TP based on SL price
        function calculatePrices() {
            console.log('Calculating prices based on SL input');
            
            const slPrice = parseFloat(slPriceInputSL.value);
            if (isNaN(slPrice)) {
                console.log('SL price is not a valid number');
                entryPriceInputSL.value = '';
                tpPriceInputSL.value = '';
                return;
            }
            
            const symbol = symbolInputSL.value || 'NQ';
            const rootSymbol = symbol.replace(/[A-Z]\d+$/, '');
            const symbolData = futuresTickData[rootSymbol];
            
            // Get tick size and tick value
            const tickSize = parseFloat(tickInputSL.value) || (symbolData?.tickSize || 0.25);
            const tickValue = symbolData?.tickValue || 5.0; // Default to NQ tick value
            
            // Get dollar risk and risk/reward ratio
            const dollarRisk = parseFloat(dollarRiskInput.value) || 200;
            const riskReward = parseFloat(riskRewardInput.value) || 3;
            const quantity = parseInt(qtyInputSL.value) || 1;
            
            // Calculate how many ticks of risk based on dollar risk
            const ticksOfRisk = Math.round(dollarRisk / (tickValue * quantity));
            console.log(`Calculated ${ticksOfRisk} ticks of risk for $${dollarRisk} with ${quantity} contracts`);
            
            // Calculate entry price - assume we're buying (will be flipped for selling)
            const buyEntryPrice = slPrice + (ticksOfRisk * tickSize);
            
            // Calculate take profit price based on risk/reward ratio
            const buyTpPrice = buyEntryPrice + (ticksOfRisk * tickSize * riskReward);
            
            // Format to proper decimal places
            const precision = symbolData?.precision || 2;
            entryPriceInputSL.value = buyEntryPrice.toFixed(precision);
            tpPriceInputSL.value = buyTpPrice.toFixed(precision);
            
            console.log(`Buy scenario - Entry: ${buyEntryPrice.toFixed(precision)}, TP: ${buyTpPrice.toFixed(precision)}, SL: ${slPrice}`);
        }

        // Flag to track if price inputs are being updated manually
        let manualEntryFlag = false;
        let manualTPFlag = false;

        // Setup event listeners for price calculation
        slPriceInputSL.addEventListener('input', function() {
            // Reset manual flags when SL is updated, forcing recalculation
            manualEntryFlag = false;
            manualTPFlag = false;
            calculatePrices();
        });

        dollarRiskInput.addEventListener('input', function() {
            localStorage.setItem('bracketTradeSL_dollarRisk', this.value);
            // Only auto-calculate if manual flags are not set
            if (!manualEntryFlag && !manualTPFlag) {
                calculatePrices();
            }
        });

        riskRewardInput.addEventListener('input', function() {
            localStorage.setItem('bracketTradeSL_riskReward', this.value);
            // Only auto-calculate if manual flags are not set
            if (!manualEntryFlag && !manualTPFlag) {
                calculatePrices();
            }
        });

        qtyInputSL.addEventListener('input', function() {
            localStorage.setItem('bracketTradeSL_qty', this.value);
            // Only auto-calculate if manual flags are not set
            if (!manualEntryFlag && !manualTPFlag) {
                calculatePrices();
            }
        });

        tickInputSL.addEventListener('input', function() {
            localStorage.setItem('bracketTradeSL_tick', this.value);
            // Only auto-calculate if manual flags are not set
            if (!manualEntryFlag && !manualTPFlag) {
                calculatePrices();
            }
        });

        // Handle manual entry in price fields
        entryPriceInputSL.addEventListener('focus', function() {
            manualEntryFlag = true;
        });

        entryPriceInputSL.addEventListener('blur', function() {
            manualEntryFlag = entryPriceInputSL.value !== '';
        });

        tpPriceInputSL.addEventListener('focus', function() {
            manualTPFlag = true;
        });

        tpPriceInputSL.addEventListener('blur', function() {
            manualTPFlag = tpPriceInputSL.value !== '';
        });

        // Function to force recalculation (available programmatically but no button)
        function forceRecalculate() {
            console.log('Force recalculation triggered');
            manualEntryFlag = false;
            manualTPFlag = false;
            calculatePrices();
        }

        // Close and Cancel buttons
        document.getElementById('closeAllBtnSL').addEventListener('click', () => {
            console.log('Close All button clicked');
            try {
                const symbol = symbolInputSL.value || 'NQ';
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
        
        document.getElementById('cancelAllBtnSL').addEventListener('click', () => {
            console.log('Cancel All button clicked');
            try {
                const symbol = symbolInputSL.value || 'NQ';
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
        document.getElementById('reverseBtnSL').addEventListener('click', () => {
            console.log('Reverse Position button clicked');
            try {
                const symbol = symbolInputSL.value || 'NQ';
                const normalizedSymbol = normalizeSymbol(symbol);
                console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Reverse & Cxl option`);
                
                // Call the clickExitForSymbol function with the normalized symbol and Reverse option
                clickExitForSymbol(normalizedSymbol, 'cancel-option-Reverse-Cxl');
                console.log('Reverse Position action triggered for symbol:', normalizedSymbol);
            } catch (err) {
                console.error("Reverse Position operation failed:", err);
            }
        });

        // Persist settings inputs
        console.log('Setting up persistent settings');
        symbolInputSL.addEventListener('input', e => {
            console.log(`Symbol input changed to: ${e.target.value}`);
            localStorage.setItem('bracketTradeSL_symbol', e.target.value);
        });

        // Symbol change handler
        symbolInputSL.addEventListener('change', e => {
            const symbolValue = e.target.value;
            const normalizedSymbol = normalizeSymbol(symbolValue);
            console.log(`Symbol changed to: ${symbolValue}, normalized: ${normalizedSymbol}`);

            // Update tick size based on the symbol
            const rootSymbol = symbolValue.replace(/[A-Z]\d+$/, '');
            const symbolDefaults = futuresTickData[rootSymbol];

            if (symbolDefaults) {
                console.log(`Found default values for ${rootSymbol}`);

                // Update tick size if available
                if (typeof symbolDefaults.tickSize === 'number') {
                    tickInputSL.value = symbolDefaults.tickSize;
                    localStorage.setItem('bracketTradeSL_tick', symbolDefaults.tickSize);
                    console.log(`Updated tick size to ${symbolDefaults.tickSize} for ${rootSymbol}`);
                }

                // Recalculate prices with new symbol data
                calculatePrices();
            }

            // Update the symbol in Tradovate's interface
            updateSymbol('.search-box--input', normalizedSymbol);
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
                localStorage.setItem('bracketTradeBoxSLLeft', container.style.left);
                localStorage.setItem('bracketTradeBoxSLTop', container.style.top);
            }
            isDragging = false;
            container.style.cursor = 'grab';
        });

        // Buy and Sell buttons
        document.getElementById('buyBtnSL').addEventListener('click', () => {
            console.log('BUY button clicked');
            const symbol = symbolInputSL.value || 'NQ';
            const qty = parseInt(qtyInputSL.value) || 1;
            const entryPrice = parseFloat(entryPriceInputSL.value);
            const tpPrice = parseFloat(tpPriceInputSL.value);
            const slPrice = parseFloat(slPriceInputSL.value);
            const tickSize = parseFloat(tickInputSL.value) || 0.25;
            
            if (isNaN(entryPrice) || isNaN(tpPrice) || isNaN(slPrice)) {
                console.error('Invalid price values');
                alert('Please enter valid price values');
                return;
            }
            
            console.log(`Initiating BUY order: Symbol=${symbol}, Qty=${qty}, Entry=${entryPrice}, TP=${tpPrice}, SL=${slPrice}`);
            autoTradeSL(symbol, qty, 'Buy', entryPrice, tpPrice, slPrice, tickSize);
        });
        
        document.getElementById('sellBtnSL').addEventListener('click', () => {
            console.log('SELL button clicked');
            const symbol = symbolInputSL.value || 'NQ';
            const qty = parseInt(qtyInputSL.value) || 1;
            const slPrice = parseFloat(slPriceInputSL.value);
            const tickSize = parseFloat(tickInputSL.value) || 0.25;
            
            if (isNaN(slPrice)) {
                console.error('Invalid SL price value');
                alert('Please enter a valid SL price');
                return;
            }
            
            // For selling, we need to flip the calculations
            const dollarRisk = parseFloat(dollarRiskInput.value) || 200;
            const riskReward = parseFloat(riskRewardInput.value) || 3;
            const rootSymbol = symbol.replace(/[A-Z]\d+$/, '');
            const symbolData = futuresTickData[rootSymbol] || { tickValue: 5.0, precision: 2 };
            const tickValue = symbolData.tickValue || 5.0;
            const precision = symbolData.precision || 2;
            
            // Calculate ticks of risk
            const ticksOfRisk = Math.round(dollarRisk / (tickValue * qty));
            
            // For selling, entry is below SL
            const entryPrice = (slPrice - (ticksOfRisk * tickSize)).toFixed(precision);
            
            // TP is below entry by risk*reward
            const tpPrice = (parseFloat(entryPrice) - (ticksOfRisk * tickSize * riskReward)).toFixed(precision);
            
            console.log(`Initiating SELL order: Symbol=${symbol}, Qty=${qty}, Entry=${entryPrice}, TP=${tpPrice}, SL=${slPrice}`);
            autoTradeSL(symbol, qty, 'Sell', parseFloat(entryPrice), parseFloat(tpPrice), slPrice, tickSize);
        });
    }

    // Function to click dropdown option for a specific symbol (same as original)
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

    // Helper function for symbol normalization
    // Use unified symbol processing from UI Elements mapping
    function normalizeSymbol(s) {
        if (window.TRADOVATE_UI_ELEMENTS?.TRADING_DATA_PROCESSORS?.normalizeSymbol) {
            return window.TRADOVATE_UI_ELEMENTS.TRADING_DATA_PROCESSORS.normalizeSymbol(s);
        }
        // Fallback for backwards compatibility
        console.log(`normalizeSymbol fallback called with: "${s}"`);
        const isRootSymbol = /^[A-Z]{1,3}$/.test(s);
        const result = isRootSymbol ? getFrontQuarter(s) : s.toUpperCase();
        return result;
    }

    async function createBracketOrdersManual(tradeData) {
        console.log('Creating bracket orders with unified trading framework:', tradeData);

        // Use unified trading framework if available, fallback to original implementation
        if (window.UNIFIED_TRADING_FRAMEWORK?.createBracketOrder) {
            console.log('Using unified trading framework for bracket order creation');
            
            // Enable validation for SL orders (safety-first approach)
            const result = await window.UNIFIED_TRADING_FRAMEWORK.createBracketOrder(tradeData, {
                enableValidation: true,
                source: 'autoOrderSL'
            });
            
            if (result.success) {
                console.log(`✅ Unified bracket order created successfully: ${result.bracketId}`);
                return result;
            } else {
                console.error(`❌ Unified bracket order failed: ${result.error}`);
                console.log('Falling back to legacy implementation...');
                // Continue to fallback implementation below
            }
        } else {
            console.log('Unified trading framework not available, using legacy implementation');
        }

        // LEGACY FALLBACK: Original implementation for backwards compatibility
        async function updateInputValue(selector, value) {
            // Use unified framework if available
            if (window.UNIFIED_TRADING_FRAMEWORK?.updateInputValue) {
                return await window.UNIFIED_TRADING_FRAMEWORK.updateInputValue(selector, value);
            }
            
            // Fallback to original implementation
            let input;
            for (let i = 0; i < 25; i++) {
                input = [...document.querySelectorAll(selector)]
                    .find(el => el.offsetParent && !el.disabled);
                if (input) break;
                await delay(100);
            }
            if (!input) return console.error(`No live input for ${selector}`);

            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;

            for (let tries = 0; tries < 3; tries++) {
                input.focus();
                setVal.call(input, value);
                ['input','change'].forEach(ev =>
                                           input.dispatchEvent(new Event(ev, { bubbles: true }))
                                          );
                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                }));
                input.blur();
                await delay(300);

                if (+input.value === +value) break;
            }
            return true;
        }

        async function setCommonFields() {
            // Use unified framework if available
            if (window.UNIFIED_TRADING_FRAMEWORK?.setCommonFields) {
                return await window.UNIFIED_TRADING_FRAMEWORK.setCommonFields(tradeData);
            }
            
            // Fallback to original implementation
            console.log('Setting common order fields (legacy)');
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
            // Use unified framework if available
            if (window.UNIFIED_TRADING_FRAMEWORK?.getOrderEvents) {
                return window.UNIFIED_TRADING_FRAMEWORK.getOrderEvents(container);
            }
            
            // Fallback to original implementation
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

        function clickPriceArrow(direction = 'up') {
          const wrapper = document.querySelector('.numeric-input-value-controls');
          if (!wrapper) return;

          const target = wrapper.querySelector(
            direction === 'up' ? '.numeric-input-increment' : '.numeric-input-decrement'
          );
          target?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }

        async function submitOrder(orderType, priceValue) {
            // Use unified framework if available for comprehensive validation
            if (window.UNIFIED_TRADING_FRAMEWORK?.submitOrder) {
                console.log(`Using unified framework for ${orderType} order submission`);
                
                const result = await window.UNIFIED_TRADING_FRAMEWORK.submitOrder(orderType, priceValue, {
                    tradeData: tradeData,
                    enableValidation: true,  // Enable validation for safety
                    source: 'autoOrderSL'
                });
                
                if (result.success) {
                    console.log(`✅ Unified order submission successful: ${result.submissionId}`);
                    return result;
                } else {
                    console.error(`❌ Unified order submission failed: ${result.error}`);
                    console.log('Falling back to legacy order submission...');
                    // Continue to fallback implementation below
                }
            } else {
                console.log('Unified framework not available, using legacy order submission');
            }

            // LEGACY FALLBACK: Original implementation
            await setCommonFields();

            const typeSel = document.querySelector('.group.order-type .select-input div[tabindex]');
            typeSel?.click();
            [...document.querySelectorAll('ul.dropdown-menu li')]
                .find(li => li.textContent.trim() === orderType)
                ?.click();

            if (priceValue)
                await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);
            clickPriceArrow();

            document.querySelector('.btn-group .btn-primary')?.click();
            await delay(200);
            console.log(getOrderEvents());
            document.querySelector('.icon.icon-back')?.click();
            await delay(200);
            
            return { success: true, orderType, price: priceValue, source: 'legacy' };
        }

        console.log(`Submitting initial ${tradeData.orderType || 'MARKET'} order`);
        await submitOrder(tradeData.orderType || 'MARKET', tradeData.entryPrice);

        if (tradeData.action === 'Buy') {
            console.log('Flipping action to Sell for TP/SL orders');
            tradeData.action = 'Sell';
            console.log(`Creating take profit order at ${tradeData.takeProfit}`);
            await submitOrder('LIMIT', tradeData.takeProfit);
            console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
            await submitOrder('STOP', tradeData.stopLoss);
        } else {
            console.log('Flipping action to Buy for TP/SL orders');
            tradeData.action = 'Buy';
            console.log(`Creating take profit order at ${tradeData.takeProfit}`);
            await submitOrder('LIMIT', tradeData.takeProfit);
            console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
            await submitOrder('STOP', tradeData.stopLoss);
        }
        console.log('Bracket order creation complete');
        return Promise.resolve();
    }

    // Futures tick data dictionary with default SL/TP settings for each instrument
    // Use unified futures tick data from trading framework
    const futuresTickData = window.UNIFIED_TRADING_FRAMEWORK?.FUTURES_TICK_DATA || {
      // Fallback data if unified framework not loaded
      MNQ: { tickSize: 0.25, tickValue: 0.5,  defaultSL: 40,  defaultTP: 100, precision: 2 },
      NQ:  { tickSize: 0.25, tickValue: 5.0,  defaultSL: 40,  defaultTP: 100, precision: 2 },
      ES:  { tickSize: 0.25, tickValue: 12.5, defaultSL: 40,  defaultTP: 100, precision: 2 },
      RTY: { tickSize: 0.1,  tickValue: 5.0,  defaultSL: 90,  defaultTP: 225, precision: 1 },
      YM:  { tickSize: 1.0,  tickValue: 5.0,  defaultSL: 10,  defaultTP: 25,  precision: 0 },
      CL:  { tickSize: 0.01, tickValue: 10.0, defaultSL: 50,  defaultTP: 100, precision: 2 },
      GC:  { tickSize: 0.1,  tickValue: 10.0, defaultSL: 15,  defaultTP: 30,  precision: 1 },
      MGC: { tickSize: 0.1,  tickValue: 1.0,  defaultSL: 15,  defaultTP: 30,  precision: 1 }
    };

    // SL-based bracket order function
    function autoTradeSL(inputSymbol, quantity = 1, action = 'Buy', entryPrice, takeProfitPrice, stopLossPrice, tickSize = 0.25) {
        console.log(`autoTradeSL called with: symbol=${inputSymbol}, qty=${quantity}, action=${action}, entry=${entryPrice}, TP=${takeProfitPrice}, SL=${stopLossPrice}, tickSize=${tickSize}`);

        const symbolInput = document.getElementById('symbolInputSL').value || 'NQ';
        console.log(`Using symbol: ${symbolInput}`);

        // Get root symbol (e.g., 'NQH5' -> 'NQ')
        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '');
        console.log(`Root symbol: ${rootSymbol}`);

        // Get decimal precision for this instrument
        const symbolData = futuresTickData[rootSymbol];
        const decimalPrecision = symbolData?.precision ?? 2;
        
        console.log(`Getting market data for ${symbolInput}`);
        const marketData = getMarketData(symbolInput);
        if (!marketData) {
            console.error(`No market data for ${symbolInput}`);
            return;
        }
        console.log('Market data:', marketData);
        
        // Determine order type
        const marketPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
        console.log(`Market price: ${marketPrice} (${action === 'Buy' ? 'offer' : 'bid'} price)`);
        
        let orderType = 'MARKET';
        
        if (entryPrice !== null) {
            console.log(`Custom entry price provided: ${entryPrice}`);
            
            // Determine if this should be a LIMIT or STOP order based on price comparison
            if (action === 'Buy') {
                // For Buy: LIMIT if entry below market, STOP if entry above market
                orderType = entryPrice < marketPrice ? 'LIMIT' : 'STOP';
            } else {
                // For Sell: LIMIT if entry above market, STOP if entry below market
                orderType = entryPrice > marketPrice ? 'LIMIT' : 'STOP';
            }
            console.log(`Order type determined to be: ${orderType}`);
        } else {
            console.log(`No custom entry price provided, using market order at ${marketPrice}`);
            entryPrice = marketPrice;
        }

        const tradeData = {
            symbol: marketData.symbol,
            action,
            qty: quantity.toString(),
            takeProfit: takeProfitPrice.toFixed(decimalPrecision),
            stopLoss: stopLossPrice.toFixed(decimalPrecision),
            orderType: orderType,
            entryPrice: orderType !== 'MARKET' ? entryPrice.toFixed(decimalPrecision) : null
        };
        console.log('Trade data prepared:', tradeData);

        console.log('Submitting bracket orders');
        return createBracketOrdersManual(tradeData);
    }

    // Helper function for getting market data
    function getMarketData(inputSymbol) {
        console.log(`getMarketData called for: "${inputSymbol}"`);
        const symbol = /^[A-Z]{1,3}$/.test(inputSymbol)
            ? getFrontQuarter(inputSymbol)
            : inputSymbol.toUpperCase();
        console.log(`Using symbol: "${symbol}" for market data lookup`);

        // 1️⃣ look for an existing row
        console.log('Searching for symbol in data table rows');
        const symbolCells = document.querySelectorAll('.symbol-main');
        console.log(`Found ${symbolCells.length} symbol cells in the table`);

        let row = [...symbolCells]
            .find(el => el.textContent.trim() === symbol)
            ?.closest('.fixedDataTableRowLayout_rowWrapper');

        // 2️⃣ if missing, type the symbol into Tradovate's search so it appears
        if (row) {
            console.log('Found matching row for symbol in data table');
        } else {
            console.error(`Row for symbol "${symbol}" not found in data table`);
            alert(`Cannot Find ${inputSymbol}`);
        }

        if (!row) {
            console.log('Aborting market data retrieval - no matching row');
            return null; // still not there → abort
        }

        console.log('Extracting price data from cells');
        const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
        console.log(`Found ${cells.length} cells in the row`);

        const bidPrice = cells[4]?.textContent.trim();
        const offerPrice = cells[5]?.textContent.trim();
        console.log(`Extracted prices: bid=${bidPrice}, offer=${offerPrice}`);

        return {
            symbol,
            bidPrice,
            offerPrice
        };
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
     * Returns the next quarterly contract (Mar (H), Jun (M), Sep (U), Dec (Z)).
     * Example: 2025-04-23  →  { letter:'M', yearDigit:'5' }   // Jun 2025
     */
    function getQuarterlyCode(date = new Date()) {
        console.log(`getQuarterlyCode called with date: ${date.toISOString()}`);
        const quarters = [2, 5, 8, 11];                  // month indexes
        const quarterLetters = { 2:'H', 5:'M', 8:'U', 11:'Z' };
        console.log(`Current month index: ${date.getUTCMonth()}`);

        let y = date.getUTCFullYear();
        let m = date.getUTCMonth();
        console.log(`Starting calculation with year=${y}, month=${m}`);

        // bump forward until we land on a quarter month
        let iterations = 0;
        while (!quarters.includes(m)) {
            console.log(`Month ${m} is not a quarter month, advancing...`);
            m++;
            if (m > 11) { m = 0; y++; }
            // Prevent infinite loops
            if (++iterations > 12) break;
        }

        const result = { letter: quarterLetters[m], yearDigit: (y % 10) + '' };
        console.log(`Calculated quarterly code: letter=${result.letter}, yearDigit=${result.yearDigit}`);
        return result;
    }

    // Use unified front quarter processing from UI Elements mapping
    function getFrontQuarter(root) {
        if (window.TRADOVATE_UI_ELEMENTS?.TRADING_DATA_PROCESSORS?.getFrontQuarter) {
            return window.TRADOVATE_UI_ELEMENTS.TRADING_DATA_PROCESSORS.getFrontQuarter(root);
        }
        // Fallback for backwards compatibility
        console.log(`getFrontQuarter fallback called for root: "${root}"`);
        const { letter, yearDigit } = getQuarterlyCode();
        const result = `${root.toUpperCase()}${letter}${yearDigit}`;
        return result;
    }

    console.log('Creating example front-quarter symbol');
    const { letter, yearDigit } = getQuarterlyCode();  // e.g. M & 5
    const nqFront = `NQ${letter}${yearDigit}`;         // → "NQM5"
    console.log(`Example front-quarter symbol created: ${nqFront}`);

})();