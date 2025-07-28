
// Check all possible selectors
const selectors = [
    '.public_fixedDataTable_main',
    '.module.positions.data-table',
    '.positions .data-table',
    '.positions',
    '[role="table"]',
    '.fixedDataTable',
    'table',
    '.data-table'
];

console.log('Checking selectors...');
selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} elements for: ${selector}`);
        console.log('   First element:', elements[0]);
    } else {
        console.log(`❌ No elements found for: ${selector}`);
    }
});

// Check if getAllAccountTableData exists
if (typeof getAllAccountTableData === 'function') {
    console.log('\n✅ getAllAccountTableData function exists');
    console.log('Calling it now...');
    try {
        const result = getAllAccountTableData();
        console.log('Result:', result);
    } catch (e) {
        console.error('Error calling function:', e);
    }
} else {
    console.error('\n❌ getAllAccountTableData function NOT found');
}

// Check login status
const userElements = document.querySelectorAll('[class*="user"], [class*="account"], [id*="user"]');
console.log(`\nFound ${userElements.length} user-related elements`);
