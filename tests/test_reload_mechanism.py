#!/usr/bin/env python3
"""Test the config reload mechanism"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_reload_mechanism():
    """Test that reload endpoint properly updates values"""
    print("=== Testing Reload Mechanism ===")
    
    # Clear cache and import fresh
    modules_to_clear = [m for m in sys.modules.keys() if m.startswith('src.')]
    for module in modules_to_clear:
        del sys.modules[module]
    
    from src.dashboard import reload_trading_defaults, TRADING_DEFAULTS, trading_defaults_path
    
    # Save original config
    with open(trading_defaults_path, 'r') as f:
        original_config = json.load(f)
    
    print(f"\n1. Original quantity: {TRADING_DEFAULTS.get('quantity')}")
    
    # Modify config file
    test_config = original_config.copy()
    test_config['trading_defaults']['quantity'] = 25
    test_config['trading_defaults']['stop_loss_ticks'] = 30
    
    with open(trading_defaults_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print("2. Modified config file (quantity=25, sl=30)")
    
    # Before reload, values should be unchanged
    print(f"3. Before reload - quantity: {TRADING_DEFAULTS.get('quantity')}")
    
    # Simulate the reload endpoint call
    try:
        # Import the Flask app context
        from src.dashboard import app
        
        with app.app_context():
            response = reload_trading_defaults()
            response_data, status_code = response
            
            print(f"4. Reload response: {response_data.get_json()}")
            print(f"   Status code: {status_code}")
        
        # After reload, values should be updated
        print(f"5. After reload - quantity: {TRADING_DEFAULTS.get('quantity')}")
        print(f"   After reload - stop_loss: {TRADING_DEFAULTS.get('stop_loss_ticks')}")
        
        if TRADING_DEFAULTS.get('quantity') == 25:
            print("✅ PASS: Reload successfully updated values")
        else:
            print("❌ FAIL: Reload did not update values")
    
    except Exception as e:
        print(f"Error during reload test: {e}")
    
    finally:
        # Restore original config
        with open(trading_defaults_path, 'w') as f:
            json.dump(original_config, f, indent=2)
        
        # Reload again to restore
        try:
            from src.dashboard import app
            with app.app_context():
                reload_trading_defaults()
        except:
            pass
        
        print("\n6. Config restored to original")

if __name__ == "__main__":
    test_reload_mechanism()