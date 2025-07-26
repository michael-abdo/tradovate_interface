#!/usr/bin/env python3
"""
Real-time log monitoring for startup process
Monitors multiple log files simultaneously and provides live updates
"""

import os
import sys
import time
import json
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import select
from collections import deque

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from structured_logger import get_logger


class LogMonitor:
    """Monitors multiple log files in real-time"""
    
    def __init__(self):
        self.logger = get_logger("log_monitor", log_file="test/log_monitor.log")
        self.active = True
        self.threads = []
        self.events = deque(maxlen=1000)  # Keep last 1000 events
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.startup_phases = {}
        self.phase_lock = threading.Lock()
        
    def monitor_json_log(self, log_file: str, label: str):
        """Monitor a JSON-formatted log file"""
        self.logger.info(f"Starting JSON monitor for {label}", log_file=log_file)
        
        # Ensure file exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        if not os.path.exists(log_file):
            Path(log_file).touch()
        
        # Use tail -f for real-time monitoring
        try:
            process = subprocess.Popen(
                ['tail', '-f', log_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while self.active:
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                try:
                    # Parse JSON log entry
                    entry = json.loads(line.strip())
                    self.process_log_entry(entry, label)
                except json.JSONDecodeError:
                    # Not JSON, might be plain text
                    if line.strip():
                        self.process_text_line(line.strip(), label)
                except Exception as e:
                    self.logger.error(f"Error processing log line: {e}")
            
            process.terminate()
            
        except Exception as e:
            self.logger.error(f"Error monitoring {label}", error=str(e))
    
    def monitor_text_log(self, log_file: str, label: str):
        """Monitor a plain text log file"""
        self.logger.info(f"Starting text monitor for {label}", log_file=log_file)
        
        # Ensure file exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        if not os.path.exists(log_file):
            Path(log_file).touch()
        
        try:
            process = subprocess.Popen(
                ['tail', '-f', log_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while self.active:
                line = process.stdout.readline()
                if line:
                    self.process_text_line(line.strip(), label)
                else:
                    time.sleep(0.1)
            
            process.terminate()
            
        except Exception as e:
            self.logger.error(f"Error monitoring {label}", error=str(e))
    
    def process_log_entry(self, entry: dict, source: str):
        """Process a JSON log entry"""
        timestamp = entry.get('timestamp', datetime.now().isoformat())
        level = entry.get('level', 'INFO')
        message = entry.get('message', '')
        logger_name = entry.get('logger', source)
        
        # Update counters
        if level == 'ERROR':
            self.error_count += 1
            color = '\033[91m'  # Red
            symbol = '❌'
        elif level == 'WARNING':
            self.warning_count += 1
            color = '\033[93m'  # Yellow
            symbol = '⚠️'
        else:
            self.info_count += 1
            color = '\033[92m'  # Green
            symbol = '✓'
        
        # Track startup phases
        if 'event_type' in entry or 'phase' in entry:
            phase = entry.get('event_type') or entry.get('phase')
            with self.phase_lock:
                self.startup_phases[phase] = {
                    'status': 'completed' if entry.get('success', True) else 'failed',
                    'timestamp': timestamp,
                    'details': entry
                }
        
        # Format and display
        reset = '\033[0m'
        output = f"{color}[{timestamp[:19]}] {symbol} [{logger_name}] {message}{reset}"
        
        # Add extra details for important events
        if level == 'ERROR' or 'startup' in message.lower():
            for key, value in entry.items():
                if key not in ['timestamp', 'level', 'message', 'logger']:
                    output += f"\n    {key}: {value}"
        
        print(output)
        
        # Store event
        self.events.append({
            'timestamp': timestamp,
            'source': source,
            'level': level,
            'message': message,
            'details': entry
        })
    
    def process_text_line(self, line: str, source: str):
        """Process a plain text log line"""
        if not line:
            return
        
        # Simple pattern matching for log levels
        level = 'INFO'
        if 'ERROR' in line or 'FAIL' in line:
            level = 'ERROR'
            self.error_count += 1
        elif 'WARNING' in line or 'WARN' in line:
            level = 'WARNING'
            self.warning_count += 1
        else:
            self.info_count += 1
        
        # Color coding
        colors = {
            'ERROR': '\033[91m',
            'WARNING': '\033[93m',
            'INFO': '\033[92m'
        }
        
        color = colors.get(level, '')
        reset = '\033[0m'
        
        print(f"{color}[{source}] {line}{reset}")
        
        # Store event
        self.events.append({
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'level': level,
            'message': line
        })
    
    def start_monitoring(self, log_configs: List[Dict[str, str]]):
        """Start monitoring multiple log files"""
        print("\n" + "="*60)
        print("📊 REAL-TIME LOG MONITORING")
        print("="*60)
        print("\nMonitoring the following logs:")
        
        for config in log_configs:
            log_file = config['file']
            label = config['label']
            log_type = config.get('type', 'json')
            
            print(f"  • {label}: {log_file}")
            
            if log_type == 'json':
                thread = threading.Thread(
                    target=self.monitor_json_log,
                    args=(log_file, label),
                    daemon=True
                )
            else:
                thread = threading.Thread(
                    target=self.monitor_text_log,
                    args=(log_file, label),
                    daemon=True
                )
            
            thread.start()
            self.threads.append(thread)
        
        print("\n" + "-"*60)
        print("Log output will appear below (Press Ctrl+C to stop):")
        print("-"*60 + "\n")
    
    def get_summary(self) -> dict:
        """Get monitoring summary"""
        return {
            'total_events': len(self.events),
            'errors': self.error_count,
            'warnings': self.warning_count,
            'info': self.info_count,
            'startup_phases': dict(self.startup_phases),
            'monitoring_duration': None  # Will be calculated on stop
        }
    
    def stop(self):
        """Stop monitoring"""
        self.active = False
        for thread in self.threads:
            thread.join(timeout=1)
        
        # Display summary
        print("\n" + "="*60)
        print("📊 MONITORING SUMMARY")
        print("="*60)
        
        summary = self.get_summary()
        print(f"\nTotal Events: {summary['total_events']}")
        print(f"  ✓ Info: {summary['info']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ❌ Errors: {summary['errors']}")
        
        if self.startup_phases:
            print("\nStartup Phases:")
            for phase, info in self.startup_phases.items():
                status_symbol = "✓" if info['status'] == 'completed' else "✗"
                print(f"  {status_symbol} {phase}: {info['status']}")
        
        # Save detailed report
        report_file = f"logs/test/monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                'summary': summary,
                'events': list(self.events)
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return summary


def monitor_startup_test():
    """Monitor logs during startup test"""
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
            'file': 'logs/operations/file_ops.log',
            'label': 'FileOps',
            'type': 'json'
        },
        {
            'file': 'logs/chrome_cleanup/cleanup.log',
            'label': 'ChromeCleanup',
            'type': 'text'
        },
        {
            'file': 'tradovate_interface/logs/chrome_monitor.log',
            'label': 'ChromeMonitor',
            'type': 'text'
        }
    ]
    
    try:
        monitor.start_monitoring(log_configs)
        
        # Keep monitoring until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        return monitor.stop()


if __name__ == "__main__":
    monitor_startup_test()