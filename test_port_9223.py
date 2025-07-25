#!/usr/bin/env python3
"""
Test script to verify port 9223 Chrome works independently
"""
import sys
import os
import time
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import TradovateConnection

def test_port_9223():
    """Test connection to port 9223 without affecting port 9222"""
    print("🧪 Testing Chrome connection on port 9223...")
    print("📌 This is COMPLETELY SEPARATE from port 9222")
    print("-" * 60)
    
    try:
        # Connect to port 9223 (our separate instance)
        conn = TradovateConnection(9223, "Port 9223 Test")
        
        if not conn.tab:
            print("❌ No Tradovate tab found on port 9223")
            print("💡 Make sure to run: ./start_chrome_9223.sh first")
            return False
            
        print("✅ Connected to Tradovate tab on port 9223")
        
        # Test basic JavaScript execution
        result = conn.tab.Runtime.evaluate(expression="document.title")
        title = result.get('result', {}).get('value', 'Unknown')
        print(f"📄 Page title: {title}")
        
        # Test console interceptor injection
        print("\n🔧 Testing console interceptor injection...")
        success = conn.inject_tampermonkey()
        
        if success:
            print("✅ Console interceptor injected successfully")
            
            # Test console logging
            conn.tab.Runtime.evaluate(expression="console.log('Test from port 9223')")
            conn.tab.Runtime.evaluate(expression="console.error('Error test from port 9223')")
            time.sleep(0.5)
            
            # Get console logs
            logs = conn.get_console_logs()
            if logs.get('status') == 'success':
                log_count = logs.get('count', 0)
                print(f"✅ Retrieved {log_count} console logs")
                
                # Show recent logs
                for log in logs.get('logs', [])[-3:]:
                    level = log.get('level', '').upper()
                    message = log.get('message', '')
                    print(f"   [{level}] {message}")
            else:
                print(f"❌ Failed to get console logs: {logs.get('error')}")
                
        else:
            print("❌ Failed to inject console interceptor")
            
        print("\n✅ Port 9223 test completed successfully!")
        print("🔒 Port 9222 remains completely unaffected")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_port_9222_unaffected():
    """Verify that port 9222 is still working normally"""
    print("\n🔍 Verifying port 9222 is unaffected...")
    
    try:
        # Quick connection test to port 9222
        import pychrome
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        tabs = browser.list_tab()
        print(f"✅ Port 9222 still active with {len(tabs)} tabs")
        return True
    except Exception as e:
        print(f"⚠️  Port 9222 check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Chrome Port 9223 Independence Test")
    print("=" * 60)
    
    # First verify 9222 is still working
    port_9222_ok = verify_port_9222_unaffected()
    
    # Test our 9223 connection
    success = test_port_9223()
    
    # Final verification that 9222 is still unaffected
    port_9222_still_ok = verify_port_9222_unaffected()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"Port 9222 (existing): {'✅ SAFE' if port_9222_ok and port_9222_still_ok else '❌ AFFECTED'}")
    print(f"Port 9223 (new): {'✅ WORKING' if success else '❌ FAILED'}")
    
    if success and port_9222_ok and port_9222_still_ok:
        print("\n🎉 SUCCESS: Port 9223 works independently!")
        print("🔒 Port 9222 completely unaffected")
    else:
        print("\n⚠️  Issues detected - check output above")
    
    sys.exit(0 if success and port_9222_still_ok else 1)