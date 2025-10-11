#!/usr/bin/env python3

import requests
import json
import sys

def test_dashboard_scale_order():
    """Test scale order through the dashboard API"""
    
    # Simulate the same API call that the dashboard would make
    api_url = "http://localhost:6001/api/trade"
    
    # Test data with scale enabled
    test_data = {
        "symbol": "NQ",
        "quantity": 4,  # 4 contracts to split into 4 levels = 1 each
        "action": "Buy",
        "tick_size": 0.25,
        "entry_price": None,  # Market orders
        "account": "all",
        "enable_tp": True,
        "tp_ticks": 100,
        "enable_sl": True,
        "sl_ticks": 40,
        "scale_in_enabled": True,   # THIS IS THE KEY - enable scale
        "scale_in_levels": 4,       # 4 levels as expected
        "scale_in_ticks": 20        # 20 ticks between levels
    }
    
    print(f"Testing dashboard scale order with data:")
    print(json.dumps(test_data, indent=2))
    print(f"\nMaking API call to {api_url}...")
    
    try:
        response = requests.post(api_url, json=test_data, timeout=30)
        
        print(f"\n=== API RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Response JSON:")
                print(json.dumps(response_data, indent=2))
                
                # Check if it was a scale order
                if 'scale_orders' in str(response_data):
                    print(f"\n✅ Scale order detected in response")
                else:
                    print(f"\n❌ No scale order indication in response")
                    
                return True
            except json.JSONDecodeError:
                print(f"Response Text: {response.text}")
                return False
        else:
            print(f"Response Text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to {api_url}")
        print(f"Make sure the dashboard is running with: python3 -m src.app dashboard")
        return False
    except Exception as e:
        print(f"❌ Error making API call: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_scale_order()
    if success:
        print(f"\n✅ Dashboard scale order test completed")
    else:
        print(f"\n❌ Dashboard scale order test failed")
    
    sys.exit(0 if success else 1)