#!/usr/bin/env python3
"""
Ultra-Simple NQ Options Trading System Runner
Just run: python3 simple_run.py
"""

import sys
import os

# Add system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system'))

# Import and run
from integration import run_complete_nq_trading_system

print("🚀 Running NQ Options Analysis (Parallel Execution)...")
print("⚡ All analyses running simultaneously for speed!")

# Run with defaults
result = run_complete_nq_trading_system()

# Show key results
if result['status'] == 'success':
    rec = result['system_summary']['trading_summary']['primary_recommendation']
    print(f"\n✅ TRADE: {rec['direction']} @ ${rec['entry']:,.2f} → ${rec['target']:,.0f}")
    print(f"💰 Expected Value: {rec['expected_value']:+.1f} points")
    print(f"🎯 Win Probability: {rec['probability']:.1%}")
else:
    print(f"❌ Failed: {result.get('error')}")