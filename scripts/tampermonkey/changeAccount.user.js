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
        validateElementExists: (selector) => !!document.querySelector(selector),
        validateElementVisible: (element) => {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return style.display !== 'none' && style.visibility !== 'hidden' && 
                   element.offsetWidth > 0 && element.offsetHeight > 0;
        },
        waitForElement: async (selector, timeout = 10000) => {
            const startTime = Date.now();
            return new Promise((resolve) => {
                const checkElement = () => {
                    const element = document.querySelector(selector);
                    if (element) {
                        resolve(element);
                        return;
                    }
                    if (Date.now() - startTime >= timeout) {
                        resolve(null);
                        return;
                    }
                    setTimeout(checkElement, 100);
                };
                checkElement();
            });
        },
        delays: { modal: 500, dropdown: 300 }
    };
    
    console.log('✅ DOM Helpers initialized with inline fallback');
    return true;
}

// Load DOM helpers on startup
loadDOMHelpers();

/**
 * Enhanced account switching with comprehensive DOM validation
 * @param {string} accountName - The account name/ID to switch to
 * @returns {Promise<boolean>} - Returns true if the account was found and clicked, false otherwise
 */
async function clickAccountItemByName(accountName) {
    console.log(`🔍 DOM Intelligence: Starting account switch to: ${accountName}`);
    
    try {
        // STEP 1: Pre-validation - Check current account
        console.log('🔍 Pre-validation: Checking current account');
        const currentAccountSelector = '.pane.account-selector.dropdown [data-toggle="dropdown"] .name div';
        
        if (window.domHelpers.validateElementExists(currentAccountSelector)) {
            const currentAccountElement = document.querySelector(currentAccountSelector);
            if (currentAccountElement) {
                const currentAccount = currentAccountElement.textContent.trim();
                console.log(`🔍 Current account: "${currentAccount}"`);
                
                // Check if already on target account
                if (currentAccount === accountName) {
                    console.log(`✅ Already on target account: ${currentAccount}`);
                    return true;
                }
            }
        } else {
            console.warn('⚠️ Current account element not found');
        }
        
        // STEP 2: Pre-validation - Check dropdown availability
        console.log('🔍 Pre-validation: Checking account dropdown');
        const dropdownSelector = '.pane.account-selector.dropdown [data-toggle="dropdown"]';
        
        if (!window.domHelpers.validateElementExists(dropdownSelector)) {
            console.error('❌ Pre-validation failed: Account dropdown not found');
            return false;
        }
        
        const dropdown = document.querySelector(dropdownSelector);
        if (!window.domHelpers.validateElementVisible(dropdown)) {
            console.error('❌ Pre-validation failed: Account dropdown not visible');
            return false;
        }
        
        console.log('✅ Pre-validation passed: Account dropdown found and visible');
        
        // STEP 3: Open dropdown with validation
        try {
            dropdown.click();
            console.log('✅ Clicked dropdown to open account list');
        } catch (error) {
            console.error('❌ Error clicking dropdown:', error.message);
            return false;
        }
        
        // STEP 4: Wait for dropdown menu to appear
        console.log('🔍 Waiting for dropdown menu to appear');
        await new Promise(resolve => setTimeout(resolve, window.domHelpers.delays.dropdown));
        
        // STEP 5: Validate dropdown menu appeared
        const dropdownMenuSelector = '.dropdown-menu';
        const dropdownMenu = await window.domHelpers.waitForElement(dropdownMenuSelector, 3000);
        
        if (!dropdownMenu || !window.domHelpers.validateElementVisible(dropdownMenu)) {
            console.error('❌ Dropdown menu did not appear or is not visible');
            return false;
        }
        
        console.log('✅ Dropdown menu appeared and is visible');
        
        // STEP 6: Find and validate account items
        const accountItemsSelector = '.dropdown-menu li a.account';
        const accountItems = document.querySelectorAll(accountItemsSelector);
        
        if (accountItems.length === 0) {
            console.error('❌ No account items found in dropdown');
            document.body.click(); // Close dropdown
            return false;
        }
        
        console.log(`✅ Found ${accountItems.length} account items`);
        
        // STEP 7: Log available accounts for debugging
        accountItems.forEach((item, index) => {
            const itemText = item.textContent.trim();
            const isSelected = item.closest('li').classList.contains('selected');
            console.log(`📋 Account ${index + 1}: "${itemText}" (Selected: ${isSelected})`);
        });
        
        // STEP 8: Find target account with exact matching
        let targetAccountItem = null;
        let targetAccountText = '';
        
        for (const item of accountItems) {
            const itemText = item.textContent.trim();
            const itemMainText = item.querySelector('.name .main')?.textContent.trim();
            const displayText = itemMainText || itemText;
            
            console.log(`🔍 Checking account: "${displayText}" against target: "${accountName}"`);
            
            // Exact matching only
            if (displayText === accountName) {
                targetAccountItem = item;
                targetAccountText = displayText;
                console.log(`✅ Found exact matching account: "${displayText}"`);
                break;
            }
        }
        
        if (!targetAccountItem) {
            console.error(`❌ Target account "${accountName}" not found in dropdown`);
            document.body.click(); // Close dropdown
            return false;
        }
        
        // STEP 9: Check if target account is already selected
        const isAlreadySelected = targetAccountItem.closest('li').classList.contains('selected');
        console.log(`🔍 Target account already selected: ${isAlreadySelected}`);
        
        if (isAlreadySelected) {
            console.log(`✅ Target account "${targetAccountText}" already selected, closing dropdown`);
            document.body.click(); // Close dropdown
            return true;
        }
        
        // STEP 10: Pre-validation - Check if target item is clickable
        if (!window.domHelpers.validateElementVisible(targetAccountItem)) {
            console.error('❌ Target account item not visible');
            document.body.click(); // Close dropdown
            return false;
        }
        
        // STEP 11: Click target account
        try {
            targetAccountItem.click();
            console.log(`✅ Clicked target account: "${targetAccountText}"`);
        } catch (error) {
            console.error('❌ Error clicking target account:', error.message);
            return false;
        }
        
        // STEP 12: Post-validation - Wait for account switch to complete
        console.log('🔍 Waiting for account switch to complete');
        await new Promise(resolve => setTimeout(resolve, window.domHelpers.delays.modal));
        
        // STEP 13: Post-validation - Verify account switch success
        const updatedAccountElement = document.querySelector(currentAccountSelector);
        if (updatedAccountElement) {
            const updatedAccount = updatedAccountElement.textContent.trim();
            const switchSuccessful = updatedAccount === accountName;
            
            console.log(`🔍 Post-validation: Current account is now: "${updatedAccount}"`);
            console.log(`🔍 Switch successful: ${switchSuccessful}`);
            
            if (switchSuccessful) {
                console.log(`✅ DOM Intelligence: Account switch completed successfully to "${accountName}"`);
                return true;
            } else {
                console.error(`❌ Post-validation failed: Expected "${accountName}", got "${updatedAccount}"`);
                return false;
            }
        } else {
            console.error('❌ Post-validation failed: Cannot determine current account after switch');
            return false;
        }
        
    } catch (error) {
        console.error('❌ DOM Intelligence: Account switch failed with error:', error.message);
        // Try to close any open dropdown
        try {
            document.body.click();
        } catch (e) {
            // Ignore cleanup errors
        }
        return false;
    }
}

// Make the function available globally
window.clickAccountItemByName = clickAccountItemByName;
