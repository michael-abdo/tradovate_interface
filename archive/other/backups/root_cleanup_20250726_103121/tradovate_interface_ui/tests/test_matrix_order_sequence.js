// Size Matrix Order Sequence Tests
// Run these tests using a browser console or a framework like Jest

// Mock userPreferences
const userPreferences = {
    scalingEnabled: true,
    currentOrderNumber: 1
};

// Mock account phase data
const accountsData = [
    { id: 1001, name: "Phase1Account", phase: 1 },
    { id: 1002, name: "Phase2Account", phase: 2 },
    { id: 1003, name: "Phase3Account", phase: 3 }
];

// Mock DOM with matrix inputs
function setupMockDOM() {
    // Create a clean testing div
    const testDiv = document.createElement('div');
    testDiv.id = 'test-container';
    document.body.appendChild(testDiv);
    
    // Create matrix inputs
    const phases = [1, 2, 3];
    const orders = [1, 2, 3, 4];
    
    phases.forEach(phase => {
        orders.forEach(order => {
            const input = document.createElement('input');
            input.type = 'number';
            input.id = `phase${phase}_order${order}`;
            input.className = 'matrix-input';
            
            // Set test values: Phase 1 = order*5, Phase 2 = 10+order*5, Phase 3 = 20+order*5
            if (phase === 1) input.value = order * 5;
            else if (phase === 2) input.value = 10 + (order * 5);
            else input.value = 20 + (order * 5);
            
            testDiv.appendChild(input);
        });
    });
    
    // Create account checkboxes
    const accountsContainer = document.createElement('div');
    accountsData.forEach(account => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'accounts';
        checkbox.value = account.name;
        checkbox.setAttribute('data-account-id', account.id);
        accountsContainer.appendChild(checkbox);
    });
    document.body.appendChild(accountsContainer);
    
    return testDiv;
}

// Clean up mock DOM
function cleanupMockDOM() {
    const testDiv = document.getElementById('test-container');
    if (testDiv) document.body.removeChild(testDiv);
    
    // Remove account checkboxes
    const checkboxes = document.querySelectorAll('input[name="accounts"]');
    checkboxes.forEach(checkbox => {
        if (checkbox.parentNode) checkbox.parentNode.removeChild(checkbox);
    });
}

// Get matrix value function (simplified version of the one in the app)
function getMatrixValue(phase, orderNum) {
    // Limit to valid ranges
    phase = Math.min(Math.max(phase, 1), 3);
    orderNum = Math.min(Math.max(orderNum, 1), 4);
    
    // Get the value directly from the DOM input
    const inputId = `phase${phase}_order${orderNum}`;
    const input = document.getElementById(inputId);
    
    if (input) {
        return parseInt(input.value) || 1;
    }
    
    // Default fallback values if all else fails
    let defaultValue;
    if (phase === 1) defaultValue = 5 * orderNum;
    else if (phase === 2) defaultValue = 5 + (5 * orderNum);
    else defaultValue = 15 + (5 * orderNum);
    
    return defaultValue;
}

// Get current order size based on sequence number and account phase
function getCurrentOrderSize() {
    // Check if scaling is enabled
    if (!userPreferences.scalingEnabled) {
        return null;
    }
    
    // Get the current order number
    const orderNum = userPreferences.currentOrderNumber || 1;
    
    // Get the account phase from selected account(s)
    let phase = 1; // Default to Phase 1 if no account is selected
    
    // Get all checked accounts
    const selectedAccountCheckboxes = document.querySelectorAll('input[name="accounts"]:checked');
    
    if (selectedAccountCheckboxes.length > 0) {
        // Get the account ID from the first selected checkbox
        const accountId = parseInt(selectedAccountCheckboxes[0].getAttribute('data-account-id'));
        
        // Find the account data to get the phase
        const account = accountsData.find(acc => acc.id === accountId);
        if (account && account.phase) {
            phase = parseInt(account.phase);
        }
    }
    
    // Look up the lot size from the matrix by phase and order number
    const size = getMatrixValue(phase, orderNum);
    return size;
}

// Test helper
function assertEqual(actual, expected, testName) {
    if (actual === expected) {
        console.log(`✅ PASS: ${testName}`);
        return true;
    } else {
        console.error(`❌ FAIL: ${testName} - Expected ${expected}, got ${actual}`);
        return false;
    }
}

// Run all tests
function runTests() {
    console.log("Starting Size Matrix Order Sequence Tests");
    let passCount = 0;
    let totalTests = 0;
    
    try {
        // Setup the mock DOM
        setupMockDOM();
        
        // Test 1: Basic matrix value retrieval
        totalTests++;
        const phase1Order2Value = getMatrixValue(1, 2);
        if (assertEqual(phase1Order2Value, 10, "Phase 1, Order 2 should be 10")) passCount++;
        
        totalTests++;
        const phase2Order3Value = getMatrixValue(2, 3);
        if (assertEqual(phase2Order3Value, 25, "Phase 2, Order 3 should be 25")) passCount++;
        
        totalTests++;
        const phase3Order4Value = getMatrixValue(3, 4);
        if (assertEqual(phase3Order4Value, 40, "Phase 3, Order 4 should be 40")) passCount++;
        
        // Test 2: Default scaling enabled but no account selected
        totalTests++;
        userPreferences.currentOrderNumber = 2;
        userPreferences.scalingEnabled = true;
        const defaultPhaseOrder2Size = getCurrentOrderSize();
        if (assertEqual(defaultPhaseOrder2Size, 10, "Default Phase 1, Order 2 should be 10")) passCount++;
        
        // Test 3: Select a Phase 2 account
        const phase2Checkbox = document.querySelector(`input[data-account-id="1002"]`);
        phase2Checkbox.checked = true;
        
        totalTests++;
        userPreferences.currentOrderNumber = 3;
        const phase2Order3Size = getCurrentOrderSize();
        if (assertEqual(phase2Order3Size, 25, "Phase 2, Order 3 should be 25")) passCount++;
        
        // Test 4: Change to a Phase 3 account
        phase2Checkbox.checked = false;
        const phase3Checkbox = document.querySelector(`input[data-account-id="1003"]`);
        phase3Checkbox.checked = true;
        
        totalTests++;
        userPreferences.currentOrderNumber = 4;
        const phase3Order4Size = getCurrentOrderSize();
        if (assertEqual(phase3Order4Size, 40, "Phase 3, Order 4 should be 40")) passCount++;
        
        // Test 5: Scaling disabled
        totalTests++;
        userPreferences.scalingEnabled = false;
        const scalingDisabledSize = getCurrentOrderSize();
        if (assertEqual(scalingDisabledSize, null, "Scaling disabled should return null")) passCount++;
        
        // Test 6: Re-enable scaling but select multiple accounts (should use first one)
        userPreferences.scalingEnabled = true;
        userPreferences.currentOrderNumber = 2;
        phase3Checkbox.checked = true;
        phase2Checkbox.checked = true;
        
        totalTests++;
        const multiAccountSize = getCurrentOrderSize();
        if (assertEqual(multiAccountSize, 20, "Multiple accounts should use first selected (Phase 2, Order 2)")) passCount++;
        
    } finally {
        // Clean up the DOM
        cleanupMockDOM();
    }
    
    console.log(`Test results: ${passCount} of ${totalTests} passed`);
    return { passCount, totalTests };
}

// Run tests if in a browser context
if (typeof window !== 'undefined') {
    console.log("Tests will run in 1 second...");
    setTimeout(runTests, 1000);
} else {
    console.log("This script should be run in a browser environment");
}

// Export for Node.js/Jest environment
if (typeof module !== 'undefined') {
    module.exports = { 
        getMatrixValue, 
        getCurrentOrderSize, 
        setupMockDOM, 
        cleanupMockDOM, 
        runTests 
    };
}