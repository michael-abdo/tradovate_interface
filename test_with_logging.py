#!/usr/bin/env python3

import sys
import time
import json
from src.app import TradovateController

def test_scale_with_detailed_logging():
    """Execute a scale order and capture all browser console output"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing scale order with detailed logging on {conn.account_name}...")
    
    # Enable console and runtime
    conn.tab.Console.enable()
    conn.tab.Runtime.enable()
    
    # Set up console message capture
    console_messages = []
    
    def on_console_message(message):
        console_messages.append(message)
        print(f"[CONSOLE] {message}")
    
    # Start capturing console messages (this won't work with pychrome, but we'll use Runtime.evaluate)
    
    # Clear console and add start marker
    conn.tab.Runtime.evaluate(expression="""
        console.clear();
        console.log('🚨🚨🚨 STARTING SCALE ORDER TEST 🚨🚨🚨');
        console.log('Timestamp:', new Date().toISOString());
    """)
    
    print("Console cleared, starting scale order test...")
    
    # Execute scale order with detailed logging
    scale_orders = [
        {"quantity": 1, "entry_price": None},
        {"quantity": 1, "entry_price": None},
        {"quantity": 1, "entry_price": None},
        {"quantity": 1, "entry_price": None}
    ]
    
    print(f"Executing scale order: {scale_orders}")
    
    # Add pre-execution logging
    conn.tab.Runtime.evaluate(expression="""
        console.log('🔥 PRE-EXECUTION: About to call auto_trade_scale');
        console.log('Function exists:', typeof auto_trade_scale === 'function');
        console.log('autoTrade exists:', typeof autoTrade === 'function');
    """)
    
    # Execute the scale order
    result = conn.auto_trade_scale(
        symbol="NQ", 
        scale_orders=scale_orders, 
        action="Buy", 
        tp_ticks=0,
        sl_ticks=0, 
        tick_size=0.25
    )
    
    print(f"Scale order execution result: {result}")
    
    # Wait for execution to complete
    print("Waiting 10 seconds for order execution...")
    time.sleep(10)
    
    # Add post-execution logging
    conn.tab.Runtime.evaluate(expression="""
        console.log('🔥 POST-EXECUTION: Scale order completed');
        console.log('Final timestamp:', new Date().toISOString());
    """)
    
    # Capture all recent console activity
    capture_logs = """
    // Try to capture any recent console activity or execution traces
    JSON.stringify({
        timestamp: new Date().toISOString(),
        testCompleted: true,
        functionsAvailable: {
            autoTrade: typeof autoTrade === 'function',
            auto_trade_scale: typeof auto_trade_scale === 'function'
        }
    });
    """
    
    log_result = conn.tab.Runtime.evaluate(expression=capture_logs)
    print(f"Final log capture: {log_result}")
    
    return True

if __name__ == "__main__":
    test_scale_with_detailed_logging()