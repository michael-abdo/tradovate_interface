// Test script for symbol update functionality
// Run this in Chrome console after autoOrder.user.js is loaded

(function testSymbolUpdate() {
    console.log('=== Testing Symbol Update Functionality ===');
    
    // Test 1: Check if updateSymbol function exists
    if (typeof updateSymbol !== 'function') {
        console.error('❌ updateSymbol function not found! Make sure autoOrder.user.js is loaded');
        return;
    }
    console.log('✓ updateSymbol function exists');
    
    // Test 2: Find all search inputs
    const selectors = [
        '.trading-ticket .search-box--input',    // New specific selector
        '.search-box--input',                     // Old generic selector
        '.trading-ticket input[type="text"]'     // Fallback selector
    ];
    
    console.log('\n=== Checking selectors ===');
    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`Selector '${selector}': found ${elements.length} elements`);
        if (elements.length > 0) {
            elements.forEach((el, i) => {
                const location = {
                    inTradingTicket: !!el.closest('.trading-ticket'),
                    inMarketAnalyzer: !!el.closest('.market-analyzer, .market-watchlist'),
                    value: el.value,
                    placeholder: el.placeholder
                };
                console.log(`  [${i}]`, location);
            });
        }
    });
    
    // Test 3: Simulate symbol change
    console.log('\n=== Testing symbol change ===');
    const testSymbol = 'MNQ';
    
    // Get current value from order ticket before change
    const orderTicketBefore = document.querySelector('.trading-ticket .search-box--input');
    const marketAnalyzerBefore = document.querySelector('.market-analyzer .search-box--input, .market-watchlist .search-box--input');
    
    console.log('Before update:');
    console.log('  Order Ticket value:', orderTicketBefore?.value || 'not found');
    console.log('  Market Analyzer value:', marketAnalyzerBefore?.value || 'not found');
    
    // Trigger symbol change through the UI
    const symbolInput = document.getElementById('symbolInput');
    if (symbolInput) {
        console.log('\nTriggering symbol change to:', testSymbol);
        symbolInput.value = testSymbol;
        symbolInput.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Wait for update to complete
        setTimeout(() => {
            console.log('\nAfter update:');
            const orderTicketAfter = document.querySelector('.trading-ticket .search-box--input');
            const marketAnalyzerAfter = document.querySelector('.market-analyzer .search-box--input, .market-watchlist .search-box--input');
            
            console.log('  Order Ticket value:', orderTicketAfter?.value || 'not found');
            console.log('  Market Analyzer value:', marketAnalyzerAfter?.value || 'not found');
            
            // Check results
            if (orderTicketAfter && orderTicketAfter.value === testSymbol) {
                console.log('✅ SUCCESS: Order ticket updated correctly!');
            } else {
                console.log('❌ FAIL: Order ticket not updated correctly');
            }
            
            if (marketAnalyzerAfter && marketAnalyzerAfter.value !== testSymbol) {
                console.log('✅ SUCCESS: Market analyzer NOT updated (as expected)');
            } else if (marketAnalyzerAfter && marketAnalyzerAfter.value === testSymbol) {
                console.log('⚠️  WARNING: Market analyzer was also updated');
            }
            
            console.log('\n=== Test complete ===');
        }, 2000);  // Wait 2 seconds for async update
    } else {
        console.error('❌ Symbol input element not found!');
    }
})();