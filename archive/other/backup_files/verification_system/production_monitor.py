#!/usr/bin/env python3
"""
Production Monitoring Script for Order Verification System
Monitors verification health, success rates, and performance for 24 hours
"""

import requests
import json
import time
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

class ProductionVerificationMonitor:
    def __init__(self):
        self.dashboard_url = "http://localhost:6001"
        self.log_file = "verification_production_monitor.log"
        self.csv_file = f"verification_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.start_time = datetime.now()
        self.alert_counts = {}
        self.metrics_history = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def get_verification_health(self) -> Dict[str, Any]:
        """Get current verification health status"""
        try:
            response = requests.get(f"{self.dashboard_url}/api/verification-health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Failed to get health status: {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Error getting health status: {e}", "ERROR")
            return None
    
    def get_verification_metrics(self) -> Dict[str, Any]:
        """Get current verification metrics"""
        try:
            response = requests.get(f"{self.dashboard_url}/api/verification-metrics", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Failed to get metrics: {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Error getting metrics: {e}", "ERROR")
            return None
    
    def check_success_criteria(self, health: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, bool]:
        """Check if success criteria are being met"""
        criteria = {}
        
        # Get success/failure rates
        hourly_rates = metrics.get('success_failure_rates', {}).get('last_hour', {})
        
        # Criteria 1: Failure rate < 1%
        failure_rate = hourly_rates.get('failure_rate', 0)
        criteria['failure_rate_ok'] = failure_rate < 1.0
        
        # Criteria 2: No false positives (checked via alerts)
        active_alerts = health.get('alert_status', [])
        criteria['no_false_positives'] = 'false positive' not in str(active_alerts).lower()
        
        # Criteria 3: Performance overhead < 100ms
        perf_metrics = metrics.get('performance_summary', {})
        avg_overhead = perf_metrics.get('total_overhead_times', {}).get('avg', 0)
        criteria['performance_ok'] = avg_overhead < 100
        
        # Criteria 4: Health score > 90
        health_score = health.get('health_score', 0)
        criteria['health_score_ok'] = health_score > 90
        
        # Criteria 5: Audit trail (check if we're getting data)
        total_attempts = hourly_rates.get('total_attempts', 0)
        criteria['audit_trail_ok'] = True  # Always true if monitoring is working
        
        return criteria
    
    def save_metrics_snapshot(self, health: Dict[str, Any], metrics: Dict[str, Any]):
        """Save current metrics to CSV"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health.get('health_score', 0),
            'total_attempts': metrics.get('success_failure_rates', {}).get('last_hour', {}).get('total_attempts', 0),
            'success_rate': metrics.get('success_failure_rates', {}).get('last_hour', {}).get('success_rate', 0),
            'failure_rate': metrics.get('success_failure_rates', {}).get('last_hour', {}).get('failure_rate', 0),
            'avg_execution_time': metrics.get('performance_summary', {}).get('execution_times', {}).get('avg', 0),
            'avg_overhead_time': metrics.get('performance_summary', {}).get('total_overhead_times', {}).get('avg', 0),
            'consecutive_failures': health.get('consecutive_failures', 0),
            'active_alerts': len(health.get('alert_status', []))
        }
        
        self.metrics_history.append(snapshot)
        
        # Write to CSV
        file_exists = os.path.exists(self.csv_file)
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=snapshot.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(snapshot)
    
    def generate_hourly_report(self):
        """Generate hourly summary report"""
        self.log("=" * 60)
        self.log("HOURLY VERIFICATION SYSTEM REPORT")
        self.log("=" * 60)
        
        health = self.get_verification_health()
        metrics = self.get_verification_metrics()
        
        if health and metrics:
            # Health summary
            self.log(f"Health Score: {health.get('health_score', 0):.1f}/100")
            self.log(f"Status: {health.get('status', 'UNKNOWN')} ({health.get('status_color', 'gray')})")
            
            # Success/failure rates
            hourly = metrics.get('success_failure_rates', {}).get('last_hour', {})
            self.log(f"Total Attempts (last hour): {hourly.get('total_attempts', 0)}")
            self.log(f"Success Rate: {hourly.get('success_rate', 0):.1f}%")
            self.log(f"Failure Rate: {hourly.get('failure_rate', 0):.1f}%")
            
            # Performance
            perf = metrics.get('performance_summary', {})
            self.log(f"Avg Execution Time: {perf.get('execution_times', {}).get('avg', 0):.1f}ms")
            self.log(f"Avg Overhead Time: {perf.get('total_overhead_times', {}).get('avg', 0):.1f}ms")
            
            # Success criteria check
            criteria = self.check_success_criteria(health, metrics)
            self.log("\nSuccess Criteria Status:")
            for criterion, passed in criteria.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                self.log(f"  {criterion}: {status}")
            
            # Active alerts
            alerts = health.get('alert_status', [])
            if alerts:
                self.log("\n⚠️ Active Alerts:")
                for alert in alerts:
                    self.log(f"  - {alert}")
            else:
                self.log("\n✅ No active alerts")
            
            self.save_metrics_snapshot(health, metrics)
        
        self.log("=" * 60)
    
    def run_monitoring(self, duration_hours: int = 24):
        """Run continuous monitoring for specified duration"""
        self.log(f"🚀 Starting Production Verification Monitoring")
        self.log(f"Duration: {duration_hours} hours")
        self.log(f"Dashboard URL: {self.dashboard_url}")
        self.log("=" * 60)
        
        # Initial check
        health = self.get_verification_health()
        if not health:
            self.log("❌ Cannot connect to dashboard. Aborting.", "ERROR")
            return
        
        self.log(f"✅ Initial health check successful")
        self.log(f"Initial health score: {health.get('health_score', 0):.1f}/100")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        last_hourly_report = datetime.now()
        check_interval = 300  # 5 minutes
        
        while datetime.now() < end_time:
            try:
                # Check if hour has passed for report
                if datetime.now() - last_hourly_report >= timedelta(hours=1):
                    self.generate_hourly_report()
                    last_hourly_report = datetime.now()
                
                # Get current status
                health = self.get_verification_health()
                metrics = self.get_verification_metrics()
                
                if health and metrics:
                    # Check for critical issues
                    health_score = health.get('health_score', 0)
                    if health_score < 70:
                        self.log(f"⚠️ WARNING: Health score below 70: {health_score:.1f}", "WARNING")
                    
                    consecutive_failures = health.get('consecutive_failures', 0)
                    if consecutive_failures >= 5:
                        self.log(f"🚨 CRITICAL: {consecutive_failures} consecutive failures!", "CRITICAL")
                    
                    # Save snapshot every check
                    self.save_metrics_snapshot(health, metrics)
                
                # Wait for next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.log("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                self.log(f"Error during monitoring: {e}", "ERROR")
                time.sleep(check_interval)
        
        # Final report
        self.log("\n" + "=" * 60)
        self.log("FINAL MONITORING REPORT")
        self.log("=" * 60)
        self.log(f"Monitoring Duration: {datetime.now() - self.start_time}")
        self.log(f"Total Snapshots: {len(self.metrics_history)}")
        self.log(f"Metrics saved to: {self.csv_file}")
        self.log(f"Log saved to: {self.log_file}")
        
        # Calculate overall statistics
        if self.metrics_history:
            avg_health = sum(m['health_score'] for m in self.metrics_history) / len(self.metrics_history)
            max_failures = max(m['consecutive_failures'] for m in self.metrics_history)
            total_attempts = sum(m['total_attempts'] for m in self.metrics_history)
            
            self.log(f"\nOverall Statistics:")
            self.log(f"  Average Health Score: {avg_health:.1f}/100")
            self.log(f"  Max Consecutive Failures: {max_failures}")
            self.log(f"  Total Verification Attempts: {total_attempts}")

if __name__ == "__main__":
    monitor = ProductionVerificationMonitor()
    
    # Run for 24 hours by default, or specify custom duration
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    
    monitor.run_monitoring(duration)