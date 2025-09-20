#!/usr/bin/env python3
"""Quick reload autoOrder script on all Chrome instances"""
from src.app import TradovateController

# Initialize controller and find all Chrome instances
controller = TradovateController()

# Inject scripts on all connections
for conn in controller.connections:
    conn.inject_tampermonkey()
    print(f"✅ Reloaded scripts on {conn.account_name}")

print(f"\n🎉 Done! Reloaded {len(controller.connections)} instances")