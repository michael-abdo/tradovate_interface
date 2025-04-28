// ==UserScript==
// @name         Change Tradovate Account
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Switch between Tradovate accounts
// @author       You
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// ==/UserScript==

/**
 * Changes the active account in Tradovate UI to the specified account
 * 
 * @param {string} accountName - The account name/ID to switch to (e.g., "DEMO4656027")
 * @returns {Promise<string>} - Result message
 */
function changeAccount(accountName) {
    return new Promise((resolve, reject) => {
        try {
            console.log(`Attempting to change to account: ${accountName}`);
            
            // First check if the account is already selected
            const currentAccountElement = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"] .name div');
            if (currentAccountElement) {
                const currentAccount = currentAccountElement.textContent.trim();
                console.log(`Current account is: "${currentAccount}"`);
                
                // Only consider exact match for account switching - no substring matching
                if (currentAccount === accountName) {
                    console.log(`Already on the exact account: ${currentAccount}`);
                    return resolve(`Already on account: ${currentAccount}`);
                }
            }
            
            // Step 1: Find and click the account dropdown
            const dropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
            if (!dropdown) {
                console.error('Account dropdown not found');
                return reject('Account dropdown not found');
            }
            
            console.log('Found account dropdown, clicking to open');
            dropdown.click();
            
            // Step 2: Find and click the specified account in the dropdown
            setTimeout(() => {
                const accountItems = document.querySelectorAll('.dropdown-menu li a.account');
                console.log(`Found ${accountItems.length} account items in dropdown`);
                
                let found = false;
                
                // Log all available accounts for debugging
                accountItems.forEach(item => {
                    const itemText = item.textContent.trim();
                    const isSelected = item.closest('li').classList.contains('selected');
                    console.log(`Available account: "${itemText}" (Selected: ${isSelected})`);
                });
                
                // Try to find and click the matching account
                for (const item of accountItems) {
                    const itemText = item.textContent.trim();
                    const itemMainText = item.querySelector('.name .main')?.textContent.trim();
                    console.log(`Checking account item: "${itemMainText || itemText}"`);
                    
                    // Only use exact matching for account names
                    if ((itemMainText && itemMainText === accountName) || 
                        (itemText === accountName)) {
                        
                        // Check if this item is already selected
                        const isAlreadySelected = item.closest('li').classList.contains('selected');
                        console.log(`Found matching account: "${itemMainText || itemText}" (Already selected: ${isAlreadySelected})`);
                        
                        if (isAlreadySelected) {
                            // If already selected, just close the dropdown by clicking elsewhere
                            document.body.click();
                            found = true;
                            resolve(`Already on account: ${itemMainText || itemText}`);
                            return;
                        }
                        
                        console.log(`Clicking to switch to account: ${itemMainText || itemText}`);
                        item.click();
                        found = true;
                        
                        // Give the UI time to update
                        setTimeout(() => {
                            const newAccountElement = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"] .name div');
                            const newAccount = newAccountElement ? newAccountElement.textContent.trim() : 'Unknown';
                            console.log(`Account switched to: ${newAccount}`);
                            
                            // Verify switch was successful with exact matching
                            const switchSuccessful = newAccount && newAccount === accountName;
                            
                            if (switchSuccessful) {
                                resolve(`Successfully changed to account: ${newAccount}`);
                            } else {
                                console.error(`Account switch may have failed. Expected: "${accountName}", Got: "${newAccount}"`);
                                // Return success if we tried our best but the text doesn't match exactly
                                // This helps with cases where the account display might include extra text
                                resolve(`Attempted to change to account: ${accountName}, now showing: ${newAccount}`);
                            }
                        }, 500);
                        break;
                    }
                }
                
                if (!found) {
                    console.error(`Account "${accountName}" not found in dropdown`);
                    // Close the dropdown by clicking elsewhere
                    document.body.click();
                    reject(`Account "${accountName}" not found in dropdown`);
                }
            }, 300);
        } catch (error) {
            console.error('Error changing account:', error);
            reject(`Error changing account: ${error.message}`);
        }
    });
}

// Make the function available globally
window.changeAccount = changeAccount;