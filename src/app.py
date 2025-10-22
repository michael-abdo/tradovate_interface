import pychrome
import os
import sys
import json
import argparse
import threading
import time
from .utils.core import (
    get_project_root,
    find_chrome_executable,
    load_json_config,
    setup_logging
)

project_root = get_project_root()
driver_bundle_path = project_root / 'scripts' / 'tampermonkey' / 'dist' / 'tradovate_auto_driver.js'
ui_bundle_path = project_root / 'scripts' / 'tampermonkey' / 'dist' / 'tradovate_ui_panel.js'

with open(driver_bundle_path, 'r', encoding='utf-8') as file:
    tradovate_auto_driver_bundle = file.read()

with open(ui_bundle_path, 'r', encoding='utf-8') as file:
    tradovate_ui_panel_bundle = file.read()

bootstrap_snippet = """
(function ready(attempt = 0) {
    try {
        if (window.TradoAuto && typeof window.TradoAuto.init === 'function') {
            window.TradoAuto.init({ source: 'python-controller' });
            if (window.TradoUIPanel && typeof window.TradoUIPanel.createInvisibleUI === 'function') {
                window.TradoUIPanel.createInvisibleUI();
            }
        } else if (attempt < 50) {
            setTimeout(function() { ready(attempt + 1); }, 200);
        }
    } catch (err) {
        console.error('[PythonController] Error during TradoAuto bootstrap', err);
    }
})();
"""

class TradovateConnection:
    def __init__(self, port, account_name=None):
        self.port = port
        self.account_name = account_name or f"Account on port {port}"
        self.browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
        self.tab = None
        self.find_tradovate_tab()
        
    def find_tradovate_tab(self):
        """Find a Tradovate tab in the browser"""
        for tab in self.browser.list_tab():
            try:
                tab.start()
                tab.Page.enable()
                result = tab.Runtime.evaluate(expression="document.location.href")
                url = result.get("result", {}).get("value", "")
                
                if "tradovate" in url:
                    self.tab = tab
                    print(f"Found Tradovate tab for {self.account_name}")
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
                    
        print(f"No Tradovate tab found for {self.account_name}")
        
    def inject_tampermonkey(self):
        """Inject the Tampermonkey functions into the tab"""
        if not self.tab:
            print(f"No tab available for {self.account_name}")
            return False
            
        try:
            print(f"Injecting TradoAuto bundles for {self.account_name}...")
            self.tab.Runtime.evaluate(expression=tradovate_auto_driver_bundle)
            self.tab.Runtime.evaluate(expression="(function(){\n  if (typeof window.TradoAuto === 'undefined' && typeof TradovateAutoDriverBundle !== 'undefined') {\n    var candidate = TradovateAutoDriverBundle.default || TradovateAutoDriverBundle;\n    if (candidate) {\n      window.TradoAuto = candidate;\n      if (typeof window.TradoAuto.init === 'function') {\n        window.TradoAuto.init({ source: 'python-controller' });\n      }\n    }\n  }\n})();")
            self.tab.Runtime.evaluate(expression=tradovate_ui_panel_bundle)
            self.tab.Runtime.evaluate(expression=bootstrap_snippet)
            
            # Also inject the getAllAccountTableData function
            project_root = get_project_root()
            account_data_path = os.path.join(project_root, 
                                         'scripts/tampermonkey/getAllAccountTableData.user.js')
            if os.path.exists(account_data_path):
                with open(account_data_path, 'r') as file:
                    account_data_js = file.read()
                self.tab.Runtime.evaluate(expression=account_data_js)
                print(f"Account data function injected for {self.account_name}")
            
            # Inject the autoriskManagement.js script
            risk_management_path = os.path.join(project_root, 
                                         'scripts/tampermonkey/autoriskManagement.js')
            if os.path.exists(risk_management_path):
                with open(risk_management_path, 'r') as file:
                    risk_management_js = file.read()
                # First evaluate the script to define the functions
                self.tab.Runtime.evaluate(expression=risk_management_js)
                print(f"Auto risk management script injected for {self.account_name}")
                
                # Wait a moment for the script to fully initialize
                time.sleep(1)
                
                # Then explicitly run the risk management functions
                self.tab.Runtime.evaluate(expression="""
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
                """)
                print(f"Auto risk management executed for {self.account_name}")
            
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
            result = self.tab.Runtime.evaluate(
                expression="window.TradoUIPanel && window.TradoUIPanel.mount && window.TradoUIPanel.mount({ visible: true });"
            )
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def auto_trade(self, symbol, quantity=1, action='Buy', tp_ticks=100, sl_ticks=40, tick_size=0.25):
        """Execute an auto trade using the Tampermonkey script"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            self.tab.Runtime.evaluate(expression=tradovate_auto_driver_bundle)
            js_code = f"""
            (async () => {{
                console.log('🔥 [DASHBOARD] About to call TradoAuto.autoTrade("{symbol}", {quantity}, "{action}", {tp_ticks}, {sl_ticks}, {tick_size})');
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const resolveDriver = () => {{
                    if (window.TradoAuto && typeof window.TradoAuto.autoTrade === 'function') {{
                        return window.TradoAuto;
                    }}
                    if (typeof window.TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = window.TradovateAutoDriverBundle.default || window.TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.autoTrade === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    if (typeof TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = TradovateAutoDriverBundle.default || TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.autoTrade === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    return null;
                }};
                let driver = resolveDriver();
                for (let attempt = 0; !driver && attempt < 50; attempt++) {{
                    await sleep(120);
                    driver = resolveDriver();
                }}
                if (!driver) {{
                    console.error('TradoAuto.autoTrade not available');
                    return {{ error: 'TradoAuto.autoTrade unavailable' }};
                }}
                const normalizedSymbol = typeof driver.normalizeSymbol === 'function'
                    ? driver.normalizeSymbol('{symbol}')
                    : '{symbol}'.toUpperCase();
                if (driver.state) {{
                    driver.state.symbol = normalizedSymbol;
                }}
                try {{
                    const result = driver.autoTrade(normalizedSymbol, {quantity}, '{action}', {tp_ticks}, {sl_ticks}, {tick_size});
                    if (result && typeof result.then === 'function') {{
                        await result;
                    }}
                }} catch (err) {{
                    console.error('TradoAuto.autoTrade threw', err);
                    return {{ error: err && err.message ? err.message : String(err) }};
                }}
                return {{ status: 'invoked', symbol: normalizedSymbol }};
            }})();
            """
            result = self.tab.Runtime.evaluate(expression=js_code, awaitPromise=True)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def exit_positions(self, symbol, option='cancel-option-Exit-at-Mkt-Cxl'):
        """Close all positions for the given symbol"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            self.tab.Runtime.evaluate(expression=tradovate_auto_driver_bundle)
            js_code = f"""
            (async () => {{
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const resolveDriver = () => {{
                    if (window.TradoAuto && typeof window.TradoAuto.clickExitForSymbol === 'function') {{
                        return window.TradoAuto;
                    }}
                    if (typeof window.TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = window.TradovateAutoDriverBundle.default || window.TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.clickExitForSymbol === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    if (typeof TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = TradovateAutoDriverBundle.default || TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.clickExitForSymbol === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    return null;
                }};
                let driver = resolveDriver();
                for (let attempt = 0; !driver && attempt < 50; attempt++) {{
                    await sleep(120);
                    driver = resolveDriver();
                }}
                if (!driver) {{
                    console.error('TradoAuto.clickExitForSymbol not available');
                    return {{ error: 'TradoAuto.clickExitForSymbol unavailable' }};
                }}
                const normalizedSymbol = typeof driver.normalizeSymbol === 'function'
                    ? driver.normalizeSymbol('{symbol}')
                    : '{symbol}'.toUpperCase();
                driver.clickExitForSymbol(normalizedSymbol, '{option}');
                return {{ status: 'invoked', symbol: normalizedSymbol }};
            }})();
            """
            result = self.tab.Runtime.evaluate(expression=js_code, awaitPromise=True)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def update_symbol(self, symbol):
        """Update the symbol in Tradovate's interface"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            self.tab.Runtime.evaluate(expression=tradovate_auto_driver_bundle)
            js_code = f"""
            (async () => {{
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const resolveDriver = () => {{
                    if (window.TradoAuto && typeof window.TradoAuto.updateSymbol === 'function') {{
                        return window.TradoAuto;
                    }}
                    if (typeof window.TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = window.TradovateAutoDriverBundle.default || window.TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.updateSymbol === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    if (typeof TradovateAutoDriverBundle !== 'undefined') {{
                        const candidate = TradovateAutoDriverBundle.default || TradovateAutoDriverBundle;
                        if (candidate && typeof candidate.updateSymbol === 'function') {{
                            window.TradoAuto = candidate;
                            return candidate;
                        }}
                    }}
                    return null;
                }};
                let driver = resolveDriver();
                for (let attempt = 0; !driver && attempt < 50; attempt++) {{
                    await sleep(120);
                    driver = resolveDriver();
                }}
                if (!driver) {{
                    console.error('TradoAuto.updateSymbol not available');
                    return {{ error: 'TradoAuto.updateSymbol unavailable' }};
                }}
                const normalizedSymbol = typeof driver.normalizeSymbol === 'function'
                    ? driver.normalizeSymbol('{symbol}')
                    : '{symbol}'.toUpperCase();
                driver.updateSymbol('.trading-ticket .search-box--input', normalizedSymbol);
                if (driver.state) {{
                    driver.state.symbol = normalizedSymbol;
                }}
                return {{ status: 'invoked', symbol: normalizedSymbol }};
            }})();
            """
            result = self.tab.Runtime.evaluate(expression=js_code, awaitPromise=True)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def run_risk_management(self):
        """Run the auto risk management functions"""
        print(f"🔄 [DEBUG] run_risk_management() called for account: {self.account_name}")
        if not self.tab:
            print("❌ [DEBUG] No Chrome tab available")
            return {"error": "No tab available"}
            
        print("🔄 [DEBUG] Chrome tab is available, proceeding with risk management")
        try:
            # First check if the required functions exist
            print("🔄 [DEBUG] Checking if required JavaScript functions exist")
            check_code = """
            {
                "getTableData": typeof getTableData === 'function',
                "updateUserColumnPhaseStatus": typeof updateUserColumnPhaseStatus === 'function',
                "performAccountActions": typeof performAccountActions === 'function'
            }
            """
            check_result = self.tab.Runtime.evaluate(expression=check_code)
            check_data = json.loads(check_result.get('result', {}).get('value', '{}'))
            print(f"🔄 [DEBUG] Function check results: {check_data}")
            
            # If any function is missing, try to re-inject the script
            if not all(check_data.values()):
                print(f"Re-injecting auto risk management script because some functions are missing: {check_data}")
                project_root = get_project_root()
                risk_management_path = os.path.join(project_root, 
                                            'scripts/tampermonkey/autoriskManagement.js')
                if os.path.exists(risk_management_path):
                    with open(risk_management_path, 'r') as file:
                        risk_management_js = file.read()
                    self.tab.Runtime.evaluate(expression=risk_management_js)
                    # Give it a moment to initialize
                    time.sleep(0.5)
            
            # Run the main auto risk management sequence
            print("🔄 [DEBUG] About to execute risk management JavaScript sequence")
            js_code = """
            console.log("[DEBUG] 🔄 Starting risk management sequence...");
            try {
                if (typeof getTableData !== 'function') {
                    throw new Error("getTableData function not available");
                }
                console.log("[DEBUG] 🔄 Calling getTableData()");
                getTableData();
                console.log("[DEBUG] ✅ getTableData() completed");
                
                if (typeof updateUserColumnPhaseStatus !== 'function') {
                    throw new Error("updateUserColumnPhaseStatus function not available");
                }
                console.log("[DEBUG] 🔄 Calling updateUserColumnPhaseStatus()");
                updateUserColumnPhaseStatus();
                console.log("[DEBUG] ✅ updateUserColumnPhaseStatus() completed");
                
                if (typeof performAccountActions !== 'function') {
                    throw new Error("performAccountActions function not available");
                }
                console.log("[DEBUG] 🔄 Calling performAccountActions()");
                performAccountActions();
                console.log("[DEBUG] ✅ performAccountActions() completed");
                
                console.log("[DEBUG] ✅ Full risk management sequence completed successfully");
                return {status: "success", message: "Risk management sequence completed"};
            } catch (err) {
                console.error("[DEBUG] ❌ Error in risk management sequence:", err);
                return {status: "error", message: err.toString()};
            }
            """
            result = self.tab.Runtime.evaluate(expression=js_code)
            print(f"🔄 [DEBUG] JavaScript execution result: {result}")
            result_data = json.loads(result.get('result', {}).get('value', '{}'))
            print(f"🔄 [DEBUG] Parsed result data: {result_data}")
            
            if result_data.get('status') == 'success':
                print("✅ [DEBUG] Risk management completed successfully")
                return {"status": "success", "message": "Auto risk management executed"}
            else:
                print(f"❌ [DEBUG] Risk management failed: {result_data.get('message', 'Unknown error')}")
                return {"status": "error", "message": result_data.get('message', 'Unknown error')}
        except Exception as e:
            print(f"❌ [DEBUG] Exception in run_risk_management(): {e}")
            import traceback
            print(f"❌ [DEBUG] Full traceback: {traceback.format_exc()}")
            return {"error": str(e)}
            
    def get_account_data(self):
        """Get account data from the tab using the getAllAccountTableData function"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            result = self.tab.Runtime.evaluate(expression="getAllAccountTableData()")
            return result
        except Exception as e:
            return {"error": str(e)}

class TradovateController:
    def __init__(self, base_port=9223):  # Changed from 9222 to protect that port
        self.base_port = base_port
        self.connections = []
        self.initialize_connections()
        
    def initialize_connections(self, max_instances=10):
        """Find and connect to all available Tradovate instances"""
        for i in range(max_instances):
            port = self.base_port + i
            try:
                connection = TradovateConnection(port, f"Account {i+1}")
                if connection.tab:
                    # Only add connections with a valid tab
                    connection.inject_tampermonkey()
                    self.connections.append(connection)
                    print(f"Added connection on port {port}")
            except Exception as e:
                # This port might not have a running Chrome instance
                pass
                
        print(f"Found {len(self.connections)} active Tradovate connections")
        
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
    
    args = parser.parse_args()
    
    # Initialize the controller
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found. Make sure auto_login.py is running.")
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
                project_root = get_project_root()
                account_data_path = os.path.join(project_root, 
                                          'scripts/tampermonkey/getAllAccountTableData.user.js')
                if os.path.exists(account_data_path):
                    with open(account_data_path, 'r') as file:
                        account_data_js = file.read()
                    conn.tab.Runtime.evaluate(expression=account_data_js)
        
        # Import the dashboard module here to avoid circular imports
        try:
            from src.dashboard import run_flask_dashboard
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
                
        except ImportError as e:
            print(f"Error loading dashboard: {e}")
            print("Make sure dashboard.py exists in the same directory")
            return 1
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
