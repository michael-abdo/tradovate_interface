#!/usr/bin/env python3
"""
Main entry point for the Tradovate Interface application

This script provides a simple command-line interface to select which
component to launch: auto-login, dashboard, webhook, etc.
"""
import sys
import os
import argparse
import time
import threading
import subprocess

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import all main functions from modules
from src.app import main as app_main
from src.auto_login import main as auto_login_main
from src.dashboard import run_flask_dashboard
from src.login_helper import main as login_helper_main
from src.pinescript_webhook import run_flask as run_webhook_server
from src.chrome_logger import main as chrome_logger_main
# Use unified credential management from Chrome Communication Framework
try:
    from src.utils.chrome_communication import get_unified_credentials_count
    def load_credentials_count():
        """Load credentials count using unified authentication manager"""
        count = get_unified_credentials_count()
        print(f"📊 Found {count} accounts via unified authentication manager")
        return count
except ImportError:
    def load_credentials_count():
        """Fallback credential count if unified framework not available"""
        print("❌ Unified authentication not available")
        return 0

def ensure_chrome_range_running():
    """
    Enhanced Chrome management - check required Chrome instances and return missing ports.
    NEVER touches port 9222 (CLAUDE.md Rule #0 compliance).
    """
    import requests
    
    # Pre-flight validation
    account_count = load_credentials_count()
    if account_count == 0:
        print("❌ No valid credentials found - cannot determine Chrome instances needed")
        return [], []
        
    # SAFETY: Verify we never touch protected port 9222
    base_port = 9223  # Start from 9223 per CLAUDE.md rules
    required_ports = [base_port + i for i in range(account_count)]
    
    # Verify no port 9222 in our range (paranoid safety check)
    if 9222 in required_ports:
        print("🚨 SAFETY VIOLATION: Port 9222 detected in required ports - ABORTING")
        return [], []
    
    print(f"🔍 Checking Chrome instances on ports: {required_ports}")
    
    # Check each required port
    running_ports = []
    missing_ports = []
    
    for port in required_ports:
        try:
            response = requests.get(f'http://127.0.0.1:{port}/json', timeout=2)
            if response.status_code == 200:
                tabs = response.json()
                print(f"✅ Chrome running on port {port} with {len(tabs)} tabs")
                running_ports.append(port)
            else:
                print(f"⚠️  Chrome on port {port} not responding properly")
                missing_ports.append(port)
        except Exception:
            print(f"❌ Chrome not accessible on port {port}")
            missing_ports.append(port)
    
    print(f"📊 Status: {len(running_ports)} running, {len(missing_ports)} missing")
    return running_ports, missing_ports

def start_chrome_instances(missing_ports):
    """
    Start Chrome instances on missing ports with robust error handling.
    NEVER starts Chrome on port 9222 (CLAUDE.md Rule #0 compliance).
    
    Returns:
        tuple: (success: bool, started_ports: list, failed_ports: list)
    """
    if not missing_ports:
        print("✅ No Chrome instances need to be started")
        return True, [], []
    
    # SAFETY: Double-check we never touch port 9222
    if 9222 in missing_ports:
        print("🚨 SAFETY VIOLATION: Attempt to start Chrome on protected port 9222 - ABORTING")
        return False, [], missing_ports
    
    print(f"🚀 Starting Chrome instances on ports: {missing_ports}")
    
    try:
        # Import required modules
        import json
        import re
        from src.auto_login import ChromeInstance
        from src.utils.chrome_stability import ChromeStabilityMonitor
        
        # Load credentials using unified authentication manager
        try:
            from src.utils.chrome_communication import load_unified_credentials
            cred_list = load_unified_credentials(allow_duplicates=True)
            print(f"✅ Loaded {len(cred_list)} credential pairs via unified authentication manager")
        except ImportError:
            print("⚠️  Unified authentication not available, using fallback credential loading")
            # Fallback credential loading
            credentials_path = os.path.join(project_root, 'config/credentials.json')
            with open(credentials_path, 'r') as file:
                file_content = file.read()
                
            # Handle JSON parsing with regex fallback
            try:
                credentials = json.loads(file_content)
            except json.JSONDecodeError:
                print("⚠️  Using regex extraction for credentials")
                pairs = re.findall(r'"([^"]+@[^"]+)"\s*:\s*"([^"]+)"', file_content)
                credentials = dict(pairs)
            
            # Convert credentials to list for port assignment
            cred_list = list(credentials.items())
        
        # Initialize monitoring
        monitor = ChromeStabilityMonitor()
        
        # Start Chrome instances
        started_instances = []
        started_ports = []
        failed_ports = []
        
        for i, port in enumerate(missing_ports):
            try:
                # Get credentials for this port (cycling if more ports than accounts)
                username, password = cred_list[i % len(cred_list)]
                account_name = f"Account_{port-9223+1}_{username.split('@')[0]}"
                
                print(f"🔧 Starting Chrome instance {i+1}: {account_name} on port {port}")
                
                # Create and start Chrome instance
                instance = ChromeInstance(port, username, password, account_name)
                success = instance.start()
                
                if success:
                    print(f"✅ Chrome instance started successfully on port {port}")
                    started_instances.append(instance)
                    started_ports.append(port)
                    
                    # Register for health monitoring
                    monitor.register_connection(account_name, port)
                    
                    # Brief pause between instance starts to avoid resource conflicts
                    time.sleep(2)
                else:
                    print(f"❌ Failed to start Chrome instance on port {port}")
                    failed_ports.append(port)
                    
            except Exception as e:
                print(f"❌ Error starting Chrome on port {port}: {e}")
                failed_ports.append(port)
        
        # Start health monitoring for validation
        if started_ports:
            print(f"🔍 Starting health monitoring for {len(started_ports)} instances...")
            monitor.start_health_monitoring()
            
            # Wait for initial health validation (5 seconds)
            print("⏳ Waiting for health validation...")
            time.sleep(5)
            
            # Check health status
            health_status = monitor.get_connection_health_status()
            healthy_count = 0
            
            for account, status in health_status.get('connections', {}).items():
                if status['state'] in ['healthy', 'degraded']:
                    healthy_count += 1
                    print(f"✅ {account}: {status['state']}")
                else:
                    print(f"⚠️  {account}: {status['state']}")
            
            print(f"📊 Health check: {healthy_count}/{len(started_ports)} instances healthy")
        
        # Determine overall success
        total_success = len(failed_ports) == 0
        
        if total_success:
            print(f"🎉 Successfully started all {len(started_ports)} Chrome instances")
        elif started_ports:
            print(f"⚠️  Partial success: {len(started_ports)} started, {len(failed_ports)} failed")
        else:
            print(f"❌ Failed to start any Chrome instances")
        
        return total_success, started_ports, failed_ports
        
    except Exception as e:
        print(f"❌ Critical error in Chrome instance startup: {e}")
        return False, [], missing_ports

def ensure_chrome_9223_running():
    """
    Legacy function - maintained for backward compatibility.
    Use ensure_chrome_range_running() for enhanced multi-instance support.
    """
    running_ports, missing_ports = ensure_chrome_range_running()
    return 9223 in running_ports

def main():
    parser = argparse.ArgumentParser(
        description="Tradovate Multi-Account Interface - Main Entry Point"
    )
    
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Component to launch"
    )
    
    # App commands
    app_parser = subparsers.add_parser(
        "app", 
        help="Launch the main application (equivalent to app_launcher.py)"
    )
    app_subparsers = app_parser.add_subparsers(dest="app_command")
    list_parser = app_subparsers.add_parser("list", help="List all active Tradovate connections")
    ui_parser = app_subparsers.add_parser("ui", help="Create the UI")
    ui_parser.add_argument("--account", type=int, help="Account index (all if not specified)")
    
    trade_parser = app_subparsers.add_parser("trade", help="Execute a trade")
    trade_parser.add_argument("symbol", help="Symbol to trade (e.g., NQ)")
    trade_parser.add_argument("--account", type=int, help="Account index (all if not specified)")
    trade_parser.add_argument("--qty", type=int, default=1, help="Quantity to trade")
    trade_parser.add_argument("--action", choices=["Buy", "Sell"], default="Buy", help="Buy or Sell")
    trade_parser.add_argument("--tp", type=int, default=100, help="Take profit in ticks")
    trade_parser.add_argument("--sl", type=int, default=40, help="Stop loss in ticks")
    trade_parser.add_argument("--tick", type=float, default=0.25, help="Tick size")
    
    exit_parser = app_subparsers.add_parser("exit", help="Close positions")
    exit_parser.add_argument("symbol", help="Symbol to close positions for")
    exit_parser.add_argument("--account", type=int, help="Account index (all if not specified)")
    exit_parser.add_argument(
        "--option", 
        choices=["cancel-option-Exit-at-Mkt-Cxl", "cancel-option-Cancel-All"],
        default="cancel-option-Exit-at-Mkt-Cxl", 
        help="Exit option"
    )
    
    symbol_parser = app_subparsers.add_parser("symbol", help="Update the symbol")
    symbol_parser.add_argument("symbol", help="Symbol to update to")
    symbol_parser.add_argument("--account", type=int, help="Account index (all if not specified)")
    
    risk_parser = app_subparsers.add_parser("risk", help="Run auto risk management")
    risk_parser.add_argument("--account", type=int, help="Account index (all if not specified)")
    
    dashboard_subparser = app_subparsers.add_parser("dashboard", help="Launch the dashboard UI")
    
    # Auto-login command
    auto_login_parser = subparsers.add_parser(
        "login", 
        help="Start automatic Chrome login (equivalent to auto_login_launcher.py)"
    )
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", 
        help="Launch the web dashboard (equivalent to dashboard_launcher.py)"
    )
    
    # Webhook command
    webhook_parser = subparsers.add_parser(
        "webhook", 
        help="Start the webhook server (equivalent to pinescript_webhook_launcher.py)"
    )
    
    # Login helper command
    login_helper_parser = subparsers.add_parser(
        "login-helper", 
        help="Connect to existing Chrome instance (equivalent to login_helper_launcher.py)"
    )
    login_helper_parser.add_argument("--port", type=int, default=9223, help="Chrome debugging port")
    
    # Chrome logger command
    chrome_logger_parser = subparsers.add_parser(
        "logger", 
        help="Start Chrome logger (equivalent to chrome_logger_launcher.py)"
    )
    
    # Chrome 9223 management command
    chrome_9223_parser = subparsers.add_parser(
        "chrome",
        help="Manage Chrome instance on port 9223"
    )
    chrome_9223_parser.add_argument(
        "chrome_action", 
        choices=["start", "stop", "status", "restart"],
        help="Chrome management action"
    )
    
    # Start-all command - start Chrome, auto-login, and dashboard together
    start_all_parser = subparsers.add_parser(
        "start-all",
        help="Launch the complete stack: Chrome, auto-login, and dashboard"
    )
    start_all_parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard start (default: 15)")
    start_all_parser.add_argument("--background", action="store_true", 
                        help="Run auto-login in the background")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the requested command
    if args.command == "app":
        # Ensure Chrome 9223 is running before app commands
        if not ensure_chrome_9223_running():
            return 1
        # Pass all args to app_main, it has its own arg parsing
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return app_main()
    
    elif args.command == "login":
        return auto_login_main()
    
    elif args.command == "dashboard":
        # Ensure Chrome 9223 is running for dashboard
        if not ensure_chrome_9223_running():
            return 1
        run_flask_dashboard()
        return 0
    
    elif args.command == "webhook":
        run_webhook_server()
        return 0
    
    elif args.command == "login-helper":
        sys.argv = [sys.argv[0]] + ["--port", str(args.port)]
        return login_helper_main()
    
    elif args.command == "logger":
        return chrome_logger_main()
    
    elif args.command == "chrome":
        # Chrome management is handled externally as per CLAUDE.md rules
        print("Chrome management is handled externally as per CLAUDE.md rules")
        print("Use the external Chrome start script instead:")
        print("/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/start_chrome_debug.sh")
        
        if args.chrome_action == "status":
            try:
                import requests
                response = requests.get('http://127.0.0.1:9223/json', timeout=2)
                if response.status_code == 200:
                    tabs = response.json()
                    print(f"✅ Chrome running on port 9223 with {len(tabs)} tabs")
                    for i, tab in enumerate(tabs):
                        print(f"  Tab {i+1}: {tab.get('title', 'Unknown')} - {tab.get('url', 'Unknown')}")
                else:
                    print("⚠️  Chrome on port 9223 not responding properly")
            except Exception as e:
                print("❌ Chrome not accessible on port 9223")
            return 0
        else:
            print(f"Chrome action '{args.chrome_action}' not supported.")
            print("Please use external Chrome management script.")
            return 1
    
    elif args.command == "start-all":
        # Enhanced Chrome management - check and start required instances
        print("🚀 Starting complete trading stack...")
        
        # Step 1: Check existing Chrome instances
        running_ports, missing_ports = ensure_chrome_range_running()
        
        # Step 2: Start missing Chrome instances if needed
        if missing_ports:
            print(f"🔧 Starting {len(missing_ports)} missing Chrome instances...")
            success, started_ports, failed_ports = start_chrome_instances(missing_ports)
            
            if not success:
                if failed_ports:
                    print(f"❌ Failed to start Chrome instances on ports: {failed_ports}")
                    print("💡 Check system resources and port availability")
                return 1
            
            # Update running ports list
            running_ports.extend(started_ports)
            print(f"✅ Chrome instances ready on ports: {running_ports}")
        else:
            print(f"✅ All required Chrome instances already running on ports: {running_ports}")
        
        # Step 3: Verify at least one Chrome instance is available
        if not running_ports:
            print("❌ No Chrome instances available for trading operations")
            return 1
            
        # Handle the complete stack: auto-login + dashboard
        if args.background:
            # Start auto-login in the background
            print("Starting auto-login process in the background...")
            auto_login_process = subprocess.Popen(
                [sys.executable, f"{project_root}/main.py", "login"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            print(f"Auto-login started (PID: {auto_login_process.pid})")
            
            # Wait for Chrome instances to start and log in
            print(f"Waiting {args.wait} seconds for login to complete...")
            time.sleep(args.wait)
            
            # Start the dashboard in the foreground
            run_flask_dashboard()
            return 0
        else:
            # Start auto-login in a separate thread
            auto_login_thread = threading.Thread(target=auto_login_main)
            auto_login_thread.daemon = True
            auto_login_thread.start()
            
            # Wait for Chrome instances to start and log in
            print(f"Waiting {args.wait} seconds for login to complete...")
            time.sleep(args.wait)
            
            # Start dashboard in the main thread
            run_flask_dashboard()
            return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())