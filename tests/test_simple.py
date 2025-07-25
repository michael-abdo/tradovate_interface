#!/usr/bin/env python3
"""
Simple test to open a Chrome browser to the mock Tradovate login page
"""
import webbrowser
import os
import time
import http.server
import threading

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
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    httpd.serve_forever()

# Start the server in a background thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

print("Starting server...")
time.sleep(1)  # Give the server time to start

# Open the mock Tradovate login page in the default browser
mock_url = "http://localhost:8000/mock_tradovate.html"
print(f"Opening {mock_url} in your browser...")
webbrowser.open(mock_url)

print("\n=== Test Instructions ===")
print("1. The page should now be open in your browser")
print("2. You can test the login flow manually:")
print("   - Enter credentials and click 'Sign In'")
print("   - Click 'Access Simulation' to continue to the dashboard")
print("3. Use the test controls at the bottom to simulate different states:")
print("   - 'Show Login Page' - Shows the login form (similar to being logged out)")
print("   - 'Show Account Selection' - Shows the account selection page")
print("   - 'Show Dashboard' - Shows the logged-in dashboard")
print("   - 'Auto Logout' - Will automatically log out after 10 seconds")
print("\nPress Ctrl+C to stop the test server when done")

try:
    # Keep the script running so the server stays up
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTest terminated by user")
except Exception as e:
    print(f"\nTest terminated with error: {e}")
finally:
    print("\nCleaning up...")
    # The HTTP server will automatically shut down when the program exits
    # because it's running in a daemon thread