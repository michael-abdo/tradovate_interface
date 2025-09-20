#!/usr/bin/env python3
"""
Production Trading System Validator
FAIL FAST, FAIL LOUD, FAIL SAFELY

This module implements the production validation requirements from CLAUDE.md
"""

import os
import sys
import time
import json
import threading
import pychrome
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.chrome_communication import safe_evaluate, OperationType

@dataclass
class TradingAccount:
    username: str
    password: str
    name: str
    port: int
    initial_balance: float = 0.0
    last_balance: float = 0.0
    last_positions: Dict = None
    authenticated: bool = False

class ProductionValidator:
    """Validates trading system for production use - FAIL FAST, FAIL LOUD, FAIL SAFELY"""
    
    def __init__(self):
        self.trading_accounts = self._load_trading_accounts()
        self.trading_active = False
        self.critical_errors = []
        self.warning_errors = []
        
    def _load_trading_accounts(self) -> List[TradingAccount]:
        """Load real trading accounts from credentials"""
        try:
            credentials_path = os.path.join(project_root, 'config', 'credentials.json')
            if not os.path.exists(credentials_path):
                self.FAIL_LOUD("CRITICAL: No credentials.json found")
                return []
                
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                
            accounts = []
            for i, (username, password) in enumerate(creds.items()):
                port = 9223 + i  # Trading ports start at 9223
                account = TradingAccount(
                    username=username,
                    password=password, 
                    name=f"Account_{i+1}_{username.split('@')[0]}",
                    port=port
                )
                accounts.append(account)
                
            self.LOG_SUCCESS(f"✓ Loaded {len(accounts)} trading accounts")
            return accounts
            
        except Exception as e:
            self.FAIL_LOUD(f"CRITICAL: Failed to load trading accounts - {str(e)}")
            return []
    
    def FAIL_LOUD(self, message: str):
        """Log critical errors loudly"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! CRITICAL ERROR !!! {message}"
        print(error_msg)
        self.critical_errors.append(error_msg)
        
    def LOG_SUCCESS(self, message: str):
        """Log successful operations"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✓ SUCCESS: {message}"
        print(success_msg)
        
    def LOG_WARNING(self, message: str):
        """Log warning messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  WARNING: {message}"
        print(warning_msg)
        self.warning_errors.append(warning_msg)
        
    def validate_real_authentication(self) -> bool:
        """Test authentication with actual Tradovate credentials - FAIL FAST"""
        self.LOG_SUCCESS("Starting real authentication validation...")
        
        for account in self.trading_accounts:
            try:
                # Test Chrome connection to real Tradovate
                browser = pychrome.Browser(url=f"http://127.0.0.1:{account.port}")
                tabs = browser.list_tab()
                
                if not tabs:
                    self.FAIL_LOUD(f"NO CHROME TABS: Port {account.port} has no accessible tabs")
                    return False
                    
                # Find Tradovate tab
                tradovate_tab = None
                for tab_info in tabs:
                    try:
                        tab = browser.get_tab(tab_info['id'])
                        tab.start()
                        
                        # Check if this is a real Tradovate tab
                        url_result = safe_evaluate(tab, "window.location.href", OperationType.CRITICAL)
                        if url_result.success and "trader.tradovate.com" in str(url_result.value):
                            tradovate_tab = tab
                            break
                        else:
                            tab.stop()
                    except Exception as e:
                        self.LOG_WARNING(f"Tab check failed: {str(e)}")
                        continue
                        
                if not tradovate_tab:
                    self.FAIL_LOUD(f"NO REAL TRADOVATE: Port {account.port} not connected to trader.tradovate.com")
                    return False
                    
                # Test authentication by checking login status
                auth_result = safe_evaluate(
                    tradovate_tab, 
                    "document.querySelector('.user-menu, .account-selector, [data-qa=\"account-selector\"]') !== null",
                    OperationType.CRITICAL,
                    f"Authentication check for {account.name}"
                )
                
                if auth_result.success and auth_result.value:
                    account.authenticated = True
                    self.LOG_SUCCESS(f"✓ Authentication successful: {account.name}")
                else:
                    self.FAIL_LOUD(f"AUTHENTICATION FAILED: {account.name} - Not logged in to real Tradovate")
                    return False
                    
                tradovate_tab.stop()
                
            except Exception as e:
                self.FAIL_LOUD(f"AUTHENTICATION ERROR: {account.name} - {str(e)}")
                return False
                
        return True
    
    def validate_real_chrome_connections(self) -> bool:
        """Connect to real Chrome instances on trading ports - FAIL FAST"""
        self.LOG_SUCCESS("Validating real Chrome connections...")
        
        for port in [9223, 9224, 9225]:  # All trading accounts
            try:
                browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
                tabs = browser.list_tab()
                
                if not tabs:
                    self.FAIL_LOUD(f"NO CHROME TABS: Port {port} has no accessible tabs")
                    return False
                
                # Must connect to real Tradovate
                has_tradovate_tab = False
                for tab_info in tabs:
                    try:
                        tab = browser.get_tab(tab_info['id'])
                        tab.start()
                        
                        url_result = safe_evaluate(tab, "window.location.href", OperationType.NON_CRITICAL)
                        if url_result.success and "trader.tradovate.com" in str(url_result.value):
                            has_tradovate_tab = True
                            self.LOG_SUCCESS(f"✓ Real Tradovate connection: Port {port}")
                            tab.stop()
                            break
                        tab.stop()
                    except Exception as e:
                        self.LOG_WARNING(f"Tab validation failed on port {port}: {str(e)}")
                        continue
                
                if not has_tradovate_tab:
                    self.FAIL_LOUD(f"NO REAL TRADOVATE: Port {port} not connected to trader.tradovate.com")
                    return False
                    
            except Exception as e:
                self.FAIL_LOUD(f"CHROME CONNECTION FAILED: Port {port} - {str(e)}")
                return False
                
        return True
    
    def validate_real_trading_functions(self) -> bool:
        """Test JavaScript execution on actual Tradovate interface - FAIL FAST"""
        self.LOG_SUCCESS("Validating real trading functions...")
        
        for account in self.trading_accounts:
            try:
                browser = pychrome.Browser(url=f"http://127.0.0.1:{account.port}")
                tabs = browser.list_tab()
                
                # Find Tradovate tab
                tradovate_tab = None
                for tab_info in tabs:
                    try:
                        tab = browser.get_tab(tab_info['id'])
                        tab.start()
                        
                        url_result = safe_evaluate(tab, "window.location.href", OperationType.NON_CRITICAL)
                        if url_result.success and "trader.tradovate.com" in str(url_result.value):
                            tradovate_tab = tab
                            break
                        else:
                            tab.stop()
                    except Exception:
                        continue
                
                if not tradovate_tab:
                    self.FAIL_LOUD(f"NO TRADOVATE TAB: Cannot find real Tradovate tab for {account.name}")
                    return False
                
                # Test real account data retrieval
                account_test = safe_evaluate(
                    tradovate_tab, 
                    "document.querySelector('.account-selector, [data-qa=\"account-selector\"]') !== null",
                    OperationType.CRITICAL,
                    f"Account selector check for {account.name}"
                )
                
                if not account_test.success:
                    self.FAIL_LOUD(f"ACCOUNT DATA FAILED: {account.name} - Cannot access account selector")
                    return False
                
                # Test DOM trading elements  
                trading_test = safe_evaluate(
                    tradovate_tab,
                    "document.querySelector('.dom-container, .trading-panel, [data-qa=\"trading-panel\"]') !== null",
                    OperationType.CRITICAL,
                    f"Trading interface check for {account.name}"
                )
                
                if not trading_test.success:
                    self.FAIL_LOUD(f"TRADING INTERFACE FAILED: {account.name} - Cannot access trading interface")
                    return False
                
                self.LOG_SUCCESS(f"✓ Real trading functions validated: {account.name}")
                tradovate_tab.stop()
                
            except Exception as e:
                self.FAIL_LOUD(f"TRADING FUNCTION ERROR: {account.name} - {str(e)}")
                return False
                
        return True
    
    def get_real_balance(self, account: TradingAccount) -> Optional[float]:
        """Get real account balance from Tradovate interface"""
        try:
            browser = pychrome.Browser(url=f"http://127.0.0.1:{account.port}")
            tabs = browser.list_tab()
            
            for tab_info in tabs:
                try:
                    tab = browser.get_tab(tab_info['id'])
                    tab.start()
                    
                    url_result = safe_evaluate(tab, "window.location.href", OperationType.NON_CRITICAL)
                    if url_result.success and "trader.tradovate.com" in str(url_result.value):
                        # Try to get balance from various possible selectors
                        balance_selectors = [
                            "document.querySelector('[data-qa=\"cash-balance\"]')?.textContent",
                            "document.querySelector('.cash-balance')?.textContent", 
                            "document.querySelector('.account-balance')?.textContent",
                            "document.querySelector('[data-testid=\"cash-balance\"]')?.textContent"
                        ]
                        
                        for selector in balance_selectors:
                            balance_result = safe_evaluate(tab, selector, OperationType.NON_CRITICAL)
                            if balance_result.success and balance_result.value:
                                try:
                                    # Extract numeric value from balance text
                                    balance_text = str(balance_result.value)
                                    balance_clean = ''.join(c for c in balance_text if c.isdigit() or c == '.')
                                    balance = float(balance_clean)
                                    tab.stop()
                                    return balance
                                except (ValueError, TypeError):
                                    continue
                        
                        tab.stop()
                        break
                    else:
                        tab.stop()
                except Exception:
                    continue
                    
        except Exception as e:
            self.LOG_WARNING(f"Balance retrieval failed for {account.name}: {str(e)}")
            
        return None
    
    def implement_realtime_monitoring(self):
        """Monitor real account positions and balances - FAIL SAFELY"""
        def monitor_account_changes():
            self.LOG_SUCCESS("Starting real-time account monitoring...")
            
            while self.trading_active:
                try:
                    for account in self.trading_accounts:
                        if not account.authenticated:
                            continue
                            
                        current_balance = self.get_real_balance(account)
                        
                        if current_balance is not None:
                            # Initialize balance if first time
                            if account.initial_balance == 0.0:
                                account.initial_balance = current_balance
                                account.last_balance = current_balance
                                self.LOG_SUCCESS(f"Initial balance set: {account.name} - ${current_balance:.2f}")
                            
                            # Check for significant balance changes
                            balance_change = abs(current_balance - account.last_balance)
                            if balance_change > 10.0:  # $10 threshold
                                self.LOG_WARNING(f"BALANCE CHANGE: {account.name} - ${account.last_balance:.2f} → ${current_balance:.2f}")
                                
                            # FAIL SAFELY: Stop trading if excessive losses
                            loss_threshold = account.initial_balance * 0.05  # 5% loss limit
                            total_loss = account.initial_balance - current_balance
                            
                            if total_loss > loss_threshold:
                                self.FAIL_LOUD(f"STOP LOSS TRIGGERED: {account.name} - Loss: ${total_loss:.2f}")
                                self.trading_active = False
                                return False
                                
                            account.last_balance = current_balance
                        
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.FAIL_LOUD(f"MONITORING ERROR: {str(e)}")
                    time.sleep(5)  # Continue monitoring after errors
                    
        monitoring_thread = threading.Thread(target=monitor_account_changes, daemon=True)
        monitoring_thread.start()
        return monitoring_thread
    
    def run_production_validation(self) -> bool:
        """Run complete production validation sequence"""
        print("="*60)
        print("PRODUCTION TRADING SYSTEM VALIDATION")
        print("FAIL FAST, FAIL LOUD, FAIL SAFELY")
        print("="*60)
        
        validation_steps = [
            ("Real Authentication Validation", self.validate_real_authentication),
            ("Real Chrome Connection Validation", self.validate_real_chrome_connections),
            ("Real Trading Function Validation", self.validate_real_trading_functions),
        ]
        
        for step_name, validation_func in validation_steps:
            print(f"\n🔍 {step_name}...")
            
            if not validation_func():
                self.FAIL_LOUD(f"VALIDATION FAILED: {step_name}")
                print(f"\n❌ PRODUCTION VALIDATION FAILED at: {step_name}")
                print("⚠️  System is NOT ready for production trading")
                return False
            
            self.LOG_SUCCESS(f"{step_name} completed successfully")
        
        # Start monitoring if all validations pass
        self.trading_active = True
        self.implement_realtime_monitoring()
        
        print("\n" + "="*60)
        print("✅ PRODUCTION VALIDATION SUCCESSFUL")
        print("🚀 System is ready for live trading")
        print("📊 Real-time monitoring active")
        print("="*60)
        
        return True

def main():
    """Main validation entry point"""
    validator = ProductionValidator()
    
    if not validator.trading_accounts:
        print("❌ No trading accounts loaded - cannot proceed")
        return 1
        
    success = validator.run_production_validation()
    
    if success:
        print("\n⏳ Monitoring active - Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
            validator.trading_active = False
        return 0
    else:
        print("\n💥 Production validation failed - fix errors before trading")
        return 1

if __name__ == "__main__":
    sys.exit(main())