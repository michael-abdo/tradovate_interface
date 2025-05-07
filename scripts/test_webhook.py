#!/usr/bin/env python3
"""
Webhook Testing Script

This script tests the webhook endpoint with various payload formats to help debug any issues.
"""
import requests
import json
import time
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Default webhook URL (change if needed)
DEFAULT_URL = "http://localhost:6000/webhook"

def test_json_payload(url=DEFAULT_URL):
    """Test with proper JSON payload"""
    print("\n=== Testing with proper JSON payload ===")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "symbol": "NQ",
        "action": "Buy",
        "orderQty": 1,
        "orderType": "Market",
        "entryPrice": 20000,
        "takeProfitPrice": 20100,
        "tradeType": "Open",
        "strategy": "DEFAULT"
    }
    
    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_text_plain_payload(url=DEFAULT_URL):
    """Test with text/plain payload (TradingView format)"""
    print("\n=== Testing with text/plain payload (TradingView format) ===")
    
    headers = {
        "Content-Type": "text/plain"
    }
    
    # TradingView sometimes sends data in this format
    payload = """
    symbol: NQ
    action: Buy
    orderQty: 1
    orderType: Market
    entryPrice: 20000
    takeProfitPrice: 20100
    tradeType: Open
    strategy: DEFAULT
    """
    
    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_embedded_json_payload(url=DEFAULT_URL):
    """Test with text/plain payload containing embedded JSON (TradingView alert format)"""
    print("\n=== Testing with embedded JSON in text/plain payload ===")
    
    headers = {
        "Content-Type": "text/plain"
    }
    
    # TradingView alert might have JSON embedded in text
    payload = """
    TradingView Alert Triggered at 2023-04-29 05:59:00
    
    {"symbol": "NQ", "action": "Buy", "orderQty": 1, "orderType": "Market", "entryPrice": 20000, "takeProfitPrice": 20100, "tradeType": "Open", "strategy": "DEFAULT"}
    
    End of alert.
    """
    
    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_minimal_payload(url=DEFAULT_URL):
    """Test with minimal required payload (just symbol)"""
    print("\n=== Testing with minimal payload ===")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "symbol": "NQ"
    }
    
    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_health_endpoint(url="http://localhost:6000/health"):
    """Test the health check endpoint"""
    print("\n=== Testing health check endpoint ===")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function to run all tests"""
    # First test the health endpoint
    health_ok = test_health_endpoint()
    
    if not health_ok:
        print("\n❌ Health check failed. Server might not be running.")
        decision = input("Continue with tests anyway? (y/n): ")
        if decision.lower() != 'y':
            return
    
    # Get custom URL if provided
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = DEFAULT_URL
    
    print(f"\nRunning webhook tests against: {url}")
    
    # Run the tests
    results = []
    results.append(("JSON payload", test_json_payload(url)))
    time.sleep(1)
    results.append(("Text/plain payload", test_text_plain_payload(url)))
    time.sleep(1)
    results.append(("Embedded JSON payload", test_embedded_json_payload(url)))
    time.sleep(1)
    results.append(("Minimal payload", test_minimal_payload(url)))
    
    # Summary
    print("\n=== Test Results Summary ===")
    for name, result in results:
        print(f"{name}: {'✅ PASS' if result else '❌ FAIL'}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed. Check the logs for more details.")

if __name__ == "__main__":
    main()