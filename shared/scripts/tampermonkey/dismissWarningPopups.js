// Auto-dismiss warning popups for Tradovate
(function() {
    'use strict';
    
    console.log('📋 Warning popup dismisser initialized');
    
    // Track dismissed popups to avoid duplicate logging
    const dismissedPopups = new WeakSet();
    
    // Selectors for warning/alert popup buttons
    const POPUP_BUTTON_SELECTORS = [
        // Alert close buttons
        '.alert button.close',
        '.alert button[class*="close"]',
        '.alert button[aria-label="Close"]',
        '.alert button[aria-label="close"]',
        
        // Modal close buttons
        '.modal button.close',
        '.modal button[class*="close"]',
        '.modal-header button.close',
        '.modal-header button[aria-label="Close"]',
        
        // Warning specific buttons
        '.warning button',
        '.alert-warning button',
        'div[class*="warning"] button',
        'div[class*="alert"] button',
        
        // Generic OK/Dismiss buttons in popups
        '.modal button:contains("OK")',
        '.alert button:contains("OK")',
        '.modal button:contains("Dismiss")',
        '.alert button:contains("Dismiss")',
        
        // Tradovate specific patterns
        'button[class*="btn-close"]',
        'button[class*="dismiss"]',
        '.notification button.close',
        '.toast button.close'
    ];
    
    function findAndDismissPopups() {
        // Try each selector
        for (const selector of POPUP_BUTTON_SELECTORS) {
            try {
                // Handle :contains pseudo-selector manually
                if (selector.includes(':contains')) {
                    const [baseSelector, containsText] = selector.split(':contains');
                    const text = containsText.replace(/[()'"]/g, '');
                    const buttons = document.querySelectorAll(baseSelector.trim());
                    
                    buttons.forEach(button => {
                        if (button.textContent.includes(text) && 
                            !dismissedPopups.has(button) && 
                            isElementVisible(button)) {
                            dismissPopup(button, selector);
                        }
                    });
                } else {
                    // Regular selectors
                    const buttons = document.querySelectorAll(selector);
                    buttons.forEach(button => {
                        if (!dismissedPopups.has(button) && isElementVisible(button)) {
                            dismissPopup(button, selector);
                        }
                    });
                }
            } catch (e) {
                // Ignore selector errors
            }
        }
    }
    
    function isElementVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') {
            return false;
        }
        
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }
    
    function dismissPopup(button, selector) {
        try {
            // Mark as dismissed before clicking to avoid race conditions
            dismissedPopups.add(button);
            
            // Get popup container for logging
            const popup = button.closest('.alert, .modal, .warning, .notification, .toast');
            const popupText = popup ? popup.textContent.slice(0, 100) : 'Unknown popup';
            
            console.log(`🚨 Dismissing popup: "${popupText.trim()}..." via ${selector}`);
            
            // Click the button
            button.click();
            
            // Also try dispatching a click event if direct click doesn't work
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            button.dispatchEvent(clickEvent);
            
        } catch (e) {
            console.error('❌ Error dismissing popup:', e);
        }
    }
    
    // Start monitoring for popups
    const checkInterval = setInterval(findAndDismissPopups, 500);
    
    // Also check immediately on page changes
    const observer = new MutationObserver(() => {
        findAndDismissPopups();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Initial check
    findAndDismissPopups();
    
    console.log('✅ Warning popup dismisser active - checking every 500ms');
    
    // Cleanup function if needed
    window.stopPopupDismisser = function() {
        clearInterval(checkInterval);
        observer.disconnect();
        console.log('🛑 Warning popup dismisser stopped');
    };
})();