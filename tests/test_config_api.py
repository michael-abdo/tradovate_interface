#!/usr/bin/env python3
"""Test script for trading defaults configuration API"""

import json
import requests
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_endpoints(base_url="http://localhost:6001"):
    """Test the trading defaults API endpoints"""
    
    print("=== Testing Trading Defaults API Endpoints ===\n")
    
    # Test 1: GET /api/trading-defaults
    print("Test 1: GET /api/trading-defaults")
    try:
        response = requests.get(f"{base_url}/api/trading-defaults", timeout=5)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("  Response structure:")
            print(f"    - trading_defaults: {list(data.get('trading_defaults', {}).keys())}")
            print(f"    - symbol_defaults: {list(data.get('symbol_defaults', {}).keys())}")
            
            defaults = data.get('trading_defaults', {})
            print(f"  Quantity default: {defaults.get('quantity')}")
            print(f"  Risk/Reward ratio: {defaults.get('risk_reward_ratio')}")
            print("  ✅ PASS")
        else:
            print(f"  ❌ FAIL: Expected 200, got {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    print()
    
    # Test 2: POST /api/trading-defaults/reload
    print("Test 2: POST /api/trading-defaults/reload")
    try:
        response = requests.post(f"{base_url}/api/trading-defaults/reload", timeout=5)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
            print("  ✅ PASS")
        else:
            print(f"  ❌ FAIL: Expected 200, got {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    print()
    
    # Test 3: Test config change and reload
    print("Test 3: Config change and reload")
    config_path = "config/trading_defaults.json"
    
    try:
        # Read current config
        with open(config_path, 'r') as f:
            original_config = json.load(f)
        
        # Modify config
        test_config = original_config.copy()
        test_config['trading_defaults']['quantity'] = 99
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        print("  Modified config (quantity = 99)")
        
        # Reload
        response = requests.post(f"{base_url}/api/trading-defaults/reload", timeout=5)
        if response.status_code != 200:
            print(f"  ❌ FAIL: Reload failed with status {response.status_code}")
        else:
            # Verify change
            response = requests.get(f"{base_url}/api/trading-defaults", timeout=5)
            if response.status_code == 200:
                data = response.json()
                new_quantity = data['trading_defaults']['quantity']
                if new_quantity == 99:
                    print(f"  ✅ PASS: Quantity updated to {new_quantity}")
                else:
                    print(f"  ❌ FAIL: Expected quantity 99, got {new_quantity}")
            else:
                print(f"  ❌ FAIL: Could not verify change")
        
        # Restore original config
        with open(config_path, 'w') as f:
            json.dump(original_config, f, indent=2)
        
        # Reload again
        requests.post(f"{base_url}/api/trading-defaults/reload", timeout=5)
        print("  Restored original config")
        
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        # Try to restore config
        try:
            with open(config_path, 'w') as f:
                json.dump(original_config, f, indent=2)
        except:
            pass
    
    print()
    
    # Test 4: Error handling - malformed config
    print("Test 4: Error handling with malformed config")
    try:
        # Save current config
        with open(config_path, 'r') as f:
            original_config = f.read()
        
        # Write malformed JSON
        with open(config_path, 'w') as f:
            f.write('{ invalid json }')
        
        # Try to reload
        response = requests.post(f"{base_url}/api/trading-defaults/reload", timeout=5)
        print(f"  Reload status: {response.status_code}")
        
        if response.status_code == 500:
            print("  ✅ PASS: Server correctly returned error status")
        else:
            print(f"  ⚠️  WARNING: Expected 500, got {response.status_code}")
        
        # Verify defaults still work
        response = requests.get(f"{base_url}/api/trading-defaults", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('trading_defaults', {}).get('quantity') is not None:
                print("  ✅ PASS: API still returns valid defaults")
            else:
                print("  ❌ FAIL: API not returning valid defaults")
        
        # Restore config
        with open(config_path, 'w') as f:
            f.write(original_config)
        
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        # Try to restore
        try:
            with open(config_path, 'w') as f:
                f.write(original_config)
        except:
            pass
    
    print("\n=== API Endpoint Tests Complete ===")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:6001"
    
    print(f"Testing against: {base_url}")
    print("Make sure the dashboard is running!")
    print()
    
    test_api_endpoints(base_url)