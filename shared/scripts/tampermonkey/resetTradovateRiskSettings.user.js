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

  // ============================================================================
// DOM VALIDATION HELPER FUNCTIONS - Load unified library
// ============================================================================

async function loadDOMHelpers() {
    if (window.domHelpers) {
        console.log('✅ DOM Helpers already loaded globally');
        return true;
    }
    
    try {
        const script = document.createElement('script');
        script.src = '/scripts/tampermonkey/domHelpers.js';
        document.head.appendChild(script);
        
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            setTimeout(() => reject(new Error('Timeout loading domHelpers')), 5000);
        });
        
        if (window.domHelpers) {
            console.log('✅ DOM Helpers loaded successfully from external file');
            return true;
        }
    } catch (error) {
        console.warn('⚠️ Could not load external domHelpers.js, using inline fallback');
    }
    
    // Inline fallback for critical functions
    window.domHelpers = {
        waitForElement: async (selector, timeout = 10000) => {
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
        },
        validateElementExists: (selector) => !!document.querySelector(selector),
        validateElementVisible: (element) => {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return style.display !== 'none' && style.visibility !== 'hidden' && 
                   element.offsetWidth > 0 && element.offsetHeight > 0;
        },
        safeClick: async (element) => {
            if (!element) return false;
            try {
                element.click();
                return true;
            } catch (error) {
                console.error('Error clicking element:', error);
                return false;
            }
        },
        safeSetValue: async (element, value) => {
            if (!element) return false;
            try {
                element.focus();
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(element, value);
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            } catch (error) {
                console.error('Error setting value:', error);
                return false;
            }
        }
    };
    
    console.log('✅ DOM Helpers initialized with inline fallback');
    return true;
}

// Load DOM helpers on startup
loadDOMHelpers();

// Legacy compatibility wrapper
const waitForElement = (selector, timeout = 10000) => {
    return window.domHelpers.waitForElement(selector, timeout);
};

  const clickSave = async () => {
    console.log('🔍 DOM Intelligence: Starting Save button click with validation');
    
    // Pre-validation: Find Save button
    const saveBtn = Array.from(document.querySelectorAll('button'))
      .find(btn => {
        const span = btn.querySelector('span.MuiButton-label');
        return span && span.textContent.trim() === "Save";
      });
    
    if (!saveBtn) {
      console.error('❌ Pre-validation failed: Save button not found');
      return false;
    }
    
    // Pre-validation: Check if button is visible and enabled
    if (!window.domHelpers.validateElementVisible(saveBtn)) {
      console.error('❌ Pre-validation failed: Save button not visible');
      return false;
    }
    
    if (saveBtn.disabled) {
      console.error('❌ Pre-validation failed: Save button is disabled');
      return false;
    }
    
    console.log('✅ Pre-validation passed: Save button found, visible, and enabled');
    
    // Click the button
    const clickSuccess = await window.domHelpers.safeClick(saveBtn);
    if (clickSuccess) {
      console.log('✅ Save button clicked successfully');
      return true;
    } else {
      console.error('❌ Failed to click Save button');
      return false;
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

  const setValue = async (val) => {
    console.log(`🔍 DOM Intelligence: Setting value to ${val} with validation`);
    
    // Pre-validation: Find input field
    const inputSelector = '#trailingMaxDrawdownRealTime';
    if (!window.domHelpers.validateElementExists(inputSelector)) {
      console.error('❌ Pre-validation failed: Value input not found');
      return false;
    }
    
    const input = document.getElementById('trailingMaxDrawdownRealTime');
    
    // Pre-validation: Check if input is visible and enabled
    if (!window.domHelpers.validateElementVisible(input)) {
      console.error('❌ Pre-validation failed: Value input not visible');
      return false;
    }
    
    if (input.disabled) {
      console.error('❌ Pre-validation failed: Value input is disabled');
      return false;
    }
    
    console.log('✅ Pre-validation passed: Value input found, visible, and enabled');
    
    // Set the value using safe method
    const setSuccess = await window.domHelpers.safeSetValue(input, val);
    
    if (setSuccess) {
      console.log(`✅ Value set successfully to $${val}`);
      return true;
    } else {
      console.error(`❌ Failed to set value to $${val}`);
      return false;
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
