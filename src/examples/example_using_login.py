#!/usr/bin/env python3
import time
import sys
from login_helper import login_to_existing_chrome, wait_for_element, execute_js

def change_symbol_and_trade(tab, symbol="NQ", action="Buy", quantity=1):
    """
    Change the symbol and place a trade.
    
    Args:
        tab: The Chrome tab handle
        symbol: Trading symbol (e.g., "NQ", "ES")
        action: "Buy" or "Sell"
        quantity: Number of contracts
        
    Returns:
        bool: Success or failure
    """
    print(f"\nChanging symbol to {symbol} and placing {action} order for {quantity} contract(s)...")
    
    # Wait to ensure we're fully logged in
    time.sleep(3)
    
    # Enter symbol in the chart
    symbol_script = f"""
    (function() {{
        const symbolInput = document.querySelector('input.symbol-input, input[placeholder="Symbol"]');
        if (!symbolInput) {{
            console.error("Symbol input not found");
            return false;
        }}
        
        console.log("Found symbol input, setting value to {symbol}");
        
        // Set the value and trigger events
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(symbolInput, "{symbol}");
        symbolInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
        symbolInput.dispatchEvent(new Event("change", {{ bubbles: true }}));
        
        // Also try pressing Enter
        setTimeout(() => {{
            symbolInput.dispatchEvent(new KeyboardEvent("keydown", {{ key: "Enter", code: "Enter", keyCode: 13, bubbles: true }}));
        }}, 300);
        
        return true;
    }})();
    """
    
    symbol_result = execute_js(tab, symbol_script)
    print(f"Symbol change result: {symbol_result}")
    
    # Allow time for the symbol to load
    time.sleep(2)
    
    # Set quantity
    qty_script = f"""
    (function() {{
        const qtyInput = document.querySelector('input#qtyInput, input[placeholder="Quantity"]');
        if (!qtyInput) {{
            console.error("Quantity input not found");
            return false;
        }}
        
        console.log("Found quantity input, setting value to {quantity}");
        
        // Set the value and trigger events
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(qtyInput, "{quantity}");
        qtyInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
        qtyInput.dispatchEvent(new Event("change", {{ bubbles: true }}));
        
        return true;
    }})();
    """
    
    qty_result = execute_js(tab, qty_script)
    print(f"Quantity change result: {qty_result}")
    
    # Allow time for UI to update
    time.sleep(1)
    
    # Click Buy or Sell button
    trade_script = f"""
    (function() {{
        const button = document.querySelector('{"button.buy-button" if action.lower() == "buy" else "button.sell-button"}');
        if (!button) {{
            console.error("{action} button not found");
            return false;
        }}
        
        console.log("Found {action} button, clicking it");
        button.click();
        return true;
    }})();
    """
    
    trade_result = execute_js(tab, trade_script)
    print(f"Trade execution result: {trade_result}")
    
    # Visual confirmation
    confirm_script = f"""
    (function() {{
        const notification = document.createElement('div');
        notification.style.position = 'fixed';
        notification.style.top = '50%';
        notification.style.left = '50%';
        notification.style.transform = 'translate(-50%, -50%)';
        notification.style.background = '{"#4cd964" if action.lower() == "buy" else "#ff3b30"}';
        notification.style.color = 'white';
        notification.style.padding = '20px';
        notification.style.borderRadius = '10px';
        notification.style.zIndex = '10000';
        notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.5)';
        notification.style.fontWeight = 'bold';
        notification.innerHTML = '{action} {quantity} {symbol}';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {{
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => notification.remove(), 500);
        }}, 2000);
        
        return true;
    }})();
    """
    
    execute_js(tab, confirm_script)
    return True

def main():
    """Example script demonstrating how to use the login helper"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Example of using the Tradovate login helper")
    parser.add_argument("--port", type=int, default=9222, help="Chrome debugging port")
    parser.add_argument("--symbol", default="NQ", help="Symbol to trade")
    parser.add_argument("--action", default="Buy", choices=["Buy", "Sell"], help="Trade action")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity to trade")
    args = parser.parse_args()
    
    print(f"Logging in to Chrome on port {args.port}...")
    success, tab, browser = login_to_existing_chrome(port=args.port)
    
    if not success:
        print("Failed to login")
        return 1
    
    print("Login initiated successfully")
    
    # Wait for dashboard to appear (indicating successful login)
    if wait_for_element(tab, ".desktop-dashboard", timeout=20):
        print("Dashboard loaded - login successful")
        
        # Now change symbol and place trade
        change_symbol_and_trade(tab, args.symbol, args.action, args.quantity)
        
        print("\nOperation completed. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print("Login may have failed - dashboard not detected")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())