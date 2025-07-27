// ==UserScript==
// @name         Auto Order
// @namespace    http://tampermonkey.net/
// @version      5.4
// @description  Tampermonkey UI for bracket auto trades with TP/SL checkboxes (DOM Intelligence Enhanced)
// @author       You
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/AutoOrder.user.js
// @downloadURL  http://localhost:8080/AutoOrder.user.js
// ==/UserScript==

(function () {
    'use strict';
    console.log('Auto Order script initialized with DOM Intelligence validation');
    var debug = false;

    // ============================================================================
    // DOM INTELLIGENCE VALIDATION FUNCTIONS
    // ============================================================================
    
    // Load UI Elements mapping for unified selectors
    function loadUIElementsMapping() {
        if (window.TRADOVATE_UI_ELEMENTS) {
            console.log('✅ UI Elements mapping already loaded');
            return Promise.resolve();
        }
        
        // Check if mapping script is available
        const script = document.createElement('script');
        script.src = '/scripts/tampermonkey/tradovate_ui_elements_map.js';
        script.onload = () => {
            console.log('✅ UI Elements mapping loaded from external script');
        };
        script.onerror = () => {
            console.log('ℹ️ External UI mapping not found, using inline fallback');
            // Inline fallback for critical selectors used in this script
            window.TRADOVATE_UI_ELEMENTS = {
                MARKET_DATA: {
                    SYMBOL_DISPLAY: '.search-box--input',
                    SYMBOL_ALT: '.contract-symbol span',
                    MARKET_CELLS: '.public_fixedDataTableCell_cellContent'
                },
                ORDER_SUBMISSION: {
                    SUBMIT_BUTTON: '.btn-group .btn-primary'
                },
                ORDER_STATUS: {
                    ORDER_ROWS: '.module.orders .fixedDataTableRowLayout_rowWrapper',
                    ORDER_CELLS: '.public_fixedDataTableCell_cellContent',
                    POSITION_ROWS: '.module.positions .fixedDataTableRowLayout_rowWrapper'
                },
                ACCOUNT_SELECTION: {
                    ACCOUNT_DROPDOWN: '.dropdown-menu'
                }
            };
        };
        document.head.appendChild(script);
        
        return Promise.resolve();
    }

    // Load DOM validation helpers
    function loadDOMHelpers() {
        if (window.domHelpers) {
            console.log('✅ DOM Helpers already loaded');
            return Promise.resolve();
        }
        
        return new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'http://localhost:8080/domHelpers.js';
            script.onload = () => {
                console.log('✅ DOM Helpers loaded externally');
                resolve();
            };
            script.onerror = () => {
                console.warn('⚠️ Could not load external DOM Helpers, using inline version');
                // Inline basic validation functions if external load fails
                window.domHelpers = {
                    waitForElement: async (selector, timeout = 10000) => {
                        const startTime = Date.now();
                        return new Promise((resolve) => {
                            const checkElement = () => {
                                const element = document.querySelector(selector);
                                if (element) {
                                    console.log(`✅ Element found: ${selector} (${Date.now() - startTime}ms)`);
                                    resolve(element);
                                } else if (Date.now() - startTime >= timeout) {
                                    console.warn(`⏰ Timeout waiting for element: ${selector} (${timeout}ms)`);
                                    resolve(null);
                                } else {
                                    setTimeout(checkElement, 100);
                                }
                            };
                            checkElement();
                        });
                    },
                    validateElementExists: (selector) => {
                        const element = document.querySelector(selector);
                        const exists = element !== null;
                        if (exists) {
                            console.log(`✅ Element exists: ${selector}`);
                        } else {
                            console.warn(`❌ Element not found: ${selector}`);
                        }
                        return exists;
                    },
                    validateElementVisible: (element) => {
                        if (!element) return false;
                        const style = window.getComputedStyle(element);
                        const isVisible = style.display !== 'none' && 
                                         style.visibility !== 'hidden' && 
                                         element.offsetWidth > 0 && 
                                         element.offsetHeight > 0;
                        console.log(`${isVisible ? '✅' : '❌'} Element visibility: ${isVisible}`);
                        return isVisible;
                    },
                    validateElementClickable: (element) => {
                        if (!element) return false;
                        const isVisible = window.domHelpers.validateElementVisible(element);
                        const isEnabled = !element.disabled && !element.hasAttribute('disabled');
                        const isClickable = isVisible && isEnabled;
                        console.log(`${isClickable ? '✅' : '❌'} Element clickable: ${isClickable}`);
                        return isClickable;
                    },
                    safeClick: async (selector) => {
                        console.log(`🔍 Safe click validation for: ${selector}`);
                        const element = await window.domHelpers.waitForElement(selector, 5000);
                        if (!element) {
                            console.error(`❌ Cannot click: element not found: ${selector}`);
                            return false;
                        }
                        if (!window.domHelpers.validateElementClickable(element)) {
                            console.error(`❌ Cannot click: element not clickable: ${selector}`);
                            return false;
                        }
                        try {
                            element.click();
                            console.log(`✅ Clicked element successfully: ${selector}`);
                            return true;
                        } catch (error) {
                            console.error(`❌ Error clicking element: ${error.message}`);
                            return false;
                        }
                    }
                };
                console.log('✅ Inline DOM Helpers ready');
                resolve();
            };
            document.head.appendChild(script);
        });
    }
    
    // Initialize DOM Helpers and Order Validation Framework
    Promise.all([
        loadUIElementsMapping(),
        loadDOMHelpers(),
        loadOrderValidationFramework()
    ]).then(() => {
        console.log('🚀 Auto Order script ready with unified UI mapping, DOM Intelligence and Order Validation');
    });
    
    // Load Order Validation Framework
    function loadOrderValidationFramework() {
        return new Promise((resolve) => {
            // Load UI elements mapping
            const uiElementsScript = document.createElement('script');
            uiElementsScript.src = 'http://localhost:8080/tradovate_ui_elements_map.js';
            uiElementsScript.onload = () => {
                console.log('✅ UI Elements mapping loaded');
                
                // Load error patterns
                const errorPatternsScript = document.createElement('script');
                errorPatternsScript.src = 'http://localhost:8080/order_error_patterns.js';
                errorPatternsScript.onload = () => {
                    console.log('✅ Error patterns loaded');
                    
                    // Load validation framework
                    const frameworkScript = document.createElement('script');
                    frameworkScript.src = 'http://localhost:8080/OrderValidationFramework.js';
                    frameworkScript.onload = () => {
                        console.log('✅ OrderValidationFramework loaded');
                        
                        // Initialize validation framework with auto order settings
                        if (!window.autoOrderValidator) {
                            window.autoOrderValidator = new window.OrderValidationFramework({
                                scriptName: 'autoOrder',
                                debugMode: localStorage.getItem('autoOrderValidationDebug') === 'true',
                                performanceMode: true
                            });
                            
                            // Start monitoring for active trading sessions
                            window.autoOrderValidator.startMonitoring();
                            
                            console.log('✅ Auto Order validation framework initialized');
                        }
                        
                        resolve();
                    };
                    frameworkScript.onerror = () => {
                        console.warn('⚠️ Could not load OrderValidationFramework, continuing without advanced validation');
                        resolve();
                    };
                    document.head.appendChild(frameworkScript);
                };
                errorPatternsScript.onerror = () => {
                    console.warn('⚠️ Could not load error patterns');
                    resolve();
                };
                document.head.appendChild(errorPatternsScript);
            };
            uiElementsScript.onerror = () => {
                console.warn('⚠️ Could not load UI elements mapping');
                resolve();
            };
            document.head.appendChild(uiElementsScript);
        });
    }

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
            updateSymbol(window.TRADOVATE_UI_ELEMENTS?.MARKET_DATA?.SYMBOL_DISPLAY || '.search-box--input', normalizedSymbol);
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


    // Enhanced function to click dropdown option for a specific symbol with validation
    async function clickExitForSymbol(symbol, optionId = 'cancel-option-Exit-at-Mkt-Cxl') {
        console.log(`🔍 Order Cancellation: Starting clickExitForSymbol for symbol: ${symbol}, option: ${optionId}`);
        
        // Generate cancellation tracking ID
        const cancellationId = `CANCEL_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        
        // Record cancellation attempt in validation framework
        if (window.autoOrderValidator) {
            window.autoOrderValidator.recordOrderEvent(cancellationId, 'CANCELLATION_ATTEMPT', {
                symbol: symbol,
                optionId: optionId,
                timestamp: Date.now()
            });
        }
        
        // Get baseline state before cancellation
        const preState = await captureOrdersState(symbol);
        console.log(`🔍 Pre-cancellation state captured:`, preState);
        
        const modules = document.querySelectorAll('.module.module-dom');
        let cancellationExecuted = false;
        
        for (const module of modules) {
            const symEl = module.querySelector(window.TRADOVATE_UI_ELEMENTS?.MARKET_DATA?.SYMBOL_ALT || '.contract-symbol span');
            if (symEl && symEl.textContent.trim() === symbol) {
                console.log(`✅ Found matching module for symbol: ${symbol}`);
                
                // Pre-validation: Check if dropdown button exists and is clickable
                const dropdownBtn = module.querySelector('button.btn.dropdown-toggle');
                if (dropdownBtn) {
                    if (!window.domHelpers?.validateElementVisible(dropdownBtn)) {
                        console.error(`❌ Dropdown button not visible for ${symbol}`);
                        if (window.autoOrderValidator) {
                            window.autoOrderValidator.recordOrderEvent(cancellationId, 'CANCELLATION_FAILED', {
                                error: 'Dropdown button not visible',
                                symbol: symbol
                            });
                        }
                        continue;
                    }
                    
                    console.log('✅ Pre-validation passed: Clicking dropdown button');
                    dropdownBtn.click();
                    
                    // Wait for dropdown to appear and process
                    await new Promise((resolve) => {
                        setTimeout(async () => {
                            // Look for visible dropdown menu
                            const dropdownMenu = module.querySelector(window.TRADOVATE_UI_ELEMENTS?.ACCOUNT_SELECTION?.ACCOUNT_DROPDOWN || '.dropdown-menu') || 
                                                document.querySelector('.dropdown-menu[style*="display: block"]');
                            
                            if (dropdownMenu && window.domHelpers?.validateElementVisible(dropdownMenu)) {
                                console.log('✅ Found and validated dropdown menu');
                                
                                // Find the option within the dropdown menu by ID
                                const option = dropdownMenu.querySelector(`#${optionId}`);
                                
                                if (option && window.domHelpers?.validateElementClickable(option)) {
                                    console.log(`✅ Found and clicking option: ${optionId}`);
                                    option.click();
                                    cancellationExecuted = true;
                                } else {
                                    console.warn(`⚠️ Option ${optionId} not found, trying by text`);
                                    
                                    // Try finding by option text if ID doesn't work
                                    const optionByText = Array.from(dropdownMenu.querySelectorAll('a[role="menuitem"]'))
                                        .find(link => link.textContent.includes('Exit at Mkt'));
                                    
                                    if (optionByText && window.domHelpers?.validateElementClickable(optionByText)) {
                                        console.log('✅ Found option by text: Exit at Mkt');
                                        optionByText.click();
                                        cancellationExecuted = true;
                                    } else {
                                        console.warn(`⚠️ Dropdown option not found, trying direct button`);
                                        cancellationExecuted = await tryDirectCancellation(module, symbol);
                                    }
                                }
                            } else {
                                console.warn(`⚠️ Dropdown menu not found or not visible, trying direct button`);
                                cancellationExecuted = await tryDirectCancellation(module, symbol);
                            }
                            
                            resolve();
                        }, 300); // Increased delay for dropdown to appear
                    });
                } else {
                    console.warn(`⚠️ Dropdown button not found for ${symbol}, trying direct cancellation`);
                    cancellationExecuted = await tryDirectCancellation(module, symbol);
                }
                
                break; // Stop after first match
            }
        }
        
        if (!cancellationExecuted) {
            console.error(`❌ Cancellation execution failed for ${symbol}`);
            if (window.autoOrderValidator) {
                window.autoOrderValidator.recordOrderEvent(cancellationId, 'CANCELLATION_FAILED', {
                    error: 'No cancellation method executed',
                    symbol: symbol
                });
            }
            return false;
        }
        
        // Post-cancellation validation
        console.log(`🔍 Starting post-cancellation validation for ${symbol}...`);
        
        // Wait for cancellation to process
        await delay(1000);
        
        // Get post-cancellation state
        const postState = await captureOrdersState(symbol);
        console.log(`🔍 Post-cancellation state captured:`, postState);
        
        // Validate cancellation success
        const validationResult = validateCancellationSuccess(preState, postState, symbol);
        
        if (window.autoOrderValidator) {
            window.autoOrderValidator.recordOrderEvent(cancellationId, 'CANCELLATION_VALIDATED', {
                symbol: symbol,
                preState: preState,
                postState: postState,
                validationResult: validationResult,
                success: validationResult.success
            });
        }
        
        if (validationResult.success) {
            console.log(`✅ Cancellation validation successful for ${symbol}:`, validationResult);
        } else {
            console.error(`❌ Cancellation validation failed for ${symbol}:`, validationResult);
        }
        
        return validationResult.success;
    }
    
    // Helper function to try direct cancellation button
    async function tryDirectCancellation(module, symbol) {
        const exitBtn = Array.from(module.querySelectorAll('button.btn.btn-default'))
            .find(btn => btn.textContent.replace(/\s+/g, ' ').includes('Exit at Mkt'));
        
        if (exitBtn && window.domHelpers?.validateElementClickable(exitBtn)) {
            console.log(`✅ Found and clicking direct Exit at Mkt button for ${symbol}`);
            exitBtn.click();
            return true;
        } else {
            console.error(`❌ No clickable Exit at Mkt button found for ${symbol}`);
            return false;
        }
    }
    
    // Helper function to capture current orders state
    async function captureOrdersState(symbol) {
        try {
            const state = {
                timestamp: Date.now(),
                symbol: symbol,
                ordersCount: 0,
                positionsCount: 0,
                orders: [],
                positions: []
            };
            
            // Capture orders from orders table
            const orderRows = document.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_ROWS || '.module.orders .fixedDataTableRowLayout_rowWrapper');
            for (const row of orderRows) {
                const cells = row.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_CELLS || '.public_fixedDataTableCell_cellContent');
                if (cells.length >= 3) {
                    const orderSymbol = cells[2]?.textContent?.trim();
                    if (!symbol || orderSymbol === symbol) {
                        state.orders.push({
                            id: cells[1]?.textContent?.trim(),
                            symbol: orderSymbol,
                            side: cells[3]?.textContent?.trim(),
                            quantity: cells[4]?.textContent?.trim(),
                            status: cells[6]?.textContent?.trim()
                        });
                    }
                }
            }
            
            // Capture positions from positions table
            const positionRows = document.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.POSITION_ROWS || '.module.positions .fixedDataTableRowLayout_rowWrapper');
            for (const row of positionRows) {
                const cells = row.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_CELLS || '.public_fixedDataTableCell_cellContent');
                if (cells.length >= 2) {
                    const positionSymbol = cells[1]?.textContent?.trim();
                    if (!symbol || positionSymbol === symbol) {
                        state.positions.push({
                            symbol: positionSymbol,
                            quantity: cells[2]?.textContent?.trim(),
                            avgPrice: cells[3]?.textContent?.trim()
                        });
                    }
                }
            }
            
            state.ordersCount = state.orders.length;
            state.positionsCount = state.positions.length;
            
            return state;
        } catch (error) {
            console.error(`❌ Error capturing orders state:`, error);
            return {
                timestamp: Date.now(),
                symbol: symbol,
                error: error.message,
                ordersCount: 0,
                positionsCount: 0,
                orders: [],
                positions: []
            };
        }
    }
    
    // Helper function to validate cancellation success
    function validateCancellationSuccess(preState, postState, symbol) {
        const result = {
            success: false,
            changes: [],
            warnings: [],
            errors: []
        };
        
        try {
            // Check if orders were reduced
            if (postState.ordersCount < preState.ordersCount) {
                const orderReduction = preState.ordersCount - postState.ordersCount;
                result.changes.push(`Orders reduced by ${orderReduction}`);
                result.success = true;
            } else if (postState.ordersCount === preState.ordersCount) {
                result.warnings.push('Order count unchanged after cancellation');
            } else {
                result.errors.push('Order count increased after cancellation attempt');
            }
            
            // Check for position changes (closes)
            if (postState.positionsCount < preState.positionsCount) {
                const positionReduction = preState.positionsCount - postState.positionsCount;
                result.changes.push(`Positions reduced by ${positionReduction}`);
                result.success = true;
            }
            
            // Detailed order comparison
            const cancelledOrders = preState.orders.filter(preOrder => 
                !postState.orders.some(postOrder => postOrder.id === preOrder.id)
            );
            
            if (cancelledOrders.length > 0) {
                result.changes.push(`Cancelled orders: ${cancelledOrders.map(o => o.id).join(', ')}`);
                result.success = true;
            }
            
            // If no changes detected but no errors, consider it potentially successful
            if (result.changes.length === 0 && result.errors.length === 0) {
                result.warnings.push('No detectable changes after cancellation - may have succeeded silently');
            }
            
        } catch (error) {
            result.errors.push(`Validation error: ${error.message}`);
        }
        
        return result;
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
            
            const enableTP = document.getElementById('tpCheckbox').checked;
            const enableSL = document.getElementById('slCheckbox').checked;
            console.log(`TP enabled: ${enableTP}, SL enabled: ${enableSL}`);
            
            // Prepare trade data for unified framework
            tradeData.tpEnabled = enableTP;
            tradeData.slEnabled = enableSL;
            
            const result = await window.UNIFIED_TRADING_FRAMEWORK.createBracketOrder(tradeData, {
                enableValidation: true,
                source: 'autoOrder'
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
        console.log('Creating bracket orders with legacy data:', tradeData);
        const enableTP = document.getElementById('tpCheckbox').checked;
        const enableSL = document.getElementById('slCheckbox').checked;
        console.log(`TP enabled: ${enableTP}, SL enabled: ${enableSL}`);
        
        // Generate bracket group ID for order validation framework
        const bracketGroupId = `BRACKET_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        tradeData.bracketGroupId = bracketGroupId;
        
        console.log(`🔗 Bracket Group ID: ${bracketGroupId}`);

        // DO NOT UNDER ANY CIRCUMSTANCES UPDATE THIS FUNCTION
        async function updateInputValue(selector, value) {
            // wait for the live, visible field
            let input;
            for (let i = 0; i < 25; i++) {
                input = [...document.querySelectorAll(selector)]
                    .find(el => el.offsetParent && !el.disabled);
                if (input) break;
                await delay(100);
            }
            if (!input) return console.error(`No live input for ${selector}`);

            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;

            // write-verify loop – commit with Enter so Tradovate locks the value
            for (let tries = 0; tries < 3; tries++) {
                input.focus();
                setVal.call(input, value);
                ['input','change'].forEach(ev =>
                                           input.dispatchEvent(new Event(ev, { bubbles: true }))
                                          );
                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                }));
                input.blur();                      // force validation
                await delay(300);                  // wait for repaint

                if (+input.value === +value) break; // done
            }
        }


        async function setCommonFields() {
            console.log('Setting common order fields');
            //if (tradeData.symbol) await updateSymbol(window.TRADOVATE_UI_ELEMENTS?.MARKET_DATA?.SYMBOL_DISPLAY || '.search-box--input', normalizeSymbol(tradeData.symbol));
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
            console.log(`🔍 Order Validation Framework: Starting submitOrder for ${orderType}`);
            
            // Use unified framework if available for comprehensive validation and consistency
            if (window.UNIFIED_TRADING_FRAMEWORK?.submitOrder) {
                console.log(`Using unified framework for ${orderType} order submission`);
                
                const result = await window.UNIFIED_TRADING_FRAMEWORK.submitOrder(orderType, priceValue, {
                    tradeData: tradeData,
                    enableValidation: true,  // Enable validation for safety
                    source: 'autoOrder'
                });
                
                if (result.success) {
                    console.log(`✅ Unified order submission successful: ${result.submissionId}`);
                    return result.success;
                } else {
                    console.error(`❌ Unified order submission failed: ${result.error}`);
                    console.log('Falling back to legacy order submission...');
                    // Continue to fallback implementation below
                }
            } else {
                console.log('Unified framework not available, using legacy order submission');
            }
            
            // LEGACY FALLBACK: Pre-submission validation using OrderValidationFramework
            let orderId = null;
            if (window.autoOrderValidator) {
                try {
                    const orderData = {
                        symbol: tradeData.symbol,
                        action: tradeData.action,
                        qty: tradeData.qty,
                        orderType: orderType,
                        price: priceValue,
                        takeProfit: tradeData.takeProfit,
                        stopLoss: tradeData.stopLoss,
                        bracketGroupId: tradeData.bracketGroupId,
                        clientId: `AO_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
                    };
                    
                    console.log(`🔍 Pre-submission validation starting...`);
                    const validationResult = await window.autoOrderValidator.validatePreSubmission(orderData);
                    
                    if (!validationResult.valid) {
                        console.error(`❌ Pre-submission validation failed:`, validationResult.errors);
                        
                        // Log validation failure event
                        if (window.autoOrderValidator.recordOrderEvent) {
                            window.autoOrderValidator.recordOrderEvent(validationResult.validationId, 'VALIDATION_FAILED', {
                                errors: validationResult.errors,
                                warnings: validationResult.warnings
                            });
                        }
                        
                        return false;
                    }
                    
                    orderId = validationResult.orderId;
                    console.log(`✅ Pre-submission validation passed. Order ID: ${orderId}`);
                    
                    // Start submission monitoring
                    window.autoOrderValidator.monitorOrderSubmission(orderId).then(result => {
                        console.log(`📊 Submission monitoring result:`, result);
                    }).catch(error => {
                        console.error(`❌ Submission monitoring error:`, error);
                    });
                    
                } catch (error) {
                    console.error(`❌ Validation framework error:`, error);
                    // Continue with basic validation as fallback
                }
            }
            
            await setCommonFields();

            // STEP 1: Validate and click order type selector
            console.log(`🔍 Pre-validation: Order type selector`);
            const typeSelSelector = '.group.order-type .select-input div[tabindex]';
            if (!window.domHelpers.validateElementExists(typeSelSelector)) {
                console.error(`❌ Order type selector not found: ${typeSelSelector}`);
                if (orderId && window.autoOrderValidator) {
                    window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_FAILED', {
                        error: 'Order type selector not found',
                        selector: typeSelSelector
                    });
                }
                return false;
            }
            
            const typeSel = document.querySelector(typeSelSelector);
            if (!window.domHelpers.validateElementClickable(typeSel)) {
                console.error(`❌ Order type selector not clickable`);
                if (orderId && window.autoOrderValidator) {
                    window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_FAILED', {
                        error: 'Order type selector not clickable'
                    });
                }
                return false;
            }
            
            console.log(`✅ Pre-validation passed: Clicking order type selector`);
            typeSel.click();
            
            // STEP 2: Validate and click dropdown menu item
            await delay(300); // Wait for dropdown to appear
            console.log(`🔍 Pre-validation: Dropdown menu for ${orderType}`);
            
            const dropdownItems = document.querySelectorAll('ul.dropdown-menu li');
            const targetItem = [...dropdownItems].find(li => li.textContent.trim() === orderType);
            
            if (!targetItem) {
                console.error(`❌ Dropdown item not found for order type: ${orderType}`);
                return false;
            }
            
            if (!window.domHelpers.validateElementClickable(targetItem)) {
                console.error(`❌ Dropdown item not clickable: ${orderType}`);
                return false;
            }
            
            console.log(`✅ Pre-validation passed: Clicking dropdown item ${orderType}`);
            targetItem.click();

            await delay(400); // Let Tradovate draw the price box

            // STEP 3: Validate and update price input if needed
            if (priceValue) {
                console.log(`🔍 Pre-validation: Price input field`);
                const priceInputSelector = '.numeric-input.feedback-wrapper input';
                if (!window.domHelpers.validateElementExists(priceInputSelector)) {
                    console.error(`❌ Price input field not found: ${priceInputSelector}`);
                    return false;
                }
                
                console.log(`✅ Pre-validation passed: Updating price input`);
                await updateInputValue(priceInputSelector, priceValue);
                
                // Post-validation: Verify price was set
                const priceInput = document.querySelector(priceInputSelector);
                if (priceInput && priceInput.value !== priceValue.toString()) {
                    console.warn(`⚠️ Post-validation: Price input value mismatch. Expected: ${priceValue}, Got: ${priceInput.value}`);
                } else {
                    console.log(`✅ Post-validation passed: Price input set correctly`);
                }
            }
            
            clickPriceArrow();

            // STEP 4: CRITICAL - Validate and click submit button
            console.log(`🔍 Pre-validation: CRITICAL SUBMIT BUTTON`);
            const submitButtonSelector = '.btn-group .btn-primary';
            
            if (!window.domHelpers.validateElementExists(submitButtonSelector)) {
                console.error(`❌ CRITICAL: Submit button not found: ${submitButtonSelector}`);
                if (orderId && window.autoOrderValidator) {
                    window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_FAILED', {
                        error: 'Submit button not found',
                        selector: submitButtonSelector,
                        critical: true
                    });
                }
                return false;
            }
            
            const submitButton = document.querySelector(submitButtonSelector);
            if (!window.domHelpers.validateElementClickable(submitButton)) {
                console.error(`❌ CRITICAL: Submit button not clickable`);
                if (orderId && window.autoOrderValidator) {
                    window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_FAILED', {
                        error: 'Submit button not clickable',
                        critical: true
                    });
                }
                return false;
            }
            
            // Record submission attempt
            if (orderId && window.autoOrderValidator) {
                window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_ATTEMPT', {
                    orderType: orderType,
                    price: priceValue,
                    timestamp: Date.now()
                });
            }
            
            console.log(`✅ Pre-validation passed: CLICKING CRITICAL SUBMIT BUTTON`);
            submitButton.click();
            
            // Post-validation: Check for submit confirmation or error
            await delay(200);
            console.log(`✅ Post-validation: Submit button clicked, checking order events`);
            const orderEvents = getOrderEvents();
            console.log('📋 Order events after submit:', orderEvents);
            
            // Enhanced post-submission validation using OrderValidationFramework
            if (orderId && window.autoOrderValidator) {
                try {
                    console.log(`🔍 Starting post-submission validation...`);
                    const postValidationResult = await window.autoOrderValidator.validatePostSubmission(orderId);
                    
                    if (postValidationResult.confirmed) {
                        console.log(`✅ Order submission confirmed by validation framework`);
                        window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_CONFIRMED', {
                            confirmationMethod: 'framework_validation',
                            orderEvents: orderEvents
                        });
                    } else if (postValidationResult.errors.length > 0) {
                        console.error(`❌ Post-submission validation detected errors:`, postValidationResult.errors);
                        
                        // Classify each error using the error classification system
                        for (const error of postValidationResult.errors) {
                            if (window.ERROR_CLASSIFICATION) {
                                const classification = window.ERROR_CLASSIFICATION.classifyError(error);
                                const recovery = window.ERROR_CLASSIFICATION.getRecoveryStrategy(classification);
                                
                                console.log(`🔍 Error Classification:`, {
                                    originalError: error,
                                    category: classification.category,
                                    severity: classification.severity,
                                    recovery: recovery.actions,
                                    userAction: classification.userAction
                                });
                                
                                // Record classified error
                                window.autoOrderValidator.recordOrderEvent(orderId, 'CLASSIFIED_ERROR', {
                                    error: error,
                                    classification: classification,
                                    recovery: recovery,
                                    isCritical: window.ERROR_CLASSIFICATION.isCritical(classification),
                                    isRetryable: window.ERROR_CLASSIFICATION.isRetryable(classification)
                                });
                                
                                // Handle critical errors immediately
                                if (window.ERROR_CLASSIFICATION.isCritical(classification)) {
                                    console.error(`🚨 CRITICAL ERROR DETECTED:`, classification);
                                    window.autoOrderValidator.recordOrderEvent(orderId, 'CRITICAL_ERROR_RESPONSE', {
                                        classification: classification,
                                        immediateAction: 'ABORT_SUBMISSION'
                                    });
                                    return false; // Abort on critical errors
                                }
                            }
                        }
                        
                        window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_ERROR_DETECTED', {
                            errors: postValidationResult.errors,
                            warnings: postValidationResult.warnings
                        });
                    } else {
                        console.warn(`⚠️ Post-submission validation inconclusive`);
                        window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_STATUS_UNKNOWN', {
                            warnings: postValidationResult.warnings
                        });
                    }
                } catch (error) {
                    console.error(`❌ Post-submission validation error:`, error);
                    if (window.autoOrderValidator.recordOrderEvent) {
                        window.autoOrderValidator.recordOrderEvent(orderId, 'POST_VALIDATION_ERROR', {
                            error: error.message
                        });
                    }
                }
            }
            
            // Additional error detection using DOM scanning
            if (window.TRADOVATE_UI_ELEMENTS && window.ERROR_CLASSIFICATION) {
                const errorElements = window.TRADOVATE_UI_ELEMENTS.ERROR_DETECTION;
                const errorSelectors = [
                    errorElements.ERROR_MODAL,
                    errorElements.ERROR_ALERT,
                    errorElements.ERROR_MESSAGE,
                    errorElements.WARNING_ALERT
                ];
                
                for (const selector of errorSelectors) {
                    const errorElement = document.querySelector(selector);
                    if (errorElement && window.domHelpers?.validateElementVisible(errorElement)) {
                        const errorText = errorElement.textContent?.trim();
                        if (errorText) {
                            console.error(`🔍 DOM Error Detection: Found error element`, {
                                selector: selector,
                                errorText: errorText
                            });
                            
                            // Classify and handle the error
                            const classification = window.ERROR_CLASSIFICATION.classifyError(errorText);
                            const recovery = window.ERROR_CLASSIFICATION.getRecoveryStrategy(classification);
                            
                            if (orderId && window.autoOrderValidator) {
                                window.autoOrderValidator.recordOrderEvent(orderId, 'DOM_ERROR_DETECTED', {
                                    selector: selector,
                                    errorText: errorText,
                                    classification: classification,
                                    recovery: recovery
                                });
                            }
                            
                            // Log comprehensive error information
                            console.error(`🔍 Classified DOM Error:`, {
                                errorText: errorText,
                                category: classification.category,
                                severity: classification.severity,
                                recovery: recovery.actions,
                                userAction: classification.userAction,
                                isCritical: window.ERROR_CLASSIFICATION.isCritical(classification)
                            });
                            
                            // Handle critical DOM errors
                            if (window.ERROR_CLASSIFICATION.isCritical(classification)) {
                                console.error(`🚨 CRITICAL DOM ERROR - ABORTING SUBMISSION`);
                                return false;
                            }
                        }
                    }
                }
            }
            
            // STEP 5: Validate and click back button
            console.log(`🔍 Pre-validation: Back navigation button`);
            const backButtonSelector = '.icon.icon-back';
            
            // Wait for back button to appear
            const backButton = await window.domHelpers.waitForElement(backButtonSelector, 3000);
            if (!backButton) {
                console.warn(`⚠️ Back button not found within timeout: ${backButtonSelector}`);
                return true; // Still consider success if order was submitted
            }
            
            if (!window.domHelpers.validateElementClickable(backButton)) {
                console.warn(`⚠️ Back button not clickable, but order was submitted`);
                return true;
            }
            
            console.log(`✅ Pre-validation passed: Clicking back button`);
            backButton.click();
            await delay(200);
            
            // Final validation - record successful completion
            if (orderId && window.autoOrderValidator) {
                window.autoOrderValidator.recordOrderEvent(orderId, 'SUBMISSION_COMPLETED', {
                    orderType: orderType,
                    completionTime: Date.now(),
                    success: true
                });
                
                console.log(`✅ Order Validation Framework: submitOrder completed successfully for ${orderType}, Order ID: ${orderId}`);
            } else {
                console.log(`✅ DOM Intelligence: submitOrder completed successfully for ${orderType}`);
            }
            
            return orderId || true; // Return order ID if available, otherwise true for backward compatibility
        }

        console.log(`Submitting initial ${tradeData.orderType || 'MARKET'} order`);
        const parentOrderId = await submitOrder(tradeData.orderType || 'MARKET', tradeData.entryPrice);

        if (tradeData.action === 'Buy') {
            console.log('Flipping action to Sell for TP/SL orders');
            tradeData.action = 'Sell';
            
            // Set parent order reference for child orders
            const originalParentOrderId = tradeData.parentOrderId;
            tradeData.parentOrderId = parentOrderId;
            
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                const tpOrderId = await submitOrder('LIMIT', tradeData.takeProfit);
                
                // Record bracket relationship in validation framework
                if (window.autoOrderValidator && parentOrderId && tpOrderId) {
                    window.autoOrderValidator.recordOrderEvent(parentOrderId, 'CHILD_ORDER_CREATED', {
                        childOrderId: tpOrderId,
                        childOrderType: 'TAKE_PROFIT',
                        price: tradeData.takeProfit
                    });
                }
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                const slOrderId = await submitOrder('STOP', tradeData.stopLoss);
                
                // Record bracket relationship in validation framework
                if (window.autoOrderValidator && parentOrderId && slOrderId) {
                    window.autoOrderValidator.recordOrderEvent(parentOrderId, 'CHILD_ORDER_CREATED', {
                        childOrderId: slOrderId,
                        childOrderType: 'STOP_LOSS',
                        price: tradeData.stopLoss
                    });
                }
            }
            
            // Restore original parent order ID
            tradeData.parentOrderId = originalParentOrderId;
        } else {
            console.log('Flipping action to Buy for TP/SL orders');
            tradeData.action = 'Buy';
            
            // Set parent order reference for child orders
            const originalParentOrderId = tradeData.parentOrderId;
            tradeData.parentOrderId = parentOrderId;
            
            if (enableTP) {
                console.log(`Creating take profit order at ${tradeData.takeProfit}`);
                const tpOrderId = await submitOrder('LIMIT', tradeData.takeProfit);
                
                // Record bracket relationship in validation framework
                if (window.autoOrderValidator && parentOrderId && tpOrderId) {
                    window.autoOrderValidator.recordOrderEvent(parentOrderId, 'CHILD_ORDER_CREATED', {
                        childOrderId: tpOrderId,
                        childOrderType: 'TAKE_PROFIT',
                        price: tradeData.takeProfit
                    });
                }
            }
            if (enableSL) {
                console.log(`Creating stop loss order at ${tradeData.stopLoss}`);
                const slOrderId = await submitOrder('STOP', tradeData.stopLoss);
                
                // Record bracket relationship in validation framework
                if (window.autoOrderValidator && parentOrderId && slOrderId) {
                    window.autoOrderValidator.recordOrderEvent(parentOrderId, 'CHILD_ORDER_CREATED', {
                        childOrderId: slOrderId,
                        childOrderType: 'STOP_LOSS',
                        price: tradeData.stopLoss
                    });
                }
            }
            
            // Restore original parent order ID
            tradeData.parentOrderId = originalParentOrderId;
        }
        
        // Mark bracket group as complete
        if (window.autoOrderValidator && parentOrderId) {
            window.autoOrderValidator.recordOrderEvent(parentOrderId, 'BRACKET_GROUP_COMPLETE', {
                bracketGroupId: tradeData.bracketGroupId,
                enableTP: enableTP,
                enableSL: enableSL,
                completionTime: Date.now()
            });
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

function autoTrade(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, _tickSize = 0.25) {
        console.log(`autoTrade called with: symbol=${inputSymbol}, qty=${quantity}, action=${action}, TP=${takeProfitTicks}, SL=${stopLossTicks}, tickSize=${_tickSize}`);

        // Apply unified risk management position sizing - DRY refactored
        let adjustedQuantity = quantity;
        try {
            if (typeof window.unifiedRiskManagement !== 'undefined') {
                console.log('[autoTrade] Applying unified risk management position sizing');
                
                // Try to get current account name
                let accountName = null;
                try {
                    const accountElement = document.querySelector('.account-selector .account-name');
                    if (accountElement) {
                        accountName = accountElement.textContent.trim();
                    }
                } catch (e) {
                    console.warn('[autoTrade] Could not get account name:', e);
                }
                
                if (accountName) {
                    adjustedQuantity = window.unifiedRiskManagement.calculatePositionSize(
                        quantity, 
                        accountName
                    );
                    
                    if (adjustedQuantity !== quantity) {
                        console.log(`[autoTrade] Position size adjusted: ${quantity} -> ${adjustedQuantity} for account ${accountName}`);
                    }
                }
            }
        } catch (error) {
            console.warn('[autoTrade] Risk management adjustment failed, using original quantity:', error);
        }

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
            qty: adjustedQuantity.toString(), // Use risk-adjusted quantity
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

    function getMarketData(inputSymbol) {
        console.log(`getMarketData called for: "${inputSymbol}"`);
        const symbol = /^[A-Z]{1,3}$/.test(inputSymbol)
            ? getFrontQuarter(inputSymbol)
            : inputSymbol.toUpperCase();
        console.log(`Using symbol: "${symbol}" for market data lookup`);

        // 1️⃣ look for an existing row - updated to search more flexibly
        console.log('Searching for symbol in data table rows');
        
        // First try the old selector for backwards compatibility
        let symbolCells = document.querySelectorAll('.symbol-main');
        console.log(`Found ${symbolCells.length} .symbol-main cells`);
        
        // If old selector doesn't work, search all elements for the symbol
        if (symbolCells.length === 0) {
            console.log('Trying flexible symbol search...');
            const allElements = Array.from(document.querySelectorAll('*'));
            symbolCells = allElements.filter(el => 
                el.textContent && 
                el.textContent.trim() === symbol &&
                el.children.length === 0 // Only leaf elements
            );
            console.log(`Found ${symbolCells.length} elements containing "${symbol}"`);
        }

        let row = null;
        if (symbolCells.length > 0) {
            // Try to find the row using old structure first
            row = [...symbolCells]
                .find(el => el.textContent.trim() === symbol)
                ?.closest('.fixedDataTableRowLayout_rowWrapper');
                
            // If old structure doesn't work, try to find parent row element
            if (!row && symbolCells.length > 0) {
                console.log('Trying flexible row search...');
                const symbolElement = [...symbolCells].find(el => el.textContent.trim() === symbol);
                if (symbolElement) {
                    // Look for parent elements that might be the row (tr, div with multiple cells, etc.)
                    let parent = symbolElement.parentElement;
                    while (parent && parent !== document.body) {
                        // Check if this parent has multiple "cell-like" children
                        const childCells = parent.querySelectorAll('*').length;
                        if (childCells >= 5) { // A data row should have multiple cells
                            row = parent;
                            console.log(`Found potential row element: ${parent.tagName} with ${childCells} child elements`);
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
            }
        }

        // 2️⃣ if missing, type the symbol into Tradovate’s search so it appears
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
        
        // Try old selector first
        let cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
        console.log(`Found ${cells.length} .public_fixedDataTableCell_cellContent cells`);
        
        // If old selector doesn't work, get all child elements as potential cells
        if (cells.length === 0) {
            console.log('Trying flexible cell extraction...');
            cells = Array.from(row.querySelectorAll('*')).filter(el => 
                el.textContent && 
                el.textContent.trim() && 
                el.children.length === 0 // Only leaf elements with text
            );
            console.log(`Found ${cells.length} potential cell elements`);
        }

        let bidPrice, offerPrice;
        
        if (cells.length >= 6) {
            // Standard case: use expected positions
            bidPrice = cells[4]?.textContent.trim();
            offerPrice = cells[5]?.textContent.trim();
        } else {
            // Flexible case: search for price-like patterns
            console.log('Searching for price patterns in cells...');
            const pricePattern = /^\d+\.?\d*$/;
            const priceCells = Array.from(cells).filter(cell => {
                const text = cell.textContent.trim();
                return pricePattern.test(text) && parseFloat(text) > 1000; // Futures prices are typically > 1000
            });
            
            if (priceCells.length >= 2) {
                bidPrice = priceCells[0]?.textContent.trim();
                offerPrice = priceCells[1]?.textContent.trim();
                console.log(`Found price patterns: bid=${bidPrice}, offer=${offerPrice}`);
            } else {
                console.log('Could not identify bid/offer prices from cell patterns');
            }
        }
        
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

    // --- EXAMPLE: build an NQ front-quarter symbol ---
    console.log('Creating example front-quarter symbol');
    const { letter, yearDigit } = getQuarterlyCode();  // e.g. M & 5
    const nqFront = `NQ${letter}${yearDigit}`;         // → "NQM5"
    console.log(`Example front-quarter symbol created: ${nqFront}`);

})();