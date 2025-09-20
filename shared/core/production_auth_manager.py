#!/usr/bin/env python3
"""
Production Authentication Manager
FAIL FAST, FAIL LOUD, FAIL SAFELY

Real Tradovate account authentication with session monitoring
"""

import os
import sys
import time
import json
import pychrome
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.chrome_communication import safe_evaluate, OperationType

@dataclass
class AuthSession:
    account_name: str
    username: str
    port: int
    authenticated: bool = False
    session_start: Optional[datetime] = None
    last_validated: Optional[datetime] = None
    login_attempts: int = 0
    max_login_attempts: int = 3
    session_timeout_minutes: int = 240  # 4 hours

class ProductionAuthManager:
    """Manages real Tradovate authentication for production trading"""
    
    def __init__(self):
        self.auth_sessions: Dict[str, AuthSession] = {}
        self.monitoring_active = False
        self.validation_interval = 60  # Check auth every 60 seconds
        
    def FAIL_LOUD(self, message: str):
        """Critical error logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! AUTH CRITICAL !!! {message}"
        print(error_msg)
        self._log_to_file("CRITICAL", error_msg)
        
    def LOG_SUCCESS(self, message: str):
        """Success logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✅ AUTH SUCCESS: {message}"
        print(success_msg)
        self._log_to_file("SUCCESS", success_msg)
        
    def LOG_WARNING(self, message: str):
        """Warning logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  AUTH WARNING: {message}"
        print(warning_msg)
        self._log_to_file("WARNING", warning_msg)
        
    def _log_to_file(self, level: str, message: str):
        """Log messages to file"""
        log_dir = os.path.join(project_root, "logs", "auth")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"auth_{today}.log")
        
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
    
    def load_trading_accounts(self) -> bool:
        """Load trading accounts from credentials - FAIL FAST"""
        try:
            credentials_path = os.path.join(project_root, 'config', 'credentials.json')
            if not os.path.exists(credentials_path):
                self.FAIL_LOUD("No credentials.json found")
                return False
                
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                
            self.auth_sessions.clear()
            
            for i, (username, password) in enumerate(creds.items()):
                port = 9222  # CLAUDE.md Rule: NEVER START CHROME - Use existing port 9222
                account_name = f"Account_{i+1}_{username.split('@')[0]}"
                
                session = AuthSession(
                    account_name=account_name,
                    username=username,
                    port=port
                )
                
                self.auth_sessions[account_name] = session
                
            self.LOG_SUCCESS(f"Loaded {len(self.auth_sessions)} trading accounts")
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Failed to load trading accounts: {str(e)}")
            return False
    
    def validate_real_authentication(self, account_name: str) -> bool:
        """Validate authentication with real Tradovate - FAIL FAST"""
        
        if account_name not in self.auth_sessions:
            self.FAIL_LOUD(f"Account not found: {account_name}")
            return False
            
        session = self.auth_sessions[account_name]
        
        try:
            # Connect to Chrome instance
            browser = pychrome.Browser(url=f"http://127.0.0.1:{session.port}")
            tabs = browser.list_tab()
            
            if not tabs:
                self.FAIL_LOUD(f"NO CHROME TABS: {account_name} port {session.port}")
                return False
                
            # Find Tradovate tab
            tradovate_tab = None
            for tab in tabs:
                try:
                    tab.start()
                    
                    # Verify real Tradovate connection
                    url_result = safe_evaluate(tab, "window.location.href", OperationType.CRITICAL)
                    if url_result.success and "trader.tradovate.com" in str(url_result.value):
                        tradovate_tab = tab
                        break
                    else:
                        tab.stop()
                        
                except Exception as e:
                    self.LOG_WARNING(f"Tab check failed for {account_name}: {str(e)}")
                    try:
                        tab.stop()
                    except:
                        pass
                    continue
            
            if not tradovate_tab:
                self.FAIL_LOUD(f"NO REAL TRADOVATE: {account_name} not connected to trader.tradovate.com")
                session.authenticated = False
                return False
            
            # Check authentication status using multiple methods
            auth_checks = [
                # Method 1: Look for user menu or account selector
                """
                const userMenu = document.querySelector('.user-menu, .account-selector, [data-qa="account-selector"]');
                const userInfo = document.querySelector('.user-info, .account-info, [data-qa="user-info"]');
                const logoutButton = document.querySelector('[data-qa="logout"], .logout-button, .sign-out');
                return !!(userMenu || userInfo || logoutButton);
                """,
                
                # Method 2: Check for trading interface elements (only available when logged in)
                """
                const tradingPanel = document.querySelector('.trading-panel, .dom-container, [data-qa="trading-panel"]');
                const orderEntry = document.querySelector('.order-entry, [data-qa="order-entry"]');
                return !!(tradingPanel || orderEntry);
                """,
                
                # Method 3: Check URL for login page (if on login page, not authenticated)
                """
                const currentUrl = window.location.href;
                const isLoginPage = currentUrl.includes('/login') || currentUrl.includes('/signin') || 
                                  document.querySelector('.login-form, .signin-form, [data-qa="login-form"]');
                return !isLoginPage;
                """,
                
                # Method 4: Check for account balance or position elements
                """
                const balance = document.querySelector('.cash-balance, .account-balance, [data-qa="cash-balance"]');
                const positions = document.querySelector('.positions-table, .portfolio, [data-qa="positions"]');
                return !!(balance || positions);
                """
            ]
            
            authenticated = False
            
            for i, auth_check in enumerate(auth_checks):
                auth_result = safe_evaluate(
                    tradovate_tab,
                    auth_check,
                    OperationType.CRITICAL,
                    f"Auth check {i+1} for {account_name}"
                )
                
                if auth_result.success and auth_result.value:
                    authenticated = True
                    self.LOG_SUCCESS(f"✅ Authentication confirmed (method {i+1}): {account_name}")
                    break
                    
            tradovate_tab.stop()
            
            # Update session status
            session.authenticated = authenticated
            session.last_validated = datetime.now()
            
            if authenticated:
                if session.session_start is None:
                    session.session_start = datetime.now()
                    
                self.LOG_SUCCESS(f"✅ Authentication validated: {account_name}")
                return True
            else:
                self.FAIL_LOUD(f"AUTHENTICATION FAILED: {account_name} - Not logged in to real Tradovate")
                return False
                
        except Exception as e:
            session.authenticated = False
            self.FAIL_LOUD(f"AUTH VALIDATION ERROR: {account_name} - {str(e)}")
            return False
    
    def attempt_real_login(self, account_name: str, password: str) -> bool:
        """Attempt to log into real Tradovate account - FAIL SAFELY"""
        
        if account_name not in self.auth_sessions:
            self.FAIL_LOUD(f"Account not found: {account_name}")
            return False
            
        session = self.auth_sessions[account_name]
        
        # FAIL SAFELY: Check login attempt limits
        if session.login_attempts >= session.max_login_attempts:
            self.FAIL_LOUD(f"MAX LOGIN ATTEMPTS EXCEEDED: {account_name} - {session.login_attempts} attempts")
            return False
        
        session.login_attempts += 1
        
        try:
            browser = pychrome.Browser(url=f"http://127.0.0.1:{session.port}")
            tabs = browser.list_tab()
            
            if not tabs:
                self.FAIL_LOUD(f"NO CHROME TABS for login: {account_name}")
                return False
                
            # Find Tradovate tab
            tradovate_tab = None
            for tab in tabs:
                try:
                    tab.start()
                    
                    url_result = safe_evaluate(tab, "window.location.href", OperationType.NON_CRITICAL)
                    if url_result.success and "trader.tradovate.com" in str(url_result.value):
                        tradovate_tab = tab
                        break
                    else:
                        tab.stop()
                        
                except Exception:
                    try:
                        tab.stop()
                    except:
                        pass
                    continue
            
            if not tradovate_tab:
                self.FAIL_LOUD(f"NO TRADOVATE TAB for login: {account_name}")
                return False
            
            # Navigate to login page if needed
            login_nav_result = safe_evaluate(
                tradovate_tab,
                """
                // Check if already on login page or need to navigate
                if (window.location.href.includes('/login') || 
                    document.querySelector('.login-form, .signin-form, [data-qa="login-form"]')) {
                    return { already_on_login: true };
                } else {
                    // Look for login/signin link
                    const loginLink = document.querySelector('a[href*="login"], a[href*="signin"], [data-qa="login-link"]');
                    if (loginLink) {
                        loginLink.click();
                        return { navigated_to_login: true };
                    }
                    return { login_link_not_found: true };
                }
                """,
                OperationType.CRITICAL,
                f"Navigate to login for {account_name}"
            )
            
            if not login_nav_result.success:
                self.FAIL_LOUD(f"FAILED TO NAVIGATE TO LOGIN: {account_name}")
                tradovate_tab.stop()
                return False
            
            # Wait for login page to load
            time.sleep(3)
            
            # Attempt login
            login_result = safe_evaluate(
                tradovate_tab,
                f"""
                // Real Tradovate login attempt
                try {{
                    // Find username/email field
                    const usernameField = document.querySelector('input[type="email"], input[name="username"], input[name="email"], [data-qa="username"], [data-qa="email"]');
                    if (!usernameField) {{
                        return {{ error: "Username field not found" }};
                    }}
                    
                    // Find password field
                    const passwordField = document.querySelector('input[type="password"], input[name="password"], [data-qa="password"]');
                    if (!passwordField) {{
                        return {{ error: "Password field not found" }};
                    }}
                    
                    // Fill in credentials
                    usernameField.value = '{session.username}';
                    usernameField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    passwordField.value = '{password}';
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    // Find and click login button
                    const loginButton = document.querySelector('button[type="submit"], input[type="submit"], .login-button, [data-qa="login-button"]');
                    if (!loginButton) {{
                        return {{ error: "Login button not found" }};
                    }}
                    
                    // Click login button
                    loginButton.click();
                    
                    return {{ login_attempted: true }};
                    
                }} catch (error) {{
                    return {{ error: error.message }};
                }}
                """,
                OperationType.CRITICAL,
                f"Login attempt for {account_name}"
            )
            
            tradovate_tab.stop()
            
            if login_result.success and login_result.value and not login_result.value.get('error'):
                self.LOG_SUCCESS(f"✅ Login attempted: {account_name}")
                
                # Wait for login to process
                time.sleep(5)
                
                # Validate authentication after login attempt
                if self.validate_real_authentication(account_name):
                    session.login_attempts = 0  # Reset on success
                    return True
                else:
                    self.LOG_WARNING(f"Login attempt failed - authentication not confirmed: {account_name}")
                    return False
            else:
                error_msg = login_result.value.get('error', 'Unknown error') if login_result.value else login_result.error
                self.FAIL_LOUD(f"LOGIN ATTEMPT FAILED: {account_name} - {error_msg}")
                return False
                
        except Exception as e:
            self.FAIL_LOUD(f"LOGIN ERROR: {account_name} - {str(e)}")
            return False
    
    def validate_all_authentications(self) -> bool:
        """Validate authentication for all accounts - FAIL FAST"""
        
        print("="*60)
        print("🔐 VALIDATING REAL TRADOVATE AUTHENTICATION")
        print("="*60)
        
        if not self.auth_sessions:
            if not self.load_trading_accounts():
                return False
        
        all_authenticated = True
        
        for account_name, session in self.auth_sessions.items():
            print(f"\n🔍 Validating authentication: {account_name}...")
            
            if self.validate_real_authentication(account_name):
                self.LOG_SUCCESS(f"✅ Authentication valid: {account_name}")
            else:
                self.LOG_WARNING(f"⚠️  Authentication required: {account_name}")
                all_authenticated = False
        
        if all_authenticated:
            print("\n" + "="*60)
            print("✅ ALL ACCOUNTS AUTHENTICATED")
            print("🚀 Ready for production trading")
            print("="*60)
            
            # Start continuous monitoring
            self._start_auth_monitoring()
            
        else:
            print("\n" + "="*60)
            print("❌ AUTHENTICATION INCOMPLETE")
            print("⚠️  Manual login required for some accounts")
            print("="*60)
        
        return all_authenticated
    
    def _start_auth_monitoring(self):
        """Start continuous authentication monitoring"""
        
        def monitor_auth():
            self.monitoring_active = True
            self.LOG_SUCCESS("Started authentication monitoring")
            
            while self.monitoring_active:
                try:
                    for account_name, session in self.auth_sessions.items():
                        # Check if session has timed out
                        if (session.last_validated and 
                            datetime.now() - session.last_validated > timedelta(minutes=session.session_timeout_minutes)):
                            
                            self.LOG_WARNING(f"SESSION TIMEOUT: {account_name}")
                            session.authenticated = False
                            
                        # Re-validate authentication
                        if not self.validate_real_authentication(account_name):
                            self.LOG_WARNING(f"AUTH LOST: {account_name} - Manual re-login required")
                            
                    time.sleep(self.validation_interval)
                    
                except Exception as e:
                    self.LOG_WARNING(f"Auth monitoring error: {str(e)}")
                    time.sleep(30)  # Wait before retrying
        
        auth_thread = threading.Thread(target=monitor_auth, daemon=True)
        auth_thread.start()
    
    def get_auth_status(self) -> Dict[str, any]:
        """Get authentication status for all accounts"""
        status = {
            "total_accounts": len(self.auth_sessions),
            "authenticated_accounts": len([s for s in self.auth_sessions.values() if s.authenticated]),
            "monitoring_active": self.monitoring_active,
            "accounts": {}
        }
        
        for account_name, session in self.auth_sessions.items():
            status["accounts"][account_name] = {
                "authenticated": session.authenticated,
                "username": session.username,
                "port": session.port,
                "session_start": session.session_start.isoformat() if session.session_start else None,
                "last_validated": session.last_validated.isoformat() if session.last_validated else None,
                "login_attempts": session.login_attempts
            }
            
        return status
    
    def stop_monitoring(self):
        """Stop authentication monitoring"""
        self.monitoring_active = False
        self.LOG_SUCCESS("Authentication monitoring stopped")

def main():
    """Main authentication manager entry point"""
    auth_manager = ProductionAuthManager()
    
    try:
        if not auth_manager.validate_all_authentications():
            print("❌ Authentication validation failed")
            print("💡 Ensure you're logged into trader.tradovate.com in all Chrome instances")
            return 1
            
        print("\n⏳ Authentication monitoring active - Press Ctrl+C to stop")
        
        while True:
            status = auth_manager.get_auth_status()
            print(f"\r🔐 Auth Status: {status['authenticated_accounts']}/{status['total_accounts']} accounts authenticated", end="", flush=True)
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping authentication monitoring...")
        auth_manager.stop_monitoring()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())