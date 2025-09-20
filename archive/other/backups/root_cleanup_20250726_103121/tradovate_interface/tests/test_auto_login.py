#!/usr/bin/env python3
"""
Test script for auto_login.py with a local test HTML page
instead of the actual Tradovate site
"""
import os
import time
import subprocess
import webbrowser
import http.server
import threading
import signal
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Create a mock login page for testing
MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Tradovate Login Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }
        .login-page {
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .dashboard-page {
            display: none;
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .account-selection {
            display: none;
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .bar--heading {
            background-color: #f0f0f0;
            padding: 10px;
            margin-bottom: 10px;
        }
        .pane.account-selector {
            background-color: #f0f0f0;
            padding: 10px;
            margin-bottom: 10px;
        }
        button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button.MuiButton-containedPrimary {
            background-color: #2196F3;
        }
        button.tm {
            background-color: #9C27B0;
        }
        input {
            padding: 8px;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
        }
        .controls {
            margin-top: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Tradovate Login Test Page</h1>
    <p>This page simulates the Tradovate login flow for testing auto_login.py</p>
    
    <div class="login-page" id="login-page">
        <h2>Login</h2>
        <div>
            <label for="name-input">Email:</label>
            <input type="text" id="name-input" placeholder="Email">
        </div>
        <div>
            <label for="password-input">Password:</label>
            <input type="password" id="password-input" placeholder="Password">
        </div>
        <div>
            <button class="MuiButton-containedPrimary" id="login-button">Sign In</button>
        </div>
    </div>
    
    <div class="account-selection" id="account-selection">
        <h2>Select Account</h2>
        <p>Choose an account to access:</p>
        <button class="tm" id="access-simulation">Access Simulation</button>
    </div>
    
    <div class="dashboard-page" id="dashboard-page">
        <h2>Tradovate Dashboard</h2>
        <div class="bar--heading">Welcome to Tradovate</div>
        <div class="pane account-selector">Account: Demo Account</div>
        <p>You are now logged in!</p>
        <button id="logout-button">Log Out</button>
    </div>
    
    <div class="controls">
        <h3>Test Controls</h3>
        <button id="show-login">Show Login Page</button>
        <button id="show-account-selection">Show Account Selection</button>
        <button id="show-dashboard">Show Dashboard</button>
        <button id="auto-logout">Auto Logout (after 10s)</button>
    </div>
    
    <script>
        // Simulate the login flow
        document.getElementById('login-button').addEventListener('click', function() {
            const email = document.getElementById('name-input').value;
            const password = document.getElementById('password-input').value;
            
            if (email && password) {
                console.log(`Login attempt with: ${email}`);
                document.getElementById('login-page').style.display = 'none';
                document.getElementById('account-selection').style.display = 'block';
            } else {
                console.error('Email and password required');
            }
        });
        
        document.getElementById('access-simulation').addEventListener('click', function() {
            console.log('Access Simulation clicked');
            document.getElementById('account-selection').style.display = 'none';
            document.getElementById('dashboard-page').style.display = 'block';
        });
        
        document.getElementById('logout-button').addEventListener('click', function() {
            console.log('Manual logout');
            document.getElementById('dashboard-page').style.display = 'none';
            document.getElementById('login-page').style.display = 'block';
            // Clear inputs
            document.getElementById('name-input').value = '';
            document.getElementById('password-input').value = '';
        });
        
        // Test controls
        document.getElementById('show-login').addEventListener('click', function() {
            document.getElementById('login-page').style.display = 'block';
            document.getElementById('account-selection').style.display = 'none';
            document.getElementById('dashboard-page').style.display = 'none';
        });
        
        document.getElementById('show-account-selection').addEventListener('click', function() {
            document.getElementById('login-page').style.display = 'none';
            document.getElementById('account-selection').style.display = 'block';
            document.getElementById('dashboard-page').style.display = 'none';
        });
        
        document.getElementById('show-dashboard').addEventListener('click', function() {
            document.getElementById('login-page').style.display = 'none';
            document.getElementById('account-selection').style.display = 'none';
            document.getElementById('dashboard-page').style.display = 'block';
        });
        
        document.getElementById('auto-logout').addEventListener('click', function() {
            setTimeout(function() {
                console.log('Auto logout triggered after timeout');
                document.getElementById('dashboard-page').style.display = 'none';
                document.getElementById('login-page').style.display = 'block';
                // Clear inputs
                document.getElementById('name-input').value = '';
                document.getElementById('password-input').value = '';
            }, 10000); // 10 seconds
        });
    </script>
</body>
</html>
"""

# Create a directory for the mock HTML page
os.makedirs(os.path.join(project_root, "temp"), exist_ok=True)
mock_html_path = os.path.join(project_root, "temp", "mock_tradovate.html")

# Write the mock HTML
with open(mock_html_path, "w") as f:
    f.write(MOCK_HTML)

# Define a simple HTTP server to serve the mock login page
class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(mock_html_path), **kwargs)
    
    def log_message(self, format, *args):
        # Suppress logging
        pass

# Start the HTTP server in a separate thread
def start_server():
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Mock server started at http://localhost:8000")
    print("You can access the mock login page at http://localhost:8000/mock_tradovate.html")
    httpd.serve_forever()

# Start the server in a background thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

print("Starting server...")
time.sleep(1)  # Give the server time to start

# Now import and run a modified version of auto_login
from src import auto_login

# Override TRADOVATE_URL to point to our mock server
auto_login.TRADOVATE_URL = "http://localhost:8000/mock_tradovate.html"

# Reduce login monitor interval for testing
auto_login.ChromeInstance.login_check_interval = 5  # Check every 5 seconds instead of 30

print("\nStarting auto_login with modified URL...")
print("This test will use the mock Tradovate login page to test the auto-login functionality")
print("You can use the test controls on the page to simulate different login states")
print("\nNOTE: To test the auto re-login feature, click 'Auto Logout' and wait 10 seconds")
print("The auto-login script should detect the logout and automatically log back in\n")

try:
    auto_login.main()
except KeyboardInterrupt:
    print("\nTest terminated by user")
except Exception as e:
    print(f"\nTest terminated with error: {e}")
finally:
    print("\nCleaning up...")
    # Clean up mock files if desired
    # os.remove(mock_html_path)
    
    # Note: The HTTP server will automatically shut down when the program exits
    # because it's running in a daemon thread.