// ==UserScript==
// @name         Order Validation Health Dashboard
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Real-time performance monitoring UI for Order Validation Framework
// @author       Trading System
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/OrderValidationDashboard.js
// @downloadURL  http://localhost:8080/OrderValidationDashboard.js
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('Order Validation Health Dashboard initializing...');
    
    // Dashboard state
    let dashboardState = {
        visible: true,
        minimized: false,
        position: { x: 20, y: 20 },
        updateInterval: null,
        alertsEnabled: true,
        performanceHistory: [],
        maxHistoryLength: 100
    };
    
    // Create dashboard container
    function createDashboard() {
        const dashboard = document.createElement('div');
        dashboard.id = 'order-validation-dashboard';
        dashboard.style.cssText = `
            position: fixed;
            top: ${dashboardState.position.y}px;
            left: ${dashboardState.position.x}px;
            width: 320px;
            background: rgba(20, 20, 30, 0.95);
            border: 1px solid #4CAF50;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            font-family: 'Roboto', Arial, sans-serif;
            font-size: 12px;
            color: #fff;
            z-index: 10000;
            transition: all 0.3s ease;
        `;
        
        // Dashboard header
        const header = document.createElement('div');
        header.style.cssText = `
            padding: 10px;
            background: rgba(30, 30, 40, 0.9);
            border-bottom: 1px solid #4CAF50;
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px 8px 0 0;
        `;
        
        header.innerHTML = `
            <span style="font-weight: bold; font-size: 14px;">📊 Validation Health Monitor</span>
            <div>
                <button id="dashboard-minimize" style="
                    background: transparent;
                    border: none;
                    color: #fff;
                    cursor: pointer;
                    font-size: 16px;
                    margin-right: 5px;
                ">_</button>
                <button id="dashboard-close" style="
                    background: transparent;
                    border: none;
                    color: #fff;
                    cursor: pointer;
                    font-size: 16px;
                ">×</button>
            </div>
        `;
        
        // Dashboard content
        const content = document.createElement('div');
        content.id = 'dashboard-content';
        content.style.cssText = `
            padding: 15px;
            max-height: 500px;
            overflow-y: auto;
        `;
        
        content.innerHTML = `
            <!-- Health Score Section -->
            <div class="health-score-section" style="margin-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">Health Score</h3>
                <div style="display: flex; align-items: center;">
                    <div id="health-score-circle" style="
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        background: conic-gradient(#4CAF50 0deg, #4CAF50 0deg, #333 0deg);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        position: relative;
                        margin-right: 20px;
                    ">
                        <div style="
                            width: 70px;
                            height: 70px;
                            border-radius: 50%;
                            background: rgba(20, 20, 30, 0.95);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 24px;
                            font-weight: bold;
                        ">
                            <span id="health-score-value">--</span>
                        </div>
                    </div>
                    <div id="health-status" style="flex: 1;">
                        <div id="health-status-text" style="font-size: 14px; font-weight: bold;">Initializing...</div>
                        <div id="health-details" style="font-size: 11px; color: #aaa; margin-top: 5px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Performance Metrics Section -->
            <div class="metrics-section" style="margin-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">Performance Metrics</h3>
                <div id="metrics-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div class="metric-card" style="background: rgba(40, 40, 50, 0.5); padding: 10px; border-radius: 4px;">
                        <div style="font-size: 10px; color: #aaa;">Avg Time</div>
                        <div id="metric-avg-time" style="font-size: 18px; font-weight: bold;">--ms</div>
                    </div>
                    <div class="metric-card" style="background: rgba(40, 40, 50, 0.5); padding: 10px; border-radius: 4px;">
                        <div style="font-size: 10px; color: #aaa;">Max Time</div>
                        <div id="metric-max-time" style="font-size: 18px; font-weight: bold;">--ms</div>
                    </div>
                    <div class="metric-card" style="background: rgba(40, 40, 50, 0.5); padding: 10px; border-radius: 4px;">
                        <div style="font-size: 10px; color: #aaa;">Violations</div>
                        <div id="metric-violations" style="font-size: 18px; font-weight: bold;">0</div>
                    </div>
                    <div class="metric-card" style="background: rgba(40, 40, 50, 0.5); padding: 10px; border-radius: 4px;">
                        <div style="font-size: 10px; color: #aaa;">Compliance</div>
                        <div id="metric-compliance" style="font-size: 18px; font-weight: bold;">--%</div>
                    </div>
                </div>
            </div>
            
            <!-- Performance Graph -->
            <div class="graph-section" style="margin-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">Performance Timeline</h3>
                <canvas id="performance-graph" width="290" height="100" style="
                    background: rgba(40, 40, 50, 0.5);
                    border-radius: 4px;
                    width: 100%;
                "></canvas>
            </div>
            
            <!-- Status Section -->
            <div class="status-section" style="margin-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">System Status</h3>
                <div id="status-info" style="background: rgba(40, 40, 50, 0.5); padding: 10px; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Performance Mode:</span>
                        <span id="status-mode" style="font-weight: bold;">--</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Adaptive Level:</span>
                        <span id="status-level" style="font-weight: bold;">--</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Total Validations:</span>
                        <span id="status-total" style="font-weight: bold;">0</span>
                    </div>
                </div>
            </div>
            
            <!-- Alerts Section -->
            <div class="alerts-section">
                <h3 style="margin: 0 0 10px 0; font-size: 16px; display: flex; justify-content: space-between; align-items: center;">
                    <span>Recent Alerts</span>
                    <label style="font-size: 11px; font-weight: normal;">
                        <input type="checkbox" id="alerts-toggle" checked style="margin-right: 5px;">
                        Enable
                    </label>
                </h3>
                <div id="alerts-container" style="
                    background: rgba(40, 40, 50, 0.5);
                    padding: 10px;
                    border-radius: 4px;
                    max-height: 100px;
                    overflow-y: auto;
                    font-size: 11px;
                ">
                    <div style="color: #aaa;">No alerts</div>
                </div>
            </div>
        `;
        
        dashboard.appendChild(header);
        dashboard.appendChild(content);
        document.body.appendChild(dashboard);
        
        // Make dashboard draggable
        makeDraggable(dashboard, header);
        
        // Setup event handlers
        setupEventHandlers();
        
        // Initialize graph
        initializeGraph();
        
        return dashboard;
    }
    
    // Make element draggable
    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
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
            
            const newTop = element.offsetTop - pos2;
            const newLeft = element.offsetLeft - pos1;
            
            // Keep within viewport
            const maxX = window.innerWidth - element.offsetWidth;
            const maxY = window.innerHeight - element.offsetHeight;
            
            element.style.top = Math.max(0, Math.min(newTop, maxY)) + "px";
            element.style.left = Math.max(0, Math.min(newLeft, maxX)) + "px";
            
            // Update position state
            dashboardState.position.x = element.offsetLeft;
            dashboardState.position.y = element.offsetTop;
        }
        
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
    
    // Setup event handlers
    function setupEventHandlers() {
        // Minimize button
        document.getElementById('dashboard-minimize').onclick = () => {
            const content = document.getElementById('dashboard-content');
            dashboardState.minimized = !dashboardState.minimized;
            content.style.display = dashboardState.minimized ? 'none' : 'block';
            document.getElementById('dashboard-minimize').textContent = dashboardState.minimized ? '□' : '_';
        };
        
        // Close button
        document.getElementById('dashboard-close').onclick = () => {
            const dashboard = document.getElementById('order-validation-dashboard');
            dashboard.style.display = 'none';
            dashboardState.visible = false;
            clearInterval(dashboardState.updateInterval);
        };
        
        // Alerts toggle
        document.getElementById('alerts-toggle').onchange = (e) => {
            dashboardState.alertsEnabled = e.target.checked;
        };
    }
    
    // Initialize performance graph
    function initializeGraph() {
        const canvas = document.getElementById('performance-graph');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = 290;
        canvas.height = 100;
        
        // Initial draw
        drawGraph(ctx, []);
    }
    
    // Draw performance graph
    function drawGraph(ctx, data) {
        const width = ctx.canvas.width;
        const height = ctx.canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw grid lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        
        // Horizontal lines
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Draw threshold line (10ms)
        ctx.strokeStyle = 'rgba(255, 152, 0, 0.5)';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        const thresholdY = height - (10 / 20) * height; // 10ms on 20ms scale
        ctx.beginPath();
        ctx.moveTo(0, thresholdY);
        ctx.lineTo(width, thresholdY);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Draw data
        if (data.length > 1) {
            ctx.strokeStyle = '#4CAF50';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            data.forEach((point, index) => {
                const x = (index / (data.length - 1)) * width;
                const y = height - (Math.min(point, 20) / 20) * height;
                
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Fill area under curve
            ctx.lineTo(width, height);
            ctx.lineTo(0, height);
            ctx.closePath();
            ctx.fillStyle = 'rgba(76, 175, 80, 0.2)';
            ctx.fill();
        }
        
        // Draw labels
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '10px Arial';
        ctx.fillText('20ms', 5, 10);
        ctx.fillText('10ms', 5, height / 2);
        ctx.fillText('0ms', 5, height - 5);
    }
    
    // Update dashboard with latest metrics
    function updateDashboard() {
        if (!window.autoOrderValidator || !dashboardState.visible) {
            return;
        }
        
        try {
            const report = window.autoOrderValidator.getPerformanceReport();
            
            // Update health score
            const healthScore = report.performanceHealthScore || 0;
            updateHealthScore(healthScore);
            
            // Update metrics
            document.getElementById('metric-avg-time').textContent = 
                (report.averageValidationTime || 0).toFixed(2) + 'ms';
            document.getElementById('metric-max-time').textContent = 
                (report.maxValidationTime || 0).toFixed(2) + 'ms';
            document.getElementById('metric-violations').textContent = 
                report.overheadWarnings || 0;
            document.getElementById('metric-compliance').textContent = 
                report.complianceRate || '0%';
            
            // Update status
            document.getElementById('status-mode').textContent = 
                report.performanceMode || 'UNKNOWN';
            document.getElementById('status-level').textContent = 
                report.adaptiveLevel || 'UNKNOWN';
            document.getElementById('status-total').textContent = 
                report.validationCalls || 0;
            
            // Update performance history
            const avgTime = report.averageValidationTime || 0;
            dashboardState.performanceHistory.push(avgTime);
            if (dashboardState.performanceHistory.length > dashboardState.maxHistoryLength) {
                dashboardState.performanceHistory.shift();
            }
            
            // Update graph
            const canvas = document.getElementById('performance-graph');
            const ctx = canvas.getContext('2d');
            drawGraph(ctx, dashboardState.performanceHistory);
            
            // Check for alerts
            checkAlerts(report);
            
        } catch (error) {
            console.error('Dashboard update error:', error);
        }
    }
    
    // Update health score visualization
    function updateHealthScore(score) {
        const scoreElement = document.getElementById('health-score-value');
        const circleElement = document.getElementById('health-score-circle');
        const statusText = document.getElementById('health-status-text');
        const statusDetails = document.getElementById('health-details');
        
        scoreElement.textContent = Math.round(score);
        
        // Update circle color based on score
        const degrees = (score / 100) * 360;
        let color;
        let status;
        let details;
        
        if (score >= 80) {
            color = '#4CAF50'; // Green
            status = 'Excellent';
            details = 'System performing optimally';
        } else if (score >= 60) {
            color = '#FFC107'; // Yellow
            status = 'Good';
            details = 'Minor performance issues detected';
        } else if (score >= 40) {
            color = '#FF9800'; // Orange
            status = 'Degraded';
            details = 'Performance optimization active';
        } else {
            color = '#F44336'; // Red
            status = 'Critical';
            details = 'Immediate attention required';
        }
        
        circleElement.style.background = 
            `conic-gradient(${color} 0deg, ${color} ${degrees}deg, #333 ${degrees}deg)`;
        
        statusText.textContent = status;
        statusText.style.color = color;
        statusDetails.textContent = details;
    }
    
    // Check for alerts
    function checkAlerts(report) {
        if (!dashboardState.alertsEnabled) return;
        
        const alertsContainer = document.getElementById('alerts-container');
        const alerts = [];
        
        // Check for performance violations
        if (report.averageValidationTime > 10) {
            alerts.push({
                type: 'error',
                message: `Average time ${report.averageValidationTime.toFixed(2)}ms exceeds 10ms threshold`,
                timestamp: new Date().toLocaleTimeString()
            });
        }
        
        // Check for degraded mode
        if (report.performanceMode !== 'OPTIMAL') {
            alerts.push({
                type: 'warning',
                message: `Performance mode: ${report.performanceMode}`,
                timestamp: new Date().toLocaleTimeString()
            });
        }
        
        // Check for recent violations
        if (report.recentViolations > 0) {
            alerts.push({
                type: 'warning',
                message: `${report.recentViolations} recent violations detected`,
                timestamp: new Date().toLocaleTimeString()
            });
        }
        
        // Update alerts display
        if (alerts.length > 0) {
            const alertsHtml = alerts.map(alert => `
                <div style="
                    margin-bottom: 5px;
                    padding: 5px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 3px;
                    border-left: 3px solid ${alert.type === 'error' ? '#F44336' : '#FF9800'};
                ">
                    <div style="font-size: 10px; color: #aaa;">${alert.timestamp}</div>
                    <div style="color: ${alert.type === 'error' ? '#F44336' : '#FF9800'};">
                        ${alert.message}
                    </div>
                </div>
            `).join('');
            
            // Prepend new alerts
            const currentHtml = alertsContainer.innerHTML;
            if (!currentHtml.includes('No alerts')) {
                alertsContainer.innerHTML = alertsHtml + currentHtml;
            } else {
                alertsContainer.innerHTML = alertsHtml;
            }
            
            // Limit alerts history
            const alertDivs = alertsContainer.querySelectorAll('div > div');
            if (alertDivs.length > 10) {
                for (let i = 10; i < alertDivs.length; i++) {
                    alertDivs[i].parentElement.remove();
                }
            }
        }
    }
    
    // Initialize dashboard
    function initializeDashboard() {
        // Wait for page load
        if (document.readyState !== 'complete') {
            window.addEventListener('load', initializeDashboard);
            return;
        }
        
        // Create dashboard
        createDashboard();
        
        // Start update interval
        dashboardState.updateInterval = setInterval(updateDashboard, 1000);
        
        // Initial update
        setTimeout(updateDashboard, 2000);
        
        console.log('Order Validation Health Dashboard initialized');
    }
    
    // Start initialization
    setTimeout(initializeDashboard, 3000);
    
})();