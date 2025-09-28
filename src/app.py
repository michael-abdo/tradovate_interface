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

# Load the Tampermonkey script
project_root = get_project_root()
tampermonkey_path = project_root / 'scripts' / 'tampermonkey' / 'autoOrder.user.js'
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
            print(f"Injecting Tampermonkey functions for {self.account_name}...")
            self.tab.Runtime.evaluate(expression=tampermonkey_functions)
            
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
            result = self.tab.Runtime.evaluate(expression="createUI();")
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def auto_trade(self, symbol, quantity=1, action='Buy', tp_ticks=100, sl_ticks=40, tick_size=0.25, order_type='MARKET'):
        """Execute an auto trade using the Tampermonkey script"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            js_code = f"autoTrade('{symbol}', {quantity}, '{action}', {tp_ticks}, {sl_ticks}, {tick_size}, '{order_type}');"
            result = self.tab.Runtime.evaluate(expression=js_code)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def exit_positions(self, symbol, option='cancel-option-Exit-at-Mkt-Cxl'):
        """Close all positions for the given symbol"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            js_code = f"clickExitForSymbol(normalizeSymbol('{symbol}'), '{option}');"
            result = self.tab.Runtime.evaluate(expression=js_code)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def update_symbol(self, symbol):
        """Update the symbol in Tradovate's interface"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            js_code = f"updateSymbol('.trading-ticket .search-box--input', normalizeSymbol('{symbol}'));"
            result = self.tab.Runtime.evaluate(expression=js_code)
            return result
        except Exception as e:
            return {"error": str(e)}
            
    def run_risk_management(self):
        """Run the auto risk management functions"""
        if not self.tab:
            return {"error": "No tab available"}
            
        try:
            # First check if the required functions exist
            check_code = """
            {
                "getTableData": typeof getTableData === 'function',
                "updateUserColumnPhaseStatus": typeof updateUserColumnPhaseStatus === 'function',
                "performAccountActions": typeof performAccountActions === 'function'
            }
            """
            check_result = self.tab.Runtime.evaluate(expression=check_code)
            check_data = json.loads(check_result.get('result', {}).get('value', '{}'))
            
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
            result = self.tab.Runtime.evaluate(expression=js_code)
            result_data = json.loads(result.get('result', {}).get('value', '{}'))
            
            if result_data.get('status') == 'success':
                return {"status": "success", "message": "Auto risk management executed"}
            else:
                return {"status": "error", "message": result_data.get('message', 'Unknown error')}
        except Exception as e:
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