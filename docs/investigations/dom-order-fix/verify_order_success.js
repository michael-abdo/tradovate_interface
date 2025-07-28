// Quick Verification Script - Paste this in Tradovate browser console
// This will test if orders are now executing successfully

console.log('🔍 Verifying Order Success with DOM Fix...\n');

// Step 1: Check if DOM is visible
const domModule = document.querySelector('.module.module-dom');
const domVisible = domModule && domModule.offsetParent !== null;
console.log(`DOM Trading Mode: ${domVisible ? '✅ Active' : '❌ Not Active'}`);

if (!domVisible) {
    console.log('⚠️  Switch to DOM trading view to test the fix');
    console.log('The fix only applies when DOM trading module is visible');
}

// Step 2: Check if autoOrder function exists
if (typeof window.autoOrder !== 'function') {
    console.log('\n❌ autoOrder function not found!');
    console.log('Please inject the Tampermonkey script first');
} else {
    console.log('\n✅ autoOrder function is available');
    
    // Step 3: Capture state before order
    console.log('\n📊 Capturing state before order...');
    
    window.captureOrdersState('NQU5').then(beforeState => {
        console.log(`Before: ${beforeState.ordersCount} orders, ${beforeState.positionsCount} positions`);
        
        // Step 4: Execute test order
        console.log('\n🚀 Executing test order with DOM fix...');
        console.log('Order: Buy 1 NQ at Market');
        
        return window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25);
    }).then(result => {
        console.log(`\n📋 Order Result: ${result}`);
        
        // Step 5: Wait for execution
        console.log('⏳ Waiting 5 seconds for order to execute...');
        
        return new Promise(resolve => {
            setTimeout(() => resolve(result), 5000);
        });
    }).then(result => {
        // Step 6: Capture state after order
        console.log('\n📊 Capturing state after order...');
        
        return window.captureOrdersState('NQU5');
    }).then(afterState => {
        console.log(`After: ${afterState.ordersCount} orders, ${afterState.positionsCount} positions`);
        
        // Step 7: Compare states
        return window.captureOrdersState('NQU5').then(beforeState => {
            const comparison = window.compareOrderStates(beforeState, afterState, 'NQU5');
            
            console.log('\n🔍 VERIFICATION RESULTS:');
            console.log('=' + '='.repeat(50));
            
            if (comparison.executionDetected) {
                console.log('✅ SUCCESS! Order ACTUALLY EXECUTED!');
                console.log(`   Confidence: ${comparison.validation.confidence}`);
                console.log(`   Position Changes: ${comparison.positionChanges.detected}`);
                console.log(`   Order Changes: ${comparison.orderChanges.detected}`);
                console.log('\n🎉 The DOM fix is working! Orders are now executing properly.');
            } else {
                console.log('❌ Order DID NOT execute');
                console.log('   No position or order changes detected');
                console.log('\n⚠️  Possible issues:');
                console.log('   - Market might be closed');
                console.log('   - Account might not have permissions');
                console.log('   - DOM module might not be visible');
                console.log('   - Check browser console for errors');
            }
            
            console.log('=' + '='.repeat(50));
        });
    }).catch(error => {
        console.error('\n❌ Test failed with error:', error);
        console.log('\nTroubleshooting:');
        console.log('1. Make sure you\'re logged into Tradovate');
        console.log('2. Ensure DOM trading module is visible');
        console.log('3. Check that market is open');
        console.log('4. Verify the Tampermonkey script is loaded');
    });
}

console.log('\n📌 Note: This test will submit a REAL order if market is open!');