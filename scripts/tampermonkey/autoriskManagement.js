// ==UserScript==
// @name         Auto Risk Management
// @namespace    http://tampermonkey.net/
// @version      2025-04-17.1
// @description  try to take over the world!
// @author       You
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
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
                    console.log(`✅ Element is visible: ${element.tagName}${element.className ? '.' + element.className : ''}`);
                } else {
                    console.warn(`❌ Element is not visible: ${element.tagName}${element.className ? '.' + element.className : ''}`);
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
    
    // ============================================================================
    // UNIFIED RISK MANAGEMENT FUNCTIONS - DRY Refactored
    // ============================================================================
    
    // Global risk management utilities that consolidate duplicate logic
    window.unifiedRiskManagement = {
        
        /**
         * Calculate position size based on account phase and risk rules
         * Consolidates logic from autoTrade and risk management calculations
         */
        calculatePositionSize: function(baseQuantity, accountName, accountMetrics = null) {
            try {
                console.log(`[Risk] Calculating position size: base=${baseQuantity}, account=${accountName}`);
                
                if (!baseQuantity || baseQuantity <= 0) {
                    console.warn('[Risk] Invalid base quantity provided');
                    return 1; // Safe default
                }
                
                // Get account phase if metrics provided
                let phaseRule = null;
                if (accountMetrics) {
                    phaseRule = this.determineAccountPhase(accountName, accountMetrics);
                } else {
                    // Try to get phase from current table data
                    try {
                        const tableData = typeof getTableData === 'function' ? getTableData() : [];
                        const accountRow = tableData.find(row => 
                            row.accountName && row.accountName.includes(accountName)
                        );
                        if (accountRow) {
                            phaseRule = this.determineAccountPhase(accountName, {
                                totalAvail: accountRow.totalAvail,
                                distDraw: accountRow.distDraw
                            });
                        }
                    } catch (e) {
                        console.warn('[Risk] Could not get current account data:', e);
                    }
                }
                
                if (!phaseRule) {
                    console.warn('[Risk] No phase rule found, using base quantity');
                    return Math.max(1, Math.min(baseQuantity, 1000)); // Hard limit
                }
                
                // Apply phase-based sizing
                let adjustedQuantity = baseQuantity;
                
                // Use phase-specific quantity if defined
                if (phaseRule.quantity !== undefined && phaseRule.quantity > 0) {
                    adjustedQuantity = phaseRule.quantity;
                }
                
                // Apply reduction factor for high-risk phases
                if (phaseRule.reduceFactor && phaseRule.reduceFactor < 1) {
                    adjustedQuantity = Math.floor(adjustedQuantity * phaseRule.reduceFactor);
                }
                
                // Enforce limits
                adjustedQuantity = Math.max(1, Math.min(adjustedQuantity, 1000));
                
                console.log(`[Risk] Position size calculated: ${baseQuantity} -> ${adjustedQuantity} (phase ${phaseRule.phase})`);
                return adjustedQuantity;
                
            } catch (error) {
                console.error('[Risk] Error calculating position size:', error);
                return Math.max(1, Math.min(baseQuantity || 1, 1000)); // Safe fallback
            }
        },
        
        /**
         * Determine account phase based on metrics
         * Consolidates phase determination logic
         */
        determineAccountPhase: function(accountName, metrics) {
            try {
                if (!accountName || !metrics) {
                    return { phase: 'Unknown', maxActive: 0, quantity: 1 };
                }
                
                const { totalAvail, distDraw } = metrics;
                
                // Helper function for numeric comparisons
                const compareNumeric = (value, operator, compareValue) => {
                    const ops = {
                        '<': (a, b) => a < b,
                        '<=': (a, b) => a <= b,
                        '>': (a, b) => a > b,
                        '>=': (a, b) => a >= b,
                        '==': (a, b) => a == b,
                        '!=': (a, b) => a != b
                    };
                    return ops[operator]?.(value, compareValue) ?? false;
                };
                
                // Find matching rule
                const matchesRule = (rule) => {
                    if (rule.accountNameIncludes && !accountName.includes(rule.accountNameIncludes)) {
                        return false;
                    }
                    
                    const totalAvailMatch = rule.totalAvailOperator
                        ? compareNumeric(totalAvail, rule.totalAvailOperator, rule.totalAvailValue)
                        : true;
                        
                    const distDrawMatch = rule.distDrawOperator
                        ? compareNumeric(distDraw, rule.distDrawOperator, rule.distDrawValue)
                        : true;
                    
                    return rule.useOr && rule.totalAvailOperator && rule.distDrawOperator
                        ? (totalAvailMatch || distDrawMatch)
                        : (totalAvailMatch && distDrawMatch);
                };
                
                // Special case for PAAPEX
                if (accountName.includes('PAAPEX')) {
                    return phaseCriteria.find(r => r.accountNameIncludes === 'PAAPEX') || 
                           { phase: 'Unknown', maxActive: 0, quantity: 1 };
                }
                
                // Find matching rule
                const rule = phaseCriteria.find(matchesRule) || 
                            { phase: 'Unknown', maxActive: 0, quantity: 1 };
                
                console.log(`[Risk] Account ${accountName} determined as Phase ${rule.phase}`);
                return rule;
                
            } catch (error) {
                console.error('[Risk] Error determining account phase:', error);
                return { phase: 'Unknown', maxActive: 0, quantity: 1 };
            }
        },
        
        /**
         * Validate order against risk limits
         * Consolidates validation logic from OrderValidationFramework
         */
        validateOrderRisk: function(orderData, accountName = null, accountMetrics = null) {
            const errors = [];
            const warnings = [];
            
            try {
                // Basic quantity validation
                const quantity = Number(orderData.qty || orderData.quantity || 0);
                if (quantity <= 0) {
                    errors.push('Quantity must be greater than 0');
                }
                if (quantity > 1000) {
                    errors.push('Quantity exceeds maximum limit (1000)');
                }
                
                // Account-specific validation
                if (accountName && accountMetrics) {
                    const phaseRule = this.determineAccountPhase(accountName, accountMetrics);
                    
                    // Check against phase-specific limits
                    if (phaseRule.quantity && quantity > phaseRule.quantity) {
                        warnings.push(`Quantity (${quantity}) exceeds recommended size for Phase ${phaseRule.phase} (${phaseRule.quantity})`);
                    }
                    
                    // Check for high-risk phase
                    if (phaseRule.reduceFactor && phaseRule.reduceFactor < 1) {
                        warnings.push(`Account in high-risk Phase ${phaseRule.phase} - position size reduced by ${Math.round((1 - phaseRule.reduceFactor) * 100)}%`);
                    }
                }
                
                return {
                    valid: errors.length === 0,
                    errors: errors,
                    warnings: warnings
                };
                
            } catch (error) {
                console.error('[Risk] Error validating order risk:', error);
                return {
                    valid: false,
                    errors: ['Risk validation failed'],
                    warnings: []
                };
            }
        }
    };

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
        console.log('🔍 DOM Intelligence: Starting performAccountActions with validation');
        
        // STEP 1: Pre-validation - Check if account dropdown exists
        const dropdownSelector = '.pane.account-selector.dropdown [data-toggle="dropdown"]';
        console.log('🔍 Pre-validation: Checking for account dropdown');
        
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
        
        // Step 1: Open settings by clicking the dropdown toggle
        dropdown.click();
        console.log('✅ Clicked account dropdown');

        // Step 2: After 500ms, click the gear in the "Account group" entry
        setTimeout(() => {
            console.log('🔍 Pre-validation: Checking for dropdown menu items');
            
            const menuItemsSelector = '.dropdown-menu li a.account';
            if (!window.domHelpers.validateElementExists(menuItemsSelector)) {
                console.error('❌ Pre-validation failed: Dropdown menu items not found');
                return;
            }
            
            let gearFound = false;
            document.querySelectorAll(menuItemsSelector).forEach(item => {
                if (item.textContent.includes('Account group')) {
                    console.log('✅ Found Account group menu item');
                    const gear = item.querySelector('.btn.btn-icon');
                    if (gear) {
                        if (window.domHelpers.validateElementVisible(gear)) {
                            gear.click();
                            gearFound = true;
                            console.log('✅ Clicked gear button in Account group');
                        } else {
                            console.error('❌ Gear button not visible');
                        }
                    } else {
                        console.error('❌ Gear button not found in Account group item');
                    }
                }
            });
            
            if (!gearFound) {
                console.error('❌ Could not find or click Account group gear');
                return;
            }

            // After clicking gear, move active left->right and inactive right->left, then set quantities
            setTimeout(() => {
                console.log('🔍 Pre-validation: Checking for configurator containers');
                
                const containerSelector = '.columns-configurator--container';
                const containers = document.querySelectorAll(containerSelector);
                
                if (containers.length < 2) {
                    console.error(`❌ Pre-validation failed: Need 2 configurator containers, found ${containers.length}`);
                    return;
                }
                
                const leftList = containers[0].querySelector('.sortable-list');
                const rightList = containers[1].querySelector('.sortable-list');
                
                if (!leftList || !rightList) {
                    console.error('❌ Pre-validation failed: Sortable lists not found in containers');
                    return;
                }
                
                console.log('✅ Pre-validation passed: Found both sortable lists');
                
                const tableData = getTableData();
                const map = {};
                tableData.forEach(row => {
                    const name = row["Account ▲"] || row["Account"];
                    map[name] = row;
                });

                // Move active from left->right
                leftList.querySelectorAll('[draggable="true"]').forEach(item => {
                    const name = item.textContent.trim().split('\n')[0];
                    if (map[name]?.active) {
                        console.log(`🔍 Moving active account ${name} left->right`);
                        simulateDragAndDrop(item, rightList);
                    }
                });

                // Move inactive from right->left
                rightList.querySelectorAll('[draggable="true"]').forEach(item => {
                    const name = item.textContent.trim().split('\n')[0];
                    if (!map[name]?.active) {
                        console.log(`🔍 Moving inactive account ${name} right->left`);
                        simulateDragAndDrop(item, leftList);
                    }
                });

                // Set quantities based on phase, then update total and master quantity
                setTimeout(() => {
                    console.log('🔍 Setting quantities with validation');
                    const setQuantitiesSuccess = setQuantities();
                    const total = calculateTotalQuantity();
                    
                    console.log(`🔍 Calculated total quantity: ${total}`);

                    // STEP 3: Pre-validation - Check for Save button
                    console.log('🔍 Pre-validation: Checking for Save button');
                    const saveBtnSelector = '.modal-footer .btn.btn-primary';
                    const saveBtn = document.querySelector(saveBtnSelector);
                    
                    if (saveBtn && window.domHelpers.validateElementVisible(saveBtn)) {
                        console.log('✅ Save button found and visible, clicking');
                        saveBtn.click();
                    } else {
                        console.warn('⚠️ Save button not found or not visible');
                    }

                    // After saving, OK/Close if present, then update master quantity
                    setTimeout(() => {
                        console.log('🔍 Pre-validation: Checking for OK button');
                        const okBtn = Array.from(document.querySelectorAll('.modal-footer .btn'))
                        .find(btn => btn.textContent.trim() === 'OK');
                        
                        if (okBtn && window.domHelpers.validateElementVisible(okBtn)) {
                            console.log('✅ OK button found and visible, clicking');
                            okBtn.click();
                        } else {
                            console.warn('⚠️ OK button not found or not visible');
                        }

                        setTimeout(() => {
                            console.log('🔍 Pre-validation: Checking for Close button');
                            const closeBtn = Array.from(document.querySelectorAll('.modal-header .close, .modal-footer .btn'))
                            .find(btn => btn.textContent.trim() === 'Close');
                            
                            if (closeBtn && window.domHelpers.validateElementVisible(closeBtn)) {
                                console.log('✅ Close button found and visible, clicking');
                                closeBtn.click();
                            } else {
                                console.warn('⚠️ Close button not found or not visible');
                            }

                            setTimeout(() => {
                                console.log('🔍 Updating master quantity with validation');
                                const updateSuccess = updateMasterQuantity(total);
                                console.log(`🔍 DOM Intelligence: performAccountActions completed. SetQuantities: ${setQuantitiesSuccess}, UpdateMaster: ${updateSuccess}`);
                            }, 500);
                        }, 500);
                    }, 500);
                }, 500);
            }, 500);
        }, 500);
        
        return true;
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
        console.log('🔍 DOM Intelligence: Starting setQuantities with form field validation');
        
        // STEP 1: Pre-validation - Check if the sortable container exists
        const containerSelector = '.columns-configurator--container';
        if (!window.domHelpers.validateElementExists(containerSelector)) {
            console.error('❌ Pre-validation failed: columns-configurator--container not found');
            return false;
        }
        
        const containers = document.querySelectorAll(containerSelector);
        if (containers.length < 2) {
            console.error('❌ Pre-validation failed: Need at least 2 containers, found', containers.length);
            return false;
        }
        
        const added = containers[1].querySelector('.sortable-list');
        if (!added) {
            console.error('❌ Pre-validation failed: Sortable list not found in second container');
            return false;
        }
        
        console.log('✅ Pre-validation passed: Found sortable containers and list');
        
        const tableData = getTableData();
        const phaseByAccount = {};
        tableData.forEach(r => {
            const key = r["Account ▲"] || r["Account"];
            phaseByAccount[key] = r.phase;
        });

        let processedCount = 0;
        let errorCount = 0;
        
        // STEP 2: Process each sortable list item with form field validation
        added.querySelectorAll('.sortable-list-item').forEach((item, index) => {
            const accountName = item.textContent.trim().split('\n')[0];
            const qty = getPhaseQuantity(phaseByAccount[accountName]);
            
            console.log(`🔍 Processing item ${index + 1}: ${accountName} -> quantity ${qty}`);
            
            // STEP 3: Pre-validation - Check if form control input exists
            const inputSelector = 'input.form-control';
            const input = item.querySelector(inputSelector);
            
            if (!input) {
                console.error(`❌ Form field not found for ${accountName}: ${inputSelector}`);
                errorCount++;
                return;
            }
            
            // STEP 4: Pre-validation - Check if input is visible and enabled
            if (!window.domHelpers.validateElementVisible(input)) {
                console.error(`❌ Form field not visible for ${accountName}`);
                errorCount++;
                return;
            }
            
            if (input.disabled) {
                console.warn(`⚠️ Form field disabled for ${accountName}, skipping`);
                return;
            }
            
            console.log(`✅ Pre-validation passed for ${accountName} form field`);
            
            // STEP 5: Set the form field value
            try {
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(input, qty);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                
                // STEP 6: Post-validation - Verify the value was set correctly
                setTimeout(() => {
                    if (window.domHelpers.validateFormFieldValue(input, qty.toString())) {
                        console.log(`✅ Successfully set ${accountName} quantity to ${qty}`);
                    } else {
                        console.error(`❌ Post-validation failed: ${accountName} quantity not set correctly`);
                        errorCount++;
                    }
                }, 100);
                
                processedCount++;
                
            } catch (error) {
                console.error(`❌ Error setting form field for ${accountName}:`, error.message);
                errorCount++;
            }
        });
        
        // STEP 7: Summary validation results
        console.log(`🔍 DOM Intelligence: setQuantities completed`);
        console.log(`📊 Summary: ${processedCount} fields processed, ${errorCount} errors`);
        
        return errorCount === 0;
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
        console.log('🔍 DOM Intelligence: Starting updateMasterQuantity with form field validation');
        console.log(`🔍 Target total quantity: ${total}`);
        
        let successCount = 0;
        let errorCount = 0;
        
        // STEP 1: Update master quantity field
        console.log('🔍 Pre-validation: Checking for master quantity field');
        const masterSelector = 'input.form-control[placeholder="Select value"]';
        const masterInput = document.querySelector(masterSelector);
        
        if (masterInput) {
            console.log('✅ Master quantity field found');
            
            // Pre-validation checks
            if (!window.domHelpers.validateElementVisible(masterInput)) {
                console.error('❌ Master quantity field not visible');
                errorCount++;
            } else if (masterInput.disabled) {
                console.warn('⚠️ Master quantity field is disabled');
                errorCount++;
            } else {
                try {
                    // Set the value
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(masterInput, total);
                    masterInput.dispatchEvent(new Event('input', { bubbles: true }));
                    masterInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Post-validation - verify value was set
                    setTimeout(() => {
                        if (window.domHelpers.validateFormFieldValue(masterInput, total.toString())) {
                            console.log('✅ Master quantity field updated successfully to', total);
                        } else {
                            console.error('❌ Post-validation failed: Master quantity field value not set correctly');
                            errorCount++;
                        }
                    }, 100);
                    
                    successCount++;
                } catch (error) {
                    console.error('❌ Error updating master quantity field:', error.message);
                    errorCount++;
                }
            }
        } else {
            console.warn('⚠️ Master quantity field not found, skipping');
        }
        
        // STEP 2: Update bracket quantity field
        console.log('🔍 Pre-validation: Checking for bracket quantity field');
        const bracketSelector = '#qtyInput';
        const bracketQtyInput = document.getElementById('qtyInput');
        
        if (bracketQtyInput) {
            console.log('✅ Bracket quantity field found');
            
            // Pre-validation checks
            if (!window.domHelpers.validateElementVisible(bracketQtyInput)) {
                console.error('❌ Bracket quantity field not visible');
                errorCount++;
            } else if (bracketQtyInput.disabled) {
                console.warn('⚠️ Bracket quantity field is disabled');
                errorCount++;
            } else {
                try {
                    // Set the value
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(bracketQtyInput, total);
                    bracketQtyInput.dispatchEvent(new Event('input', { bubbles: true }));
                    bracketQtyInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Post-validation - verify value was set
                    setTimeout(() => {
                        if (window.domHelpers.validateFormFieldValue(bracketQtyInput, total.toString())) {
                            console.log('✅ Bracket quantity field updated successfully to', total);
                        } else {
                            console.error('❌ Post-validation failed: Bracket quantity field value not set correctly');
                            errorCount++;
                        }
                    }, 100);
                    
                    successCount++;
                } catch (error) {
                    console.error('❌ Error updating bracket quantity field:', error.message);
                    errorCount++;
                }
            }
        } else {
            console.warn('⚠️ Bracket quantity field not found, skipping');
        }
        
        // STEP 3: Summary validation results
        console.log('🔍 DOM Intelligence: updateMasterQuantity completed');
        console.log(`📊 Summary: ${successCount} fields updated, ${errorCount} errors`);
        
        return errorCount === 0;
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