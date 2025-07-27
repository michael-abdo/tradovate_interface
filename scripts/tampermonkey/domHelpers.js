// ============================================================================
// DOM VALIDATION HELPER FUNCTIONS
// ============================================================================
// 
// Original specification implementation for Task 2.2 requirements.
// Provides basic DOM validation functions as specified in the visibility 
// gaps task breakdown document.
//
// Usage:
//   await waitForElement('#mySelector', 5000);
//   if (validateElementExists('#button')) { ... }
//   if (validateElementVisible(element)) { ... }
//
// ============================================================================

/**
 * Wait for an element to appear in the DOM
 * @param {string} selector - CSS selector for the element
 * @param {number} timeout - Maximum time to wait in milliseconds (default: 10000)
 * @returns {Promise<Element|null>} The element when found, or null if timeout
 */
async function waitForElement(selector, timeout = 10000) {
    const startTime = Date.now();
    
    return new Promise((resolve) => {
        const checkElement = () => {
            const element = document.querySelector(selector);
            
            if (element) {
                console.log(`✅ Element found: ${selector} (${Date.now() - startTime}ms)`);
                resolve(element);
                return;
            }
            
            // Check if timeout exceeded
            if (Date.now() - startTime >= timeout) {
                console.warn(`⏰ Timeout waiting for element: ${selector} (${timeout}ms)`);
                resolve(null);
                return;
            }
            
            // Continue checking
            setTimeout(checkElement, 100);
        };
        
        checkElement();
    });
}

/**
 * Validate that an element exists in the DOM
 * @param {string} selector - CSS selector for the element
 * @returns {boolean} True if element exists, false otherwise
 */
function validateElementExists(selector) {
    const element = document.querySelector(selector);
    const exists = element !== null;
    
    if (exists) {
        console.log(`✅ Element exists: ${selector}`);
    } else {
        console.warn(`❌ Element not found: ${selector}`);
    }
    
    return exists;
}

/**
 * Validate that an element is visible (not hidden by CSS)
 * @param {Element} element - DOM element to check
 * @returns {boolean} True if element is visible, false otherwise
 */
function validateElementVisible(element) {
    if (!element) {
        console.warn(`❌ Cannot check visibility: element is null`);
        return false;
    }
    
    const style = window.getComputedStyle(element);
    const isVisible = style.display !== 'none' && 
                     style.visibility !== 'hidden' && 
                     element.offsetWidth > 0 && 
                     element.offsetHeight > 0;
    
    if (isVisible) {
        console.log(`✅ Element is visible: ${element.tagName}${element.className ? '.' + element.className : ''}`);
    } else {
        console.warn(`❌ Element is not visible: ${element.tagName}${element.className ? '.' + element.className : ''}`);
    }
    
    return isVisible;
}

/**
 * Validate that an element is clickable (visible and not disabled)
 * @param {Element} element - DOM element to check
 * @returns {boolean} True if element is clickable, false otherwise
 */
function validateElementClickable(element) {
    if (!element) {
        console.warn(`❌ Cannot check clickability: element is null`);
        return false;
    }
    
    const isVisible = validateElementVisible(element);
    const isEnabled = !element.disabled && !element.hasAttribute('disabled');
    const isClickable = isVisible && isEnabled;
    
    if (isClickable) {
        console.log(`✅ Element is clickable: ${element.tagName}${element.className ? '.' + element.className : ''}`);
    } else {
        console.warn(`❌ Element is not clickable: ${element.tagName}${element.className ? '.' + element.className : ''} (visible: ${isVisible}, enabled: ${isEnabled})`);
    }
    
    return isClickable;
}

/**
 * Validate that a form field has the expected value
 * @param {Element} element - Form element to check
 * @param {string} expectedValue - Expected value
 * @returns {boolean} True if value matches expected, false otherwise
 */
function validateFormFieldValue(element, expectedValue) {
    if (!element) {
        console.warn(`❌ Cannot validate form field: element is null`);
        return false;
    }
    
    const actualValue = element.value || element.textContent || '';
    const matches = actualValue.toString() === expectedValue.toString();
    
    if (matches) {
        console.log(`✅ Form field value correct: "${actualValue}" matches "${expectedValue}"`);
    } else {
        console.warn(`❌ Form field value mismatch: expected "${expectedValue}", got "${actualValue}"`);
    }
    
    return matches;
}

/**
 * Enhanced element finder with retry logic
 * @param {string} selector - CSS selector for the element
 * @param {Object} options - Options object
 * @param {number} options.timeout - Maximum time to wait (default: 10000)
 * @param {number} options.retries - Number of retries (default: 3)
 * @param {boolean} options.mustBeVisible - Element must be visible (default: true)
 * @param {boolean} options.mustBeClickable - Element must be clickable (default: false)
 * @returns {Promise<Element|null>} The element when found and validated
 */
async function findElementWithValidation(selector, options = {}) {
    const {
        timeout = 10000,
        retries = 3,
        mustBeVisible = true,
        mustBeClickable = false
    } = options;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        console.log(`🔍 Finding element attempt ${attempt}/${retries}: ${selector}`);
        
        const element = await waitForElement(selector, timeout);
        
        if (!element) {
            console.warn(`❌ Element not found on attempt ${attempt}: ${selector}`);
            continue;
        }
        
        // Validate visibility if required
        if (mustBeVisible && !validateElementVisible(element)) {
            console.warn(`❌ Element not visible on attempt ${attempt}: ${selector}`);
            continue;
        }
        
        // Validate clickability if required
        if (mustBeClickable && !validateElementClickable(element)) {
            console.warn(`❌ Element not clickable on attempt ${attempt}: ${selector}`);
            continue;
        }
        
        console.log(`✅ Element found and validated: ${selector}`);
        return element;
    }
    
    console.error(`❌ Failed to find valid element after ${retries} attempts: ${selector}`);
    return null;
}

/**
 * Safely click an element with validation
 * @param {string|Element} selectorOrElement - CSS selector or DOM element
 * @param {Object} options - Options object
 * @returns {Promise<boolean>} True if click was successful
 */
async function safeClick(selectorOrElement, options = {}) {
    let element;
    
    if (typeof selectorOrElement === 'string') {
        element = await findElementWithValidation(selectorOrElement, {
            ...options,
            mustBeVisible: true,
            mustBeClickable: true
        });
    } else {
        element = selectorOrElement;
    }
    
    if (!element) {
        console.error(`❌ Cannot click: element not found or invalid`);
        return false;
    }
    
    try {
        element.click();
        console.log(`✅ Clicked element successfully`);
        return true;
    } catch (error) {
        console.error(`❌ Error clicking element: ${error.message}`);
        return false;
    }
}

/**
 * Safely set a form field value with validation (Tradovate-optimized)
 * @param {string|Element} selectorOrElement - CSS selector or DOM element
 * @param {string} value - Value to set
 * @param {Object} options - Options object
 * @returns {Promise<boolean>} True if value was set successfully
 */
async function safeSetValue(selectorOrElement, value, options = {}) {
    let element;
    
    if (typeof selectorOrElement === 'string') {
        element = await findElementWithValidation(selectorOrElement, {
            ...options,
            mustBeVisible: true
        });
    } else {
        element = selectorOrElement;
    }
    
    if (!element) {
        console.error(`❌ Cannot set value: element not found or invalid`);
        return false;
    }
    
    try {
        // Use native property setter for React/Vue compatibility
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(element, value);
        
        // Focus element (required by Tradovate)
        element.focus();
        
        // Trigger events in order that Tradovate expects
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Add keyboard events if needed (for symbols/search)
        if (options.triggerKeyboard) {
            ['keydown', 'keypress', 'keyup'].forEach(eventType => {
                element.dispatchEvent(new KeyboardEvent(eventType, {
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
                    bubbles: true, cancelable: true
                }));
            });
        }
        
        // Wait for value to be processed
        await new Promise(resolve => setTimeout(resolve, options.delay || 100));
        
        // Validate the value was set
        const success = validateFormFieldValue(element, value);
        
        if (success) {
            console.log(`✅ Set form field value successfully: "${value}"`);
        } else {
            console.error(`❌ Failed to set form field value: "${value}"`);
        }
        
        return success;
    } catch (error) {
        console.error(`❌ Error setting form field value: ${error.message}`);
        return false;
    }
}

/**
 * Enhanced dropdown selection with validation and retry logic
 * @param {string} triggerSelector - CSS selector for dropdown trigger
 * @param {string} optionText - Text content of option to select
 * @param {Object} options - Options object
 * @returns {Promise<boolean>} True if selection was successful
 */
async function safeSelectDropdownOption(triggerSelector, optionText, options = {}) {
    const {
        timeout = 5000,
        retries = 3,
        dropdownSelector = '.dropdown-menu',
        delay = 300
    } = options;
    
    console.log(`🔍 Starting dropdown selection: ${triggerSelector} -> "${optionText}"`);
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            // Step 1: Click dropdown trigger
            const trigger = await findElementWithValidation(triggerSelector, {
                timeout: timeout / retries,
                mustBeClickable: true
            });
            
            if (!trigger) {
                console.warn(`❌ Dropdown trigger not found on attempt ${attempt}`);
                continue;
            }
            
            trigger.click();
            console.log(`✅ Clicked dropdown trigger on attempt ${attempt}`);
            
            // Step 2: Wait for dropdown to appear
            await new Promise(resolve => setTimeout(resolve, delay));
            
            // Step 3: Find and click option
            const dropdown = document.querySelector(dropdownSelector);
            if (!dropdown || !validateElementVisible(dropdown)) {
                console.warn(`❌ Dropdown menu not visible on attempt ${attempt}`);
                continue;
            }
            
            const options = Array.from(dropdown.querySelectorAll('li, .dropdown-item, [role="menuitem"]'));
            const targetOption = options.find(option => 
                option.textContent.trim() === optionText || 
                option.textContent.includes(optionText)
            );
            
            if (!targetOption) {
                console.warn(`❌ Option "${optionText}" not found on attempt ${attempt}`);
                continue;
            }
            
            if (!validateElementClickable(targetOption)) {
                console.warn(`❌ Option not clickable on attempt ${attempt}`);
                continue;
            }
            
            targetOption.click();
            console.log(`✅ Successfully selected dropdown option: "${optionText}"`);
            return true;
            
        } catch (error) {
            console.error(`❌ Error on dropdown selection attempt ${attempt}: ${error.message}`);
        }
    }
    
    console.error(`❌ Failed to select dropdown option after ${retries} attempts: "${optionText}"`);
    return false;
}

/**
 * Enhanced modal navigation with comprehensive validation
 * @param {string} buttonSelector - CSS selector for button to click
 * @param {Object} options - Options object
 * @returns {Promise<boolean>} True if button was clicked successfully
 */
async function safeModalAction(buttonSelector, options = {}) {
    const {
        timeout = 5000,
        waitAfterClick = 500,
        expectedText = null,
        mustBeInModal = true
    } = options;
    
    console.log(`🔍 Starting modal action: ${buttonSelector}`);
    
    // Validate we're in a modal context if required
    if (mustBeInModal) {
        const modal = document.querySelector('.modal, .modal-dialog, [role="dialog"]');
        if (!modal || !validateElementVisible(modal)) {
            console.error(`❌ Modal not found or not visible`);
            return false;
        }
        console.log(`✅ Confirmed modal context`);
    }
    
    // Find button with validation
    const button = await findElementWithValidation(buttonSelector, {
        timeout,
        mustBeClickable: true
    });
    
    if (!button) {
        console.error(`❌ Modal button not found: ${buttonSelector}`);
        return false;
    }
    
    // Validate button text if specified
    if (expectedText && !button.textContent.includes(expectedText)) {
        console.error(`❌ Button text mismatch. Expected: "${expectedText}", Got: "${button.textContent}"`);
        return false;
    }
    
    try {
        button.click();
        console.log(`✅ Modal button clicked successfully: ${buttonSelector}`);
        
        // Wait for modal transition
        if (waitAfterClick > 0) {
            await new Promise(resolve => setTimeout(resolve, waitAfterClick));
        }
        
        return true;
    } catch (error) {
        console.error(`❌ Error clicking modal button: ${error.message}`);
        return false;
    }
}

/**
 * Enhanced table data extraction with validation
 * @param {string} tableSelector - CSS selector for the table
 * @param {Object} options - Options object
 * @returns {Promise<Array>} Array of row objects
 */
async function safeExtractTableData(tableSelector, options = {}) {
    const {
        headerSelector = '[role="columnheader"], th',
        rowSelector = '.public_fixedDataTable_bodyRow, tbody tr',
        cellSelector = '[role="gridcell"], td',
        timeout = 5000,
        requireHeaders = true
    } = options;
    
    console.log(`🔍 Starting table data extraction: ${tableSelector}`);
    
    // Find table with validation
    const table = await findElementWithValidation(tableSelector, {
        timeout,
        mustBeVisible: true
    });
    
    if (!table) {
        console.error(`❌ Table not found: ${tableSelector}`);
        return [];
    }
    
    // Extract headers
    const headers = Array.from(table.querySelectorAll(headerSelector))
        .map(header => header.textContent.trim().replace(/[\u25b2\u25bc]/g, '').trim());
    
    if (requireHeaders && headers.length === 0) {
        console.error(`❌ No table headers found`);
        return [];
    }
    
    console.log(`✅ Found ${headers.length} table headers:`, headers);
    
    // Extract rows
    const rows = Array.from(table.querySelectorAll(rowSelector));
    if (rows.length === 0) {
        console.warn(`⚠️ No table rows found`);
        return [];
    }
    
    console.log(`✅ Found ${rows.length} table rows`);
    
    const extractedData = [];
    
    rows.forEach((row, index) => {
        const cells = Array.from(row.querySelectorAll(cellSelector));
        
        if (cells.length === 0) {
            console.warn(`⚠️ Row ${index} has no cells`);
            return;
        }
        
        const rowData = {};
        
        headers.forEach((header, cellIndex) => {
            if (cellIndex < cells.length) {
                let cellText = cells[cellIndex].textContent.trim();
                
                // Convert currency values to numbers
                if (cellText.startsWith('$')) {
                    try {
                        cellText = Number(cellText.replace(/[$,()]/g, '')) || 0;
                        if (cells[cellIndex].textContent.includes('(')) {
                            cellText = -Math.abs(cellText);
                        }
                    } catch (e) {
                        console.warn(`⚠️ Could not convert currency value: ${cellText}`);
                    }
                }
                
                rowData[header] = cellText;
            }
        });
        
        if (Object.keys(rowData).length > 0) {
            extractedData.push(rowData);
        }
    });
    
    console.log(`✅ Extracted ${extractedData.length} valid table rows`);
    return extractedData;
}

/**
 * Drag and drop simulation with validation
 * @param {Element} sourceElement - Element to drag
 * @param {Element} targetElement - Element to drop on
 * @param {Object} options - Options object
 * @returns {Promise<boolean>} True if drag and drop was successful
 */
async function safeDragAndDrop(sourceElement, targetElement, options = {}) {
    const { delay = 100 } = options;
    
    if (!sourceElement || !targetElement) {
        console.error(`❌ Invalid drag and drop elements`);
        return false;
    }
    
    if (!validateElementVisible(sourceElement) || !validateElementVisible(targetElement)) {
        console.error(`❌ Drag and drop elements not visible`);
        return false;
    }
    
    try {
        console.log(`🔍 Starting drag and drop: ${sourceElement.textContent?.trim()}`);
        
        // Create and dispatch drag events
        const dragStartEvent = new DragEvent('dragstart', { bubbles: true });
        const dragOverEvent = new DragEvent('dragover', { bubbles: true });
        const dropEvent = new DragEvent('drop', { bubbles: true });
        
        sourceElement.dispatchEvent(dragStartEvent);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        targetElement.dispatchEvent(dragOverEvent);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        targetElement.dispatchEvent(dropEvent);
        
        console.log(`✅ Drag and drop completed successfully`);
        return true;
        
    } catch (error) {
        console.error(`❌ Error during drag and drop: ${error.message}`);
        return false;
    }
}

// ============================================================================
// EXPORT FUNCTIONS FOR USE IN OTHER SCRIPTS
// ============================================================================

// Make functions available globally for Tampermonkey scripts
if (typeof window !== 'undefined') {
    window.domHelpers = {
        // Core validation functions
        waitForElement,
        validateElementExists,
        validateElementVisible,
        validateElementClickable,
        validateFormFieldValue,
        findElementWithValidation,
        
        // Safe interaction functions
        safeClick,
        safeSetValue,
        safeSelectDropdownOption,
        safeModalAction,
        safeExtractTableData,
        safeDragAndDrop,
        
        // Standardized timeout values for consistency
        timeouts: {
            short: 2000,      // Quick operations
            medium: 5000,     // Standard operations
            long: 10000,      // Complex operations
            tableLoad: 15000  // Table/data loading
        },
        
        // Common delay values
        delays: {
            click: 100,       // After clicking
            dropdown: 300,    // Dropdown appearance
            modal: 500,       // Modal transitions
            formInput: 200,   // Form field processing
            dragDrop: 150     // Drag and drop steps
        }
    };
    
    console.log('✅ Enhanced DOM Helpers loaded and available globally as window.domHelpers');
    console.log('📋 Available functions:', Object.keys(window.domHelpers).filter(key => typeof window.domHelpers[key] === 'function'));
}

// Also export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        waitForElement,
        validateElementExists,
        validateElementVisible,
        validateElementClickable,
        validateFormFieldValue,
        findElementWithValidation,
        safeClick,
        safeSetValue,
        safeSelectDropdownOption,
        safeModalAction,
        safeExtractTableData,
        safeDragAndDrop
    };
}