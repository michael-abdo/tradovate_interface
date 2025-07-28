// ==UserScript==
// @name         Enhanced Account Table Data Extractor
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Extract account data with DOM Intelligence System integration
// @match        https://trader.tradovate.com/*
// @require      file:///Users/Mike/trading/scripts/tampermonkey/dom_intelligence_client.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    // Create DOM Intelligence client for this script
    const domClient = new DOMIntelligenceClient({
        scriptName: 'enhanced_account_data',
        debugMode: localStorage.getItem('account_data_debug') === 'true'
    });
    
    // Enhanced account data extraction with DOM Intelligence
    async function getAllAccountTableDataEnhanced() {
        const startTime = performance.now();
        const result = {
            timestamp: new Date().toISOString(),
            method: 'enhanced',
            data: [],
            performance: {},
            errors: [],
            warnings: []
        };
        
        try {
            // Use DOM Intelligence to find the market data table
            const table = await domClient.findElement('market_data_table', {
                timeout: 10000,
                checkVisibility: true
            });
            
            if (!table) {
                throw new Error('Market data table not found');
            }
            
            // Extract comprehensive table data using DOM Intelligence
            const tableData = await domClient.extractData('market_data_table', {
                includeHeaders: true,
                validateData: true
            });
            
            // Process the extracted data with enhanced logic
            result.data = processAccountTableData(tableData, result);
            
            // Record performance metrics
            result.performance = {
                totalDuration: performance.now() - startTime,
                rowsProcessed: result.data.length,
                domIntelligenceReport: domClient.getPerformanceReport()
            };
            
            // Validate data quality
            validateDataQuality(result.data, result);
            
        } catch (error) {
            result.errors.push({
                type: 'extraction_error',
                message: error.message,
                timestamp: new Date().toISOString()
            });
            
            // Fallback to traditional method if DOM Intelligence fails
            console.warn('DOM Intelligence extraction failed, falling back to traditional method');
            try {
                result.data = await getAllAccountTableDataTraditional();
                result.method = 'fallback';
                result.warnings.push('Used fallback extraction method due to DOM Intelligence failure');
            } catch (fallbackError) {
                result.errors.push({
                    type: 'fallback_error',
                    message: fallbackError.message,
                    timestamp: new Date().toISOString()
                });
            }
        }
        
        return result;
    }
    
    // Process raw table data into structured account information
    function processAccountTableData(tableData, result) {
        if (!tableData || !tableData.rows) {
            throw new Error('Invalid table data structure');
        }
        
        const accounts = [];
        
        // Enhanced header mapping with more robust detection
        const headerMapping = {
            'Account': ['Account', 'Acct', 'Account Name', 'Account ▲', 'Account ▼'],
            'Open P&L': ['Dollar Open P L', 'Open P&L', 'Open PnL', 'Open P/L', 'Unrealized P&L'],
            'Net Liquidation': ['Dist Drawdown Net Liq', 'Net Liquidation', 'Net Liq', 'Total Value'],
            'Available Margin': ['Total Available Margin', 'Available Margin', 'Margin Available', 'Avail Margin'],
            'Phase': ['User', 'Phase', 'Trading Phase', 'Account Phase'],
            'Total P&L': ['Dollar Total P L', 'Total P&L', 'Total PnL', 'Total P/L', 'Realized P&L'],
            'Strategy': ['Strategy', 'Trading Strategy', 'Strat']
        };
        
        // Create reverse mapping for header detection
        const reverseHeaderMapping = {};
        Object.entries(headerMapping).forEach(([standardName, variations]) => {
            variations.forEach(variation => {
                // Clean variation for comparison
                const cleanVariation = variation.replace(/[\u25b2\u25bc\s]/g, '').toLowerCase();
                reverseHeaderMapping[cleanVariation] = standardName;
            });
        });
        
        // Map actual headers to standard names
        const standardHeaders = tableData.headers.map(header => {
            const cleanHeader = header.replace(/[\u25b2\u25bc\s]/g, '').toLowerCase();
            return reverseHeaderMapping[cleanHeader] || header;
        });
        
        // Process each row
        tableData.rows.forEach((row, rowIndex) => {
            try {
                const accountData = {};
                
                // Extract data using standard headers
                standardHeaders.forEach((standardHeader, colIndex) => {
                    const cellValue = Object.values(row)[colIndex] || '';
                    accountData[standardHeader] = processCellValue(cellValue, standardHeader);
                });
                
                // Enhanced account processing
                enhanceAccountData(accountData, result);
                
                // Validate required fields
                if (accountData.Account && accountData.Account.trim() !== '') {
                    accounts.push(accountData);
                } else {
                    result.warnings.push(`Row ${rowIndex + 1}: Missing or empty account name`);
                }
                
            } catch (rowError) {
                result.errors.push({
                    type: 'row_processing_error',
                    message: `Row ${rowIndex + 1}: ${rowError.message}`,
                    rowData: row
                });
            }
        });
        
        return accounts;
    }
    
    // Process individual cell values with type conversion and validation
    function processCellValue(value, columnType) {
        if (!value || typeof value !== 'string') {
            return value;
        }
        
        const trimmedValue = value.trim();
        
        // Currency value processing
        if (trimmedValue.startsWith('$') || trimmedValue.startsWith('-$')) {
            try {
                const numericValue = trimmedValue.replace(/[$,]/g, '');
                const parsed = parseFloat(numericValue);
                return isNaN(parsed) ? trimmedValue : parsed;
            } catch (e) {
                console.warn(`Currency conversion error for value: ${trimmedValue}`);
                return trimmedValue;
            }
        }
        
        // Percentage processing
        if (trimmedValue.endsWith('%')) {
            try {
                const numericValue = trimmedValue.replace('%', '');
                const parsed = parseFloat(numericValue);
                return isNaN(parsed) ? trimmedValue : parsed / 100;
            } catch (e) {
                return trimmedValue;
            }
        }
        
        // Numeric processing for other numeric columns
        if (['Available Margin', 'Net Liquidation'].includes(columnType)) {
            const numericValue = parseFloat(trimmedValue.replace(/[,$]/g, ''));
            return isNaN(numericValue) ? trimmedValue : numericValue;
        }
        
        return trimmedValue;
    }
    
    // Enhance account data with additional derived information
    function enhanceAccountData(accountData, result) {
        // Enhanced phase and status parsing
        if (accountData.Phase) {
            const phaseText = accountData.Phase.toString().toLowerCase();
            
            // Extract status
            if (phaseText.includes('active')) {
                accountData.Status = phaseText.includes('inactive') ? 'Inactive' : 'Active';
            } else {
                accountData.Status = 'Unknown';
                result.warnings.push(`Unknown phase status for account ${accountData.Account}: ${accountData.Phase}`);
            }
            
            // Extract phase number
            const phaseMatch = accountData.Phase.toString().match(/(\\d+)/);
            if (phaseMatch) {
                accountData.PhaseNumber = parseInt(phaseMatch[1]);
                accountData.Phase = phaseMatch[1]; // Clean phase display
            }
        }
        
        // Enhanced platform detection
        const accountName = accountData.Account || '';
        accountData.Platform = detectTradingPlatform(accountName);
        
        // Risk assessment
        if (typeof accountData['Open P&L'] === 'number' && typeof accountData['Net Liquidation'] === 'number') {
            const openPnL = accountData['Open P&L'];
            const netLiq = accountData['Net Liquidation'];
            
            if (netLiq > 0) {
                const riskPercentage = Math.abs(openPnL) / netLiq;
                accountData.RiskPercentage = riskPercentage;
                
                // Risk level classification
                if (riskPercentage > 0.05) {
                    accountData.RiskLevel = 'High';
                } else if (riskPercentage > 0.02) {
                    accountData.RiskLevel = 'Medium';
                } else {
                    accountData.RiskLevel = 'Low';
                }
            }
        }
        
        // Performance metrics
        if (typeof accountData['Total P&L'] === 'number' && typeof accountData['Net Liquidation'] === 'number') {
            const totalPnL = accountData['Total P&L'];
            const netLiq = accountData['Net Liquidation'];
            
            if (netLiq > 0) {
                accountData.ROI = totalPnL / netLiq;
            }
        }
        
        // Account health score (0-100)
        accountData.HealthScore = calculateAccountHealthScore(accountData);
    }
    
    // Detect trading platform based on account name patterns
    function detectTradingPlatform(accountName) {
        const accountNameLower = accountName.toString().toLowerCase();
        
        const platformPatterns = {
            'Tradovate': ['demo', 'tv', 'tradovate', 'live', 'sim'],
            'Apex': ['apex', 'pa', 'prop'],
            'AMP': ['amp', 'advantage'],
            'NinjaTrader': ['ninja', 'nt'],
            'TT': ['tt', 'trading tech'],
            'TrailingTie': ['trailing', 'tie'],
            'TopStep': ['topstep', 'ts'],
            'OneUp': ['oneup', '1up'],
            'FTMO': ['ftmo'],
            'MyForexFunds': ['mff', 'myforex']
        };
        
        for (const [platform, patterns] of Object.entries(platformPatterns)) {
            if (patterns.some(pattern => accountNameLower.includes(pattern))) {
                return platform;
            }
        }
        
        return 'Unknown';
    }
    
    // Calculate account health score based on multiple factors
    function calculateAccountHealthScore(accountData) {
        let score = 50; // Base score
        
        // Status factor
        if (accountData.Status === 'Active') {
            score += 20;
        } else if (accountData.Status === 'Inactive') {
            score -= 10;
        }
        
        // P&L factor
        if (typeof accountData['Open P&L'] === 'number') {
            const openPnL = accountData['Open P&L'];
            if (openPnL > 0) {
                score += 15;
            } else if (openPnL < 0) {
                score -= Math.min(20, Math.abs(openPnL) / 1000 * 5); // Deduct based on loss amount
            }
        }
        
        // Risk factor
        if (accountData.RiskLevel === 'Low') {
            score += 10;
        } else if (accountData.RiskLevel === 'High') {
            score -= 15;
        }
        
        // Available margin factor
        if (typeof accountData['Available Margin'] === 'number') {
            const margin = accountData['Available Margin'];
            if (margin > 10000) {
                score += 10;
            } else if (margin < 1000) {
                score -= 10;
            }
        }
        
        // Ensure score is within 0-100 range
        return Math.max(0, Math.min(100, Math.round(score)));
    }
    
    // Validate data quality and add warnings/errors
    function validateDataQuality(accounts, result) {
        if (!Array.isArray(accounts) || accounts.length === 0) {
            result.warnings.push('No account data extracted');
            return;
        }
        
        // Check for duplicate accounts
        const accountNames = accounts.map(acc => acc.Account);
        const duplicates = accountNames.filter((name, index) => accountNames.indexOf(name) !== index);
        if (duplicates.length > 0) {
            result.warnings.push(`Duplicate accounts found: ${[...new Set(duplicates)].join(', ')}`);
        }
        
        // Check data completeness
        const requiredFields = ['Account', 'Status'];
        const incompleteAccounts = accounts.filter(acc => 
            requiredFields.some(field => !acc[field] || acc[field] === '')
        );
        
        if (incompleteAccounts.length > 0) {
            result.warnings.push(`${incompleteAccounts.length} accounts have incomplete data`);
        }
        
        // Check for suspicious values
        accounts.forEach((acc, index) => {
            if (typeof acc['Net Liquidation'] === 'number' && acc['Net Liquidation'] < 0) {
                result.warnings.push(`Account ${acc.Account} has negative net liquidation`);
            }
            
            if (acc.HealthScore < 30) {
                result.warnings.push(`Account ${acc.Account} has low health score: ${acc.HealthScore}`);
            }
        });
    }
    
    // Traditional extraction method as fallback
    async function getAllAccountTableDataTraditional() {
        // Try multiple selectors to find account tables
        const tableSelectors = ['.public_fixedDataTable_main', '.module.positions.data-table'];
        let tables = [];
        
        for (const selector of tableSelectors) {
            const foundTables = document.querySelectorAll(selector);
            if (foundTables.length > 0) {
                console.log(`✅ Found ${foundTables.length} tables with selector: ${selector}`);
                tables = foundTables;
                break;
            } else {
                console.warn(`❌ No tables found with selector: ${selector}`);
            }
        }
        
        let accountTable = null;
        for (let i = 0; i < tables.length; i++) {
            const table = tables[i];
            const headers = [...table.querySelectorAll('[role="columnheader"]')].map(h => 
                h.textContent.trim()
            );
            
            if (headers.includes('Account ▲') || headers.includes('Total Available Margin')) {
                accountTable = table;
                break;
            }
        }
        
        if (!accountTable) {
            throw new Error('Account table not found using traditional method');
        }
        
        // Extract using traditional method (simplified)
        const headers = [...accountTable.querySelectorAll('[role="columnheader"]')];
        const headerNames = headers.map(h => h.textContent.replace(/[\u25b2\u25bc]/g, '').trim());
        const rows = [...accountTable.querySelectorAll('.public_fixedDataTable_bodyRow')];
        
        return rows.map(r => {
            const cells = r.querySelectorAll('[role="gridcell"]');
            const rowData = {};
            
            headerNames.forEach((name, idx) => {
                if (idx < cells.length) {
                    rowData[name] = cells[idx]?.innerText?.trim() || '';
                }
            });
            
            return rowData;
        });
    }
    
    // Create monitoring dashboard
    function createAccountDataDashboard() {
        // Remove existing dashboard
        const existingDashboard = document.getElementById('account-data-dashboard');
        if (existingDashboard) {
            existingDashboard.remove();
        }
        
        // Create dashboard container
        const dashboard = document.createElement('div');
        dashboard.id = 'account-data-dashboard';
        dashboard.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            width: 350px;
            max-height: 60vh;
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            border: 2px solid #4a5568;
            border-radius: 10px;
            padding: 15px;
            z-index: 10000;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            overflow-y: auto;
        `;
        
        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 15px;
            text-align: center;
            color: #f7fafc;
            border-bottom: 1px solid #4a5568;
            padding-bottom: 8px;
        `;
        header.textContent = 'Enhanced Account Data Monitor';
        
        // Control buttons
        const controls = document.createElement('div');
        controls.style.cssText = `
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
        `;
        
        const extractButton = document.createElement('button');
        extractButton.textContent = 'Extract Data';
        extractButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #48bb78;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
            transition: background 0.2s;
        `;
        
        const exportButton = document.createElement('button');
        exportButton.textContent = 'Export JSON';
        exportButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #4299e1;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
        `;
        
        const clearButton = document.createElement('button');
        clearButton.textContent = 'Clear';
        clearButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #f56565;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
        `;
        
        // Results display
        const resultsDisplay = document.createElement('div');
        resultsDisplay.id = 'account-results';
        resultsDisplay.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            padding: 10px;
            max-height: 35vh;
            overflow-y: auto;
            font-size: 10px;
            line-height: 1.4;
        `;
        
        // Event handlers
        extractButton.addEventListener('click', async () => {
            extractButton.disabled = true;
            extractButton.textContent = 'Extracting...';
            
            try {
                const results = await getAllAccountTableDataEnhanced();
                displayAccountResults(results, resultsDisplay);
                
                // Store latest results for export
                dashboard._latestResults = results;
                
            } catch (error) {
                resultsDisplay.innerHTML = `<span style="color: #f56565;">Error: ${error.message}</span>`;
            } finally {
                extractButton.disabled = false;
                extractButton.textContent = 'Extract Data';
            }
        });
        
        exportButton.addEventListener('click', () => {
            if (dashboard._latestResults) {
                const dataUrl = 'data:application/json;charset=utf-8,' + 
                    encodeURIComponent(JSON.stringify(dashboard._latestResults, null, 2));
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = `account_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                link.click();
            } else {
                alert('No data to export. Extract data first.');
            }
        });
        
        clearButton.addEventListener('click', () => {
            resultsDisplay.innerHTML = '<span style="color: #a0aec0;">Click "Extract Data" to start...</span>';
            dashboard._latestResults = null;
        });
        
        // Assemble dashboard
        controls.appendChild(extractButton);
        controls.appendChild(exportButton);
        controls.appendChild(clearButton);
        
        dashboard.appendChild(header);
        dashboard.appendChild(controls);
        dashboard.appendChild(resultsDisplay);
        
        // Initial message
        resultsDisplay.innerHTML = '<span style="color: #a0aec0;">Enhanced Account Data Monitor Ready. Click "Extract Data" to start...</span>';
        
        document.body.appendChild(dashboard);
        
        // Make draggable
        makeDraggable(dashboard, header);
        
        return dashboard;
    }
    
    // Display account extraction results
    function displayAccountResults(results, container) {
        let html = '';
        
        // Status summary
        const statusColor = results.errors.length > 0 ? '#f56565' : '#48bb78';
        html += `<div style="margin-bottom: 10px;">
            <span style="color: ${statusColor}; font-weight: bold;">● Status: ${results.errors.length > 0 ? 'ERRORS' : 'SUCCESS'}</span>
            <div style="font-size: 9px; color: #a0aec0;">Method: ${results.method}, Duration: ${results.performance?.totalDuration?.toFixed(1)}ms</div>
        </div>`;
        
        // Account summary
        if (results.data && results.data.length > 0) {
            const totalAccounts = results.data.length;
            const activeAccounts = results.data.filter(acc => acc.Status === 'Active').length;
            const totalPnL = results.data.reduce((sum, acc) => sum + (acc['Total P&L'] || 0), 0);
            const totalNetLiq = results.data.reduce((sum, acc) => sum + (acc['Net Liquidation'] || 0), 0);
            
            html += `<div style="margin-bottom: 10px; padding: 8px; background: rgba(72, 187, 120, 0.1); border-radius: 5px;">
                <div style="font-weight: bold; color: #68d391;">Account Summary:</div>
                <div>Total: ${totalAccounts} (${activeAccounts} active)</div>
                <div>Total P&L: $${totalPnL.toLocaleString()}</div>
                <div>Total Net Liq: $${totalNetLiq.toLocaleString()}</div>
            </div>`;
            
            // Account details
            html += `<div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #e2e8f0; margin-bottom: 5px;">Accounts:</div>`;
            
            results.data.forEach(account => {
                const healthColor = account.HealthScore >= 70 ? '#48bb78' : account.HealthScore >= 40 ? '#ed8936' : '#f56565';
                const statusColor = account.Status === 'Active' ? '#48bb78' : '#a0aec0';
                
                html += `<div style="margin-bottom: 5px; padding: 5px; background: rgba(0,0,0,0.2); border-radius: 3px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold;">${account.Account}</span>
                        <span style="color: ${statusColor}; font-size: 9px;">${account.Status}</span>
                    </div>
                    <div style="font-size: 9px; display: flex; justify-content: space-between;">
                        <span>Platform: ${account.Platform}</span>
                        <span style="color: ${healthColor};">Health: ${account.HealthScore}</span>
                    </div>
                    <div style="font-size: 9px;">
                        Open P&L: $${(account['Open P&L'] || 0).toLocaleString()} | 
                        Net Liq: $${(account['Net Liquidation'] || 0).toLocaleString()}
                    </div>
                </div>`;
            });
            html += `</div>`;
        }
        
        // Warnings and errors
        if (results.warnings && results.warnings.length > 0) {
            html += `<div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #ed8936; margin-bottom: 5px;">Warnings:</div>`;
            results.warnings.forEach(warning => {
                html += `<div style="margin-left: 10px; font-size: 9px; color: #ed8936;">• ${warning}</div>`;
            });
            html += `</div>`;
        }
        
        if (results.errors && results.errors.length > 0) {
            html += `<div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #f56565; margin-bottom: 5px;">Errors:</div>`;
            results.errors.forEach(error => {
                html += `<div style="margin-left: 10px; font-size: 9px; color: #f56565;">• ${error.message}</div>`;
            });
            html += `</div>`;
        }
        
        container.innerHTML = html;
    }
    
    // Utility function to make elements draggable
    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        handle.style.cursor = 'move';
        handle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
    
    // Initialize dashboard when page is ready
    function initialize() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(createAccountDataDashboard, 1500);
            });
        } else {
            setTimeout(createAccountDataDashboard, 1500);
        }
    }
    
    // Make functions available globally
    window.getAllAccountTableDataEnhanced = getAllAccountTableDataEnhanced;
    window.getAllAccountTableDataTraditional = getAllAccountTableDataTraditional;
    
    // Start initialization
    initialize();
    
    console.log('[Enhanced Account Data] Loaded with DOM Intelligence integration');
    
})();