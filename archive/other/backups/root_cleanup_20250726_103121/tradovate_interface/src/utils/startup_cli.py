#!/usr/bin/env python3
"""
Startup Monitoring CLI Utilities
Provides command-line interface for startup monitoring operations
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Add project path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
    MONITORING_AVAILABLE = True
except ImportError:
    print("Error: Process monitor not available. Make sure you're running from the correct directory.")
    MONITORING_AVAILABLE = False
    sys.exit(1)

class StartupMonitoringCLI:
    """Command-line interface for startup monitoring operations"""
    
    def __init__(self):
        self.monitor = None
        self._init_monitor()
    
    def _init_monitor(self):
        """Initialize the process monitor"""
        try:
            self.monitor = ChromeProcessMonitor()
        except Exception as e:
            print(f"Error initializing process monitor: {e}")
            sys.exit(1)
    
    def status(self, args):
        """Show startup monitoring status"""
        print("🔍 Startup Monitoring Status")
        print("=" * 50)
        
        try:
            status = self.monitor.get_status()
            startup_monitoring = status.get('startup_monitoring', {})
            
            # General status
            print(f"Regular monitoring active: {status.get('monitoring_active', False)}")
            print(f"Startup monitoring active: {startup_monitoring.get('monitoring_active', False)}")
            print(f"Startup monitoring mode: {startup_monitoring.get('mode', 'unknown')}")
            
            # Configuration
            config = startup_monitoring.get('configuration', {})
            if config:
                print(f"\nConfiguration:")
                print(f"  Timeout: {config.get('timeout_seconds', 'unknown')}s")
                print(f"  Max attempts: {config.get('max_attempts', 'unknown')}")
                print(f"  Check interval: {config.get('check_interval', 'unknown')}s")
                
                resource_limits = config.get('resource_limits', {})
                if resource_limits:
                    print(f"  Resource limits:")
                    print(f"    Memory: {resource_limits.get('max_memory_mb', 'unknown')}MB")
                    print(f"    CPU: {resource_limits.get('max_cpu_percent', 'unknown')}%")
                    print(f"    Max concurrent: {resource_limits.get('max_concurrent_startups', 'unknown')}")
            
            # Startup processes
            startup_processes = startup_monitoring.get('startup_processes', {})
            if startup_processes:
                print(f"\nStartup processes ({len(startup_processes)}):")
                for account_name, process_info in startup_processes.items():
                    phase = process_info.get('phase', 'unknown')
                    duration = process_info.get('duration_seconds', 0)
                    attempts = process_info.get('attempts', 0)
                    is_timeout = process_info.get('is_timeout', False)
                    
                    status_icon = "⏱️" if is_timeout else "✅" if phase == "ready" else "🔄"
                    print(f"  {status_icon} {account_name}:")
                    print(f"    Phase: {phase}")
                    print(f"    Duration: {duration:.2f}s")
                    print(f"    Attempts: {attempts}")
                    if is_timeout:
                        print(f"    ⚠️  TIMEOUT")
            else:
                print("\nNo startup processes currently registered")
            
            # Health summary
            health_summary = startup_monitoring.get('health_summary', {})
            if health_summary and health_summary.get('total_processes', 0) > 0:
                print(f"\nHealth Summary:")
                print(f"  Total processes: {health_summary.get('total_processes', 0)}")
                print(f"  Healthy: {health_summary.get('healthy_count', 0)}")
                print(f"  Warnings: {health_summary.get('warning_count', 0)}")
                print(f"  Errors: {health_summary.get('error_count', 0)}")
                print(f"  Average startup time: {health_summary.get('average_startup_time', 0):.2f}s")
                
                # Phase distribution
                phase_dist = health_summary.get('phase_distribution', {})
                if phase_dist:
                    print(f"  Phase distribution:")
                    for phase, count in phase_dist.items():
                        print(f"    {phase}: {count}")
                
                # Recent issues
                recent_issues = health_summary.get('recent_issues', [])
                if recent_issues:
                    print(f"  Recent issues:")
                    for issue in recent_issues[:5]:  # Show last 5
                        print(f"    - {issue}")
            
        except Exception as e:
            print(f"Error getting status: {e}")
            return 1
        
        return 0
    
    def enable(self, args):
        """Enable startup monitoring"""
        mode = args.mode.upper()
        
        try:
            monitoring_mode = StartupMonitoringMode(mode.lower())
        except ValueError:
            print(f"Error: Invalid mode '{mode}'. Valid modes: disabled, passive, active")
            return 1
        
        try:
            self.monitor.enable_startup_monitoring(monitoring_mode)
            print(f"✅ Startup monitoring enabled in {mode} mode")
            
            if mode == "ACTIVE":
                print("⚠️  ACTIVE mode will automatically restart failed Chrome processes")
            elif mode == "PASSIVE":
                print("ℹ️  PASSIVE mode will monitor but not restart failed processes")
            
            return 0
        except Exception as e:
            print(f"Error enabling startup monitoring: {e}")
            return 1
    
    def disable(self, args):
        """Disable startup monitoring"""
        try:
            self.monitor.enable_startup_monitoring(StartupMonitoringMode.DISABLED)
            print("✅ Startup monitoring disabled")
            return 0
        except Exception as e:
            print(f"Error disabling startup monitoring: {e}")
            return 1
    
    def register(self, args):
        """Register a process for startup monitoring"""
        account_name = args.account
        port = args.port
        
        # SAFETY: Never register port 9222
        if port == 9222:
            print("❌ Error: Cannot register port 9222 - this port is protected")
            return 1
        
        try:
            success = self.monitor.register_for_startup_monitoring(account_name, port)
            if success:
                print(f"✅ Registered {account_name} for startup monitoring on port {port}")
                return 0
            else:
                print(f"❌ Failed to register {account_name}")
                return 1
        except Exception as e:
            print(f"Error registering process: {e}")
            return 1
    
    def health(self, args):
        """Show startup health information"""
        print("🏥 Startup Health Check")
        print("=" * 50)
        
        try:
            if args.account:
                # Individual health check
                health_status = self.monitor.startup_health_check(args.account)
                self._print_health_status(args.account, health_status)
            else:
                # Batch health check
                batch_results = self.monitor.batch_startup_health_check()
                
                print(f"Total processes: {batch_results.get('total_startup_processes', 0)}")
                print(f"Healthy: {batch_results.get('healthy_processes', 0)}")
                print(f"Unhealthy: {batch_results.get('unhealthy_processes', 0)}")
                print()
                
                processes = batch_results.get('processes', {})
                for account_name, health_status in processes.items():
                    self._print_health_status(account_name, health_status)
                    print()
            
            return 0
        except Exception as e:
            print(f"Error checking health: {e}")
            return 1
    
    def _print_health_status(self, account_name: str, health_status: Dict):
        """Print detailed health status for an account"""
        healthy = health_status.get('healthy', False)
        phase = health_status.get('startup_phase', 'unknown')
        
        health_icon = "✅" if healthy else "❌"
        print(f"{health_icon} {account_name} ({phase})")
        
        # Metrics
        metrics = health_status.get('metrics', {})
        if metrics:
            elapsed = metrics.get('elapsed_time_seconds', 0)
            attempts = metrics.get('launch_attempts', 0)
            print(f"  Duration: {elapsed:.2f}s, Attempts: {attempts}")
            
            if 'system_cpu_percent' in metrics:
                cpu = metrics['system_cpu_percent']
                memory = metrics['system_memory_percent']
                print(f"  System: CPU {cpu:.1f}%, Memory {memory:.1f}%")
        
        # Checks
        checks = health_status.get('checks', {})
        if checks:
            passed_checks = sum(1 for check in checks.values() if check)
            total_checks = len(checks)
            print(f"  Checks: {passed_checks}/{total_checks} passed")
            
            for check_name, result in checks.items():
                check_icon = "✅" if result else "❌"
                print(f"    {check_icon} {check_name}")
        
        # Warnings
        warnings = health_status.get('warnings', [])
        if warnings:
            print(f"  Warnings:")
            for warning in warnings:
                print(f"    ⚠️  {warning}")
        
        # Errors
        errors = health_status.get('errors', [])
        if errors:
            print(f"  Errors:")
            for error in errors:
                print(f"    ❌ {error}")
    
    def clear(self, args):
        """Clear completed startup processes"""
        print("🧹 Clearing completed startup processes...")
        
        try:
            # Get current startup processes
            with self.monitor.startup_lock:
                startup_processes = getattr(self.monitor, 'startup_processes', {})
                completed_count = 0
                accounts_to_remove = []
                
                for account_name, startup_info in startup_processes.items():
                    if startup_info.current_phase == StartupPhase.READY:
                        accounts_to_remove.append(account_name)
                        completed_count += 1
                
                # Remove completed processes
                for account_name in accounts_to_remove:
                    del startup_processes[account_name]
                    print(f"  ✅ Cleared {account_name}")
            
            print(f"✅ Cleared {completed_count} completed startup processes")
            return 0
            
        except Exception as e:
            print(f"Error clearing processes: {e}")
            return 1
    
    def logs(self, args):
        """Show startup monitoring logs"""
        print("📋 Startup Monitoring Logs")
        print("=" * 50)
        
        try:
            # Try to read log files
            log_dir = "logs"
            if not os.path.exists(log_dir):
                print("No log directory found")
                return 1
            
            # Find Chrome monitor logs
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.startswith('chrome_monitor_') and filename.endswith('.log'):
                    log_files.append(os.path.join(log_dir, filename))
            
            if not log_files:
                print("No Chrome monitor log files found")
                return 1
            
            # Show most recent log file
            latest_log = max(log_files, key=os.path.getctime)
            print(f"Showing logs from: {latest_log}")
            print()
            
            lines_to_show = args.lines if args.lines else 50
            
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                
                # Show last N lines
                for line in lines[-lines_to_show:]:
                    line = line.strip()
                    if 'startup' in line.lower() or 'phase' in line.lower():
                        # Highlight startup-related logs
                        print(f"🔄 {line}")
                    elif 'error' in line.lower():
                        print(f"❌ {line}")
                    elif 'warning' in line.lower():
                        print(f"⚠️  {line}")
                    else:
                        print(f"ℹ️  {line}")
            
            return 0
            
        except Exception as e:
            print(f"Error reading logs: {e}")
            return 1
    
    def validate(self, args):
        """Validate startup monitoring configuration"""
        print("✅ Startup Monitoring Configuration Validation")
        print("=" * 50)
        
        try:
            # Check configuration
            config = self.monitor.startup_config
            
            print("Configuration checks:")
            
            # Check timeout settings
            timeout = config.get('startup_timeout_seconds', 60)
            if timeout < 30:
                print("  ⚠️  Timeout too short (< 30s), may cause false failures")
            elif timeout > 300:
                print("  ⚠️  Timeout very long (> 300s), may delay failure detection")
            else:
                print(f"  ✅ Timeout setting appropriate: {timeout}s")
            
            # Check resource limits
            resource_limits = config.get('resource_limits', {})
            max_memory = resource_limits.get('max_memory_mb', 1000)
            max_cpu = resource_limits.get('max_cpu_percent', 50)
            
            if max_memory < 500:
                print("  ⚠️  Memory limit very low (< 500MB)")
            elif max_memory > 4000:
                print("  ⚠️  Memory limit very high (> 4GB)")
            else:
                print(f"  ✅ Memory limit appropriate: {max_memory}MB")
            
            if max_cpu < 25:
                print("  ⚠️  CPU limit very low (< 25%)")
            elif max_cpu > 80:
                print("  ⚠️  CPU limit very high (> 80%)")
            else:
                print(f"  ✅ CPU limit appropriate: {max_cpu}%")
            
            # Check monitoring capabilities
            print("\nMonitoring capabilities:")
            
            if hasattr(self.monitor, 'startup_processes'):
                print("  ✅ Startup process tracking available")
            else:
                print("  ❌ Startup process tracking not available")
            
            if hasattr(self.monitor, 'startup_health_check'):
                print("  ✅ Health checking available")
            else:
                print("  ❌ Health checking not available")
            
            if hasattr(self.monitor, 'startup_monitoring_thread'):
                print("  ✅ Background monitoring available")
            else:
                print("  ❌ Background monitoring not available")
            
            # Check system requirements
            print("\nSystem requirements:")
            
            try:
                import psutil
                print("  ✅ psutil available for resource monitoring")
                
                # Check system resources
                cpu_count = psutil.cpu_count()
                memory_gb = psutil.virtual_memory().total / (1024**3)
                
                print(f"  ℹ️  System: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
                
                if cpu_count < 2:
                    print("  ⚠️  Low CPU count may impact monitoring performance")
                
                if memory_gb < 4:
                    print("  ⚠️  Low memory may impact monitoring capabilities")
                    
            except ImportError:
                print("  ⚠️  psutil not available - resource monitoring limited")
            
            print("\n✅ Configuration validation complete")
            return 0
            
        except Exception as e:
            print(f"Error validating configuration: {e}")
            return 1

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Startup Monitoring CLI Utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                          # Show current status
  %(prog)s enable --mode passive           # Enable in passive mode
  %(prog)s register --account "Test" --port 9223  # Register process
  %(prog)s health --account "Test"         # Check specific account health
  %(prog)s health                          # Check all accounts health
  %(prog)s clear                           # Clear completed processes
  %(prog)s logs --lines 100                # Show last 100 log lines
  %(prog)s validate                        # Validate configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show startup monitoring status')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable startup monitoring')
    enable_parser.add_argument('--mode', required=True, choices=['disabled', 'passive', 'active'],
                              help='Monitoring mode')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable startup monitoring')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register process for startup monitoring')
    register_parser.add_argument('--account', required=True, help='Account name')
    register_parser.add_argument('--port', type=int, required=True, help='Chrome debugging port')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check startup health')
    health_parser.add_argument('--account', help='Specific account to check (optional)')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear completed startup processes')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show startup monitoring logs')
    logs_parser.add_argument('--lines', type=int, help='Number of log lines to show (default: 50)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate startup monitoring configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if not MONITORING_AVAILABLE:
        print("Error: Startup monitoring not available")
        return 1
    
    cli = StartupMonitoringCLI()
    
    # Route to appropriate command handler
    command_handlers = {
        'status': cli.status,
        'enable': cli.enable,
        'disable': cli.disable,
        'register': cli.register,
        'health': cli.health,
        'clear': cli.clear,
        'logs': cli.logs,
        'validate': cli.validate
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())