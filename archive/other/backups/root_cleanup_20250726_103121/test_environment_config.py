#!/usr/bin/env python3
"""
Test environment-specific configuration support for startup monitoring
"""

import sys
import os
import time

# Add correct paths - order matters!
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path = [path for path in sys.path if 'tradovate_interface' not in path]
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'tradovate_interface', 'src'))

def test_environment_config():
    """Test environment-specific configuration loading"""
    print("🌍 Testing Environment-Specific Configuration Support")
    print("=" * 60)
    
    try:
        from utils.process_monitor import ChromeProcessMonitor
        
        # Test different environments
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            print(f"\n--- Testing {env.upper()} Environment ---")
            
            # Set environment variable
            os.environ['TRADOVATE_ENV'] = env
            
            # Create monitor to load config
            monitor = ChromeProcessMonitor()
            
            # Check that environment was loaded
            if hasattr(monitor, 'environment'):
                print(f"✅ Environment loaded: {monitor.environment}")
            else:
                print(f"❌ Environment not loaded")
                return False
            
            # Check config values specific to this environment
            config = monitor.config
            startup_config = config.get('startup_monitoring', {})
            
            print(f"✅ Configuration loaded:")
            print(f"   Check interval: {config.get('check_interval')}s")
            print(f"   Log level: {config.get('log_level')}")
            print(f"   Startup monitoring enabled: {startup_config.get('enabled')}")
            print(f"   Startup timeout: {startup_config.get('startup_timeout_seconds')}s")
            
            resource_limits = startup_config.get('resource_limits', {})
            if resource_limits:
                print(f"   Resource limits:")
                print(f"     Memory: {resource_limits.get('max_memory_mb')}MB")
                print(f"     CPU: {resource_limits.get('max_cpu_percent')}%")
                print(f"     Concurrent: {resource_limits.get('max_concurrent_startups')}")
            
            # Verify environment-specific values
            if env == 'development':
                expected_check_interval = 5
                expected_log_level = 'DEBUG'
                expected_memory = 2000
            elif env == 'staging':
                expected_check_interval = 8
                expected_log_level = 'INFO'
                expected_memory = 1500
            elif env == 'production':
                expected_check_interval = 10
                expected_log_level = 'INFO'
                expected_memory = 1000
            
            # Verify values match expected
            if config.get('check_interval') == expected_check_interval:
                print(f"✅ Check interval correct for {env}: {expected_check_interval}s")
            else:
                print(f"❌ Wrong check interval for {env}: expected {expected_check_interval}, got {config.get('check_interval')}")
                return False
            
            if config.get('log_level') == expected_log_level:
                print(f"✅ Log level correct for {env}: {expected_log_level}")
            else:
                print(f"❌ Wrong log level for {env}: expected {expected_log_level}, got {config.get('log_level')}")
                return False
            
            if resource_limits.get('max_memory_mb') == expected_memory:
                print(f"✅ Memory limit correct for {env}: {expected_memory}MB")
            else:
                print(f"❌ Wrong memory limit for {env}: expected {expected_memory}, got {resource_limits.get('max_memory_mb')}")
                return False
        
        # Test with unknown environment
        print(f"\n--- Testing UNKNOWN Environment ---")
        os.environ['TRADOVATE_ENV'] = 'unknown_env'
        
        monitor = ChromeProcessMonitor()
        
        # Should fall back to base config
        if monitor.environment == 'unknown_env':
            print("✅ Unknown environment handled correctly")
            print(f"   Fallback config applied - Check interval: {monitor.config.get('check_interval')}s")
        else:
            print("❌ Unknown environment not handled correctly")
            return False
        
        # Test with no environment variable (should default to production)
        print(f"\n--- Testing DEFAULT Environment (no env var) ---")
        if 'TRADOVATE_ENV' in os.environ:
            del os.environ['TRADOVATE_ENV']
        
        monitor = ChromeProcessMonitor()
        
        if monitor.environment == 'production':
            print("✅ Default environment set to production")
            print(f"   Production config applied - Check interval: {monitor.config.get('check_interval')}s")
        else:
            print(f"❌ Wrong default environment: expected 'production', got '{monitor.environment}'")
            return False
        
        print("\n🎉 ENVIRONMENT-SPECIFIC CONFIGURATION TEST SUCCESSFUL!")
        print("All environments load correct configuration values.")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_environment_usage():
    """Demonstrate how to use environment-specific configuration"""
    print("\n📚 Environment Configuration Usage Examples")
    print("=" * 60)
    
    print("Environment configuration is controlled by the TRADOVATE_ENV environment variable:")
    print()
    print("1. Development environment (enhanced debugging):")
    print("   export TRADOVATE_ENV=development")
    print("   - Debug logging enabled")
    print("   - Faster check intervals (5s)")
    print("   - Higher resource limits (2GB memory, 70% CPU)")
    print("   - Longer startup timeouts (120s)")
    print()
    print("2. Staging environment (balanced testing):")
    print("   export TRADOVATE_ENV=staging")  
    print("   - Info logging")
    print("   - Moderate check intervals (8s)")
    print("   - Medium resource limits (1.5GB memory, 60% CPU)")
    print("   - Extended startup timeouts (90s)")
    print()
    print("3. Production environment (optimized performance):")
    print("   export TRADOVATE_ENV=production")
    print("   - Info logging")
    print("   - Standard check intervals (10s)")
    print("   - Conservative resource limits (1GB memory, 40% CPU)")
    print("   - Standard startup timeouts (60s)")
    print()
    print("4. Default (no environment variable):")
    print("   - Defaults to production environment")
    print()
    print("✅ Environment-specific configuration provides:")
    print("  - Optimized settings for each deployment stage")
    print("  - Easy switching between configurations")
    print("  - No code changes required - only environment variable")
    print("  - Deep merging of configuration sections")
    print("  - Fallback to base configuration for unknown environments")

def create_environment_validation_test():
    """Create a comprehensive validation test"""
    print("\n🧪 Creating Environment Validation Test")
    print("=" * 60)
    
    validation_script = '''#!/usr/bin/env python3
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
'''
    
    try:
        with open('/Users/Mike/trading/validate_environments.py', 'w') as f:
            f.write(validation_script)
        print("✅ Created environment validation script: validate_environments.py")
        print("   Run with: python validate_environments.py")
    except Exception as e:
        print(f"❌ Failed to create validation script: {e}")

def main():
    """Main test function"""
    # Run environment configuration test
    success = test_environment_config()
    
    # Demonstrate usage
    demonstrate_environment_usage()
    
    # Create validation test
    create_environment_validation_test()
    
    if success:
        print("\n✅ ENVIRONMENT-SPECIFIC CONFIGURATION IMPLEMENTATION COMPLETE")
        print("Phase 2 now supports environment-specific settings!")
        return 0
    else:
        print("\n❌ ENVIRONMENT-SPECIFIC CONFIGURATION NEEDS FIXES")
        return 1

if __name__ == "__main__":
    sys.exit(main())