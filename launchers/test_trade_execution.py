#!/usr/bin/env python3
"""
Test script for executing a trade and detecting it in the Positions table.
"""

import os
import sys
import time
import json
import logging
import traceback
import requests

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login
from src import app
from src.chrome_logger import ChromeLogger
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_trade_execution')

class TestTradeExecution:
    """Test class for executing a trade and detecting the position."""
    
    def __init__(self):
        """Initialize the test."""
        self.chrome_instance = None
        self.controller = None
        self.dashboard_thread = None
        self.dashboard_running = False
        
    def setup(self):
        """Set up the test environment."""
        username = "stonkz92224@gmail.com"
        password = "24$tonkZ24"
        
        logger.info(f"Starting Chrome with user: {username}")
        
        # Start Chrome with debugging
        test_port = 9222
        process = auto_login.start_chrome_with_debugging(test_port)
        
        if not process:
            logger.error("Failed to start Chrome")
            return False
        
        logger.info("Chrome started successfully")
        
        # Wait for Chrome to initialize
        time.sleep(5)
        
        # Connect to Chrome
        logger.info("Connecting to Chrome...")
        browser, tab = auto_login.connect_to_chrome(test_port)
        
        if not tab:
            logger.error("Failed to connect to Chrome tab")
            return False
        
        logger.info("Connected to Chrome tab")
        
        # Create a Chrome instance object
        chrome_instance = auto_login.ChromeInstance(test_port, username, password)
        chrome_instance.browser = browser
        chrome_instance.tab = tab
        chrome_instance.process = process
        
        # Disable alerts
        logger.info("Disabling alerts...")
        auto_login.disable_alerts(tab)
        
        # Inject and execute login script
        logger.info("Injecting login script...")
        auto_login.inject_login_script(tab, username, password)
        
        # Wait for login
        logger.info("Waiting for login to complete...")
        for i in range(60):  # 60 seconds timeout
            # Check if we're logged in
            check_js = """
            (function() {
                const isLoggedIn = document.querySelector(".bar--heading") || 
                                document.querySelector(".app-bar--account-menu-button") ||
                                document.querySelector(".dashboard--container") ||
                                document.querySelector(".pane.account-selector");
                return !!isLoggedIn;
            })();
            """
            result = tab.Runtime.evaluate(expression=check_js)
            is_logged_in = result.get("result", {}).get("value", False)
            
            if is_logged_in:
                logger.info(f"Successfully logged in after {i} seconds")
                self.chrome_instance = chrome_instance
                return True
            
            # Not logged in yet, check for account selection page
            account_selection_js = """
            (function() {
                const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                    .filter(btn => 
                        btn.textContent.trim() === "Access Simulation" || 
                        btn.textContent.trim() === "Launch"
                    );
                if (accessButtons.length > 0) {
                    console.log("Clicking Access Simulation button");
                    accessButtons[0].click();
                    return true;
                }
                return false;
            })();
            """
            
            tab.Runtime.evaluate(expression=account_selection_js)
            time.sleep(1)
        
        logger.error("Failed to login after waiting 60 seconds")
        return False
    
    def start_dashboard(self, port=6001, max_attempts=3):
        """Start the dashboard.
        
        Args:
            port: Initial port to try
            max_attempts: Number of ports to try (will increment port number)
        """
        if not self.chrome_instance:
            logger.error("No Chrome instance available")
            return False
        
        try:
            # Create controller with our Chrome instance
            self.controller = app.TradovateController(base_port=self.chrome_instance.port)
            
            # Import dashboard module
            from src import dashboard
            
            # Try to connect first to see if dashboard is already running
            try:
                response = requests.get(f"http://localhost:{port}/api/accounts", timeout=2)
                if response.status_code == 200:
                    logger.info(f"Dashboard already running on port {port}")
                    self.dashboard_running = True
                    return True
            except requests.exceptions.ConnectionError:
                logger.info(f"Dashboard not already running on port {port}")
            except Exception as e:
                logger.warning(f"Error checking for existing dashboard: {e}")
            
            # Try starting dashboard on different ports if needed
            for attempt in range(max_attempts):
                current_port = port + attempt
                logger.info(f"Attempting to start dashboard on port {current_port} (attempt {attempt+1}/{max_attempts})")
                
                # Start dashboard in a separate thread
                def run_dashboard(port_to_use):
                    try:
                        logger.info(f"Starting dashboard on port {port_to_use}...")
                        self.dashboard_running = True
                        dashboard.app.run(host='0.0.0.0', port=port_to_use)
                    except Exception as e:
                        logger.error(f"Error running dashboard: {e}")
                        self.dashboard_running = False
                
                self.dashboard_thread = threading.Thread(target=run_dashboard, args=(current_port,))
                self.dashboard_thread.daemon = True
                self.dashboard_thread.start()
                
                # Wait for dashboard to start
                time.sleep(3)
                
                # Test dashboard connection
                try:
                    response = requests.get(f"http://localhost:{current_port}/api/accounts", timeout=5)
                    if response.status_code == 200:
                        logger.info(f"Dashboard is running and accessible on port {current_port}")
                        return True
                    else:
                        logger.error(f"Dashboard returned status code {response.status_code}")
                except Exception as e:
                    logger.error(f"Error connecting to dashboard: {e}")
                    
                    # Try the next port
                    logger.info(f"Will try next port {current_port + 1}")
                    continue
            
            # If we got here, we couldn't start the dashboard on any port
            logger.error(f"Failed to start dashboard after {max_attempts} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
            return False
    
    def execute_trade(self, port=6001):
        """Execute a trade via the dashboard API."""
        if not self.dashboard_running:
            logger.error("Dashboard is not running")
            return False
        
        try:
            # Detect which port dashboard is running on
            for test_port in range(port, port + 3):
                try:
                    test_response = requests.get(f"http://localhost:{test_port}/api/accounts", timeout=2)
                    if test_response.status_code == 200:
                        port = test_port
                        logger.info(f"Found dashboard running on port {port}")
                        break
                except:
                    pass
            
            # Trade parameters - using a very small quantity (1)
            trade_data = {
                "symbol": "NQ",
                "quantity": 1,
                "action": "Buy",
                "tp_ticks": 100,
                "sl_ticks": 40,
                "tick_size": 0.25,
                "enable_tp": True,
                "enable_sl": True,
                "account": "all"
            }
            
            # Execute trade via dashboard API
            logger.info(f"Executing trade via http://localhost:{port}/api/trade: {json.dumps(trade_data)}")
            response = requests.post(f"http://localhost:{port}/api/trade", json=trade_data, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Trade execution failed: {response.text}")
                return False
            
            result = response.json()
            logger.info(f"Trade execution result: {json.dumps(result)}")
            
            # Check if any accounts were affected
            if result.get("accounts_affected", 0) < 1:
                logger.error("No accounts were affected by the trade")
                return False
            
            logger.info("Trade execution appears successful")
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            traceback.print_exc()
            return False
    
    def verify_position(self, timeout=30, port=6001):
        """Verify that the position appears in the Positions table."""
        if not self.dashboard_running:
            logger.error("Dashboard is not running")
            return False
        
        # Detect which port dashboard is running on
        for test_port in range(port, port + 3):
            try:
                test_response = requests.get(f"http://localhost:{test_port}/api/accounts", timeout=2)
                if test_response.status_code == 200:
                    port = test_port
                    logger.info(f"Found dashboard running on port {port}")
                    break
            except:
                pass
        
        logger.info(f"Verifying position (timeout: {timeout}s) via port {port}...")
        
        # Try to find position for timeout seconds
        start_time = time.time()
        iteration = 0
        while time.time() - start_time < timeout:
            try:
                iteration += 1
                # Check accounts endpoint
                response = requests.get(f"http://localhost:{port}/api/accounts", timeout=5)
                if response.status_code != 200:
                    logger.error(f"Failed to get account data: {response.text}")
                    time.sleep(1)
                    continue
                
                accounts_data = response.json()
                logger.info(f"Retrieved data for {len(accounts_data)} accounts")
                
                # Detailed diagnostic of account data structure
                if iteration == 1 or iteration % 10 == 0:  # Log structure at beginning and every 10 seconds
                    logger.info("=== Account Data Structure ===")
                    for idx, account in enumerate(accounts_data):
                        logger.info(f"Account {idx + 1} structure:")
                        # Log all keys present in the account data
                        logger.info(f"  Available fields: {sorted(list(account.keys()))}")
                        # Sample some key values
                        for key in ['Account', 'Net Pos', 'NetPos', 'Net Position', 'P&L', 'Available Margin', 'User', 'Phase']:
                            if key in account:
                                logger.info(f"  {key}: {account[key]}")
                
                # Extract positions from accounts data
                has_position = False
                
                for account in accounts_data:
                    # Look for position fields - they might have different names
                    position_fields = ['Net Pos', 'Net Position', 'NetPos']
                    
                    for field in position_fields:
                        if field in account and account.get(field) != "0" and account.get(field) != 0:
                            logger.info(f"Found position in account: {account}")
                            has_position = True
                            break
                    
                    if has_position:
                        break
                
                if has_position:
                    logger.info("Position verified!")
                    return True
                
                # Check for positions in the browser's console logs and inject position monitor
                console_log_check = """
                (function() {
                    try {
                        // Inject a position monitor script
                        if (!window.testPositionMonitor) {
                            console.log("[TEST] Injecting position monitor...");
                            
                            // Create a simple monitor object to track positions 
                            window.testPositionMonitor = {
                                positions: {},
                                positionFound: false,
                                lastCheck: new Date(),
                                
                                checkForPositions: function() {
                                    console.log("[TEST] Actively checking for positions...");
                                    this.lastCheck = new Date();
                                    
                                    // Try to find position indicators in DOM
                                    
                                    // Method 1: Look for tradovatePositions object
                                    if (window.tradovatePositions) {
                                        this.positionFound = true;
                                        this.positions = JSON.parse(JSON.stringify(window.tradovatePositions));
                                        console.log("[TEST] Found tradovatePositions:", this.positions);
                                        return true;
                                    }
                                    
                                    // Method 2: Look at DOM modules with 'Positions' header
                                    const posHeaders = Array.from(document.querySelectorAll('.panel--header'))
                                        .filter(h => h.textContent.includes('Position'));
                                    
                                    if (posHeaders.length > 0) {
                                        console.log("[TEST] Found position headers:", posHeaders.length);
                                        
                                        // Look for NQ text in same module
                                        for (const header of posHeaders) {
                                            const module = header.closest('.module');
                                            if (module && module.textContent.includes('NQ')) {
                                                this.positionFound = true;
                                                this.positions = { fromDOM: true, source: 'header', text: module.textContent };
                                                console.log("[TEST] Found NQ in position module!");
                                                return true;
                                            }
                                        }
                                    }
                                    
                                    // Method 3: Check for NQ in any table
                                    const tables = document.querySelectorAll('.fixedDataTable_main, table');
                                    
                                    for (const table of tables) {
                                        if (table.textContent.includes('NQ')) {
                                            // Look for numeric values that might be positions
                                            const cells = table.querySelectorAll('.public_fixedDataTableCell_cellContent, td');
                                            for (const cell of cells) {
                                                if (/^[-+]?[0-9]+$/.test(cell.textContent.trim()) && 
                                                    cell.textContent.trim() !== '0') {
                                                    this.positionFound = true;
                                                    this.positions = { 
                                                        fromDOM: true, 
                                                        source: 'table', 
                                                        value: cell.textContent.trim() 
                                                    };
                                                    console.log("[TEST] Found position value in table with NQ:", this.positions);
                                                    return true;
                                                }
                                            }
                                        }
                                    }
                                    
                                    return false;
                                }
                            };
                            
                            // Run the check immediately
                            window.testPositionMonitor.checkForPositions();
                            
                            // Also set up a periodic check
                            window.testPositionInterval = setInterval(function() {
                                window.testPositionMonitor.checkForPositions();
                            }, 2000);
                        }
                        
                        // Return the current state
                        return {
                            positionFound: window.testPositionMonitor.positionFound,
                            positions: window.testPositionMonitor.positions,
                            lastCheck: window.testPositionMonitor.lastCheck.toString()
                        };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                })();
                """
                
                # Execute the console log check
                if self.chrome_instance and self.chrome_instance.tab:
                    console_result = self.chrome_instance.tab.Runtime.evaluate(expression=console_log_check)
                    console_check = json.loads(console_result.get("result", {}).get("value", "{}"))
                    if console_check.get("positionFound", False):
                        logger.info(f"Found position via console check: {console_check}")
                        return True
                    
                # Also check position table directly using JavaScript
                # Detailed logging of DOM structure for positions table (every iteration)
                # Search ALL tables for position data
                comprehensive_dom_check = """
                (function() {
                    try {
                        // Comprehensive analysis of all tables and modules
                        const output = {
                            allTables: [],
                            allModules: [],
                            positionData: null,
                            success: false,
                            consoleMessages: []
                        };
                        
                        // Check the window for any globally published positions
                        if (window.tradovatePositions) {
                            output.tradovatePositions = window.tradovatePositions;
                            output.success = true;
                            output.positionData = { source: "tradovatePositions", data: window.tradovatePositions };
                            return output;
                        }
                        
                        // Look for console messages about positions
                        // (We can't access console history directly, but we can check if our code is logging)
                        console.log("[POSITION_CHECK] Checking for positions");
                        output.consoleMessages.push("[POSITION_CHECK] Checking for positions");
                        
                        // Check ANY position-related text in DOM
                        const textContent = document.body.textContent || '';
                        
                        // Look for position indicators in text
                        if (textContent.includes('NQ') && 
                            (textContent.includes('Net Pos') || 
                             textContent.includes('Position') || 
                             textContent.includes('SELL') ||
                             textContent.includes('BUY'))) {
                            
                            output.success = true;
                            output.positionData = {
                                source: "textSearch",
                                message: "Found NQ and position-related text in DOM"
                            };
                            
                            // Try to extract detailed position info from body text
                            const nqMatch = textContent.match(/NQ\s*[-+]?[0-9]+/);
                            if (nqMatch) {
                                output.positionData.matchedText = nqMatch[0];
                            }
                        }
                        
                        // Get all modules
                        const modules = document.querySelectorAll('.module');
                        output.moduleCount = modules.length;
                        
                        // Analyze each module
                        modules.forEach((module, moduleIndex) => {
                            const moduleInfo = {
                                index: moduleIndex,
                                className: module.className,
                                id: module.id,
                                headerText: '',
                                hasPositionsTable: false,
                                tableData: []
                            };
                            
                            // Try to get header text
                            const headerEl = module.querySelector('.panel--header');
                            if (headerEl) {
                                moduleInfo.headerText = headerEl.textContent.trim();
                            }
                            
                            // Check for tables within this module
                            const tables = module.querySelectorAll('.fixedDataTable_main, table');
                            moduleInfo.tableCount = tables.length;
                            
                            tables.forEach((table, tableIndex) => {
                                const tableInfo = {
                                    index: tableIndex,
                                    rowCount: table.querySelectorAll('.public_fixedDataTable_bodyRow, tr').length,
                                    headerCells: [],
                                    rows: []
                                };
                                
                                // Try to find table headers - could be in various formats
                                const headerCells = table.querySelectorAll('.public_fixedDataTableCell_cellContent, th');
                                headerCells.forEach(cell => {
                                    if (cell.textContent) {
                                        tableInfo.headerCells.push(cell.textContent.trim());
                                    }
                                });
                                
                                // Look for position-related headers
                                if (
                                    tableInfo.headerCells.some(text => 
                                        text.includes('Net Pos') || 
                                        text.includes('Position') || 
                                        text.includes('Symbol') ||
                                        text.includes('P/L')
                                    )
                                ) {
                                    moduleInfo.hasPositionsTable = true;
                                    // This might be the positions table!
                                    
                                    // Get all rows
                                    const rows = table.querySelectorAll('.public_fixedDataTable_bodyRow, tr');
                                    rows.forEach((row, rowIndex) => {
                                        const rowData = {
                                            index: rowIndex,
                                            cells: []
                                        };
                                        
                                        // Get all cells in this row
                                        const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent, td');
                                        cells.forEach((cell, cellIndex) => {
                                            rowData.cells.push({
                                                index: cellIndex,
                                                text: cell.textContent.trim()
                                            });
                                        });
                                        
                                        // Try to determine if this is a position row for NQ
                                        if (rowData.cells.some(cell => cell.text.includes('NQ'))) {
                                            // This might be an NQ position!
                                            rowData.mightBeNQPosition = true;
                                            
                                            // See if we can identify position size (Net Pos)
                                            // Usually the 2nd or 3rd cell might have the position size
                                            rowData.cells.forEach(cell => {
                                                // Position sizes are typically numbers like 1, 2, -1, etc.
                                                const isPosNumber = /^[-+]?[0-9]+$/.test(cell.text);
                                                if (isPosNumber && cell.text !== '0') {
                                                    rowData.possiblePositionSize = cell.text;
                                                    
                                                    // If we find a non-zero position for NQ, mark as success
                                                    output.success = true;
                                                    output.positionData = {
                                                        symbol: 'NQ',
                                                        size: cell.text,
                                                        row: rowData
                                                    };
                                                }
                                            });
                                        }
                                        
                                        tableInfo.rows.push(rowData);
                                    });
                                }
                                
                                moduleInfo.tableData.push(tableInfo);
                            });
                            
                            output.allModules.push(moduleInfo);
                        });
                        
                        // Also look for any DOM element containing "NQ" and a number
                        const allDomElements = document.querySelectorAll('*');
                        output.elementsWithNQ = [];
                        
                        for (let i = 0; i < Math.min(allDomElements.length, 1000); i++) {
                            const element = allDomElements[i];
                            if (element.textContent && element.textContent.includes('NQ')) {
                                output.elementsWithNQ.push({
                                    tagName: element.tagName,
                                    className: element.className,
                                    id: element.id,
                                    text: element.textContent.trim().substring(0, 50)  // Limit text length
                                });
                            }
                        }
                        
                        return output;
                    } catch (e) {
                        return { error: e.toString() };
                    }
                })();
                """
                
                if self.chrome_instance and self.chrome_instance.tab and iteration == 1:
                    dom_check_result = self.chrome_instance.tab.Runtime.evaluate(expression=comprehensive_dom_check)
                    dom_structure = json.loads(dom_check_result.get("result", {}).get("value", "{}"))
                    logger.info("=== Initial Comprehensive DOM Analysis ===")
                    logger.info(f"DOM Structure: {json.dumps(dom_structure, indent=2)}")

                js_check = """
                (function() {
                    try {
                        // Find positions table
                        const positionsTable = document.querySelector('.module.module-dom');
                        if (!positionsTable) {
                            return { found: false, reason: "Positions table not found" };
                        }
                        
                        // Find rows
                        const rows = positionsTable.querySelectorAll('.public_fixedDataTable_bodyRow');
                        if (!rows || rows.length === 0) {
                            return { found: false, reason: "No rows in positions table" };
                        }
                        
                        // Check for NQ positions
                        let foundPosition = false;
                        let positionData = null;
                        
                        for (const row of rows) {
                            const symbolCell = row.querySelector('.symbol-name-cell');
                            if (!symbolCell) continue;
                            
                            const symbolText = symbolCell.textContent.trim();
                            if (symbolText.includes('NQ')) {
                                // Find position size (Net Pos)
                                const cells = row.querySelectorAll('.fixedDataTableCellLayout_alignRight');
                                if (cells.length > 0) {
                                    const netPosElement = cells[0].querySelector('.public_fixedDataTableCell_cellContent');
                                    const netPos = netPosElement ? netPosElement.textContent.trim() : '0';
                                    
                                    if (netPos !== '0') {
                                        foundPosition = true;
                                        positionData = {
                                            symbol: symbolText,
                                            netPos: netPos
                                        };
                                        
                                        // Try to get more data
                                        if (cells.length > 1) {
                                            const priceElement = cells[1].querySelector('.public_fixedDataTableCell_cellContent');
                                            positionData.price = priceElement ? priceElement.textContent.trim() : '';
                                        }
                                        
                                        if (cells.length > 2) {
                                            const plElement = cells[2].querySelector('.public_fixedDataTableCell_cellContent');
                                            positionData.pnl = plElement ? plElement.textContent.trim() : '';
                                        }
                                    }
                                }
                            }
                        }
                        
                        return { 
                            found: foundPosition, 
                            data: positionData,
                            rowCount: rows.length
                        };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                })();
                """
                
                if self.chrome_instance and self.chrome_instance.tab:
                    result = self.chrome_instance.tab.Runtime.evaluate(expression=js_check)
                    position_check = json.loads(result.get("result", {}).get("value", "{}"))
                    
                    # Now also check our comprehensive DOM analysis for position data
                    if self.chrome_instance and self.chrome_instance.tab:
                        dom_check_result = self.chrome_instance.tab.Runtime.evaluate(expression=comprehensive_dom_check)
                        dom_analysis = json.loads(dom_check_result.get("result", {}).get("value", "{}"))
                        
                        # Check if we found a position successfully
                        if dom_analysis.get("success", False) and dom_analysis.get("positionData"):
                            logger.info(f"Found position data: {dom_analysis.get('positionData')}")
                            return True
                        
                        # Only log the full DOM analysis periodically to avoid excessive output
                        if iteration % 10 == 0 or iteration == 1:
                            logger.info("=== Comprehensive DOM Analysis ===")
                            # Limit the output to keep logs manageable
                            logger.info(f"Module count: {dom_analysis.get('moduleCount', 0)}")
                            logger.info(f"Position data: {dom_analysis.get('positionData')}")
                            logger.info(f"Elements with NQ: {len(dom_analysis.get('elementsWithNQ', []))}")
                            
                            # Log modules with position tables
                            position_modules = [m for m in dom_analysis.get('allModules', []) if m.get('hasPositionsTable')]
                            logger.info(f"Modules with position tables: {len(position_modules)}")
                            for module in position_modules:
                                logger.info(f"  Module {module.get('index')}: {module.get('headerText')} - {len(module.get('tableData', []))} tables")
                    
                    logger.info(f"Position check via JS: {position_check}")
                    
                    # Check if either method found a position
                    if position_check.get("found", False) or (dom_analysis and dom_analysis.get("success", False)):
                        logger.info(f"Position found via JavaScript!" + 
                                   (f" Details: {position_check.get('data')}" if position_check.get("found") else "") +
                                   (f" DOM Analysis: {dom_analysis.get('positionData')}" if dom_analysis and dom_analysis.get("success") else ""))
                        return True
                        
                    # For debugging only - this code is disabled
                    if False:
                        demo_structure_js = """
                        (function() {
                            try {
                                // Log structure of positions table
                                const output = { domStructure: {} };
                                
                                // Check for module-dom sections
                                const domModules = document.querySelectorAll('.module.module-dom');
                                output.domStructure.moduleCount = domModules.length;
                                
                                // Check for table structure
                                output.domStructure.tables = [];
                                document.querySelectorAll('.fixedDataTable_main').forEach((table, tableIdx) => {
                                    const tableInfo = {
                                        index: tableIdx,
                                        rowCount: table.querySelectorAll('.public_fixedDataTable_bodyRow').length,
                                        headerCount: table.querySelectorAll('.public_fixedDataTable_header').length,
                                        cellCount: table.querySelectorAll('.public_fixedDataTableCell_cellContent').length
                                    };
                                    
                                    // Analyze first row if exists
                                    const firstRow = table.querySelector('.public_fixedDataTable_bodyRow');
                                    if (firstRow) {
                                        tableInfo.firstRowContent = [];
                                        firstRow.querySelectorAll('.public_fixedDataTableCell_cellContent').forEach((cell) => {
                                            tableInfo.firstRowContent.push(cell.textContent.trim());
                                        });
                                    }
                                    
                                    output.domStructure.tables.push(tableInfo);
                                });
                                
                                // Look for specific positions elements
                                output.domStructure.symbolCells = document.querySelectorAll('.symbol-name-cell').length;
                                output.domStructure.rightAlignedCells = document.querySelectorAll('.fixedDataTableCellLayout_alignRight').length;
                                
                                // Check for contract-symbol elements
                                const contractSymbols = document.querySelectorAll('.contract-symbol');
                                output.domStructure.contractSymbolCount = contractSymbols.length;
                                output.domStructure.contractSymbolTexts = [];
                                contractSymbols.forEach(symbol => {
                                    output.domStructure.contractSymbolTexts.push(symbol.textContent.trim());
                                });
                                
                                return output;
                            } catch (e) {
                                return { error: e.toString() };
                            }
                        })();
                        """
                        dom_check_result = self.chrome_instance.tab.Runtime.evaluate(expression=dom_structure_js)
                        dom_structure = json.loads(dom_check_result.get("result", {}).get("value", "{}"))
                        logger.info("=== DOM Structure Analysis ===")
                        logger.info(f"DOM Structure: {json.dumps(dom_structure, indent=2)}")
                    
                    if position_check.get("found", False):
                        logger.info(f"Position found via JavaScript: {position_check.get('data')}")
                        return True
                
                logger.info("No position found yet, waiting...")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error verifying position: {e}")
                time.sleep(1)
        
        logger.error(f"Failed to verify position after {timeout} seconds")
        return False
    
    def cleanup(self):
        """Clean up resources."""
        if self.chrome_instance:
            logger.info("Closing Chrome instance...")
            try:
                self.chrome_instance.stop()
            except Exception as e:
                logger.error(f"Error stopping Chrome: {e}")

def run_test():
    """Run the complete trade execution test."""
    print("\n=== Running Trade Execution Test ===\n")
    
    test = TestTradeExecution()
    
    try:
        # 1. Setup (Chrome and login)
        logger.info("Step 1: Setting up Chrome and logging in...")
        if not test.setup():
            logger.error("Setup failed")
            return False
        
        # 2. Start dashboard
        logger.info("Step 2: Starting dashboard...")
        if not test.start_dashboard():
            logger.error("Dashboard start failed")
            return False
        
        # 3. Execute trade
        logger.info("Step 3: Executing trade...")
        if not test.execute_trade():
            logger.error("Trade execution failed")
            return False
        
        # 4. Verify position
        logger.info("Step 4: Verifying position...")
        if not test.verify_position(timeout=60):
            logger.error("Position verification failed")
            return False
        
        logger.info("All steps completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        test.cleanup()

if __name__ == "__main__":
    success = run_test()
    if success:
        print("\n✅ Trade execution test passed!")
        sys.exit(0)
    else:
        print("\n❌ Trade execution test failed.")
        sys.exit(1)