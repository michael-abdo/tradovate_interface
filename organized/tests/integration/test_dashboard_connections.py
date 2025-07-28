#!/usr/bin/env python3
import requests
import json
import time

# First, let's check the health endpoint
print("=== Checking connection health ===")
try:
    response = requests.get('http://localhost:6001/api/health')
    if response.status_code == 200:
        health_data = response.json()
        print(f"Health API Response: {json.dumps(health_data, indent=2)}")
    else:
        print(f"Health API Error: {response.status_code}")
except Exception as e:
    print(f"Error calling health API: {e}")

# Now check accounts
print("\n=== Checking accounts endpoint ===")
try:
    response = requests.get('http://localhost:6001/api/accounts')
    if response.status_code == 200:
        accounts_data = response.json()
        print(f"Accounts API Response: {json.dumps(accounts_data, indent=2)}")
    else:
        print(f"Accounts API Error: {response.status_code}")
except Exception as e:
    print(f"Error calling accounts API: {e}")

# Check summary endpoint
print("\n=== Checking summary endpoint ===")
try:
    response = requests.get('http://localhost:6001/api/summary')
    if response.status_code == 200:
        summary_data = response.json()
        print(f"Summary API Response: {json.dumps(summary_data, indent=2)}")
    else:
        print(f"Summary API Error: {response.status_code}")
except Exception as e:
    print(f"Error calling summary API: {e}")