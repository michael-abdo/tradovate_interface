// ==UserScript==
// @name         Tradovate Auto Login
// @namespace    http://tampermonkey.net/
// @version      1.1.1
// @description  Adds a dropdown for auto login and waits for the "Access Simulation" button to click it automatically.
// @match        https://trader.tradovate.com/welcome*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // ============================================================================
    // DOM VALIDATION HELPER FUNCTIONS - Load or define inline
    // ============================================================================
    
    async function loadDOMHelpers() {
        if (window.domHelpers) {
            console.log('✅ DOM Helpers already loaded globally');
            return true;
        }
        
        try {
            // Try to load external domHelpers.js
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
        
        // Inline fallback DOM helpers
        window.domHelpers = {
            validateElementExists: function(selector) {
                const element = document.querySelector(selector);
                const exists = element !== null;
                if (exists) {
                    console.log(`✅ Element exists: ${selector}`);
                } else {
                    console.warn(`❌ Element not found: ${selector}`);
                }
                return exists;
            },
            
            validateElementVisible: function(element) {
                if (!element) {
                    console.warn(`❌ Cannot check visibility: element is null`);
                    return false;
                }
                const style = window.getComputedStyle(element);
                const isVisible = style.display !== 'none' && 
                                 style.visibility !== 'hidden' && 
                                 element.offsetWidth > 0 && 
                                 element.offsetHeight > 0;
                if (isVisible) {
                    console.log(`✅ Element is visible: ${element.tagName}${element.id ? '#' + element.id : ''}${element.className ? '.' + element.className : ''}`);
                } else {
                    console.warn(`❌ Element is not visible: ${element.tagName}${element.id ? '#' + element.id : ''}${element.className ? '.' + element.className : ''}`);
                }
                return isVisible;
            },
            
            validateFormFieldValue: function(element, expectedValue) {
                if (!element) {
                    console.warn(`❌ Cannot validate form field: element is null`);
                    return false;
                }
                const actualValue = element.value || element.textContent || '';
                const matches = actualValue.toString() === expectedValue.toString();
                if (matches) {
                    console.log(`✅ Form field value correct: "${actualValue}" matches "${expectedValue}"`);
                } else {
                    console.warn(`❌ Form field value mismatch: expected "${expectedValue}", got "${actualValue}"`);
                }
                return matches;
            },
            
            waitForElement: async function(selector, timeout = 10000) {
                const startTime = Date.now();
                return new Promise((resolve) => {
                    const checkElement = () => {
                        const element = document.querySelector(selector);
                        if (element) {
                            console.log(`✅ Element found: ${selector} (${Date.now() - startTime}ms)`);
                            resolve(element);
                            return;
                        }
                        if (Date.now() - startTime >= timeout) {
                            console.warn(`⏰ Timeout waiting for element: ${selector} (${timeout}ms)`);
                            resolve(null);
                            return;
                        }
                        setTimeout(checkElement, 100);
                    };
                    checkElement();
                });
            }
        };
        
        console.log('✅ DOM Helpers initialized with inline fallback');
        return true;
    }
    
    // Load DOM helpers on startup
    loadDOMHelpers();

    function login(username, password) {
        console.log('🔍 DOM Intelligence: Starting login with form validation');
        console.log(`🔍 Login credentials: username="${username}", password="${password ? '[REDACTED]' : 'empty'}"`);
        
        // STEP 1: Pre-validation - Check if login form fields exist
        console.log('🔍 Pre-validation: Checking for login form fields');
        
        const emailSelector = '#name-input';
        const passwordSelector = '#password-input';
        
        if (!window.domHelpers.validateElementExists(emailSelector)) {
            console.error('❌ Pre-validation failed: Email input field not found');
            return false;
        }
        
        if (!window.domHelpers.validateElementExists(passwordSelector)) {
            console.error('❌ Pre-validation failed: Password input field not found');
            return false;
        }
        
        const emailInput = document.getElementById("name-input");
        const passwordInput = document.getElementById("password-input");
        
        // STEP 2: Pre-validation - Check if form fields are visible and enabled
        if (!window.domHelpers.validateElementVisible(emailInput)) {
            console.error('❌ Pre-validation failed: Email input field not visible');
            return false;
        }
        
        if (!window.domHelpers.validateElementVisible(passwordInput)) {
            console.error('❌ Pre-validation failed: Password input field not visible');
            return false;
        }
        
        if (emailInput.disabled) {
            console.error('❌ Pre-validation failed: Email input field is disabled');
            return false;
        }
        
        if (passwordInput.disabled) {
            console.error('❌ Pre-validation failed: Password input field is disabled');
            return false;
        }
        
        console.log('✅ Pre-validation passed: Login form fields found, visible, and enabled');
        
        // STEP 3: Set form field values with validation
        try {
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            
            // Set email field
            console.log('🔍 Setting email field value');
            nativeSetter.call(emailInput, username);
            emailInput.dispatchEvent(new Event("input", { bubbles: true }));
            
            // Set password field  
            console.log('🔍 Setting password field value');
            nativeSetter.call(passwordInput, password);
            passwordInput.dispatchEvent(new Event("input", { bubbles: true }));
            
            // STEP 4: Post-validation - Verify values were set correctly
            setTimeout(() => {
                console.log('🔍 Post-validation: Verifying form field values');
                
                let validationErrors = 0;
                
                if (!window.domHelpers.validateFormFieldValue(emailInput, username)) {
                    console.error('❌ Post-validation failed: Email field value not set correctly');
                    validationErrors++;
                } else {
                    console.log('✅ Email field value set successfully');
                }
                
                if (!window.domHelpers.validateFormFieldValue(passwordInput, password)) {
                    console.error('❌ Post-validation failed: Password field value not set correctly');
                    validationErrors++;
                } else {
                    console.log('✅ Password field value set successfully');
                }
                
                if (validationErrors > 0) {
                    console.error(`❌ Form validation failed with ${validationErrors} errors`);
                    return;
                }
                
                console.log('✅ Post-validation passed: All form fields set correctly');
                
                // STEP 5: Pre-validation - Check for login button before clicking
                console.log('🔍 Pre-validation: Checking for login button');
                const loginButtonSelector = 'button.MuiButton-containedPrimary';
                
                if (!window.domHelpers.validateElementExists(loginButtonSelector)) {
                    console.error('❌ Pre-validation failed: Login button not found');
                    return;
                }
                
                const loginButton = document.querySelector(loginButtonSelector);
                if (!window.domHelpers.validateElementVisible(loginButton)) {
                    console.error('❌ Pre-validation failed: Login button not visible');
                    return;
                }
                
                if (loginButton.disabled) {
                    console.error('❌ Pre-validation failed: Login button is disabled');
                    return;
                }
                
                console.log('✅ Pre-validation passed: Login button found, visible, and enabled');
                
                // STEP 6: Click login button
                try {
                    loginButton.click();
                    console.log('✅ Login button clicked successfully');
                    console.log('🔍 DOM Intelligence: Login form submission completed');
                } catch (error) {
                    console.error('❌ Error clicking login button:', error.message);
                }
                
            }, 200);
            
        } catch (error) {
            console.error('❌ Error setting form field values:', error.message);
            return false;
        }
        
        return true;
    }

    // Credentials will be populated from environment variables by the Python script
    const credentials = {
        "YOUR_USERNAME": "YOUR_PASSWORD"
    };

    function createDropdown() {
        const container = document.createElement("div");
        container.style.position = "fixed";
        container.style.top = "10px";
        container.style.right = "10px";
        container.style.zIndex = 9999;
        container.style.backgroundColor = "white";
        container.style.padding = "5px";
        container.style.border = "1px solid #ccc";
        container.style.borderRadius = "4px";

        const select = document.createElement("select");
        const defaultOption = document.createElement("option");
        defaultOption.textContent = "Select account";
        defaultOption.value = "";
        select.appendChild(defaultOption);

        for (const user in credentials) {
            const option = document.createElement("option");
            option.value = user;
            option.textContent = user;
            select.appendChild(option);
        }

        select.addEventListener("change", function() {
            const selectedUser = this.value;
            if (selectedUser) {
                const selectedPassword = credentials[selectedUser];
                login(selectedUser, selectedPassword);
            }
        });

        container.appendChild(select);
        document.body.appendChild(container);
    }

    function waitForAccessSimulation() {
        console.log('🔍 DOM Intelligence: Starting waitForAccessSimulation with validation');
        
        let attemptCount = 0;
        const maxAttempts = 60; // 30 seconds total (500ms * 60)
        
        const interval = setInterval(() => {
            attemptCount++;
            console.log(`🔍 Attempt ${attemptCount}/${maxAttempts}: Checking for Access Simulation button`);
            
            // STEP 1: Pre-validation - Check if any buttons exist
            const buttonSelector = 'button.tm';
            if (!window.domHelpers.validateElementExists(buttonSelector)) {
                if (attemptCount % 10 === 0) { // Log every 5 seconds
                    console.log(`⚠️ No buttons found yet (attempt ${attemptCount}/${maxAttempts})`);
                }
                
                if (attemptCount >= maxAttempts) {
                    console.error('❌ Timeout: Access Simulation button not found after 30 seconds');
                    clearInterval(interval);
                }
                return;
            }
            
            const buttons = document.querySelectorAll(buttonSelector);
            console.log(`🔍 Found ${buttons.length} buttons with class 'tm'`);
            
            // STEP 2: Search for the Access Simulation button
            let targetButton = null;
            for (const btn of buttons) {
                const buttonText = btn.textContent.trim();
                console.log(`🔍 Checking button text: "${buttonText}"`);
                
                if (buttonText === "Access Simulation") {
                    targetButton = btn;
                    console.log('✅ Found Access Simulation button');
                    break;
                }
            }
            
            if (!targetButton) {
                if (attemptCount % 10 === 0) { // Log every 5 seconds
                    console.log(`⚠️ Access Simulation button not found yet (attempt ${attemptCount}/${maxAttempts})`);
                }
                
                if (attemptCount >= maxAttempts) {
                    console.error('❌ Timeout: Access Simulation button not found after 30 seconds');
                    clearInterval(interval);
                }
                return;
            }
            
            // STEP 3: Pre-validation - Check if button is visible and enabled
            if (!window.domHelpers.validateElementVisible(targetButton)) {
                console.warn('⚠️ Access Simulation button found but not visible, continuing to wait');
                return;
            }
            
            if (targetButton.disabled) {
                console.warn('⚠️ Access Simulation button found but disabled, continuing to wait');
                return;
            }
            
            console.log('✅ Pre-validation passed: Access Simulation button found, visible, and enabled');
            
            // STEP 4: Click the button
            try {
                targetButton.click();
                console.log('✅ Access Simulation button clicked successfully');
                console.log('🔍 DOM Intelligence: waitForAccessSimulation completed');
                clearInterval(interval);
            } catch (error) {
                console.error('❌ Error clicking Access Simulation button:', error.message);
                clearInterval(interval);
            }
        }, 500);
    }

        createDropdown();
        waitForAccessSimulation();
})();