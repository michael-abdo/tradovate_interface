#!/usr/bin/env python3
"""
Manual Hot Reload Trigger
Use this script to manually trigger hot-reload of autoOrder.user.js
"""
import pychrome
import requests

def manual_hot_reload():
    print("🔥 MANUAL HOT RELOAD: Starting...")
    
    try:
        # Fetch the updated script from HTTP server
        print("📡 Fetching updated script from localhost:8080...")
        response = requests.get('http://localhost:8080/autoOrder.user.js')
        script_content = response.text
        print(f"✅ Script fetched ({len(script_content)} characters)")
        
        # Connect to Chrome instances
        print("🌐 Connecting to Chrome instances...")
        ports = [9222, 9223]  # Both Chrome instances
        
        for port in ports:
            try:
                print(f"🔗 Connecting to Chrome on port {port}...")
                browser = pychrome.Browser(f"http://127.0.0.1:{port}")
                tabs = browser.list_tab()
                
                if not tabs:
                    print(f"⚠️  No tabs found on port {port}")
                    continue
                    
                tab = tabs[0]  # Use first tab
                tab.start()
                
                # Check if it's a Tradovate tab
                result = tab.Runtime.evaluate(expression='window.location.hostname')
                hostname = result.get('result', {}).get('value', 'unknown')
                
                if 'tradovate' not in hostname:
                    print(f"⚠️  Port {port} is not a Tradovate tab (hostname: {hostname})")
                    tab.stop()
                    continue
                
                print(f"✅ Found Tradovate tab on port {port}")
                
                # Hot-reload cleanup and injection
                print(f"🔥 HOT RELOAD: Cleaning up existing autoOrder UI on port {port}...")
                cleanup_script = """
                console.log('🔥 MANUAL HOT RELOAD: Removing old autoOrder UI...');
                let oldUI = document.getElementById('bracket-trade-box');
                if (oldUI) {
                    oldUI.remove();
                    console.log('🔥 MANUAL HOT RELOAD: Old UI removed');
                } else {
                    console.log('🔥 MANUAL HOT RELOAD: No existing UI found');
                }
                // Clear localStorage quantity to force new defaults
                localStorage.removeItem('bracketTrade_qty');
                console.log('🔥 MANUAL HOT RELOAD: localStorage cleared');
                """
                
                tab.Runtime.evaluate(expression=cleanup_script)
                print(f"🧹 Cleanup completed on port {port}")
                
                # Inject updated script
                print(f"💉 Injecting updated script on port {port}...")
                result = tab.Runtime.evaluate(expression=script_content)
                
                if result.get('wasThrown'):
                    print(f"❌ Script injection failed on port {port}: {result.get('result', {})}")
                else:
                    print(f"✅ Script injected successfully on port {port}")
                
                # Verify the change
                qty_result = tab.Runtime.evaluate(expression='document.getElementById("qtyInput")?.value || "NOT_FOUND"')
                qty_value = qty_result.get('result', {}).get('value', 'unknown')
                print(f"📊 Current quantity value on port {port}: {qty_value}")
                
                tab.stop()
                
            except Exception as e:
                print(f"❌ Error with port {port}: {e}")
        
        print("🎉 MANUAL HOT RELOAD: Complete!")
        
    except Exception as e:
        print(f"❌ MANUAL HOT RELOAD FAILED: {e}")

if __name__ == "__main__":
    manual_hot_reload()