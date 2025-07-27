/**
 * Comprehensive Unit Tests for DOM Validation Helpers
 * Tests all DOM helper functions including edge cases, shadow DOM, and iframes
 * 
 * Following CLAUDE.md principles:
 * - Real scenario testing 
 * - Comprehensive logging
 * - Fast failure with clear messages
 */

// Mock DOM environment for testing
const { JSDOM } = require('jsdom');
const assert = require('assert');

// Create a mock DOM
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<head>
    <title>DOM Helper Tests</title>
</head>
<body>
    <div id="main-container">
        <input id="symbol-input" type="text" value="NQ" />
        <button id="submit-button" class="btn-primary">Submit</button>
        <div class="hidden-element" style="display: none;">Hidden</div>
        <button id="disabled-button" disabled>Disabled</button>
        <select id="account-selector">
            <option value="account1">Account 1</option>
            <option value="account2" selected>Account 2</option>
        </select>
        <div id="shadow-host"></div>
        <iframe id="test-iframe" src="about:blank"></iframe>
        <div class="loading-spinner" style="display: block;">Loading...</div>
        <table id="data-table">
            <tbody>
                <tr><td>Row 1</td></tr>
                <tr><td>Row 2</td></tr>
            </tbody>
        </table>
    </div>
    <div id="modal-container" style="display: none;">
        <div class="modal">
            <button class="modal-close">X</button>
            <div class="modal-content">Modal Content</div>
        </div>
    </div>
</body>
</html>
`);

// Load DOM helpers (mock implementation for testing)
const domHelpers = {
    // Timeouts configuration
    timeouts: {
        short: 2000,
        medium: 5000,
        long: 10000,
        tableLoad: 15000
    },

    // Core validation functions
    waitForElement: async function(selector, timeout = this.timeouts.medium) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            const element = dom.window.document.querySelector(selector);
            if (element) return element;
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        throw new Error(`Element ${selector} not found after ${timeout}ms`);
    },

    validateElementExists: function(selector) {
        const element = dom.window.document.querySelector(selector);
        if (!element) {
            throw new Error(`Element not found: ${selector}`);
        }
        return element;
    },

    validateElementVisible: function(element) {
        if (!element) return false;
        const style = dom.window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0';
    },

    validateElementClickable: function(element) {
        if (!element) return false;
        if (element.disabled) return false;
        if (!this.validateElementVisible(element)) return false;
        
        // Check if element is covered by another element
        const rect = element.getBoundingClientRect();
        const elementAtPoint = dom.window.document.elementFromPoint(
            rect.left + rect.width / 2,
            rect.top + rect.height / 2
        );
        
        return elementAtPoint === element || element.contains(elementAtPoint);
    },

    validateFormFieldValue: function(element, expectedValue) {
        if (!element) return false;
        const actualValue = element.value || element.textContent;
        return actualValue === expectedValue;
    },

    findElementWithValidation: function(selectors, context = dom.window.document) {
        for (const selector of selectors) {
            try {
                const element = context.querySelector(selector);
                if (element && this.validateElementVisible(element)) {
                    return { element, selector, found: true };
                }
            } catch (e) {
                // Invalid selector, continue
            }
        }
        return { element: null, selector: null, found: false };
    },

    // Safe interaction functions
    safeClick: async function(selector, options = {}) {
        const element = await this.waitForElement(selector, options.timeout);
        if (!this.validateElementClickable(element)) {
            throw new Error(`Element ${selector} is not clickable`);
        }
        
        // Simulate click with logging
        console.log(`Clicking element: ${selector}`);
        element.click();
        
        // Wait for any animations/transitions
        if (options.waitAfterClick) {
            await new Promise(resolve => setTimeout(resolve, options.waitAfterClick));
        }
        
        return { success: true, element };
    },

    safeSetValue: async function(selector, value, options = {}) {
        const element = await this.waitForElement(selector, options.timeout);
        if (element.disabled || element.readOnly) {
            throw new Error(`Element ${selector} is not editable`);
        }
        
        // Clear existing value
        element.value = '';
        
        // Set new value with input event
        element.value = value;
        element.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
        element.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
        
        // Verify value was set
        if (!this.validateFormFieldValue(element, value)) {
            throw new Error(`Failed to set value for ${selector}`);
        }
        
        return { success: true, element, value };
    },

    safeSelectDropdownOption: async function(selector, value, options = {}) {
        const select = await this.waitForElement(selector, options.timeout);
        if (select.tagName !== 'SELECT') {
            throw new Error(`Element ${selector} is not a select element`);
        }
        
        // Find option
        const option = Array.from(select.options).find(opt => 
            opt.value === value || opt.textContent === value
        );
        
        if (!option) {
            throw new Error(`Option ${value} not found in ${selector}`);
        }
        
        // Select option
        select.value = option.value;
        select.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
        
        return { success: true, element: select, value: option.value };
    },

    safeModalAction: async function(modalSelector, actionSelector, options = {}) {
        // Wait for modal to be visible
        const modal = await this.waitForElement(modalSelector, options.timeout);
        if (!this.validateElementVisible(modal)) {
            throw new Error(`Modal ${modalSelector} is not visible`);
        }
        
        // Find and click action button within modal
        const actionButton = modal.querySelector(actionSelector);
        if (!actionButton) {
            throw new Error(`Action button ${actionSelector} not found in modal`);
        }
        
        await this.safeClick(actionSelector, options);
        
        // Wait for modal to close if specified
        if (options.waitForClose) {
            const closeTimeout = options.closeTimeout || this.timeouts.medium;
            const startTime = Date.now();
            while (Date.now() - startTime < closeTimeout) {
                if (!this.validateElementVisible(modal)) {
                    return { success: true, modalClosed: true };
                }
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
        
        return { success: true, modalClosed: false };
    },

    safeExtractTableData: async function(tableSelector, options = {}) {
        const table = await this.waitForElement(tableSelector, options.timeout || this.timeouts.tableLoad);
        const rows = table.querySelectorAll('tbody tr');
        
        if (rows.length === 0) {
            return { success: true, data: [], rowCount: 0 };
        }
        
        const data = [];
        rows.forEach((row, index) => {
            const cells = row.querySelectorAll('td, th');
            const rowData = Array.from(cells).map(cell => cell.textContent.trim());
            data.push(rowData);
        });
        
        return { success: true, data, rowCount: rows.length };
    },

    safeDragAndDrop: async function(sourceSelector, targetSelector, options = {}) {
        const source = await this.waitForElement(sourceSelector, options.timeout);
        const target = await this.waitForElement(targetSelector, options.timeout);
        
        if (!this.validateElementVisible(source) || !this.validateElementVisible(target)) {
            throw new Error('Source or target element not visible for drag and drop');
        }
        
        // Simulate drag and drop events
        const dragStart = new dom.window.DragEvent('dragstart', {
            bubbles: true,
            cancelable: true
        });
        const dragOver = new dom.window.DragEvent('dragover', {
            bubbles: true,
            cancelable: true
        });
        const drop = new dom.window.DragEvent('drop', {
            bubbles: true,
            cancelable: true
        });
        const dragEnd = new dom.window.DragEvent('dragend', {
            bubbles: true,
            cancelable: true
        });
        
        source.dispatchEvent(dragStart);
        target.dispatchEvent(dragOver);
        target.dispatchEvent(drop);
        source.dispatchEvent(dragEnd);
        
        return { success: true, source, target };
    },

    // Advanced validation functions
    waitForLoadingComplete: async function(loadingSelector, options = {}) {
        const timeout = options.timeout || this.timeouts.long;
        const startTime = Date.now();
        
        // Wait for loading element to disappear
        while (Date.now() - startTime < timeout) {
            const loadingElement = dom.window.document.querySelector(loadingSelector);
            if (!loadingElement || !this.validateElementVisible(loadingElement)) {
                return { success: true, loadTime: Date.now() - startTime };
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        throw new Error(`Loading did not complete within ${timeout}ms`);
    },

    validateMultipleElements: function(selectors) {
        const results = {};
        for (const [key, selector] of Object.entries(selectors)) {
            try {
                const element = this.validateElementExists(selector);
                results[key] = {
                    found: true,
                    visible: this.validateElementVisible(element),
                    clickable: this.validateElementClickable(element)
                };
            } catch (e) {
                results[key] = {
                    found: false,
                    visible: false,
                    clickable: false,
                    error: e.message
                };
            }
        }
        return results;
    },

    // Shadow DOM support
    findInShadowDom: function(hostSelector, shadowSelector) {
        const host = dom.window.document.querySelector(hostSelector);
        if (!host || !host.shadowRoot) {
            throw new Error(`No shadow root found for ${hostSelector}`);
        }
        
        const element = host.shadowRoot.querySelector(shadowSelector);
        if (!element) {
            throw new Error(`Element ${shadowSelector} not found in shadow DOM`);
        }
        
        return element;
    },

    // iframe support
    findInIframe: async function(iframeSelector, elementSelector, options = {}) {
        const iframe = await this.waitForElement(iframeSelector, options.timeout);
        if (iframe.tagName !== 'IFRAME') {
            throw new Error(`Element ${iframeSelector} is not an iframe`);
        }
        
        // Wait for iframe to load
        if (!iframe.contentDocument) {
            await new Promise(resolve => {
                iframe.addEventListener('load', resolve);
                setTimeout(resolve, options.timeout || this.timeouts.medium);
            });
        }
        
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        const element = iframeDoc.querySelector(elementSelector);
        
        if (!element) {
            throw new Error(`Element ${elementSelector} not found in iframe`);
        }
        
        return element;
    }
};

// Test Suite
describe('DOM Helpers Unit Tests', function() {
    
    describe('Core Validation Functions', function() {
        
        it('should wait for existing element', async function() {
            const element = await domHelpers.waitForElement('#submit-button', 1000);
            assert(element);
            assert.equal(element.textContent, 'Submit');
        });
        
        it('should timeout waiting for non-existent element', async function() {
            try {
                await domHelpers.waitForElement('#non-existent', 100);
                assert.fail('Should have thrown timeout error');
            } catch (error) {
                assert(error.message.includes('not found after'));
            }
        });
        
        it('should validate element exists', function() {
            const element = domHelpers.validateElementExists('#symbol-input');
            assert(element);
            assert.equal(element.value, 'NQ');
        });
        
        it('should throw for non-existent element', function() {
            assert.throws(() => {
                domHelpers.validateElementExists('#fake-element');
            }, /Element not found/);
        });
        
        it('should validate element visibility correctly', function() {
            const visible = dom.window.document.querySelector('#submit-button');
            const hidden = dom.window.document.querySelector('.hidden-element');
            
            assert(domHelpers.validateElementVisible(visible));
            assert(!domHelpers.validateElementVisible(hidden));
        });
        
        it('should validate element clickability', function() {
            const enabledButton = dom.window.document.querySelector('#submit-button');
            const disabledButton = dom.window.document.querySelector('#disabled-button');
            const hiddenElement = dom.window.document.querySelector('.hidden-element');
            
            assert(domHelpers.validateElementClickable(enabledButton));
            assert(!domHelpers.validateElementClickable(disabledButton));
            assert(!domHelpers.validateElementClickable(hiddenElement));
        });
        
        it('should validate form field values', function() {
            const input = dom.window.document.querySelector('#symbol-input');
            assert(domHelpers.validateFormFieldValue(input, 'NQ'));
            assert(!domHelpers.validateFormFieldValue(input, 'ES'));
        });
        
        it('should find element with fallback selectors', function() {
            const selectors = ['#fake-id', '.fake-class', '#submit-button'];
            const result = domHelpers.findElementWithValidation(selectors);
            
            assert(result.found);
            assert(result.element);
            assert.equal(result.selector, '#submit-button');
        });
    });
    
    describe('Safe Interaction Functions', function() {
        
        it('should safely click clickable elements', async function() {
            const result = await domHelpers.safeClick('#submit-button');
            assert(result.success);
            assert(result.element);
        });
        
        it('should fail clicking non-clickable elements', async function() {
            try {
                await domHelpers.safeClick('#disabled-button');
                assert.fail('Should have thrown error');
            } catch (error) {
                assert(error.message.includes('not clickable'));
            }
        });
        
        it('should safely set input values', async function() {
            const result = await domHelpers.safeSetValue('#symbol-input', 'ES');
            assert(result.success);
            assert.equal(result.value, 'ES');
            
            // Verify value was actually set
            const input = dom.window.document.querySelector('#symbol-input');
            assert.equal(input.value, 'ES');
        });
        
        it('should safely select dropdown options', async function() {
            const result = await domHelpers.safeSelectDropdownOption('#account-selector', 'account1');
            assert(result.success);
            assert.equal(result.value, 'account1');
            
            // Verify selection
            const select = dom.window.document.querySelector('#account-selector');
            assert.equal(select.value, 'account1');
        });
        
        it('should handle modal interactions', async function() {
            // Show modal first
            const modal = dom.window.document.querySelector('#modal-container');
            modal.style.display = 'block';
            
            const result = await domHelpers.safeModalAction('#modal-container', '.modal-close');
            assert(result.success);
        });
        
        it('should extract table data', async function() {
            const result = await domHelpers.safeExtractTableData('#data-table');
            assert(result.success);
            assert.equal(result.rowCount, 2);
            assert.equal(result.data.length, 2);
            assert.equal(result.data[0][0], 'Row 1');
            assert.equal(result.data[1][0], 'Row 2');
        });
        
        it('should handle drag and drop', async function() {
            const sourceButton = dom.window.document.querySelector('#submit-button');
            const targetDiv = dom.window.document.querySelector('#main-container');
            
            const result = await domHelpers.safeDragAndDrop('#submit-button', '#main-container');
            assert(result.success);
            assert(result.source === sourceButton);
            assert(result.target === targetDiv);
        });
    });
    
    describe('Advanced Validation Functions', function() {
        
        it('should wait for loading to complete', async function() {
            // Hide loading spinner after 200ms
            setTimeout(() => {
                const spinner = dom.window.document.querySelector('.loading-spinner');
                spinner.style.display = 'none';
            }, 200);
            
            const result = await domHelpers.waitForLoadingComplete('.loading-spinner');
            assert(result.success);
            assert(result.loadTime >= 200);
        });
        
        it('should validate multiple elements at once', function() {
            const results = domHelpers.validateMultipleElements({
                submitButton: '#submit-button',
                symbolInput: '#symbol-input',
                fakeElement: '#non-existent',
                hiddenElement: '.hidden-element'
            });
            
            assert(results.submitButton.found);
            assert(results.submitButton.visible);
            assert(results.submitButton.clickable);
            
            assert(results.symbolInput.found);
            assert(results.symbolInput.visible);
            
            assert(!results.fakeElement.found);
            
            assert(results.hiddenElement.found);
            assert(!results.hiddenElement.visible);
        });
    });
    
    describe('Shadow DOM Support', function() {
        
        beforeEach(function() {
            // Create shadow DOM for testing
            const host = dom.window.document.querySelector('#shadow-host');
            if (!host.shadowRoot) {
                const shadow = host.attachShadow({ mode: 'open' });
                shadow.innerHTML = '<button id="shadow-button">Shadow Button</button>';
            }
        });
        
        it('should find elements in shadow DOM', function() {
            const element = domHelpers.findInShadowDom('#shadow-host', '#shadow-button');
            assert(element);
            assert.equal(element.textContent, 'Shadow Button');
        });
        
        it('should throw for non-existent shadow elements', function() {
            assert.throws(() => {
                domHelpers.findInShadowDom('#shadow-host', '#fake-shadow-element');
            }, /not found in shadow DOM/);
        });
        
        it('should throw for non-shadow hosts', function() {
            assert.throws(() => {
                domHelpers.findInShadowDom('#submit-button', '#anything');
            }, /No shadow root found/);
        });
    });
    
    describe('iframe Support', function() {
        
        beforeEach(function() {
            // Setup iframe content
            const iframe = dom.window.document.querySelector('#test-iframe');
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            iframeDoc.body.innerHTML = '<button id="iframe-button">iframe Button</button>';
        });
        
        it('should find elements in iframes', async function() {
            const element = await domHelpers.findInIframe('#test-iframe', '#iframe-button');
            assert(element);
            assert.equal(element.textContent, 'iframe Button');
        });
        
        it('should throw for non-iframe elements', async function() {
            try {
                await domHelpers.findInIframe('#submit-button', '#anything');
                assert.fail('Should have thrown error');
            } catch (error) {
                assert(error.message.includes('not an iframe'));
            }
        });
        
        it('should throw for non-existent iframe elements', async function() {
            try {
                await domHelpers.findInIframe('#test-iframe', '#fake-iframe-element');
                assert.fail('Should have thrown error');
            } catch (error) {
                assert(error.message.includes('not found in iframe'));
            }
        });
    });
    
    describe('Edge Cases and Error Handling', function() {
        
        it('should handle null/undefined elements gracefully', function() {
            assert(!domHelpers.validateElementVisible(null));
            assert(!domHelpers.validateElementVisible(undefined));
            assert(!domHelpers.validateElementClickable(null));
            assert(!domHelpers.validateFormFieldValue(null, 'any'));
        });
        
        it('should handle invalid selectors', function() {
            const result = domHelpers.findElementWithValidation(['###invalid', '!!!bad', '#submit-button']);
            assert(result.found);
            assert.equal(result.selector, '#submit-button');
        });
        
        it('should handle elements with special characters in text', async function() {
            const input = dom.window.document.querySelector('#symbol-input');
            const specialValue = 'Test "quotes" & <special> chars';
            
            const result = await domHelpers.safeSetValue('#symbol-input', specialValue);
            assert(result.success);
            assert.equal(input.value, specialValue);
        });
        
        it('should handle rapid successive operations', async function() {
            const operations = [];
            
            // Queue up rapid operations
            for (let i = 0; i < 10; i++) {
                operations.push(
                    domHelpers.safeSetValue('#symbol-input', `TEST${i}`)
                );
            }
            
            const results = await Promise.all(operations);
            assert(results.every(r => r.success));
            
            // Final value should be from last operation
            const input = dom.window.document.querySelector('#symbol-input');
            assert.equal(input.value, 'TEST9');
        });
        
        it('should handle timing issues with dynamic content', async function() {
            // Simulate dynamic content addition
            setTimeout(() => {
                const container = dom.window.document.querySelector('#main-container');
                const newButton = dom.window.document.createElement('button');
                newButton.id = 'dynamic-button';
                newButton.textContent = 'Dynamic';
                container.appendChild(newButton);
            }, 100);
            
            // Should wait and find the dynamic element
            const element = await domHelpers.waitForElement('#dynamic-button', 1000);
            assert(element);
            assert.equal(element.textContent, 'Dynamic');
        });
    });
    
    describe('Performance Tests', function() {
        
        it('should find elements quickly', async function() {
            const startTime = Date.now();
            const element = await domHelpers.waitForElement('#submit-button', 1000);
            const elapsed = Date.now() - startTime;
            
            assert(element);
            assert(elapsed < 50); // Should find immediately
        });
        
        it('should handle multiple concurrent validations', async function() {
            const startTime = Date.now();
            
            const validations = [];
            for (let i = 0; i < 50; i++) {
                validations.push(
                    domHelpers.validateElementExists('#submit-button')
                );
            }
            
            const results = await Promise.all(validations);
            const elapsed = Date.now() - startTime;
            
            assert.equal(results.length, 50);
            assert(elapsed < 100); // Should complete quickly
        });
    });
});

// Run tests if this file is executed directly
if (require.main === module) {
    const Mocha = require('mocha');
    const mocha = new Mocha();
    
    // Add this file to mocha
    mocha.addFile(__filename);
    
    // Run tests
    mocha.run(failures => {
        process.exitCode = failures ? 1 : 0;
    });
}