#!/usr/bin/env python3
"""
Unified Chrome Configuration Management
Consolidates Chrome path detection, port management, and startup arguments
"""
import platform
import os
import subprocess

def find_chrome_path():
    """Find the Chrome executable path based on the operating system"""
    print(f"Operating system: {platform.system()}")
    
    if platform.system() == "Darwin":  # macOS
        # Try multiple possible paths
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            # Add any other possible macOS Chrome paths here
        ]
    elif platform.system() == "Windows":
        # Try multiple possible paths
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
            # Add any other possible Windows Chrome paths here
        ]
    else:  # Linux and others
        # Try multiple possible paths
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            # Add any other possible Linux Chrome paths here
        ]
    
    # Try each path
    for path in paths:
        print(f"Checking path: {path}")
        if os.path.exists(path):
            print(f"Found Chrome at: {path}")
            return path
        else:
            print(f"  - Not found")
    
    # If Chrome is not found in the common paths, try to find it in PATH
    try:
        print("Trying to find Chrome in PATH...")
        if platform.system() == "Windows":
            result = subprocess.run(["where", "chrome"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            
            if result.returncode != 0:
                result = subprocess.run(["which", "chrome"], capture_output=True, text=True)
            
            if result.returncode != 0:
                result = subprocess.run(["which", "chromium"], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            print(f"Found Chrome in PATH: {path}")
            return path
        else:
            print(f"Chrome not found in PATH: {result.stderr}")
    except Exception as e:
        print(f"Error finding Chrome in PATH: {e}")
    
    # Default path as fallback
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    print(f"Chrome not found, will try with default path: {default_path}")
    return default_path

# Chrome Port Configuration Management
BASE_DEBUGGING_PORT = 9223  # Start from 9223 to avoid 9222 (Rule #0)
PROTECTED_PORT = 9222       # Never kill or interfere with this port

def get_chrome_ports():
    """Get standardized Chrome port configuration"""
    return {
        'base_trading_port': BASE_DEBUGGING_PORT,
        'protected_port': PROTECTED_PORT,
        'port_range': range(BASE_DEBUGGING_PORT, BASE_DEBUGGING_PORT + 20)
    }

def is_port_safe_to_use(port):
    """Check if a port is safe to use for trading Chrome instances"""
    if port == PROTECTED_PORT:
        print(f"SAFETY: Port {port} is protected and cannot be used for trading")
        return False
    if port < BASE_DEBUGGING_PORT:
        print(f"SAFETY: Port {port} is below base trading port {BASE_DEBUGGING_PORT}")
        return False
    return True

def validate_chrome_port(port):
    """Validate Chrome port with safety checks"""
    try:
        port = int(port)
        if not is_port_safe_to_use(port):
            return False
        return True
    except (ValueError, TypeError):
        print(f"ERROR: Invalid port value: {port}")
        return False

def get_chrome_startup_args(port, profile_dir, target_url="https://trader.tradovate.com"):
    """Get standardized Chrome startup arguments"""
    return [
        "--remote-debugging-port=" + str(port),
        "--remote-allow-origins=*",
        "--user-data-dir=" + str(profile_dir),
        "--no-first-run",
        "--no-default-browser-check", 
        "--new-window",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-save-password-bubble",
        # GPU-related flags to prevent crashes
        "--disable-gpu-sandbox",
        "--disable-software-rasterizer", 
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu-compositing",
        "--enable-features=SharedArrayBuffer",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        # Additional stability flags
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        # Memory and performance flags
        "--max_old_space_size=4096",
        "--js-flags=--max-old-space-size=4096",
        "--force-color-profile=srgb",
        target_url,
    ]

def get_unified_chrome_config(port=None, profile_dir=None, target_url=None):
    """Get complete unified Chrome configuration"""
    config = {
        'chrome_path': find_chrome_path(),
        'port': port or BASE_DEBUGGING_PORT,
        'profile_dir': profile_dir or f"/tmp/chrome_profile_{port or BASE_DEBUGGING_PORT}",
        'target_url': target_url or "https://trader.tradovate.com"
    }
    
    # Validate port safety
    if not validate_chrome_port(config['port']):
        raise ValueError(f"Invalid or unsafe Chrome port: {config['port']}")
    
    # Build complete Chrome command
    config['chrome_args'] = get_chrome_startup_args(
        config['port'], 
        config['profile_dir'], 
        config['target_url']
    )
    config['chrome_command'] = [config['chrome_path']] + config['chrome_args']
    
    return config

if __name__ == "__main__":
    chrome_path = find_chrome_path()
    print(f"\nSelected Chrome path: {chrome_path}")
    
    # Try to get Chrome version without running it
    try:
        result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Chrome version: {result.stdout.strip()}")
        else:
            print(f"Failed to get Chrome version: {result.stderr}")
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
    
    # Test unified configuration
    print("\n--- Unified Chrome Configuration Test ---")
    try:
        config = get_unified_chrome_config()
        print(f"Port: {config['port']}")
        print(f"Profile: {config['profile_dir']}")
        print(f"Target: {config['target_url']}")
        print(f"Args count: {len(config['chrome_args'])}")
        print(f"Command ready: {len(config['chrome_command'])} components")
    except Exception as e:
        print(f"Configuration error: {e}")