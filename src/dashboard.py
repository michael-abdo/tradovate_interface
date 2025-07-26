#!/usr/bin/env python3
import threading
import time
from flask import Flask, render_template, jsonify
import sys
import os
import json
import datetime

# Import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import TradovateController
from flask import request
from utils.chrome_stability import ChromeStabilityMonitor

# Create Flask app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'web/static'),
            template_folder=os.path.join(project_root, 'web/templates'))

# Initialize controller and health monitor
controller = TradovateController()

# Initialize connection health monitoring
health_monitor = ChromeStabilityMonitor(log_dir="logs/dashboard_health")

# Register connections with health monitor
for idx, connection in enumerate(controller.connections):
    account_name = f"Account_{idx+1}_{connection.account_name.replace(' ', '_')}"
    health_monitor.register_connection(account_name, connection.port)

# Start health monitoring
health_monitor.start_health_monitoring()

def inject_account_data_function():
    """Inject the getAllAccountTableData function into all tabs"""
    for conn in controller.connections:
        if conn.tab:
            try:
                # Read the function from the file
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                account_data_path = os.path.join(project_root, 
                                       'scripts/tampermonkey/getAllAccountTableData.user.js')
                with open(account_data_path, 'r') as file:
                    get_account_data_js = file.read()
                
                # Inject it into the tab
                conn.tab.Runtime.evaluate(expression=get_account_data_js)
                print(f"Injected getAllAccountTableData into {conn.account_name}")
            except Exception as e:
                print(f"Error injecting account data function: {e}")

# Route for dashboard UI
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# API endpoint to get all account data
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    account_data = []
    
    # Fetch data from all tabs
    for i, conn in enumerate(controller.connections):
        if conn.tab:
            try:
                # Inject the phase analysis logic from autoriskManagement.js
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                autorisk_path = os.path.join(project_root, 'scripts/tampermonkey/autoriskManagement.js')
                with open(autorisk_path, 'r') as file:
                    autorisk_js = file.read()
                
                # Just inject the entire autorisk script and call getTableData directly
                print(f"[Accounts API] Injecting phase logic for {conn.account_name}")
                conn.tab.Runtime.evaluate(expression=autorisk_js)
                
                # Execute the getTableData() function with real phase analysis
                result = conn.tab.Runtime.evaluate(
                    expression="JSON.stringify(getTableData())")
                
                print(f"[Accounts API] Raw result for {conn.account_name}: {result}")
                
                if result and 'result' in result and 'value' in result['result']:
                    try:
                        # Parse the JSON result
                        tab_data = json.loads(result['result']['value'])
                        print(f"[Accounts API] Parsed data for {conn.account_name}: {len(tab_data) if tab_data else 0} rows")
                        
                        if not tab_data:
                            continue
                            
                        # Add account identifier to each item
                        for item in tab_data:
                            item['account_name'] = conn.account_name
                            item['account_index'] = i
                            
                            # Ensure we have both User and Phase fields (Phase is the renamed User field)
                            if 'User' in item and 'Phase' not in item:
                                item['Phase'] = item['User']
                                
                            # Standardize Account field - ensure there's only one Account field
                            # and remove any with arrows
                            if 'Account ▲' in item:
                                account_value = item['Account ▲']
                                # Remove the old key and add standardized one
                                item.pop('Account ▲', None)
                                # Make sure we don't create duplicate Account fields
                                if 'Account' not in item:
                                    item['Account'] = account_value
                        
                        account_data.extend(tab_data)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON from {conn.account_name}: {e}")
                else:
                    print(f"No valid result structure for {conn.account_name}")
            except Exception as e:
                print(f"Error getting account data from {conn.account_name}: {e}")
    
    return jsonify(account_data)

# API endpoint to update phase status in Chrome tabs
@app.route('/api/update-phases', methods=['POST'])
def update_phases():
    print(f"\n[Phase Update API] Called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Phase Update API] Total connections: {len(controller.connections)}")
    
    try:
        results = []
        # Execute updateUserColumnPhaseStatus on all tabs
        for i, conn in enumerate(controller.connections):
            print(f"[Phase Update API] Processing connection {i}: {conn.account_name}")
            if conn.tab:
                try:
                    # First inject the risk management script that contains updateUserColumnPhaseStatus
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    risk_script_path = os.path.join(project_root, 
                                          'scripts/tampermonkey/autoriskManagement.js')
                    
                    # Read and extract the core functions from the script
                    with open(risk_script_path, 'r') as file:
                        risk_script = file.read()
                    
                    # Inject the complete autoriskManagement.js functions to run actual phase logic
                    functions_to_inject = """
                    // Inject phase criteria from autoriskManagement.js
                    const phaseCriteria = [
                        // ── DEMO ──
                        {
                            phase: '1',
                            accountNameIncludes: 'DEMO',
                            totalAvailOperator: '<',
                            totalAvailValue: 60000,
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
                    
                    // Phase analysis function
                    function analyzePhase(row, reset = false) {
                        if (reset || typeof analyzePhase.phaseData === 'undefined') {
                            console.log("[analyzePhase] resetting phaseData");
                            analyzePhase.phaseData = {};

                            const phase1Count = phaseCriteria.filter(r => r.phase === '1').length;
                            const rule1 = phaseCriteria.find(r => r.phase === '1');
                            if (rule1) {
                                rule1.maxActive = 1;
                                console.log(`[analyzePhase] set phase 1 maxActive to ${rule1.maxActive}`);
                            }

                            const increment = typeof analyzePhase.maxActiveIncrement === 'number'
                            ? analyzePhase.maxActiveIncrement
                            : 1;
                            const rule2 = phaseCriteria.find(r => r.phase === '2');
                            if (rule2) {
                                rule2.maxActive = 1;
                                console.log(`[analyzePhase] increased phase 2 maxActive to ${rule2.maxActive}`);
                            }
                        }

                        if (row === null) {
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
                            return rule.phase;
                        }

                        // Otherwise activate
                        row.active = true;
                        analyzePhase.phaseData[rule.phase].activeCount++;

                        return rule.phase;
                    }
                    
                    // Enhanced getTableData function with real phase analysis
                    if (typeof getTableData === 'undefined') {
                        window.getTableData = function() {
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
                        };
                    }
                    
                    if (typeof updateUserColumnPhaseStatus === 'undefined') {
                        window.updateUserColumnPhaseStatus = function() {
                            console.log("[updateUserColumnPhaseStatus] Starting...");
                            
                            const accountTable = document.querySelector('.module.positions.data-table');
                            if (!accountTable) {
                                console.error("[updateUserColumnPhaseStatus] No accountTable found");
                                return;
                            }
                            
                            const rows = accountTable.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
                            if (!rows.length) {
                                console.error("[updateUserColumnPhaseStatus] No rows found");
                                return;
                            }
                            console.log(`[updateUserColumnPhaseStatus] Found ${rows.length} rows`);
                            
                            // Determine the index of the "User" column from the header row
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
                            
                            // Update the "User" column cells for each data row with phase and status
                            rows.forEach((row, idx) => {
                                if (idx === 0) return; // skip header row
                                const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
                                
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
                                    console.error(`[updateUserColumnPhaseStatus] Row ${idx} doesn't have enough cells`);
                                }
                            });
                            
                            console.log("[updateUserColumnPhaseStatus] Completed");
                        };
                    }
                    """
                    
                    # Inject the functions
                    print(f"[Phase Update API] Injecting functions for {conn.account_name}")
                    conn.tab.Runtime.evaluate(expression=functions_to_inject)
                    
                    # Now execute updateUserColumnPhaseStatus
                    print(f"[Phase Update API] Executing updateUserColumnPhaseStatus for {conn.account_name}")
                    result = conn.tab.Runtime.evaluate(
                        expression="updateUserColumnPhaseStatus(); 'Phase update completed';")
                    
                    if result and 'result' in result:
                        print(f"[Phase Update API] Success for {conn.account_name}: {result['result'].get('value', 'Completed')}")
                        results.append({
                            "account": conn.account_name,
                            "status": "success",
                            "message": result['result'].get('value', 'Completed')
                        })
                    else:
                        print(f"[Phase Update API] No result for {conn.account_name}")
                        results.append({
                            "account": conn.account_name,
                            "status": "error",
                            "message": "No result returned"
                        })
                        
                except Exception as e:
                    print(f"[Phase Update API] Error for {conn.account_name}: {str(e)}")
                    results.append({
                        "account": conn.account_name,
                        "status": "error",
                        "message": str(e)
                    })
            else:
                print(f"[Phase Update API] No tab for connection {i}: {conn.account_name}")
        
        print(f"[Phase Update API] Completed. Total results: {len(results)}")
        return jsonify({
            "status": "success",
            "message": f"Phase update executed on {len(results)} accounts",
            "details": results
        })
        
    except Exception as e:
        print(f"[Phase Update API] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# API endpoint to get summary data
@app.route('/api/summary', methods=['GET'])
def get_summary():
    # We'll forward this to the accounts endpoint since we're now focusing on account data
    accounts_response = get_accounts()
    accounts_data = json.loads(accounts_response.get_data(as_text=True))
    
    # Calculate summary stats
    total_pnl = 0
    total_margin = 0
    
    for account in accounts_data:
        # Try to extract P&L (check both original and standardized names)
        pnl_fields = ['Total P&L', 'Dollar Total P L']
        for field in pnl_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_pnl += val
                elif isinstance(val, str):
                    try:
                        total_pnl += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
                    
        # Try to extract margin (check both original and standardized names)
        margin_fields = ['Available Margin', 'Total Available Margin']
        for field in margin_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_margin += val
                elif isinstance(val, str):
                    try:
                        total_margin += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
    
    return jsonify({
        'total_pnl': total_pnl,
        'total_margin': total_margin,
        'account_count': len(accounts_data)
    })

# API endpoint to get connection health status
@app.route('/api/health', methods=['GET'])
def get_connection_health():
    """Get real-time connection health status for all monitored connections"""
    try:
        # Get health status from the monitor
        health_status = health_monitor.get_connection_health_status()
        
        # Enhance with current Chrome instance health checks
        enhanced_status = health_status.copy()
        enhanced_status['chrome_instances'] = []
        
        for idx, connection in enumerate(controller.connections):
            if connection.tab:
                try:
                    # Get real-time health check from the Chrome instance
                    instance_health = connection.check_connection_health()
                    enhanced_status['chrome_instances'].append({
                        'account_index': idx,
                        'account_name': connection.account_name,
                        'port': connection.port,
                        'health': instance_health
                    })
                except Exception as e:
                    enhanced_status['chrome_instances'].append({
                        'account_index': idx,
                        'account_name': connection.account_name,
                        'port': connection.port,
                        'health': {
                            'healthy': False,
                            'errors': [f"Health check failed: {str(e)}"]
                        }
                    })
        
        return jsonify(enhanced_status)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get health status: {str(e)}',
            'timestamp': time.time(),
            'monitoring_active': False,
            'connections': {},
            'chrome_instances': []
        }), 500

# API endpoint to get network quality metrics
@app.route('/api/network-quality', methods=['GET'])
def get_network_quality():
    """Get comprehensive network quality metrics for all monitored connections"""
    try:
        # Get network quality summary from the health monitor
        network_summary = health_monitor.get_network_quality_summary()
        
        # Enhance with real-time status
        enhanced_summary = network_summary.copy()
        enhanced_summary['real_time_checks'] = []
        
        # Add current connection quality assessments
        for idx, connection in enumerate(controller.connections):
            if connection.tab:
                try:
                    account_name = f"Account_{idx+1}_{connection.account_name.replace(' ', '_')}"
                    
                    # Get quick network quality check
                    start_time = time.time()
                    instance_health = connection.check_connection_health()
                    check_duration = (time.time() - start_time) * 1000  # Convert to ms
                    
                    quality_check = {
                        'account_index': idx,
                        'account_name': connection.account_name,
                        'port': connection.port,
                        'response_time_ms': round(check_duration, 2),
                        'healthy': instance_health.get('healthy', False),
                        'checks_passed': sum(1 for check in instance_health.get('checks', {}).values() if check),
                        'total_checks': len(instance_health.get('checks', {})),
                        'errors': instance_health.get('errors', [])
                    }
                    
                    enhanced_summary['real_time_checks'].append(quality_check)
                    
                except Exception as e:
                    enhanced_summary['real_time_checks'].append({
                        'account_index': idx,
                        'account_name': connection.account_name,
                        'port': connection.port,
                        'error': f"Quality check failed: {str(e)}"
                    })
        
        return jsonify(enhanced_summary)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get network quality: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat(),
            'network_monitoring_enabled': False,
            'connections': {},
            'real_time_checks': []
        }), 500

# API endpoint to execute trades
@app.route('/api/trade', methods=['POST'])
def execute_trade():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        quantity = data.get('quantity', 1)
        action = data.get('action', 'Buy')
        tick_size = data.get('tick_size', 0.25)
        account_index = data.get('account', 'all')
        
        # Check TP/SL enable flags
        enable_tp = data.get('enable_tp', True)
        enable_sl = data.get('enable_sl', True)
        
        # Only get TP/SL values if they are enabled
        tp_ticks = data.get('tp_ticks', 100) if enable_tp else 0
        sl_ticks = data.get('sl_ticks', 40) if enable_sl else 0
        
        # Ensure tp_ticks and sl_ticks are integers
        tp_ticks = int(tp_ticks) if tp_ticks else 0
        sl_ticks = int(sl_ticks) if sl_ticks else 0
        
        print(f"Trade request: {symbol} {action} {quantity} TP:{tp_ticks if enable_tp else 'disabled'} SL:{sl_ticks if enable_sl else 'disabled'}")
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            # We need to update auto_trade.js to respect tp_ticks=0 and sl_ticks=0 as disabled
            result = controller.execute_on_all(
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            # Count successful trades
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to exit positions or cancel orders
@app.route('/api/exit', methods=['POST'])
def exit_positions():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        option = data.get('option', 'cancel-option-Exit-at-Mkt-Cxl')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('exit_positions', symbol, option)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            # After exit positions, run risk management on all accounts
            print(f"Running auto risk management after exit positions on all accounts")
            risk_results = controller.execute_on_all('run_risk_management')
            risk_accounts_affected = sum(1 for r in risk_results if r.get('result', {}).get('status') == 'success')
            print(f"Auto risk management completed on {risk_accounts_affected} accounts")
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result,
                'risk_management': {
                    'accounts_affected': risk_accounts_affected,
                    'details': risk_results
                }
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'exit_positions', 
                symbol, 
                option
            )
            
            # After exit positions, run risk management
            print(f"Running auto risk management after exit positions on account {account_index}")
            risk_result = controller.execute_on_one(
                account_index,
                'run_risk_management'
            )
            print(f"Auto risk management completed: {risk_result}")
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on account {account_index}',
                'accounts_affected': 1,
                'details': result,
                'risk_management': risk_result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
# API endpoint to update symbol on accounts
@app.route('/api/update-symbol', methods=['POST'])
def update_symbol():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('update_symbol', symbol)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'update_symbol', 
                symbol
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to update quantity on accounts
@app.route('/api/update-quantity', methods=['POST'])
def update_quantity():
    try:
        data = request.json
        
        # Extract parameters from request
        quantity = data.get('quantity', 1)
        account_index = data.get('account', 'all')
        
        # Update quantity in Chrome UI
        js_code = f"""
        (function() {{
            try {{
                // Update quantity input field
                const qtyInput = document.getElementById('quantityInput');
                if (qtyInput) {{
                    qtyInput.value = {quantity};
                    qtyInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    qtyInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log("Quantity updated to {quantity} in Tradovate UI");
                    return "Quantity updated in UI";
                }} else {{
                    console.error("Quantity input field not found");
                    return "Quantity input field not found";
                }}
            }} catch (err) {{
                console.error("Error updating quantity:", err);
                return "Error: " + err.toString();
            }}
        }})();
        """
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            results = []
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        ui_result = conn.tab.Runtime.evaluate(expression=js_code)
                        result_value = ui_result.get('result', {}).get('value', 'Unknown')
                        results.append({"account": i, "result": result_value})
                    except Exception as e:
                        results.append({"account": i, "error": str(e)})
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if "error" not in r)
            
            return jsonify({
                'status': 'success',
                'message': f'Quantity updated to {quantity} on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            if account_index < len(controller.connections) and controller.connections[account_index].tab:
                try:
                    ui_result = controller.connections[account_index].tab.Runtime.evaluate(expression=js_code)
                    result_value = ui_result.get('result', {}).get('value', 'Unknown')
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Quantity updated to {quantity} on account {account_index}',
                        'accounts_affected': 1,
                        'details': result_value
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Account {account_index} not found or not available'
                }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to run auto risk management
@app.route('/api/risk-management', methods=['POST'])
def run_risk_management():
    try:
        data = request.json
        account_index = data.get('account', 'all')
        
        if account_index == 'all':
            # Run on all accounts
            results = controller.execute_on_all('run_risk_management')
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if r.get('result', {}).get('status') == 'success')
            
            return jsonify({
                'status': 'success',
                'message': f'Auto risk management executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'run_risk_management'
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Auto risk management executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to get strategy mappings
@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, 'config/strategy_mappings.json')
        if not os.path.exists(strategy_file):
            # Create default file if it doesn't exist
            default_mappings = {
                "strategy_mappings": {
                    "DEFAULT": []
                }
            }
            with open(strategy_file, 'w') as f:
                json.dump(default_mappings, f, indent=2)
                
        with open(strategy_file, 'r') as f:
            mappings = json.load(f)
        return jsonify(mappings), 200
    except Exception as e:
        print(f"Error loading strategy mappings: {e}")
        return jsonify({"error": f"Failed to load strategy mappings: {str(e)}"}), 500

# API endpoint to update strategy mappings
@app.route('/api/strategies', methods=['POST'])
def update_strategies():
    try:
        data = request.json
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, 'config/strategy_mappings.json')
        
        with open(strategy_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Strategy mappings updated: {json.dumps(data, indent=2)}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error saving strategy mappings: {e}")
        return jsonify({"error": f"Failed to update strategy mappings: {str(e)}"}), 500

# API endpoint to update all trade control settings
@app.route('/api/update-trade-controls', methods=['POST'])
def update_trade_controls():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        tp_ticks = data.get('tp_ticks')
        sl_ticks = data.get('sl_ticks')
        tick_size = data.get('tick_size')
        
        # Additional parameters
        enable_tp = data.get('enable_tp')
        enable_sl = data.get('enable_sl')
        tp_price = data.get('tp_price')
        sl_price = data.get('sl_price')
        entry_price = data.get('entry_price')
        source_field = data.get('source_field', None)  # Which field triggered the update
        account_index = data.get('account', 'all')
        
        # Create JavaScript to update all the trade controls in the UI
        js_code = """
        (function() {
            try {
                const updates = {
                    success: true,
                    updates: {}
                };
        """
        
        # Only update symbol if it was explicitly changed in the dashboard (not when other fields change)
        if symbol and source_field == 'symbolInput':
            js_code += f"""
                // Update symbol in Tradovate UI
                try {{
                    const symbolInput = document.getElementById('symbolInput');
                    if (symbolInput) {{
                        symbolInput.value = "{symbol}";
                        symbolInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        symbolInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.symbol = "{symbol}";
                        console.log("Updated symbol to {symbol} in Tradovate UI");
                    }}
                }} catch (err) {{
                    updates.updates.symbol = "error: " + err.toString();
                    console.error("Error updating symbol:", err);
                }}
            """
            
        if quantity:
            js_code += f"""
                // Update quantity - matching ID 'qtyInput' from autoOrder.user.js
                try {{
                    const qtyInput = document.getElementById('qtyInput');
                    if (qtyInput) {{
                        qtyInput.value = {quantity};
                        qtyInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        qtyInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.quantity = {quantity};
                    }}
                }} catch (err) {{
                    updates.updates.quantity = "error: " + err.toString();
                }}
            """
            
        if tp_ticks:
            js_code += f"""
                // Update TP ticks - matching ID 'tpInput' from autoOrder.user.js
                try {{
                    const tpInput = document.getElementById('tpInput');
                    if (tpInput) {{
                        tpInput.value = {tp_ticks};
                        tpInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tpInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tp_ticks = {tp_ticks};
                    }}
                }} catch (err) {{
                    updates.updates.tp_ticks = "error: " + err.toString();
                }}
            """
            
        if sl_ticks:
            js_code += f"""
                // Update SL ticks - matching ID 'slInput' from autoOrder.user.js
                try {{
                    const slInput = document.getElementById('slInput');
                    if (slInput) {{
                        slInput.value = {sl_ticks};
                        slInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        slInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.sl_ticks = {sl_ticks};
                    }}
                }} catch (err) {{
                    updates.updates.sl_ticks = "error: " + err.toString();
                }}
            """
            
        if tick_size:
            js_code += f"""
                // Update tick size - matching ID 'tickInput' from autoOrder.user.js
                try {{
                    const tickInput = document.getElementById('tickInput');
                    if (tickInput) {{
                        tickInput.value = {tick_size};
                        tickInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tickInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tick_size = {tick_size};
                    }}
                }} catch (err) {{
                    updates.updates.tick_size = "error: " + err.toString();
                }}
            """
        
        # Add additional fields
        if enable_tp is not None:
            js_code += f"""
                // Update TP checkbox - matching ID 'tpCheckbox' from autoOrder.user.js
                try {{
                    const tpCheckbox = document.getElementById('tpCheckbox');
                    if (tpCheckbox) {{
                        tpCheckbox.checked = {'true' if enable_tp else 'false'};
                        tpCheckbox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.enable_tp = {'true' if enable_tp else 'false'};
                    }}
                }} catch (err) {{
                    updates.updates.enable_tp = "error: " + err.toString();
                }}
            """
            
        if enable_sl is not None:
            js_code += f"""
                // Update SL checkbox - matching ID 'slCheckbox' from autoOrder.user.js
                try {{
                    const slCheckbox = document.getElementById('slCheckbox');
                    if (slCheckbox) {{
                        slCheckbox.checked = {'true' if enable_sl else 'false'};
                        slCheckbox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.enable_sl = {'true' if enable_sl else 'false'};
                    }}
                }} catch (err) {{
                    updates.updates.enable_sl = "error: " + err.toString();
                }}
            """
            
        if tp_price:
            js_code += f"""
                // Update TP price input - matching ID 'tpPriceInput' from autoOrder.user.js
                try {{
                    const tpPriceInput = document.getElementById('tpPriceInput');
                    if (tpPriceInput) {{
                        tpPriceInput.value = {tp_price};
                        tpPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tpPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tp_price = {tp_price};
                    }}
                }} catch (err) {{
                    updates.updates.tp_price = "error: " + err.toString();
                }}
            """
            
        if sl_price:
            js_code += f"""
                // Update SL price input - matching ID 'slPriceInput' from autoOrder.user.js
                try {{
                    const slPriceInput = document.getElementById('slPriceInput');
                    if (slPriceInput) {{
                        slPriceInput.value = {sl_price};
                        slPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        slPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.sl_price = {sl_price};
                    }}
                }} catch (err) {{
                    updates.updates.sl_price = "error: " + err.toString();
                }}
            """
            
        if entry_price:
            js_code += f"""
                // Update entry price input - matching ID 'entryPriceInput' from autoOrder.user.js
                try {{
                    const entryPriceInput = document.getElementById('entryPriceInput');
                    if (entryPriceInput) {{
                        entryPriceInput.value = {entry_price};
                        entryPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        entryPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.entry_price = {entry_price};
                    }}
                }} catch (err) {{
                    updates.updates.entry_price = "error: " + err.toString();
                }}
            """
        
        # Close the JavaScript function
        js_code += """
                console.log("Trade control updates complete:", updates);
                return JSON.stringify(updates);
            } catch (err) {
                console.error("Error updating trade controls:", err);
                return JSON.stringify({success: false, error: err.toString()});
            }
        })();
        """
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            results = []
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        ui_result = conn.tab.Runtime.evaluate(expression=js_code)
                        result_value = ui_result.get('result', {}).get('value', '{}')
                        # Parse the JSON result
                        try:
                            parsed_result = json.loads(result_value)
                            results.append({"account": i, "result": parsed_result})
                        except:
                            results.append({"account": i, "result": result_value})
                    except Exception as e:
                        results.append({"account": i, "error": str(e)})
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if "error" not in r)
            
            return jsonify({
                'status': 'success',
                'message': f'Trade controls updated on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            if account_index < len(controller.connections) and controller.connections[account_index].tab:
                try:
                    ui_result = controller.connections[account_index].tab.Runtime.evaluate(expression=js_code)
                    result_value = ui_result.get('result', {}).get('value', '{}')
                    # Parse the JSON result
                    try:
                        parsed_result = json.loads(result_value)
                        result = parsed_result
                    except:
                        result = result_value
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Trade controls updated on account {account_index}',
                        'accounts_affected': 1,
                        'details': result
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Account {account_index} not found or not available'
                }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Run the app
def run_flask_dashboard():
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001)

if __name__ == '__main__':
    # Start the Flask server
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001, debug=True)
    print("Dashboard running at http://localhost:6001")