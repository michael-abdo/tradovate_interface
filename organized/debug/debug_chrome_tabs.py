#!/usr/bin/env python3
"""Debug what tabs are available in Chrome"""

import pychrome
import json

def debug_tabs():
    """Debug Chrome tabs"""
    
    ports = [9223, 9224]
    
    for port in ports:
        print(f"\n{'='*60}")
        print(f"Chrome on port {port}")
        print(f"{'='*60}")
        
        try:
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            
            print(f"Found {len(tabs)} tabs:")
            
            for i, tab in enumerate(tabs):
                print(f"\nTab {i}:")
                # Print all attributes
                for attr in dir(tab):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(tab, attr)
                            if not callable(value):
                                print(f"  {attr}: {value}")
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_tabs()