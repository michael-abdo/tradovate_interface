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
    
    // Only consider exact match for account switching - no substring matching
    if (currentAccount === accountName) {
      console.log(`clickAccountItemByName: Already on the exact account: ${currentAccount}`);
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
      
      // Look for exact match only
      let found = false;
      
      for (const item of items) {
        const itemText = item.textContent.trim();
        const itemMainText = item.querySelector('.name .main')?.textContent.trim();
        console.log(`clickAccountItemByName: Checking against "${itemMainText || itemText}"`);
        
        // Only use exact matching for account names
        if ((itemMainText && itemMainText === accountName) || 
            (itemText === accountName)) {
          
          // Check if this item is already selected
          const isAlreadySelected = item.closest('li').classList.contains('selected');
          console.log(`clickAccountItemByName: Found exact matching account: "${itemMainText || itemText}" (Already selected: ${isAlreadySelected})`);
          
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
          
          // Check if the switch actually worked by verifying the dropdown text matches the account name exactly
          const switchSuccessful = currentAccount && currentAccount === accountName;
          console.log(`clickAccountItemByName: Switch successful: ${switchSuccessful} (current: "${currentAccount}", target: "${accountName}")`);
          
          resolve(switchSuccessful);
        }, 500);
      }
    }, 300);
  });
}

// Make the function available globally
window.clickAccountItemByName = clickAccountItemByName;
