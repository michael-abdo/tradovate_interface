#!/usr/bin/env python3
import requests
import time

# Call the API and check console output
print("=== Calling /api/accounts ===")
response = requests.get('http://localhost:6001/api/accounts')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Now let's see if we can get more info by triggering an error
print("\n=== Calling /api/health ===")
try:
    response = requests.get('http://localhost:6001/api/health')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # First 200 chars
except Exception as e:
    print(f"Error: {e}")

# Let's check the startup monitoring endpoint
print("\n=== Calling /api/startup-monitoring ===")
try:
    response = requests.get('http://localhost:6001/api/startup-monitoring')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # First 200 chars
except Exception as e:
    print(f"Error: {e}")

# Try to trigger account data update
print("\n=== Trying to update phases ===")
try:
    response = requests.post('http://localhost:6001/api/update-phases')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Wait a moment and try accounts again
time.sleep(2)
print("\n=== Calling /api/accounts again ===")
response = requests.get('http://localhost:6001/api/accounts')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")