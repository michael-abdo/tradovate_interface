# webhook_server.py
import subprocess
import threading
import time
import re
import sys
import logging
import json
import os
import signal
import datetime
import traceback
from flask import Flask, request, jsonify, Response
import requests
from werkzeug.serving import is_running_from_reloader
import atexit

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'webhook_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('webhook_server')

# Import the TradovateController from app.py
# Handle case where __file__ might not be defined
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.append(os.getcwd())
from src.app import TradovateController

app = Flask(__name__)
PORT = 6000

# Global variables
controller = None  # Initialize the TradovateController
ngrok_process = None
ngrok_url = None
watchdog_thread = None
reconnect_lock = threading.Lock()
is_shutting_down = False
last_request_time = time.time()
health_check_interval = 30  # seconds

def initialize_controller():
    """Initialize or reinitialize the TradovateController"""
    global controller
    try:
        logger.info("Initializing TradovateController...")
        controller = TradovateController()
        if len(controller.connections) == 0:
            logger.warning("No Tradovate connections found. Make sure auto_login.py is running.")
            return False
        logger.info(f"Successfully initialized controller with {len(controller.connections)} connections")
        return True
    except Exception as e:
        logger.error(f"Error initializing controller: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def start_ngrok(port: int) -> str | None:
    """
    Launch ngrok using a fixed domain: stonkz92224.ngrok.app
    Returns the ngrok URL if successful, None otherwise
    """
    global ngrok_process
    
    try:
        domain = "stonkz92224.ngrok.app"
        logger.info(f"Starting ngrok with domain: {domain}")
        
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "--domain", domain, str(port), "--log", "stdout"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        
        pat = re.compile(r"url=(https?://[^\s]+)")
        for _ in range(120):  # ~12s timeout
            if ngrok_process.poll() is not None:
                logger.error("ngrok process terminated unexpectedly")
                return None
                
            line = ngrok_process.stdout.readline()
            logger.debug(f"ngrok output: {line.strip()}")
            
            if "ERR_NGROK_15002" in line:
                ngrok_process.terminate()
                logger.error("Error: Reserved domain requires valid ngrok plan.")
                return None
            if m := pat.search(line):
                if domain in m.group(1):
                    url = m.group(1)
                    logger.info(f"Ngrok tunnel URL confirmed: {url}")
                    
                    # Verify the tunnel is working
                    try:
                        resp = requests.get(f"{url}/", timeout=5)
                        logger.info(f"Tunnel test response: {resp.status_code}")
                    except Exception as e:
                        logger.warning(f"Tunnel test failed: {e}")
                        
                    return url
                    
        logger.error("Timeout: ngrok did not confirm the domain in time.")
        if ngrok_process and ngrok_process.poll() is None:
            ngrok_process.terminate()
        return None
        
    except Exception as e:
        logger.error(f"Error starting ngrok: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def restart_ngrok():
    """Restart the ngrok process and reconnect"""
    global ngrok_process, ngrok_url
    
    with reconnect_lock:
        logger.info("Restarting ngrok connection...")
        
        # Terminate existing process if it exists
        if ngrok_process and ngrok_process.poll() is None:
            try:
                ngrok_process.terminate()
                ngrok_process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating ngrok process: {e}")
                
        # Start a new ngrok process
        ngrok_url = start_ngrok(PORT)
        if ngrok_url:
            logger.info(f"Successfully restarted ngrok tunnel: {ngrok_url}")
            return True
        else:
            logger.error("Failed to restart ngrok tunnel")
            return False

def check_chrome_connections():
    """Check if Chrome connections are still active and reconnect if needed"""
    global controller
    
    with reconnect_lock:
        if not controller or len(controller.connections) == 0:
            logger.warning("No active Chrome connections, attempting to reinitialize controller...")
            return initialize_controller()
            
        # Check each connection
        reconnection_needed = False
        for conn in controller.connections:
            try:
                if not conn.tab:
                    logger.warning(f"Tab not available for {conn.account_name}, reconnection needed")
                    reconnection_needed = True
                    continue
                    
                # Test the connection by evaluating a simple expression
                conn.tab.Runtime.evaluate(expression="1+1")
            except Exception as e:
                logger.warning(f"Connection test failed for {conn.account_name}: {e}")
                reconnection_needed = True
                
        if reconnection_needed:
            logger.info("Reinitializing all Chrome connections...")
            return initialize_controller()
        
        logger.debug("All Chrome connections are active")
        return True

def is_ngrok_tunnel_active():
    """Check if the ngrok tunnel is still active"""
    global ngrok_url, ngrok_process
    
    if not ngrok_url or not ngrok_process:
        return False
        
    # Check if the ngrok process is still running
    if ngrok_process.poll() is not None:
        logger.warning("ngrok process has terminated")
        return False
        
    # Try to connect to the tunnel URL
    try:
        resp = requests.get(f"{ngrok_url}/", timeout=5)
        if resp.status_code == 200:
            logger.debug("ngrok tunnel is active")
            return True
        else:
            logger.warning(f"ngrok tunnel check failed with status code: {resp.status_code}")
            return False
    except Exception as e:
        logger.warning(f"ngrok tunnel check failed: {e}")
        return False

def watchdog_routine():
    """Monitor and restart services if they fail"""
    global is_shutting_down, last_request_time
    
    logger.info("Watchdog thread started")
    
    while not is_shutting_down:
        try:
            # Only perform checks if we've been idle for a while
            current_time = time.time()
            time_since_last_request = current_time - last_request_time
            
            if time_since_last_request > health_check_interval:
                logger.info(f"Performing health check (idle for {time_since_last_request:.1f}s)")
                
                # Check Chrome connections
                chrome_ok = check_chrome_connections()
                
                # Check ngrok tunnel
                ngrok_ok = is_ngrok_tunnel_active()
                
                if not ngrok_ok:
                    logger.warning("ngrok tunnel is down, attempting to restart")
                    restart_ngrok()
                    
                logger.info(f"Health check complete: Chrome connections: {'OK' if chrome_ok else 'FAIL'}, " +
                           f"ngrok tunnel: {'OK' if ngrok_ok else 'FAIL'}")
            
            # Sleep for a bit before the next check
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in watchdog routine: {str(e)}")
            logger.debug(traceback.format_exc())
            time.sleep(30)  # Sleep longer on error

def get_target_accounts_for_strategy(strategy_name):
    """Get account indices and account names mapped to a specific strategy"""
    try:
        # Use the current working directory if __file__ is not defined
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()
            
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, 'config/strategy_mappings.json')
        if not os.path.exists(strategy_file):
            logger.warning(f"Strategy mappings file not found. Using all accounts.")
            return list(range(len(controller.connections))), []
            
        with open(strategy_file, 'r') as f:
            mappings = json.load(f)
            
        # Get the exact account names from strategy_mappings.json
        strategy_accounts = mappings.get("strategy_mappings", {}).get(strategy_name, [])
        logger.info(f"Found strategy accounts for {strategy_name}: {strategy_accounts}")
        
        # If no mappings for this strategy, try DEFAULT strategy
        if not strategy_accounts and strategy_name != "DEFAULT":
            logger.info(f"No accounts mapped for strategy {strategy_name}, using DEFAULT")
            strategy_accounts = mappings.get("strategy_mappings", {}).get("DEFAULT", [])
            logger.info(f"DEFAULT strategy accounts: {strategy_accounts}")
        
        # If still no accounts, use all accounts
        if not strategy_accounts:
            logger.info(f"No DEFAULT mapping or empty, using all accounts")
            return list(range(len(controller.connections))), []
        
        # Include all connections but provide the target account names from strategy_mappings.json
        # This way we'll try to execute on all tabs but switch to the correct accounts before executing
        account_indices = list(range(len(controller.connections)))
        
        logger.info(f"Using all {len(account_indices)} connections but will switch to accounts: {strategy_accounts}")
        
        # Return all indices but with the specific account names to switch to
        return account_indices, strategy_accounts
            
    except Exception as e:
        logger.error(f"Error loading strategy mappings: {e}")
        logger.debug(traceback.format_exc())
        # Fallback to all accounts
        return list(range(len(controller.connections))), []

def update_ui_symbol(account_index, symbol):
    """
    Update the symbol in the Tradovate interface and the Bracket UI
    """
    if account_index >= len(controller.connections):
        return {"status": "error", "message": "Invalid account index"}
    
    try:
        # First update the symbol in Tradovate's interface
        controller.execute_on_one(account_index, 'update_symbol', symbol)
        
        # Then update the symbolInput element in the Bracket UI
        update_ui_script = f"""
        (function() {{
            // Update the symbolInput in the Bracket UI
            const symbolInput = document.getElementById('symbolInput');
            if (symbolInput) {{
                symbolInput.value = "{symbol}";
                // Dispatch events to ensure value change is registered
                symbolInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                symbolInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                console.log("Updated UI symbol to {symbol}");
                
                // Also store in localStorage for persistence
                localStorage.setItem('bracketTrade_symbol', "{symbol}");
                return "Symbol updated in UI";
            }} else {{
                return "symbolInput element not found";
            }}
        }})();
        """
        ui_result = controller.connections[account_index].tab.Runtime.evaluate(expression=update_ui_script)
        result_value = ui_result.get('result', {}).get('value', 'Unknown')
        logger.info(f"UI symbol update on account {account_index}: {result_value}")
        return {"status": "success", "message": result_value}
    except Exception as e:
        logger.error(f"Error updating UI symbol on account {account_index}: {e}")
        logger.debug(traceback.format_exc())
        return {"status": "error", "message": str(e)}

def process_trading_signal(data):
    """
    Process incoming trading signal and execute it on specific accounts based on strategy
    """
    logger.info(f"Processing trade signal: {json.dumps(data, indent=2)}")
    
    # Extract the data from the webhook payload
    symbol = data.get("symbol", "")
    
    # Clean the symbol by removing numeric suffixes and exclamation points (e.g., "NQ1!" -> "NQ")
    if symbol:
        original_symbol = symbol
        # First remove any trailing exclamation point
        symbol = symbol.replace('!', '')
        # Then remove any numeric suffixes (like NQ1, ES2, etc.)
        symbol = re.sub(r'(\D+)\d+$', r'\1', symbol)
        if original_symbol != symbol:
            logger.info(f"Symbol cleaning: Transformed '{original_symbol}' -> '{symbol}'")
    
    action = data.get("action", "Buy")  # Buy or Sell
    order_qty = int(data.get("orderQty", 1))
    order_type = data.get("orderType", "Market")
    entry_price = data.get("entryPrice", 0)
    tp_price = data.get("takeProfitPrice", 0)
    trade_type = data.get("tradeType", "Open")  # Open or Close
    strategy = data.get("strategy", "DEFAULT")
    
    # Now processing the already-logged strategy
    
    # Determine target accounts for this strategy
    target_account_indices, account_names = get_target_accounts_for_strategy(strategy)
    logger.info(f"Target accounts for strategy {strategy}: {target_account_indices}")
    logger.info(f"Account names for strategy {strategy}: {account_names}")
    
    # Check if controller has connections
    if not controller or len(controller.connections) == 0:
        logger.warning("No active Chrome connections. Attempting to reinitialize...")
        if not initialize_controller():
            logger.error("Failed to initialize controller. Cannot process trading signal.")
            return {"status": "error", "message": "No Tradovate connections available"}
        # Update target accounts after reinitialization
        target_account_indices, account_names = get_target_accounts_for_strategy(strategy)
    
    # Inject the changeAccount.user.js script into each matching browser tab
    # to enable account switching functionality
    logger.info("Injecting account switching functionality...")
    # Use the current working directory if __file__ is not defined
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base_dir = os.getcwd()
    
    account_switcher_path = os.path.join(base_dir, 'tampermonkey/changeAccount.user.js')
    # Try the new path if the file doesn't exist
    if not os.path.exists(account_switcher_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        account_switcher_path = os.path.join(project_root, 'scripts/tampermonkey/changeAccount.user.js')
    if os.path.exists(account_switcher_path):
        with open(account_switcher_path, 'r') as file:
            account_switcher_js = file.read()
            for i in target_account_indices:
                try:
                    if i < len(controller.connections) and controller.connections[i].tab:
                        controller.connections[i].tab.Runtime.evaluate(expression=account_switcher_js)
                        logger.info(f"Injected account switcher script into connection {i}")
                except Exception as e:
                    logger.error(f"Error injecting account switcher into connection {i}: {e}")
    else:
        logger.warning(f"Warning: Account switcher script not found at {account_switcher_path}")
    
    # If this is a Close signal, use closeAll
    if trade_type == "Close":
        logger.info(f"🔴 Closing all positions for {symbol}")
        
        # We'll update the symbol for each account individually just before closing positions
        logger.info(f"🔄 Will update symbol to {symbol} before closing positions for each account")
        
        results = []
        # Execute on each targeted account
        for i, account_index in enumerate(target_account_indices):
            if account_index < len(controller.connections):
                conn = controller.connections[account_index]
                if not conn.tab:
                    logger.warning(f"⚠️ Tab not available for connection {account_index}, skipping")
                    results.append({"error": "Tab not available"})
                    continue
                    
                try:
                    # Try each of the target account names in this browser tab
                    account_switch_success = False
                    
                    for account_name in account_names:
                        logger.info(f"🔄 Attempting to switch to account: {account_name} on connection {account_index}")
                        
                        # Call the account switching function in the browser context
                        switch_script = f"""
                        (async function() {{
                            try {{
                                // First check which function is available
                                if (typeof changeAccount === 'function') {{
                                    console.log("Using changeAccount function to switch to {account_name}");
                                    const result = await changeAccount('{account_name}');
                                    return {{ success: !result.includes("not found"), message: result }};
                                }} else if (typeof clickAccountItemByName === 'function') {{
                                    console.log("Using clickAccountItemByName function to switch to {account_name}");
                                    const result = clickAccountItemByName('{account_name}');
                                    return {{ success: result, message: "Called clickAccountItemByName for account {account_name}" }};
                                }} else {{
                                    return {{ success: false, message: "No account switching function available" }};
                                }}
                            }} catch (error) {{
                                console.error("Error switching account:", error);
                                return {{ success: false, message: "Error switching account: " + error.toString() }};
                            }}
                        }})();
                        """
                        
                        switch_result = conn.tab.Runtime.evaluate(expression=switch_script)
                        switch_response = switch_result.get('result', {}).get('value', {})
                        
                        # Parse the success status from the response
                        success = False
                        message = "Unknown result"
                        
                        if isinstance(switch_response, str):
                            # Handle string responses for backward compatibility
                            message = switch_response
                            success = "not found" not in switch_response.lower()
                        elif isinstance(switch_response, dict):
                            # Handle structured responses
                            success = switch_response.get('success', False)
                            message = switch_response.get('message', "Unknown result")
                        
                        logger.info(f"Account switch result: {message} (Success: {success})")
                        
                        if success:
                            account_switch_success = True
                            # Give the UI time to update after successful account switch
                            time.sleep(0.5)
                            break  # Exit the loop if we successfully switched to this account
                        else:
                            logger.warning(f"Failed to switch to account {account_name}, trying next account if available")
                    
                    # Only proceed with position closing if account switching was successful
                    if account_switch_success:
                        # First, update the symbol and wait for UI to adjust
                        logger.info(f"Updating symbol to {symbol} on account index {account_index}")
                        symbol_update_result = update_ui_symbol(account_index, symbol)
                        logger.info(f"Symbol update result: {symbol_update_result}")
                        
                        # Add a longer delay after updating symbol to let the UI fully adjust
                        logger.info(f"Waiting for symbol to update and market data to load...")
                        time.sleep(2.0)  # Increased delay for UI to update
                        
                        # Use exit_positions with the Exit-at-Mkt-Cxl option for Close trade type
                        logger.info(f"Closing positions on account index {account_index}")
                        result = controller.execute_on_one(account_index, 'exit_positions', symbol, 'cancel-option-Exit-at-Mkt-Cxl')
                        
                        # Add account info to the result
                        result_with_account = result.copy() if isinstance(result, dict) else {"result": result}
                        result_with_account["account_id"] = account_name  # Use the successful account name
                        result_with_account["account_index"] = account_index
                        result_with_account["account_switch_success"] = True
                        results.append(result_with_account)
                    else:
                        logger.warning(f"⚠️ Failed to switch to any account for connection {account_index}, skipping position closing")
                        results.append({
                            "error": "Failed to switch to any account",
                            "account_index": account_index,
                            "account_names_tried": account_names,
                            "account_switch_success": False
                        })
                    
                except Exception as e:
                    logger.error(f"⚠️ Error closing positions on connection {account_index}: {e}")
                    logger.debug(traceback.format_exc())
                    results.append({
                        "error": str(e),
                        "account_index": account_index,
                        "account_names_tried": account_names
                    })
        
        logger.info(f"Close all positions results: {results}")
        return {
            "status": "closed_all", 
            "symbol": symbol, 
            "strategy": strategy,
            "target_accounts": target_account_indices,
            "results": results
        }
    
    # Otherwise, it's an open signal - calculate TP and SL in ticks
    # Get the tick size from the first connection (assuming consistent across all)
    # Process symbol for lookup in futuresTickData
    # Remove USD suffix if present and ensure any other suffixes are removed
    lookup_symbol = symbol.replace('USD', '')
    # Double-check that we have a clean base symbol (no suffixes)
    lookup_symbol = re.sub(r'(\D+)\d+$', r'\1', lookup_symbol)
    tick_size = 0.25  # Default tick size
    
    try:
        if controller.connections:
            js_code = f"futuresTickData['{lookup_symbol}']?.tickSize || 0.25;"
            tick_size_result = controller.connections[0].tab.Runtime.evaluate(expression=js_code)
            if tick_size_result and 'result' in tick_size_result and 'value' in tick_size_result['result']:
                tick_size = float(tick_size_result['result']['value'])
    except Exception as e:
        logger.error(f"Error getting tick size: {e}")
    
    # Calculate TP ticks if TP price is provided
    tp_ticks = 100  # Default TP ticks
    if tp_price and entry_price and tp_price > 0 and entry_price > 0:
        price_diff = abs(tp_price - entry_price)
        if price_diff > 0 and tick_size > 0:
            tp_ticks = int(price_diff / tick_size)
            logger.info(f"Calculated TP ticks: {tp_ticks} (price diff: {price_diff}, tick size: {tick_size})")
    
    # Default SL ticks (typically 40% of TP)
    sl_ticks = int(tp_ticks * 0.4) if tp_ticks else 40
    
    # We'll update the symbol for each account individually just before trade execution
    logger.info(f"🔄 Will update symbol to {symbol} before each trade execution")
            
    # Execute the trade on targeted Tradovate instances
    logger.info(f"🟢 Executing {action} order for {order_qty} {symbol} with TP: {tp_ticks} ticks, SL: {sl_ticks} ticks")
    
    results = []
    # Execute on each targeted account
    for account_index in target_account_indices:
        if account_index < len(controller.connections):
            conn = controller.connections[account_index]
            if not conn.tab:
                logger.warning(f"⚠️ Tab not available for connection {account_index}, skipping")
                results.append({"error": "Tab not available"})
                continue
                
            try:
                # Try each of the target account names in this browser tab
                account_switch_success = False
                
                for account_name in account_names:
                    logger.info(f"🔄 Attempting to switch to account: {account_name} on connection {account_index}")
                    
                    # Check if the account exists in the available accounts list
                    # This is a more reliable approach that avoids Promise handling issues
                    switch_script = f"""
                    (function() {{
                        // Add console.debug for all return values to verify they're properly formatted
                        function debugReturn(result) {{
                            console.debug("Returning to Python:", JSON.stringify(result));
                            return result;
                        }}
                        
                        try {{
                            // First check if the account exists in the dropdown
                            // Do this by clicking the dropdown and checking the account items
                            const accountSelector = document.querySelector('.pane.account-selector.dropdown [data-toggle="dropdown"]');
                            if (!accountSelector) {{
                                return debugReturn({{ 
                                    success: false, 
                                    message: "Account selector not found" 
                                }});
                            }}
                            
                            // Check if we're already on the account
                            const currentAccountElement = accountSelector.querySelector('.name div');
                            if (currentAccountElement) {{
                                const currentAccount = currentAccountElement.textContent.trim();
                                console.log(`Current account is: "${{currentAccount}}"`);
                                
                                if (currentAccount === "{account_name}") {{
                                    console.log(`Already on the exact account: ${{currentAccount}}`);
                                    return debugReturn({{ 
                                        success: true, 
                                        message: `Already on account: ${{currentAccount}}`,
                                        availableAccounts: [currentAccount]
                                    }});
                                }}
                            }}
                            
                            // Click to open the dropdown
                            accountSelector.click();
                            
                            // Get all available accounts
                            const availableAccounts = [];
                            const accountItems = document.querySelectorAll('.dropdown-menu li a.account');
                            accountItems.forEach(item => {{
                                const mainDiv = item.querySelector('.name .main');
                                if (mainDiv) {{
                                    availableAccounts.push(mainDiv.textContent.trim());
                                }} else {{
                                    availableAccounts.push(item.textContent.trim());
                                }}
                            }});
                            
                            console.log(`Available accounts: ${{JSON.stringify(availableAccounts)}}`);
                            
                            // Check if the target account is in the list
                            const accountExists = availableAccounts.includes("{account_name}");
                            
                            // Close the dropdown by clicking elsewhere
                            document.body.click();
                            
                            if (accountExists) {{
                                console.log(`Account {account_name} exists in available accounts. Proceeding with switch.`);
                                
                                // Don't wait for the Promise, just initiate the switch
                                if (typeof changeAccount === 'function') {{
                                    changeAccount('{account_name}');
                                }} else if (typeof clickAccountItemByName === 'function') {{
                                    clickAccountItemByName('{account_name}');
                                }}
                                
                                return debugReturn({{ 
                                    success: true, 
                                    message: `Account exists and switch initiated: {account_name}`,
                                    availableAccounts: availableAccounts
                                }});
                            }} else {{
                                console.error(`Account {account_name} not found in available accounts.`);
                                return debugReturn({{ 
                                    success: false, 
                                    message: `Account not found: {account_name}`,
                                    availableAccounts: availableAccounts
                                }});
                            }}
                        }} catch (error) {{
                            console.error("Error checking/switching account:", error);
                            return debugReturn({{ 
                                success: false, 
                                message: `Error: ${{error.toString()}}` 
                            }});
                        }}
                    }})();
                    """
                    
                    switch_result = conn.tab.Runtime.evaluate(expression=switch_script)
                    
                    # Log the raw response from JavaScript
                    logger.debug(f"DEBUG - Raw switch_result: {switch_result}")
                    
                    # Try to extract the value with more verbose logging
                    result_obj = switch_result.get('result', {})
                    logger.debug(f"DEBUG - Result object: {result_obj}")
                    
                    # Check if we got a Promise or an empty object reference
                    if result_obj.get('subtype') == 'promise' or (result_obj.get('type') == 'object' and 'objectId' in result_obj):
                        logger.debug(f"DEBUG - Detected non-serializable object, forcing success for {account_name}")
                        switch_response = {
                            'success': True,
                            'message': f"Object reference detected, assuming success for {account_name}",
                            'availableAccounts': [account_name]
                        }
                    else:
                        # Get the value property or empty dict if not present
                        switch_response = result_obj.get('value', {})
                        
                    logger.debug(f"DEBUG - Extracted switch_response: {switch_response}")
                    logger.debug(f"DEBUG - Response type: {type(switch_response)}")
                    
                    # Parse the success status from the response
                    success = False
                    message = "Unknown result"
                    available_accounts = []
                    
                    if isinstance(switch_response, str):
                        # Handle string responses for backward compatibility
                        message = switch_response
                        success = "already on account" in switch_response.lower() or "account exists" in switch_response.lower()
                    elif isinstance(switch_response, dict):
                        # Handle structured responses
                        success = switch_response.get('success', False)
                        message = switch_response.get('message', "Unknown result")
                        available_accounts = switch_response.get('availableAccounts', [])
                        
                        # Log the available accounts if present
                        if available_accounts:
                            logger.info(f"Available accounts in dropdown: {available_accounts}")
                            # If our target account is in the list, ensure success is true
                            if account_name in available_accounts:
                                success = True
                    
                    logger.info(f"Account switch result: {message} (Success: {success})")
                    
                    if success:
                        account_switch_success = True
                        # Give the UI time to update after successful account switch
                        time.sleep(0.5)
                        break  # Exit the loop if we successfully switched to this account
                    else:
                        logger.warning(f"Failed to switch to account {account_name}, trying next account if available")
                
                # Only proceed with trade execution if account switching was successful
                if account_switch_success:
                    # First, update the symbol and wait for UI to adjust
                    logger.info(f"Updating symbol to {symbol} on account index {account_index}")
                    symbol_update_result = update_ui_symbol(account_index, symbol)
                    logger.info(f"Symbol update result: {symbol_update_result}")
                    
                    # Add a longer delay after updating symbol to let the UI fully adjust
                    logger.info(f"Waiting for symbol to update and market data to load...")
                    time.sleep(2.0)  # Increased delay for UI to update
                    
                    # Now execute the trade on this account
                    logger.info(f"Executing trade on account index {account_index}")
                    result = controller.execute_on_one(
                        account_index, 'auto_trade', 
                        symbol, order_qty, action, 
                        tp_ticks, sl_ticks, tick_size
                    )
                    
                    # Add account info to the result
                    result_with_account = result.copy() if isinstance(result, dict) else {"result": result}
                    result_with_account["account_id"] = account_name  # Use the correct account name
                    result_with_account["account_index"] = account_index
                    result_with_account["account_switch_success"] = True
                    results.append(result_with_account)
                else:
                    logger.warning(f"⚠️ Failed to switch to any account for connection {account_index}, skipping trade execution")
                    results.append({
                        "error": "Failed to switch to any account",
                        "account_index": account_index,
                        "account_names_tried": account_names,
                        "account_switch_success": False
                    })
                
            except Exception as e:
                logger.error(f"⚠️ Error executing trade on connection {account_index}: {e}")
                logger.debug(traceback.format_exc())
                results.append({
                    "error": str(e),
                    "account_index": account_index,
                    "account_names_tried": account_names
                })
    
    return {
        "status": "executed", 
        "symbol": symbol, 
        "action": action,
        "quantity": order_qty,
        "tp_ticks": tp_ticks,
        "sl_ticks": sl_ticks,
        "strategy": strategy,
        "target_accounts": target_account_indices,
        "results": results
    }

@app.route('/')
def home():
    return """
    <html>
      <head><title>Webhook Server</title></head>
      <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 100px;">
        <h1>✅ Server is Running</h1>
        <p>Waiting for webhooks at <b>/webhook</b> endpoint.</p>
        <p><small>Last updated: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</small></p>
      </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    global controller
    
    # Basic health check
    status = {
        "status": "ok",
        "time": datetime.datetime.now().isoformat(),
        "uptime": time.time() - last_request_time,
        "controller": bool(controller),
        "connections": len(controller.connections) if controller else 0,
        "ngrok_url": ngrok_url,
        "ngrok_process_running": ngrok_process is not None and ngrok_process.poll() is None,
    }
    
    # Check Chrome connections (lightweight check)
    if controller and controller.connections:
        live_connections = 0
        for conn in controller.connections:
            if conn.tab:
                live_connections += 1
        status["live_connections"] = live_connections
    
    return jsonify(status)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    global last_request_time
    
    # Update the last request time
    last_request_time = time.time()
    
    if request.method == 'POST':
        logger.info("\n=============================================")
        logger.info("📥 WEBHOOK REQUEST RECEIVED")
        logger.info("=============================================")
        
        # Print request metadata
        logger.info(f"Request from: {request.remote_addr}")
        logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
        logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Not specified')}")
        
        # Log the raw request data for debugging
        raw_data = request.get_data(as_text=True)
        logger.debug(f"Raw request data: {raw_data}")
        
        try:
            # Try to parse the JSON data
            try:
                data = request.get_json(force=True)
                logger.info("\n📋 Webhook Payload:")
                logger.info(json.dumps(data, indent=2))
            except ValueError as json_err:
                # If JSON parsing fails, check for alternative formats
                if request.headers.get('Content-Type', '').startswith('text/plain'):
                    # Try to extract JSON from the text
                    raw_text = request.get_data(as_text=True).strip()
                    
                    # Try to find a JSON object in the text
                    try:
                        # Look for patterns like {key:value} or {"key":"value"}
                        json_pattern = re.search(r'({[^}]+})', raw_text)
                        if json_pattern:
                            extracted_json = json_pattern.group(1)
                            logger.info(f"Extracted potential JSON: {extracted_json}")
                            data = json.loads(extracted_json)
                            logger.info("Successfully parsed JSON from text content")
                        else:
                            # Try to construct JSON from key-value format
                            lines = raw_text.split('\n')
                            data = {}
                            for line in lines:
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    key = key.strip()
                                    value = value.strip()
                                    # Try to convert numeric values
                                    try:
                                        if '.' in value:
                                            value = float(value)
                                        else:
                                            value = int(value)
                                    except ValueError:
                                        pass
                                    data[key] = value
                            
                            if not data:
                                raise ValueError("Could not extract structured data from text content")
                    except Exception as text_err:
                        error_msg = f"Failed to parse text content: {str(text_err)}\nRaw data: {raw_text}"
                        logger.error(error_msg)
                        return jsonify({"status": "error", "message": error_msg}), 400
                else:
                    error_msg = f"Invalid JSON data: {str(json_err)}\nRaw data: {raw_data}"
                    logger.error(error_msg)
                    return jsonify({"status": "error", "message": error_msg}), 400
            
            # Validate required fields
            symbol = data.get("symbol", "")
            if not symbol:
                error_msg = "Missing required field: 'symbol'"
                logger.warning(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 400
                
            # Extract and highlight strategy information
            strategy = data.get("strategy", "DEFAULT")
            logger.info(f"\n🎯 Strategy specified in webhook: '{strategy}'")
            
            # Check if controller is initialized and has connections
            if not controller or len(controller.connections) == 0:
                logger.warning("No active controller or connections. Attempting to initialize...")
                initialize_controller()
            
            # Process and execute the trading signal
            if controller and controller.connections:
                logger.info(f"Found {len(controller.connections)} active Tradovate connections")
                result = process_trading_signal(data)
                logger.info("\n✅ Webhook processed successfully")
                logger.info("=============================================\n")
                return jsonify(result), 200
            else:
                error_msg = "No Tradovate connections available. Make sure auto_login.py is running."
                logger.error(error_msg)
                logger.info("=============================================\n")
                return jsonify({"status": "error", "message": error_msg}), 500
                
        except Exception as e:
            error_msg = f"Error processing webhook: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            logger.info("=============================================\n")
            return jsonify({"status": "error", "message": error_msg}), 500
    
    # Handle browser GET so you see a friendly page
    return (
        "<h3>🔔 Webhook endpoint is alive</h3>"
        "<p>Send a <code>POST</code> with your TradingView JSON here.</p>"
        f"<p><small>Server time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>",
        200,
    )

def cleanup():
    """Clean up resources before shutdown"""
    global ngrok_process, is_shutting_down
    
    is_shutting_down = True
    logger.info("Shutting down webhook server...")
    
    # Terminate ngrok process
    if ngrok_process and ngrok_process.poll() is None:
        try:
            logger.info("Terminating ngrok process...")
            ngrok_process.terminate()
            ngrok_process.wait(timeout=5)
        except Exception as e:
            logger.error(f"Error terminating ngrok process: {e}")
    
    logger.info("Webhook server shutdown complete")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    cleanup()
    sys.exit(0)

def run_flask(debug=False):
    """Run the Flask application"""
    global controller, watchdog_thread, ngrok_url
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # Initialize the controller if we're the main process (not a reloader)
    if not is_running_from_reloader():
        logger.info("Initializing TradovateController...")
        initialize_controller()
        
        # Start the watchdog thread to monitor connections
        watchdog_thread = threading.Thread(target=watchdog_routine)
        watchdog_thread.daemon = True
        watchdog_thread.start()
        
        # Start ngrok (only in the main process, not reloader)
        ngrok_url = start_ngrok(PORT)
        if not ngrok_url:
            logger.warning("Failed to start ngrok. Webhook server is still accessible locally.")
        else:
            logger.info(f"Webhook now accessible at: {ngrok_url}/webhook")
    
    try:
        # Start the Flask app
        app.run(host='0.0.0.0', port=PORT, debug=debug)
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    # Check if we have any Tradovate connections
    initialize_controller()
    if controller and len(controller.connections) == 0:
        logger.warning("No Tradovate connections found. Make sure auto_login.py is running.")
        logger.info("Starting server anyway, but trades cannot be executed until connections are available.")
    else:
        logger.info(f"Found {len(controller.connections)} active Tradovate connections")
    
    # Start the Flask thread in the main thread
    run_flask(debug=False)