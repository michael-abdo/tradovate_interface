// ==UserScript==
// @name         Enhanced DOM Analysis with Intelligence
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Analyze Tradovate DOM with DOM Intelligence System integration
// @match        https://trader.tradovate.com/*
// @require      file:///Users/Mike/trading/scripts/tampermonkey/dom_intelligence_client.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    // Create DOM Intelligence client for this script
    const domClient = new DOMIntelligenceClient({
        scriptName: 'enhanced_dom_debug',
        debugMode: true
    });
    
    // Enhanced DOM analysis function using DOM Intelligence
    async function analyzeTradevatedomWithIntelligence() {
        const results = {
            timestamp: new Date().toISOString(),
            domIntelligenceStatus: domClient.getPerformanceReport(),
            traditionalAnalysis: {},
            intelligentAnalysis: {},
            performanceComparison: {}
        };
        
        try {
            // Traditional DOM analysis (for comparison)
            const traditionalStart = performance.now();
            results.traditionalAnalysis = await performTraditionalAnalysis();
            const traditionalDuration = performance.now() - traditionalStart;
            
            // Enhanced analysis using DOM Intelligence
            const intelligentStart = performance.now();
            results.intelligentAnalysis = await performIntelligentAnalysis();
            const intelligentDuration = performance.now() - intelligentStart;
            
            // Performance comparison
            results.performanceComparison = {
                traditionalDuration: traditionalDuration,
                intelligentDuration: intelligentDuration,
                speedImprovement: traditionalDuration > 0 ? ((traditionalDuration - intelligentDuration) / traditionalDuration * 100).toFixed(2) + '%' : 'N/A'
            };
            
        } catch (error) {
            results.error = error.message;
            console.error('DOM Analysis error:', error);
        }
        
        return results;
    }
    
    // Traditional DOM analysis (original method)
    async function performTraditionalAnalysis() {
        const results = {
            tables: 0,
            potentialAccountTables: [],
            publicDataTables: [],
            accountsModuleFound: false,
            sidebarFound: false,
            url: window.location.href,
            title: document.title
        };
        
        // Find all tables
        const allTables = document.querySelectorAll('table');
        results.tables = allTables.length;
        
        // Find all data tables
        const dataTables = document.querySelectorAll('.data-table');
        dataTables.forEach((table, idx) => {
            results.potentialAccountTables.push({
                index: idx,
                className: table.className,
                childCount: table.children.length,
                headers: [...table.querySelectorAll('th, [role="columnheader"]')].map(h => h.textContent.trim())
            });
        });
        
        // Find FixedDataTable elements
        const fixedDataTables = document.querySelectorAll('.public_fixedDataTable_main');
        fixedDataTables.forEach((table, idx) => {
            const headers = [...table.querySelectorAll('[role="columnheader"]')].map(h => h.textContent.trim());
            const rows = table.querySelectorAll('.public_fixedDataTable_bodyRow');
            
            let sampleData = {};
            if (rows.length > 0) {
                const firstRow = rows[0];
                const cells = firstRow.querySelectorAll('[role="gridcell"]');
                headers.forEach((header, i) => {
                    if (i < cells.length) {
                        sampleData[header] = cells[i].innerText.trim();
                    }
                });
            }
            
            results.publicDataTables.push({
                index: idx,
                position: {
                    top: table.offsetTop,
                    left: table.offsetLeft,
                    width: table.offsetWidth,
                    height: table.offsetHeight
                },
                headerCount: headers.length,
                headers: headers,
                rowCount: rows.length,
                sampleData: sampleData,
                isVisible: table.offsetParent !== null
            });
        });
        
        // Look for accounts module
        const accountsModule = document.querySelector('.module.accounts');
        if (accountsModule) {
            results.accountsModuleFound = true;
            results.accountsModuleInfo = {
                childCount: accountsModule.children.length,
                text: accountsModule.innerText.substring(0, 100) + '...'
            };
        }
        
        // Look for sidebar
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            results.sidebarFound = true;
            const sidebarTables = sidebar.querySelectorAll('.public_fixedDataTable_main');
            results.sidebarTableCount = sidebarTables.length;
            
            if (sidebarTables.length > 0) {
                const firstTable = sidebarTables[0];
                results.sidebarFirstTableHeaders = [...firstTable.querySelectorAll('[role="columnheader"]')].map(h => h.textContent.trim());
            }
        }
        
        return results;
    }
    
    // Enhanced analysis using DOM Intelligence
    async function performIntelligentAnalysis() {
        const results = {
            criticalElements: {},
            marketDataAnalysis: {},
            uiElementsHealth: {},
            recommendations: []
        };
        
        // Test critical trading elements
        const criticalElementTypes = [
            'symbol_input',
            'order_submit_button', 
            'account_selector',
            'market_data_table',
            'login_username',
            'login_password'
        ];
        
        for (const elementType of criticalElementTypes) {
            try {
                const element = await domClient.findElement(elementType, { timeout: 2000 });
                results.criticalElements[elementType] = {
                    found: true,
                    isVisible: element.offsetParent !== null,
                    isEnabled: !element.disabled,
                    tagName: element.tagName,
                    className: element.className,
                    id: element.id,
                    position: {
                        top: element.offsetTop,
                        left: element.offsetLeft,
                        width: element.offsetWidth,
                        height: element.offsetHeight
                    }
                };
            } catch (error) {
                results.criticalElements[elementType] = {
                    found: false,
                    error: error.message
                };
            }
        }
        
        // Enhanced market data analysis
        try {
            const marketTable = await domClient.findElement('market_data_table', { timeout: 3000 });
            const tableData = await domClient.extractData('market_data_table');
            
            results.marketDataAnalysis = {
                tableFound: true,
                structure: tableData,
                performance: {
                    rowCount: tableData.rowCount,
                    columnCount: tableData.headers.length,
                    dataQuality: tableData.rows.every(row => Object.values(row).some(val => val.trim() !== ''))
                }
            };
        } catch (error) {
            results.marketDataAnalysis = {
                tableFound: false,
                error: error.message
            };
        }
        
        // UI Elements Health Check
        results.uiElementsHealth = {
            overallHealth: domClient.healthStatus,
            performanceReport: domClient.getPerformanceReport(),
            elementCacheStatus: {
                cacheSize: domClient.elementCache.size,
                cacheTimeout: domClient.cacheTimeout
            }
        };
        
        // Generate recommendations based on analysis
        results.recommendations = generateRecommendations(results);
        
        return results;
    }
    
    // Generate intelligent recommendations
    function generateRecommendations(analysisResults) {
        const recommendations = [];
        
        // Check for missing critical elements
        const missingElements = Object.entries(analysisResults.criticalElements)
            .filter(([_, data]) => !data.found)
            .map(([elementType, _]) => elementType);
        
        if (missingElements.length > 0) {
            recommendations.push({
                type: 'missing_elements',
                severity: 'high',
                message: `Critical elements not found: ${missingElements.join(', ')}`,
                action: 'Verify page is fully loaded and UI has not changed'
            });
        }
        
        // Check for invisible elements
        const invisibleElements = Object.entries(analysisResults.criticalElements)
            .filter(([_, data]) => data.found && !data.isVisible)
            .map(([elementType, _]) => elementType);
        
        if (invisibleElements.length > 0) {
            recommendations.push({
                type: 'invisible_elements',
                severity: 'medium',
                message: `Elements found but not visible: ${invisibleElements.join(', ')}`,
                action: 'Check if elements are hidden by CSS or user interaction required'
            });
        }
        
        // Check performance issues
        const healthReport = analysisResults.uiElementsHealth.performanceReport;
        if (healthReport.successRate < 0.9) {
            recommendations.push({
                type: 'performance_issue',
                severity: 'high',
                message: `Low success rate: ${(healthReport.successRate * 100).toFixed(1)}%`,
                action: 'Review selector strategies and page loading times'
            });
        }
        
        if (healthReport.averageDuration > 2000) {
            recommendations.push({
                type: 'slow_operations',
                severity: 'medium',
                message: `Slow average operation time: ${healthReport.averageDuration.toFixed(0)}ms`,
                action: 'Optimize selectors and reduce timeout values'
            });
        }
        
        // Check market data availability
        if (!analysisResults.marketDataAnalysis.tableFound) {
            recommendations.push({
                type: 'market_data_missing',
                severity: 'high',
                message: 'Market data table not accessible',
                action: 'Verify trading interface is loaded and user is logged in'
            });
        }
        
        return recommendations;
    }
    
    // Create enhanced debug interface
    function createEnhancedDebugInterface() {
        // Remove existing debug interface if present
        const existingInterface = document.getElementById('enhanced-dom-debug');
        if (existingInterface) {
            existingInterface.remove();
        }
        
        // Create debug panel
        const debugPanel = document.createElement('div');
        debugPanel.id = 'enhanced-dom-debug';
        debugPanel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            max-height: 80vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: 2px solid #4a5568;
            border-radius: 10px;
            padding: 15px;
            z-index: 10000;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            overflow-y: auto;
        `;
        
        // Create header
        const header = document.createElement('div');
        header.style.cssText = `
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 10px;
            text-align: center;
            color: #f7fafc;
        `;
        header.textContent = 'Enhanced DOM Intelligence Debug';
        
        // Create buttons container
        const buttonsContainer = document.createElement('div');
        buttonsContainer.style.cssText = `
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        `;
        
        // Analyze button
        const analyzeButton = document.createElement('button');
        analyzeButton.textContent = 'Analyze DOM';
        analyzeButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #48bb78;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
        `;
        
        // Clear button
        const clearButton = document.createElement('button');
        clearButton.textContent = 'Clear';
        clearButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #f56565;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
        `;
        
        // Export button
        const exportButton = document.createElement('button');
        exportButton.textContent = 'Export';
        exportButton.style.cssText = `
            flex: 1;
            padding: 8px;
            background: #4299e1;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
        `;
        
        // Results container
        const resultsContainer = document.createElement('div');
        resultsContainer.id = 'debug-results';
        resultsContainer.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            padding: 10px;
            max-height: 50vh;
            overflow-y: auto;
            font-size: 10px;
            line-height: 1.4;
        `;
        
        // Event handlers
        analyzeButton.addEventListener('click', async () => {
            analyzeButton.disabled = true;
            analyzeButton.textContent = 'Analyzing...';
            
            try {
                const results = await analyzeTradevatedomWithIntelligence();
                displayResults(results, resultsContainer);
            } catch (error) {
                resultsContainer.innerHTML = `<span style="color: #f56565;">Error: ${error.message}</span>`;
            } finally {
                analyzeButton.disabled = false;
                analyzeButton.textContent = 'Analyze DOM';
            }
        });
        
        clearButton.addEventListener('click', () => {
            resultsContainer.innerHTML = '<span style="color: #a0aec0;">Click "Analyze DOM" to start...</span>';
        });
        
        exportButton.addEventListener('click', async () => {
            try {
                const results = await analyzeTradevatedomWithIntelligence();
                const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(results, null, 2));
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = `dom_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                link.click();
            } catch (error) {
                alert('Export failed: ' + error.message);
            }
        });
        
        // Assemble interface
        buttonsContainer.appendChild(analyzeButton);
        buttonsContainer.appendChild(clearButton);
        buttonsContainer.appendChild(exportButton);
        
        debugPanel.appendChild(header);
        debugPanel.appendChild(buttonsContainer);
        debugPanel.appendChild(resultsContainer);
        
        // Initial message
        resultsContainer.innerHTML = '<span style="color: #a0aec0;">Enhanced DOM Intelligence Debug Panel Ready. Click "Analyze DOM" to start...</span>';
        
        document.body.appendChild(debugPanel);
        
        // Make draggable
        makeDraggable(debugPanel, header);
    }
    
    // Display analysis results in a formatted way
    function displayResults(results, container) {
        let html = '';
        
        // Health Status
        const healthColor = {
            'healthy': '#48bb78',
            'warning': '#ed8936',
            'degraded': '#f56565',
            'critical': '#e53e3e'
        }[domClient.healthStatus] || '#a0aec0';
        
        html += `<div style="margin-bottom: 10px;">
            <span style="color: ${healthColor}; font-weight: bold;">● Health: ${domClient.healthStatus.toUpperCase()}</span>
        </div>`;
        
        // Performance Comparison
        if (results.performanceComparison) {
            html += `<div style="margin-bottom: 10px; padding: 5px; background: rgba(255,255,255,0.1); border-radius: 3px;">
                <div style="font-weight: bold; color: #e2e8f0;">Performance Comparison:</div>
                <div>Traditional: ${results.performanceComparison.traditionalDuration.toFixed(1)}ms</div>
                <div>Intelligence: ${results.performanceComparison.intelligentDuration.toFixed(1)}ms</div>
                <div style="color: #48bb78;">Improvement: ${results.performanceComparison.speedImprovement}</div>
            </div>`;
        }
        
        // Critical Elements Status
        if (results.intelligentAnalysis && results.intelligentAnalysis.criticalElements) {
            html += `<div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #e2e8f0; margin-bottom: 5px;">Critical Elements:</div>`;
            
            Object.entries(results.intelligentAnalysis.criticalElements).forEach(([elementType, data]) => {
                const statusColor = data.found ? (data.isVisible ? '#48bb78' : '#ed8936') : '#f56565';
                const statusText = data.found ? (data.isVisible ? 'OK' : 'HIDDEN') : 'MISSING';
                html += `<div style="margin-left: 10px;">
                    <span style="color: ${statusColor};">●</span> ${elementType}: ${statusText}
                </div>`;
            });
            html += `</div>`;
        }
        
        // Recommendations
        if (results.intelligentAnalysis && results.intelligentAnalysis.recommendations && results.intelligentAnalysis.recommendations.length > 0) {
            html += `<div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #e2e8f0; margin-bottom: 5px;">Recommendations:</div>`;
            
            results.intelligentAnalysis.recommendations.forEach((rec, index) => {
                const severityColor = {
                    'high': '#f56565',
                    'medium': '#ed8936',
                    'low': '#48bb78'
                }[rec.severity] || '#a0aec0';
                
                html += `<div style="margin-left: 10px; margin-bottom: 5px; padding: 3px; background: rgba(0,0,0,0.2); border-radius: 3px;">
                    <div style="color: ${severityColor}; font-weight: bold;">${rec.type.toUpperCase()}</div>
                    <div style="font-size: 9px;">${rec.message}</div>
                    <div style="font-size: 9px; color: #a0aec0; font-style: italic;">${rec.action}</div>
                </div>`;
            });
            html += `</div>`;
        }
        
        // Performance Summary
        if (results.domIntelligenceStatus) {
            const report = results.domIntelligenceStatus;
            html += `<div style="margin-bottom: 10px; padding: 5px; background: rgba(255,255,255,0.1); border-radius: 3px;">
                <div style="font-weight: bold; color: #e2e8f0;">Performance Summary:</div>
                <div>Operations: ${report.totalOperations}</div>
                <div>Success Rate: ${(report.successRate * 100).toFixed(1)}%</div>
                <div>Avg Duration: ${report.averageDuration?.toFixed(0)}ms</div>
            </div>`;
        }
        
        container.innerHTML = html;
    }
    
    // Make element draggable
    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        handle.style.cursor = 'move';
        handle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
    
    // Initialize when page is ready
    function initialize() {
        // Wait for page to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(createEnhancedDebugInterface, 1000);
            });
        } else {
            setTimeout(createEnhancedDebugInterface, 1000);
        }
    }
    
    // Start initialization
    initialize();
    
    // Make analyze function available globally for console access
    window.analyzeTradevatedomWithIntelligence = analyzeTradevatedomWithIntelligence;
    
    console.log('[Enhanced DOM Debug] Loaded with DOM Intelligence integration');
    
})();