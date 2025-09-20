// ============================================================================
// ORDER RECONCILIATION AND REPORTING SYSTEM
// ============================================================================
// 
// Comprehensive order reconciliation and reporting system for the Tradovate
// platform. Provides detailed analysis of order validation performance,
// success rates, error patterns, and discrepancies.
//
// Features:
// - Order vs Intent reconciliation
// - Performance analytics
// - Error pattern analysis
// - Success rate tracking
// - Bracket order coordination analysis
// - Real-time reporting dashboard
// - Export capabilities
//
// Last Updated: 2025-01-26
// ============================================================================

class OrderReconciliationReporting {
    constructor(validationFramework) {
        this.framework = validationFramework;
        this.reportingInterval = null;
        this.reportHistory = [];
        this.maxHistoryEntries = 100;
        
        // Performance tracking
        this.metrics = {
            totalValidations: 0,
            successfulSubmissions: 0,
            failedSubmissions: 0,
            averageValidationTime: 0,
            totalErrors: 0,
            criticalErrors: 0
        };
        
        // Reconciliation tracking
        this.reconciliationData = {
            expectedVsActual: [],
            bracketCoordination: [],
            cancellationEffectiveness: [],
            errorRecovery: []
        };
        
        this.initializeReporting();
        this.log('info', 'OrderReconciliationReporting initialized');
    }
    
    // ============================================================================
    // INITIALIZATION
    // ============================================================================
    
    initializeReporting() {
        // Set up periodic reporting
        this.startPeriodicReporting();
        
        // Listen to validation framework events
        if (this.framework) {
            this.setupEventListeners();
        }
        
        // Create reporting UI elements
        this.createReportingUI();
    }
    
    setupEventListeners() {
        this.framework.addEventListener('SUBMISSION_COMPLETED', (event) => {
            this.recordSubmissionEvent(event);
        });
        
        this.framework.addEventListener('VALIDATION_FAILED', (event) => {
            this.recordValidationFailure(event);
        });
        
        this.framework.addEventListener('ERROR_DETECTED', (event) => {
            this.recordError(event);
        });
        
        this.framework.addEventListener('CANCELLATION_VALIDATED', (event) => {
            this.recordCancellation(event);
        });
        
        this.framework.addEventListener('BRACKET_GROUP_COMPLETE', (event) => {
            this.recordBracketCompletion(event);
        });
    }
    
    createReportingUI() {
        // Check if panel already exists and remove it to prevent duplicates
        const existingPanel = document.querySelector('#orderReportingPanel');
        if (existingPanel) {
            console.log('Reporting panel already exists, removing old one to prevent duplicates');
            existingPanel.remove();
        }
        
        // Create floating report panel
        const panel = document.createElement('div');
        panel.id = 'orderReportingPanel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            left: 250px;
            width: 300px;
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid #444;
            border-radius: 8px;
            padding: 12px;
            z-index: 99998;
            color: #fff;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            display: none;
            max-height: 400px;
            overflow-y: auto;
        `;
        
        panel.innerHTML = `
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: bold;">📊 Order Validation Report</span>
                <button id="closeReportPanel" style="background: none; border: none; color: #fff; cursor: pointer;">✕</button>
            </div>
            <div id="reportContent">Loading...</div>
        `;
        
        document.body.appendChild(panel);
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'toggleReportPanel';
        toggleBtn.textContent = '📊';
        toggleBtn.style.cssText = `
            position: fixed;
            top: 80px;
            left: 20px;
            background: #2196F3;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 8px;
            cursor: pointer;
            z-index: 99999;
            font-size: 16px;
        `;
        toggleBtn.title = 'Toggle Order Validation Report';
        
        document.body.appendChild(toggleBtn);
        
        // Set up event listeners
        toggleBtn.addEventListener('click', () => {
            const panel = document.getElementById('orderReportingPanel');
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                this.updateReportDisplay();
            } else {
                panel.style.display = 'none';
            }
        });
        
        document.getElementById('closeReportPanel').addEventListener('click', () => {
            document.getElementById('orderReportingPanel').style.display = 'none';
        });
    }
    
    // ============================================================================
    // REPORTING METHODS
    // ============================================================================
    
    generateComprehensiveReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: this.generateSummaryReport(),
            performance: this.generatePerformanceReport(),
            reconciliation: this.generateReconciliationReport(),
            errorAnalysis: this.generateErrorAnalysisReport(),
            recommendations: this.generateRecommendations()
        };
        
        this.reportHistory.push(report);
        
        // Maintain history limit
        if (this.reportHistory.length > this.maxHistoryEntries) {
            this.reportHistory = this.reportHistory.slice(-this.maxHistoryEntries);
        }
        
        return report;
    }
    
    generateSummaryReport() {
        const orders = this.framework ? this.framework.getAllOrders() : [];
        const activeOrders = this.framework ? this.framework.getActiveOrders() : [];
        
        return {
            totalOrders: orders.length,
            activeOrders: activeOrders.length,
            completedOrders: orders.length - activeOrders.length,
            successRate: this.calculateSuccessRate(),
            validationCompliance: this.calculateValidationCompliance(),
            lastUpdate: Date.now()
        };
    }
    
    generatePerformanceReport() {
        const performanceData = this.framework ? this.framework.getPerformanceReport() : {};
        
        return {
            ...performanceData,
            validationOverhead: this.calculateValidationOverhead(),
            memoryUsage: this.estimateMemoryUsage(),
            cpuImpact: this.estimateCPUImpact(),
            complianceWithThreshold: this.checkPerformanceCompliance()
        };
    }
    
    generateReconciliationReport() {
        return {
            expectedVsActual: this.analyzeExpectedVsActual(),
            bracketCoordination: this.analyzeBracketCoordination(),
            cancellationEffectiveness: this.analyzeCancellationEffectiveness(),
            orderLifecycle: this.analyzeOrderLifecycle(),
            discrepancies: this.identifyDiscrepancies()
        };
    }
    
    generateErrorAnalysisReport() {
        const errors = this.collectErrorData();
        
        return {
            totalErrors: errors.length,
            errorCategories: this.categorizeErrors(errors),
            errorTrends: this.analyzeErrorTrends(errors),
            recoverySuccess: this.analyzeRecoverySuccess(errors),
            criticalIncidents: this.identifyCriticalIncidents(errors),
            errorImpact: this.assessErrorImpact(errors)
        };
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        // Performance recommendations
        const perfReport = this.generatePerformanceReport();
        if (!perfReport.complianceWithThreshold) {
            recommendations.push({
                type: 'PERFORMANCE',
                priority: 'HIGH',
                title: 'Validation Overhead Exceeds Threshold',
                description: `Average validation time (${perfReport.averageDuration?.toFixed(2)}ms) exceeds 10ms threshold`,
                action: 'Optimize validation logic or disable non-critical validations'
            });
        }
        
        // Error pattern recommendations
        const errorReport = this.generateErrorAnalysisReport();
        const topErrorCategory = this.getTopErrorCategory(errorReport.errorCategories);
        if (topErrorCategory && topErrorCategory.count > 5) {
            recommendations.push({
                type: 'ERROR_REDUCTION',
                priority: 'MEDIUM',
                title: `High Frequency ${topErrorCategory.category} Errors`,
                description: `${topErrorCategory.count} errors in category ${topErrorCategory.category}`,
                action: 'Review and improve error handling for this category'
            });
        }
        
        // Reconciliation recommendations
        const reconReport = this.generateReconciliationReport();
        if (reconReport.discrepancies.length > 0) {
            recommendations.push({
                type: 'RECONCILIATION',
                priority: 'HIGH',
                title: 'Order Discrepancies Detected',
                description: `${reconReport.discrepancies.length} discrepancies found between intended and actual orders`,
                action: 'Investigate order submission process and validation logic'
            });
        }
        
        return recommendations;
    }
    
    // ============================================================================
    // ANALYSIS METHODS
    // ============================================================================
    
    analyzeExpectedVsActual() {
        const analysis = {
            matches: 0,
            discrepancies: 0,
            details: []
        };
        
        if (!this.framework) return analysis;
        
        const orders = this.framework.getAllOrders();
        
        for (const order of orders) {
            const expected = order.originalData;
            const actual = this.extractActualOrderData(order);
            
            const comparison = this.compareOrderData(expected, actual);
            if (comparison.isMatch) {
                analysis.matches++;
            } else {
                analysis.discrepancies++;
                analysis.details.push({
                    orderId: order.id,
                    expected: expected,
                    actual: actual,
                    differences: comparison.differences
                });
            }
        }
        
        return analysis;
    }
    
    analyzeBracketCoordination() {
        const analysis = {
            totalBrackets: 0,
            successfulBrackets: 0,
            failedBrackets: 0,
            orphanedOrders: 0,
            coordinationIssues: []
        };
        
        if (!this.framework) return analysis;
        
        const bracketGroups = new Map();
        const orders = this.framework.getAllOrders();
        
        // Group orders by bracket group ID
        for (const order of orders) {
            if (order.bracketGroupId) {
                if (!bracketGroups.has(order.bracketGroupId)) {
                    bracketGroups.set(order.bracketGroupId, []);
                }
                bracketGroups.get(order.bracketGroupId).push(order);
            } else if (order.isChildOrder) {
                analysis.orphanedOrders++;
            }
        }
        
        analysis.totalBrackets = bracketGroups.size;
        
        // Analyze each bracket group
        for (const [groupId, groupOrders] of bracketGroups) {
            const parentOrders = groupOrders.filter(o => !o.isChildOrder);
            const childOrders = groupOrders.filter(o => o.isChildOrder);
            
            if (parentOrders.length === 1 && childOrders.length >= 1) {
                analysis.successfulBrackets++;
            } else {
                analysis.failedBrackets++;
                analysis.coordinationIssues.push({
                    groupId: groupId,
                    parentCount: parentOrders.length,
                    childCount: childOrders.length,
                    issue: parentOrders.length !== 1 ? 'Multiple/No parent orders' : 'No child orders'
                });
            }
        }
        
        return analysis;
    }
    
    analyzeCancellationEffectiveness() {
        const analysis = {
            totalCancellations: 0,
            successfulCancellations: 0,
            failedCancellations: 0,
            averageTime: 0,
            details: []
        };
        
        if (!this.framework) return analysis;
        
        const orders = this.framework.getAllOrders();
        const cancellationEvents = [];
        
        for (const order of orders) {
            const cancellationAttempts = order.events?.filter(e => 
                e.type === 'CANCELLATION_ATTEMPT' || e.type === 'CANCELLATION_VALIDATED'
            ) || [];
            
            if (cancellationAttempts.length > 0) {
                analysis.totalCancellations++;
                
                const validationEvent = cancellationAttempts.find(e => e.type === 'CANCELLATION_VALIDATED');
                if (validationEvent && validationEvent.data?.success) {
                    analysis.successfulCancellations++;
                } else {
                    analysis.failedCancellations++;
                }
                
                cancellationEvents.push(...cancellationAttempts);
            }
        }
        
        if (cancellationEvents.length > 0) {
            const times = cancellationEvents.map(e => e.data?.duration || 0).filter(t => t > 0);
            analysis.averageTime = times.reduce((sum, time) => sum + time, 0) / times.length;
        }
        
        return analysis;
    }
    
    analyzeOrderLifecycle() {
        const analysis = {
            averageSubmissionTime: 0,
            averageConfirmationTime: 0,
            averageCompletionTime: 0,
            lifecycleStages: {},
            stuckOrders: []
        };
        
        if (!this.framework) return analysis;
        
        const orders = this.framework.getAllOrders();
        const submissionTimes = [];
        const confirmationTimes = [];
        const completionTimes = [];
        
        for (const order of orders) {
            const submissionTime = order.submissionDuration;
            if (submissionTime) submissionTimes.push(submissionTime);
            
            const confirmationTime = order.lastValidation - order.submissionStartTime;
            if (confirmationTime > 0) confirmationTimes.push(confirmationTime);
            
            const completionTime = order.completionTime - order.timestamp;
            if (completionTime > 0) completionTimes.push(completionTime);
            
            // Track lifecycle stages
            const stage = this.determineOrderStage(order);
            analysis.lifecycleStages[stage] = (analysis.lifecycleStages[stage] || 0) + 1;
            
            // Identify stuck orders
            if (this.isOrderStuck(order)) {
                analysis.stuckOrders.push({
                    orderId: order.id,
                    stage: stage,
                    stuckTime: Date.now() - order.timestamp,
                    lastEvent: order.events?.slice(-1)[0]
                });
            }
        }
        
        analysis.averageSubmissionTime = this.calculateAverage(submissionTimes);
        analysis.averageConfirmationTime = this.calculateAverage(confirmationTimes);
        analysis.averageCompletionTime = this.calculateAverage(completionTimes);
        
        return analysis;
    }
    
    identifyDiscrepancies() {
        const discrepancies = [];
        
        if (!this.framework) return discrepancies;
        
        const orders = this.framework.getAllOrders();
        
        for (const order of orders) {
            // Check for timing discrepancies
            if (order.submissionDuration > 10000) { // 10 seconds
                discrepancies.push({
                    type: 'SLOW_SUBMISSION',
                    orderId: order.id,
                    description: `Submission took ${order.submissionDuration}ms`,
                    severity: 'MEDIUM'
                });
            }
            
            // Check for validation discrepancies
            if (order.validationHistory?.length > 3) {
                discrepancies.push({
                    type: 'EXCESSIVE_VALIDATION',
                    orderId: order.id,
                    description: `${order.validationHistory.length} validation attempts`,
                    severity: 'LOW'
                });
            }
            
            // Check for bracket coordination discrepancies
            if (order.bracketGroupId && !order.isChildOrder) {
                const childOrders = orders.filter(o => o.parentOrderId === order.id);
                if (childOrders.length === 0) {
                    discrepancies.push({
                        type: 'MISSING_BRACKET_ORDERS',
                        orderId: order.id,
                        description: 'Parent order has no child orders',
                        severity: 'HIGH'
                    });
                }
            }
        }
        
        return discrepancies;
    }
    
    // ============================================================================
    // UTILITY METHODS
    // ============================================================================
    
    calculateSuccessRate() {
        if (!this.framework) return 0;
        
        const orders = this.framework.getAllOrders();
        if (orders.length === 0) return 0;
        
        const successfulOrders = orders.filter(order => 
            order.status === 'FILLED' || order.status === 'SUBMITTED'
        ).length;
        
        return (successfulOrders / orders.length) * 100;
    }
    
    calculateValidationCompliance() {
        if (!this.framework) return 0;
        
        const performanceReport = this.framework.getPerformanceReport();
        return parseFloat(performanceReport.complianceRate) || 0;
    }
    
    calculateValidationOverhead() {
        if (!this.framework) return 0;
        
        const performanceReport = this.framework.getPerformanceReport();
        return performanceReport.averageDuration || 0;
    }
    
    estimateMemoryUsage() {
        if (!this.framework) return 0;
        
        const orders = this.framework.getAllOrders();
        const avgOrderSize = 1024; // Estimated bytes per order
        return orders.length * avgOrderSize;
    }
    
    estimateCPUImpact() {
        const performanceReport = this.framework ? this.framework.getPerformanceReport() : {};
        const validationsPerSecond = performanceReport.validationCalls || 0;
        const avgDuration = performanceReport.averageDuration || 0;
        
        return (validationsPerSecond * avgDuration) / 1000; // Percentage of CPU time
    }
    
    checkPerformanceCompliance() {
        const overhead = this.calculateValidationOverhead();
        return overhead <= 10; // 10ms threshold from CLAUDE.md
    }
    
    compareOrderData(expected, actual) {
        const differences = [];
        const fields = ['symbol', 'action', 'qty', 'orderType', 'price'];
        
        for (const field of fields) {
            if (expected[field] !== actual[field]) {
                differences.push({
                    field: field,
                    expected: expected[field],
                    actual: actual[field]
                });
            }
        }
        
        return {
            isMatch: differences.length === 0,
            differences: differences
        };
    }
    
    extractActualOrderData(order) {
        // This would typically extract data from the UI tables
        // For now, return the order data as stored
        return {
            symbol: order.symbol,
            action: order.side,
            qty: order.quantity,
            orderType: order.orderType,
            price: order.price
        };
    }
    
    collectErrorData() {
        if (!this.framework) return [];
        
        const orders = this.framework.getAllOrders();
        const errors = [];
        
        for (const order of orders) {
            const errorEvents = order.events?.filter(e => 
                e.type.includes('ERROR') || e.type.includes('FAILED')
            ) || [];
            
            errors.push(...errorEvents.map(e => ({
                orderId: order.id,
                timestamp: e.timestamp,
                type: e.type,
                data: e.data
            })));
        }
        
        return errors;
    }
    
    categorizeErrors(errors) {
        const categories = {};
        
        for (const error of errors) {
            const category = error.data?.classification?.category || 'UNKNOWN';
            categories[category] = (categories[category] || 0) + 1;
        }
        
        return Object.entries(categories).map(([category, count]) => ({
            category,
            count
        })).sort((a, b) => b.count - a.count);
    }
    
    getTopErrorCategory(categories) {
        return categories.length > 0 ? categories[0] : null;
    }
    
    determineOrderStage(order) {
        if (order.completionTime) return 'COMPLETED';
        if (order.submissionResult?.success) return 'SUBMITTED';
        if (order.submissionStartTime) return 'SUBMITTING';
        return 'PENDING';
    }
    
    isOrderStuck(order) {
        const now = Date.now();
        const stuckThreshold = 300000; // 5 minutes
        
        return (now - order.timestamp) > stuckThreshold && 
               !order.completionTime && 
               !this.isTerminalStatus(order.status);
    }
    
    isTerminalStatus(status) {
        return ['FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED'].includes(status);
    }
    
    calculateAverage(numbers) {
        if (numbers.length === 0) return 0;
        return numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
    }
    
    // ============================================================================
    // EVENT HANDLERS
    // ============================================================================
    
    recordSubmissionEvent(event) {
        this.metrics.totalValidations++;
        
        if (event.success) {
            this.metrics.successfulSubmissions++;
        } else {
            this.metrics.failedSubmissions++;
        }
        
        this.updateMetrics();
    }
    
    recordValidationFailure(event) {
        this.metrics.failedSubmissions++;
        this.updateMetrics();
    }
    
    recordError(event) {
        this.metrics.totalErrors++;
        
        if (event.classification?.severity === 'CRITICAL') {
            this.metrics.criticalErrors++;
        }
        
        this.updateMetrics();
    }
    
    recordCancellation(event) {
        this.reconciliationData.cancellationEffectiveness.push({
            timestamp: Date.now(),
            success: event.success,
            symbol: event.symbol,
            details: event.validationResult
        });
    }
    
    recordBracketCompletion(event) {
        this.reconciliationData.bracketCoordination.push({
            timestamp: Date.now(),
            groupId: event.bracketGroupId,
            enableTP: event.enableTP,
            enableSL: event.enableSL
        });
    }
    
    updateMetrics() {
        if (this.metrics.totalValidations > 0) {
            this.metrics.averageValidationTime = 
                (this.metrics.successfulSubmissions + this.metrics.failedSubmissions) / 
                this.metrics.totalValidations;
        }
    }
    
    // ============================================================================
    // REPORTING DISPLAY
    // ============================================================================
    
    updateReportDisplay() {
        const contentDiv = document.getElementById('reportContent');
        if (!contentDiv) return;
        
        const report = this.generateComprehensiveReport();
        
        contentDiv.innerHTML = `
            <div style="margin-bottom: 8px;">
                <strong>Summary:</strong><br>
                Orders: ${report.summary.totalOrders} (${report.summary.activeOrders} active)<br>
                Success Rate: ${report.summary.successRate.toFixed(1)}%<br>
                Compliance: ${report.summary.validationCompliance.toFixed(1)}%
            </div>
            
            <div style="margin-bottom: 8px;">
                <strong>Performance:</strong><br>
                Avg Validation: ${report.performance.averageDuration?.toFixed(2) || 0}ms<br>
                Threshold Compliance: ${report.performance.complianceWithThreshold ? '✅' : '❌'}<br>
                CPU Impact: ${report.performance.cpuImpact?.toFixed(2) || 0}%
            </div>
            
            <div style="margin-bottom: 8px;">
                <strong>Errors:</strong><br>
                Total: ${report.errorAnalysis.totalErrors}<br>
                Critical: ${report.errorAnalysis.criticalIncidents?.length || 0}<br>
                Top Category: ${this.getTopErrorCategory(report.errorAnalysis.errorCategories)?.category || 'None'}
            </div>
            
            <div style="margin-bottom: 8px;">
                <strong>Reconciliation:</strong><br>
                Discrepancies: ${report.reconciliation.discrepancies.length}<br>
                Bracket Success: ${report.reconciliation.bracketCoordination.successfulBrackets}/${report.reconciliation.bracketCoordination.totalBrackets}<br>
                Cancel Success: ${report.reconciliation.cancellationEffectiveness.successfulCancellations}/${report.reconciliation.cancellationEffectiveness.totalCancellations}
            </div>
            
            ${report.recommendations.length > 0 ? `
                <div style="border-top: 1px solid #666; padding-top: 8px;">
                    <strong>Recommendations:</strong><br>
                    ${report.recommendations.slice(0, 2).map(r => 
                        `<div style="margin: 4px 0; padding: 4px; background: rgba(255,193,7,0.2); border-radius: 3px;">
                            <strong>${r.priority}:</strong> ${r.title}
                        </div>`
                    ).join('')}
                </div>
            ` : ''}
        `;
    }
    
    startPeriodicReporting() {
        // Update report display every 30 seconds
        this.reportingInterval = setInterval(() => {
            if (document.getElementById('orderReportingPanel')?.style.display === 'block') {
                this.updateReportDisplay();
            }
        }, 30000);
    }
    
    stopPeriodicReporting() {
        if (this.reportingInterval) {
            clearInterval(this.reportingInterval);
            this.reportingInterval = null;
        }
    }
    
    // ============================================================================
    // EXPORT METHODS
    // ============================================================================
    
    exportReport(format = 'json') {
        const report = this.generateComprehensiveReport();
        
        if (format === 'json') {
            return JSON.stringify(report, null, 2);
        } else if (format === 'csv') {
            return this.convertToCSV(report);
        } else {
            return report;
        }
    }
    
    convertToCSV(report) {
        // Simple CSV conversion for summary data
        const lines = [
            'Metric,Value',
            `Total Orders,${report.summary.totalOrders}`,
            `Active Orders,${report.summary.activeOrders}`,
            `Success Rate,${report.summary.successRate.toFixed(2)}%`,
            `Validation Compliance,${report.summary.validationCompliance.toFixed(2)}%`,
            `Average Validation Time,${report.performance.averageDuration?.toFixed(2) || 0}ms`,
            `Total Errors,${report.errorAnalysis.totalErrors}`,
            `Critical Errors,${report.errorAnalysis.criticalIncidents?.length || 0}`,
            `Discrepancies,${report.reconciliation.discrepancies.length}`
        ];
        
        return lines.join('\n');
    }
    
    downloadReport(format = 'json') {
        const report = this.exportReport(format);
        const blob = new Blob([report], { type: format === 'json' ? 'application/json' : 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `order-validation-report-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // ============================================================================
    // UTILITY METHODS
    // ============================================================================
    
    log(level, message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}][OrderReporting][${level.toUpperCase()}] ${message}`;
        
        if (level === 'error') {
            console.error(logEntry, data);
        } else if (level === 'warn') {
            console.warn(logEntry, data);
        } else {
            console.log(logEntry, data);
        }
    }
}

// ============================================================================
// GLOBAL INTEGRATION
// ============================================================================

// Auto-initialize with validation framework if available
if (typeof window !== 'undefined') {
    window.OrderReconciliationReporting = OrderReconciliationReporting;
    
    // Initialize with global validation framework when available
    if (window.autoOrderValidator) {
        window.orderReporting = new OrderReconciliationReporting(window.autoOrderValidator);
        console.log('✅ Order Reconciliation and Reporting initialized');
    } else {
        // Wait for validation framework to be available
        let checkCount = 0;
        const checkInterval = setInterval(() => {
            if (window.autoOrderValidator || checkCount > 10) {
                clearInterval(checkInterval);
                if (window.autoOrderValidator) {
                    window.orderReporting = new OrderReconciliationReporting(window.autoOrderValidator);
                    console.log('✅ Order Reconciliation and Reporting initialized (delayed)');
                }
            }
            checkCount++;
        }, 1000);
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrderReconciliationReporting;
}

console.log('✅ OrderReconciliationReporting loaded');