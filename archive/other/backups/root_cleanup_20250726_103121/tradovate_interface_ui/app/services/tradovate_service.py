import time
import threading
import requests
import csv
import os
from datetime import datetime

from app.config import (
    TRADOVATE_API_URL, NAME, PASSWORD, APP_ID, APP_VERSION,
    DEVICE_ID, CID, SEC, MAX_OPEN_POSITIONS
)

# Singleton instance
_service_instance = None

def get_service_instance():
    """
    Get or create the TradovateService singleton instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = TradovateService()
    return _service_instance

def start_background_tasks():
    """
    Start background tasks for the application.
    """
    service = get_service_instance()
    threading.Thread(target=service.periodic_cache_update, daemon=True).start()

class TradovateService:
    """
    Service class for interacting with the Tradovate API.
    """
    def __init__(self):
        self.access_token = None
        self.token_expiration_time = 0
        self.position_cache = []
        self.order_tracker = {}  # Track orders by account_id -> {order_id: order_details}
        self.fill_cache = {}  # Cache fill data by order_id
        self.trade_pairs = {}  # Track entry/exit trade pairs for profit calculation
    
    def is_token_valid(self):
        """
        Check if the current access token is valid.
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        return self.access_token is not None and time.time() < self.token_expiration_time
    
    def request_access_token(self):
        """
        Request a new access token from the Tradovate API.
        
        Returns:
            str or None: The access token if successful, None otherwise
        """
        url = f"{TRADOVATE_API_URL}/auth/accesstokenrequest"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            "name": NAME,
            "password": PASSWORD,
            "appId": APP_ID,
            "appVersion": APP_VERSION,
            "deviceId": DEVICE_ID,
            "cid": CID,
            "sec": SEC
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get('accessToken')
            self.token_expiration_time = time.time() + data.get('expiresIn', 3600)
            print("Access token acquired: ", self.access_token)
            return self.access_token
        else:
            print("Error getting access token:", response.text)
            return None
    
    def ensure_token(self):
        """
        Ensure a valid access token is available.
        
        Returns:
            str or None: The access token if successful, None otherwise
        """
        if not self.is_token_valid():
            return self.request_access_token()
        return self.access_token
    
    def place_order(self, account_id, symbol, action, quantity, text):
        """
        Place an order through the Tradovate API.
        
        Args:
            account_id (int): The account ID
            symbol (str): The trading symbol
            action (str): The action (Buy/Sell)
            quantity (int): The order quantity
            text (str): The order text/comment
            
        Returns:
            dict: The API response or error information
        """
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get access token"}
            
        url = f"{TRADOVATE_API_URL}/order/placeOrder"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Order data
        order_data = {
            "accountId": account_id,
            "action": action.capitalize(),
            "symbol": symbol,
            "orderQty": quantity,
            "orderType": "Market",
            "isAutomated": True,
            "text": text
        }
    
        print(f"Placing order for account ID {account_id}: {order_data} using {token}")
        response = requests.post(url, json=order_data, headers=headers)
        
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    
        if response.status_code != 200:
            try:
                error_info = response.json()
                print(f"Error placing order: {error_info.get('failureText', 'No additional error info')}")
            except requests.exceptions.JSONDecodeError:
                print("Response is not in JSON format:", response.text)
            return {"error": "Failed to place order", "status_code": response.status_code}
    
        # Get response data
        response_data = response.json()
        
        # Store the order in our local tracker if the order was successful
        if 'orderId' in response_data:
            order_id = response_data['orderId']
            # Initialize account dictionary if it doesn't exist
            if account_id not in self.order_tracker:
                self.order_tracker[account_id] = {}
            
            # Store the order with timestamp and details
            self.order_tracker[account_id][order_id] = {
                'id': order_id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'status': 'Working'
            }
            print(f"Order {order_id} added to local tracker for account {account_id}")
            
            # For entries (Open orders), record to the CSV file
            if "Open" in text or "Entry" in text:
                # Wait for the fill to be available
                time.sleep(2)
                
                # Get the execution price
                fill_price = self.get_order_fill_price(order_id)
                
                if fill_price:
                    # Add the price to our tracker
                    self.order_tracker[account_id][order_id]['execution_price'] = fill_price
                    
                    # Record the entry to the CSV
                    trade_data = {
                        'tradeNumber': order_id,
                        'type': action,
                        'signal': text,
                        'dateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'price': fill_price,
                        'contracts': quantity,
                        'profit': 0  # No profit for entries
                    }
                    self.record_trade_to_csv(trade_data)
        
        # Update the cache after placing the order
        time.sleep(1)  # Adding a 1-second delay
        self.update_cache()
    
        return response_data
    
    def fetch_positions_for_account(self, account_id):
        """
        Fetch positions for a given account from the cache.
        
        Args:
            account_id (int): The account ID
            
        Returns:
            list: The positions for the account
        """
        positions = [pos for pos in self.position_cache if pos['accountId'] == account_id]
        print(f"Retrieved positions for account {account_id}: {positions}")
        return positions
    
    def get_contract_id(self, symbol):
        """
        Get the contract ID for a symbol.
        
        Args:
            symbol (str): The trading symbol
            
        Returns:
            int or None: The contract ID if successful, None otherwise
        """
        token = self.ensure_token()
        if not token:
            return None
    
        url = f"{TRADOVATE_API_URL}/contract/find"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        params = {'name': symbol}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            contract_id = data.get('id')
            return contract_id
        else:
            print(f"Error fetching contract ID for symbol '{symbol}': {response.status_code} - {response.text}")
            return None
    
    def update_cache(self):
        """
        Update the position cache with the latest data from the Tradovate API.
        """
        token = self.ensure_token()
        if not token:
            return
        
        url = f"{TRADOVATE_API_URL}/position/list"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
        response = requests.get(url, headers=headers)
    
        if response.status_code == 200:
            # Successfully fetched the positions
            self.position_cache = response.json()
            print("Cache updated with new positions:")
            from app.models.account import Account
            accounts = Account.get_accounts()
            
            for position in self.position_cache:
                if position['netPos'] != 0:
                    account_name = next((acc.name for acc in accounts if acc.id == position['accountId']), "Unknown Account")
                    position_type = "Long" if position['netPos'] > 0 else "Short"
                    
                    print(f"Account Name: {account_name}, Position Type: {position_type}")
        else:
            print(f"Error fetching positions: {response.status_code} - {response.text}")
    
    def get_active_orders(self, account_id=None):
        """
        Get active orders from the local tracker.
        
        Args:
            account_id (int, optional): The account ID to filter orders by. If None, returns orders for all accounts.
            
        Returns:
            list: The active orders for the specified account(s)
        """
        active_orders = []
        
        # If account_id is specified, only get orders for that account
        if account_id is not None:
            if account_id in self.order_tracker:
                for order_id, order in self.order_tracker[account_id].items():
                    if order.get('status') in ['Working', 'Pending']:
                        active_orders.append(order)
        else:
            # Get orders for all accounts
            for acc_id, orders in self.order_tracker.items():
                for order_id, order in orders.items():
                    if order.get('status') in ['Working', 'Pending']:
                        active_orders.append(order)
        
        print(f"Found {len(active_orders)} active orders in local tracker.")
        return active_orders
    
    def cancel_order(self, order_id):
        """
        Cancel a specific order by ID.
        
        Args:
            order_id (int): The ID of the order to cancel
            
        Returns:
            dict: The API response or error information
        """
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get access token"}
            
        url = f"{TRADOVATE_API_URL}/order/cancelorder"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "orderId": order_id
        }
    
        print(f"Canceling order ID {order_id}")
        response = requests.post(url, json=payload, headers=headers)
        
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    
        if response.status_code != 200:
            try:
                error_info = response.json()
                print(f"Error canceling order: {error_info.get('failureText', 'No additional error info')}")
            except requests.exceptions.JSONDecodeError:
                print("Response is not in JSON format:", response.text)
            return {"error": "Failed to cancel order", "status_code": response.status_code}
        
        # Update order status in the local tracker
        for account_id, orders in self.order_tracker.items():
            if order_id in orders:
                orders[order_id]['status'] = 'Canceled'
                print(f"Order {order_id} marked as Canceled in local tracker")
                break
    
        return response.json()
    
    def cancel_all_orders(self, account_id=None):
        """
        Cancel all active orders for the specified account or all accounts using the local order tracker.
        
        Args:
            account_id (int, optional): The account ID to cancel orders for. If None, cancels orders for all accounts.
            
        Returns:
            dict: Summary of canceled orders
        """
        # Get all active orders from our local tracker
        active_orders = self.get_active_orders(account_id)
        
        if not active_orders:
            return {"message": "No active orders to cancel", "canceled_count": 0}
        
        # Cancel each order
        success_count = 0
        failed_orders = []
        
        for order in active_orders:
            order_id = order.get('id')
            try:
                result = self.cancel_order(order_id)
                if "error" not in result:
                    success_count += 1
                else:
                    failed_orders.append({"order_id": order_id, "error": result.get("error")})
            except Exception as e:
                failed_orders.append({"order_id": order_id, "error": str(e)})
        
        return {
            "message": f"Canceled {success_count} of {len(active_orders)} orders",
            "total_orders": len(active_orders),
            "success_count": success_count,
            "failed_orders": failed_orders
        }
        
    def close_position(self, account_id, contract_id, net_pos):
        """
        Close a specific position using the liquidatePosition endpoint.
        
        Args:
            account_id (int): The account ID
            contract_id (int): The contract ID
            net_pos (int): The current position size (used for validation only)
            
        Returns:
            dict: The API response or error information
        """
        if net_pos == 0:
            return {"error": "No position to close"}
        
        # Before closing the position, get the contract symbol for recording trade
        contract_symbol = None
        for position in self.position_cache:
            if position.get('contractId') == contract_id and position.get('accountId') == account_id:
                contract_symbol = position.get('symbol', 'Unknown')
                break
        
        # Store information about the position before closing it
        position_info = {
            'account_id': account_id,
            'contract_id': contract_id,
            'net_pos': net_pos,
            'symbol': contract_symbol
        }
        
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get access token"}
            
        url = f"{TRADOVATE_API_URL}/order/liquidateposition"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Payload according to OpenAPI spec
        payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "admin": False  # Required field per API spec
        }
    
        print(f"Liquidating position for account ID {account_id}, contract ID {contract_id}")
        response = requests.post(url, json=payload, headers=headers)
        
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    
        if response.status_code != 200:
            try:
                error_info = response.json()
                print(f"Error closing position: {error_info.get('failureText', 'No additional error info')}")
            except requests.exceptions.JSONDecodeError:
                print("Response is not in JSON format:", response.text)
            return {"error": "Failed to close position", "status_code": response.status_code}
        
        # If the position was closed successfully, calculate profit
        result = response.json()
        close_order_id = result.get('orderId')
        
        if close_order_id:
            print(f"Position closed with order ID: {close_order_id}")
            
            # Wait for the order to execute and fills to be available
            time.sleep(2)
            
            # Process trade profit
            self.process_closed_position_profit(position_info, close_order_id)
        
        return result
    
    def liquidate_all_positions(self, account_id=None):
        """
        Liquidate all positions for a specific account using the liquidatePositions endpoint.
        
        Args:
            account_id (int, optional): The account ID to close positions for. 
                                       If None, tries to close all positions individually.
            
        Returns:
            dict: Summary of closed positions
        """
        # Update positions cache to get the latest positions
        self.update_cache()
        
        # If no account_id is specified and there are multiple accounts with positions,
        # we need to make multiple API calls
        if account_id is None:
            # Get unique account IDs with open positions
            account_ids = list(set(pos.get('accountId') for pos in self.position_cache if pos.get('netPos') != 0))
            
            results = []
            for acc_id in account_ids:
                result = self.liquidate_all_positions(acc_id)
                results.append(result)
                
            # Combine results
            total_closed = sum(r.get('success_count', 0) for r in results)
            total_positions = sum(r.get('total_positions', 0) for r in results)
            
            return {
                "message": f"Liquidated {total_closed} of {total_positions} positions across {len(account_ids)} accounts",
                "account_results": results,
                "total_positions": total_positions,
                "success_count": total_closed,
                "accounts_processed": account_ids
            }
        
        # Process positions for the specified account
        positions = [pos for pos in self.position_cache if pos.get('accountId') == account_id and pos.get('netPos') != 0]
        
        # No positions to close
        if not positions:
            return {
                "message": "No open positions to liquidate",
                "closed_count": 0,
                "total_positions": 0,
                "accounts_processed": [account_id] if account_id else []
            }
            
        # Try the batch liquidatePositions endpoint
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get access token"}
            
        # Get position IDs
        position_ids = [pos.get('id') for pos in positions if 'id' in pos]
        
        # If we have position IDs, use the liquidatePositions endpoint
        if position_ids:
            url = f"{TRADOVATE_API_URL}/order/liquidatepositions"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "positions": position_ids,
                "admin": False
            }
            
            print(f"Liquidating {len(position_ids)} positions for account {account_id}")
            response = requests.post(url, json=payload, headers=headers)
            
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            
            if response.status_code == 200:
                return {
                    "message": f"Successfully liquidated {len(position_ids)} positions",
                    "total_positions": len(position_ids),
                    "success_count": len(position_ids),
                    "accounts_processed": [account_id]
                }
            else:
                try:
                    error_info = response.json()
                    error_message = error_info.get('failureText', 'No additional error info')
                except requests.exceptions.JSONDecodeError:
                    error_message = response.text
                    
                print(f"Error liquidating positions: {error_message}")
                    
                # Fall back to individual liquidation if batch fails
                print("Falling back to individual position liquidation")
        else:
            print("No position IDs found, falling back to individual contract liquidation")
        
        # Fall back to closing each position individually using the contract ID
        closed_positions = []
        failed_positions = []
        
        for position in positions:
            account_id = position.get('accountId')
            contract_id = position.get('contractId')
            net_pos = position.get('netPos')
            symbol = position.get('symbol', 'Unknown')
            
            try:
                result = self.close_position(account_id, contract_id, net_pos)
                if "error" not in result:
                    closed_positions.append({
                        "account_id": account_id,
                        "contract_id": contract_id,
                        "symbol": symbol,
                        "position_size": net_pos,
                        "order_id": result.get('orderId')
                    })
                else:
                    failed_positions.append({
                        "account_id": account_id,
                        "contract_id": contract_id,
                        "symbol": symbol,
                        "position_size": net_pos,
                        "error": result.get("error")
                    })
            except Exception as e:
                failed_positions.append({
                    "account_id": account_id,
                    "contract_id": contract_id,
                    "symbol": symbol,
                    "position_size": net_pos,
                    "error": str(e)
                })
                
        return {
            "message": f"Closed {len(closed_positions)} of {len(positions)} positions",
            "closed_positions": closed_positions,
            "failed_positions": failed_positions,
            "total_positions": len(positions),
            "success_count": len(closed_positions),
            "accounts_processed": [account_id]
        }
        
    # Keep the close_all_positions for backward compatibility
    def close_all_positions(self, account_id=None):
        """
        Close all open positions for the specified account or all accounts.
        This is now a wrapper around liquidate_all_positions.
        
        Args:
            account_id (int, optional): The account ID to close positions for. If None, closes positions for all accounts.
            
        Returns:
            dict: Summary of closed positions
        """
        return self.liquidate_all_positions(account_id)
        
    def periodic_cache_update(self):
        """
        Periodically update the position cache.
        """
        while True:
            self.update_cache()
            time.sleep(60)
            
    def get_fills(self, order_id=None, account_id=None, contract_id=None):
        """
        Get fill information using the Tradovate API.
        
        Args:
            order_id (int, optional): Filter fills by order ID
            account_id (int, optional): Filter fills by account ID
            contract_id (int, optional): Filter fills by contract ID
            
        Returns:
            list: List of fills or None if error
        """
        token = self.ensure_token()
        if not token:
            print("Failed to get access token for fill request")
            return None
            
        # Try to use fill/list endpoint
        url = f"{TRADOVATE_API_URL}/fill/list"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"Fetching fills from {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching fills: {response.status_code} - {response.text}")
            return None
        
        fills = response.json()
        print(f"Retrieved {len(fills)} fills from Tradovate API")
        
        # Filter fills if parameters provided
        filtered_fills = fills
        
        if order_id:
            filtered_fills = [fill for fill in filtered_fills if fill.get('orderId') == order_id]
            print(f"Filtered to {len(filtered_fills)} fills for order ID {order_id}")
            
        if account_id:
            # First, get all orders for this account
            account_orders = self.get_orders(account_id)
            if account_orders:
                order_ids = [order.get('id') for order in account_orders]
                filtered_fills = [fill for fill in filtered_fills if fill.get('orderId') in order_ids]
                print(f"Filtered to {len(filtered_fills)} fills for account ID {account_id}")
            
        if contract_id:
            filtered_fills = [fill for fill in filtered_fills if fill.get('contractId') == contract_id]
            print(f"Filtered to {len(filtered_fills)} fills for contract ID {contract_id}")
            
        # Cache the fills by order ID for future use
        for fill in filtered_fills:
            order_id = fill.get('orderId')
            if order_id:
                if order_id not in self.fill_cache:
                    self.fill_cache[order_id] = []
                self.fill_cache[order_id].append(fill)
        
        return filtered_fills
        
    def get_order_fill_price(self, order_id):
        """
        Get the execution price for an order.
        
        Args:
            order_id (int): The order ID
            
        Returns:
            float or None: The execution price if found, None otherwise
        """
        # Check cache first
        if order_id in self.fill_cache:
            fills = self.fill_cache[order_id]
            if fills:
                # Return the average price if multiple fills
                total_qty = sum(fill.get('qty', 0) for fill in fills)
                if total_qty > 0:
                    weighted_price = sum(fill.get('price', 0) * fill.get('qty', 0) for fill in fills) / total_qty
                    return weighted_price
                return fills[0].get('price')
        
        # If not in cache, fetch from API
        fills = self.get_fills(order_id=order_id)
        if not fills or len(fills) == 0:
            print(f"No fills found for order ID {order_id}")
            return None
            
        # Calculate average price if multiple fills
        total_qty = sum(fill.get('qty', 0) for fill in fills)
        if total_qty > 0:
            weighted_price = sum(fill.get('price', 0) * fill.get('qty', 0) for fill in fills) / total_qty
            return weighted_price
        
        return fills[0].get('price')
        
    def get_orders(self, account_id=None):
        """
        Get all orders using the Tradovate API.
        
        Args:
            account_id (int, optional): Filter by account ID
            
        Returns:
            list: List of orders or None if error
        """
        token = self.ensure_token()
        if not token:
            return None
            
        url = f"{TRADOVATE_API_URL}/order/list"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"Fetching orders from {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching orders: {response.status_code} - {response.text}")
            return None
        
        orders = response.json()
        print(f"Retrieved {len(orders)} orders from Tradovate API")
        
        # Filter by account ID if provided
        if account_id:
            orders = [order for order in orders if order.get('accountId') == account_id]
            print(f"Filtered to {len(orders)} orders for account ID {account_id}")
            
        return orders
        
    def record_trade_to_csv(self, trade_data):
        """
        Record a trade to the trades_history.csv file.
        
        Args:
            trade_data (dict): Trade information to record
        """
        file_path = 'trades_history.csv'
        file_exists = os.path.isfile(file_path)
        
        fieldnames = ['tradeNumber', 'type', 'signal', 'dateTime', 'price', 'contracts', 'profit']
        
        try:
            with open(file_path, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(trade_data)
                print(f"Trade recorded to {file_path}: {trade_data}")
        except Exception as e:
            print(f"Error recording trade to CSV: {e}")
            
    def calculate_trade_profit(self, entry_fill, exit_fill):
        """
        Calculate profit for a trade based on entry and exit fills.
        
        Args:
            entry_fill (dict): Entry fill information
            exit_fill (dict): Exit fill information
            
        Returns:
            float: Profit amount
        """
        if not entry_fill or not exit_fill:
            return 0
            
        entry_price = entry_fill.get('price', 0)
        exit_price = exit_fill.get('price', 0)
        qty = min(entry_fill.get('qty', 0), exit_fill.get('qty', 0))
        
        if entry_fill.get('action') == 'Buy':
            # Long trade: exit_price - entry_price
            profit = (exit_price - entry_price) * qty
        else:
            # Short trade: entry_price - exit_price
            profit = (entry_price - exit_price) * qty
            
        print(f"Calculated profit: {profit} (Entry: {entry_price}, Exit: {exit_price}, Qty: {qty})")
        return profit
        
    def process_closed_position_profit(self, position_info, close_order_id):
        """
        Process profit calculation for a closed position.
        
        Args:
            position_info (dict): Information about the closed position
            close_order_id (int): The order ID used to close the position
        """
        print(f"Processing profit calculation for position: {position_info}")
        
        account_id = position_info.get('account_id')
        contract_id = position_info.get('contract_id')
        symbol = position_info.get('symbol', 'Unknown')
        net_pos = position_info.get('net_pos', 0)
        
        if not account_id or not contract_id or not net_pos:
            print("Insufficient position information for profit calculation")
            return
            
        # Get account information for recording trade
        from app.models.account import Account
        account = next((acc for acc in Account.get_accounts() if acc.id == account_id), None)
        if not account:
            print(f"Account ID {account_id} not found for profit calculation")
            return
        
        # Find matching entry and exit fills
        trade_pairs = self.find_matching_fills(account_id, contract_id)
        
        if not trade_pairs:
            print("No matching trades found for profit calculation")
            return
            
        # Calculate the total profit across all trade pairs
        total_profit = sum(pair.get('profit', 0) for pair in trade_pairs)
        total_qty = sum(pair.get('qty', 0) for pair in trade_pairs)
        
        # Get the last entry and exit prices for reporting
        last_pair = trade_pairs[-1]
        entry_price = last_pair.get('entry_fill', {}).get('price', 0)
        exit_price = last_pair.get('exit_fill', {}).get('price', 0)
        
        print(f"Total profit for {symbol}: {total_profit} (Entry: {entry_price}, Exit: {exit_price}, Qty: {total_qty})")
        
        # Record the trade to the CSV file
        trade_type = 'Sell' if net_pos > 0 else 'Buy'  # Closing action
        
        trade_data = {
            'tradeNumber': close_order_id,
            'type': trade_type,
            'signal': f"{account.strategy or 'Unknown'} (Close)",
            'dateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': exit_price,
            'contracts': total_qty,
            'profit': total_profit
        }
        
        self.record_trade_to_csv(trade_data)
        
    def find_matching_fills(self, account_id, contract_id):
        """
        Find matching entry and exit fills for a position.
        
        Args:
            account_id (int): The account ID
            contract_id (int): The contract ID
            
        Returns:
            list: List of trade pairs (entry_fill, exit_fill, profit)
        """
        # Get all fills for this account and contract
        all_fills = self.get_fills(account_id=account_id, contract_id=contract_id)
        if not all_fills:
            return []
            
        # Sort fills by timestamp
        sorted_fills = sorted(all_fills, key=lambda x: x.get('timestamp', ''))
        
        # Process fills to find entry/exit pairs
        entry_fills = []
        exit_fills = []
        trade_pairs = []
        
        current_position = 0
        
        for fill in sorted_fills:
            action = fill.get('action')
            qty = fill.get('qty', 0)
            
            if action == 'Buy':
                if current_position < 0:
                    # This is covering a short position
                    exit_qty = min(abs(current_position), qty)
                    
                    # Find matching entry fill(s)
                    remaining_exit_qty = exit_qty
                    for entry_fill in entry_fills:
                        if entry_fill.get('action') == 'Sell' and entry_fill.get('available_qty', 0) > 0:
                            match_qty = min(entry_fill.get('available_qty', 0), remaining_exit_qty)
                            
                            # Create trade pair
                            profit = self.calculate_trade_profit(entry_fill, fill)
                            trade_pairs.append({
                                'entry_fill': entry_fill,
                                'exit_fill': fill,
                                'qty': match_qty,
                                'profit': profit
                            })
                            
                            # Update available quantities
                            entry_fill['available_qty'] -= match_qty
                            remaining_exit_qty -= match_qty
                            
                            if remaining_exit_qty <= 0:
                                break
                                
                    current_position += exit_qty
                    
                # Any remaining buy quantity becomes a new long position
                new_long_qty = qty - (qty if current_position < 0 else 0)
                if new_long_qty > 0:
                    fill_copy = fill.copy()
                    fill_copy['available_qty'] = new_long_qty
                    entry_fills.append(fill_copy)
                    current_position += new_long_qty
                    
            elif action == 'Sell':
                if current_position > 0:
                    # This is closing a long position
                    exit_qty = min(current_position, qty)
                    
                    # Find matching entry fill(s)
                    remaining_exit_qty = exit_qty
                    for entry_fill in entry_fills:
                        if entry_fill.get('action') == 'Buy' and entry_fill.get('available_qty', 0) > 0:
                            match_qty = min(entry_fill.get('available_qty', 0), remaining_exit_qty)
                            
                            # Create trade pair
                            profit = self.calculate_trade_profit(entry_fill, fill)
                            trade_pairs.append({
                                'entry_fill': entry_fill,
                                'exit_fill': fill,
                                'qty': match_qty,
                                'profit': profit
                            })
                            
                            # Update available quantities
                            entry_fill['available_qty'] -= match_qty
                            remaining_exit_qty -= match_qty
                            
                            if remaining_exit_qty <= 0:
                                break
                                
                    current_position -= exit_qty
                    
                # Any remaining sell quantity becomes a new short position
                new_short_qty = qty - (qty if current_position > 0 else 0)
                if new_short_qty > 0:
                    fill_copy = fill.copy()
                    fill_copy['available_qty'] = new_short_qty
                    entry_fills.append(fill_copy)
                    current_position -= new_short_qty
        
        # Clean up entry fills with zero available qty
        entry_fills = [fill for fill in entry_fills if fill.get('available_qty', 0) > 0]
        
        print(f"Found {len(trade_pairs)} trade pairs, remaining position: {current_position}")
        
        return trade_pairs
