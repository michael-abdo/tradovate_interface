#!/usr/bin/env python3
"""
Comprehensive test runner for enhanced startup
Executes start_all.py with monitoring, metrics collection, and analysis
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import psutil
from datetime import datetime
from typing import Dict, Optional, Tuple
import resource

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from structured_logger import get_logger
from tests.startup.monitor_startup_logs import LogMonitor
from tests.startup.test_startup_validation import StartupTestValidator


class StartupTestRunner:
    """Runs startup test with comprehensive monitoring"""
    
    def __init__(self):
        self.logger = get_logger("test_runner", log_file="test/startup_test.log")
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = None
        self.end_time = None
        self.process = None
        self.monitor = None
        self.metrics = {
            'startup_time': None,
            'peak_memory_mb': 0,
            'peak_cpu_percent': 0,
            'chrome_instances_started': 0,
            'retry_attempts': 0,
            'final_status': None,
            'exit_code': None
        }
        self.resource_monitor_active = True
        
    def pre_test_validation(self) -> bool:
        """Run pre-test validation"""
        self.logger.info("Running pre-test validation", test_id=self.test_id)
        
        validator = StartupTestValidator()
        return validator.run_validation()
    
    def start_log_monitoring(self) -> LogMonitor:
        """Start real-time log monitoring in background"""
        self.logger.info("Starting log monitoring")
        
        monitor = LogMonitor()
        
        # Configure logs to monitor
        log_configs = [
            {
                'file': 'logs/startup/startup_manager.log',
                'label': 'StartupManager',
                'type': 'json'
            },
            {
                'file': 'logs/startup/start_all.log',
                'label': 'StartAll',
                'type': 'json'
            },
            {
                'file': 'logs/chrome_cleanup/cleanup.log',
                'label': 'Cleanup',
                'type': 'text'
            }
        ]
        
        # Start monitoring in background
        monitor_thread = threading.Thread(
            target=monitor.start_monitoring,
            args=(log_configs,),
            daemon=True
        )
        monitor_thread.start()
        
        return monitor
    
    def monitor_resources(self):
        """Monitor system resources during test"""
        self.logger.info("Starting resource monitoring")
        
        while self.resource_monitor_active and self.process:
            try:
                # Monitor main process
                if self.process.poll() is None:  # Still running
                    proc = psutil.Process(self.process.pid)
                    
                    # Get memory usage
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                    self.metrics['peak_memory_mb'] = max(
                        self.metrics['peak_memory_mb'], 
                        memory_mb
                    )
                    
                    # Get CPU usage
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    self.metrics['peak_cpu_percent'] = max(
                        self.metrics['peak_cpu_percent'],
                        cpu_percent
                    )
                
                # Count Chrome instances
                chrome_count = 0
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if 'chrome' in proc.info['name'].lower():
                            cmdline = ' '.join(proc.info.get('cmdline', []))
                            if any(f'922{i}' in cmdline for i in range(3, 5)):
                                chrome_count += 1
                    except:
                        pass
                
                self.metrics['chrome_instances_started'] = max(
                    self.metrics['chrome_instances_started'],
                    chrome_count
                )
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error("Resource monitoring error", error=str(e))
                time.sleep(1)
    
    def execute_startup(self, timeout: int = 120) -> Tuple[bool, str]:
        """Execute start_all.py with timeout and monitoring"""
        self.logger.info("Executing startup test", test_id=self.test_id, timeout=timeout)
        
        print("\n" + "="*60)
        print("🚀 EXECUTING ENHANCED STARTUP TEST")
        print("="*60)
        print(f"\nTest ID: {self.test_id}")
        print(f"Timeout: {timeout} seconds")
        print("\nStarting start_all.py...\n")
        
        self.start_time = time.time()
        
        try:
            # Start the process
            self.process = subprocess.Popen(
                [sys.executable, "start_all.py", "--no-watchdog", "--wait", "10"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Start resource monitoring
            resource_thread = threading.Thread(
                target=self.monitor_resources,
                daemon=True
            )
            resource_thread.start()
            
            # Monitor output with timeout
            output_lines = []
            start_time = time.time()
            
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    self.logger.error("Startup timeout exceeded", timeout=timeout)
                    print(f"\n❌ Timeout exceeded ({timeout}s)")
                    self.process.terminate()
                    self.metrics['final_status'] = 'timeout'
                    return False, "Timeout exceeded"
                
                # Read output
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                
                # Display and store output
                line = line.rstrip()
                print(f"[start_all] {line}")
                output_lines.append(line)
                
                # Check for specific patterns
                if "Starting enhanced auto-login process" in line:
                    self.logger.info("Enhanced startup detected")
                elif "Startup failed:" in line:
                    self.logger.error("Startup failure detected", line=line)
                elif "retry" in line.lower():
                    self.metrics['retry_attempts'] += 1
                elif "Starting dashboard..." in line:
                    self.logger.info("Dashboard starting - startup successful")
                    self.metrics['final_status'] = 'success'
            
            # Get exit code
            exit_code = self.process.wait()
            self.metrics['exit_code'] = exit_code
            
            if exit_code == 0:
                print("\n✅ Startup completed successfully")
                self.logger.info("Startup successful", exit_code=exit_code)
                if not self.metrics['final_status']:
                    self.metrics['final_status'] = 'success'
                return True, "Success"
            else:
                print(f"\n❌ Startup failed with exit code: {exit_code}")
                self.logger.error("Startup failed", exit_code=exit_code)
                self.metrics['final_status'] = 'failed'
                
                # Extract error from output
                error_msg = "Unknown error"
                for line in reversed(output_lines):
                    if "error" in line.lower() or "failed" in line.lower():
                        error_msg = line
                        break
                
                return False, error_msg
                
        except Exception as e:
            self.logger.exception("Unexpected error during startup")
            self.metrics['final_status'] = 'error'
            return False, str(e)
        
        finally:
            self.end_time = time.time()
            self.metrics['startup_time'] = self.end_time - self.start_time
            self.resource_monitor_active = False
            
            # Ensure process is terminated
            if self.process and self.process.poll() is None:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
    
    def analyze_results(self) -> dict:
        """Analyze test results and generate report"""
        self.logger.info("Analyzing test results")
        
        # Get log monitor summary
        monitor_summary = {}
        if self.monitor:
            try:
                monitor_summary = self.monitor.get_summary()
            except:
                pass
        
        # Analyze performance
        performance_analysis = {
            'startup_speed': 'fast' if self.metrics['startup_time'] < 30 else 'slow',
            'memory_usage': 'low' if self.metrics['peak_memory_mb'] < 500 else 'high',
            'retry_needed': self.metrics['retry_attempts'] > 0,
            'all_instances_started': self.metrics['chrome_instances_started'] >= 2
        }
        
        # Generate recommendations
        recommendations = []
        
        if self.metrics['startup_time'] > 60:
            recommendations.append("Startup time is slow - consider optimizing Chrome launch")
        
        if self.metrics['retry_attempts'] > 0:
            recommendations.append(f"Startup required {self.metrics['retry_attempts']} retries - investigate stability")
        
        if monitor_summary.get('errors', 0) > 0:
            recommendations.append(f"Found {monitor_summary['errors']} errors in logs - review for issues")
        
        if self.metrics['peak_memory_mb'] > 1000:
            recommendations.append("High memory usage detected - monitor for resource constraints")
        
        # Build comprehensive report
        report = {
            'test_id': self.test_id,
            'timestamp': datetime.now().isoformat(),
            'success': self.metrics['final_status'] == 'success',
            'metrics': self.metrics,
            'performance_analysis': performance_analysis,
            'log_summary': monitor_summary,
            'recommendations': recommendations,
            'environment': {
                'platform': sys.platform,
                'python_version': sys.version.split()[0],
                'available_memory_gb': psutil.virtual_memory().available / (1024**3),
                'cpu_count': psutil.cpu_count()
            }
        }
        
        return report
    
    def save_test_report(self, report: dict):
        """Save comprehensive test report"""
        report_file = f"logs/test/startup_test_report_{self.test_id}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("Test report saved", report_file=report_file)
        
        # Also create a summary report
        summary_file = f"test_summary_{self.test_id}.txt"
        with open(summary_file, 'w') as f:
            f.write("ENHANCED STARTUP TEST SUMMARY\n")
            f.write("="*60 + "\n\n")
            f.write(f"Test ID: {self.test_id}\n")
            f.write(f"Status: {report['success'] and 'PASSED' or 'FAILED'}\n")
            f.write(f"Duration: {report['metrics']['startup_time']:.2f} seconds\n")
            f.write(f"Chrome Instances: {report['metrics']['chrome_instances_started']}\n")
            f.write(f"Retry Attempts: {report['metrics']['retry_attempts']}\n")
            f.write(f"Peak Memory: {report['metrics']['peak_memory_mb']:.1f} MB\n")
            f.write(f"Exit Code: {report['metrics']['exit_code']}\n")
            
            if report['recommendations']:
                f.write("\nRecommendations:\n")
                for rec in report['recommendations']:
                    f.write(f"- {rec}\n")
        
        print(f"\n📄 Test report saved to: {report_file}")
        print(f"📋 Summary saved to: {summary_file}")
        
        return report_file
    
    def run_test(self, skip_validation: bool = False) -> bool:
        """Run the complete startup test"""
        print("\n" + "="*60)
        print("🧪 ENHANCED STARTUP TEST SUITE")
        print("="*60)
        
        try:
            # Step 1: Pre-test validation
            if not skip_validation:
                if not self.pre_test_validation():
                    print("\n❌ Pre-test validation failed")
                    return False
            
            # Step 2: Start monitoring
            print("\n📊 Starting log monitoring...")
            self.monitor = self.start_log_monitoring()
            time.sleep(2)  # Give monitors time to start
            
            # Step 3: Execute startup
            print("\n🚀 Executing startup test...")
            success, error_msg = self.execute_startup(timeout=120)
            
            # Step 4: Stop monitoring
            if self.monitor:
                self.monitor.stop()
            
            # Step 5: Analyze results
            print("\n📈 Analyzing results...")
            report = self.analyze_results()
            
            # Step 6: Save report
            self.save_test_report(report)
            
            # Display final summary
            print("\n" + "="*60)
            print("📊 TEST RESULTS")
            print("="*60)
            print(f"\nStatus: {'✅ PASSED' if success else '❌ FAILED'}")
            print(f"Duration: {self.metrics['startup_time']:.2f} seconds")
            print(f"Chrome Instances: {self.metrics['chrome_instances_started']}")
            print(f"Retries: {self.metrics['retry_attempts']}")
            
            if not success:
                print(f"\nFailure Reason: {error_msg}")
            
            if report['recommendations']:
                print("\n📌 Recommendations:")
                for rec in report['recommendations']:
                    print(f"  • {rec}")
            
            return success
            
        except Exception as e:
            self.logger.exception("Test execution failed")
            print(f"\n❌ Test failed with error: {e}")
            return False


def main():
    """Run enhanced startup test"""
    runner = StartupTestRunner()
    
    # Parse arguments
    skip_validation = "--skip-validation" in sys.argv
    
    # Run test
    success = runner.run_test(skip_validation=skip_validation)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()