#!/usr/bin/env python3
"""
Production Real-Time Position and Balance Monitor
FAIL FAST, FAIL LOUD, FAIL SAFELY

Real-time monitoring of actual account positions, balances, and trading activity
"""

import os
import sys
import time
import json
import pychrome
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add project root for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.chrome_communication import safe_evaluate, OperationType

@dataclass
class Position:
    symbol: str
    quantity: int
    side: str  # "Long" or "Short"
    entry_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: str

@dataclass
class AccountSnapshot:
    account_name: str
    cash_balance: float
    buying_power: float
    total_pnl: float
    day_pnl: float
    positions: List[Position]
    last_updated: str

class ProductionMonitor:
    """Real-time monitoring of production trading accounts"""
    
    def __init__(self):
        self.account_snapshots: Dict[str, AccountSnapshot] = {}
        self.monitoring_active = False
        self.monitor_interval = 5  # seconds
        self.alert_thresholds = {
            'max_daily_loss': 500.0,      # $500 max daily loss
            'max_position_loss': 200.0,   # $200 max single position loss
            'balance_change_alert': 50.0  # Alert on $50+ balance changes
        }
        self.trading_accounts = []
        
    def FAIL_LOUD(self, message: str):
        """Critical error logging with alerts"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! MONITOR CRITICAL !!! {message}"
        print(error_msg)
        self._log_to_file("CRITICAL", error_msg)
        self._send_alert("CRITICAL", message)
        
    def LOG_SUCCESS(self, message: str):
        """Success logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✅ MONITOR SUCCESS: {message}"
        print(success_msg)
        self._log_to_file("SUCCESS", success_msg)
        
    def LOG_WARNING(self, message: str):
        """Warning logging with alerts"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  MONITOR WARNING: {message}"
        print(warning_msg)
        self._log_to_file("WARNING", warning_msg)
        self._send_alert("WARNING", message)
        
    def _log_to_file(self, level: str, message: str):
        """Log messages to file"""
        log_dir = os.path.join(project_root, "logs", "monitor")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"monitor_{today}.log")
        
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
    
    def _send_alert(self, level: str, message: str):
        """Send alert (placeholder for notification system)"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        alert_dir = os.path.join(project_root, "logs", "alerts")
        os.makedirs(alert_dir, exist_ok=True)
        
        alert_file = os.path.join(alert_dir, f"alert_{int(time.time())}.json")
        with open(alert_file, "w") as f:
            json.dump(alert_data, f, indent=2)
    
    def load_trading_accounts(self) -> bool:
        """Load trading accounts from credentials - FAIL FAST"""
        try:
            credentials_path = os.path.join(project_root, 'config', 'credentials.json')
            if not os.path.exists(credentials_path):
                self.FAIL_LOUD("No credentials.json found")
                return False
                
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                
            self.trading_accounts.clear()
            
            for i, (username, password) in enumerate(creds.items()):
                port = 9222  # CLAUDE.md Rule: NEVER START CHROME - Use existing port 9222
                account_name = f"Account_{i+1}_{username.split('@')[0]}"
                
                self.trading_accounts.append({
                    'name': account_name,
                    'username': username,
                    'port': port
                })
                
            self.LOG_SUCCESS(f"Loaded {len(self.trading_accounts)} trading accounts for monitoring")
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Failed to load trading accounts: {str(e)}")
            return False
    
    def get_real_account_data(self, account: Dict[str, Any]) -> Optional[AccountSnapshot]:
        """Get real account data from Tradovate interface - FAIL FAST"""
        
        try:
            browser = pychrome.Browser(url=f"http://127.0.0.1:{account['port']}")
            tabs = browser.list_tab()
            
            if not tabs:
                self.LOG_WARNING(f"No Chrome tabs for {account['name']}")
                return None
                
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
                self.LOG_WARNING(f"No Tradovate tab found for {account['name']}")
                return None
            
            # Extract account data using multiple methods
            account_data_script = """
            (function() {
                try {
                    const accountData = {
                        cash_balance: null,
                        buying_power: null,
                        total_pnl: null,
                        day_pnl: null,
                        positions: []
                    };
                    
                    // Method 1: Look for account summary elements
                    const balanceElements = [
                        'cash-balance', 'account-balance', 'balance-value',
                        '[data-qa="cash-balance"]', '[data-qa="account-balance"]',
                        '.cash-balance', '.account-balance'
                    ];
                    
                    for (const selector of balanceElements) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent) {
                            const text = element.textContent.replace(/[^0-9.-]/g, '');
                            if (text && !isNaN(parseFloat(text))) {
                                accountData.cash_balance = parseFloat(text);
                                break;
                            }
                        }
                    }
                    
                    // Method 2: Look for P&L elements
                    const pnlElements = [
                        'unrealized-pnl', 'total-pnl', 'pnl-value',
                        '[data-qa="unrealized-pnl"]', '[data-qa="total-pnl"]',
                        '.unrealized-pnl', '.total-pnl'
                    ];
                    
                    for (const selector of pnlElements) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent) {
                            const text = element.textContent.replace(/[^0-9.-]/g, '');
                            if (text && !isNaN(parseFloat(text))) {
                                accountData.total_pnl = parseFloat(text);
                                break;
                            }
                        }
                    }
                    
                    // Method 3: Extract positions from positions table
                    const positionTables = document.querySelectorAll(
                        '.positions-table tbody tr, .portfolio-table tbody tr, [data-qa="positions-table"] tbody tr'
                    );
                    
                    positionTables.forEach(row => {
                        try {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 4) {
                                const symbol = cells[0]?.textContent?.trim();
                                const quantity = cells[1]?.textContent?.trim();
                                const price = cells[2]?.textContent?.trim();
                                const pnl = cells[3]?.textContent?.trim();
                                
                                if (symbol && quantity && !isNaN(parseInt(quantity))) {
                                    accountData.positions.push({
                                        symbol: symbol,
                                        quantity: parseInt(quantity.replace(/[^0-9-]/g, '')),
                                        entry_price: price ? parseFloat(price.replace(/[^0-9.-]/g, '')) : 0,
                                        unrealized_pnl: pnl ? parseFloat(pnl.replace(/[^0-9.-]/g, '')) : 0
                                    });
                                }
                            }
                        } catch (e) {
                            // Skip invalid rows
                        }
                    });
                    
                    // Method 4: Try to get data from DOM or account selector
                    const accountSelector = document.querySelector('.account-selector, [data-qa="account-selector"]');
                    if (accountSelector) {
                        const balanceText = accountSelector.textContent;
                        const balanceMatch = balanceText.match(/\\$?([0-9,]+\\.?[0-9]*)/);
                        if (balanceMatch && !accountData.cash_balance) {
                            accountData.cash_balance = parseFloat(balanceMatch[1].replace(/,/g, ''));
                        }
                    }
                    
                    return {
                        success: true,
                        data: accountData
                    };
                    
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            })();
            """
            
            data_result = safe_evaluate(
                tradovate_tab,
                account_data_script,
                OperationType.CRITICAL,
                f"Get account data for {account['name']}"
            )
            
            tradovate_tab.stop()
            
            if data_result.success and data_result.value and data_result.value.get('success'):
                raw_data = data_result.value['data']
                
                # Convert positions
                positions = []
                for pos_data in raw_data.get('positions', []):
                    position = Position(
                        symbol=pos_data['symbol'],
                        quantity=pos_data['quantity'],
                        side="Long" if pos_data['quantity'] > 0 else "Short",
                        entry_price=pos_data['entry_price'],
                        current_price=pos_data['entry_price'],  # Would need market data for current
                        unrealized_pnl=pos_data['unrealized_pnl'],
                        timestamp=datetime.now().isoformat()
                    )
                    positions.append(position)
                
                # Create account snapshot
                snapshot = AccountSnapshot(
                    account_name=account['name'],
                    cash_balance=raw_data.get('cash_balance', 0.0) or 0.0,
                    buying_power=raw_data.get('buying_power', 0.0) or 0.0,
                    total_pnl=raw_data.get('total_pnl', 0.0) or 0.0,
                    day_pnl=raw_data.get('day_pnl', 0.0) or 0.0,
                    positions=positions,
                    last_updated=datetime.now().isoformat()
                )
                
                return snapshot
            else:
                error_msg = data_result.value.get('error', 'Unknown error') if data_result.value else data_result.error
                self.LOG_WARNING(f"Failed to get account data for {account['name']}: {error_msg}")
                return None
                
        except Exception as e:
            self.LOG_WARNING(f"Account data retrieval error for {account['name']}: {str(e)}")
            return None
    
    def check_account_alerts(self, current_snapshot: AccountSnapshot, previous_snapshot: Optional[AccountSnapshot]):
        """Check for alert conditions - FAIL LOUD on critical issues"""
        
        if not previous_snapshot:
            return  # First snapshot, no comparison possible
            
        # Check for significant balance changes
        balance_change = current_snapshot.cash_balance - previous_snapshot.cash_balance
        if abs(balance_change) >= self.alert_thresholds['balance_change_alert']:
            if balance_change > 0:
                self.LOG_SUCCESS(f"💰 BALANCE INCREASE: {current_snapshot.account_name} +${balance_change:.2f}")
            else:
                self.LOG_WARNING(f"💸 BALANCE DECREASE: {current_snapshot.account_name} -${abs(balance_change):.2f}")
        
        # Check for daily loss limits
        if current_snapshot.day_pnl < -self.alert_thresholds['max_daily_loss']:
            self.FAIL_LOUD(f"🚨 DAILY LOSS LIMIT EXCEEDED: {current_snapshot.account_name} - Day P&L: ${current_snapshot.day_pnl:.2f}")
        
        # Check individual position losses
        for position in current_snapshot.positions:
            if position.unrealized_pnl < -self.alert_thresholds['max_position_loss']:
                self.LOG_WARNING(f"⚠️  LARGE POSITION LOSS: {current_snapshot.account_name} - {position.symbol}: ${position.unrealized_pnl:.2f}")
        
        # Check for new positions
        current_symbols = set(pos.symbol for pos in current_snapshot.positions)
        previous_symbols = set(pos.symbol for pos in previous_snapshot.positions)
        
        new_positions = current_symbols - previous_symbols
        closed_positions = previous_symbols - current_symbols
        
        for symbol in new_positions:
            position = next(pos for pos in current_snapshot.positions if pos.symbol == symbol)
            self.LOG_SUCCESS(f"📈 NEW POSITION: {current_snapshot.account_name} - {position.side} {position.quantity} {symbol}")
        
        for symbol in closed_positions:
            self.LOG_SUCCESS(f"📉 POSITION CLOSED: {current_snapshot.account_name} - {symbol}")
    
    def start_realtime_monitoring(self) -> bool:
        """Start real-time account monitoring - FAIL FAST"""
        
        print("="*60)
        print("📊 STARTING PRODUCTION ACCOUNT MONITORING")
        print("="*60)
        
        if not self.load_trading_accounts():
            return False
        
        def monitor_accounts():
            self.monitoring_active = True
            self.LOG_SUCCESS("Real-time account monitoring started")
            
            while self.monitoring_active:
                try:
                    for account in self.trading_accounts:
                        # Get current account snapshot
                        current_snapshot = self.get_real_account_data(account)
                        
                        if current_snapshot:
                            # Get previous snapshot for comparison
                            previous_snapshot = self.account_snapshots.get(account['name'])
                            
                            # Check for alerts
                            self.check_account_alerts(current_snapshot, previous_snapshot)
                            
                            # Update stored snapshot
                            self.account_snapshots[account['name']] = current_snapshot
                            
                        else:
                            self.LOG_WARNING(f"Failed to get data for {account['name']}")
                    
                    # Save snapshots to file
                    self._save_snapshots()
                    
                    time.sleep(self.monitor_interval)
                    
                except Exception as e:
                    self.FAIL_LOUD(f"Monitoring loop error: {str(e)}")
                    time.sleep(30)  # Wait before retrying
            
            self.LOG_SUCCESS("Real-time monitoring stopped")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_accounts, daemon=True)
        monitor_thread.start()
        
        self.LOG_SUCCESS("✅ Production monitoring started successfully")
        return True
    
    def _save_snapshots(self):
        """Save current snapshots to file"""
        try:
            snapshot_dir = os.path.join(project_root, "logs", "snapshots")
            os.makedirs(snapshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = os.path.join(snapshot_dir, f"snapshot_{timestamp}.json")
            
            # Convert snapshots to dict for JSON serialization
            snapshot_data = {}
            for account_name, snapshot in self.account_snapshots.items():
                snapshot_dict = asdict(snapshot)
                snapshot_data[account_name] = snapshot_dict
            
            with open(snapshot_file, "w") as f:
                json.dump(snapshot_data, f, indent=2)
                
        except Exception as e:
            self.LOG_WARNING(f"Failed to save snapshots: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        total_balance = sum(snapshot.cash_balance for snapshot in self.account_snapshots.values())
        total_pnl = sum(snapshot.total_pnl for snapshot in self.account_snapshots.values())
        total_positions = sum(len(snapshot.positions) for snapshot in self.account_snapshots.values())
        
        return {
            "monitoring_active": self.monitoring_active,
            "accounts_monitored": len(self.account_snapshots),
            "total_accounts": len(self.trading_accounts),
            "total_balance": total_balance,
            "total_pnl": total_pnl,
            "total_positions": total_positions,
            "last_updated": max(
                (snapshot.last_updated for snapshot in self.account_snapshots.values()),
                default="Never"
            )
        }
    
    def emergency_stop_monitoring(self, reason: str):
        """Emergency stop monitoring - FAIL SAFELY"""
        self.FAIL_LOUD(f"🚨 EMERGENCY STOP MONITORING: {reason}")
        self.monitoring_active = False
        
        # Save final snapshots
        self._save_snapshots()
        
        # Create emergency report
        emergency_data = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "final_snapshots": {name: asdict(snapshot) for name, snapshot in self.account_snapshots.items()},
            "monitoring_status": self.get_monitoring_status()
        }
        
        emergency_dir = os.path.join(project_root, "logs", "emergency")
        os.makedirs(emergency_dir, exist_ok=True)
        
        emergency_file = os.path.join(emergency_dir, f"emergency_monitor_{int(time.time())}.json")
        with open(emergency_file, "w") as f:
            json.dump(emergency_data, f, indent=2)
        
        print("🛑 MONITORING STOPPED - Check logs for details")
    
    def stop_monitoring(self):
        """Stop monitoring gracefully"""
        self.monitoring_active = False
        self._save_snapshots()
        self.LOG_SUCCESS("Monitoring stopped gracefully")

def main():
    """Main monitor entry point"""
    monitor = ProductionMonitor()
    
    try:
        if not monitor.start_realtime_monitoring():
            print("❌ Failed to start monitoring")
            return 1
            
        print("\n📊 Production Monitor Ready")
        print("💰 Monitoring real account balances and positions")
        print("⏹️  Press Ctrl+C to stop")
        
        while monitor.monitoring_active:
            status = monitor.get_monitoring_status()
            print(f"\r💹 Monitoring: {status['accounts_monitored']}/{status['total_accounts']} accounts | Balance: ${status['total_balance']:.2f} | P&L: ${status['total_pnl']:.2f} | Positions: {status['total_positions']}", end="", flush=True)
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down monitor...")
        monitor.stop_monitoring()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())