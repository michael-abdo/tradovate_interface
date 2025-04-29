// ==UserScript==
// @name         Auto Risk Management
// @namespace    http://tampermonkey.net/
// @version      2025-04-17
// @description  try to take over the world!
// @author       You
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function updateDOMDollarTotalPL(...manualAdds) {
        const phaseRandomValues = {};
        const rows = Array.from(document.querySelectorAll('.fixedDataTableCellGroupLayout_cellGroupWrapper[style*="left: 185px"]'));
        const formatCurrency = num =>
        "$" + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        rows.slice(1).forEach((row, i) => {
            const cellGroup = row.querySelector('.fixedDataTableCellGroupLayout_cellGroup');
            if (!cellGroup || cellGroup.children.length < 4) return;

            let addition = 0;
            if (manualAdds.length > 0) {
                addition = parseFloat(manualAdds[i]) || 0;
            } else {
                const phase = row.getAttribute('data-phase') || 'Unknown';
                if (!(phase in phaseRandomValues)) {
                    phaseRandomValues[phase] = Math.floor(Math.random() * (10000 - 1000 + 1)) + 1000;
                }
                addition = phaseRandomValues[phase];
            }

            const updateCell = cell => {
                const contentEl = cell.querySelector('.public_fixedDataTableCell_cellContent');
                if (!contentEl) return;
                const current = parseFloat(contentEl.textContent.replace(/[^0-9.-]+/g, ""));
                if (isNaN(current)) return;
                contentEl.textContent = formatCurrency(current + addition);
            };

            updateCell(cellGroup.children[0]);
            updateCell(cellGroup.children[3]);
        });
    }



    function updateUserColumnPhaseStatus() {
        console.log("[updateUserColumnPhaseStatus] Starting...");
        //debugger; // JavaScript debugger breakpoint
        
        const accountTable = document.querySelector('.module.positions.data-table');
        if (!accountTable) {
          console.error("[updateUserColumnPhaseStatus] No accountTable found");
          return;
        }

        const rows = accountTable.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
        if (!rows.length){
            console.error("[updateUserColumnPhaseStatus] No rows found");
            return;
        } 
        console.log(`[updateUserColumnPhaseStatus] Found ${rows.length} rows`);

        // Determine the index of the "User" column from the header row.
        const headerCells = rows[0].querySelectorAll('.public_fixedDataTableCell_cellContent');
        console.log(`[updateUserColumnPhaseStatus] Header cells:`, 
            Array.from(headerCells).map(c => c.textContent.trim()));
            
        let userIndex = -1;
        headerCells.forEach((cell, i) => {
            if (cell.textContent.trim().startsWith("User")) {
                userIndex = i;
                console.log(`[updateUserColumnPhaseStatus] Found User column at index ${i}`);
            }
        });
        
        if (userIndex === -1) {
            console.error("[updateUserColumnPhaseStatus] User column not found");
            return;
        }

        console.log("[updateUserColumnPhaseStatus] Getting table data...");
        const tableData = getTableData();
        console.log(`[updateUserColumnPhaseStatus] Table data: ${tableData.length} rows`);
        if (tableData.length === 0) {
            console.error("[updateUserColumnPhaseStatus] No data from getTableData()");
            return;
        }

        // Update the "User" column cells for each data row with phase and status.
        rows.forEach((row, idx) => {
            if (idx === 0) return; // skip header row
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            
            if (idx === 1) {
                console.log(`[updateUserColumnPhaseStatus] First data row has ${cells.length} cells, we need index ${userIndex}`);
            }
            
            if (cells.length > userIndex) {
                const cell = cells[userIndex];
                if (!tableData[idx - 1]) {
                    console.error(`[updateUserColumnPhaseStatus] No data for row ${idx}`);
                    return;
                }
                
                const dataRow = tableData[idx - 1];
                const accountName = dataRow["Account ▲"] || dataRow["Account"] || "Unknown";
                console.log(`[updateUserColumnPhaseStatus] Setting row ${idx} (${accountName}) phase=${dataRow.phase}, active=${dataRow.active}`);
                
                cell.textContent = `${dataRow.phase} (${dataRow.active ? 'active' : 'inactive'})`;
                cell.style.color = dataRow.active ? 'green' : 'red';
            } else {
                console.error(`[updateUserColumnPhaseStatus] Row ${idx} doesn't have enough cells (has ${cells.length}, needs index ${userIndex})`);
            }
        });
        
        console.log("[updateUserColumnPhaseStatus] Completed");
    }




    const phaseCriteria = [
          // ── DEMO ──
        {
            phase: '1',
            accountNameIncludes: 'DEMO',
            totalAvailOperator: '<',
            totalAvailValue: 60000,   // midpoint between 50 k-70 k
            distDrawOperator: '>',
            distDrawValue: 2000,
            maxActive: 0,
            reduceFactor: 0.5,
            useOr: false,
            quantity: 20
        },
        {
            phase: '2',
            accountNameIncludes: 'DEMO',
            totalAvailOperator: '>=',
            totalAvailValue: 60000,
            distDrawOperator: '<=',
            distDrawValue: 2000,
            maxActive: 0,
            reduceFactor: null,
            useOr: true,
            quantity: 10
        },
        
        // ── APEX ──
        {
            phase: '1',
            accountNameIncludes: 'APEX',
            totalAvailOperator: '<',
            totalAvailValue: 310000,
            distDrawOperator: '>',
            distDrawValue: 2000,
            maxActive: 0,
            reduceFactor: 0.5,
            useOr: false,
            quantity: 20
        },
        {
            phase: '2',
            accountNameIncludes: 'APEX',
            totalAvailOperator: '>=',
            totalAvailValue: 310000,
            distDrawOperator: '<=',
            distDrawValue: 2000,
            maxActive: 0,
            reduceFactor: null,
            useOr: true,
            quantity: 10
        },
        {
            phase: '3',
            accountNameIncludes: 'PAAPEX',
            totalAvailOperator: null,
            totalAvailValue: 0,
            distDrawOperator: null,
            distDrawValue: 0,
            maxActive: 20,
            reduceFactor: null,
            useOr: false,
            quantity: 2
        }
    ];



    function getTableData() {
        const accountTable = document.querySelector('.module.positions.data-table');
        if (!accountTable) return [];

        const rows = accountTable.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
        if (!rows.length) return [];

        // First row as header (skip header in final output)
        const headerCells = rows[0].querySelectorAll('.public_fixedDataTableCell_cellContent');
        const headers = Array.from(headerCells).map(cell => cell.textContent.trim());

        const jsonData = [];
        // Reset phase tracking before processing rows.
        analyzePhase(null, true);

        rows.forEach((row, index) => {
            if (index === 0) return; // Skip header row
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            const values = Array.from(cells).map(cell => cell.textContent.trim());
            if (values.length) {
                const rowObj = {};
                headers.forEach((header, i) => {
                    rowObj[header] = values[i];
                });
                // Process the row to determine its phase and active state.
                rowObj.phase = analyzePhase(rowObj);

                // Build a simplified object with the desired keys including "active".
                const simpleRow = {
                    "Account ▲": rowObj["Account ▲"] || rowObj["Account"] || "",
                    "Dollar Total P L": rowObj["Dollar Total P L"] || "",
                    "Dollar Open P L": rowObj["Dollar Open P L"] || "",
                    "Dist Drawdown Net Liq": rowObj["Dist Drawdown Net Liq"] || "",
                    "Total Available Margin": rowObj["Total Available Margin"] || "",
                    "phase": rowObj.phase,
                    "active": rowObj.active || false
                };

                jsonData.push(simpleRow);
            }
        });

        return jsonData;
    }


    function analyzePhase(row, reset = false) {
        //console.log("[analyzePhase] called with row:", row, "reset:", reset);

        if (reset || typeof analyzePhase.phaseData === 'undefined') {
            console.log("[analyzePhase] resetting phaseData");
            analyzePhase.phaseData = {};

            const phase1Count = phaseCriteria.filter(r => r.phase === '1').length;
            const rule1 = phaseCriteria.find(r => r.phase === '1');
            if (rule1) {
                rule1.maxActive = 1//Math.ceil(phase1Count / 2);
                console.log(`[analyzePhase] set phase 1 maxActive to ${rule1.maxActive}`);
            }

            const increment = typeof analyzePhase.maxActiveIncrement === 'number'
            ? analyzePhase.maxActiveIncrement
            : 1;
            const rule2 = phaseCriteria.find(r => r.phase === '2');
            if (rule2) {
                rule2.maxActive = 1//+= increment;
                console.log(`[analyzePhase] increased phase 2 maxActive to ${rule2.maxActive}`);
            }
        }


        if (row === null) {
            //console.log("[analyzePhase] row is null, exiting");
            return;
        }

        function parseValue(val) {
            if (!val || typeof val !== 'string') {
                console.log(`[parseValue] Invalid value: ${val}, type: ${typeof val}`);
                return 0;
            }
            const num = parseFloat(val.replace(/[$,()]/g, ''));
            return (val.includes('(') && val.includes(')')) ? -num : num;
        }
        const parsed = {
            totalAvail: parseValue(row["Total Available Margin"] || "$0.00"),
            distDraw:   parseValue(row["Dist Drawdown Net Liq"] || "$0.00")
        };

        const accountName = row["Account ▲"] || row["Account"] || "";
        function compareNumeric(value, operator, compareValue) {
            const ops = { '>':(a,b)=>a>b, '<':(a,b)=>a<b, '>=':(a,b)=>a>=b, '<=':(a,b)=>a<=b };
            return ops[operator]?.(value, compareValue) ?? false;
        }
        function matchesRule(rule) {
            if (rule.accountNameIncludes && !accountName.includes(rule.accountNameIncludes)) return false;
            const ta = rule.totalAvailOperator
            ? compareNumeric(parsed.totalAvail, rule.totalAvailOperator, rule.totalAvailValue)
            : true;
            const dd = rule.distDrawOperator
            ? compareNumeric(parsed.distDraw, rule.distDrawOperator, rule.distDrawValue)
            : true;
            return rule.useOr && rule.totalAvailOperator && rule.distDrawOperator
                ? (ta || dd)
            : (ta && dd);
        }

        let rule = accountName.includes('PAAPEX')
        ? phaseCriteria.find(r => r.accountNameIncludes === 'PAAPEX')
        : phaseCriteria.find(matchesRule) || { phase:'Unknown', maxActive:0, profitLimit:Infinity };

        row.phase = rule.phase;
        row.phaseInfo = { phase:rule.phase, maxActive:rule.maxActive, profitLimit:rule.profitLimit,
                         accountName, totalAvail:parsed.totalAvail, distDraw:parsed.distDraw,
                         reduceFactor:rule.reduceFactor||null };

        if (rule.phase === '2' && parsed.totalAvail > 320000) {
            row.active = false;
            return rule.phase;
        }

        if (!analyzePhase.phaseData[rule.phase]) {
            analyzePhase.phaseData[rule.phase] = { activeCount:0, cumulativeProfit:0 };
        }

        function parseDollar(val) {
            const num = parseFloat(val.replace(/[$,()]/g, ''));
            return (val.includes('(') && val.includes(')')) ? -num : num;
        }
        const profit = parseDollar(row["Dollar Total P L"]||"$0.00");
        analyzePhase.phaseData[rule.phase].cumulativeProfit += profit;

        // Determine how many can be active
        let allowedActive = rule.maxActive;
        if (analyzePhase.phaseData[rule.phase].cumulativeProfit > rule.profitLimit) {
            allowedActive = rule.reduceFactor
                ? Math.ceil(rule.maxActive * rule.reduceFactor)
            : 0;
        }

        const currentActive = analyzePhase.phaseData[rule.phase].activeCount;
        if (currentActive >= allowedActive) {
            row.active = false;
            //console.log(`[analyzePhase] phase ${rule.phase} activeCount ${currentActive} ≥ maxActive ${allowedActive}, deactivating`);
            return rule.phase;
        }

        // Otherwise activate
        row.active = true;
        analyzePhase.phaseData[rule.phase].activeCount++;
        //console.log(`[analyzePhase] activating phase ${rule.phase}, new count:`, analyzePhase.phaseData[rule.phase].activeCount);

        return rule.phase;
    }









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


function addActionButton() {
  if (document.getElementById('phaseActionBtn')) return;

  const btn = document.createElement('button');
  btn.id = 'phaseActionBtn';
  btn.textContent = 'Run Phases';
  Object.assign(btn.style, {
    position: 'fixed',
    top: '20px',
    left: '20px',
    background: '#28a745',
    color: '#fff',
    padding: '10px 14px',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    zIndex: 999
  });
  document.body.appendChild(btn);

  let dragging = false, offsetX = 0, offsetY = 0, moved = false;

  btn.addEventListener('pointerdown', e => {
    dragging = true;
    moved = false;
    offsetX = e.clientX - btn.offsetLeft;
    offsetY = e.clientY - btn.offsetTop;
    btn.setPointerCapture(e.pointerId);
  });

  btn.addEventListener('pointermove', e => {
    if (!dragging) return;
    const newLeft = Math.min(Math.max(0, e.clientX - offsetX), window.innerWidth - btn.offsetWidth);
    const newTop  = Math.min(Math.max(0, e.clientY - offsetY), window.innerHeight - btn.offsetHeight);
    btn.style.left = `${newLeft}px`;
    btn.style.top  = `${newTop}px`;
    moved = true;
  });

  btn.addEventListener('pointerup', e => {
    dragging = false;
    btn.releasePointerCapture(e.pointerId);
    if (!moved) {                      // treat as click if no drag
      getTableData();
      updateUserColumnPhaseStatus();
      performAccountActions();
    }
  });
}


    addActionButton();
    
    // Run auto risk management immediately when the script loads
    console.log("Auto Risk Management: Running initial risk assessment...");
    getTableData();
    updateUserColumnPhaseStatus();
    performAccountActions();
    console.log("Auto Risk Management: Initial risk assessment completed");

})();