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
from src.app import TradovateController
from flask import request
from src.utils.chrome_stability import ChromeStabilityMonitor
from src.utils.chrome_communication import safe_evaluate, OperationType
from src.utils.trading_errors import (
    error_aggregator, ErrorSeverity, ErrorCategory,
    configure_error_logging, TradingError
)

# Note: Process monitor was moved to archive with tradovate_interface
# Disable startup monitoring integration for now
STARTUP_MONITORING_AVAILABLE = False

# Create Flask app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'web/static'),
            template_folder=os.path.join(project_root, 'web/templates'))

# Initialize controller and health monitor
controller = TradovateController()

# Initialize connection health monitoring
health_monitor = ChromeStabilityMonitor(log_dir="logs/dashboard_health")

# Initialize startup monitoring for dashboard integration if available
startup_monitor = None
if STARTUP_MONITORING_AVAILABLE:
    try:
        startup_monitor = ChromeProcessMonitor(config_path="config/process_monitor.json")
        startup_monitor.enable_startup_monitoring(StartupMonitoringMode.PASSIVE)  # Passive monitoring for dashboard
        print("Startup monitoring initialized for dashboard integration")
    except Exception as e:
        print(f"Warning: Failed to initialize startup monitoring for dashboard: {e}")
        startup_monitor = None

# Register connections with health monitor if methods exist
for idx, connection in enumerate(controller.connections):
    account_name = f"Account_{idx+1}_{connection.account_name.replace(' ', '_')}"
    if hasattr(health_monitor, 'register_connection'):
        health_monitor.register_connection(account_name, connection.port)

# Start health monitoring if method exists
if hasattr(health_monitor, 'start_health_monitoring'):
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
                result = safe_evaluate(
                    tab=conn.tab,
                    js_code=get_account_data_js,
                    operation_type=OperationType.IMPORTANT,
                    description=f"Inject getAllAccountTableData into {conn.account_name}"
                )
                if result.success:
                    print(f"Injected getAllAccountTableData into {conn.account_name}")
                else:
                    print(f"Failed to inject getAllAccountTableData into {conn.account_name}: {result.error}")
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
                safe_evaluate(
                tab=conn.tab,
                js_code=autorisk_js,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                
                # Execute the getTableData() function with real phase analysis
                result = safe_evaluate(
                    tab=conn.tab,
                    js_code="JSON.stringify(getTableData())",
                    operation_type=OperationType.CRITICAL,
                    description=f"Get table data for {conn.account_name}"
                )
                
                print(f"[Accounts API] Raw result for {conn.account_name}: {result}")
                
                if result and result.success:
                    try:
                        # Parse the JSON result
                        tab_data = json.loads(result.value)
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
                            // Try multiple selectors to find account table
                            const selectors = ['.module.positions.data-table', '.public_fixedDataTable_main'];
                            let accountTable = null;
                            
                            for (const selector of selectors) {
                                accountTable = document.querySelector(selector);
                                if (accountTable) {
                                    console.log('[Dashboard] Found account table with selector:', selector);
                                    break;
                                }
                            }
                            
                            if (!accountTable) {
                                console.error('[Dashboard] No account table found with any known selector');
                                return [];
                            }
                            
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
                    safe_evaluate(
                tab=conn.tab,
                js_code=functions_to_inject,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                    
                    # Now execute updateUserColumnPhaseStatus
                    print(f"[Phase Update API] Executing updateUserColumnPhaseStatus for {conn.account_name}")
                    result = safe_evaluate(
                        tab=conn.tab,
                        js_code="updateUserColumnPhaseStatus(); 'Phase update completed';",
                        operation_type=OperationType.CRITICAL,
                        description=f"Update phase status for {conn.account_name}"
                    )
                    
                    if result and result.success:
                        print(f"[Phase Update API] Success for {conn.account_name}: {result.value}")
                        results.append({
                            "account": conn.account_name,
                            "status": "success",
                            "message": result['result'].get('value', 'Completed')
                        })
                    else:
                        error_msg = result.error if result else "No result"
                        print(f"[Phase Update API] Failed for {conn.account_name}: {error_msg}")
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
        
        # Get error summary from aggregator
        error_summary = error_aggregator.get_summary()
        
        # Calculate overall system health score
        total_errors = error_summary['total_errors']
        critical_errors = error_summary['by_severity'].get('CRITICAL', 0)
        error_errors = error_summary['by_severity'].get('ERROR', 0)
        warn_errors = error_summary['by_severity'].get('WARNING', 0)
        
        # Health score calculation (0-100)
        health_score = 100
        health_score -= critical_errors * 10  # Critical errors heavily impact score
        health_score -= error_errors * 5      # Regular errors moderately impact
        health_score -= warn_errors * 1       # Warnings lightly impact
        health_score = max(0, health_score)   # Don't go below 0
        
        # Determine overall status
        if health_score >= 90:
            overall_status = "HEALTHY"
        elif health_score >= 70:
            overall_status = "DEGRADED"
        elif health_score >= 50:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"
        
        # Enhance with current Chrome instance health checks
        enhanced_status = health_status.copy()
        enhanced_status['chrome_instances'] = []
        enhanced_status['error_summary'] = error_summary
        enhanced_status['system_health'] = {
            'score': health_score,
            'status': overall_status,
            'uptime_seconds': error_summary['uptime_seconds']
        }
        
        # Get error rates for key categories
        enhanced_status['error_rates'] = {
            'chrome_communication': error_aggregator.get_error_rate(ErrorCategory.CHROME_COMMUNICATION),
            'order_execution': error_aggregator.get_error_rate(ErrorCategory.ORDER_EXECUTION),
            'dom_operation': error_aggregator.get_error_rate(ErrorCategory.DOM_OPERATION),
            'overall': error_aggregator.get_error_rate()
        }
        
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
            'chrome_instances': [],
            'system_health': {
                'score': 0,
                'status': 'UNKNOWN'
            }
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

# API endpoint to get startup monitoring status
@app.route('/api/startup-monitoring', methods=['GET'])
def get_startup_monitoring():
    """Get comprehensive startup monitoring status and metrics"""
    try:
        if not STARTUP_MONITORING_AVAILABLE or not startup_monitor:
            return jsonify({
                'error': 'Startup monitoring not available',
                'timestamp': datetime.datetime.now().isoformat(),
                'startup_monitoring_enabled': False,
                'startup_processes': {},
                'monitoring_stats': {}
            }), 503
        
        # Get current startup monitoring status
        status = startup_monitor.get_status()
        
        # Enhance with startup-specific information
        startup_status = {
            'timestamp': datetime.datetime.now().isoformat(), 
            'startup_monitoring_enabled': STARTUP_MONITORING_AVAILABLE and startup_monitor is not None,
            'monitoring_active': status.get('monitoring_active', False),
            'startup_monitoring_active': hasattr(startup_monitor, 'startup_monitoring_thread') and 
                                       startup_monitor.startup_monitoring_thread and 
                                       startup_monitor.startup_monitoring_thread.is_alive(),
            'startup_processes': {},
            'monitoring_stats': {
                'total_startup_processes': 0,
                'active_startup_processes': 0,
                'completed_startup_processes': 0,
                'failed_startup_processes': 0,
                'average_startup_time': 0,
                'startup_success_rate': 0
            },
            'startup_phases': {},
            'resource_usage': {}
        }
        
        # Get startup process information if available
        if hasattr(startup_monitor, 'startup_processes'):
            with startup_monitor.process_lock:
                startup_processes = getattr(startup_monitor, 'startup_processes', {})
                
                total_processes = len(startup_processes)
                active_count = 0
                completed_count = 0
                failed_count = 0
                startup_times = []
                phase_counts = {}
                
                for account_name, process_info in startup_processes.items():
                    # Convert process info to serializable format
                    if hasattr(process_info, '__dict__'):
                        process_dict = {}
                        for key, value in process_info.__dict__.items():
                            if isinstance(value, datetime.datetime):
                                process_dict[key] = value.isoformat()
                            elif hasattr(value, 'value'):  # Enum value
                                process_dict[key] = value.value
                            else:
                                try:
                                    # Test if value is JSON serializable
                                    json.dumps(value)
                                    process_dict[key] = value
                                except (TypeError, ValueError):
                                    process_dict[key] = str(value)
                        
                        startup_status['startup_processes'][account_name] = process_dict
                        
                        # Calculate statistics
                        current_phase = getattr(process_info, 'current_phase', StartupPhase.REGISTERED)
                        phase_name = current_phase.value if hasattr(current_phase, 'value') else str(current_phase)
                        phase_counts[phase_name] = phase_counts.get(phase_name, 0) + 1
                        
                        if phase_name == StartupPhase.READY.value:
                            completed_count += 1
                            # Calculate startup time if available
                            if hasattr(process_info, 'startup_time') and hasattr(process_info, 'completion_time'):
                                startup_time = process_info.completion_time - process_info.startup_time
                                startup_times.append(startup_time.total_seconds())
                        elif phase_name in ['failed', 'timeout']:
                            failed_count += 1
                        else:
                            active_count += 1
                
                # Update statistics
                startup_status['monitoring_stats'].update({
                    'total_startup_processes': total_processes,
                    'active_startup_processes': active_count,
                    'completed_startup_processes': completed_count,
                    'failed_startup_processes': failed_count,
                    'average_startup_time': sum(startup_times) / len(startup_times) if startup_times else 0,
                    'startup_success_rate': (completed_count / total_processes * 100) if total_processes > 0 else 0
                })
                
                startup_status['startup_phases'] = phase_counts
        
        # Get resource usage information if available
        if hasattr(startup_monitor, 'startup_monitoring_thread'):
            try:
                import psutil
                startup_status['resource_usage'] = {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'startup_monitoring_memory': 0  # Could be enhanced to track specific thread memory
                }
            except ImportError:
                startup_status['resource_usage'] = {
                    'error': 'psutil not available for resource monitoring'
                }
        
        # Add startup monitoring configuration
        if hasattr(startup_monitor, 'config'):
            config = startup_monitor.config
            startup_status['configuration'] = {
                'startup_timeout': config.get('startup_timeout', 60),
                'startup_warning_threshold': config.get('startup_warning_threshold', 30),
                'startup_retry_threshold': config.get('startup_retry_threshold', 45),
                'startup_resource_limit_cpu': config.get('startup_resource_limit_cpu', 80),
                'startup_resource_limit_memory': config.get('startup_resource_limit_memory', 80),
                'startup_check_interval': config.get('startup_check_interval', 2)
            }
        
        return jsonify(startup_status)
        
    except Exception as e:
        print(f"Error getting startup monitoring status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Failed to get startup monitoring status: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat(),
            'startup_monitoring_enabled': False,
            'startup_processes': {},
            'monitoring_stats': {}
        }), 500

# API endpoint to control startup monitoring
@app.route('/api/startup-monitoring/control', methods=['POST'])
def control_startup_monitoring():
    """Enable, disable, or configure startup monitoring"""
    try:
        if not STARTUP_MONITORING_AVAILABLE or not startup_monitor:
            return jsonify({
                'error': 'Startup monitoring not available',
                'status': 'unavailable'
            }), 503
        
        data = request.json
        action = data.get('action', 'status')
        
        if action == 'enable':
            mode = data.get('mode', 'PASSIVE')
            try:
                monitoring_mode = StartupMonitoringMode(mode.lower())
                startup_monitor.enable_startup_monitoring(monitoring_mode)
                return jsonify({
                    'status': 'success',
                    'message': f'Startup monitoring enabled in {mode} mode',
                    'monitoring_mode': mode
                })
            except ValueError:
                return jsonify({
                    'error': f'Invalid monitoring mode: {mode}',
                    'valid_modes': [mode.value for mode in StartupMonitoringMode]
                }), 400
                
        elif action == 'disable':
            startup_monitor.enable_startup_monitoring(StartupMonitoringMode.DISABLED)
            return jsonify({
                'status': 'success',
                'message': 'Startup monitoring disabled'
            })
            
        elif action == 'clear':
            # Clear completed startup processes from tracking
            if hasattr(startup_monitor, 'startup_processes'):
                with startup_monitor.process_lock:
                    startup_processes = getattr(startup_monitor, 'startup_processes', {})
                    completed_count = 0
                    accounts_to_remove = []
                    
                    for account_name, process_info in startup_processes.items():
                        current_phase = getattr(process_info, 'current_phase', StartupPhase.REGISTERED)
                        if current_phase == StartupPhase.READY:
                            accounts_to_remove.append(account_name)
                            completed_count += 1
                    
                    for account_name in accounts_to_remove:
                        del startup_processes[account_name]
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Cleared {completed_count} completed startup processes',
                        'cleared_count': completed_count
                    })
            
            return jsonify({
                'status': 'success',
                'message': 'No completed processes to clear',
                'cleared_count': 0
            })
            
        else:
            # Return current status
            status = startup_monitor.get_status()
            return jsonify({
                'status': 'success',
                'monitoring_active': status.get('monitoring_active', False),
                'startup_monitoring_active': hasattr(startup_monitor, 'startup_monitoring_thread') and 
                                           startup_monitor.startup_monitoring_thread and 
                                           startup_monitor.startup_monitoring_thread.is_alive()
            })
        
    except Exception as e:
        print(f"Error controlling startup monitoring: {e}")
        return jsonify({
            'error': f'Failed to control startup monitoring: {str(e)}',
            'status': 'error'
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
                        ui_result = safe_evaluate(
                tab=conn.tab,
                js_code=js_code,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                        result_value = ui_result.value if result.success else 'Unknown'
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
                    ui_result = controller.connections[account_index].safe_evaluate(
                tab=tab,
                js_code=js_code,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                    result_value = ui_result.value if result.success else 'Unknown'
                    
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
                        ui_result = safe_evaluate(
                tab=conn.tab,
                js_code=js_code,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                        result_value = ui_result.value if result.success else '{}'
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
                    ui_result = controller.connections[account_index].safe_evaluate(
                tab=tab,
                js_code=js_code,
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )
                    result_value = ui_result.value if result.success else '{}'
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

# API endpoint for detailed error information and trends
@app.route('/api/errors', methods=['GET'])
def get_error_details():
    """Get detailed error information, trends, and statistics"""
    try:
        # Get query parameters
        category = request.args.get('category', None)
        window_minutes = int(request.args.get('window', 5))
        
        # Get error summary
        error_summary = error_aggregator.get_summary()
        
        # Calculate error trends
        trends = {}
        for cat in ErrorCategory:
            rate = error_aggregator.get_error_rate(cat, window_minutes)
            trends[cat.value] = {
                'rate_per_minute': rate,
                'total_in_window': int(rate * window_minutes)
            }
        
        # Build response
        response = {
            'timestamp': datetime.datetime.now().isoformat(),
            'window_minutes': window_minutes,
            'summary': error_summary,
            'trends': trends,
            'critical_errors': error_summary['recent_critical_errors']
        }
        
        # If specific category requested, add detailed errors
        if category:
            try:
                cat_enum = ErrorCategory(category.upper())
                category_errors = []
                
                # Get errors for specific category (simplified for now)
                # In production, this would fetch from error_aggregator._errors
                response['category_details'] = {
                    'category': category,
                    'errors': category_errors
                }
            except ValueError:
                response['warning'] = f'Invalid category: {category}'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get error details: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

# API endpoint to clear old errors
@app.route('/api/errors/clear', methods=['POST'])
def clear_old_errors():
    """Clear errors older than specified hours"""
    try:
        data = request.json or {}
        hours = data.get('hours', 24)
        
        # Clear old errors
        error_aggregator.clear_old_errors(hours)
        
        # Get updated summary
        summary = error_aggregator.get_summary()
        
        return jsonify({
            'status': 'success',
            'message': f'Cleared errors older than {hours} hours',
            'remaining_errors': summary['total_errors'],
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to clear errors: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

# API endpoint for system health alerts configuration
@app.route('/api/health/alerts', methods=['GET', 'POST'])
def health_alerts():
    """Get or update health alert thresholds"""
    try:
        if request.method == 'GET':
            # Return current alert configuration
            # This would be loaded from config in production
            return jsonify({
                'thresholds': {
                    'health_score_critical': 50,
                    'health_score_warning': 70,
                    'error_rate_critical': 10.0,  # errors per minute
                    'error_rate_warning': 5.0,
                    'chrome_disconnect_threshold': 3
                },
                'alert_channels': ['console', 'dashboard'],
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        else:  # POST
            data = request.json
            # Update alert configuration
            # In production, this would save to config file
            
            return jsonify({
                'status': 'success',
                'message': 'Alert configuration updated',
                'timestamp': datetime.datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'error': f'Failed to manage health alerts: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
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