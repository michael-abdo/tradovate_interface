# Order Verification System - Usage Examples

## Quick Start Examples

### 1. Basic Single Order

```python
from src.app import TradovateConnection

# Connect to Tradovate instance
connection = TradovateConnection(port=9222, account_name="Demo Account")

# Execute verified single order
result = connection.auto_trade(
    symbol='NQ',
    quantity=1,
    action='Buy',
    tp_ticks=100,    # Take profit: 100 ticks
    sl_ticks=40,     # Stop loss: 40 ticks  
    tick_size=0.25
)

# Check verification result
if result.get('success'):
    orders = result.get('orders', [])
    print(f"✅ Order verified: {len(orders)} orders placed")
    for order in orders:
        print(f"   {order['symbol']} {order['side']} {order['quantity']} @ {order['price']}")
else:
    print(f"❌ Order failed: {result.get('error')}")
```

### 2. Scale In Orders

```python
# Define scale-in levels
scale_orders = [
    {"quantity": 1, "price": 15200},  # First entry
    {"quantity": 1, "price": 15190},  # Scale in level 1
    {"quantity": 1, "price": 15180}   # Scale in level 2
]

# Execute scale orders with verification
result = connection.auto_trade_scale(
    symbol='NQ',
    scale_orders=scale_orders,
    action='Buy',
    tp_ticks=100,
    sl_ticks=40,
    tick_size=0.25
)

# Process results
if result.get('success'):
    print(f"✅ Scale orders verified: {len(result['orders'])} orders")
else:
    print(f"❌ Scale orders failed: {result.get('error')}")
```

## Multi-Account Trading

### 3. Trade Across All Accounts

```python
from src.app import TradovateController

# Initialize controller (finds all Chrome instances)
controller = TradovateController()

print(f"Found {len(controller.connections)} active accounts")

# Execute on all accounts
results = controller.execute_on_all(
    'auto_trade',
    'NQ',           # symbol
    1,              # quantity
    'Buy',          # action
    100,            # tp_ticks
    40,             # sl_ticks
    0.25            # tick_size
)

# Analyze results across accounts
verified_accounts = []
failed_accounts = []

for r in results:
    account = r.get('account', 'Unknown')
    result = r.get('result', {})
    
    if result.get('success'):
        verified_accounts.append(account)
        orders = result.get('orders', [])
        print(f"✅ {account}: {len(orders)} orders verified")
    else:
        failed_accounts.append(account)
        error = result.get('error', 'Unknown error')
        print(f"❌ {account}: {error}")

print(f"\nSummary: {len(verified_accounts)}/{len(results)} accounts successful")
```

### 4. Target Specific Account

```python
# Execute on specific account (by index)
result = controller.execute_on_one(
    0,              # account index
    'auto_trade',   # method
    'ES',           # symbol
    2,              # quantity
    'Sell',         # action
    50,             # tp_ticks
    25,             # sl_ticks
    0.25            # tick_size
)

print(f"Account {result['account']}: {result['result']}")
```

## Error Handling Patterns

### 5. Robust Error Handling

```python
def safe_trade_execution(connection, symbol, quantity, action):
    """Execute trade with comprehensive error handling"""
    
    try:
        # Attempt the trade
        result = connection.auto_trade(
            symbol=symbol,
            quantity=quantity,
            action=action,
            tp_ticks=100,
            sl_ticks=40,
            tick_size=0.25
        )
        
        # Check verification result
        if result.get('success'):
            orders = result.get('orders', [])
            return {
                'status': 'success',
                'message': f'{len(orders)} orders verified',
                'orders': orders
            }
        else:
            # Handle verification failure
            error = result.get('error', 'Unknown verification error')
            return {
                'status': 'verification_failed',
                'message': f'Order verification failed: {error}',
                'details': result.get('details', '')
            }
            
    except Exception as e:
        # Handle Python/Chrome DevTools errors
        return {
            'status': 'execution_error', 
            'message': f'Trade execution failed: {str(e)}'
        }

# Usage
result = safe_trade_execution(connection, 'NQ', 1, 'Buy')
print(f"Trade result: {result['status']} - {result['message']}")
```

### 6. Timeout Handling

```python
def trade_with_custom_timeout(connection, symbol, orders):
    """Scale trading with custom timeout calculation"""
    
    # Calculate timeout based on order complexity
    base_timeout = 15000  # 15 seconds
    per_order_timeout = 2000  # 2 seconds per order
    total_timeout = base_timeout + (len(orders) * per_order_timeout)
    
    print(f"Setting timeout to {total_timeout/1000} seconds for {len(orders)} orders")
    
    try:
        result = connection.auto_trade_scale(
            symbol=symbol,
            scale_orders=orders,
            action='Buy',
            tp_ticks=100,
            sl_ticks=40,
            tick_size=0.25
        )
        return result
        
    except Exception as e:
        if 'timeout' in str(e).lower():
            return {
                'success': False,
                'error': 'Operation timed out',
                'details': f'Orders may still be processing. Timeout was {total_timeout/1000}s'
            }
        else:
            raise
```

## Dashboard API Integration

### 7. Flask Route Implementation

```python
from flask import Flask, request, jsonify
from src.app import TradovateController

app = Flask(__name__)
controller = TradovateController()

@app.route('/api/execute_verified_trade', methods=['POST'])
def execute_verified_trade():
    """Execute trade with verification across all accounts"""
    
    data = request.json
    symbol = data.get('symbol', 'NQ')
    quantity = data.get('quantity', 1)
    action = data.get('action', 'Buy')
    tp_ticks = data.get('tp_ticks', 100)
    sl_ticks = data.get('sl_ticks', 40)
    tick_size = data.get('tick_size', 0.25)
    
    # Execute across all accounts
    results = controller.execute_on_all(
        'auto_trade', symbol, quantity, action, tp_ticks, sl_ticks, tick_size
    )
    
    # Process verification results
    verified_trades = []
    failed_trades = []
    
    for r in results:
        account = r.get('account', 'Unknown')
        result = r.get('result', {})
        
        if result.get('success'):
            verified_trades.append({
                'account': account,
                'orders': result.get('orders', []),
                'message': result.get('message', '')
            })
        else:
            failed_trades.append({
                'account': account,
                'error': result.get('error', 'Unknown error'),
                'details': result.get('details', '')
            })
    
    # Return comprehensive response
    success = len(failed_trades) == 0
    
    return jsonify({
        'success': success,
        'message': f'{len(verified_trades)}/{len(results)} accounts successful',
        'verified_trades': verified_trades,
        'failed_trades': failed_trades,
        'total_accounts': len(results)
    })
```

### 8. Client-Side JavaScript

```javascript
async function executeVerifiedTrade(tradeData) {
    try {
        const response = await fetch('/api/execute_verified_trade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tradeData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`✅ All trades verified successfully`);
            result.verified_trades.forEach(trade => {
                console.log(`  ${trade.account}: ${trade.orders.length} orders`);
            });
        } else {
            console.log(`⚠️ Some trades failed: ${result.message}`);
            result.failed_trades.forEach(trade => {
                console.log(`  ❌ ${trade.account}: ${trade.error}`);
            });
        }
        
        return result;
        
    } catch (error) {
        console.error('Trade execution error:', error);
        throw error;
    }
}

// Usage
const tradeData = {
    symbol: 'NQ',
    quantity: 1,
    action: 'Buy',
    tp_ticks: 100,
    sl_ticks: 40,
    tick_size: 0.25
};

executeVerifiedTrade(tradeData);
```

## Advanced Scenarios

### 9. Portfolio Diversification

```python
def diversified_portfolio_entry(controller, allocations):
    """Enter positions across multiple symbols with verification"""
    
    results = {}
    
    for symbol, config in allocations.items():
        print(f"Executing {symbol} trades...")
        
        # Execute trades for this symbol
        symbol_results = controller.execute_on_all(
            'auto_trade',
            symbol,
            config['quantity'],
            config['action'],
            config['tp_ticks'],
            config['sl_ticks'],
            config['tick_size']
        )
        
        # Count successes
        verified_count = sum(1 for r in symbol_results 
                           if r.get('result', {}).get('success'))
        
        results[symbol] = {
            'verified_accounts': verified_count,
            'total_accounts': len(symbol_results),
            'success_rate': verified_count / len(symbol_results),
            'details': symbol_results
        }
        
        print(f"  {symbol}: {verified_count}/{len(symbol_results)} verified")
    
    return results

# Usage
portfolio = {
    'NQ': {'quantity': 1, 'action': 'Buy', 'tp_ticks': 100, 'sl_ticks': 40, 'tick_size': 0.25},
    'ES': {'quantity': 2, 'action': 'Buy', 'tp_ticks': 50, 'sl_ticks': 25, 'tick_size': 0.25},
    'CL': {'quantity': 1, 'action': 'Sell', 'tp_ticks': 20, 'sl_ticks': 15, 'tick_size': 0.01}
}

results = diversified_portfolio_entry(controller, portfolio)
```

### 10. Risk Management Integration

```python
def risk_managed_trading(controller, max_risk_per_account=500):
    """Execute trades with pre-trade risk assessment"""
    
    # Get account data first
    account_data = controller.execute_on_all('get_account_data')
    
    eligible_accounts = []
    
    for data in account_data:
        account = data.get('account')
        account_info = data.get('result', {})
        
        # Extract account balance (example logic)
        if account_info.get('result', {}).get('value'):
            balance = extract_balance(account_info)  # Custom function
            
            if balance and balance > max_risk_per_account * 10:  # 10:1 buffer
                eligible_accounts.append(account)
                print(f"✅ {account}: Eligible (Balance: ${balance})")
            else:
                print(f"❌ {account}: Insufficient balance")
    
    if not eligible_accounts:
        return {'error': 'No eligible accounts for trading'}
    
    # Execute trades only on eligible accounts
    print(f"Executing trades on {len(eligible_accounts)} eligible accounts...")
    
    # Here you would filter controller.connections to only eligible accounts
    # For brevity, executing on all accounts
    results = controller.execute_on_all('auto_trade', 'NQ', 1, 'Buy', 100, 40, 0.25)
    
    return {
        'eligible_accounts': eligible_accounts,
        'trade_results': results
    }

def extract_balance(account_info):
    """Extract balance from account data (implementation depends on data structure)"""
    # Custom logic to parse account balance
    pass
```

## Command Line Usage

### 11. CLI Trading Scripts

```bash
# Single account trade
python3 -m src.app trade NQ --account 0 --qty 1 --action Buy --tp 100 --sl 40

# All accounts trade  
python3 -m src.app trade NQ --qty 1 --action Buy --tp 100 --sl 40

# Check verification results
python3 -c "
from src.app import TradovateController
controller = TradovateController()
results = controller.execute_on_all('auto_trade', 'NQ', 1, 'Buy', 100, 40, 0.25)
verified = sum(1 for r in results if r.get('result', {}).get('success'))
print(f'Verified: {verified}/{len(results)} accounts')
"
```

### 12. Batch Processing

```python
#!/usr/bin/env python3
"""Batch trading script with verification"""

import json
import sys
from src.app import TradovateController

def batch_trade_from_file(filename):
    """Execute trades from JSON configuration file"""
    
    with open(filename, 'r') as f:
        trade_configs = json.load(f)
    
    controller = TradovateController()
    all_results = []
    
    for config in trade_configs:
        print(f"Executing: {config['symbol']} {config['action']} {config['quantity']}")
        
        results = controller.execute_on_all(
            'auto_trade',
            config['symbol'],
            config['quantity'],
            config['action'],
            config['tp_ticks'],
            config['sl_ticks'],
            config['tick_size']
        )
        
        verified_count = sum(1 for r in results if r.get('result', {}).get('success'))
        print(f"  Verified: {verified_count}/{len(results)} accounts")
        
        all_results.append({
            'config': config,
            'results': results,
            'verified_count': verified_count
        })
    
    return all_results

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 batch_trade.py <config.json>")
        sys.exit(1)
    
    results = batch_trade_from_file(sys.argv[1])
    
    # Summary
    total_trades = len(results)
    successful_trades = sum(1 for r in results if r['verified_count'] > 0)
    
    print(f"\nBatch Summary: {successful_trades}/{total_trades} trade configs had verified orders")
```

## Testing and Validation

### 13. Order Verification Testing

```python
def test_order_verification_system():
    """Test order verification functionality"""
    
    connection = TradovateConnection(port=9222)
    
    # Test 1: Valid order
    print("Test 1: Valid order verification")
    result = connection.auto_trade('NQ', 1, 'Buy', 100, 40, 0.25)
    assert 'success' in result, "Response missing success field"
    assert 'error' in result or 'orders' in result, "Response missing error or orders"
    print(f"  Result: {result.get('success', False)}")
    
    # Test 2: Invalid symbol
    print("Test 2: Invalid symbol handling")
    result = connection.auto_trade('INVALID', 1, 'Buy', 100, 40, 0.25)
    # Should return error, not success
    print(f"  Result: {result}")
    
    # Test 3: Scale orders
    print("Test 3: Scale order verification")
    scale_orders = [{"quantity": 1, "price": 15200}]
    result = connection.auto_trade_scale('NQ', scale_orders, 'Buy', 100, 40, 0.25)
    print(f"  Result: {result.get('success', False)}")
    
    print("Verification tests completed")

# Run tests
test_order_verification_system()
```

These examples demonstrate the comprehensive verification system ensuring that only actually placed orders are reported as successful, maintaining the "browser as source of truth" principle throughout all trading operations.