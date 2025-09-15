#!/usr/bin/env python3
"""
Continuous Order Execution Monitor
Ensures orders are executing correctly by verifying position changes
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque

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


class VerificationMonitor:
    """
    Advanced monitoring system for mandatory order verification
    Tracks verification attempts, success/failure rates, and patterns
    Provides comprehensive analysis and alerting for verification health
    """
    
    def __init__(self, alert_webhook=None, data_retention_hours=24):
        self.alert_webhook = alert_webhook
        self.data_retention_hours = data_retention_hours
        
        # Verification tracking data structures
        self.verification_attempts = deque(maxlen=1000)  # Keep last 1000 attempts
        self.verification_by_account = defaultdict(list)
        self.verification_by_symbol = defaultdict(list)
        self.failure_patterns = defaultdict(int)
        
        # Performance tracking
        self.performance_metrics = {
            'execution_times': deque(maxlen=500),
            'state_capture_times': deque(maxlen=500),
            'total_overhead_times': deque(maxlen=500)
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'failure_rate_percent': 10,      # Alert if >10% failure rate
            'consecutive_failures': 5,       # Alert after 5 consecutive failures
            'high_overhead_percent': 20,     # Alert if >20% of orders have high overhead
            'timeout_rate_percent': 5        # Alert if >5% of verifications timeout
        }
        
        # State tracking
        self.consecutive_failures = 0
        self.last_alert_time = {}
        self.alert_cooldown_minutes = 15
    
    def record_verification_attempt(self, verification_data: Dict[str, Any]):
        """
        Record a verification attempt with all relevant metadata
        @param verification_data: Dictionary containing verification details
        """
        timestamp = datetime.now()
        
        # Enrich the data with timestamp and derived metrics
        enriched_data = {
            **verification_data,
            'timestamp': timestamp,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_success': verification_data.get('success', False),
            'execution_time_ms': verification_data.get('executionTime', 0),
            'total_overhead_ms': verification_data.get('totalOverhead', 0)
        }
        
        # Store in main tracking structures
        self.verification_attempts.append(enriched_data)
        
        # Organize by account and symbol for detailed analysis
        account = verification_data.get('account', 'unknown')
        symbol = verification_data.get('symbol', 'unknown')
        
        self.verification_by_account[account].append(enriched_data)
        self.verification_by_symbol[symbol].append(enriched_data)
        
        # Track failure patterns
        if not enriched_data['is_success']:
            failure_reason = verification_data.get('failureReason', 'UNKNOWN')
            self.failure_patterns[failure_reason] += 1
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        # Track performance metrics
        exec_time = enriched_data['execution_time_ms']
        if exec_time > 0:
            self.performance_metrics['execution_times'].append(exec_time)
        
        overhead_time = enriched_data['total_overhead_ms']
        if overhead_time > 0:
            self.performance_metrics['total_overhead_times'].append(overhead_time)
        
        # Clean old data
        self._cleanup_old_data()
        
        # Check for alert conditions
        self._check_alert_conditions(enriched_data)
    
    def get_success_failure_rates(self, hours_back: int = 1) -> Dict[str, Any]:
        """Calculate verification success/failure rates for specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_attempts = [
            attempt for attempt in self.verification_attempts 
            if attempt['timestamp'] > cutoff_time
        ]
        
        if not recent_attempts:
            return {
                'total_attempts': 0,
                'success_count': 0,
                'failure_count': 0,
                'success_rate': 0.0,
                'failure_rate': 0.0
            }
        
        total_attempts = len(recent_attempts)
        success_count = sum(1 for attempt in recent_attempts if attempt['is_success'])
        failure_count = total_attempts - success_count
        
        return {
            'total_attempts': total_attempts,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': (success_count / total_attempts) * 100,
            'failure_rate': (failure_count / total_attempts) * 100,
            'time_window_hours': hours_back
        }
    
    def detect_failure_patterns(self) -> Dict[str, Any]:
        """Analyze failure patterns to identify systemic issues"""
        
        # Get recent failures (last 2 hours)
        cutoff_time = datetime.now() - timedelta(hours=2)
        recent_failures = [
            attempt for attempt in self.verification_attempts 
            if attempt['timestamp'] > cutoff_time and not attempt['is_success']
        ]
        
        if not recent_failures:
            return {'patterns_detected': False, 'analysis': 'No recent failures to analyze'}
        
        # Analyze patterns
        patterns = {
            'by_account': defaultdict(int),
            'by_symbol': defaultdict(int),
            'by_hour': defaultdict(int),
            'by_failure_reason': defaultdict(int),
            'by_time_of_day': defaultdict(int)
        }
        
        for failure in recent_failures:
            patterns['by_account'][failure.get('account', 'unknown')] += 1
            patterns['by_symbol'][failure.get('symbol', 'unknown')] += 1
            patterns['by_hour'][failure['timestamp'].hour] += 1
            patterns['by_failure_reason'][failure.get('failureReason', 'UNKNOWN')] += 1
            
            # Categorize time of day
            hour = failure['timestamp'].hour
            if 6 <= hour < 12:
                time_category = 'morning'
            elif 12 <= hour < 18:
                time_category = 'afternoon'
            elif 18 <= hour < 24:
                time_category = 'evening'
            else:
                time_category = 'night'
            patterns['by_time_of_day'][time_category] += 1
        
        # Identify significant patterns (more than 30% of failures)
        failure_threshold = len(recent_failures) * 0.3
        significant_patterns = []
        
        for pattern_type, pattern_data in patterns.items():
            for key, count in pattern_data.items():
                if count >= failure_threshold:
                    significant_patterns.append({
                        'type': pattern_type,
                        'key': key,
                        'count': count,
                        'percentage': (count / len(recent_failures)) * 100
                    })
        
        return {
            'patterns_detected': len(significant_patterns) > 0,
            'total_recent_failures': len(recent_failures),
            'significant_patterns': significant_patterns,
            'all_patterns': dict(patterns),
            'analysis_window_hours': 2
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate comprehensive performance metrics summary"""
        
        def calculate_stats(values):
            if not values:
                return {'min': 0, 'max': 0, 'avg': 0, 'p95': 0, 'p99': 0}
            
            sorted_values = sorted(values)
            length = len(sorted_values)
            
            return {
                'min': sorted_values[0],
                'max': sorted_values[-1],
                'avg': sum(sorted_values) / length,
                'p95': sorted_values[int(length * 0.95)] if length > 0 else 0,
                'p99': sorted_values[int(length * 0.99)] if length > 0 else 0,
                'count': length
            }
        
        # Calculate performance statistics
        exec_times = list(self.performance_metrics['execution_times'])
        overhead_times = list(self.performance_metrics['total_overhead_times'])
        
        # Calculate performance health indicators
        slow_executions = sum(1 for t in exec_times if t > 500)  # >500ms
        high_overhead = sum(1 for t in overhead_times if t > 1000)  # >1s
        
        exec_count = len(exec_times)
        overhead_count = len(overhead_times)
        
        return {
            'execution_times': calculate_stats(exec_times),
            'total_overhead_times': calculate_stats(overhead_times),
            'performance_health': {
                'slow_execution_rate': (slow_executions / exec_count * 100) if exec_count > 0 else 0,
                'high_overhead_rate': (high_overhead / overhead_count * 100) if overhead_count > 0 else 0,
                'total_measurements': max(exec_count, overhead_count)
            }
        }
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        # Get various time window metrics
        hourly_rates = self.get_success_failure_rates(1)
        daily_rates = self.get_success_failure_rates(24)
        
        # Get pattern analysis
        patterns = self.detect_failure_patterns()
        
        # Get performance summary
        performance = self.get_performance_summary()
        
        # Calculate health score (0-100)
        health_factors = []
        
        # Factor 1: Success rate (weight: 40%)
        success_rate_score = min(hourly_rates['success_rate'], 100)
        health_factors.append(('success_rate', success_rate_score, 0.4))
        
        # Factor 2: Performance (weight: 30%)
        perf_health = performance['performance_health']
        perf_score = max(0, 100 - perf_health['slow_execution_rate'] - perf_health['high_overhead_rate'])
        health_factors.append(('performance', perf_score, 0.3))
        
        # Factor 3: Pattern stability (weight: 20%)
        pattern_penalty = len(patterns.get('significant_patterns', [])) * 10
        pattern_score = max(0, 100 - pattern_penalty)
        health_factors.append(('patterns', pattern_score, 0.2))
        
        # Factor 4: Consecutive failures (weight: 10%)
        consecutive_penalty = min(self.consecutive_failures * 20, 100)
        consecutive_score = max(0, 100 - consecutive_penalty)
        health_factors.append(('consecutive_failures', consecutive_score, 0.1))
        
        # Calculate weighted health score
        health_score = sum(score * weight for _, score, weight in health_factors)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': round(health_score, 1),
            'health_factors': {name: round(score, 1) for name, score, _ in health_factors},
            'success_failure_rates': {
                'last_hour': hourly_rates,
                'last_24_hours': daily_rates
            },
            'failure_patterns': patterns,
            'performance_metrics': performance,
            'consecutive_failures': self.consecutive_failures,
            'most_common_failures': dict(list(self.failure_patterns.items())[:5]),
            'alert_status': self._get_active_alerts()
        }
    
    def _cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.data_retention_hours)
        
        # Clean account-specific data
        for account, attempts in self.verification_by_account.items():
            self.verification_by_account[account] = [
                attempt for attempt in attempts 
                if attempt['timestamp'] > cutoff_time
            ]
        
        # Clean symbol-specific data
        for symbol, attempts in self.verification_by_symbol.items():
            self.verification_by_symbol[symbol] = [
                attempt for attempt in attempts 
                if attempt['timestamp'] > cutoff_time
            ]
    
    def _check_alert_conditions(self, verification_data: Dict[str, Any]):
        """Check if any alert conditions are met"""
        
        # Check failure rate
        hourly_rates = self.get_success_failure_rates(1)
        if (hourly_rates['total_attempts'] >= 10 and 
            hourly_rates['failure_rate'] > self.alert_thresholds['failure_rate_percent']):
            self._send_alert('HIGH_FAILURE_RATE', {
                'failure_rate': hourly_rates['failure_rate'],
                'threshold': self.alert_thresholds['failure_rate_percent'],
                'details': hourly_rates
            })
        
        # Check consecutive failures
        if self.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            self._send_alert('CONSECUTIVE_FAILURES', {
                'consecutive_count': self.consecutive_failures,
                'threshold': self.alert_thresholds['consecutive_failures']
            })
        
        # Check performance issues
        performance = self.get_performance_summary()
        perf_health = performance['performance_health']
        if perf_health['high_overhead_rate'] > self.alert_thresholds['high_overhead_percent']:
            self._send_alert('HIGH_OVERHEAD', {
                'overhead_rate': perf_health['high_overhead_rate'],
                'threshold': self.alert_thresholds['high_overhead_percent'],
                'performance_details': performance
            })
    
    def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Send alert if not in cooldown period"""
        
        now = datetime.now()
        last_alert = self.last_alert_time.get(alert_type)
        
        # Check cooldown
        if (last_alert and 
            (now - last_alert).total_seconds() < self.alert_cooldown_minutes * 60):
            return
        
        self.last_alert_time[alert_type] = now
        
        try:
            if self.alert_webhook:
                import requests
                
                alert_payload = {
                    'type': 'VERIFICATION_ALERT',
                    'alert_category': alert_type,
                    'severity': 'HIGH' if alert_type in ['CONSECUTIVE_FAILURES', 'HIGH_FAILURE_RATE'] else 'MEDIUM',
                    'timestamp': now.isoformat(),
                    'data': alert_data,
                    'source': 'VerificationMonitor'
                }
                
                response = requests.post(self.alert_webhook, json=alert_payload, timeout=10)
                print(f"🚨 Alert sent [{alert_type}]: {response.status_code}")
            else:
                print(f"🚨 VERIFICATION ALERT [{alert_type}]: {alert_data}")
                
        except Exception as e:
            print(f"❌ Failed to send verification alert: {e}")
    
    def _get_active_alerts(self) -> List[str]:
        """Get list of currently active alert conditions"""
        active_alerts = []
        
        # Check current conditions
        hourly_rates = self.get_success_failure_rates(1)
        
        if (hourly_rates['total_attempts'] >= 10 and 
            hourly_rates['failure_rate'] > self.alert_thresholds['failure_rate_percent']):
            active_alerts.append(f"High failure rate: {hourly_rates['failure_rate']:.1f}%")
        
        if self.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            active_alerts.append(f"Consecutive failures: {self.consecutive_failures}")
        
        performance = self.get_performance_summary()
        perf_health = performance['performance_health']
        if perf_health['high_overhead_rate'] > self.alert_thresholds['high_overhead_percent']:
            active_alerts.append(f"High overhead rate: {perf_health['high_overhead_rate']:.1f}%")
        
        return active_alerts

async def main():
    """Main entry point"""
    
    # Optional: Set your alert webhook URL
    # webhook_url = "https://your-webhook.com/alerts"
    webhook_url = None
    
    monitor = OrderExecutionMonitor(alert_webhook=webhook_url)
    await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main())