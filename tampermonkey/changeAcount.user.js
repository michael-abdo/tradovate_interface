/**
 * Switches to the specified account by name
 * 
 * @param {string} accountName - The account name/ID to switch to
 * @returns {boolean} - Returns true if the account was found and clicked, false otherwise
 */
function clickAccountItemByName(accountName) {
  console.log(`clickAccountItemByName: Attempting to switch to account: ${accountName}`);
  
  // First check if the account is already selected
  const currentAccountElement = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"] .name div');
  if (currentAccountElement) {
    const currentAccount = currentAccountElement.textContent.trim();
    console.log(`clickAccountItemByName: Current account is: "${currentAccount}"`);
    
    // If already on the correct account, return success immediately
    if (currentAccount === accountName || (accountName && currentAccount.includes(accountName))) {
      console.log(`clickAccountItemByName: Already on the correct account: ${currentAccount}`);
      return Promise.resolve(true);
    }
  }
  
  // First check if account dropdown is available
  const dropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
  if (!dropdown) {
    console.error('clickAccountItemByName: Account dropdown not found');
    return Promise.resolve(false);
  }
  
  // Open the dropdown
  dropdown.click();
  console.log('clickAccountItemByName: Clicked dropdown to open it');
  
  // Return a promise that resolves with the result
  return new Promise((resolve) => {
    setTimeout(() => {
      const items = document.querySelectorAll('.dropdown-menu li a.account');
      console.log(`clickAccountItemByName: Found ${items.length} account items`);
      
      // Log available accounts for debugging
      items.forEach(item => {
        const itemText = item.textContent.trim();
        const isSelected = item.closest('li').classList.contains('selected');
        console.log(`clickAccountItemByName: Available account: "${itemText}" (Selected: ${isSelected})`);
      });
      
      // Look for exact match first
      let found = false;
      
      for (const item of items) {
        const itemText = item.textContent.trim();
        const itemMainText = item.querySelector('.name .main')?.textContent.trim();
        console.log(`clickAccountItemByName: Checking against "${itemMainText || itemText}"`);
        
        // First try exact match, then fallback to contains
        if ((itemMainText && (itemMainText === accountName || itemMainText.includes(accountName))) ||
            (itemText === accountName || itemText.includes(accountName))) {
          
          // Check if this item is already selected
          const isAlreadySelected = item.closest('li').classList.contains('selected');
          console.log(`clickAccountItemByName: Found matching account: "${itemMainText || itemText}" (Already selected: ${isAlreadySelected})`);
          
          if (isAlreadySelected) {
            // If already selected, just close the dropdown by clicking elsewhere
            document.body.click();
            found = true;
            resolve(true);
            return;
          }
          
          // Otherwise click to switch to this account
          item.click();
          found = true;
          break;
        }
      }
      
      if (!found) {
        console.error(`clickAccountItemByName: Account "${accountName}" not found in dropdown`);
        // Close the dropdown by clicking elsewhere
        document.body.click();
        resolve(false); // Account not found
      } else {
        // Give UI time to update and verify the switch worked
        setTimeout(() => {
          const currentAccountElement = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"] .name div');
          const currentAccount = currentAccountElement ? currentAccountElement.textContent.trim() : null;
          console.log(`clickAccountItemByName: Account switched to: "${currentAccount}"`);
          
          // Check if the switch actually worked by verifying the dropdown text contains the account name
          const switchSuccessful = currentAccount && 
            (currentAccount === accountName || (accountName && currentAccount.includes(accountName)));
          console.log(`clickAccountItemByName: Switch successful: ${switchSuccessful}`);
          
          resolve(switchSuccessful);
        }, 500);
      }
    }, 300);
  });
}

// Make the function available globally
window.clickAccountItemByName = clickAccountItemByName;
