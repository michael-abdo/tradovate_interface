// Manual DOM Order Test Script
// Copy and paste this into the Tradovate browser console

console.log('🚀 Starting Manual DOM Order Test...');

// Test 1: Check DOM visibility
console.log('\n📍 Test 1: DOM Module Visibility');
const domModule = document.querySelector('.module.module-dom');
const orderTicket = document.querySelector('.module.order-ticket');

console.log('DOM Module exists:', !!domModule);
console.log('DOM Module visible:', domModule ? domModule.offsetParent !== null : false);
console.log('Order Ticket exists:', !!orderTicket);
console.log('Order Ticket visible:', orderTicket ? orderTicket.offsetParent !== null : false);

// Test 2: Find price cells
console.log('\n📍 Test 2: Price Cell Detection');
const cellSelectors = [
    '.dom-cell-container-bid',
    '.dom-cell-container-ask',
    '.dom-price-cell',
    '[class*="dom-cell"]',
    '.dom-bid',
    '.dom-ask'
];

let totalCells = 0;
for (const selector of cellSelectors) {
    const cells = document.querySelectorAll(selector);
    if (cells.length > 0) {
        console.log(`  ${selector}: ${cells.length} cells`);
        totalCells += cells.length;
    }
}
console.log(`Total price cells found: ${totalCells}`);

// Test 3: Test order submission with DOM click
console.log('\n📍 Test 3: Testing Order Submission with DOM Click');

// First check if autoOrder function exists
if (typeof window.autoOrder === 'function') {
    console.log('✅ autoOrder function is available');
    
    // Test the enhanced submission
    console.log('Testing order submission...');
    
    // Capture state before
    const beforeState = {
        orders: document.querySelectorAll('.order-row').length,
        positions: document.querySelectorAll('.position-row').length
    };
    console.log('Before state:', beforeState);
    
    // Try to submit an order
    console.log('Submitting test order...');
    window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25).then(result => {
        console.log('Order result:', result);
        
        // Wait and check state after
        setTimeout(() => {
            const afterState = {
                orders: document.querySelectorAll('.order-row').length,
                positions: document.querySelectorAll('.position-row').length
            };
            console.log('After state:', afterState);
            console.log('Orders changed:', afterState.orders !== beforeState.orders);
            console.log('Positions changed:', afterState.positions !== beforeState.positions);
        }, 3000);
    }).catch(error => {
        console.error('Order submission error:', error);
    });
    
} else {
    console.log('❌ autoOrder function not found - inject it first');
    console.log('You can inject it by running the Tampermonkey script or pasting autoOrder.user.js content');
}

// Test 4: Direct DOM click test (without autoOrder)
console.log('\n📍 Test 4: Direct DOM Click Test');
const askCells = document.querySelectorAll('.dom-cell-container-ask, .dom-ask');
if (askCells.length > 0) {
    console.log(`Found ${askCells.length} ask cells`);
    console.log('To test clicking, run:');
    console.log('askCells[Math.floor(askCells.length/2)].click()');
} else {
    console.log('No ask cells found - make sure DOM trading module is visible');
}

console.log('\n✅ Manual test script completed!');
console.log('Check the results above to verify DOM functionality');