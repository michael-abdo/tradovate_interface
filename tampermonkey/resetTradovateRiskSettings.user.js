// ==UserScript==
// @name         Reset Tradovate Risk Settings
// @namespace    http://tampermonkey.net/
// @version      1.4
// @description  Automates toggling Real-Time Trailing Max Drawdown in Tradovate with account selection
// @match        https://trader.tradovate.com/*
// @grant        none
// ==/UserScript==

const accountIds = ['account-20653801', 'account-20658313', 'account-20658317'];
let ACCOUNT_ID = null;

(function () {
  'use strict';

  const waitForElement = (selector, timeout = 10000) => {
    return new Promise((resolve, reject) => {
      const interval = 100;
      let elapsed = 0;
      const check = () => {
        const el = document.querySelector(selector);
        if (el) return resolve(el);
        elapsed += interval;
        if (elapsed >= timeout) return reject('Element not found: ' + selector);
        setTimeout(check, interval);
      };
      check();
    });
  };

  const clickSave = () => {
    const saveBtn = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const span = btn.querySelector('span.MuiButton-label');
        return span && span.textContent.trim() === "Save";
      });
    if (saveBtn) {
      saveBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      console.log('Clicked Save button.');
    } else {
      console.error('Save button not found.');
    }
  };

  const openRiskSettings = () => {
    const account = document.getElementById(ACCOUNT_ID);
    if (!account) return Promise.reject('Account container not found.');
    const riskBtn = Array.from(account.querySelectorAll('button'))
      .find(btn => btn.textContent.trim() === "Risk Settings");
    if (!riskBtn) return Promise.reject('Risk Settings button not found.');
    riskBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    console.log('Clicked Risk Settings button.');
    return Promise.resolve();
  };

  const getRTToggle = () => {
    const labels = Array.from(document.querySelectorAll('label.MuiFormControlLabel-root'));
    return labels.find(label =>
      label.textContent.includes("Real-Time Trailing Max Drawdown")
    )?.querySelector('input[type="checkbox"]');
  };

  const toggleSwitch = (desiredState) => {
    const toggle = getRTToggle();
    if (!toggle) throw new Error('RT Trailing Max Drawdown toggle not found.');
    const isChecked = toggle.checked;
    if (isChecked !== desiredState) {
      toggle.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      console.log(`Toggled to ${desiredState ? 'ON' : 'OFF'}.`);
    } else {
      console.log(`Already ${desiredState ? 'ON' : 'OFF'}.`);
    }
  };

  const setValue = (val) => {
    const input = document.getElementById('trailingMaxDrawdownRealTime');
    if (input) {
      input.focus();
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputValueSetter.call(input, val);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('Value set to $' + val);
    } else {
      console.error('Value input not found.');
    }
  };

    function adjustBalance() {
        console.log('adjustBalance() called');
        const waitForModifyBtn = new Promise((resolve, reject) => {
            const start = Date.now();
            const poll = setInterval(() => {
                const btn = Array.from(document.querySelectorAll('button'))
                .find(b => b.textContent.trim() === 'Modify Balance');
                if (btn) {
                    clearInterval(poll);
                    resolve(btn);
                } else if (Date.now() - start > 10000) {
                    clearInterval(poll);
                    reject('Modify Balance button not found');
                }
            }, 100);
        });

        return waitForModifyBtn
            .then(btn => {
            btn.click();
            return waitForElement('#amount-input', 10000);
        })
            .then(() => {
            const balanceEls = document.querySelectorAll('.MuiDialogContent-root p strong');
            if (balanceEls.length < 2) throw new Error('Current balance element not found');
            const currentBalance = parseFloat(balanceEls[1].textContent.trim());
            const diff = Math.min(50000 - currentBalance, 50000);

            const input = document.getElementById('amount-input');
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            setter.call(input, diff.toFixed(2));
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));

            const submitBtn = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent.includes('Submit'));
            if (!submitBtn) throw new Error('Submit button not found');
            submitBtn.click();
        });
    }


    // helper
    let loopId = null;
    function stopLoop() {
        if (loopId !== null) {
            clearTimeout(loopId);
            loopId = null;
        }
    }

    // start-loop (re-entrant safe)
    const start = () => {
        openRiskSettings()
            .then(() => waitForElement('label.MuiFormControlLabel-root'))
            .then(() => toggleSwitch(false))
            .then(() => new Promise(r => setTimeout(r, 1000)))
            .then(clickSave)
            .then(() => new Promise(r => setTimeout(r, 3000)))
            .then(openRiskSettings)
            .then(() => waitForElement('label.MuiFormControlLabel-root'))
            .then(() => toggleSwitch(true))
            .then(() => waitForElement('#trailingMaxDrawdownRealTime'))
            .then(() => setValue(7000))
            .then(() => new Promise(r => setTimeout(r, 1000)))
//            .then(adjustBalance())
            .then(clickSave)
            .then(() => {
            const closeBtn = document.querySelector('button[aria-label="close"]');
            if (closeBtn) closeBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loopId = setTimeout(start, 3000); // remember id
        })
            .catch(err => {
            console.error(err);
            loopId = setTimeout(start, 3000); // remember id
        });
    };

  const dropdown = document.createElement('select');
  accountIds.forEach(id => {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = id;
    dropdown.appendChild(option);
  });

  const btn = document.createElement('button');
  btn.textContent = 'Start Reset';
  Object.assign(btn.style, {
    background: 'green',
    color: '#fff',
    padding: '10px',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    position: 'fixed',
    top: '20px',
    right: '20px',
    zIndex: '999'
  });

  Object.assign(dropdown.style, {
    position: 'fixed',
    top: '20px',
    right: '150px',
    zIndex: '999',
    padding: '8px',
    fontSize: '14px'
  });

  document.body.appendChild(dropdown);
  document.body.appendChild(btn);

    // listeners
    btn.addEventListener('click', () => {
        stopLoop();                      // kill any old loop
        ACCOUNT_ID = dropdown.value;
        const gear = document.querySelector('.icon.icon-settings');
        if (!gear) return console.error('RiskStarter: settings icon not found');
        gear.click();
        btn.disabled = true;
        setTimeout(start, 10000);
    });

    dropdown.addEventListener('change', () => {
        btn.disabled = false;            // re-enable when a new acct picked
    });

})();
