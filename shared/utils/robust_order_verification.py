#!/usr/bin/env python3
"""
Robust Order Verification - Checks multiple sources to confirm execution
"""

import asyncio
import json

async def verify_order_with_multiple_sources(ws, symbol, timeout=10000):
    """
    Verify order execution using multiple data sources in order of reliability:
    1. DOM position changes (most reliable)
    2. Positions table updates
    3. Orders table appearance
    4. Account balance changes
    """
    
    verification_script = f"""
    (async () => {{
        const symbol = '{symbol}';
        const startTime = Date.now();
        const timeout = {timeout};
        
        console.log('🔍 Starting multi-source order verification for', symbol);
        
        // Capture initial state from all sources
        const initialState = {{
            domPosition: document.querySelector('.module-dom .contract-symbol:contains("' + symbol + '")')
                ?.closest('.module-dom')?.querySelector('.info-column .number')?.textContent || '0',
            
            positionsTable: Array.from(document.querySelectorAll('.module.positions .public_fixedDataTable_bodyRow')).find(row => 
                row.textContent.includes(symbol))?.textContent || 'No position',
            
            ordersCount: document.querySelectorAll('.module.orders .public_fixedDataTable_bodyRow').length,
            
            accountBalance: document.querySelector('.account-selector .balance')?.textContent || '0'
        }};
        
        console.log('Initial state:', initialState);
        
        // Execute order here (example)
        // const result = await window.autoOrder(symbol, 1, 'Buy', 20, 10, 0.25);
        
        // Check for changes with multiple verification methods
        const checkInterval = 500; // Check every 500ms
        let verificationResults = {{
            domPositionChanged: false,
            positionsTableChanged: false,
            orderAppeared: false,
            balanceChanged: false,
            confidence: 'NONE'
        }};
        
        while (Date.now() - startTime < timeout) {{
            // 1. Check DOM position (MOST RELIABLE)
            const currentDomPosition = document.querySelector('.module-dom .contract-symbol:contains("' + symbol + '")')
                ?.closest('.module-dom')?.querySelector('.info-column .number')?.textContent || '0';
            
            if (currentDomPosition !== initialState.domPosition) {{
                verificationResults.domPositionChanged = true;
                verificationResults.confidence = 'HIGH';
                console.log('✅ DOM position changed:', initialState.domPosition, '→', currentDomPosition);
            }}
            
            // 2. Check positions table
            const currentPositionsTable = Array.from(document.querySelectorAll('.module.positions .public_fixedDataTable_bodyRow')).find(row => 
                row.textContent.includes(symbol))?.textContent || 'No position';
            
            if (currentPositionsTable !== initialState.positionsTable) {{
                verificationResults.positionsTableChanged = true;
                if (verificationResults.confidence === 'NONE') {{
                    verificationResults.confidence = 'MEDIUM';
                }}
                console.log('✅ Positions table changed');
            }}
            
            // 3. Check orders table
            const currentOrdersCount = document.querySelectorAll('.module.orders .public_fixedDataTable_bodyRow').length;
            
            if (currentOrdersCount > initialState.ordersCount) {{
                verificationResults.orderAppeared = true;
                if (verificationResults.confidence === 'NONE') {{
                    verificationResults.confidence = 'LOW';
                }}
                console.log('✅ New order appeared in orders table');
            }}
            
            // 4. Check account balance
            const currentBalance = document.querySelector('.account-selector .balance')?.textContent || '0';
            
            if (currentBalance !== initialState.accountBalance) {{
                verificationResults.balanceChanged = true;
                console.log('✅ Account balance changed');
            }}
            
            // If we have high confidence, we can stop early
            if (verificationResults.confidence === 'HIGH') {{
                console.log('🎯 High confidence verification achieved!');
                break;
            }}
            
            await new Promise(r => setTimeout(r, checkInterval));
        }}
        
        // Final verification summary
        console.log('\\n📊 VERIFICATION SUMMARY:');
        console.log('DOM Position Changed:', verificationResults.domPositionChanged ? '✅' : '❌');
        console.log('Positions Table Changed:', verificationResults.positionsTableChanged ? '✅' : '❌');
        console.log('Order Appeared:', verificationResults.orderAppeared ? '✅' : '❌');
        console.log('Balance Changed:', verificationResults.balanceChanged ? '✅' : '❌');
        console.log('Confidence Level:', verificationResults.confidence);
        
        // Determine overall success
        verificationResults.success = verificationResults.confidence !== 'NONE';
        
        return verificationResults;
    }})();
    """
    
    msg = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": verification_script,
            "awaitPromise": True,
            "returnByValue": True
        }
    }
    
    await ws.send(json.dumps(msg))
    response = await ws.recv()
    result = json.loads(response)
    
    return result.get('result', {}).get('result', {}).get('value', {})


# Usage example
async def main():
    import websockets
    import subprocess
    
    # Get WebSocket URL
    result = subprocess.run(['curl', '-s', 'http://localhost:9223/json/list'], 
                          capture_output=True, text=True)
    ws_data = json.loads(result.stdout)[0]
    ws_url = ws_data['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        # Test verification
        verification = await verify_order_with_multiple_sources(ws, 'NQU5')
        
        print("\n🎯 Robust Verification Results:")
        print(f"Success: {verification.get('success')}")
        print(f"Confidence: {verification.get('confidence')}")
        print("\nDetails:")
        for key, value in verification.items():
            if key not in ['success', 'confidence']:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())