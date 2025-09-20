from flask import Blueprint, request, jsonify
import time

from app.config import MAX_OPEN_POSITIONS
from app.models.account import Account
from app.services.tradovate_service import get_service_instance
from app.utils.contract_utils import get_current_contract

# Create a blueprint for webhook routes
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming webhook requests from TradingView.
    """
    print("Webhook endpoint was called.")
    
    # Get the TradovateService instance
    service = get_service_instance()
    
    # Step 1: Validate Access Token
    if not service.is_token_valid():
        print("Access token is not valid. Requesting a new one...")
        access_token = service.request_access_token()
        if access_token is None:
            return jsonify({"error": "Failed to retrieve access token"}), 401

    # Step 2: Parse and Validate Request Data
    data = request.get_json()
    print(f"Webhook Data: {data}")
    
    # Extract and sanitize input data
    action = data.get('action', '').capitalize()
    symbol = data.get('symbol')
    quantity = data.get('orderQty')
    order_type = data.get('orderType', 'Market')
    trade_type = data.get('tradeType', 'Open').capitalize()
    text = data.get('text')

    # Validate required fields
    if not all([action, symbol, quantity, text]):
        return jsonify({"error": "Missing required fields"}), 400

    # Optional: Validate data types
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Invalid 'orderQty'. Must be a positive integer."}), 400

    # Step 3: Determine Account ID
    account = Account.get_account_by_strategy(text)
    if account is None:
        return jsonify({"error": "Invalid or missing account reference in 'text'"}), 400
    
    account_id = account.id
    print(f"Account ID determined from text: {account_id}")

    # Get contract ID from symbol
    symbol_cleaned = get_current_contract(symbol)
    contract_id = service.get_contract_id(symbol_cleaned)
    if contract_id is None:
        return jsonify({"error": f"Unable to find contract ID for symbol '{symbol_cleaned}'"}), 400
    print(f"Contract ID for symbol '{symbol_cleaned}': {contract_id}")

    # Step 4: Position Confirmation Checks
    confirmation_checks_enabled = True

    if confirmation_checks_enabled:
        # Retrieve cached data
        account_positions = service.fetch_positions_for_account(account_id)
        
        # Find if there's an existing position for the symbol
        existing_position = next((pos for pos in account_positions if pos['contractId'] == contract_id), None)
        
        net_pos = existing_position.get('netPos', 0) if existing_position else 0
        print(f"Existing Position: {existing_position}")
        print(f"Net Position: {net_pos}")

        # Now, enforce the trading rules based on trade_type, action, and net_pos
        if trade_type == 'Open':
            if net_pos != 0:
                # Position already exists; cannot open another one
                return jsonify({
                    "error": f"Cannot open a new position for '{symbol_cleaned}' in account {account_id}. Position already exists."
                }), 400
            else:
                # Proceed to place the open order
                # Always get initial cash snapshot before placing the order
                from app.app import get_cash_snapshot, account_cash_snapshots
                
                # Import at a local level to avoid circular imports
                active_positions = [pos for pos in account_positions if pos.get('netPos', 0) != 0]
                
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
                        
                        print(f"Webhook: Getting initial snapshot for account {account_id} (attempt {retry+1}/{max_retries})...")
                        initial_snapshot = get_cash_snapshot(access_token, account_id)
                        
                        if initial_snapshot:
                            account_cash_snapshots[account_id] = initial_snapshot
                            print(f"INITIAL CASH SNAPSHOT - Account {account_id}: {initial_snapshot}")
                            
                            # Update message to reflect we always take a snapshot
                            if not active_positions:
                                print(f"Opening {action} trade with no previous active positions. Cash snapshot saved.")
                            else:
                                print(f"Opening {action} trade with active positions. Cash snapshot saved.")
                                
                            print(f"DEBUG: Webhook - account_cash_snapshots now contains keys: {list(account_cash_snapshots.keys())}")
                            print(f"DEBUG: Webhook - Stored snapshot for account {account_id}: {account_cash_snapshots[account_id]}")
                            print(f"DEBUG: Webhook - account_cash_snapshots id: {id(account_cash_snapshots)}")
                            break  # Success, exit the retry loop
                        else:
                            print(f"Webhook: Null initial snapshot returned (attempt {retry+1}/{max_retries})")
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

        elif trade_type == 'Close':
            if net_pos == 0:
                # No position to close
                return jsonify({
                    "error": f"No open position for '{symbol}' in account {account_id} to close."
                }), 400
            else:
                # Check if action matches the existing position
                if net_pos > 0 and action == 'Sell':
                    # Closing a long position with a Sell action
                    pass  # Proceed to place the close order
                elif net_pos < 0 and action == 'Buy':
                    # Closing a short position with a Buy action
                    pass  # Proceed to place the close order
                else:
                    # Action does not match the position; cannot close
                    return jsonify({
                        "error": f"Cannot perform '{action}' action for the current position."
                    }), 400
        else:
            # Invalid trade type
            return jsonify({
                "error": f"Invalid trade type '{trade_type}'. Must be 'Open' or 'Close'."
            }), 400

    # Step 5: Place the Order
    print(f"Received Order - Action: {action}, Symbol: {symbol_cleaned}, Quantity: {quantity}, Order Type: {order_type}, Trade Type: {trade_type}, Text: {text}")
    
    try:
        result = service.place_order(account_id, symbol_cleaned, action, quantity, text)
        print("Order result:", result)
        
        # For Close orders, calculate trade profit
        if trade_type == 'Close' and 'orderId' in result:
            order_id = result['orderId']
            print(f"Close order placed with ID: {order_id}. Will calculate profit after execution.")
            
            # Wait for the order to execute - just for fill data
            time.sleep(2)
            
            # Get the contract ID for this symbol if not already known
            if not contract_id:
                contract_id = service.get_contract_id(symbol_cleaned)
                
            # Process the profit calculation
            if contract_id:
                position_info = {
                    'account_id': account_id,
                    'contract_id': contract_id,
                    'net_pos': net_pos,  # from earlier in the code
                    'symbol': symbol_cleaned
                }
                try:
                    service.process_closed_position_profit(position_info, order_id)
                    
                    # Wait 1 second after closing the trade before attempting to get the snapshot
                    print("Waiting 1 second after trade close for balance to update...")
                    time.sleep(1)
                    
                    # Get final cash snapshot after closing position
                    from app.app import get_cash_snapshot, calculate_realized_pnl_diff, account_cash_snapshots
                    
                    # Log debug information
                    print(f"DEBUG: account_cash_snapshots keys: {list(account_cash_snapshots.keys())}")
                    print(f"DEBUG: Current account ID: {account_id}")
                    
                    # Check if we have an initial cash snapshot for this account
                    if account_id in account_cash_snapshots:
                        try:
                            access_token = service.access_token
                            if not access_token:
                                print("No access token available for final snapshot")
                                service.request_access_token()
                                access_token = service.access_token
                                if not access_token:
                                    print("Failed to get access token even after retry")
                                    return jsonify({"error": "Failed to get access token for profit calculation"}), 500
                            
                            print(f"Getting final snapshot for account {account_id}...")
                            try:
                                final_snapshot = get_cash_snapshot(access_token, account_id)
                                print(f"Final snapshot retrieved: {final_snapshot}")
                            except Exception as e:
                                print(f"Failed to get final snapshot: {e}")
                                return jsonify({"error": f"Failed to get final snapshot: {e}"}), 500
                            
                            if not final_snapshot:
                                print("Null final snapshot returned")
                                return jsonify({"error": "Null final snapshot returned"}), 500
                            
                            initial_snapshot = account_cash_snapshots.get(account_id)
                            if not initial_snapshot:
                                print(f"No initial snapshot found for account {account_id}")
                                return jsonify({"error": f"No initial snapshot found for account {account_id}"}), 500
                            
                            print(f"Initial snapshot retrieved: {initial_snapshot}")
                            
                            # Calculate profit difference
                            profit_diff = calculate_realized_pnl_diff(initial_snapshot, final_snapshot)
                            
                            # Log additional confirmation
                            print(f"Profit calculation completed. Difference: ${profit_diff:.2f}")
                            
                            # Clear the snapshot after calculating profit
                            del account_cash_snapshots[account_id]
                            print(f"Cleared snapshot for account {account_id}")
                        except Exception as e:
                            print(f"Error calculating profit: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    
                except Exception as e:
                    print(f"Error calculating profit: {e}")
            
    except Exception as e:
        print(f"Error placing order: {e}")
        return jsonify({"error": "Failed to place order"}), 500

    return jsonify(result), 200
