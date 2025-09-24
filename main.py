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
        # Pass all args to app_main, it has its own arg parsing
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return app_main()
    
    elif args.command == "login":
        return auto_login_main()
    
    elif args.command == "dashboard":
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
    
    elif args.command == "start-all":
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