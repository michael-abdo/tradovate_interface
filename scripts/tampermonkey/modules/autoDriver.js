/**
 * Automation driver extracted from autoOrder.user.js.
 * This module exposes the Tradovate automation engine without the UI layer.
 */
'use strict';
console.log('Auto Order script initialized - AUTOMATIC HOT RELOAD SUCCESS!');
var debug = false;

function delay(ms) {
    console.log(`Delaying for ${ms}ms`);
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Simple in-memory state to track current UI values
const currentState = {
    symbol: 'NQ',
    tickSize: 0.25,
    tp: null,     // Will be set from futuresTickData defaults
    sl: null,     // Will be set from futuresTickData defaults
    qty: 10,
    entryPrice: null,
    tpPrice: null,
    slPrice: null,
    tpEnabled: true,
    slEnabled: true
};




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
    const symbolData = futuresTickData[rootSymbol];
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

// Initialize UI in invisible mode to test dashboard integration

async function updateSymbol(selector, value) {
        console.log(`updateSymbol called with selector: "${selector}", value: "${value}"`);
        let inputs = document.querySelectorAll(selector);
        console.log(`Found ${inputs.length} matching inputs with selector: ${selector}`);
        
        // If no inputs found with primary selector, try fallback selectors
        if (inputs.length === 0) {
            const fallbackSelectors = [
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
    console.log('Creating bracket orders with data:', tradeData);
    const tpCheckbox = document.getElementById('tpCheckbox');
    const slCheckbox = document.getElementById('slCheckbox');

    if (tpCheckbox && typeof tradeData.enableTP === 'boolean') {
        tpCheckbox.checked = tradeData.enableTP;
    }
    if (slCheckbox && typeof tradeData.enableSL === 'boolean') {
        slCheckbox.checked = tradeData.enableSL;
    }

    const enableTP = typeof tradeData.enableTP === 'boolean' ? tradeData.enableTP : (tpCheckbox ? tpCheckbox.checked : true);
    const enableSL = typeof tradeData.enableSL === 'boolean' ? tradeData.enableSL : (slCheckbox ? slCheckbox.checked : true);
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
        console.log(`🔧 Starting submitOrder for ${orderType} order`);
        
        // DEBUG: Verify price parameter received
        console.log(`🔍 DEBUG: submitOrder called with orderType=${orderType}, priceValue=${priceValue}`);
        
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
        
        const menuItems = [...document.querySelectorAll('ul.dropdown-menu li')];
        const availableTypes = menuItems.map(li => li.textContent.trim());
        console.log('[submitOrder] Available order type options:', availableTypes);
        window.lastOrderTypeOptions = availableTypes;
        window.lastOrderTypeDebug = { orderType, availableTypes, dropdownHTML: document.querySelector('.group.order-type')?.outerHTML, timestamp: new Date().toISOString() };
        const normalizedOrderType = orderType.toUpperCase();
        const orderTypeMap = {
            'MARKET': ['MARKET', 'MARKET ORDER'],
            'LIMIT': ['LIMIT', 'LIMIT ORDER'],
            'STOP': ['STOP', 'STOP MARKET', 'STOP ORDER'],
            'STOP LIMIT': ['STOP LIMIT', 'STOP-LIMIT'],
            'TRL STOP': ['TRAILING STOP', 'TRAIL STOP'],
            'TRL STP LMT': ['TRAILING STOP LIMIT', 'TRL STP LMT']
        };
        const candidates = orderTypeMap[normalizedOrderType] || [orderType];
        const orderTypeOption = menuItems.find(li => candidates.includes(li.textContent.trim()))
            || menuItems.find(li => li.textContent.trim().toUpperCase() === normalizedOrderType);
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
            // DEBUG: Verify price value just before setting in input
            console.log(`🔍 DEBUG: About to set price input to: ${priceValue} (type: ${typeof priceValue})`);
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
            // DEBUG: Verify TP price just before submission
            console.log(`🔍 DEBUG: About to submit TP LIMIT order at price: ${tradeData.takeProfit}`);
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
            // DEBUG: Verify TP price just before submission
            console.log(`🔍 DEBUG: About to submit TP LIMIT order at price: ${tradeData.takeProfit}`);
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
    console.log(`   Main order: ${bracketFeedback.mainOrder?.success ? 'Success' : 'Failed'}`);
    console.log(`   TP order: ${bracketFeedback.tpOrder?.success ? 'Success' : bracketFeedback.tpOrder ? 'Failed' : 'N/A'}`);
    console.log(`   SL order: ${bracketFeedback.slOrder?.success ? 'Success' : bracketFeedback.slOrder ? 'Failed' : 'N/A'}`);
    
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

// 🔄 CAPTURE TRADOVATE ORDER FEEDBACK SYSTEM
async function captureOrderFeedback() {
    console.log('🔄 CAPTURING TRADOVATE ORDER FEEDBACK...');
    
    // Wait a moment for order feedback to load
    await delay(500);
    
    // Look for the order history container
    const orderHistoryDiv = document.querySelector('.order-history');
    if (!orderHistoryDiv) {
        console.log('❌ Order history div not found - no feedback to capture');
        return {
            success: false,
            orders: [],
            rejectionReason: null,
            error: 'Order history not found'
        };
    }
    
    console.log('✅ Found order history div - capturing feedback...');
    
    // Extract the trading ticket header information
    const ticketHeader = orderHistoryDiv.querySelector('.trading-ticket-header');
    let orderType = 'UNKNOWN';
    let requestedPrice = null;
    let orderQuantity = null;
    let orderAction = null;
    let orderId = null;
    let fillRatio = null;
    
    if (ticketHeader) {
        // Extract symbol info
        const symbolDiv = ticketHeader.querySelector('div[style*="font-size: 160%"]');
        const symbol = symbolDiv ? symbolDiv.textContent.trim() : 'UNKNOWN';
        
        // Extract order summary
        const orderSummaryDiv = ticketHeader.querySelector('div:last-child');
        const orderSummary = orderSummaryDiv ? orderSummaryDiv.textContent.trim() : 'No summary';
        
        // Parse order type from summary
        if (orderSummary.includes(' MKT ')) orderType = 'MARKET';
        else if (orderSummary.includes(' LMT ')) orderType = 'LIMIT';
        else if (orderSummary.includes(' STP LMT ')) orderType = 'STOP_LIMIT';
        else if (orderSummary.includes(' STP ')) orderType = 'STOP';
        
        // Extract order ID
        const orderIdMatch = orderSummary.match(/#(\d+)/);
        orderId = orderIdMatch ? orderIdMatch[1] : null;
        
        // Extract action (Buy/Sell)
        orderAction = orderSummary.includes('Buy') ? 'Buy' : 
                     orderSummary.includes('Sell') ? 'Sell' : null;
        
        // Extract quantity
        const quantityMatch = orderSummary.match(/(\d+)\s+[A-Z]+\d*\s+(?:MKT|LMT|STP)/);
        orderQuantity = quantityMatch ? parseInt(quantityMatch[1]) : null;
        
        // Extract limit price if present
        const limitPriceMatch = orderSummary.match(/LMT at ([\d.]+)/);
        requestedPrice = limitPriceMatch ? parseFloat(limitPriceMatch[1]) : null;
        
        // Extract fill ratio (e.g., "6/6" or "3/5")
        const fillRatioMatch = orderSummary.match(/(\d+)\/(\d+)/);
        fillRatio = fillRatioMatch ? {
            filled: parseInt(fillRatioMatch[1]),
            total: parseInt(fillRatioMatch[2]),
            isPartial: parseInt(fillRatioMatch[1]) < parseInt(fillRatioMatch[2]),
            percentFilled: (parseInt(fillRatioMatch[1]) / parseInt(fillRatioMatch[2]) * 100).toFixed(2)
        } : null;
        
        console.log(`📊 ORDER FEEDBACK - Symbol: ${symbol}`);
        console.log(`📊 ORDER FEEDBACK - Summary: ${orderSummary}`);
        console.log(`📊 ORDER FEEDBACK - Order Type: ${orderType}`);
        console.log(`📊 ORDER FEEDBACK - Order ID: ${orderId}`);
        console.log(`📊 ORDER FEEDBACK - Action: ${orderAction}`);
        console.log(`📊 ORDER FEEDBACK - Quantity: ${orderQuantity}`);
        if (requestedPrice) {
            console.log(`📊 ORDER FEEDBACK - Requested Price: ${requestedPrice}`);
        }
        if (fillRatio) {
            console.log(`📊 ORDER FEEDBACK - Fill Status: ${fillRatio.filled}/${fillRatio.total} (${fillRatio.percentFilled}%${fillRatio.isPartial ? ' - PARTIAL FILL' : ' - COMPLETE'})`);
        }
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

    if (orderType === 'UNKNOWN' && orderEvents.length > 0) {
        const eventTexts = orderEvents.map(e => e.event.toUpperCase());
        if (eventTexts.some(e => e.includes(' STP LMT '))) orderType = 'STOP_LIMIT';
        else if (eventTexts.some(e => e.includes(' STP '))) orderType = 'STOP';
        else if (eventTexts.some(e => e.includes(' LMT '))) orderType = 'LIMIT';
        else if (eventTexts.some(e => e.includes(' MKT '))) orderType = 'MARKET';
    }

    if (!orderAction && orderEvents.length > 0) {
        const actionMatch = orderEvents[0].event.match(/^(BUY|SELL)/i);
        if (actionMatch) {
            const word = actionMatch[1].toLowerCase();
            orderAction = word.charAt(0).toUpperCase() + word.slice(1);
        }
    }

    if (!orderQuantity && orderEvents.length > 0) {
        const qtyMatch = orderEvents[0].event.match(/^(?:BUY|SELL)\s+(\d+)/i);
        if (qtyMatch) orderQuantity = parseInt(qtyMatch[1], 10);
    }

    // Extract the entire order history HTML for complete analysis
    console.log('📊 ORDER FEEDBACK - Full HTML Structure:');
    console.log(orderHistoryDiv.outerHTML);
    
    // Extract individual fill events with quantities
    const fillEvents = orderEvents
        .filter(event => event.fillPrice !== null)
        .map(event => {
            // Parse quantity from event text (e.g., "6@24824.00 NQZ5")
            const fillMatch = event.event.match(/(\d+)@([\d.]+)/);
            return {
                timestamp: event.timestamp,
                id: event.id,
                price: event.fillPrice,
                quantity: fillMatch ? parseInt(fillMatch[1]) : null,
                eventText: event.event
            };
        });
    
    // Parse stop loss and take profit order IDs
    let stopLossOrderId = null;
    let takeProfitOrderId = null;
    let bracketOrders = [];
    
    // Look for bracket order creation events
    orderEvents.forEach(event => {
        // Check for stop loss order creation
        if (event.event.includes('STP') || event.comment.includes('Stop')) {
            const stopIdMatch = event.event.match(/#?(\d+)/);
            if (stopIdMatch) {
                stopLossOrderId = stopIdMatch[1];
                bracketOrders.push({
                    type: 'STOP_LOSS',
                    orderId: stopLossOrderId,
                    event: event
                });
            }
        }
        
        // Check for take profit order creation
        if (event.event.includes('LMT') && (event.comment.includes('Profit') || event.comment.includes('Target'))) {
            const tpIdMatch = event.event.match(/#?(\d+)/);
            if (tpIdMatch && tpIdMatch[1] !== orderId) { // Make sure it's not the main order
                takeProfitOrderId = tpIdMatch[1];
                bracketOrders.push({
                    type: 'TAKE_PROFIT',
                    orderId: takeProfitOrderId,
                    event: event
                });
            }
        }
        
        // Also check for bracket order indicators in comments
        if (event.comment.includes('bracket') || event.comment.includes('OCO')) {
            console.log(`📊 BRACKET ORDER DETECTED - Event: ${event.event}, Comment: ${event.comment}`);
        }
    });
    
    if (bracketOrders.length > 0) {
        console.log(`📊 BRACKET ORDERS FOUND: ${bracketOrders.length} orders`);
        bracketOrders.forEach(bo => {
            console.log(`📊 ${bo.type} Order ID: ${bo.orderId}`);
        });
    }
    
    // Extract commission and fees information
    let commission = null;
    let fees = [];
    let totalCost = 0;
    
    orderEvents.forEach(event => {
        // Look for commission in comments or event text
        const commissionMatch = event.comment.match(/commission[:\s]+\$?([\d.]+)/i) || 
                               event.event.match(/commission[:\s]+\$?([\d.]+)/i);
        if (commissionMatch) {
            commission = parseFloat(commissionMatch[1]);
            totalCost += commission;
            console.log(`📊 COMMISSION FOUND: $${commission}`);
        }
        
        // Look for fees
        const feeMatch = event.comment.match(/fee[:\s]+\$?([\d.]+)/i) || 
                        event.event.match(/fee[:\s]+\$?([\d.]+)/i);
        if (feeMatch) {
            const fee = parseFloat(feeMatch[1]);
            fees.push({
                amount: fee,
                description: event.comment || event.event,
                timestamp: event.timestamp
            });
            totalCost += fee;
            console.log(`📊 FEE FOUND: $${fee}`);
        }
        
        // Look for exchange fees specifically
        if (event.comment.includes('Exchange') || event.event.includes('Exchange')) {
            const exchangeFeeMatch = event.comment.match(/\$?([\d.]+)/) || 
                                    event.event.match(/\$?([\d.]+)/);
            if (exchangeFeeMatch) {
                const exchangeFee = parseFloat(exchangeFeeMatch[1]);
                fees.push({
                    amount: exchangeFee,
                    description: 'Exchange Fee',
                    timestamp: event.timestamp
                });
            }
        }
    });
    
    // Extract order timing metrics
    let timingMetrics = {
        submittedAt: null,
        firstFillAt: null,
        completedAt: null,
        timeToFill: null,
        riskCheckTime: null
    };
    
    if (orderEvents.length > 0) {
        // First event is typically order submission
        timingMetrics.submittedAt = orderEvents[0].timestamp;
        
        // Find risk check event
        const riskCheckEvent = orderEvents.find(e => e.event.includes('Risk Passed'));
        if (riskCheckEvent) {
            const submittedTime = new Date(timingMetrics.submittedAt);
            const riskTime = new Date(riskCheckEvent.timestamp);
            timingMetrics.riskCheckTime = riskTime - submittedTime; // milliseconds
            console.log(`📊 TIMING - Risk check completed in ${timingMetrics.riskCheckTime}ms`);
        }
        
        // Find first fill
        const firstFill = fillEvents[0];
        if (firstFill) {
            timingMetrics.firstFillAt = firstFill.timestamp;
            const submittedTime = new Date(timingMetrics.submittedAt);
            const fillTime = new Date(timingMetrics.firstFillAt);
            timingMetrics.timeToFill = fillTime - submittedTime; // milliseconds
            console.log(`📊 TIMING - First fill in ${timingMetrics.timeToFill}ms`);
        }
        
        // Last event timestamp is completion
        timingMetrics.completedAt = orderEvents[orderEvents.length - 1].timestamp;
        
        // Calculate total order duration
        const submittedTime = new Date(timingMetrics.submittedAt);
        const completedTime = new Date(timingMetrics.completedAt);
        const totalDuration = completedTime - submittedTime;
        timingMetrics.totalDuration = totalDuration;
        
        console.log(`📊 TIMING - Order completed in ${totalDuration}ms total`);
        console.log(`📊 TIMING - Submitted: ${timingMetrics.submittedAt}`);
        console.log(`📊 TIMING - Completed: ${timingMetrics.completedAt}`);
    }
    
    // Extract fill prices from order events
    const fillPrices = orderEvents
        .filter(event => event.fillPrice !== null)
        .map(event => event.fillPrice);
    
    // Calculate average fill price if we have fills
    const averageFillPrice = fillPrices.length > 0 
        ? fillPrices.reduce((sum, price) => sum + price, 0) / fillPrices.length
        : null;
    
    // Calculate price improvement for limit orders
    let priceImprovement = null;
    if (orderType === 'LIMIT' && requestedPrice && averageFillPrice) {
        // For buy orders: negative improvement means filled at better (lower) price
        // For sell orders: positive improvement means filled at better (higher) price
        if (orderAction === 'Buy') {
            priceImprovement = requestedPrice - averageFillPrice;
        } else if (orderAction === 'Sell') {
            priceImprovement = averageFillPrice - requestedPrice;
        }
    }
    
    // Calculate slippage for market orders
    let slippage = null;
    let slippageTicks = null;
    if (orderType === 'MARKET' && averageFillPrice) {
        // Get the symbol to determine tick size
        const symbolDiv = ticketHeader?.querySelector('div[style*="font-size: 160%"]');
        const symbol = symbolDiv ? symbolDiv.textContent.trim() : '';
        const rootSymbol = symbol.replace(/[A-Z]\d+$/, '');
        const symbolData = futuresTickData[rootSymbol];
        const tickSize = symbolData?.tickSize || 0.25;
        
        // For market orders, we need the expected price at submission
        // Since we don't have that, we'll calculate slippage indicators
        if (fillPrices.length > 1) {
            // Calculate price range for multiple fills (indicates slippage)
            const minFill = Math.min(...fillPrices);
            const maxFill = Math.max(...fillPrices);
            const priceRange = maxFill - minFill;
            const priceRangeTicks = Math.round(priceRange / tickSize);
            
            slippage = {
                priceRange: priceRange,
                priceRangeTicks: priceRangeTicks,
                minFillPrice: minFill,
                maxFillPrice: maxFill,
                fillCount: fillPrices.length,
                tickSize: tickSize,
                note: 'Slippage calculated from fill price range. Mid-price at submission not available.'
            };
            
            console.log(`📊 MARKET ORDER SLIPPAGE - Price range: ${priceRange} (${priceRangeTicks} ticks)`);
            console.log(`📊 MARKET ORDER SLIPPAGE - Fills ranged from ${minFill} to ${maxFill}`);
        } else if (fillPrices.length === 1) {
            // Single fill - can't calculate slippage without submission price
            slippage = {
                fillPrice: fillPrices[0],
                tickSize: tickSize,
                note: 'Single fill. Slippage cannot be calculated without mid-price at submission.'
            };
            console.log(`📊 MARKET ORDER - Single fill at ${fillPrices[0]}`);
        }
    }
    
    // Check for specific rejection reasons or success indicators
    const rejectionText = orderHistoryDiv.textContent;
    let feedbackResult = {
        success: false,
        orders: orderEvents || [],
        rejectionReason: null,
        error: null,
        // Enhanced order details
        orderId: orderId,
        orderType: orderType,
        orderAction: orderAction,
        orderQuantity: orderQuantity,
        requestedPrice: requestedPrice,
        averageFillPrice: averageFillPrice,
        priceImprovement: priceImprovement,
        fillPrices: fillPrices,
        fillRatio: fillRatio,
        fillEvents: fillEvents,
        slippage: slippage,
        // Bracket order information
        stopLossOrderId: stopLossOrderId,
        takeProfitOrderId: takeProfitOrderId,
        bracketOrders: bracketOrders,
        // Commission and fees
        commission: commission,
        fees: fees,
        totalCost: totalCost > 0 ? totalCost : null,
        // Timing metrics
        timingMetrics: timingMetrics,
        // Price comparison analysis
        priceComparison: null
    };
    
    // Add price comparison analysis
    if (requestedPrice && averageFillPrice) {
        feedbackResult.priceComparison = {
            requested: requestedPrice,
            filled: averageFillPrice,
            difference: averageFillPrice - requestedPrice,
            percentDifference: ((averageFillPrice - requestedPrice) / requestedPrice * 100).toFixed(3),
            improvement: priceImprovement,
            analysis: priceImprovement > 0 ? 'BETTER_THAN_REQUESTED' : 
                     priceImprovement < 0 ? 'WORSE_THAN_REQUESTED' : 
                     'FILLED_AT_REQUESTED'
        };
        
        console.log(`📊 PRICE COMPARISON - Requested: ${requestedPrice}, Filled: ${averageFillPrice}`);
        console.log(`📊 PRICE COMPARISON - Difference: ${feedbackResult.priceComparison.difference} (${feedbackResult.priceComparison.percentDifference}%)`);
        console.log(`📊 PRICE COMPARISON - Analysis: ${feedbackResult.priceComparison.analysis}`);
    }
    
    if (rejectionText.includes('Rejected')) {
        console.log('❌ ORDER REJECTED - checking rejection reason...');
        if (rejectionText.includes('outside of market hours')) {
            console.log('❌ REJECTION REASON: Order placed outside market hours');
            feedbackResult.rejectionReason = 'Order placed outside market hours';
        } else if (rejectionText.includes('Risk')) {
            console.log('❌ REJECTION REASON: Risk management violation');
            feedbackResult.rejectionReason = 'Risk management violation';
        } else {
            console.log('❌ REJECTION REASON: Other - check full feedback above');
            feedbackResult.rejectionReason = 'Order rejected';
        }
    } else if (rejectionText.includes('Risk Passed')) {
        console.log('✅ RISK MANAGEMENT: Order passed risk checks');
        feedbackResult.success = true;
    } else if (orderEvents.length > 0) {
        // If we have order events and no rejection, consider it successful
        feedbackResult.success = true;
    }
    
    // Generate comprehensive order verification report
    const generateOrderReport = () => {
        let report = '\n📊 ════════════════ ORDER VERIFICATION REPORT ════════════════\n';
        
        // Order Header
        report += `\n🔸 ORDER DETAILS:\n`;
        report += `   Order ID: ${feedbackResult.orderId || 'N/A'}\n`;
        report += `   Type: ${feedbackResult.orderType}\n`;
        report += `   Action: ${feedbackResult.orderAction} ${feedbackResult.orderQuantity || 'N/A'} units\n`;
        report += `   Status: ${feedbackResult.success ? '✅ SUCCESS' : '❌ FAILED'}\n`;
        
        // Price Analysis
        if (feedbackResult.orderType === 'LIMIT' && feedbackResult.priceComparison) {
            report += `\n🔸 PRICE VERIFICATION:\n`;
            report += `   Requested: ${feedbackResult.requestedPrice}\n`;
            report += `   Filled: ${feedbackResult.averageFillPrice}\n`;
            report += `   Difference: ${feedbackResult.priceComparison.difference} (${feedbackResult.priceComparison.percentDifference}%)\n`;
            report += `   Result: ${feedbackResult.priceComparison.analysis}\n`;
        }
        
        // Market Order Slippage
        if (feedbackResult.orderType === 'MARKET' && feedbackResult.slippage) {
            report += `\n🔸 MARKET ORDER SLIPPAGE:\n`;
            if (feedbackResult.slippage.priceRange !== undefined) {
                report += `   Fill Range: ${feedbackResult.slippage.priceRange} (${feedbackResult.slippage.priceRangeTicks} ticks)\n`;
                report += `   Min Fill: ${feedbackResult.slippage.minFillPrice}\n`;
                report += `   Max Fill: ${feedbackResult.slippage.maxFillPrice}\n`;
            }
        }
        
        // Fill Information
        if (feedbackResult.fillRatio) {
            report += `\n🔸 FILL INFORMATION:\n`;
            report += `   Fill Ratio: ${feedbackResult.fillRatio.filled}/${feedbackResult.fillRatio.total} (${feedbackResult.fillRatio.percentFilled}%)\n`;
            report += `   Status: ${feedbackResult.fillRatio.isPartial ? '⚠️ PARTIAL FILL' : '✅ COMPLETE FILL'}\n`;
            if (feedbackResult.fillEvents.length > 0) {
                report += `   Individual Fills:\n`;
                feedbackResult.fillEvents.forEach((fill, idx) => {
                    report += `     ${idx + 1}. ${fill.quantity || 'N/A'} @ ${fill.price} (${fill.timestamp})\n`;
                });
            }
        }
        
        // Bracket Orders
        if (feedbackResult.bracketOrders.length > 0) {
            report += `\n🔸 BRACKET ORDERS:\n`;
            if (feedbackResult.stopLossOrderId) {
                report += `   Stop Loss: #${feedbackResult.stopLossOrderId}\n`;
            }
            if (feedbackResult.takeProfitOrderId) {
                report += `   Take Profit: #${feedbackResult.takeProfitOrderId}\n`;
            }
        }
        
        // Timing Analysis
        if (feedbackResult.timingMetrics.timeToFill) {
            report += `\n🔸 EXECUTION TIMING:\n`;
            report += `   Time to Fill: ${feedbackResult.timingMetrics.timeToFill}ms\n`;
            if (feedbackResult.timingMetrics.riskCheckTime) {
                report += `   Risk Check: ${feedbackResult.timingMetrics.riskCheckTime}ms\n`;
            }
            report += `   Total Duration: ${feedbackResult.timingMetrics.totalDuration || 'N/A'}ms\n`;
        }
        
        // Costs
        if (feedbackResult.commission || feedbackResult.totalCost) {
            report += `\n🔸 COSTS:\n`;
            if (feedbackResult.commission) {
                report += `   Commission: $${feedbackResult.commission}\n`;
            }
            if (feedbackResult.fees.length > 0) {
                report += `   Fees: ${feedbackResult.fees.length} fee(s) totaling $${feedbackResult.fees.reduce((sum, f) => sum + f.amount, 0)}\n`;
            }
            if (feedbackResult.totalCost) {
                report += `   Total Cost: $${feedbackResult.totalCost}\n`;
            }
        }
        
        // Rejection Reason
        if (feedbackResult.rejectionReason) {
            report += `\n🔸 REJECTION DETAILS:\n`;
            report += `   Reason: ${feedbackResult.rejectionReason}\n`;
        }
        
        report += '\n══════════════════════════════════════════════════════════\n';
        return report;
    };
    
    // Generate and log the comprehensive report
    const orderReport = generateOrderReport();
    console.log(orderReport);
    
    // Add the report to the feedback result
    feedbackResult.verificationReport = orderReport;
    
    // Store last result for testing/debugging
    captureOrderFeedback.lastResult = feedbackResult;
    window.lastOrderFeedback = feedbackResult; // Also make available globally
    
    console.log('🔄 ORDER FEEDBACK CAPTURE COMPLETE');
    console.log('💡 TIP: Access last feedback with: window.lastOrderFeedback');
    return feedbackResult;
}


// Futures tick data dictionary with default SL/TP settings for each instrument
const futuresTickData = {
  // Symbol: { tickSize, tickValue, defaultSL (ticks), defaultTP (ticks), precision (decimal places) }
  MNQ: { tickSize: 0.25, tickValue: 0.5,  defaultSL: 15,  defaultTP: 200, precision: 2 },  // Micro E-mini Nasdaq-100
  NQ:  { tickSize: 0.25, tickValue: 5.0,  defaultSL: 15,  defaultTP: 200, precision: 2 },  // E-mini Nasdaq-100
  ES:  { tickSize: 0.25, tickValue: 12.5, defaultSL: 40,  defaultTP: 100, precision: 2 },  // E-mini S&P 500
  RTY: { tickSize: 0.1,  tickValue: 5.0,  defaultSL: 90,  defaultTP: 225, precision: 1 },  // E-mini Russell 2000
  YM:  { tickSize: 1.0,  tickValue: 5.0,  defaultSL: 10,  defaultTP: 25,  precision: 0 },  // E-mini Dow Jones
  CL:  { tickSize: 0.01, tickValue: 10.0, defaultSL: 50,  defaultTP: 100, precision: 2 },  // Crude Oil
  GC:  { tickSize: 0.1,  tickValue: 10.0, defaultSL: 15,  defaultTP: 30,  precision: 1 },  // Gold (15 ticks = $150 risk)
  MGC: { tickSize: 0.1,  tickValue: 1.0,  defaultSL: 15,  defaultTP: 30,  precision: 1 }   // Micro Gold
};

function autoTrade(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = null, stopLossTicks = null, _tickSize = 0.25, explicitOrderType = null) {
    console.log(`🚀 [AUTOTRADE START] autoTrade called with: symbol=${inputSymbol}, qty=${quantity}, action=${action}, TP=${takeProfitTicks}, SL=${stopLossTicks}, tickSize=${_tickSize}, orderType=${explicitOrderType}`);
    console.log(`🚀 [AUTOTRADE START] Function entry successful at ${new Date().toISOString()}`);
    
    try {
        // DEBUG: Verify TP ticks input
        console.log(`🔍 [DEBUG] TP ticks input parameter = ${takeProfitTicks} (type: ${typeof takeProfitTicks})`);

        const symbolInput = currentState.symbol || 'NQ';
        console.log(`🔍 [SYMBOL] Using symbol: ${symbolInput}`);
        console.log(`🔍 [SYMBOL] currentState.symbol = ${currentState.symbol}`);

        // Get root symbol (e.g., 'NQH5' -> 'NQ')
        const rootSymbol = symbolInput.replace(/[A-Z]\d+$/, '');
        console.log(`🔍 [SYMBOL] Root symbol: ${rootSymbol}`);

        // Get tick size and default values from dictionary or fallback
        console.log(`🔍 [DATA] Looking up symbolData for ${rootSymbol}...`);
        const symbolData = futuresTickData[rootSymbol];
        console.log(`🔍 [DATA] symbolData found:`, symbolData);

    // Keep track of the last symbol to handle symbol changes
    if (rootSymbol !== autoTrade.lastRootSymbol) {
       currentState.tickSize = symbolData?.tickSize ?? '';
       const tickInput = document.getElementById('tickInput');
       if (tickInput) tickInput.value = currentState.tickSize;
    }
    autoTrade.lastRootSymbol = rootSymbol;
    const tickSize = (symbolData && typeof symbolData.tickSize === 'number')
           ? symbolData.tickSize
           : parseFloat(currentState.tickSize) || _tickSize;

    // right after tickSize is determined
    currentState.tickSize = tickSize;
    const tickInput = document.getElementById('tickInput');
    if (tickInput) tickInput.value = tickSize;           // shows the real value
    // localStorage removed - tick size is always determined from symbol data

    // Use provided values or defaults from dictionary or UI
    const actualStopLossTicks = stopLossTicks ||
                               symbolData?.defaultSL ||
                               parseInt(currentState.sl) ||
                               40;

    const actualTakeProfitTicks = takeProfitTicks ||
                                 symbolData?.defaultTP ||
                                 parseInt(currentState.tp) ||
                                 100;

    const enableSL = actualStopLossTicks > 0;
    const enableTP = actualTakeProfitTicks > 0;
    
    // DEBUG: Verify TP ticks after processing
    console.log(`🔍 DEBUG: actualTakeProfitTicks = ${actualTakeProfitTicks} (from takeProfitTicks: ${takeProfitTicks}, defaultTP: ${symbolData?.defaultTP}, tpInput: ${currentState.tp})`);

    const from = symbolData?.tickSize ? 'dictionary'
      : currentState.tickSize ? 'input field'
      : 'default parameter';
    console.log(`Using tick size ${tickSize} (from ${from})`);
    console.log(`Using SL: ${actualStopLossTicks} ticks, TP: ${actualTakeProfitTicks} ticks`);
    
    // DEBUG: Verify tick size values
        console.log(`🔍 [DEBUG] tickSize = ${tickSize} (symbolData.tickSize: ${symbolData?.tickSize}, tickInput: ${currentState.tickSize}, _tickSize param: ${_tickSize})`);

        console.log(`📡 [MARKET DATA] Getting market data for ${symbolInput}...`);
        console.log(`📡 [MARKET DATA] About to call getMarketData(${symbolInput})`);
        const marketData = getMarketData(symbolInput);
        console.log(`📡 [MARKET DATA] getMarketData returned:`, marketData);
        
        if (!marketData) {
            console.error(`❌ [MARKET DATA] No market data for ${symbolInput} - EARLY RETURN!`);
            return;
        }
        console.log(`📡 [MARKET DATA] Market data received:`, marketData);

        console.log(`💰 [ORDER PREP] Starting order preparation...`);
        
        // Check if an entry price was provided
        const entryPriceInput = document.getElementById('entryPriceInput');
        const customEntryPrice = entryPriceInput && entryPriceInput.value ? parseFloat(entryPriceInput.value) : null;
        console.log(`💰 [ORDER PREP] Custom entry price: ${customEntryPrice}`);
        
        // Determine market price (used when no entry price is specified or for SL/TP calculations)
        const marketPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
        console.log(`💰 [ORDER PREP] Market price: ${marketPrice} (${action === 'Buy' ? 'offer' : 'bid'} price)`);
        
        // Determine entry order type and price
        let orderType = 'MARKET';
        let entryPrice = marketPrice;
        console.log(`💰 [ORDER PREP] Initial order type: ${orderType}, entry price: ${entryPrice}`);
    
    // Use explicit order type if provided, otherwise fall back to entry price logic
    if (explicitOrderType) {
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
        } else if (orderType === 'MARKET') {
            // For MARKET orders, always use the current market price
            entryPrice = marketPrice;
            console.log(`Using market price: ${entryPrice} for MARKET order`);
        }
    } else if (customEntryPrice !== null) {
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
        // DEBUG: Show calculation components before computing
        const tpOffset = actualTakeProfitTicks * tickSize;
        console.log(`🔍 DEBUG: TP calculation - entryPrice: ${entryPrice}, actualTakeProfitTicks: ${actualTakeProfitTicks}, tickSize: ${tickSize}, offset: ${tpOffset}`);
        
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
        entryPrice: orderType !== 'MARKET' ? entryPrice.toFixed(decimalPrecision) : null,
        enableTP: enableTP,
        enableSL: enableSL
    };
    console.log('Trade data prepared:', tradeData);
    
    // DEBUG: Verify TP in trade data object and validate against expected calculation
    const expectedTPPrice = (action === 'Buy' 
        ? entryPrice + actualTakeProfitTicks * tickSize 
        : entryPrice - actualTakeProfitTicks * tickSize).toFixed(decimalPrecision);
    
    console.log(`🔍 DEBUG: tradeData.takeProfit = ${tradeData.takeProfit} (should be TP price for ${actualTakeProfitTicks} ticks)`);
    console.log(`✅ TP VALIDATION: Expected=${expectedTPPrice}, Actual=${tradeData.takeProfit}, Match=${expectedTPPrice === tradeData.takeProfit ? '✅' : '❌'}`);
    
    if (expectedTPPrice !== tradeData.takeProfit) {
        console.error(`🚨 TP MISMATCH: Expected ${expectedTPPrice} but got ${tradeData.takeProfit} - this indicates a calculation error!`);
        }

        console.log(`🚀 [ORDER EXECUTION] About to submit bracket orders with tradeData:`, tradeData);
        console.log(`🚀 [ORDER EXECUTION] Calling createBracketOrdersManual...`);
        
        return createBracketOrdersManual(tradeData)
            .then(result => {
                console.log(`✅ [ORDER EXECUTION] createBracketOrdersManual SUCCESS:`, result);
                return result;
            })
            .catch(error => {
                console.error(`❌ [ORDER EXECUTION] createBracketOrdersManual ERROR:`, error);
                throw error;
            })
            .finally(() => {
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
    } catch (error) {
        console.error(`💥 [AUTOTRADE ERROR] Critical error in autoTrade function:`, error);
        console.error(`💥 [AUTOTRADE ERROR] Stack trace:`, error.stack);
        console.error(`💥 [AUTOTRADE ERROR] Function parameters:`, {
            inputSymbol, quantity, action, takeProfitTicks, stopLossTicks, _tickSize, explicitOrderType
        });
        throw error;
    }
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



const driverInit = {
    initialized: false,
    options: {},
};

let uiAdapter = null;

function bootstrap(options = {}) {
    driverInit.initialized = true;
    driverInit.options = { ...options };
    if (options.panel) {
        registerUIPanel(options.panel);
    }
}

function registerUIPanel(adapter) {
    uiAdapter = adapter;
}

function createInvisibleUI() {
    if (uiAdapter?.mount) {
        return uiAdapter.mount({ visible: false });
    }
    if (uiAdapter?.createUI) {
        return uiAdapter.createUI(false);
    }
    console.warn('[TradoAuto] No UI adapter registered; skipping invisible UI creation');
    return null;
}


const driverSingleton = {
    state: currentState,
    futuresTickData,
    delay,
    normalizeSymbol,
    updateSymbol,
    updatePrice,
    clickExitForSymbol,
    moveStopLossToBreakeven,
    getCurrentPosition,
    captureOrderFeedback,
    getOrderEvents,
    createBracketOrdersManual,
    autoTrade,
    getFrontQuarter,
    getMarketData,
    getMonthlyCode,
    getQuarterlyCode,
    init: bootstrap,
    registerUIPanel,
    createInvisibleUI,
    getInitStatus: () => ({ ...driverInit }),
};

export function createAutoDriver(options = {}) {
    bootstrap(options);
    return driverSingleton;
}

const driver = createAutoDriver();

if (typeof window !== 'undefined') {
    window.TradoAuto = driver;
}

export default driver;
export { registerUIPanel, createInvisibleUI, bootstrap as initDriver };
