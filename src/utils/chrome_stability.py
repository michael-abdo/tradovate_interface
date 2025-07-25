#!/usr/bin/env python3
"""
Chrome Stability Monitor - Detects and logs Chrome GPU/stability issues
"""
import os
import time
import datetime
import json
import logging
from typing import Dict, List, Optional
import subprocess
import re

class ChromeStabilityMonitor:
    """Monitor Chrome instances for GPU crashes and stability issues"""
    
    def __init__(self, log_dir: str = "logs/chrome_stability"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logging
        log_file = os.path.join(log_dir, f"chrome_stability_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # GPU error patterns to watch for
        self.gpu_error_patterns = [
            r"SharedImageManager",
            r"GPU process",
            r"gpu_memory_buffer",
            r"mailbox.*GPU",
            r"Failed to create shared image",
            r"GPU channel lost",
            r"Graphics pipeline error",
            r"WebGL.*lost context",
            r"GPU.*crashed",
            r"renderer.*crashed"
        ]
        
        # Chrome process tracking
        self.chrome_processes: Dict[int, dict] = {}
        
    def find_chrome_processes(self) -> List[dict]:
        """Find all Chrome processes with remote debugging enabled"""
        processes = []
        try:
            # Use ps to find Chrome processes
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'remote-debugging-port' in line and 'Google Chrome' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = int(parts[1])
                            # Extract port from command line
                            port_match = re.search(r'--remote-debugging-port=(\d+)', line)
                            port = int(port_match.group(1)) if port_match else None
                            
                            processes.append({
                                'pid': pid,
                                'port': port,
                                'command': ' '.join(parts[10:]),  # Command and args
                                'start_time': datetime.datetime.now()
                            })
            
            return processes
            
        except Exception as e:
            self.logger.error(f"Error finding Chrome processes: {e}")
            return []
    
    def check_system_logs_for_gpu_errors(self) -> List[str]:
        """Check system logs for GPU-related errors (macOS specific)"""
        errors = []
        try:
            # Check system log for Chrome GPU errors in the last hour
            cmd = [
                "log", "show",
                "--predicate", "process == 'Google Chrome' OR process == 'Google Chrome Helper'",
                "--last", "1h",
                "--style", "syslog"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    for pattern in self.gpu_error_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append(line.strip())
                            break
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error checking system logs: {e}")
            return []
    
    def analyze_chrome_stability(self) -> dict:
        """Analyze Chrome stability and return report"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'chrome_processes': [],
            'gpu_errors': [],
            'recommendations': []
        }
        
        # Find Chrome processes
        processes = self.find_chrome_processes()
        report['chrome_processes'] = processes
        
        # Check for GPU errors
        gpu_errors = self.check_system_logs_for_gpu_errors()
        report['gpu_errors'] = gpu_errors
        
        # Generate recommendations based on findings
        if gpu_errors:
            report['recommendations'].append(
                "GPU errors detected. Chrome has been configured with GPU workaround flags."
            )
            report['recommendations'].append(
                "If crashes persist, try: 1) Update Chrome, 2) Update macOS, 3) Reset Chrome profile"
            )
        
        if len(processes) > 5:
            report['recommendations'].append(
                f"High number of Chrome processes ({len(processes)}). Consider reducing concurrent instances."
            )
        
        # Log the report
        # Convert datetime objects to strings for JSON serialization
        report_json = json.dumps(report, indent=2, default=str)
        self.logger.info(f"Stability report: {report_json}")
        
        # Save report to file
        report_file = os.path.join(self.log_dir, f"stability_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def monitor_chrome_logs(self, tab, callback=None):
        """Monitor Chrome console logs for GPU errors"""
        def log_handler(entry):
            """Handle log entries from Chrome"""
            if entry.get('level', '').upper() in ['ERROR', 'WARNING']:
                text = entry.get('text', '')
                
                # Check for GPU-related errors
                for pattern in self.gpu_error_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        self.logger.error(f"GPU Error detected: {text}")
                        
                        # Save to error log
                        error_file = os.path.join(self.log_dir, "gpu_errors.log")
                        with open(error_file, 'a') as f:
                            f.write(f"{datetime.datetime.now().isoformat()} - {text}\n")
                        
                        if callback:
                            callback('gpu_error', entry)
                        break
        
        return log_handler
    
    def get_chrome_memory_usage(self, pid: int) -> Optional[dict]:
        """Get memory usage for a Chrome process"""
        try:
            cmd = ["ps", "-o", "pid,vsz,rss,comm", "-p", str(pid)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    return {
                        'pid': int(parts[0]),
                        'vsz_kb': int(parts[1]),
                        'rss_kb': int(parts[2]),
                        'vsz_mb': int(parts[1]) / 1024,
                        'rss_mb': int(parts[2]) / 1024
                    }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting memory usage for PID {pid}: {e}")
            return None
    
    def create_stability_report(self) -> str:
        """Create a comprehensive stability report"""
        report = self.analyze_chrome_stability()
        
        # Add memory usage information
        for process in report['chrome_processes']:
            memory = self.get_chrome_memory_usage(process['pid'])
            if memory:
                process['memory'] = memory
        
        # Format report for display
        report_text = f"""
Chrome Stability Report - {report['timestamp']}
{'=' * 60}

Active Chrome Processes: {len(report['chrome_processes'])}
"""
        
        for proc in report['chrome_processes']:
            report_text += f"\n  PID: {proc['pid']}, Port: {proc['port']}"
            if 'memory' in proc:
                report_text += f", Memory: {proc['memory']['rss_mb']:.1f} MB"
        
        if report['gpu_errors']:
            report_text += f"\n\nGPU Errors Found: {len(report['gpu_errors'])}\n"
            report_text += "Recent GPU errors:\n"
            for error in report['gpu_errors'][:5]:  # Show first 5
                report_text += f"  - {error[:100]}...\n"
        else:
            report_text += "\n\nNo GPU errors detected in system logs."
        
        if report['recommendations']:
            report_text += "\n\nRecommendations:\n"
            for rec in report['recommendations']:
                report_text += f"  • {rec}\n"
        
        report_text += "\n" + "=" * 60
        
        return report_text


def main():
    """Run stability check as standalone tool"""
    monitor = ChromeStabilityMonitor()
    print(monitor.create_stability_report())
    
    # Save detailed report
    report = monitor.analyze_chrome_stability()
    print(f"\nDetailed report saved to: {monitor.log_dir}")
    
    if report['gpu_errors']:
        print("\n⚠️  GPU errors detected! Chrome may be experiencing stability issues.")
        print("The Chrome launch parameters have been updated with GPU workarounds.")
    else:
        print("\n✅ No GPU errors detected in recent logs.")


if __name__ == "__main__":
    main()