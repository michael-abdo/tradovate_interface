# Tampermonkey Script Integration with DOM Intelligence System
## Comprehensive Guide for Enhanced Script Reliability and Performance

This guide demonstrates how to integrate existing Tampermonkey scripts with the DOM Intelligence System to improve reliability, performance, and maintainability.

---

## 🚀 **INTEGRATION OVERVIEW**

The DOM Intelligence System provides Tampermonkey scripts with:
- **Intelligent Element Finding**: Adaptive selectors with fallback strategies
- **Performance Monitoring**: Real-time performance tracking and health monitoring
- **Validation Framework**: Element validation before operations
- **Error Recovery**: Automatic fallback mechanisms
- **Caching System**: Smart element caching for improved performance

---

## 📋 **QUICK START INTEGRATION**

### **Step 1: Add DOM Intelligence Client**

Add the DOM Intelligence client to your Tampermonkey script:

```javascript
// ==UserScript==
// @name         Your Enhanced Script
// @require      file:///Users/Mike/trading/scripts/tampermonkey/dom_intelligence_client.js
// @grant        none
// ==/UserScript==

// Create DOM Intelligence client
const domClient = new DOMIntelligenceClient({
    scriptName: 'your_script_name',
    debugMode: false  // Set to true for debugging
});
```

### **Step 2: Replace Direct DOM Queries**

**Before (Traditional Method):**
```javascript
// Fragile direct DOM query
const element = document.querySelector('#symbolInput');
if (element) {
    element.value = 'NQ';
    element.dispatchEvent(new Event('change'));
}
```

**After (DOM Intelligence):**
```javascript
// Robust DOM Intelligence query with fallbacks
try {
    await domClient.input('symbol_input', 'NQ');
    console.log('Symbol updated successfully');
} catch (error) {
    console.error('Failed to update symbol:', error.message);
}
```

### **Step 3: Use Intelligent Element Finding**

```javascript
// Find element with automatic fallbacks and validation
const element = await domClient.findElement('order_submit_button', {
    timeout: 5000,
    checkVisibility: true
});

// Click with validation
await domClient.click('order_submit_button');

// Extract data with enhanced processing
const accountData = await domClient.extractData('market_data_table');
```

---

## 🛠️ **COMPREHENSIVE INTEGRATION PATTERNS**

### **Pattern 1: Enhanced Element Finding**

**Traditional waitForElement:**
```javascript
function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const check = () => {
            const el = document.querySelector(selector);
            if (el) return resolve(el);
            setTimeout(check, 100);
        };
        check();
        setTimeout(() => reject('Timeout'), timeout);
    });
}
```

**DOM Intelligence Enhancement:**
```javascript
async function waitForElementIntelligent(elementType, options = {}) {
    try {
        // Uses multiple selectors, validation, and caching
        return await domClient.findElement(elementType, {
            timeout: options.timeout || 10000,
            checkVisibility: options.checkVisibility !== false
        });
    } catch (error) {
        console.error(`Enhanced element finding failed for ${elementType}:`, error.message);
        throw error;
    }
}
```

### **Pattern 2: Data Extraction with Validation**

**Traditional table data extraction:**
```javascript
function extractTableData() {
    const table = document.querySelector('.public_fixedDataTable_main');
    const rows = table.querySelectorAll('.bodyRow');
    // ... basic extraction logic
}
```

**DOM Intelligence Enhancement:**
```javascript
async function extractTableDataIntelligent() {
    try {
        // Finds table using multiple selectors and validates structure
        const tableData = await domClient.extractData('market_data_table', {
            includeHeaders: true,
            validateData: true
        });
        
        // Enhanced processing with error handling
        return processTableData(tableData);
    } catch (error) {
        console.error('Table extraction failed:', error.message);
        // Fallback to traditional method if needed
        return extractTableDataTraditional();
    }
}
```

### **Pattern 3: Form Interaction with Validation**

**Traditional form filling:**
```javascript
function fillForm(values) {
    document.querySelector('#symbolInput').value = values.symbol;
    document.querySelector('#quantityInput').value = values.quantity;
    document.querySelector('.submit-btn').click();
}
```

**DOM Intelligence Enhancement:**
```javascript
async function fillFormIntelligent(values) {
    const operations = [];
    
    try {
        // Input with validation and React event handling
        await domClient.input('symbol_input', values.symbol);
        operations.push('symbol_input');
        
        await domClient.input('quantity_input', values.quantity);
        operations.push('quantity_input');
        
        // Click with validation
        await domClient.click('order_submit_button');
        operations.push('order_submit_button');
        
        console.log('Form filled successfully');
        return { success: true, operations };
        
    } catch (error) {
        console.error('Form filling failed:', error.message);
        return { 
            success: false, 
            error: error.message, 
            completedOperations: operations 
        };
    }
}
```

---

## 📊 **PERFORMANCE MONITORING INTEGRATION**

### **Adding Performance Tracking**

```javascript
// Get performance report
function getScriptPerformance() {
    const report = domClient.getPerformanceReport();
    
    console.log('Script Performance Report:');
    console.log(`Total Operations: ${report.totalOperations}`);
    console.log(`Success Rate: ${(report.successRate * 100).toFixed(1)}%`);
    console.log(`Average Duration: ${report.averageDuration.toFixed(0)}ms`);
    console.log(`Health Status: ${report.healthStatus}`);
    
    return report;
}

// Monitor script health
setInterval(() => {
    const report = domClient.getPerformanceReport();
    if (report.healthStatus === 'critical') {
        console.warn('Script health is critical - consider troubleshooting');
    }
}, 30000); // Check every 30 seconds
```

### **Custom Performance Dashboard**

```javascript
function createPerformanceDashboard() {
    const dashboard = document.createElement('div');
    dashboard.style.cssText = `
        position: fixed; top: 10px; left: 10px; 
        background: rgba(0,0,0,0.8); color: white; 
        padding: 10px; border-radius: 5px; z-index: 10000;
        font-family: monospace; font-size: 12px;
    `;
    
    function updateDashboard() {
        const report = domClient.getPerformanceReport();
        const healthColor = {
            'healthy': 'green',
            'warning': 'orange', 
            'degraded': 'red',
            'critical': 'red'
        }[report.healthStatus] || 'gray';
        
        dashboard.innerHTML = `
            <div>Script: ${domClient.scriptName}</div>
            <div>Health: <span style="color: ${healthColor}">${report.healthStatus}</span></div>
            <div>Operations: ${report.totalOperations}</div>
            <div>Success: ${(report.successRate * 100).toFixed(1)}%</div>
            <div>Avg Time: ${report.averageDuration?.toFixed(0)}ms</div>
        `;
    }
    
    // Update every 5 seconds
    updateDashboard();
    setInterval(updateDashboard, 5000);
    
    document.body.appendChild(dashboard);
}
```

---

## 🔧 **SCRIPT-SPECIFIC INTEGRATION EXAMPLES**

### **Debug DOM Script Enhancement**

```javascript
// Enhanced DOM analysis with intelligence comparison
async function analyzeDOM() {
    const results = {
        traditional: await performTraditionalAnalysis(),
        intelligent: await performIntelligentAnalysis(),
        performance: domClient.getPerformanceReport()
    };
    
    // Compare methods and show improvements
    console.log('Analysis Results:', results);
    return results;
}

async function performIntelligentAnalysis() {
    const criticalElements = [
        'symbol_input', 'order_submit_button', 'account_selector',
        'market_data_table', 'login_username', 'login_password'
    ];
    
    const results = {};
    for (const elementType of criticalElements) {
        try {
            const element = await domClient.findElement(elementType, { timeout: 2000 });
            results[elementType] = {
                found: true,
                isVisible: element.offsetParent !== null,
                isEnabled: !element.disabled,
                boundingRect: element.getBoundingClientRect()
            };
        } catch (error) {
            results[elementType] = { found: false, error: error.message };
        }
    }
    
    return results;
}
```

### **Account Data Extraction Enhancement**

```javascript
// Enhanced account table data extraction
async function getAllAccountTableDataEnhanced() {
    const startTime = performance.now();
    
    try {
        // Use DOM Intelligence to find and extract table data
        const tableData = await domClient.extractData('market_data_table', {
            timeout: 10000,
            validateData: true
        });
        
        // Enhanced processing with validation
        const processedData = processAccountData(tableData);
        
        // Performance tracking
        const duration = performance.now() - startTime;
        console.log(`Data extraction completed in ${duration.toFixed(1)}ms`);
        
        return {
            success: true,
            data: processedData,
            performance: { duration, method: 'intelligent' },
            domHealth: domClient.getPerformanceReport()
        };
        
    } catch (error) {
        console.warn('DOM Intelligence extraction failed, using fallback');
        // Fallback to traditional method
        return await getAllAccountTableDataTraditional();
    }
}

function processAccountData(tableData) {
    return tableData.rows.map(row => {
        // Enhanced data processing with validation and type conversion
        const account = {};
        
        tableData.headers.forEach((header, index) => {
            const cellValue = Object.values(row)[index] || '';
            account[header] = processCellValue(cellValue, header);
        });
        
        // Add derived fields
        account.Platform = detectPlatform(account.Account);
        account.HealthScore = calculateHealthScore(account);
        account.Status = extractStatus(account.Phase);
        
        return account;
    });
}
```

### **Risk Settings Script Enhancement**

```javascript
// Enhanced risk settings automation
async function automateRiskSettings(accountId, settings) {
    const operations = [];
    
    try {
        // Find and click risk settings button
        await domClient.click('risk_settings_button', { timeout: 5000 });
        operations.push('risk_settings_button');
        
        // Wait for modal
        const modal = await domClient.findElement('risk_settings_modal', { timeout: 10000 });
        operations.push('risk_settings_modal');
        
        // Configure settings
        for (const [setting, value] of Object.entries(settings)) {
            await domClient.input(setting, value);
            operations.push(setting);
        }
        
        // Save settings
        await domClient.click('save_button');
        operations.push('save_button');
        
        return { 
            success: true, 
            operations,
            performance: domClient.getPerformanceReport()
        };
        
    } catch (error) {
        console.error('Risk settings automation failed:', error.message);
        return { 
            success: false, 
            error: error.message,
            completedOperations: operations 
        };
    }
}
```

---

## 🏥 **ERROR HANDLING AND RECOVERY**

### **Robust Error Handling Pattern**

```javascript
async function performCriticalOperation() {
    const maxRetries = 3;
    let attempt = 0;
    
    while (attempt < maxRetries) {
        try {
            // Attempt operation with DOM Intelligence
            await domClient.click('order_submit_button');
            console.log('Operation succeeded');
            return { success: true, attempt: attempt + 1 };
            
        } catch (error) {
            attempt++;
            console.warn(`Attempt ${attempt} failed: ${error.message}`);
            
            if (attempt >= maxRetries) {
                // All attempts failed - try emergency fallback
                console.error('All attempts failed, trying emergency fallback');
                return await performEmergencyFallback();
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
    }
}

async function performEmergencyFallback() {
    try {
        // Direct DOM manipulation as last resort
        const button = document.querySelector('.btn-group .btn-primary');
        if (button) {
            button.click();
            return { success: true, method: 'emergency_fallback' };
        } else {
            throw new Error('Emergency fallback also failed');
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

### **Health Monitoring and Alerts**

```javascript
// Monitor script health and alert on issues
function setupHealthMonitoring() {
    setInterval(() => {
        const health = domClient.getPerformanceReport();
        
        // Alert on critical health issues
        if (health.healthStatus === 'critical') {
            showHealthAlert('Critical script health detected', health);
        }
        
        // Alert on low success rate
        if (health.successRate < 0.7) {
            showHealthAlert('Low operation success rate', health);
        }
        
        // Alert on slow performance
        if (health.averageDuration > 5000) {
            showHealthAlert('Slow operation performance', health);
        }
        
    }, 30000); // Check every 30 seconds
}

function showHealthAlert(message, healthData) {
    console.warn(`Health Alert: ${message}`);
    console.warn('Health Data:', healthData);
    
    // Optionally show visual alert
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed; top: 50px; right: 10px;
        background: red; color: white; padding: 10px;
        border-radius: 5px; z-index: 10001;
    `;
    alert.textContent = `⚠️ ${message}`;
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}
```

---

## 📈 **MIGRATION CHECKLIST**

### **Pre-Migration Assessment**
- [ ] Identify all DOM queries in existing script
- [ ] Document element selectors used
- [ ] Note any timing-dependent operations
- [ ] Identify critical vs non-critical operations

### **Integration Steps**
- [ ] Add DOM Intelligence client to script
- [ ] Replace direct queries with DOM Intelligence methods
- [ ] Add error handling and fallback mechanisms
- [ ] Implement performance monitoring
- [ ] Test with real Tradovate interface

### **Post-Migration Validation**
- [ ] Verify all operations work correctly
- [ ] Check performance improvements
- [ ] Monitor error rates and health status
- [ ] Validate fallback mechanisms work
- [ ] Document any remaining issues

### **Optimization Steps**
- [ ] Fine-tune timeout values
- [ ] Optimize element caching settings
- [ ] Adjust validation requirements
- [ ] Implement script-specific enhancements
- [ ] Add custom performance dashboards

---

## 🎯 **BEST PRACTICES**

### **Do's**
✅ **Use semantic element types** instead of raw selectors  
✅ **Implement proper error handling** with fallback mechanisms  
✅ **Monitor performance** regularly and adjust timeouts  
✅ **Validate operations** before considering them successful  
✅ **Cache frequently accessed elements** appropriately  
✅ **Use appropriate timeout values** for different operations  

### **Don'ts**
❌ **Don't mix DOM Intelligence with direct DOM queries** unnecessarily  
❌ **Don't ignore error messages** or health warnings  
❌ **Don't use overly aggressive timeouts** that may cause failures  
❌ **Don't skip validation** for critical trading operations  
❌ **Don't disable debugging** until script is fully stable  

### **Performance Guidelines**
- **Critical Operations**: < 1000ms timeout, minimal validation
- **Standard Operations**: 2000-5000ms timeout, full validation  
- **Background Operations**: 10000ms+ timeout, comprehensive validation
- **Data Extraction**: Variable timeout based on data size

---

## 🔍 **TROUBLESHOOTING GUIDE**

### **Common Issues and Solutions**

**Issue: Elements not found**
```javascript
// Check if element types are correctly defined
const strategy = domClient.getElementStrategy('your_element_type');
if (!strategy) {
    console.error('Element type not found in registry');
    // Add custom element definition or use fallback
}
```

**Issue: Slow performance**
```javascript
// Check performance report
const report = domClient.getPerformanceReport();
console.log('Average duration:', report.averageDuration);

// Optimize by adjusting timeouts or caching
domClient.cacheTimeout = 60000; // Increase cache timeout
```

**Issue: Validation failures**
```javascript
// Debug validation by checking element properties
const element = await domClient.findElement('element_type');
console.log('Element properties:', {
    tagName: element.tagName,
    className: element.className,
    visible: element.offsetParent !== null,
    enabled: !element.disabled
});
```

---

This integration guide provides a comprehensive framework for enhancing Tampermonkey scripts with DOM Intelligence capabilities, ensuring improved reliability, performance, and maintainability for Tradovate automation.