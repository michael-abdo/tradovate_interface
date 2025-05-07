async function updateTradeAndExecute(tradeData) {
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async function updateInputValue(selector, value) {
        var input = document.querySelector(selector);
        if (input) {
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(input, value);
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            await delay(100);
        }
    }

    // Update main entry fields
    if (tradeData.symbol) await updateInputValue('.search-box--input', tradeData.symbol);
    if (tradeData.qty) await updateInputValue('.select-input.combobox input', tradeData.qty);
    if (tradeData.price) await updateInputValue('.numeric-input.feedback-wrapper input', tradeData.price);

    if (tradeData.orderType) {
        var orderTypeContainer = document.querySelector('.group.order-type .select-input');
        if (orderTypeContainer) {
            var dropdownToggle = orderTypeContainer.querySelector('div[tabindex]');
            if (dropdownToggle) {
                dropdownToggle.click();
                var listItems = orderTypeContainer.querySelectorAll('ul.dropdown-menu li');
                for (var i = 0; i < listItems.length; i++) {
                    if (listItems[i].textContent.trim() === tradeData.orderType) {
                        listItems[i].click();
                        break;
                    }
                }
            }
        }
    }
    if (tradeData.flags) {
        var flagButtons = document.querySelectorAll('.radio-group.btn-group label');
        for (var i = 0; i < flagButtons.length; i++) {
            if (tradeData.flags.indexOf(flagButtons[i].textContent.trim()) !== -1) {
                flagButtons[i].click();
            }
        }
    }
    if (tradeData.release) {
        var releaseButtons = document.querySelectorAll('.radio-group.btn-group label');
        for (var i = 0; i < releaseButtons.length; i++) {
            if (tradeData.release === releaseButtons[i].textContent.trim()) {
                releaseButtons[i].click();
            }
        }
    }
    if (tradeData.action) {
        var actionButtons = document.querySelectorAll('.radio-group.btn-group label');
        for (var i = 0; i < actionButtons.length; i++) {
            if (tradeData.action === actionButtons[i].textContent.trim()) {
                actionButtons[i].click();
                break;
            }
        }
    }

    // --- Update dependant entry for ATM values ---
    if (tradeData.atmType) {
        var atmDropdown = document.querySelector('.trading-ticket-dependant-entry .atm-dropdown');
        if (atmDropdown) {
            var dropdownToggle = atmDropdown.querySelector('div[tabindex]');
            if (dropdownToggle) {
                dropdownToggle.click();
                var options = atmDropdown.querySelectorAll('ul.dropdown-menu li');
                for (var i = 0; i < options.length; i++) {
                    if (options[i].textContent.trim() === tradeData.atmType) {
                        options[i].click();
                        break;
                    }
                }
                await delay(100);
            }
        }
    }
    if (tradeData.showIn) {
        var showInContainers = document.querySelectorAll('.trading-ticket-dependant-entry .gm-scroll-view .select-input:not(.atm-dropdown)');
        if (showInContainers.length > 0) {
            var showInContainer = showInContainers[0];
            var dropdownToggle = showInContainer.querySelector('div[tabindex]');
            if (dropdownToggle) {
                dropdownToggle.click();
                var options = showInContainer.querySelectorAll('ul.dropdown-menu li');
                for (var i = 0; i < options.length; i++) {
                    if (options[i].textContent.trim() === tradeData.showIn) {
                        options[i].click();
                        break;
                    }
                }
                await delay(100);
            }
        }
    }
    // --- Update only TP and ST numeric inputs ---
    // These are the numeric-input elements without the "feedback-wrapper" class.
    let tpInputs = document.querySelectorAll('.numeric-input:not(.feedback-wrapper) input');
    if (tradeData.takeProfit && tpInputs[0]) {
         var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
         nativeInputValueSetter.call(tpInputs[0], tradeData.takeProfit);
         tpInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
         tpInputs[0].dispatchEvent(new Event('change', { bubbles: true }));
         tpInputs[0].dispatchEvent(new Event('blur', { bubbles: true }));
         await delay(100);
    }
    if (tradeData.stopLoss && tpInputs[1]) {
         var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
         nativeInputValueSetter.call(tpInputs[1], tradeData.stopLoss);
         tpInputs[1].dispatchEvent(new Event('input', { bubbles: true }));
         tpInputs[1].dispatchEvent(new Event('change', { bubbles: true }));
         await delay(100);
    }
    // (Removal of any updates for stopLossType/stopLossLimit ensures only TP and ST are affected.)

    if (tradeData.trailStop) {
        var depSelects = document.querySelectorAll('.trading-ticket-dependant-entry .select-input');
        for (var i = 0; i < depSelects.length; i++) {
            var span = depSelects[i].querySelector('span.form-control');
            if (span && span.textContent.trim() === 'Trail.Stop') {
                var dropdownToggle = depSelects[i].querySelector('div[tabindex]');
                if (dropdownToggle) {
                    dropdownToggle.click();
                    var options = depSelects[i].querySelectorAll('ul.dropdown-menu li');
                    for (var j = 0; j < options.length; j++) {
                        if (options[j].textContent.trim() === tradeData.trailStop) {
                            options[j].click();
                            break;
                        }
                    }
                }
                break;
            }
        }
    }
    // -----------------------------------------------------------------

    var sendButton = document.querySelector('.btn-group .btn-primary');
    if (sendButton) {
        sendButton.click();
    }

    setTimeout(function() {
        var backIcon = document.querySelector('.icon.icon-back');
        if (backIcon) {
            backIcon.click();
        }
    }, 5000);
}






// Example usage with a tradeData JSON object
const tradeData = {
  symbol: 'NQM5',
  action: 'Buy',
  //orderType: 'MARKET',
  qty: '1',
  price: '19178.00',
  flags: ['GTC'],
  //release: 'Off',
  //atmType: 'Take Profit + Stop Loss',
  //showIn: 'Ticks',
  takeProfit: '5',
  stopLoss: '1',
  //stopLossType: 'Fixed',
  //stopLossLimit: '19069',
  //trailStop: 'Trail.Stop'
};

// Call the function to update the form and submit the trade
updateTradeAndExecute(tradeData);









function compareTradeDataValues(tradeData) {
    const results = {};
    let elem;

    // Main entry fields
    elem = document.querySelector('.search-box--input');
    results.symbol = {
        expected: tradeData.symbol,
        actual: elem ? elem.value.trim() : null,
        match: elem && elem.value.trim() === (tradeData.symbol || "").trim()
    };

    elem = document.querySelector('.select-input.combobox input');
    results.qty = {
        expected: tradeData.qty,
        actual: elem ? elem.value.trim() : null,
        match: elem && elem.value.trim() === (tradeData.qty || "").trim()
    };

    elem = document.querySelector('.numeric-input.feedback-wrapper input');
    results.price = {
        expected: tradeData.price,
        actual: elem ? elem.value.trim() : null,
        match: elem && elem.value.trim() === (tradeData.price || "").trim()
    };

    // Order type dropdown
    elem = document.querySelector('.group.order-type .select-input span.form-control');
    results.orderType = {
        expected: tradeData.orderType,
        actual: elem ? elem.textContent.trim() : null,
        match: elem && elem.textContent.trim() === (tradeData.orderType || "").trim()
    };

    // Flags (compare all active labels)
    const activeFlags = Array.from(document.querySelectorAll('.group .radio-group.btn-group label.active'))
                            .map(el => el.textContent.trim());
    results.flags = {
        expected: tradeData.flags,
        actual: activeFlags,
        match: JSON.stringify(activeFlags) === JSON.stringify(tradeData.flags || [])
    };

    // Release (assuming second radio group)
    const releaseGroup = document.querySelectorAll('.group .radio-group.btn-group')[1];
    elem = releaseGroup ? releaseGroup.querySelector('label.active') : null;
    results.release = {
        expected: tradeData.release,
        actual: elem ? elem.textContent.trim() : null,
        match: elem && elem.textContent.trim() === (tradeData.release || "").trim()
    };

    // Action (assuming first radio group)
    const actionGroup = document.querySelectorAll('.radio-group.btn-group')[0];
    elem = actionGroup ? actionGroup.querySelector('label.active') : null;
    results.action = {
        expected: tradeData.action,
        actual: elem ? elem.textContent.trim() : null,
        match: elem && elem.textContent.trim() === (tradeData.action || "").trim()
    };

    // Dependant entry: ATM type and Show In dropdown
    elem = document.querySelector('.trading-ticket-dependant-entry .atm-dropdown span.form-control');
    results.atmType = {
        expected: tradeData.atmType,
        actual: elem ? elem.textContent.trim() : null,
        match: elem && elem.textContent.trim() === (tradeData.atmType || "").trim()
    };

    elem = document.querySelector('.trading-ticket-dependant-entry .gm-scroll-view .select-input:not(.atm-dropdown) span.form-control');
    results.showIn = {
        expected: tradeData.showIn,
        actual: elem ? elem.textContent.trim() : null,
        match: elem && elem.textContent.trim() === (tradeData.showIn || "").trim()
    };

    // Dependant numeric inputs: [0] takeProfit, [1] stopLoss, [2] stopLossType, [3] stopLossLimit
    const depInputs = document.querySelectorAll('.trading-ticket-dependant-entry .gm-scroll-view .numeric-input input');
    results.takeProfit = {
        expected: tradeData.takeProfit,
        actual: depInputs[0] ? depInputs[0].value.trim() : null,
        match: depInputs[0] && depInputs[0].value.trim() === (tradeData.takeProfit || "").trim()
    };
    results.stopLoss = {
        expected: tradeData.stopLoss,
        actual: depInputs[1] ? depInputs[1].value.trim() : null,
        match: depInputs[1] && depInputs[1].value.trim() === (tradeData.stopLoss || "").trim()
    };
    results.stopLossType = {
        expected: tradeData.stopLossType,
        actual: depInputs[2] ? depInputs[2].value.trim() : null,
        match: depInputs[2] && depInputs[2].value.trim() === (tradeData.stopLossType || "").trim()
    };
    results.stopLossLimit = {
        expected: tradeData.stopLossLimit,
        actual: depInputs[3] ? depInputs[3].value.trim() : null,
        match: depInputs[3] && depInputs[3].value.trim() === (tradeData.stopLossLimit || "").trim()
    };

    // Trail Stop dropdown (search for matching value)
    let trailStopMatched = false;
    const depSelects = document.querySelectorAll('.trading-ticket-dependant-entry .select-input');
    for (let i = 0; i < depSelects.length; i++) {
        let span = depSelects[i].querySelector('span.form-control');
        if (span && span.textContent.trim() === (tradeData.trailStop || "").trim()) {
            trailStopMatched = true;
            break;
        }
    }
    results.trailStop = {
        expected: tradeData.trailStop,
        actual: trailStopMatched ? tradeData.trailStop : null,
        match: trailStopMatched
    };

    return results;
}

compareTradeDataValues(tradeData);