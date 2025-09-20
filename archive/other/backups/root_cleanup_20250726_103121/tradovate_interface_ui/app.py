import os
import requests
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Import from the app package
from app import create_app
from app.services.tradovate_service import get_service_instance
from app.models.account import Account
from app.utils.contract_utils import get_current_contract

# Store cash snapshots for accounts
account_cash_snapshots = {}
print("DEBUG: Initialized empty account_cash_snapshots dictionary.")
print(f"DEBUG: account_cash_snapshots id: {id(account_cash_snapshots)}")

# Function to get cash balance snapshot with retry
def get_cash_snapshot(access_token, account_id, max_retries=3):
    url = "https://demo.tradovateapi.com/v1/cashBalance/getcashbalancesnapshot"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {"accountId": account_id}
    
    retries = 0
    while retries < max_retries:
        try:
            print(f"Attempt {retries+1} to get cash snapshot for account {account_id}")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            print(f"Successfully got cash snapshot on attempt {retries+1}")
            return result
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"Error getting cash snapshot (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                print(f"Waiting 1 second before retry...")
                time.sleep(1)
            else:
                print("All retries failed")
                raise
    
    return None  # Should not reach here, but just in case

# Function to calculate realized PnL difference
def calculate_realized_pnl_diff(begin_snapshot, end_snapshot):
    begin_realized_pnl = begin_snapshot.get("realizedPnL", 0)
    end_realized_pnl = end_snapshot.get("realizedPnL", 0)
    diff = end_realized_pnl - begin_realized_pnl
    
    # Format the values for clear logging
    print("\n===== REALIZED PNL CALCULATION =====")
    print(f"INITIAL REALIZED PNL: ${begin_realized_pnl:.2f}")
    print(f"FINAL REALIZED PNL:   ${end_realized_pnl:.2f}")
    print(f"PROFIT DIFFERENCE:    ${diff:.2f}")
    print("====================================\n")
    
    return diff

# Create the main application
app = create_app()

# Add new UI route
@app.route('/')
def index():
    return render_template('index.html')

# Add API to get accounts and their details
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = Account.get_accounts()
    accounts_list = [
        {
            "id": acc.id, 
            "name": acc.name, 
            "strategy": acc.strategy,
            "symbol": acc.symbol,
            "phase": acc.phase,
            "platform": acc.platform,
            "active": acc.active,
            "account_type": acc.account_type
        } 
        for acc in accounts
    ]
    return jsonify(accounts_list)

# Add API to get available platforms
@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    platforms = Account.get_platforms()
    return jsonify(platforms)

# Add API to get account types
@app.route('/api/account-types', methods=['GET'])
def get_account_types():
    account_types = Account.get_account_types()
    return jsonify(account_types)

# Add API endpoint to update account phase
@app.route('/api/accounts/<int:account_id>/phase', methods=['PUT'])
def update_account_phase(account_id):
    data = request.json
    new_phase = int(data.get('phase', 1))
    
    print(f"Updating account {account_id} phase to: {new_phase}")
    print(f"Raw request data: {data}")
    
    # Find the account and update its phase
    account = next((acc for acc in Account.get_accounts() if acc.id == account_id), None)
    if not account:
        print(f"Account ID {account_id} not found")
        return jsonify({"status": "error", "message": f"Account ID {account_id} not found"})
    
    # Update the phase - ensure it's an integer
    old_phase = account.phase
    account.phase = new_phase
    
    print(f"Updated account {account.name} phase from {old_phase} to {account.phase}")
    
    # Print all accounts and their phases to verify
    for acc in Account.get_accounts():
        print(f"Account {acc.name} (ID: {acc.id}) now has phase: {acc.phase}")
    
    return jsonify({
        "status": "success",
        "message": f"Updated phase for {account.name} to Phase {account.phase}",
        "account": {
            "id": account.id,
            "name": account.name,
            "phase": account.phase
        }
    })

# Add trading API endpoints for the UI
@app.route('/api/buy', methods=['POST'])
def buy():
    service = get_service_instance()
    data = request.json
    
    # Get parameters from the request or use defaults
    symbol = data.get('symbol', 'NQM5')
    base_quantity = int(data.get('orderQty', 10))
    text = data.get('text', 'test')
    
    # Get phase-specific settings if provided
    phase1_size = int(data.get('phase1Size', base_quantity))
    phase2_size = int(data.get('phase2Size', phase1_size * 2))
    phase3_size = int(data.get('phase3Size', phase1_size * 3))
    
    # Debug - show all parameters received
    print(f"Buy request data: {data}")
    print(f"Buy phase sizes - 1: {phase1_size}, 2: {phase2_size}, 3: {phase3_size}")
    
    # Check if account ID was directly provided
    account_id = data.get('accountId')
    
    if account_id:
        # Use the directly provided account ID
        account = next((acc for acc in Account.get_accounts() if acc.id == account_id), None)
        if not account:
            return jsonify({
                "status": "error", 
                "message": f"Account ID {account_id} not found"
            })
    else:
        # Get the account based on the strategy text
        account = Account.get_account_by_strategy(text)
        if not account:
            # Use the first account as a fallback
            account = Account.get_accounts()[0]
            print(f"Account not found for strategy '{text}', using default: {account.name}")
    
    try:
        # Determine the quantity based on account phase
        account_phase = int(account.phase) # Ensure phase is an integer
        print(f"Account {account.name} has phase: {account_phase}")
        
        # Debug phase values
        print(f"Available phase sizes: Phase 1={phase1_size}, Phase 2={phase2_size}, Phase 3={phase3_size}")
        
        if account_phase == 1:
            quantity = phase1_size
        elif account_phase == 2:
            quantity = phase2_size
        elif account_phase == 3:
            quantity = phase3_size
        else:
            quantity = base_quantity
            
        print(f"Calculated quantity for phase {account_phase}: {quantity}")
        
        # Always get initial cash snapshot before placing the order
        # This ensures we have a starting point for profit calculation
        positions = service.fetch_positions_for_account(account.id)
        active_positions = [pos for pos in positions if pos.get('netPos', 0) != 0]
        
        # Always take a snapshot whether there are active positions or not
        max_retries = 3
        for retry in range(max_retries):
            try:
                access_token = service.access_token
                if not access_token:
                    print("No access token available for initial snapshot")
                    service.request_access_token()
                    access_token = service.access_token
                    if not access_token:
                        print("Failed to get access token even after retry")
                        break
                
                print(f"Buy endpoint: Getting initial snapshot for account {account.id} (attempt {retry+1}/{max_retries})...")
                initial_snapshot = get_cash_snapshot(access_token, account.id)
                
                if initial_snapshot:
                    account_cash_snapshots[account.id] = initial_snapshot
                    print(f"INITIAL CASH SNAPSHOT - Account {account.id}: {initial_snapshot}")
                    
                    # Update message to reflect we always take a snapshot
                    if not active_positions:
                        print(f"Opening BUY trade with no previous active positions. Cash snapshot saved.")
                    else:
                        print(f"Opening BUY trade with active positions. Cash snapshot saved.")
                    
                    print(f"DEBUG: Buy endpoint - account_cash_snapshots now contains keys: {list(account_cash_snapshots.keys())}")
                    print(f"DEBUG: Buy endpoint - Stored snapshot for account {account.id}: {account_cash_snapshots[account.id]}") 
                    print(f"DEBUG: Buy endpoint - account_cash_snapshots id: {id(account_cash_snapshots)}")
                    break  # Success, exit the retry loop
                else:
                    print(f"Buy endpoint: Null initial snapshot returned (attempt {retry+1}/{max_retries})")
                    if retry < max_retries - 1:
                        print("Waiting 1 second before retry...")
                        time.sleep(1)
            except Exception as e:
                print(f"Error getting initial cash snapshot (attempt {retry+1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    print("Waiting 1 second before retry...")
                    time.sleep(1)
                import traceback
                traceback.print_exc()
            
        symbol_cleaned = get_current_contract(symbol)
        print(f"Placing BUY order: Symbol={symbol_cleaned}, Qty={quantity}, Account={account.name}, Phase={account_phase}, Text={text}")
        result = service.place_order(account.id, symbol_cleaned, "Buy", quantity, text)
        
        # Print order ID when entering a trade
        if result and 'orderId' in result:
            print(f"ENTERING TRADE - Order ID: {result['orderId']}")
        
        return jsonify({
            "status": "success", 
            "message": f"Buy order placed for {symbol_cleaned} on {account.name} (Phase {account_phase}, Qty {quantity})", 
            "details": result,
            "account": {
                "id": account.id,
                "name": account.name,
                "phase": account_phase
            }
        })
    except Exception as e:
        error_msg = str(e)
        print(f"Error placing buy order: {error_msg}")
        return jsonify({
            "status": "error", 
            "message": f"Error: {error_msg}",
            "account": {
                "id": account.id,
                "name": account.name
            }
        })

@app.route('/api/sell', methods=['POST'])
def sell():
    service = get_service_instance()
    data = request.json
    
    # Get parameters from the request or use defaults
    symbol = data.get('symbol', 'NQM5')
    base_quantity = int(data.get('orderQty', 10))
    text = data.get('text', 'test')
    
    # Get phase-specific settings if provided
    phase1_size = int(data.get('phase1Size', base_quantity))
    phase2_size = int(data.get('phase2Size', phase1_size * 2))
    phase3_size = int(data.get('phase3Size', phase1_size * 3))
    
    # Debug - show all parameters received
    print(f"Sell request data: {data}")
    print(f"Sell phase sizes - 1: {phase1_size}, 2: {phase2_size}, 3: {phase3_size}")
    
    # Check if account ID was directly provided
    account_id = data.get('accountId')
    
    if account_id:
        # Use the directly provided account ID
        account = next((acc for acc in Account.get_accounts() if acc.id == account_id), None)
        if not account:
            return jsonify({
                "status": "error", 
                "message": f"Account ID {account_id} not found"
            })
    else:
        # Get the account based on the strategy text
        account = Account.get_account_by_strategy(text)
        if not account:
            # Use the first account as a fallback
            account = Account.get_accounts()[0]
            print(f"Account not found for strategy '{text}', using default: {account.name}")
    
    try:
        # Determine the quantity based on account phase
        account_phase = int(account.phase) # Ensure phase is an integer
        print(f"Account {account.name} has phase: {account_phase}")
        
        # Debug phase values
        print(f"Available phase sizes: Phase 1={phase1_size}, Phase 2={phase2_size}, Phase 3={phase3_size}")
        
        if account_phase == 1:
            quantity = phase1_size
        elif account_phase == 2:
            quantity = phase2_size
        elif account_phase == 3:
            quantity = phase3_size
        else:
            quantity = base_quantity
            
        print(f"Calculated quantity for phase {account_phase}: {quantity}")
        
        # Always get initial cash snapshot before placing the order
        # This ensures we have a starting point for profit calculation
        positions = service.fetch_positions_for_account(account.id)
        active_positions = [pos for pos in positions if pos.get('netPos', 0) != 0]
        
        # Always take a snapshot whether there are active positions or not
        max_retries = 3
        for retry in range(max_retries):
            try:
                access_token = service.access_token
                if not access_token:
                    print("No access token available for initial snapshot")
                    service.request_access_token()
                    access_token = service.access_token
                    if not access_token:
                        print("Failed to get access token even after retry")
                        break
                
                print(f"Sell endpoint: Getting initial snapshot for account {account.id} (attempt {retry+1}/{max_retries})...")
                initial_snapshot = get_cash_snapshot(access_token, account.id)
                
                if initial_snapshot:
                    account_cash_snapshots[account.id] = initial_snapshot
                    print(f"INITIAL CASH SNAPSHOT - Account {account.id}: {initial_snapshot}")
                    
                    # Update message to reflect we always take a snapshot
                    if not active_positions:
                        print(f"Opening SELL trade with no previous active positions. Cash snapshot saved.")
                    else:
                        print(f"Opening SELL trade with active positions. Cash snapshot saved.")
                        
                    print(f"DEBUG: Sell endpoint - account_cash_snapshots now contains keys: {list(account_cash_snapshots.keys())}")
                    print(f"DEBUG: Sell endpoint - Stored snapshot for account {account.id}: {account_cash_snapshots[account.id]}")
                    print(f"DEBUG: Sell endpoint - account_cash_snapshots id: {id(account_cash_snapshots)}")
                    break  # Success, exit the retry loop
                else:
                    print(f"Sell endpoint: Null initial snapshot returned (attempt {retry+1}/{max_retries})")
                    if retry < max_retries - 1:
                        print("Waiting 1 second before retry...")
                        time.sleep(1)
            except Exception as e:
                print(f"Error getting initial cash snapshot (attempt {retry+1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    print("Waiting 1 second before retry...")
                    time.sleep(1)
                import traceback
                traceback.print_exc()
            
        symbol_cleaned = get_current_contract(symbol)
        print(f"Placing SELL order: Symbol={symbol_cleaned}, Qty={quantity}, Account={account.name}, Phase={account_phase}, Text={text}")
        result = service.place_order(account.id, symbol_cleaned, "Sell", quantity, text)
        
        # Print order ID when closing a trade
        if result and 'orderId' in result:
            print(f"CLOSING TRADE - Order ID: {result['orderId']}")
        
        return jsonify({
            "status": "success", 
            "message": f"Sell order placed for {symbol_cleaned} on {account.name} (Phase {account_phase}, Qty {quantity})", 
            "details": result,
            "account": {
                "id": account.id,
                "name": account.name,
                "phase": account_phase
            }
        })
    except Exception as e:
        error_msg = str(e)
        print(f"Error placing sell order: {error_msg}")
        return jsonify({
            "status": "error", 
            "message": f"Error: {error_msg}",
            "account": {
                "id": account.id,
                "name": account.name
            }
        })

@app.route('/api/cancel', methods=['POST'])
def cancel():
    service = get_service_instance()
    data = request.json
    
    # Get the account ID if specified
    account_id = None
    if data and 'accountId' in data:
        account_id = data.get('accountId')
    
    try:
        # Step 1: Cancel all pending orders
        cancel_result = service.cancel_all_orders(account_id)
        
        # Print canceled order IDs
        if cancel_result and 'canceled_orders' in cancel_result:
            for order in cancel_result['canceled_orders']:
                if 'orderId' in order:
                    print(f"CANCELED ORDER - Order ID: {order['orderId']}")
        
        # Get accounts to process
        accounts_to_process = []
        if account_id:
            accounts_to_process = [account_id]
        else:
            # Get all account IDs with open positions
            positions = service.position_cache
            accounts_to_process = list(set(pos.get('accountId') for pos in positions if pos.get('netPos', 0) != 0))
            
        # Step 2: First close all open positions
        close_result = service.close_all_positions(account_id)
        
        # Wait 1 second after closing positions for balance to update
        print("Waiting 1 second after position close for balance to update...")
        time.sleep(1)
        
        # Store profit information for the response
        profit_info = []
        
        # Process each account for profit calculation AFTER position close
        for acc_id in accounts_to_process:
            # Check if we have an initial cash snapshot for this account
            if acc_id in account_cash_snapshots:
                # Log debug information about account cash snapshots
                print(f"DEBUG: account_cash_snapshots keys: {list(account_cash_snapshots.keys())}")
                print(f"DEBUG: Current account ID: {acc_id}")
                
                # Get final cash snapshot AFTER waiting for balance update
                try:
                    access_token = service.access_token
                    if not access_token:
                        print("No access token available for final snapshot")
                        service.request_access_token()
                        access_token = service.access_token
                        if not access_token:
                            print("Failed to get access token even after retry")
                            continue
                        
                    print(f"Getting final snapshot for account {acc_id}...")
                    try:
                        final_snapshot = get_cash_snapshot(access_token, acc_id)
                        print(f"Final snapshot retrieved: {final_snapshot}")
                    except Exception as e:
                        print(f"Failed to get final snapshot: {e}")
                        continue
                        
                    if not final_snapshot:
                        print("Null final snapshot returned")
                        continue
                        
                    initial_snapshot = account_cash_snapshots.get(acc_id)
                    if not initial_snapshot:
                        print(f"No initial snapshot found for account {acc_id}")
                        continue
                        
                    print(f"Initial snapshot retrieved: {initial_snapshot}")
                    
                    # Calculate profit difference
                    profit_diff = calculate_realized_pnl_diff(initial_snapshot, final_snapshot)
                    
                    # Get account name for the display
                    from app.models.account import Account
                    account_name = "Unknown"
                    for acc in Account.get_accounts():
                        if acc.id == acc_id:
                            account_name = acc.name
                            break
                    
                    # Store profit information for the response
                    profit_info.append({
                        "account_id": acc_id,
                        "account_name": account_name,
                        "profit": profit_diff,
                        "initial_realized_pnl": initial_snapshot.get("realizedPnL", 0),
                        "final_realized_pnl": final_snapshot.get("realizedPnL", 0)
                    })
                    
                    # Log additional confirmation
                    print(f"Profit calculation completed. Difference: ${profit_diff:.2f}")
                    
                    # Clear the snapshot after calculating profit
                    del account_cash_snapshots[acc_id]
                    print(f"Cleared snapshot for account {acc_id}")
                except Exception as e:
                    print(f"Error calculating profit: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        # Print closed position order IDs
        if close_result and 'closed_positions' in close_result:
            for position in close_result['closed_positions']:
                if 'orderId' in position:
                    print(f"CLOSED POSITION - Order ID: {position['orderId']}")
        
        # Debug log for profit info
        print(f"DEBUG profit_info: {profit_info}")
        
        # Combine results
        combined_result = {
            "orders_canceled": cancel_result,
            "positions_closed": close_result,
            "profit_info": profit_info
        }
        
        # Prepare a user-friendly message
        cancel_count = cancel_result.get('success_count', 0)
        close_count = close_result.get('success_count', 0)
        
        # Add profit information to the message if available
        message = f"Canceled {cancel_count} orders and closed {close_count} positions"
        if profit_info:
            total_profit = sum(p.get('profit', 0) for p in profit_info)
            message += f" with a total profit of ${total_profit:.2f}"
        
        return jsonify({
            "status": "success", 
            "message": message,
            "details": combined_result
        })
    except Exception as e:
        error_msg = str(e)
        print(f"Error in cancel endpoint: {error_msg}")
        return jsonify({"status": "error", "message": f"Error: {error_msg}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)