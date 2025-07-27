import pychrome
import os
import sys
import json
import argparse
import threading
import time

# Import Chrome Communication Framework for safe operations
from utils.chrome_communication import safe_evaluate, OperationType

# Load the Tampermonkey script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tampermonkey_path = os.path.join(project_root, 'scripts/tampermonkey/autoOrder.user.js')
with open(tampermonkey_path, 'r') as file:
    tampermonkey_code = file.read()
    
# Extract the core functions from Tampermonkey script
def extract_core_functions(code):
    # This is a simple extraction that removes the IIFE wrapper
    lines = code.split('\n')
    core_lines = []
    
    for line in lines:
        # Skip the IIFE start and end
        if '(function ()' in line or line.strip() == '})();':
            continue
        else:
            # Remove any leading indentation that was inside the IIFE
            if line.startswith('    '):
                line = line[4:]
            core_lines.append(line)
    
    return '\n'.join(core_lines)

tampermonkey_functions = extract_core_functions(tampermonkey_code)

class TradovateConnection:
    def __init__(self, port, account_name=None):
        self.port = port
        self.account_name = account_name or f"Account on port {port}"
        # Use unified connection logic from auto_login instead of duplicating tab finding
        try:
            from src.auto_login import connect_to_chrome
            self.browser, self.tab = connect_to_chrome(port)
            if self.tab:
                print(f"✅ Connected to Tradovate tab via unified connection logic for {self.account_name}")
            else:
                print(f"❌ Failed to find Tradovate tab for {self.account_name}")
        except ImportError:
            print(f"⚠️  Unified connection not available, using fallback for {self.account_name}")
            self.browser = pychrome.Browser(url=f"http://localhost:{port}")
            self.tab = None
            self.find_tradovate_tab()
        
    def find_tradovate_tab(self):
        """Fallback tab finding method when unified connection not available"""
        for tab in self.browser.list_tab():
            try:
                tab.start()
                tab.Page.enable()
                # Use safe_evaluate to check if this is a Tradovate tab
                result = safe_evaluate(
                    tab=tab, 
                    js_code="document.location.href",
                    operation_type=OperationType.IMPORTANT,
                    description="Check if tab is Tradovate"
                )
                url = result.value if result.success else ""
                
                if "tradovate" in url:
                    self.tab = tab
                    print(f"Found Tradovate tab for {self.account_name} (fallback method)")
                    # Keep the tab open
                    return
                else:
                    tab.stop()
            except Exception as e:
                print(f"Error processing tab: {e}")
                try:
                    tab.stop()
                except:
                    pass
                    
        print(f"No Tradovate tab found for {self.account_name} (fallback method)")
        
    def inject_tampermonkey(self):
        """Inject the Tampermonkey functions into the tab"""
        if not self.tab:
            print(f"No tab available for {self.account_name}")
            return False
            
        try:
            # First, inject the console interceptor to capture ALL console output
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            console_interceptor_path = os.path.join(project_root, 
                                                   'scripts/tampermonkey/console_interceptor.js')
            if os.path.exists(console_interceptor_path):
                with open(console_interceptor_path, 'r') as file:
                    console_interceptor_js = file.read()
                # Use safe_evaluate to inject console interceptor
                result = safe_evaluate(
                    tab=self.tab,
                    js_code=console_interceptor_js,
                    operation_type=OperationType.CRITICAL,
                    description=f"Inject console interceptor for {self.account_name}"
                )
                if result.success:
                    print(f"Console interceptor injected for {self.account_name}")
                else:
                    print(f"Failed to inject console interceptor for {self.account_name}: {result.error}")
            else:
                print(f"WARNING: Console interceptor not found at {console_interceptor_path}")
            
            # Load fresh tampermonkey script from file (not cached version)
            print(f"Injecting Tampermonkey functions for {self.account_name}...")
            tampermonkey_path = os.path.join(project_root, 'scripts/tampermonkey/autoOrder.user.js')
            with open(tampermonkey_path, 'r') as file:
                fresh_tampermonkey_code = file.read()
            fresh_tampermonkey_functions = extract_core_functions(fresh_tampermonkey_code)
            # Use safe_evaluate to inject Tampermonkey functions
            result = safe_evaluate(
                tab=self.tab,
                js_code=fresh_tampermonkey_functions,
                operation_type=OperationType.CRITICAL,
                description=f"Inject Tampermonkey functions for {self.account_name}"
            )
            if not result.success:
                print(f"Failed to inject Tampermonkey functions for {self.account_name}: {result.error}")
            
            # Also inject the getAllAccountTableData function
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            account_data_path = os.path.join(project_root, 
                                         'scripts/tampermonkey/getAllAccountTableData.user.js')
            if os.path.exists(account_data_path):
                with open(account_data_path, 'r') as file:
                    account_data_js = file.read()
                # Use safe_evaluate to inject account data function
                result = safe_evaluate(
                    tab=self.tab,
                    js_code=account_data_js,
                    operation_type=OperationType.IMPORTANT,
                    description=f"Inject account data function for {self.account_name}"
                )
                if result.success:
                    print(f"Account data function injected for {self.account_name}")
                else:
                    print(f"Failed to inject account data function for {self.account_name}: {result.error}")
            
            # Inject the autoriskManagement.js script
            risk_management_path = os.path.join(project_root, 
                                         'scripts/tampermonkey/autoriskManagement.js')
            if os.path.exists(risk_management_path):
                with open(risk_management_path, 'r') as file:
                    risk_management_js = file.read()
                # Use safe_evaluate to inject risk management script
                result = safe_evaluate(
                    tab=self.tab,
                    js_code=risk_management_js,
                    operation_type=OperationType.CRITICAL,
                    description=f"Inject risk management script for {self.account_name}"
                )
                if result.success:
                    print(f"Auto risk management script injected for {self.account_name}")
                    
                    # Wait a moment for the script to fully initialize
                    time.sleep(1)
                    
                    # Then explicitly run the risk management functions
                    init_code = """
                        console.log("Executing initial risk management assessment...");
                        if (typeof getTableData === 'function') {
                            getTableData();
                            console.log("getTableData executed");
                        } else {
                            console.error("getTableData function not found");
                        }
                        
                        if (typeof updateUserColumnPhaseStatus === 'function') {
                            updateUserColumnPhaseStatus();
                            console.log("updateUserColumnPhaseStatus executed");
                        } else {
                            console.error("updateUserColumnPhaseStatus function not found");
                        }
                        
                        if (typeof performAccountActions === 'function') {
                            performAccountActions();
                            console.log("performAccountActions executed");
                        } else {
                            console.error("performAccountActions function not found");
                        }
                        console.log("Risk management assessment completed");
                    """
                    
                    init_result = safe_evaluate(
                        tab=self.tab,
                        js_code=init_code,
                        operation_type=OperationType.IMPORTANT,
                        description=f"Initialize risk management for {self.account_name}"
                    )
                    
                    if init_result.success:
                        print(f"Auto risk management executed for {self.account_name}")
                    else:
                        print(f"Failed to initialize risk management for {self.account_name}: {init_result.error}")
                else:
                    print(f"Failed to inject risk management script for {self.account_name}: {result.error}")
            
            print(f"Tampermonkey functions injected successfully for {self.account_name}")
            return True
        except Exception as e:
            print(f"Error injecting Tampermonkey functions: {e}")
            return False
            
    def create_ui(self):
        """Create the Tampermonkey UI in the tab"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            # Use safe_evaluate to create UI
            result = safe_evaluate(
                tab=self.tab,
                js_code="createUI();",
                operation_type=OperationType.IMPORTANT,
                description=f"Create UI for {self.username}"
            )
            return {"success": result.success, "value": result.value, "error": result.error}
        except Exception as e:
            return {"error": str(e)}
            
    def auto_trade(self, symbol, quantity=1, action='Buy', tp_ticks=100, sl_ticks=40, tick_size=0.25):
        """Execute an auto trade using the Tampermonkey script with health verification"""
        if not self.tab:
            return {"error": "No tab available"}
        
        # Verify connection health before executing trade
        health_check = self.check_connection_health()
        if not health_check.get('healthy', False):
            health_errors = health_check.get('errors', ['Connection unhealthy'])
            return {
                "error": "Trade rejected due to connection health issues",
                "health_status": health_check,
                "health_errors": health_errors,
                "trade_rejected": True
            }
        
        # Log trading attempt with health context
        print(f"Executing trade for {self.username}: {action} {quantity} {symbol} (Health: {health_check.get('healthy', False)})")
            
        try:
            # Clear existing console logs before trade
            self.get_console_logs(clear_after=True)
            
            # Execute the trade with DOM Intelligence validation
            from src.utils.chrome_communication import execute_auto_trade_with_validation
            
            # Prepare context for validation (market conditions, urgency, etc.)
            validation_context = {
                'high_frequency_mode': False,  # Set based on trading strategy
                'market_volatility': 0.0,     # Could be calculated from recent price data
                'system_latency': 0,          # Could be measured from recent operations
                'health_check': health_check
            }
            
            # Execute with DOM Intelligence validation and emergency bypass capability
            result = execute_auto_trade_with_validation(
                self.tab, symbol, quantity, action, tp_ticks, sl_ticks, tick_size, 
                context=validation_context
            )
            
            # Wait a moment for console logs to be generated
            time.sleep(1)
            
            # Get console logs generated during trade execution
            console_logs = self.get_console_logs(limit=50)
            
            # Enhanced result processing for DOM Intelligence integration
            if isinstance(result, dict) and 'dom_intelligence_enabled' in result:
                # DOM Intelligence result structure
                result['console_logs'] = console_logs.get('logs', [])
                result['health_at_execution'] = health_check
                result['trade_executed'] = result.get('overall_success', False)
                
                # Log DOM Intelligence metrics
                validation_result = result.get('validation_result', {})
                if validation_result.get('emergency_bypass', False):
                    print(f"⚠️  Emergency bypass used for trade: {validation_result.get('message', 'Unknown reason')}")
                
                if not validation_result.get('success', True):
                    print(f"⚠️  DOM validation warning: {validation_result.get('message', 'Validation failed')}")
                
            else:
                # Legacy result structure (fallback)
                if isinstance(result, dict):
                    result['console_logs'] = console_logs.get('logs', [])
                    result['health_at_execution'] = health_check
                    result['trade_executed'] = True
                else:
                    # Ensure result is a dict for consistency
                    result = {
                        'trade_result': result,
                        'console_logs': console_logs.get('logs', []),
                        'health_at_execution': health_check,
                        'trade_executed': True
                    }
            
            return result
        except Exception as e:
            return {
                "error": str(e),
                "health_at_execution": health_check,
                "trade_executed": False
            }
            
    def exit_positions(self, symbol, option='cancel-option-Exit-at-Mkt-Cxl'):
        """Close all positions for the given symbol with health verification"""
        if not self.tab:
            return {"error": "No tab available"}
        
        # Verify connection health before executing exit
        health_check = self.check_connection_health()
        if not health_check.get('healthy', False):
            health_errors = health_check.get('errors', ['Connection unhealthy'])
            return {
                "error": "Exit rejected due to connection health issues",
                "health_status": health_check,
                "health_errors": health_errors,
                "exit_rejected": True
            }
        
        # Log exit attempt with health context
        print(f"Exiting positions for {self.username}: {symbol} with {option} (Health: {health_check.get('healthy', False)})")
            
        try:
            # Clear existing console logs before exit
            self.get_console_logs(clear_after=True)
            
            # Execute the exit with DOM Intelligence validation
            from src.utils.chrome_communication import execute_exit_positions_with_validation
            
            # Prepare context for validation (position exit is critical)
            validation_context = {
                'high_frequency_mode': False,
                'market_volatility': 0.0,  # Could be calculated from recent price data
                'system_latency': 0,       # Could be measured from recent operations
                'health_check': health_check,
                'position_exit': True      # Mark as position exit for priority handling
            }
            
            # Execute with DOM Intelligence validation and emergency bypass capability
            result = execute_exit_positions_with_validation(
                self.tab, symbol, option, context=validation_context
            )
            
            # Wait a moment for console logs to be generated
            time.sleep(0.5)
            
            # Get console logs generated during exit execution
            console_logs = self.get_console_logs(limit=30)
            
            # Enhanced result processing for DOM Intelligence integration
            if isinstance(result, dict) and 'dom_intelligence_enabled' in result:
                # DOM Intelligence result structure
                result['console_logs'] = console_logs.get('logs', [])
                result['health_at_execution'] = health_check
                result['exit_executed'] = result.get('overall_success', False)
                
                # Log DOM Intelligence metrics for position exits
                validation_result = result.get('validation_result', {})
                if validation_result.get('emergency_bypass', False):
                    print(f"⚠️  Emergency bypass used for position exit: {validation_result.get('message', 'Unknown reason')}")
                
                if not validation_result.get('success', True):
                    print(f"⚠️  DOM validation warning for exit: {validation_result.get('message', 'Validation failed')}")
                
            else:
                # Legacy result structure (fallback)
                if isinstance(result, dict):
                    result['console_logs'] = console_logs.get('logs', [])
                    result['health_at_execution'] = health_check
                    result['exit_executed'] = True
                else:
                    # Ensure result is a dict for consistency
                    result = {
                        'exit_result': result,
                        'console_logs': console_logs.get('logs', []),
                        'health_at_execution': health_check,
                        'exit_executed': True
                    }
            
            return result
        except Exception as e:
            return {
                "error": str(e),
                "health_at_execution": health_check,
                "exit_executed": False
            }
            
    def update_symbol(self, symbol):
        """Update the symbol in Tradovate's interface with DOM Intelligence validation and state sync"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            # Use DOM Intelligence validation for symbol update
            from src.utils.chrome_communication import execute_symbol_update_with_validation, sync_symbol_across_tabs
            
            # Get tab ID for synchronization
            tab_id = getattr(self.tab, 'id', f'tab_{self.username}')
            
            # Prepare context for validation
            validation_context = {
                'high_frequency_mode': False,
                'symbol_change': True  # Mark as symbol change operation
            }
            
            # Execute with DOM Intelligence validation
            result = execute_symbol_update_with_validation(
                self.tab, symbol, context=validation_context
            )
            
            # If symbol update was successful, sync across other tabs
            if result.get('overall_success', False):
                sync_result = sync_symbol_across_tabs(tab_id, symbol)
                result['sync_result'] = sync_result
                
                if sync_result.get('success', False):
                    print(f"Symbol synced to {len(sync_result.get('synced_tabs', []))} tabs")
                else:
                    print(f"Symbol sync warning: {sync_result.get('error', 'Unknown error')}")
            
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def run_risk_management(self):
        """Run the auto risk management functions with health verification"""
        if not self.tab:
            return {"error": "No tab available"}
        
        # Verify connection health before executing risk management
        health_check = self.check_connection_health()
        if not health_check.get('healthy', False):
            health_errors = health_check.get('errors', ['Connection unhealthy'])
            return {
                "status": "error",
                "error": "Risk management rejected due to connection health issues",
                "health_status": health_check,
                "health_errors": health_errors,
                "risk_management_rejected": True
            }
        
        # Log risk management attempt with health context
        print(f"Running risk management for {self.username} (Health: {health_check.get('healthy', False)})")
            
        try:
            # First check if the required functions exist
            check_code = """
            {
                "getTableData": typeof getTableData === 'function',
                "updateUserColumnPhaseStatus": typeof updateUserColumnPhaseStatus === 'function',
                "performAccountActions": typeof performAccountActions === 'function'
            }
            """
            # Use safe_evaluate to check for required functions
            check_result = safe_evaluate(
                tab=self.tab,
                js_code=check_code,
                operation_type=OperationType.NON_CRITICAL,
                description=f"Check risk management functions for {self.username}"
            )
            
            if check_result.success:
                check_data = json.loads(check_result.value) if isinstance(check_result.value, str) else check_result.value
            else:
                check_data = {}
            
            # If any function is missing, try to re-inject the script
            if not all(check_data.values()):
                print(f"Re-injecting auto risk management script because some functions are missing: {check_data}")
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                risk_management_path = os.path.join(project_root, 
                                            'scripts/tampermonkey/autoriskManagement.js')
                if os.path.exists(risk_management_path):
                    with open(risk_management_path, 'r') as file:
                        risk_management_js = file.read()
                    # Use safe_evaluate to re-inject risk management script
                    result = safe_evaluate(
                        tab=self.tab,
                        js_code=risk_management_js,
                        operation_type=OperationType.CRITICAL,
                        description=f"Re-inject risk management script for {self.username}"
                    )
                    if not result.success:
                        print(f"Failed to re-inject risk management script for {self.username}: {result.error}")
                    # Give it a moment to initialize
                    time.sleep(0.5)
            
            # Run the main auto risk management sequence
            js_code = """
            console.log("Running risk management sequence...");
            try {
                if (typeof getTableData !== 'function') {
                    throw new Error("getTableData function not available");
                }
                getTableData();
                
                if (typeof updateUserColumnPhaseStatus !== 'function') {
                    throw new Error("updateUserColumnPhaseStatus function not available");
                }
                updateUserColumnPhaseStatus();
                
                if (typeof performAccountActions !== 'function') {
                    throw new Error("performAccountActions function not available");
                }
                performAccountActions();
                
                return {status: "success", message: "Risk management sequence completed"};
            } catch (err) {
                return {status: "error", message: err.toString()};
            }
            """
            # Use safe_evaluate to run risk management sequence
            result = safe_evaluate(
                tab=self.tab,
                js_code=js_code,
                operation_type=OperationType.CRITICAL,
                description=f"Run risk management sequence for {self.username}"
            )
            
            if result.success:
                result_data = json.loads(result.value) if isinstance(result.value, str) else result.value
            else:
                result_data = {"status": "error", "error": result.error}
            
            if result_data.get('status') == 'success':
                return {
                    "status": "success", 
                    "message": "Auto risk management executed",
                    "health_at_execution": health_check,
                    "risk_management_executed": True
                }
            else:
                return {
                    "status": "error", 
                    "message": result_data.get('message', 'Unknown error'),
                    "health_at_execution": health_check,
                    "risk_management_executed": False
                }
        except Exception as e:
            return {
                "error": str(e),
                "health_at_execution": health_check,
                "risk_management_executed": False
            }
            
    def get_console_logs(self, limit=None, clear_after=False):
        """Get captured console logs from localStorage
        
        Args:
            limit: Maximum number of logs to return (None for all)
            clear_after: Clear logs after retrieval
            
        Returns:
            List of log entries with timestamp, level, message, and url
        """
        if not self.tab:
            return {"error": "No tab available", "logs": []}
            
        try:
            # Use safe_evaluate to get console logs
            js_code = "JSON.stringify(window.getConsoleLogs())"
            result = safe_evaluate(
                tab=self.tab,
                js_code=js_code,
                operation_type=OperationType.NON_CRITICAL,
                description=f"Get console logs for {self.username}"
            )
            
            if not result.success:
                return {"error": "Failed to retrieve console logs", "logs": []}
                
            # Parse the result
            logs_json = result.value
            if logs_json:
                try:
                    logs_data = json.loads(logs_json) if isinstance(logs_json, str) else logs_json
                except json.JSONDecodeError:
                    print(f"Failed to parse logs JSON: {logs_json}")
                    logs_data = []
            else:
                logs_data = []
            
            # Apply limit if specified
            if limit and isinstance(logs_data, list):
                logs_data = logs_data[-limit:]  # Get last N logs
            
            # Clear logs if requested
            if clear_after:
                # Use safe_evaluate to clear console logs
                safe_evaluate(
                    tab=self.tab,
                    js_code="window.clearConsoleLogs && window.clearConsoleLogs()",
                    operation_type=OperationType.NON_CRITICAL,
                    description=f"Clear console logs for {self.username}"
                )
                
            return {
                "status": "success",
                "logs": logs_data,
                "count": len(logs_data) if isinstance(logs_data, list) else 0
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error getting console logs: {e}")
            return {"error": f"JSON decode error: {str(e)}", "logs": []}
        except Exception as e:
            print(f"Error getting console logs: {e}")
            return {"error": str(e), "logs": []}
    
    def get_account_data(self):
        """Get account data from the tab using the getAllAccountTableData function"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            # Use safe_evaluate to get account data
            result = safe_evaluate(
                tab=self.tab,
                js_code="getAllAccountTableData()",
                operation_type=OperationType.IMPORTANT,
                description=f"Get account data for {self.username}"
            )
            return {"success": result.success, "value": result.value, "error": result.error}
        except Exception as e:
            return {"error": str(e)}
    
    def test_order_validation(self):
        """Test order validation framework functionality"""
        if not self.tab:
            return {"error": "No tab available"}
        
        try:
            # Import the live validation test
            from src.utils.test_order_validation_live import OrderValidationLiveTester
            
            # Create tester instance
            tester = OrderValidationLiveTester(self.tab)
            
            # Run validation tests
            print(f"Running Order Validation tests for {self.username}...")
            results = tester.run_validation_tests()
            
            # Check if we need to use asyncio
            import asyncio
            if asyncio.iscoroutine(results):
                # Handle async execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(results)
                loop.close()
            
            # Log summary
            print(f"\nValidation Test Results:")
            print(f"Total Tests: {results['summary']['total_tests']}")
            print(f"Passed: {results['summary']['passed']}")
            print(f"Failed: {results['summary']['failed']}")
            print(f"Success Rate: {results['summary']['success_rate']}")
            print(f"Duration: {results['summary']['duration']}")
            
            # Add connection health context
            health_check = self.check_connection_health()
            results['health_at_testing'] = health_check
            results['account'] = self.username
            
            return results
            
        except ImportError as e:
            return {
                "error": "Test module not found. Ensure test_order_validation_live.py is in src/utils/",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": f"Test execution failed: {str(e)}",
                "account": self.username
            }

class TradovateController:
    def __init__(self, base_port=9223, max_instances=20):
        self.base_port = base_port
        self.max_instances = max_instances
        self.connections = []
        self.initialize_connections()
        
    def initialize_connections(self, max_instances=None):
        """Find and connect to all available Tradovate instances"""
        if max_instances is None:
            max_instances = self.max_instances
            
        print(f"Scanning for Chrome instances from port {self.base_port} to {self.base_port + max_instances - 1}")
        
        for i in range(max_instances):
            port = self.base_port + i
            try:
                print(f"Attempting to connect to Chrome on port {port}...")
                connection = TradovateConnection(port, f"Account {i+1}")
                if connection.tab:
                    # Only add connections with a valid tab
                    connection.inject_tampermonkey()
                    self.connections.append(connection)
                    print(f"✅ Added connection on port {port} for {connection.account_name}")
                else:
                    print(f"❌ No Tradovate tab found on port {port}")
            except Exception as e:
                # This port might not have a running Chrome instance - log for debugging
                print(f"⚠️  Port {port} not accessible: {str(e)[:100]}...")
                
        print(f"🎯 Found {len(self.connections)} active Tradovate connections")
        if self.connections:
            print("Active connections:")
            for conn in self.connections:
                print(f"  - {conn.account_name} on port {conn.port}")
        else:
            print("⚠️  No connections found. Make sure Chrome instances are running with auto_login.py")
        
    def execute_on_all(self, method_name, *args, **kwargs):
        """Execute a method on all connections"""
        results = []
        for conn in self.connections:
            method = getattr(conn, method_name)
            result = method(*args, **kwargs)
            results.append({
                "account": conn.account_name,
                "port": conn.port,
                "result": result
            })
        return results
        
    def execute_on_one(self, index, method_name, *args, **kwargs):
        """Execute a method on a specific connection by index"""
        if 0 <= index < len(self.connections):
            conn = self.connections[index]
            method = getattr(conn, method_name)
            result = method(*args, **kwargs)
            return {
                "account": conn.account_name,
                "port": conn.port,
                "result": result
            }
        else:
            return {"error": f"Invalid connection index: {index}"}
    
    def test_order_validation_all(self):
        """Run order validation tests on all connections"""
        print("\n=== Running Order Validation Tests on All Connections ===\n")
        
        results = self.execute_on_all('test_order_validation')
        
        # Summarize results
        total_connections = len(results)
        successful_tests = 0
        failed_tests = 0
        
        for result in results:
            account = result['account']
            test_result = result['result']
            
            if 'error' in test_result:
                failed_tests += 1
                print(f"❌ {account}: Test failed - {test_result['error']}")
            else:
                successful_tests += 1
                summary = test_result.get('summary', {})
                print(f"✅ {account}: {summary.get('success_rate', 'N/A')} success rate")
        
        print(f"\n=== Summary ===")
        print(f"Total Connections Tested: {total_connections}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {failed_tests}")
        
        return {
            "total_tested": total_connections,
            "successful": successful_tests,
            "failed": failed_tests,
            "details": results
        }

def main():
    parser = argparse.ArgumentParser(description='Control multiple Tradovate instances via Python')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all active Tradovate connections')
    
    # UI command
    ui_parser = subparsers.add_parser('ui', help='Create the UI')
    ui_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    
    # Trade command
    trade_parser = subparsers.add_parser('trade', help='Execute a trade')
    trade_parser.add_argument('symbol', help='Symbol to trade (e.g., NQ)')
    trade_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    trade_parser.add_argument('--qty', type=int, default=1, help='Quantity to trade')
    trade_parser.add_argument('--action', choices=['Buy', 'Sell'], default='Buy', help='Buy or Sell')
    trade_parser.add_argument('--tp', type=int, default=100, help='Take profit in ticks')
    trade_parser.add_argument('--sl', type=int, default=40, help='Stop loss in ticks')
    trade_parser.add_argument('--tick', type=float, default=0.25, help='Tick size')
    
    # Exit command
    exit_parser = subparsers.add_parser('exit', help='Close positions')
    exit_parser.add_argument('symbol', help='Symbol to close positions for')
    exit_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    exit_parser.add_argument('--option', choices=['cancel-option-Exit-at-Mkt-Cxl', 'cancel-option-Cancel-All'], 
                         default='cancel-option-Exit-at-Mkt-Cxl', help='Exit option')
    
    # Symbol command
    symbol_parser = subparsers.add_parser('symbol', help='Update the symbol')
    symbol_parser.add_argument('symbol', help='Symbol to update to')
    symbol_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    
    # Risk management command
    risk_parser = subparsers.add_parser('risk', help='Run auto risk management')
    risk_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch the dashboard UI')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run order validation tests')
    test_parser.add_argument('--account', type=int, help='Account index (all if not specified)')
    
    args = parser.parse_args()
    
    # Initialize the controller with configurable max instances  
    max_instances = int(os.environ.get('TRADOVATE_MAX_INSTANCES', '20'))
    controller = TradovateController(max_instances=max_instances)
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found. Make sure auto_login.py is running.")
        print(f"Checked ports {controller.base_port} to {controller.base_port + controller.max_instances - 1}")
        return 1
    
    # Execute the requested command
    if args.command == 'list':
        print("\nActive Tradovate Connections:")
        for i, conn in enumerate(controller.connections):
            print(f"  {i}: {conn.account_name} (Port {conn.port})")
    
    elif args.command == 'ui':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'create_ui')
            print(f"Created UI on account {args.account}: {result}")
        else:
            results = controller.execute_on_all('create_ui')
            print(f"Created UI on all {len(results)} accounts")
    
    elif args.command == 'trade':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'auto_trade', 
                                         args.symbol, args.qty, args.action, 
                                         args.tp, args.sl, args.tick)
            print(f"Trade on account {args.account}: {result}")
        else:
            results = controller.execute_on_all('auto_trade', 
                                         args.symbol, args.qty, args.action, 
                                         args.tp, args.sl, args.tick)
            print(f"Trade executed on all {len(results)} accounts")
    
    elif args.command == 'exit':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'exit_positions', 
                                         args.symbol, args.option)
            print(f"Positions closed on account {args.account}: {result}")
        else:
            results = controller.execute_on_all('exit_positions', 
                                         args.symbol, args.option)
            print(f"Positions closed on all {len(results)} accounts")
    
    elif args.command == 'symbol':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'update_symbol', 
                                         args.symbol)
            print(f"Symbol updated on account {args.account}: {result}")
        else:
            results = controller.execute_on_all('update_symbol', args.symbol)
            print(f"Symbol updated on all {len(results)} accounts")
    
    elif args.command == 'risk':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'run_risk_management')
            print(f"Auto risk management executed on account {args.account}: {result}")
        else:
            results = controller.execute_on_all('run_risk_management')
            successes = sum(1 for r in results if r.get('result', {}).get('status') == 'success')
            print(f"Auto risk management executed on {successes} of {len(results)} accounts")
    
    elif args.command == 'dashboard':
        # Ensure all connections have the account data function
        for conn in controller.connections:
            if conn.tab:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                account_data_path = os.path.join(project_root, 
                                          'scripts/tampermonkey/getAllAccountTableData.user.js')
                if os.path.exists(account_data_path):
                    with open(account_data_path, 'r') as file:
                        account_data_js = file.read()
                    # Use safe_evaluate to inject account data function
                    safe_evaluate(
                        tab=conn.tab,
                        js_code=account_data_js,
                        operation_type=OperationType.IMPORTANT,
                        description=f"Inject account data function for {conn.account_name}"
                    )
        
        # Import the dashboard module here to avoid circular imports
        try:
            # Add current directory to Python path for src import
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # First try importing with src. prefix
            from src.dashboard import run_flask_dashboard
        except ImportError:
            # Fall back to direct import (when run from within src directory)
            try:
                from dashboard import run_flask_dashboard
            except ImportError as e:
                print(f"Error loading dashboard module: {e}")
                print("Make sure you're running this script from the project root directory")
                return 1
        
        print("Starting Tradovate dashboard...")
        dashboard_thread = threading.Thread(target=run_flask_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        print("Dashboard running at http://localhost:6001")
        print("Press Ctrl+C to stop")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Dashboard stopped")
    
    elif args.command == 'test':
        if args.account is not None:
            result = controller.execute_on_one(args.account, 'test_order_validation')
            account_info = controller.connections[args.account].account_name if args.account < len(controller.connections) else f"Account {args.account}"
            
            if 'error' in result['result']:
                print(f"\n❌ Test failed on {account_info}:")
                print(f"   {result['result']['error']}")
            else:
                test_result = result['result']
                summary = test_result.get('summary', {})
                print(f"\n✅ Test completed on {account_info}:")
                print(f"   Success Rate: {summary.get('success_rate', 'N/A')}")
                print(f"   Tests Passed: {summary.get('passed', 0)}/{summary.get('total_tests', 0)}")
                
                # Show performance metrics if available
                if 'performance' in test_result:
                    perf = test_result['performance']
                    print(f"   Average Time: {perf.get('average_duration', 0):.2f}ms")
        else:
            # Run tests on all connections
            results = controller.test_order_validation_all()
            print(f"\nOverall Success Rate: {results['successful']}/{results['total_tested']} connections passed")
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())