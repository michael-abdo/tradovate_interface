#!/usr/bin/env python3

import psutil
import time
import json
from datetime import datetime
from pathlib import Path

class SystemMonitor:
    def __init__(self, log_dir="logs/system_metrics"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
    def get_chrome_processes(self):
        """Find all Chrome processes related to trading"""
        chrome_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                if 'chrome' in proc.info['name'].lower() or 'chromium' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'remote-debugging-port' in cmdline:
                        chrome_procs.append({
                            'pid': proc.info['pid'],
                            'port': self._extract_port(cmdline),
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                            'cpu_percent': proc.cpu_percent(interval=0.1)
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return chrome_procs
    
    def _extract_port(self, cmdline):
        """Extract debugging port from command line"""
        if '--remote-debugging-port=' in cmdline:
            port_str = cmdline.split('--remote-debugging-port=')[1].split()[0]
            return int(port_str)
        return None
    
    def get_system_metrics(self):
        """Get overall system metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'cores': psutil.cpu_count(logical=True),
                'per_core': psutil.cpu_percent(interval=1, percpu=True)
            },
            'memory': {
                'total_gb': psutil.virtual_memory().total / 1024**3,
                'available_gb': psutil.virtual_memory().available / 1024**3,
                'used_gb': psutil.virtual_memory().used / 1024**3,
                'percent': psutil.virtual_memory().percent
            },
            'chrome_instances': self.get_chrome_processes()
        }
    
    def monitor_continuous(self, interval=5, duration=None):
        """Monitor system resources continuously"""
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print("SYSTEM RESOURCE MONITOR - TRADOVATE MULTI-ACCOUNT")
        print(f"{'='*60}\n")
        
        try:
            while True:
                if duration and (time.time() - start_time) > duration:
                    break
                    
                metrics = self.get_system_metrics()
                
                # Display summary
                print(f"\n[{metrics['timestamp']}]")
                print(f"CPU Usage: {metrics['cpu']['percent']:.1f}%")
                print(f"Memory: {metrics['memory']['used_gb']:.1f}/{metrics['memory']['total_gb']:.1f} GB ({metrics['memory']['percent']:.1f}%)")
                
                chrome_count = len(metrics['chrome_instances'])
                if chrome_count > 0:
                    total_chrome_mem = sum(p['memory_mb'] for p in metrics['chrome_instances'])
                    print(f"\nChrome Instances: {chrome_count}")
                    print(f"Total Chrome Memory: {total_chrome_mem:.1f} MB")
                    
                    for proc in metrics['chrome_instances']:
                        port = proc['port'] or 'unknown'
                        print(f"  Port {port}: {proc['memory_mb']:.1f} MB, CPU: {proc['cpu_percent']:.1f}%")
                
                # Warnings
                if metrics['memory']['percent'] > 80:
                    print("\n⚠️  WARNING: Memory usage above 80%!")
                if metrics['cpu']['percent'] > 80:
                    print("⚠️  WARNING: CPU usage above 80%!")
                
                # Save to log
                log_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, 'a') as f:
                    f.write(json.dumps(metrics) + '\n')
                
                print("-" * 60)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            return self.analyze_session(start_time)
    
    def analyze_session(self, start_time):
        """Analyze metrics from the session"""
        duration = time.time() - start_time
        print(f"\nSession Duration: {duration/60:.1f} minutes")
        
        # Calculate scaling estimates
        chrome_instances = len(self.get_chrome_processes())
        if chrome_instances > 0:
            metrics = self.get_system_metrics()
            avg_mem_per_instance = sum(p['memory_mb'] for p in metrics['chrome_instances']) / chrome_instances
            
            print(f"\nScaling Estimates (based on current usage):")
            print(f"Average memory per account: {avg_mem_per_instance:.1f} MB")
            
            available_mem_gb = metrics['memory']['available_gb']
            max_additional_accounts = int((available_mem_gb * 1024) / avg_mem_per_instance)
            
            print(f"Available memory: {available_mem_gb:.1f} GB")
            print(f"Estimated additional accounts possible: {max_additional_accounts}")
            print(f"Total accounts with current + additional: {chrome_instances + max_additional_accounts}")
            
            # Recommendations
            print(f"\nRecommendations:")
            if max_additional_accounts < 20 - chrome_instances:
                print("⚠️  May need more RAM for 20+ accounts")
                print(f"   Recommended: {((20 * avg_mem_per_instance) / 1024):.1f} GB total RAM")
            else:
                print("✅ System should handle 20+ accounts with current resources")

if __name__ == "__main__":
    monitor = SystemMonitor()
    
    print("Starting resource monitoring...")
    print("Press Ctrl+C to stop and see analysis\n")
    
    monitor.monitor_continuous(interval=5)