#!/usr/bin/env python3
"""
Webhook Monitoring Script

This script continuously monitors the webhook service and logs its status.
It can also send notifications if the service goes down.
"""
import requests
import time
import sys
import os
import logging
import argparse
import subprocess
import json
import datetime
from typing import Dict, Any, Optional

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up logging
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'webhook_monitor_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('webhook_monitor')

class WebhookMonitor:
    def __init__(self, url: str = "http://localhost:6000/health", check_interval: int = 60, 
                 restart_script: Optional[str] = None, notify: bool = False):
        """
        Initialize the webhook monitor
        
        Args:
            url: URL to the health check endpoint
            check_interval: How often to check the service (in seconds)
            restart_script: Optional path to script that restarts the service
            notify: Whether to send system notifications
        """
        self.url = url
        self.check_interval = check_interval
        self.restart_script = restart_script
        self.notify = notify
        self.last_status = None
        self.last_connections = 0
        self.downtime_start = None
        
    def send_notification(self, title: str, message: str) -> None:
        """Send a system notification"""
        if not self.notify:
            return
            
        try:
            # macOS
            if sys.platform == 'darwin':
                os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
            # Linux with notify-send
            elif sys.platform.startswith('linux'):
                os.system(f'notify-send "{title}" "{message}"')
            # Windows
            elif sys.platform == 'win32':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=10)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def check_health(self) -> Dict[str, Any]:
        """Check the health of the webhook service"""
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Health check returned status code {response.status_code}")
                return {"status": "error", "message": f"Status code: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def restart_service(self) -> bool:
        """Attempt to restart the webhook service"""
        if not self.restart_script:
            logger.warning("No restart script provided, cannot restart service")
            return False
            
        try:
            logger.info(f"Attempting to restart service with script: {self.restart_script}")
            result = subprocess.run([self.restart_script], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Service restart successful")
                return True
            else:
                logger.error(f"Service restart failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            return False
    
    def run(self) -> None:
        """Run the monitor continuously"""
        logger.info(f"Starting webhook monitor, checking {self.url} every {self.check_interval} seconds")
        
        try:
            while True:
                health_data = self.check_health()
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Check if service is running
                if health_data.get("status") == "ok":
                    connections = health_data.get("connections", 0)
                    live_connections = health_data.get("live_connections", 0)
                    
                    if self.last_status != "ok":
                        # Service just came back online
                        if self.last_status is not None:
                            downtime = ""
                            if self.downtime_start:
                                downtime_duration = datetime.datetime.now() - self.downtime_start
                                downtime = f" after {downtime_duration.total_seconds():.1f} seconds of downtime"
                            
                            message = f"Webhook service is back online{downtime}"
                            logger.info(message)
                            self.send_notification("Webhook Service Restored", message)
                            self.downtime_start = None
                        else:
                            # First check, service is online
                            logger.info("Webhook service is online")
                            
                    # Check if connection count changed
                    if connections != self.last_connections:
                        logger.info(f"Connection count changed: {self.last_connections} -> {connections}")
                    
                    # Log periodic health status
                    logger.info(f"[{current_time}] Health check: OK | Connections: {connections} | Live connections: {live_connections}")
                    self.last_status = "ok"
                    self.last_connections = connections
                    
                else:
                    # Service is down or has errors
                    error_msg = health_data.get("message", "Unknown error")
                    
                    if self.last_status == "ok" or self.last_status is None:
                        # Service just went down
                        message = f"Webhook service is DOWN: {error_msg}"
                        logger.error(message)
                        self.send_notification("Webhook Service DOWN", message)
                        self.downtime_start = datetime.datetime.now()
                        
                        # Try to restart the service
                        if self.restart_script:
                            restart_success = self.restart_service()
                            if restart_success:
                                self.send_notification("Webhook Service", "Restart attempt successful")
                            else:
                                self.send_notification("Webhook Service", "Restart attempt failed")
                    
                    # Log periodic error status
                    logger.error(f"[{current_time}] Health check: ERROR | {error_msg}")
                    self.last_status = "error"
                
                # Wait for the next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            self.send_notification("Webhook Monitor Error", str(e))

def main():
    """Parse arguments and start the monitor"""
    parser = argparse.ArgumentParser(description="Monitor the webhook service")
    parser.add_argument("--url", default="http://localhost:6000/health", help="URL to the health check endpoint")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--restart", help="Path to script that restarts the service")
    parser.add_argument("--notify", action="store_true", help="Send system notifications")
    args = parser.parse_args()
    
    monitor = WebhookMonitor(
        url=args.url,
        check_interval=args.interval,
        restart_script=args.restart,
        notify=args.notify
    )
    
    monitor.run()

if __name__ == "__main__":
    main()