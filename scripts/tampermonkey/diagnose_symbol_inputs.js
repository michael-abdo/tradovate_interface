// Diagnostic script to find all symbol input elements on Tradovate
// Run this in Chrome DevTools console to identify the correct selector

(function() {
    console.log('=== Diagnosing Symbol Inputs on Tradovate ===');
    
    // Find all search-box inputs
    const searchInputs = document.querySelectorAll('.search-box--input');
    console.log(`\nFound ${searchInputs.length} elements with class '.search-box--input':`);
    searchInputs.forEach((input, index) => {
        console.log(`[${index}] Input:`, input);
        console.log(`  - Parent classes: ${input.parentElement?.className || 'N/A'}`);
        console.log(`  - Grandparent classes: ${input.parentElement?.parentElement?.className || 'N/A'}`);
        console.log(`  - Current value: "${input.value}"`);
        console.log(`  - Placeholder: "${input.placeholder}"`);
        
        // Check if it's in a trading ticket
        const tradingTicket = input.closest('.trading-ticket');
        const marketAnalyzer = input.closest('.market-analyzer, .market-watchlist, .watchlist-panel');
        const orderEntry = input.closest('.order-entry, .order-ticket');
        
        if (tradingTicket) {
            console.log(`  ✓ This is in a TRADING TICKET`);
        }
        if (marketAnalyzer) {
            console.log(`  ✗ This is in a MARKET ANALYZER/WATCHLIST`);
        }
        if (orderEntry) {
            console.log(`  ✓ This is in an ORDER ENTRY`);
        }
        console.log('');
    });
    
    // Look for other potential symbol inputs
    console.log('\n=== Looking for other potential symbol inputs ===');
    
    // Check for trading ticket specific inputs
    const tradingTickets = document.querySelectorAll('.trading-ticket');
    console.log(`\nFound ${tradingTickets.length} trading tickets`);
    tradingTickets.forEach((ticket, index) => {
        console.log(`\nTrading Ticket [${index}]:`);
        const inputs = ticket.querySelectorAll('input[type="text"]');
        inputs.forEach((input, i) => {
            console.log(`  Input [${i}]: value="${input.value}", placeholder="${input.placeholder}"`);
            console.log(`    - Classes: ${input.className}`);
            console.log(`    - ID: ${input.id || 'none'}`);
        });
    });
    
    // Check for specific selectors
    const selectors = [
        '.trading-ticket input[type="text"]',
        '.trading-ticket .search-box--input',
        '.order-entry input[type="text"]',
        '.order-ticket input[type="text"]',
        '.contract-search',
        '.symbol-input',
        '.symbol-search',
        'input[placeholder*="Symbol"]',
        'input[placeholder*="symbol"]',
        'input[placeholder*="Contract"]',
        'input[placeholder*="contract"]'
    ];
    
    console.log('\n=== Testing specific selectors ===');
    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            console.log(`\n✓ Selector '${selector}' found ${elements.length} elements:`);
            elements.forEach((el, i) => {
                console.log(`  [${i}] value="${el.value}", placeholder="${el.placeholder}"`);
            });
        }
    });
    
    // Recommendation
    console.log('\n=== RECOMMENDATION ===');
    console.log('Based on the DOM structure, use one of these selectors:');
    console.log('1. .trading-ticket .search-box--input');
    console.log('2. .trading-ticket input[type="text"]:first-of-type');
    console.log('3. Look for a more specific class/id once you run this diagnostic');
    
    return 'Diagnostic complete - check console output';
})();