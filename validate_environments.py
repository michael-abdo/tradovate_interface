#!/usr/bin/env python3
"""
Environment configuration validation test
Run this with different TRADOVATE_ENV values to validate configuration loading
"""

import sys
import os

# Add paths
sys.path.insert(0, 'src')
sys.path.insert(0, 'tradovate_interface/src')

def validate_environment(env_name):
    """Validate configuration for specific environment"""
    print(f"Validating {env_name} environment...")
    
    os.environ['TRADOVATE_ENV'] = env_name
    
    from utils.process_monitor import ChromeProcessMonitor
    
    monitor = ChromeProcessMonitor()
    config = monitor.config
    startup_config = config.get('startup_monitoring', {})
    
    print(f"  Environment: {monitor.environment}")
    print(f"  Check interval: {config.get('check_interval')}s")
    print(f"  Log level: {config.get('log_level')}")
    print(f"  Startup enabled: {startup_config.get('enabled')}")
    
    resource_limits = startup_config.get('resource_limits', {})
    print(f"  Memory limit: {resource_limits.get('max_memory_mb')}MB")
    print(f"  CPU limit: {resource_limits.get('max_cpu_percent')}%")
    print(f"  Concurrent limit: {resource_limits.get('max_concurrent_startups')}")
    print()

if __name__ == "__main__":
    for env in ['development', 'staging', 'production']:
        validate_environment(env)
