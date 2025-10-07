#!/usr/bin/env python3
import threading
import time
from flask import Flask, render_template, jsonify
import sys
import os
import json

# Import from app.py
from src.app import TradovateController
from flask import request
from .utils.core import (
    get_project_root,
    find_chrome_executable,
    load_json_config,
    setup_logging
)

# Create Flask app
project_root = get_project_root()

# Load trading defaults from config
try:
    trading_config = load_json_config('config/trading_defaults.json')
    TRADING_DEFAULTS = trading_config.get('trading_defaults', {})
    SYMBOL_DEFAULTS = trading_config.get('symbol_defaults', {})
except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
    print(f"Warning: Could not load trading defaults config: {e}")
    print("Using fallback defaults")
    # Fallback defaults
    TRADING_DEFAULTS = {
        "symbol": "NQ",
        "quantity": 10,
        "stop_loss_ticks": 15,
        "take_profit_ticks": 53,
        "tick_size": 0.25,
        "risk_reward_ratio": 3.5
    }
    SYMBOL_DEFAULTS = {}
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'web/static'),
            template_folder=os.path.join(project_root, 'web/templates'))

# Initialize controller
controller = TradovateController()

def inject_account_data_function():
    """Inject the getAllAccountTableData function into all tabs"""
    for conn in controller.connections:
        if conn.tab:
            try:
                # Read the function from the file
                project_root = get_project_root()
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
                # First make sure the getAllAccountTableData function is available
                try:
                    # Re-inject the function to ensure it's available
                    project_root = get_project_root()
                    account_data_path = os.path.join(project_root, 
                                           'scripts/tampermonkey/getAllAccountTableData.user.js')
                    with open(account_data_path, 'r') as file:
                        get_account_data_js = file.read()
                    conn.tab.Runtime.evaluate(expression=get_account_data_js)
                except Exception as inject_err:
                    print(f"Error re-injecting function: {inject_err}")
                
                # Execute the getAllAccountTableData() function in each tab
                result = conn.tab.Runtime.evaluate(
                    expression="getAllAccountTableData()")
                
                if result and 'result' in result and 'value' in result['result']:
                    try:
                        # Parse the JSON result
                        tab_data = json.loads(result['result']['value'])
                        
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

# Helper function to calculate scale in/out orders
def calculate_scale_orders(symbol, quantity, action, entry_price, scale_levels, scale_ticks, tick_size):
    """
    Calculate individual orders for scale in/out positions.
    
    Args:
        symbol: Trading symbol
        quantity: Total quantity to trade
        action: 'Buy' or 'Sell'
        entry_price: Base entry price (if None, uses market orders)
        scale_levels: Number of scale levels
        scale_ticks: Ticks between each level
        tick_size: Symbol tick size
        
    Returns:
        List of order dictionaries with quantity and entry_price for each level
    """
    print(f"\n=== CALCULATE SCALE ORDERS DEBUG ===")
    print(f"Input Parameters:")
    print(f"  Symbol: {symbol}")
    print(f"  Quantity: {quantity}")
    print(f"  Action: {action}")
    print(f"  Entry Price: {entry_price}")
    print(f"  Scale Levels: {scale_levels}")
    print(f"  Scale Ticks: {scale_ticks}")
    print(f"  Tick Size: {tick_size}")
    
    orders = []
    
    # Calculate quantity per level (rounded down)
    qty_per_level = quantity // scale_levels
    remaining_qty = quantity % scale_levels
    
    print(f"Quantity Distribution:")
    print(f"  Qty per level: {qty_per_level}")
    print(f"  Remaining qty: {remaining_qty}")
    
    # If quantity is too small to split, return single order
    if qty_per_level == 0:
        print(f"  WARNING: Quantity too small to split, returning single order")
        return [{
            'quantity': quantity,
            'entry_price': entry_price
        }]
    
    # Calculate prices for each level
    print(f"Calculating {scale_levels} scale levels:")
    for i in range(scale_levels):
        # Add extra quantity to first levels if there's a remainder
        level_qty = qty_per_level + (1 if i < remaining_qty else 0)
        
        # Calculate entry price for this level
        if entry_price is not None:
            # For limit/stop orders, calculate scaled entry prices
            price_offset = i * scale_ticks * tick_size
            
            if action == 'Buy':
                # For Buy: scale down from entry price (better fills)
                level_price = entry_price - price_offset
            else:
                # For Sell: scale up from entry price (better fills)
                level_price = entry_price + price_offset
                
            print(f"  Level {i+1}: {level_qty} contracts @ ${level_price:.2f} (offset: {price_offset})")
        else:
            # For market orders, all levels use None (market)
            level_price = None
            print(f"  Level {i+1}: {level_qty} contracts @ Market")
        
        orders.append({
            'quantity': level_qty,
            'entry_price': level_price
        })
    
    print(f"Total orders created: {len(orders)}")
    print(f"=== END CALCULATE SCALE ORDERS DEBUG ===\n")
    
    return orders

# API endpoint to execute trades
@app.route('/api/trade', methods=['POST'])
def execute_trade():
    try:
        data = request.json
        
        # Extract parameters from request with config defaults
        symbol = data.get('symbol', TRADING_DEFAULTS.get('symbol', 'NQ'))
        quantity = data.get('quantity', TRADING_DEFAULTS.get('quantity', 10))
        action = data.get('action', 'Buy')
        tick_size = data.get('tick_size', TRADING_DEFAULTS.get('tick_size', 0.25))
        entry_price = data.get('entry_price')  # Optional entry price
        
        account_index = data.get('account', 'all')
        
        # Check TP/SL enable flags
        enable_tp = data.get('enable_tp', True)
        enable_sl = data.get('enable_sl', True)
        
        # Extract scale in/out parameters
        scale_in_enabled = data.get('scale_in_enabled', TRADING_DEFAULTS.get('scale_in_enabled', False))
        scale_in_levels = data.get('scale_in_levels', TRADING_DEFAULTS.get('scale_in_levels', 4))
        # Get symbol-specific scale ticks if available
        symbol_config = symbol_defaults.get(symbol, {})
        scale_in_ticks = data.get('scale_in_ticks', symbol_config.get('scale_in_ticks', 20))
        
        # Only get TP/SL values if they are enabled with config defaults
        tp_ticks = data.get('tp_ticks', TRADING_DEFAULTS.get('take_profit_ticks', 53)) if enable_tp else 0
        sl_ticks = data.get('sl_ticks', TRADING_DEFAULTS.get('stop_loss_ticks', 15)) if enable_sl else 0
        
        # Ensure tp_ticks and sl_ticks are integers
        tp_ticks = int(tp_ticks) if tp_ticks else 0
        sl_ticks = int(sl_ticks) if sl_ticks else 0
        
        print(f"Trade request: {symbol} {action} {quantity} TP:{tp_ticks if enable_tp else 'disabled'} SL:{sl_ticks if enable_sl else 'disabled'} Entry:{entry_price if entry_price else 'market'}")
        
        # Always update the Tampermonkey entry price field - either set it or clear it
        if entry_price is not None:
            # JavaScript to set the entry price in Tampermonkey UI
            set_entry_js = f"""
            (function() {{
                try {{
                    const entryPriceInput = document.getElementById('entryPriceInput');
                    if (entryPriceInput) {{
                        entryPriceInput.value = {entry_price};
                        entryPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        entryPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return {{ success: true, message: 'Entry price set to {entry_price}' }};
                    }} else {{
                        return {{ success: false, error: 'Entry price input not found' }};
                    }}
                }} catch (err) {{
                    return {{ success: false, error: err.toString() }};
                }}
            }})();
            """
            
            # Set entry price on all relevant accounts
            if account_index == 'all':
                for conn in controller.connections:
                    if conn.tab:
                        try:
                            conn.tab.Runtime.evaluate(expression=set_entry_js)
                        except Exception as e:
                            print(f"Warning: Failed to set entry price on account: {e}")
            else:
                # Set entry price on specific account
                account_index_int = int(account_index)
                if account_index_int < len(controller.connections) and controller.connections[account_index_int].tab:
                    try:
                        controller.connections[account_index_int].tab.Runtime.evaluate(expression=set_entry_js)
                    except Exception as e:
                        print(f"Warning: Failed to set entry price on account {account_index}: {e}")
        else:
            # Entry price is None - need to clear the Tampermonkey entry price field
            clear_entry_js = """
            (function() {
                try {
                    const entryPriceInput = document.getElementById('entryPriceInput');
                    if (entryPriceInput) {
                        entryPriceInput.value = '';
                        entryPriceInput.dispatchEvent(new Event('input', { bubbles: true }));
                        entryPriceInput.dispatchEvent(new Event('change', { bubbles: true }));
                        return { success: true, message: 'Entry price cleared' };
                    } else {
                        return { success: false, error: 'Entry price input not found' };
                    }
                } catch (err) {
                    return { success: false, error: err.toString() };
                }
            })();
            """
            
            # Clear entry price on all relevant accounts
            if account_index == 'all':
                for conn in controller.connections:
                    if conn.tab:
                        try:
                            conn.tab.Runtime.evaluate(expression=clear_entry_js)
                        except Exception as e:
                            print(f"Warning: Failed to clear entry price on account: {e}")
            else:
                # Clear entry price on specific account
                account_index_int = int(account_index)
                if account_index_int < len(controller.connections) and controller.connections[account_index_int].tab:
                    try:
                        controller.connections[account_index_int].tab.Runtime.evaluate(expression=clear_entry_js)
                    except Exception as e:
                        print(f"Warning: Failed to clear entry price on account {account_index}: {e}")
        
        # Check if we should use scale in/out
        print(f"\n=== SCALE IN/OUT CHECK ===")
        print(f"Scale enabled: {scale_in_enabled}")
        print(f"Scale levels: {scale_in_levels}")
        print(f"Condition met: {scale_in_enabled and scale_in_levels > 1}")
        
        if scale_in_enabled and scale_in_levels > 1:
            print(f"=== EXECUTING SCALE IN/OUT ===")
            
            # Validate scale levels don't exceed quantity
            if scale_in_levels > quantity:
                print(f"ERROR: Scale levels ({scale_in_levels}) exceed quantity ({quantity})")
                return jsonify({
                    'status': 'error',
                    'message': f'Scale levels ({scale_in_levels}) cannot exceed quantity ({quantity})'
                }), 400
            
            try:
                print(f"Calling calculate_scale_orders with:")
                print(f"  symbol={symbol}, quantity={quantity}, action={action}")
                print(f"  entry_price={entry_price}, scale_levels={scale_in_levels}")
                print(f"  scale_ticks={scale_in_ticks}, tick_size={tick_size}")
                
                # Calculate scale orders
                scale_orders = calculate_scale_orders(
                    symbol, quantity, action, entry_price,
                    scale_in_levels, scale_in_ticks, tick_size
                )
                
                print(f"Scale orders calculated: {scale_orders}")
                
                # Validate scale orders were calculated successfully
                if not scale_orders or len(scale_orders) == 0:
                    print(f"ERROR: No scale orders returned from calculate_scale_orders")
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to calculate scale orders'
                    }), 500
                
                print(f"Scale in enabled: {len(scale_orders)} orders calculated")
                
                # For scale orders, we need to execute multiple trades
                # Pass the scale orders as a special parameter
                print(f"Executing scale orders on accounts...")
                
                if account_index == 'all':
                    print(f"Executing on ALL accounts ({len(controller.connections)} connections)")
                    result = controller.execute_on_all(
                        'auto_trade_scale',  # New method for scale orders
                        symbol, 
                        scale_orders,  # Pass array of orders instead of single quantity
                        action, 
                        tp_ticks if enable_tp else 0,
                        sl_ticks if enable_sl else 0,
                        tick_size
                    )
                    print(f"Scale order execution result: {result}")
                    
                    # Check if any scale orders failed
                    failed_accounts = [r for r in result if 'error' in r.get('result', {})]
                    if failed_accounts:
                        print(f"Warning: Scale orders failed on {len(failed_accounts)} accounts: {failed_accounts}")
                else:
                    # Execute on specific account
                    account_index = int(account_index)
                    print(f"Executing on account {account_index}")
                    result = controller.execute_on_one(
                        account_index,
                        'auto_trade_scale',  # New method for scale orders
                        symbol, 
                        scale_orders,  # Pass array of orders instead of single quantity
                        action, 
                        tp_ticks if enable_tp else 0,
                        sl_ticks if enable_sl else 0,
                        tick_size
                    )
                    print(f"Scale order execution result: {result}")
                    
                    # Check if scale order failed
                    if 'error' in result.get('result', {}):
                        print(f"ERROR: Scale order failed: {result['result'].get('error', 'Unknown error')}")
                        return jsonify({
                            'status': 'error',
                            'message': f"Scale order failed: {result['result'].get('error', 'Unknown error')}"
                        }), 500
            except Exception as e:
                print(f"Error calculating/executing scale orders: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to execute scale orders: {str(e)}'
                }), 500
        else:
            # Regular single order execution
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
        
        # Process results and return response
        if account_index == 'all':
            # Count successful trades
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            message = f'{action} trade executed on {accounts_affected} accounts'
            if scale_in_enabled:
                message += f' with {scale_in_levels} scale levels'
        else:
            accounts_affected = 1
            message = f'{action} trade executed on account {account_index}'
            if scale_in_enabled:
                message += f' with {scale_in_levels} scale levels'
        
        return jsonify({
            'status': 'success',
            'message': message,
            'accounts_affected': accounts_affected,
            'scale_orders': scale_in_enabled,
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
        
        # Extract parameters from request with config defaults
        quantity = data.get('quantity', TRADING_DEFAULTS.get('quantity', 10))
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

# API endpoint to move stop losses to breakeven
@app.route('/api/breakeven', methods=['POST'])
def move_to_breakeven():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        account_index = data.get('account', 'all')
        
        # JavaScript code to call the breakeven function
        js_code = f"""
        (function() {{
            try {{
                // Check if moveStopLossToBreakeven function exists
                if (typeof moveStopLossToBreakeven === 'function') {{
                    console.log('Calling moveStopLossToBreakeven for symbol: {symbol}');
                    moveStopLossToBreakeven('{symbol}');
                    return 'Breakeven function executed successfully';
                }} else {{
                    console.error('moveStopLossToBreakeven function not found');
                    return 'Error: moveStopLossToBreakeven function not found';
                }}
            }} catch (err) {{
                console.error('Error executing breakeven:', err);
                return 'Error: ' + err.toString();
            }}
        }})();
        """
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            results = []
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        result = conn.tab.Runtime.evaluate(expression=js_code)
                        result_value = result.get('result', {}).get('value', 'Unknown')
                        results.append({"account": i, "result": result_value})
                    except Exception as e:
                        results.append({"account": i, "error": str(e)})
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if "error" not in r)
            
            return jsonify({
                'status': 'success',
                'message': f'Breakeven action executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            if account_index < len(controller.connections) and controller.connections[account_index].tab:
                try:
                    result = controller.connections[account_index].tab.Runtime.evaluate(expression=js_code)
                    result_value = result.get('result', {}).get('value', 'Unknown')
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Breakeven action executed on account {account_index}',
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

# API endpoint to get trading defaults
@app.route('/api/trading-defaults', methods=['GET'])
def get_trading_defaults():
    try:
        return jsonify({
            'trading_defaults': TRADING_DEFAULTS,
            'symbol_defaults': SYMBOL_DEFAULTS
        }), 200
    except Exception as e:
        print(f"Error getting trading defaults: {e}")
        return jsonify({"error": f"Failed to get trading defaults: {str(e)}"}), 500

# API endpoint to reload trading defaults from config file
@app.route('/api/trading-defaults/reload', methods=['POST'])
def reload_trading_defaults():
    try:
        global TRADING_DEFAULTS, SYMBOL_DEFAULTS
        with open(trading_defaults_path, 'r') as f:
            trading_config = json.load(f)
            # Clear and update dictionaries in place to maintain references
            TRADING_DEFAULTS.clear()
            TRADING_DEFAULTS.update(trading_config.get('trading_defaults', {}))
            SYMBOL_DEFAULTS.clear()
            SYMBOL_DEFAULTS.update(trading_config.get('symbol_defaults', {}))
        return jsonify({"status": "success", "message": "Trading defaults reloaded"}), 200
    except Exception as e:
        print(f"Error reloading trading defaults: {e}")
        return jsonify({"error": f"Failed to reload trading defaults: {str(e)}"}), 500

# API endpoint to get strategy mappings
@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    try:
        project_root = get_project_root()
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
        project_root = get_project_root()
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