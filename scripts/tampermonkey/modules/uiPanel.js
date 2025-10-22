import driver from './autoDriver.js';

function renderPanel(driverInstance, { visible = false } = {}) {
    console.log(`Creating UI (visible=${visible})`);
    if (!driverInstance) {
        console.warn('[TradoUIPanel] renderPanel called without driver instance');
        return null;
    }

    const state = driverInstance.state;
    const futuresTickData = driverInstance.futuresTickData;
    const normalizeSymbol = driverInstance.normalizeSymbol;

    
    // Default symbol (no localStorage)
    const defaultSymbol = 'NQ';
    
    // Extract root symbol (remove expiry) for futuresTickData lookup
    const rootSymbol = defaultSymbol.replace(/[A-Z]\d+$/, '');
    const symbolData = futuresTickData[rootSymbol] || futuresTickData['NQ'];
    
    // Initialize state with symbol defaults
    state.symbol = defaultSymbol;
    state.tp = symbolData.defaultTP;
    state.sl = symbolData.defaultSL;
    state.tickSize = symbolData.tickSize;
    
    // Always use symbol defaults - no localStorage persistence
    const defaultTP   = symbolData.defaultTP.toString();
    const defaultSL   = symbolData.defaultSL.toString();
    const defaultQty  = '10';
    const defaultTick = symbolData.tickSize.toString();
    
    console.log(`Using defaults: TP=${defaultTP}, SL=${defaultSL}, Qty=${defaultQty}, Tick=${defaultTick}, Symbol=${defaultSymbol}`);
    console.log(`Symbol data for ${rootSymbol}: defaultTP=${symbolData.defaultTP}, defaultSL=${symbolData.defaultSL}`);

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

        // Default box position (no localStorage)
        container.style.top = '20px';
        container.style.right = '20px';
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
            <input type="text" id="symbolInput" value="${defaultSymbol}"
                style="width:50%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" 
                placeholder="Symbol" />
        </div>
        
        <!-- Hidden Tick Size Input -->
        <div id="tickContainer" style="display:none;margin-bottom:8px;">
            <label style="display:block;margin-bottom:4px;font-size:11px;">Tick Size</label>
            <input type="number" id="tickInput" step="0.01" value="${defaultTick}"
                style="width:100%;text-align:center;border-radius:4px;border:1px solid #666;background:#2a2a2a;color:#fff;" />
        </div>

        <!-- Main Controls -->
        <div id="mainControls">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <input type="checkbox" id="tpCheckbox" checked />
                <div style="display:flex;gap:4px;flex:1;">
                    <input type="number" id="tpInput" value="${defaultTP}"
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
                    <input type="number" id="slInput" value="${defaultSL}"
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
                    <input type="number" id="qtyInput" value="${defaultQty}" min="1"
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
    } else {
        // Invisible UI - only essential inputs
        container.innerHTML = `
            <input type="text" id="symbolInput" value="${defaultSymbol}" />
            <input type="number" id="tickInput" value="${defaultTick}" />
            <input type="number" id="tpInput" value="${defaultTP}" />
            <input type="number" id="slInput" value="${defaultSL}" />
            <input type="number" id="qtyInput" value="${defaultQty}" />
            <input type="number" id="entryPriceInput" />
            <input type="number" id="tpPriceInput" />
            <input type="number" id="slPriceInput" />
            <input type="checkbox" id="tpCheckbox" checked />
            <input type="checkbox" id="slCheckbox" checked />
        `;
    }

    // Don't create if it already exists
    const existingId = visible ? 'bracket-trade-box' : 'invisible-trade-inputs';
    if (document.getElementById(existingId)) {
        console.log(`${existingId} already exists, skipping creation`);
        return document.getElementById(existingId);
    }
    
    document.body.appendChild(container);
    console.log('UI container added to DOM');

    // --- Universal Event Handlers (Active in Both Modes) ---
    console.log('Setting up universal event handlers');
    const slInput  = document.getElementById('slInput');
    const tpInput  = document.getElementById('tpInput');
    const qtyInput = document.getElementById('qtyInput');
    
    // SL input handler - triggers TP calculation
    if (slInput) {
        slInput.addEventListener('input', () => {
            console.log(`SL input changed to: ${slInput.value}`);
            const slVal = parseFloat(slInput.value);
            if (!isNaN(slVal)) {
                state.sl = slVal;
                if (tpInput) tpInput.value = Math.round(slVal * 3.5);
                state.tp = Math.round(slVal * 3.5);
                console.log(`Calculated TP: ${state.tp} (SL × 3.5)`);
            }
        });
    }
    
    // TP input handler - updates state
    if (tpInput) {
        tpInput.addEventListener('input', () => {
            console.log(`TP input changed to: ${tpInput.value}`);
            const tpVal = parseFloat(tpInput.value);
            if (!isNaN(tpVal)) {
                state.tp = tpVal;
            }
        });
    }
    
    // Quantity input handler - updates state
    if (qtyInput) {
        qtyInput.addEventListener('input', e => {
            console.log(`Quantity input changed to: ${e.target.value}`);
            const qtyVal = parseInt(e.target.value);
            if (!isNaN(qtyVal) && qtyVal > 0) {
                state.qty = qtyVal;
            }
        });
    }
    
    // Symbol input handler - updates state
    const symbolInput = document.getElementById('symbolInput');
    if (symbolInput) {
            symbolInput.addEventListener('input', e => {
                console.log(`Symbol input changed to: ${e.target.value}`);
                state.symbol = e.target.value;
            });

            // Symbol change handler - updates defaults and Tradovate interface
            symbolInput.addEventListener('change', e => {
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
            
            // Update state with new defaults
            state.sl = symbolDefaults.defaultSL;
            state.tp = symbolDefaults.defaultTP;

            // Update tick size if available
            if (typeof symbolDefaults.tickSize === 'number') {
                tickInput.value = symbolDefaults.tickSize;
                state.tickSize = symbolDefaults.tickSize;
                console.log(`Updated tick size to ${symbolDefaults.tickSize} for ${rootSymbol}`);
            }

            console.log(`✅ Updated SL/TP to default values for ${rootSymbol}: SL=${slInput.value}, TP=${tpInput.value}`);
        }

                // Update the symbol in Tradovate's interface
                driverInstance.updateSymbol('.trading-ticket .search-box--input', normalizedSymbol);
            });
    }
    
    // Tick input handler - updates state
    const tickInput = document.getElementById('tickInput');
    if (tickInput) {
        tickInput.addEventListener('input', e => {
            console.log(`Tick size input changed to: ${e.target.value}`);
            const tickVal = parseFloat(e.target.value);
            if (!isNaN(tickVal) && tickVal > 0) {
                state.tickSize = tickVal;
            }
        });
    }

    // --- UI-Specific Event Handlers (Visible Mode Only) ---
    if (visible) {
        console.log('Setting up UI event handlers');
    document.getElementById('closeAllBtn').addEventListener('click', () => {
        console.log('Close All button clicked');
        try {
            const symbol = document.getElementById('symbolInput').value || 'NQ';
            const normalizedSymbol = normalizeSymbol(symbol);
            console.log(`Calling clickExitForSymbol for: ${normalizedSymbol} with Exit at Mkt & Cxl option`);
            
            // Call the clickExitForSymbol function with the normalized symbol and Exit at Mkt option
            driverInstance.clickExitForSymbol(normalizedSymbol, 'cancel-option-Exit-at-Mkt-Cxl');
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
            driverInstance.clickExitForSymbol(normalizedSymbol, 'cancel-option-Cancel-All');
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
            driverInstance.clickExitForSymbol(normalizedSymbol, 'cancel-option-Reverse-Cxl');
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
            driverInstance.moveStopLossToBreakeven(normalizedSymbol);
            console.log('Breakeven action triggered for symbol:', normalizedSymbol);
        } catch (err) {
            console.error("Breakeven operation failed:", err);
        }
    });

    // No toggle for tick container - it remains permanently hidden

    // Set default values (event handlers moved to universal section)
    console.log('Setting up default values');
    document.getElementById('symbolInput').value = 'NQ'; // Default symbol

    document.getElementById('tickInput').value = state.tickSize; // Use state tick size

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
            // localStorage removed - box position not persisted
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
        driverInstance.autoTrade(symbol, qty, 'Buy', tp, sl, tickSize).finally(() => {
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
        driverInstance.autoTrade(symbol, qty, 'Sell', tp, sl, tickSize).finally(() => {
            // Reset price inputs after order is placed
            document.getElementById('entryPriceInput').value = '';
            document.getElementById('tpPriceInput').value = '';
            document.getElementById('slPriceInput').value = '';
            console.log('Price inputs reset after SELL order');
        });
    });
    } // End of visible-only event handlers
    
    // No localStorage persistence - using in-memory state only
    console.log('State management: Using in-memory state only, no persistence');

    return container;
}

export function createUIPanel({ driverInstance = driver } = {}, defaultOptions = {}) {
    let mounted = false;
    let lastVisible = false;
    let lastContainer = null;

    function mount(options = {}) {
        const { visible = true } = { ...defaultOptions, ...options };
        const container = renderPanel(driverInstance, { visible });
        if (container) {
            mounted = true;
            lastVisible = visible;
            lastContainer = container;
        }
        return container;
    }

    function createInvisibleUI() {
        return mount({ visible: false });
    }

    function show() {
        return mount({ visible: true });
    }

    function hide() {
        let removed = false;
        const visiblePanel = document.getElementById('bracket-trade-box');
        const invisiblePanel = document.getElementById('invisible-trade-inputs');
        if (visiblePanel) {
            visiblePanel.remove();
            removed = true;
        }
        if (invisiblePanel) {
            invisiblePanel.remove();
            removed = true;
        }
        if (removed) {
            mounted = false;
            lastVisible = false;
            lastContainer = null;
        }
        return removed;
    }

    function getStatus() {
        return {
            mounted,
            visible: lastVisible,
            hasPanel: !!document.getElementById('bracket-trade-box'),
            hasInvisiblePanel: !!document.getElementById('invisible-trade-inputs'),
            lastContainer,
        };
    }

    return {
        mount,
        createUI: mount,
        createInvisibleUI,
        show,
        hide,
        getStatus,
        render: (options) => renderPanel(driverInstance, options),
    };
}

const panelSingleton = createUIPanel();
driver.registerUIPanel(panelSingleton);

if (typeof window !== 'undefined') {
    window.TradoUIPanel = panelSingleton;
}

export default panelSingleton;
