async function createBracketOrdersManual(tradeData) {

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async function updateInputValue(selector, value) {
        const input = document.querySelector(selector);
        if (input) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(input, value);
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.blur();
            input.focus();
            input.click();
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        const arrowDown = document.querySelector('.numeric-input.feedback-wrapper .numeric-input-arrow.numeric-input-decrement');
        if (arrowDown) arrowDown.click();
    }

    function initValueTrackers() {
        const selectors = [
            '.search-box--input',
            '.select-input.combobox input',
            '.numeric-input.feedback-wrapper input'
        ];
        selectors.forEach(selector => {
            const input = document.querySelector(selector);
            if (input && input._valueTracker) {
                input._valueTracker.setValue(input.value);
            }
        });
    }

    async function setCommonFields() {
        if (tradeData.symbol) await updateInputValue('.search-box--input', tradeData.symbol);
        if (tradeData.action) {
            const actionGroup = document.querySelectorAll('.radio-group.btn-group')[0];
            if (actionGroup) {
                const options = actionGroup.querySelectorAll('label');
                for (let opt of options) {
                    if (opt.textContent.trim() === tradeData.action) {
                        opt.click();
                        break;
                    }
                }
            }
        }
        if (tradeData.qty) await updateInputValue('.select-input.combobox input', tradeData.qty);
    }

    async function submitOrder(orderType, priceValue) {
    
        await setCommonFields();

        const orderTypeContainer = document.querySelector('.group.order-type .select-input');
        if (orderTypeContainer) {
            const dropdownToggle = orderTypeContainer.querySelector('div[tabindex]');
            if (dropdownToggle) {
                dropdownToggle.click();
                const listItems = orderTypeContainer.querySelectorAll('ul.dropdown-menu li');
                for (let item of listItems) {
                    if (item.textContent.trim() === orderType) {
                        item.click();
                        break;
                    }
                }
            }
        }

        if (priceValue) await updateInputValue('.numeric-input.feedback-wrapper input', priceValue);


        const sendButton = document.querySelector('.btn-group .btn-primary');
        if (sendButton) sendButton.click();
        await delay(200);

        const backIcon = document.querySelector('.icon.icon-back');
        if (backIcon) backIcon.click();
        await delay(200);
    }

    // Execute the entry order as a market order.
    await submitOrder("MARKET", null);

    // Exit orders: reverse the action based on the original order.
    if (tradeData.action === "Buy") {
        tradeData.action = "Sell";
        // For a Buy, TP is a sell LIMIT order above entry and SL is a sell STOP order below entry.
        await submitOrder("LIMIT", tradeData.takeProfit);
        await submitOrder("STOP", tradeData.stopLoss);
    } else if (tradeData.action === "Sell") {
        tradeData.action = "Buy";
        // For a Sell, TP is a buy LIMIT order below entry and SL is a buy STOP order above entry.
        await submitOrder("LIMIT", tradeData.takeProfit);
        await submitOrder("STOP", tradeData.stopLoss);
    }
}


let tradeData = {
  symbol: 'NQM5',       // Trading symbol
  qty: '9',             // Quantity to trade
  action: 'Buy',        // Order direction: 'Buy' or 'Sell'
  takeProfit: '20000',// Price for the Take Profit limit order
  stopLoss: '17000'  // Price for the Stop Loss limit order
};


createBracketOrdersManual(tradeData)