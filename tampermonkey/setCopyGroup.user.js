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

    // After clicking gear, move active left->right and inactive right->left, then set quantities
    setTimeout(() => {
      const tableData = getTableData();
      const map = {};
      tableData.forEach(row => {
        const name = row["Account ▲"] || row["Account"];
        map[name] = row;
      });
      const leftList = document.querySelectorAll('.columns-configurator--container')[0].querySelector('.sortable-list');
      const rightList = document.querySelectorAll('.columns-configurator--container')[1].querySelector('.sortable-list');

      // Move active from left->right
      leftList.querySelectorAll('[draggable="true"]').forEach(item => {
        const name = item.textContent.trim().split('\n')[0];
        if (map[name]?.active) simulateDragAndDrop(item, rightList);
      });

      // Move inactive from right->left
      rightList.querySelectorAll('[draggable="true"]').forEach(item => {
        const name = item.textContent.trim().split('\n')[0];
        if (!map[name]?.active) simulateDragAndDrop(item, leftList);
      });

      // Set quantities based on phase, then update total and master quantity
      setTimeout(() => {
        setQuantities();
        const total = calculateTotalQuantity();

        // Click Save if present
        const saveBtn = document.querySelector('.modal-footer .btn.btn-primary');
        if (saveBtn) saveBtn.click();

        // After saving, OK/Close if present, then update master quantity
        setTimeout(() => {
          const okBtn = Array.from(document.querySelectorAll('.modal-footer .btn'))
            .find(btn => btn.textContent.trim() === 'OK');
          if (okBtn) okBtn.click();

          setTimeout(() => {
            const closeBtn = Array.from(document.querySelectorAll('.modal-header .close, .modal-footer .btn'))
              .find(btn => btn.textContent.trim() === 'Close');
            if (closeBtn) closeBtn.click();

            setTimeout(() => updateMasterQuantity(total), 500);
          }, 500);
        }, 500);
      }, 500);
    }, 500);
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


// Helper: returns the `quantity` defined for a phase (defaults to 0)
function getPhaseQuantity(phase) {
  const crit = phaseCriteria.find(c => c.phase === phase);
  return crit ? crit.quantity : 0;
}

function setQuantities() {
  const tableData = getTableData();
  const phaseByAccount = {};
  tableData.forEach(r => {
    const key = r["Account ▲"] || r["Account"];
    phaseByAccount[key] = r.phase;
  });

  const added = document.querySelectorAll('.columns-configurator--container')[1]
                  .querySelector('.sortable-list');

  added.querySelectorAll('.sortable-list-item').forEach(item => {
    const accountName = item.textContent.trim().split('\n')[0];
    const qty = getPhaseQuantity(phaseByAccount[accountName]);
    const input = item.querySelector('input.form-control');
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, qty);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      console.log(`Set ${accountName} qty to`, qty);
    }
  });
}

function calculateTotalQuantity() {
  const tableData = getTableData();
  const phaseByAccount = {};
  tableData.forEach(r => {
    const key = r["Account ▲"] || r["Account"];
    phaseByAccount[key] = r.phase;
  });

  const added = document.querySelectorAll('.columns-configurator--container')[1]
                  .querySelector('.sortable-list');

  let total = 0;
  added.querySelectorAll('.sortable-list-item').forEach(item => {
    const accountName = item.textContent.trim().split('\n')[0];
    total += getPhaseQuantity(phaseByAccount[accountName]);
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

    // Optionally move everything back before we proceed
    if (moveBack) {
      rightList.querySelectorAll('[draggable="true"]').forEach(item => {
        simulateDragAndDrop(item, leftList);
        console.log('Moved back:', item.textContent.trim());
      });
    }

    // Move accounts based on active/inactive
    if (moveItems) {
      const tableData = getTableData();
      const map = {};
      tableData.forEach(row => {
        const accountKey = row["Account ▲"] || row["Account"];
        map[accountKey] = row.active;
      });

      // Move active from left->right
      leftList.querySelectorAll('[draggable="true"]').forEach(item => {
        const name = item.textContent.trim().split('\n')[0];
        if (map[name]) simulateDragAndDrop(item, rightList);
      });

      // Move inactive from right->left
      rightList.querySelectorAll('[draggable="true"]').forEach(item => {
        const name = item.textContent.trim().split('\n')[0];
        if (!map[name]) simulateDragAndDrop(item, leftList);
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
