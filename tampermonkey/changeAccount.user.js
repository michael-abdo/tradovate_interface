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
                    console.log(`Available account: ${item.textContent.trim()}`);
                });
                
                // Try to find and click the matching account
                for (const item of accountItems) {
                    const itemText = item.textContent.trim();
                    console.log(`Checking account item: "${itemText}"`);
                    
                    // Match by exact ID or contains the ID (more flexible)
                    if (itemText === accountName || itemText.includes(accountName)) {
                        console.log(`Found matching account: ${itemText}`);
                        item.click();
                        found = true;
                        
                        // Give the UI time to update
                        setTimeout(() => {
                            const currentAccount = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]').textContent.trim();
                            console.log(`Account switched to: ${currentAccount}`);
                            resolve(`Successfully changed to account: ${currentAccount}`);
                        }, 500);
                        break;
                    }
                }
                
                if (!found) {
                    console.error(`Account "${accountName}" not found in dropdown`);
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