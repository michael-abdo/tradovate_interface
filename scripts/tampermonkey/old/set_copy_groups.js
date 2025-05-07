




function performAccountActions() {
  // Step 1: Open settings by clicking the dropdown toggle
  const dropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
  if (dropdown) dropdown.click();

  // Step 2: After 500ms, click the gear in the "Account group" entry
  setTimeout(() => {
    document.querySelectorAll('.dropdown-menu li a.account').forEach(item => {
      if (item.textContent.includes('Account group')) {
        const gear = item.querySelector('.btn.btn-icon');
        if (gear) gear.click();
      }
    });
  }, 500);
}

function simulateDragAndDrop(item, target) {
  const dragStartEvent = new DragEvent('dragstart', { bubbles: true });
  const dragOverEvent = new DragEvent('dragover', { bubbles: true });
  const dropEvent = new DragEvent('drop', { bubbles: true });

  console.log('Simulating drag:', item.textContent.trim());
  item.dispatchEvent(dragStartEvent);
  target.dispatchEvent(dragOverEvent);
  target.dispatchEvent(dropEvent);
}

function setQuantities() {
  const tableData = getTableData();
  const accountPhaseMapping = {};
  tableData.forEach(row => {
    const accountKey = row["Account ▲"] || row["Account"];
    accountPhaseMapping[accountKey] = row.phase;
  });
  
  const phaseCount = {};
  const addedList = document.querySelectorAll('.columns-configurator--container')[1].querySelector('.sortable-list');
  addedList.querySelectorAll('.sortable-list-item').forEach(item => {
    const accountName = item.textContent.trim().split('\n')[0];
    const phase = accountPhaseMapping[accountName];
    let qty = 0;
    if (phaseQuantDict[phase]) {
      if (!phaseCount[phase]) phaseCount[phase] = 0;
      if (phaseCount[phase] < phaseQuantDict[phase].maxActiveAccounts) {
        qty = phaseQuantDict[phase].qty;
        phaseCount[phase]++;
      }
    }
    const input = item.querySelector('input.form-control');
    if (input) {
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputValueSetter.call(input, qty);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      console.log(`Set ${accountName} qty to`, qty);
    }
  });
}

function calculateTotalQuantity() {
  const tableData = getTableData();
  const accountPhaseMapping = {};
  tableData.forEach(row => {
    const accountKey = row["Account ▲"] || row["Account"];
    accountPhaseMapping[accountKey] = row.phase;
  });
  
  const phaseCount = {};
  const addedList = document.querySelectorAll('.columns-configurator--container')[1].querySelector('.sortable-list');
  let total = 0;
  addedList.querySelectorAll('.sortable-list-item').forEach(item => {
    const accountName = item.textContent.trim().split('\n')[0];
    const phase = accountPhaseMapping[accountName];
    let qty = 0;
    if (phaseQuantDict[phase]) {
      if (!phaseCount[phase]) phaseCount[phase] = 0;
      if (phaseCount[phase] < phaseQuantDict[phase].maxActiveAccounts) {
        qty = phaseQuantDict[phase].qty;
        phaseCount[phase]++;
      }
    }
    total += qty;
  });
  return total;
}

function updateMasterQuantity(total) {
  const masterInput = document.querySelector('input.form-control[placeholder="Select value"]');
  if (masterInput) {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(masterInput, total);
    masterInput.dispatchEvent(new Event('input', { bubbles: true }));
    masterInput.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('Updated master quantity to', total);
  }
  const bracketQtyInput = document.getElementById('qtyInput');
  if (bracketQtyInput) {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(bracketQtyInput, total);
    bracketQtyInput.dispatchEvent(new Event('input', { bubbles: true }));
    bracketQtyInput.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('Updated bracket trade quantity to', total);
  }
}

function moveItemsAndClickButtons(moveItems, clickSave, clickClose, moveBack) {

  let accountMarked = false;
  const accountDropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
  if (accountDropdown) {
    console.log('Step 1: Clicking account group dropdown for check mark');
    accountDropdown.click();
    setTimeout(() => {
      const accountGroupItem = Array.from(document.querySelectorAll('.dropdown-menu li a.account'))
        .find(item => item.textContent.includes('Account group'));
      if (accountGroupItem && accountGroupItem.querySelector('.icon-checkmark')) {
        accountMarked = true;
        console.log('Step 2: Account group already marked');
      } else {
        console.log('Step 2: Account group not marked');
      }
      setTimeout(() => {
        document.querySelectorAll('.dropdown-menu li a.account').forEach(item => {
          if (item.textContent.includes('Account group')) {
            const gear = item.querySelector('.btn.btn-icon');
            if (gear) {
              console.log('Step 3: Clicking gear inside Account group entry');
              gear.click();
            }
          }
        });
        proceed(accountMarked);
      }, 500);
    }, 500);
  } else {
    proceed(accountMarked);
  }

  function proceed(accountMarked) {
    const leftList = document.querySelectorAll('.columns-configurator--container')[0].querySelector('.sortable-list');
    const rightList = document.querySelectorAll('.columns-configurator--container')[1].querySelector('.sortable-list');

    // After the gear is clicked, reset items if moveBack is true.
    if (moveBack) {
      rightList.querySelectorAll('[draggable="true"]').forEach(item => {
        simulateDragAndDrop(item, leftList);
        console.log('Moved back:', item.textContent.trim());
      });
    }

    if (moveItems) {
      const tableData = getTableData();
      const accountPhaseMapping = {};
      tableData.forEach(row => {
        const accountKey = row["Account ▲"] || row["Account"];
        accountPhaseMapping[accountKey] = row.phase;
      });
      leftList.querySelectorAll('[draggable="true"]').forEach(item => {
        const accountName = item.textContent.trim().split('\n')[0];
        const phase = accountPhaseMapping[accountName];
        if (!phaseQuantDict[phase]) return;
        const currentCount = Array.from(rightList.querySelectorAll('.sortable-list-item'))
          .filter(it => {
            const name = it.textContent.trim().split('\n')[0];
            return accountPhaseMapping[name] === phase;
          }).length;
        if (currentCount < phaseQuantDict[phase].maxActiveAccounts) {
          simulateDragAndDrop(item, rightList);
        } else {
          console.log(`Skipping drag for ${accountName} - phase ${phase} limit reached`);
        }
      });
    }

    setTimeout(() => {
      if (moveItems) setQuantities();
      const total = calculateTotalQuantity();
      setTimeout(() => {
        if (clickSave) {
          const saveBtn = document.querySelector('.modal-footer .btn.btn-primary');
          if (saveBtn) {
            console.log('Clicking Save...');
            saveBtn.click();
          }
        }
        setTimeout(() => {
          if (clickClose) {
            const okBtn = Array.from(document.querySelectorAll('.modal-footer .btn'))
              .find(btn => btn.textContent.trim() === 'OK');
            if (okBtn) {
              console.log('Clicking OK...');
              okBtn.click();
            }
            setTimeout(() => {
              const closeBtn = Array.from(document.querySelectorAll('.modal-header .close, .modal-footer .btn'))
                .find(btn => btn.textContent.trim() === 'Close');
              if (closeBtn) {
                console.log('Clicking Close...');
                closeBtn.click();
              }
              setTimeout(() => {
                updateMasterQuantity(total);
                if (!accountMarked) {
                  const finalDropdown = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
                  if (finalDropdown) {
                    console.log('Final step: Clicking account group dropdown (account group not marked)');
                    finalDropdown.click();
                    setTimeout(() => {
                      const finalAccountGroup = Array.from(document.querySelectorAll('.dropdown-menu li a.account'))
                        .find(item => item.textContent.includes('Account group'));
                      if (finalAccountGroup && !finalAccountGroup.querySelector('.icon-checkmark')) {
                        console.log('Final step: Clicking final Account Group...');
                        finalAccountGroup.click();
                      }
                    }, 500);
                  }
                }
              }, 1000);
            }, 500);
          }
        }, 500);
      }, 500);
    }, 500);
  }
}


// Execute the full process: open settings, update settings, and update master quantity
  moveItemsAndClickButtons(true, true, true, true);
