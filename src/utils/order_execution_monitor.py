#!/usr/bin/env python3
"""
Continuous Order Execution Monitor
Ensures orders are executing correctly by verifying position changes
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any

class OrderExecutionMonitor:
    def __init__(self, alert_webhook=None):
        self.alert_webhook = alert_webhook
        self.failure_count = 0
        self.max_failures = 3
        self.check_interval = 300  # 5 minutes
        
    async def verify_order_execution(self, port: int) -> Dict[str, Any]:
        """Execute a test order and verify position changed"""
        
        print(f"\n[{datetime.now()}] Checking order execution on port {port}...")
        
        # Run the verification script
        result = subprocess.run(
            ['python3', 'docs/investigations/dom-order-fix/final_order_verification.py', 
             '--port', str(port)],
            capture_output=True,
            text=True
        )
        
        success = result.returncode == 0
        
        # Parse output to check if positions changed
        position_changed = "SUCCESS! ORDERS ARE EXECUTING SUCCESSFULLY!" in result.stdout
        
        return {
            'port': port,
            'success': success,
            'position_changed': position_changed,
            'timestamp': datetime.now().isoformat(),
            'output': result.stdout,
            'error': result.stderr if not success else None
        }
    
    async def check_all_accounts(self):
        """Check order execution on all trading accounts"""
        
        ports = [9223, 9224, 9225]  # All three accounts
        results = []
        
        for port in ports:
            try:
                result = await self.verify_order_execution(port)
                results.append(result)
                
                if not result['position_changed']:
                    await self.handle_failure(result)
                    
            except Exception as e:
                error_result = {
                    'port': port,
                    'success': False,
                    'position_changed': False,
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
                results.append(error_result)
                await self.handle_failure(error_result)
        
        return results
    
    async def handle_failure(self, result: Dict[str, Any]):
        """Handle order execution failure"""
        
        self.failure_count += 1
        
        print(f"❌ CRITICAL: Order execution failure on port {result['port']}!")
        print(f"Failure count: {self.failure_count}/{self.max_failures}")
        
        # Log to file
        with open('logs/order_execution_failures.log', 'a') as f:
            f.write(f"\n{json.dumps(result, indent=2)}\n")
        
        # Send alert if webhook configured
        if self.alert_webhook:
            self.send_alert(result)
        
        # If too many failures, trigger emergency response
        if self.failure_count >= self.max_failures:
            await self.emergency_response()
    
    def send_alert(self, result: Dict[str, Any]):
        """Send alert via webhook"""
        
        try:
            import requests
            
            alert_data = {
                'type': 'ORDER_EXECUTION_FAILURE',
                'severity': 'CRITICAL',
                'message': f"Order execution not updating positions on port {result['port']}",
                'details': result,
                'timestamp': result['timestamp']
            }
            
            response = requests.post(self.alert_webhook, json=alert_data)
            print(f"Alert sent: {response.status_code}")
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    async def emergency_response(self):
        """Emergency response when multiple failures detected"""
        
        print("\n🚨 EMERGENCY: Multiple order execution failures detected!")
        print("Attempting automatic recovery...")
        
        # 1. Check Chrome connections
        subprocess.run(['python3', 'src/utils/check_chrome.py'])
        
        # 2. Try to reinject scripts
        print("Reinjecting trading scripts...")
        # This would need to be implemented based on your needs
        
        # 3. Log emergency state
        emergency_log = {
            'type': 'EMERGENCY_ORDER_EXECUTION_FAILURE',
            'timestamp': datetime.now().isoformat(),
            'failure_count': self.failure_count,
            'action': 'Automatic recovery attempted'
        }
        
        with open('logs/emergency_order_failures.log', 'a') as f:
            f.write(f"\n{json.dumps(emergency_log, indent=2)}\n")
        
        # Reset failure count after emergency response
        self.failure_count = 0
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        
        print("🔍 Starting Order Execution Monitor...")
        print(f"Checking every {self.check_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        while True:
            try:
                # Run checks
                results = await self.check_all_accounts()
                
                # Summary
                successful = sum(1 for r in results if r['position_changed'])
                total = len(results)
                
                print(f"\n✅ Summary: {successful}/{total} accounts executing orders correctly")
                
                if successful == total:
                    print("All systems operational!")
                    self.failure_count = 0  # Reset on full success
                
                # Wait for next check
                print(f"\nNext check in {self.check_interval} seconds...")
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                await asyncio.sleep(30)  # Wait 30s on error

async def main():
    """Main entry point"""
    
    # Optional: Set your alert webhook URL
    # webhook_url = "https://your-webhook.com/alerts"
    webhook_url = None
    
    monitor = OrderExecutionMonitor(alert_webhook=webhook_url)
    await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main())