// Debug script to understand why account data isn't showing
function debugAccountData() {
    console.log('=== ACCOUNT DATA DEBUG ===');
    
    // Check for all possible table selectors
    const selectors = [
        '.module.positions.data-table',
        '.public_fixedDataTable_main',
        '.positions',
        '.data-table',
        '.fixedDataTable',
        'table',
        '[role="table"]',
        '.account-table',
        '.accounts-table'
    ];
    
    console.log('1. Checking for tables with various selectors:');
    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            console.log(`   ✅ Found ${elements.length} elements with selector: ${selector}`);
            // Check first element for content
            const firstEl = elements[0];
            const hasRows = firstEl.querySelectorAll('tr, .row, [role="row"], .fixedDataTableRowLayout_rowWrapper').length;
            console.log(`      - First element has ${hasRows} row-like elements`);
            console.log(`      - First element classes: ${firstEl.className}`);
            console.log(`      - First element HTML preview: ${firstEl.outerHTML.substring(0, 200)}...`);
        } else {
            console.log(`   ❌ No elements found with selector: ${selector}`);
        }
    });
    
    // Check for any elements with "account" in class name
    console.log('\n2. Elements with "account" in class name:');
    const accountElements = document.querySelectorAll('[class*="account" i]');
    console.log(`   Found ${accountElements.length} elements with "account" in class`);
    if (accountElements.length > 0) {
        Array.from(accountElements).slice(0, 5).forEach((el, i) => {
            console.log(`   [${i}] ${el.tagName}.${el.className} - ${el.textContent.substring(0, 50)}...`);
        });
    }
    
    // Check for any elements with "position" in class name
    console.log('\n3. Elements with "position" in class name:');
    const positionElements = document.querySelectorAll('[class*="position" i]');
    console.log(`   Found ${positionElements.length} elements with "position" in class`);
    if (positionElements.length > 0) {
        Array.from(positionElements).slice(0, 5).forEach((el, i) => {
            console.log(`   [${i}] ${el.tagName}.${el.className} - ${el.textContent.substring(0, 50)}...`);
        });
    }
    
    // Check if we're on the right page
    console.log('\n4. Page context check:');
    console.log(`   - Current URL: ${window.location.href}`);
    console.log(`   - Page title: ${document.title}`);
    console.log(`   - Body classes: ${document.body.className}`);
    
    // Check for any data tables at all
    console.log('\n5. Looking for any table-like structures:');
    const tableStructures = document.querySelectorAll('table, [role="table"], [role="grid"], .data-table, .table');
    console.log(`   Found ${tableStructures.length} table-like structures`);
    tableStructures.forEach((table, i) => {
        const rows = table.querySelectorAll('tr, [role="row"], .row');
        console.log(`   Table ${i}: ${table.tagName}.${table.className} with ${rows.length} rows`);
    });
    
    // Check if getAllAccountTableData function exists
    console.log('\n6. Function availability:');
    console.log(`   - getAllAccountTableData exists: ${typeof getAllAccountTableData !== 'undefined'}`);
    console.log(`   - getTableData exists: ${typeof getTableData !== 'undefined'}`);
    
    // Try to run the functions if they exist
    if (typeof getAllAccountTableData !== 'undefined') {
        try {
            const result = getAllAccountTableData();
            console.log(`   - getAllAccountTableData() returned: ${result}`);
        } catch (e) {
            console.error(`   - getAllAccountTableData() error: ${e.message}`);
        }
    }
    
    if (typeof getTableData !== 'undefined') {
        try {
            const result = getTableData();
            console.log(`   - getTableData() returned:`, result);
        } catch (e) {
            console.error(`   - getTableData() error: ${e.message}`);
        }
    }
    
    console.log('=== END DEBUG ===');
}

// Run the debug function
debugAccountData();