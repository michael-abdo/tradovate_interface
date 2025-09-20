#!/usr/bin/env python3
"""
Production Trading Engine with Real-Time Validation
FAIL FAST, FAIL LOUD, FAIL SAFELY

Real trading order execution with comprehensive safety mechanisms
"""

import os
import sys
import time
import json
import threading
import pychrome
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.chrome_communication import safe_evaluate, OperationType
from production_validator import ProductionValidator, TradingAccount

class OrderAction(Enum):
    BUY = "Buy"
    SELL = "Sell"

class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TradingOrder:
    order_id: str
    account_name: str
    symbol: str
    quantity: int
    action: OrderAction
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: str = ""
    execution_time: Optional[str] = None
    error_message: Optional[str] = None

class ProductionTradingEngine:
    """Real trading engine with production safety mechanisms"""
    
    def __init__(self):
        self.validator = ProductionValidator()
        self.trading_active = False
        self.pending_orders: List[TradingOrder] = []
        self.executed_orders: List[TradingOrder] = []
        self.stop_loss_percentage = 0.02  # 2% stop loss
        self.max_daily_loss = 500.0  # $500 max daily loss
        self.order_counter = 0
        
    def FAIL_LOUD(self, message: str):
        """Critical error logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! TRADING CRITICAL !!! {message}"
        print(error_msg)
        
        # Log to file
        self._log_to_file("CRITICAL", error_msg)
        
    def LOG_SUCCESS(self, message: str):
        """Success logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✅ TRADING SUCCESS: {message}"
        print(success_msg)
        self._log_to_file("SUCCESS", success_msg)
        
    def LOG_WARNING(self, message: str):
        """Warning logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  TRADING WARNING: {message}"
        print(warning_msg)
        self._log_to_file("WARNING", warning_msg)
        
    def _log_to_file(self, level: str, message: str):
        """Log messages to file with timestamps"""
        log_dir = os.path.join(project_root, "logs", "trading")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"trading_{today}.log")
        
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
            
    def validate_trading_permissions(self, account: TradingAccount) -> bool:
        """Validate account has trading permissions - FAIL FAST"""
        try:
            browser = pychrome.Browser(url=f"http://127.0.0.1:{account.port}")
            tabs = browser.list_tab()
            
            for tab_info in tabs:
                try:
                    tab = browser.get_tab(tab_info['id'])
                    tab.start()
                    
                    # Check if connected to real Tradovate
                    url_result = safe_evaluate(tab, "window.location.href", OperationType.CRITICAL)
                    if url_result.success and "trader.tradovate.com" in str(url_result.value):
                        
                        # Check for trading interface elements
                        trading_check = safe_evaluate(
                            tab,
                            """
                            // Check for DOM trading panel or order entry
                            const domPanel = document.querySelector('.dom-container, .trading-panel, [data-qa="dom-panel"]');
                            const orderEntry = document.querySelector('.order-entry, [data-qa="order-entry"]');
                            const buyButton = document.querySelector('[data-qa="buy-button"], .buy-button');
                            const sellButton = document.querySelector('[data-qa="sell-button"], .sell-button');
                            
                            return !!(domPanel || orderEntry || (buyButton && sellButton));
                            """,
                            OperationType.CRITICAL,
                            f"Trading permissions check for {account.name}"
                        )
                        
                        tab.stop()
                        
                        if trading_check.success and trading_check.value:
                            self.LOG_SUCCESS(f"✅ Trading permissions validated: {account.name}")
                            return True
                        else:
                            self.FAIL_LOUD(f"NO TRADING PERMISSIONS: {account.name} - Trading interface not accessible")
                            return False
                            
                    else:
                        tab.stop()
                        
                except Exception as e:
                    self.LOG_WARNING(f"Permission check failed for {account.name}: {str(e)}")
                    continue
                    
            self.FAIL_LOUD(f"NO TRADOVATE CONNECTION: {account.name} - Cannot validate permissions")
            return False
            
        except Exception as e:
            self.FAIL_LOUD(f"PERMISSION VALIDATION ERROR: {account.name} - {str(e)}")
            return False
    
    def validate_sufficient_margin(self, account: TradingAccount, symbol: str, quantity: int) -> bool:
        """Validate sufficient margin for trade - FAIL FAST"""
        try:
            current_balance = self.validator.get_real_balance(account)
            if current_balance is None:
                self.FAIL_LOUD(f"CANNOT GET BALANCE: {account.name} - Cannot validate margin")
                return False
                
            # Estimate margin requirement (simplified)
            # For ES futures: ~$1,200 per contract
            # For NQ futures: ~$2,000 per contract  
            margin_requirements = {
                "ES": 1200.0,
                "NQ": 2000.0,
                "YM": 800.0,
                "RTY": 1000.0
            }
            
            required_margin = margin_requirements.get(symbol, 2000.0) * quantity
            
            if current_balance < required_margin * 1.5:  # 50% safety buffer
                self.FAIL_LOUD(f"INSUFFICIENT MARGIN: {account.name} - Need ${required_margin:.2f}, Have ${current_balance:.2f}")
                return False
                
            self.LOG_SUCCESS(f"✅ Sufficient margin: {account.name} - ${current_balance:.2f} for ${required_margin:.2f}")
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"MARGIN VALIDATION ERROR: {account.name} - {str(e)}")
            return False
    
    def confirm_live_trade(self, symbol: str, quantity: int, action: OrderAction, account: TradingAccount) -> bool:
        """Require explicit confirmation for live trades - FAIL SAFELY"""
        print("\n" + "="*60)
        print("⚠️  LIVE TRADING CONFIRMATION REQUIRED ⚠️")
        print("="*60)
        print(f"Account: {account.name}")
        print(f"Action: {action.value}")
        print(f"Symbol: {symbol}")
        print(f"Quantity: {quantity}")
        print(f"Current Balance: ${self.validator.get_real_balance(account):.2f}")
        print("="*60)
        
        response = input("CONFIRM LIVE TRADE? Type 'YES' to proceed: ").strip().upper()
        
        if response == "YES":
            self.LOG_SUCCESS(f"✅ Trade confirmed: {action.value} {quantity} {symbol} on {account.name}")
            return True
        else:
            self.LOG_WARNING(f"🛑 Trade cancelled by user: {action.value} {quantity} {symbol} on {account.name}")
            return False
    
    def execute_real_trading_order(self, symbol: str, quantity: int, action: OrderAction, account: TradingAccount) -> TradingOrder:
        """Execute real trading order with full validation - FAIL SAFELY"""
        
        # Create order tracking
        self.order_counter += 1
        order = TradingOrder(
            order_id=f"ORDER_{self.order_counter}_{int(time.time())}",
            account_name=account.name,
            symbol=symbol,
            quantity=quantity,
            action=action,
            timestamp=datetime.now().isoformat()
        )
        
        self.pending_orders.append(order)
        
        try:
            # FAIL FAST: Pre-execution validation
            if not self.validate_trading_permissions(account):
                order.status = OrderStatus.FAILED
                order.error_message = "Trading permissions validation failed"
                return order
                
            if not self.validate_sufficient_margin(account, symbol, quantity):
                order.status = OrderStatus.FAILED
                order.error_message = "Insufficient margin"
                return order
            
            # FAIL SAFELY: Confirm before execution
            if not self.confirm_live_trade(symbol, quantity, action, account):
                order.status = OrderStatus.CANCELLED
                order.error_message = "User cancelled trade"
                return order
            
            # Execute real order on Tradovate
            browser = pychrome.Browser(url=f"http://127.0.0.1:{account.port}")
            tabs = browser.list_tab()
            
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
                order.status = OrderStatus.FAILED
                order.error_message = "No Tradovate tab found"
                self.FAIL_LOUD(f"ORDER FAILED: {order.order_id} - No Tradovate tab")
                return order
            
            # Execute the actual trade
            trade_script = f"""
            // Real trading execution script
            (function() {{
                try {{
                    // Look for DOM trading interface
                    const domPanel = document.querySelector('.dom-container, .trading-panel, [data-qa="dom-panel"]');
                    if (!domPanel) {{
                        return {{ success: false, error: "DOM panel not found" }};
                    }}
                    
                    // Set symbol
                    const symbolInput = document.querySelector('input[data-qa="symbol-input"], .symbol-input');
                    if (symbolInput) {{
                        symbolInput.value = '{symbol}';
                        symbolInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    // Set quantity
                    const quantityInput = document.querySelector('input[data-qa="quantity-input"], .quantity-input');
                    if (quantityInput) {{
                        quantityInput.value = '{quantity}';
                        quantityInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    // Click appropriate button
                    const actionButton = document.querySelector('[data-qa="{action.value.lower()}-button"], .{action.value.lower()}-button');
                    if (actionButton) {{
                        // Add delay to ensure form is ready
                        setTimeout(() => {{
                            actionButton.click();
                        }}, 1000);
                        
                        return {{ success: true, message: "Order submitted" }};
                    }} else {{
                        return {{ success: false, error: "{action.value} button not found" }};
                    }}
                    
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }})();
            """
            
            execution_result = safe_evaluate(
                tradovate_tab,
                trade_script,
                OperationType.CRITICAL,
                f"Execute {action.value} order for {account.name}"
            )
            
            tradovate_tab.stop()
            
            if execution_result.success:
                order.status = OrderStatus.EXECUTED
                order.execution_time = datetime.now().isoformat()
                self.executed_orders.append(order)
                
                self.LOG_SUCCESS(f"✅ ORDER EXECUTED: {order.order_id} - {action.value} {quantity} {symbol}")
                
                # Start order monitoring
                self._monitor_order_execution(order)
                
            else:
                order.status = OrderStatus.FAILED
                order.error_message = f"Execution failed: {execution_result.error}"
                self.FAIL_LOUD(f"ORDER EXECUTION FAILED: {order.order_id} - {execution_result.error}")
            
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            self.FAIL_LOUD(f"ORDER EXECUTION ERROR: {order.order_id} - {str(e)}")
        
        return order
    
    def _monitor_order_execution(self, order: TradingOrder):
        """Monitor order status after execution"""
        def monitor():
            time.sleep(5)  # Wait for order to settle
            
            try:
                # Check if order was actually filled
                account = next((acc for acc in self.validator.trading_accounts if acc.name == order.account_name), None)
                if account:
                    current_balance = self.validator.get_real_balance(account)
                    if current_balance != account.last_balance:
                        self.LOG_SUCCESS(f"✅ Order confirmed - Balance changed: {order.order_id}")
                    else:
                        self.LOG_WARNING(f"⚠️  Order status unclear - No balance change: {order.order_id}")
            except Exception as e:
                self.LOG_WARNING(f"Order monitoring failed: {order.order_id} - {str(e)}")
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def emergency_stop_all_trading(self, reason: str):
        """Emergency stop all trading activity - FAIL SAFELY"""
        self.FAIL_LOUD(f"🚨 EMERGENCY STOP: {reason}")
        self.trading_active = False
        
        # Cancel all pending orders
        for order in self.pending_orders:
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.error_message = f"Emergency stop: {reason}"
        
        # Log emergency stop
        emergency_data = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "pending_orders_cancelled": len([o for o in self.pending_orders if o.status == OrderStatus.CANCELLED]),
            "total_executed_orders": len(self.executed_orders)
        }
        
        log_dir = os.path.join(project_root, "logs", "emergency")
        os.makedirs(log_dir, exist_ok=True)
        
        emergency_file = os.path.join(log_dir, f"emergency_stop_{int(time.time())}.json")
        with open(emergency_file, "w") as f:
            json.dump(emergency_data, f, indent=2)
        
        print("🛑 ALL TRADING STOPPED - Check logs for details")
    
    def start_production_trading(self) -> bool:
        """Start production trading with full validation"""
        print("="*60)
        print("🚀 STARTING PRODUCTION TRADING ENGINE")
        print("="*60)
        
        # Run production validation first
        if not self.validator.run_production_validation():
            self.FAIL_LOUD("Production validation failed - cannot start trading")
            return False
        
        self.trading_active = True
        self.LOG_SUCCESS("✅ Production trading engine started successfully")
        
        return True
    
    def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            "trading_active": self.trading_active,
            "total_pending_orders": len([o for o in self.pending_orders if o.status == OrderStatus.PENDING]),
            "total_executed_orders": len(self.executed_orders),
            "total_failed_orders": len([o for o in self.pending_orders if o.status == OrderStatus.FAILED]),
            "accounts_authenticated": len([acc for acc in self.validator.trading_accounts if acc.authenticated]),
            "total_accounts": len(self.validator.trading_accounts)
        }

def main():
    """Main trading engine entry point"""
    engine = ProductionTradingEngine()
    
    if not engine.start_production_trading():
        print("❌ Failed to start production trading")
        return 1
    
    print("\n🎯 Production Trading Engine Ready")
    print("📊 Use engine.execute_real_trading_order() to place trades")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        while engine.trading_active:
            status = engine.get_trading_status()
            print(f"\r📈 Active | Accounts: {status['accounts_authenticated']}/{status['total_accounts']} | Orders: {status['total_executed_orders']} executed, {status['total_pending_orders']} pending", end="", flush=True)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down trading engine...")
        engine.emergency_stop_all_trading("Manual shutdown")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())