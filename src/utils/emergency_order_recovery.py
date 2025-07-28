#!/usr/bin/env python3
"""
Emergency Order Recovery Script
Use this when orders stop executing to diagnose and fix issues
"""

import subprocess
import json
import time
from datetime import datetime

def run_diagnostic(description, command):
    """Run a diagnostic command and return results"""
    print(f"\n🔍 {description}...")
    
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, capture_output=True, text=True)
        
        success = result.returncode == 0
        print(f"   {'✅' if success else '❌'} {description}: {'SUCCESS' if success else 'FAILED'}")
        
        if not success and result.stderr:
            print(f"   Error: {result.stderr[:200]}...")
            
        return {
            'test': description,
            'success': success,
            'output': result.stdout[:500] if result.stdout else None,
            'error': result.stderr[:500] if result.stderr else None
        }
    except Exception as e:
        print(f"   ❌ {description}: EXCEPTION - {str(e)}")
        return {
            'test': description,
            'success': False,
            'error': str(e)
        }

def main():
    """Run emergency diagnostics and recovery"""
    
    print("=" * 60)
    print("🚨 EMERGENCY ORDER RECOVERY SYSTEM")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    diagnostics = []
    
    # 1. Check Chrome connections
    diagnostics.append(run_diagnostic(
        "Checking Chrome connections",
        ["python3", "src/utils/check_chrome.py"]
    ))
    
    # 2. Check if Chrome is running on all ports
    for port in [9223, 9224, 9225]:
        diagnostics.append(run_diagnostic(
            f"Chrome debug port {port}",
            f"curl -s http://localhost:{port}/json/list | head -n 1"
        ))
    
    # 3. Test script injection
    print("\n📝 Testing Script Injection...")
    test_injection = '''
    import sys
    sys.path.append('.')
    from src.app import TradovateConnection
    
    # Test on first account
    conn = TradovateConnection("test", 9223)
    if conn.connect():
        print("✅ Connected to Chrome")
        
        # Check if autoOrder is loaded
        result = conn.tab.Runtime.evaluate(expression="typeof window.autoOrder")
        if result.get('result', {}).get('value') == 'function':
            print("✅ autoOrder function is loaded")
        else:
            print("❌ autoOrder function NOT loaded")
            # Try to inject
            conn.inject_tampermonkey()
            print("🔄 Attempted to reinject scripts")
    '''
    
    with open('/tmp/test_injection.py', 'w') as f:
        f.write(test_injection)
    
    diagnostics.append(run_diagnostic(
        "Script injection test",
        ["python3", "/tmp/test_injection.py"]
    ))
    
    # 4. Run order verification
    diagnostics.append(run_diagnostic(
        "Order execution verification",
        ["python3", "docs/investigations/dom-order-fix/final_order_verification.py"]
    ))
    
    # 5. Check dashboard status
    diagnostics.append(run_diagnostic(
        "Dashboard status",
        "curl -s http://localhost:6001/ | grep -q 'Tradovate' && echo 'Dashboard running'"
    ))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    failed_tests = [d for d in diagnostics if not d['success']]
    
    if not failed_tests:
        print("✅ All diagnostics passed! System appears healthy.")
    else:
        print(f"❌ {len(failed_tests)} tests failed:")
        for test in failed_tests:
            print(f"   - {test['test']}")
    
    # Recovery recommendations
    print("\n" + "=" * 60)
    print("🔧 RECOVERY STEPS")
    print("=" * 60)
    
    if any('Chrome debug port' in d['test'] and not d['success'] for d in diagnostics):
        print("\n1. Chrome not running on required ports. Fix with:")
        print("   ./start_all.py")
    
    if any('autoOrder function NOT loaded' in str(d.get('output', '')) for d in diagnostics):
        print("\n2. Scripts not injected. Fix with:")
        print("   python src/dashboard.py  # This will auto-inject scripts")
    
    if any('Order execution verification' in d['test'] and not d['success'] for d in diagnostics):
        print("\n3. Orders not executing. Check:")
        print("   - Is Tradovate logged in?")
        print("   - Is market open?")
        print("   - Check DOM positions at: .module-dom .info-column .number")
        print("   - NOT order tables!")
    
    # Save diagnostic report
    report_file = f"logs/emergency_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'diagnostics': diagnostics,
            'failed_count': len(failed_tests)
        }, f, indent=2)
    
    print(f"\n📄 Full diagnostic report saved to: {report_file}")
    
    # Final recommendation
    print("\n" + "=" * 60)
    if failed_tests:
        print("⚠️  RECOMMENDED ACTION: Run './start_all.py' to restart everything")
    else:
        print("✅ System healthy - orders should be executing correctly")
    print("=" * 60)

if __name__ == "__main__":
    main()