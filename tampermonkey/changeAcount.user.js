/**
 * Switches to the specified account by name
 * 
 * @param {string} accountName - The account name/ID to switch to
 * @returns {boolean} - Returns true if the account was found and clicked, false otherwise
 */
function clickAccountItemByName(accountName) {
  console.log(`clickAccountItemByName: Attempting to switch to account: ${accountName}`);
  
  // First check if account dropdown is available
  const dropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
  if (!dropdown) {
    console.error('clickAccountItemByName: Account dropdown not found');
    return false;
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
        console.log(`clickAccountItemByName: Available account: ${item.textContent.trim()}`);
      });
      
      // Look for exact match first
      let found = false;
      
      for (const item of items) {
        const itemText = item.textContent.trim();
        console.log(`clickAccountItemByName: Checking against "${itemText}"`);
        
        // First try exact match, then fallback to contains
        if (itemText === accountName || itemText.includes(accountName)) {
          console.log(`clickAccountItemByName: Found matching account: ${itemText}`);
          item.click();
          found = true;
          break;
        }
      }
      
      if (!found) {
        console.error(`clickAccountItemByName: Account "${accountName}" not found in dropdown`);
        resolve(false); // Account not found
      } else {
        // Give UI time to update and verify the switch worked
        setTimeout(() => {
          const currentAccount = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]')?.textContent.trim();
          console.log(`clickAccountItemByName: Account switched to: ${currentAccount}`);
          
          // Check if the switch actually worked by verifying the dropdown text contains the account name
          const switchSuccessful = currentAccount && currentAccount.includes(accountName);
          console.log(`clickAccountItemByName: Switch successful: ${switchSuccessful}`);
          
          resolve(switchSuccessful);
        }, 500);
      }
    }, 300);
  });
}

// Make the function available globally
window.clickAccountItemByName = clickAccountItemByName;
