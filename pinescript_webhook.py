# webhook_server.py
import subprocess
import threading
import time
import re
import sys
from flask import Flask, request, jsonify
import json
import os

# Import the TradovateController from app.py
# Handle case where __file__ might not be defined
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.append(os.getcwd())
from app import TradovateController

app = Flask(__name__)
PORT = 6000

# Initialize the TradovateController
controller = TradovateController()

def start_ngrok(port: int) -> str | None:
    """
    Launch ngrok using a fixed domain: stonkz92224.ngrok.app
    """
    domain = "stonkz92224.ngrok.app"
    proc = subprocess.Popen(
        ["ngrok", "http", "--domain", domain, str(port), "--log", "stdout"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    pat = re.compile(r"url=(https?://[^\s]+)")
    for _ in range(120):  # ~12s timeout
        line = proc.stdout.readline()
        if "ERR_NGROK_15002" in line:
            proc.terminate()
            print("♨️  Error: Reserved domain requires valid ngrok plan.")
            return None
        if m := pat.search(line):
            if domain in m.group(1):
                print(f"🌐 Ngrok tunnel URL confirmed: {m.group(1)}")
                return m.group(1)
    proc.terminate()
    print("❌ Timeout: ngrok did not confirm the domain in time.")
    return None

def get_target_accounts_for_strategy(strategy_name):
    """Get account indices and account names mapped to a specific strategy"""
    try:
        # Use the current working directory if __file__ is not defined
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()
            
        strategy_file = os.path.join(base_dir, 'strategy_mappings.json')
        if not os.path.exists(strategy_file):
            print(f"Strategy mappings file not found. Using all accounts.")
            return list(range(len(controller.connections))), []
            
        with open(strategy_file, 'r') as f:
            mappings = json.load(f)
            
        # Get the exact account names from strategy_mappings.json
        strategy_accounts = mappings.get("strategy_mappings", {}).get(strategy_name, [])
        print(f"Found strategy accounts for {strategy_name}: {strategy_accounts}")
        
        # If no mappings for this strategy, try DEFAULT strategy
        if not strategy_accounts and strategy_name != "DEFAULT":
            print(f"No accounts mapped for strategy {strategy_name}, using DEFAULT")
            strategy_accounts = mappings.get("strategy_mappings", {}).get("DEFAULT", [])
            print(f"DEFAULT strategy accounts: {strategy_accounts}")
        
        # If still no accounts, use all accounts
        if not strategy_accounts:
            print(f"No DEFAULT mapping or empty, using all accounts")
            return list(range(len(controller.connections))), []
        
        # Include all connections but provide the target account names from strategy_mappings.json
        # This way we'll try to execute on all tabs but switch to the correct accounts before executing
        account_indices = list(range(len(controller.connections)))
        
        print(f"Using all {len(account_indices)} connections but will switch to accounts: {strategy_accounts}")
        
        # Return all indices but with the specific account names to switch to
        return account_indices, strategy_accounts
            
    except Exception as e:
        print(f"Error loading strategy mappings: {e}")
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
        print(f"UI symbol update on account {account_index}: {result_value}")
        return {"status": "success", "message": result_value}
    except Exception as e:
        print(f"Error updating UI symbol on account {account_index}: {e}")
        return {"status": "error", "message": str(e)}

def process_trading_signal(data):
    """
    Process incoming trading signal and execute it on specific accounts based on strategy
    """
    print(f"Processing trade signal: {json.dumps(data, indent=2)}")
    
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
            print(f"Symbol cleaning: Transformed '{original_symbol}' -> '{symbol}'")
    
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
    print(f"Target accounts for strategy {strategy}: {target_account_indices}")
    print(f"Account names for strategy {strategy}: {account_names}")
    
    # Inject the changeAccount.user.js script into each matching browser tab
    # to enable account switching functionality
    print("Injecting account switching functionality...")
    # Use the current working directory if __file__ is not defined
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base_dir = os.getcwd()
    
    account_switcher_path = os.path.join(base_dir, 'tampermonkey/changeAccount.user.js')
    if os.path.exists(account_switcher_path):
        with open(account_switcher_path, 'r') as file:
            account_switcher_js = file.read()
            for i in target_account_indices:
                try:
                    if i < len(controller.connections) and controller.connections[i].tab:
                        controller.connections[i].tab.Runtime.evaluate(expression=account_switcher_js)
                        print(f"Injected account switcher script into connection {i}")
                except Exception as e:
                    print(f"Error injecting account switcher into connection {i}: {e}")
    else:
        print(f"Warning: Account switcher script not found at {account_switcher_path}")
    
    # If this is a Close signal, use closeAll
    if trade_type == "Close":
        print(f"🔴 Closing all positions for {symbol}")
        
        # We'll update the symbol for each account individually just before closing positions
        print(f"🔄 Will update symbol to {symbol} before closing positions for each account")
        
        results = []
        # Execute on each targeted account
        for i, account_index in enumerate(target_account_indices):
            if account_index < len(controller.connections):
                conn = controller.connections[account_index]
                if not conn.tab:
                    print(f"⚠️ Tab not available for connection {account_index}, skipping")
                    results.append({"error": "Tab not available"})
                    continue
                    
                try:
                    # Try each of the target account names in this browser tab
                    account_switch_success = False
                    
                    for account_name in account_names:
                        print(f"🔄 Attempting to switch to account: {account_name} on connection {account_index}")
                        
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
                        
                        print(f"Account switch result: {message} (Success: {success})")
                        
                        if success:
                            account_switch_success = True
                            # Give the UI time to update after successful account switch
                            time.sleep(0.5)
                            break  # Exit the loop if we successfully switched to this account
                        else:
                            print(f"Failed to switch to account {account_name}, trying next account if available")
                    
                    # Only proceed with position closing if account switching was successful
                    if account_switch_success:
                        # First, update the symbol and wait for UI to adjust
                        print(f"Updating symbol to {symbol} on account index {account_index}")
                        symbol_update_result = update_ui_symbol(account_index, symbol)
                        print(f"Symbol update result: {symbol_update_result}")
                        
                        # Add a longer delay after updating symbol to let the UI fully adjust
                        print(f"Waiting for symbol to update and market data to load...")
                        time.sleep(2.0)  # Increased delay for UI to update
                        
                        # Use exit_positions with the Exit-at-Mkt-Cxl option for Close trade type
                        print(f"Closing positions on account index {account_index}")
                        result = controller.execute_on_one(account_index, 'exit_positions', symbol, 'cancel-option-Exit-at-Mkt-Cxl')
                        
                        # Add account info to the result
                        result_with_account = result.copy() if isinstance(result, dict) else {"result": result}
                        result_with_account["account_id"] = account_name  # Use the successful account name
                        result_with_account["account_index"] = account_index
                        result_with_account["account_switch_success"] = True
                        results.append(result_with_account)
                    else:
                        print(f"⚠️ Failed to switch to any account for connection {account_index}, skipping position closing")
                        results.append({
                            "error": "Failed to switch to any account",
                            "account_index": account_index,
                            "account_names_tried": account_names,
                            "account_switch_success": False
                        })
                    
                except Exception as e:
                    print(f"⚠️ Error closing positions on connection {account_index}: {e}")
                    results.append({
                        "error": str(e),
                        "account_index": account_index,
                        "account_names_tried": account_names
                    })
        
        print(f"Close all positions results: {results}")
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
        print(f"Error getting tick size: {e}")
    
    # Calculate TP ticks if TP price is provided
    tp_ticks = 100  # Default TP ticks
    if tp_price and entry_price and tp_price > 0 and entry_price > 0:
        price_diff = abs(tp_price - entry_price)
        if price_diff > 0 and tick_size > 0:
            tp_ticks = int(price_diff / tick_size)
            print(f"Calculated TP ticks: {tp_ticks} (price diff: {price_diff}, tick size: {tick_size})")
    
    # Default SL ticks (typically 40% of TP)
    sl_ticks = int(tp_ticks * 0.4) if tp_ticks else 40
    
    # We'll update the symbol for each account individually just before trade execution
    print(f"🔄 Will update symbol to {symbol} before each trade execution")
            
    # Execute the trade on targeted Tradovate instances
    print(f"🟢 Executing {action} order for {order_qty} {symbol} with TP: {tp_ticks} ticks, SL: {sl_ticks} ticks")
    
    results = []
    # Execute on each targeted account
    for account_index in target_account_indices:
        if account_index < len(controller.connections):
            conn = controller.connections[account_index]
            if not conn.tab:
                print(f"⚠️ Tab not available for connection {account_index}, skipping")
                results.append({"error": "Tab not available"})
                continue
                
            try:
                # Try each of the target account names in this browser tab
                account_switch_success = False
                
                for account_name in account_names:
                    print(f"🔄 Attempting to switch to account: {account_name} on connection {account_index}")
                    
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
                    
                    print(f"Account switch result: {message} (Success: {success})")
                    
                    if success:
                        account_switch_success = True
                        # Give the UI time to update after successful account switch
                        time.sleep(0.5)
                        break  # Exit the loop if we successfully switched to this account
                    else:
                        print(f"Failed to switch to account {account_name}, trying next account if available")
                
                # Only proceed with trade execution if account switching was successful
                if account_switch_success:
                    # First, update the symbol and wait for UI to adjust
                    print(f"Updating symbol to {symbol} on account index {account_index}")
                    symbol_update_result = update_ui_symbol(account_index, symbol)
                    print(f"Symbol update result: {symbol_update_result}")
                    
                    # Add a longer delay after updating symbol to let the UI fully adjust
                    print(f"Waiting for symbol to update and market data to load...")
                    time.sleep(2.0)  # Increased delay for UI to update
                    
                    # Now execute the trade on this account
                    print(f"Executing trade on account index {account_index}")
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
                    print(f"⚠️ Failed to switch to any account for connection {account_index}, skipping trade execution")
                    results.append({
                        "error": "Failed to switch to any account",
                        "account_index": account_index,
                        "account_names_tried": account_names,
                        "account_switch_success": False
                    })
                
            except Exception as e:
                print(f"⚠️ Error executing trade on connection {account_index}: {e}")
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
      </body>
    </html>
    """

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        print("\n=============================================")
        print("📥 WEBHOOK REQUEST RECEIVED")
        print("=============================================")
        
        # Print request metadata
        print(f"Request from: {request.remote_addr}")
        print(f"Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
        print(f"User-Agent: {request.headers.get('User-Agent', 'Not specified')}")
        
        try:
            # Parse the JSON payload
            data = request.get_json(force=True)
            print("\n📋 Webhook Payload:")
            print(json.dumps(data, indent=2))
            
            # Validate required fields
            symbol = data.get("symbol", "")
            if not symbol:
                error_msg = "Missing required field: 'symbol'"
                print(f"⚠️ {error_msg}")
                return jsonify({"status": "error", "message": error_msg}), 400
                
            # Extract and highlight strategy information
            strategy = data.get("strategy", "DEFAULT")
            print(f"\n🎯 Strategy specified in webhook: '{strategy}'")
            
            # Process and execute the trading signal
            if controller.connections:
                print(f"Found {len(controller.connections)} active Tradovate connections")
                result = process_trading_signal(data)
                print("\n✅ Webhook processed successfully")
                print("=============================================\n")
                return jsonify(result), 200
            else:
                error_msg = "No Tradovate connections available. Make sure auto_login.py is running."
                print(f"❌ {error_msg}")
                print("=============================================\n")
                return jsonify({"status": "error", "message": error_msg}), 500
                
        except ValueError as e:
            error_msg = f"Invalid JSON data: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"Raw data: {request.data}")
            print("=============================================\n")
            return jsonify({"status": "error", "message": error_msg}), 400
            
        except Exception as e:
            error_msg = f"Error processing webhook: {str(e)}"
            print(f"❌ {error_msg}")
            print("=============================================\n")
            return jsonify({"status": "error", "message": error_msg}), 500
    
    # Handle browser GET so you see a friendly page
    return (
        "<h3>🔔 Webhook endpoint is alive</h3>"
        "<p>Send a <code>POST</code> with your TradingView JSON here.</p>",
        200,
    )

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    time.sleep(1)  # Let Flask boot

    # Check if we have any Tradovate connections
    if len(controller.connections) == 0:
        print("❌ No Tradovate connections found. Make sure auto_login.py is running.")
        print("Starting server anyway, but trades cannot be executed until connections are available.")
    else:
        print(f"✅ Found {len(controller.connections)} active Tradovate connections")

    url = start_ngrok(PORT)
    if not url:
        print("🛑 Failed to start ngrok with stonkz92224.ngrok.app.")
        print("Webhook server is still accessible at http://localhost:6000/webhook")
    else:
        print("\n🚀 Webhook now accessible at:")
        print(url + "/webhook")