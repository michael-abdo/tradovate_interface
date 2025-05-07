// ==UserScript==
// @name         Tradovate Positions Table Checker
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Monitor the Positions table in Tradovate for changes
// @author       Claude
// @match        *://*.tradovate.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        checkInterval: 1000, // Check positions table every 1 second
        logToConsole: true,  // Output position data to console
        highlightChanges: true, // Highlight position changes
        highlightColor: '#FFFF99', // Highlight color (light yellow)
        fadeTime: 3000, // Time in ms for highlight to fade
    };
    
    // Store previous positions for change detection
    let previousPositions = {};
    
    // Create a custom logger
    const logger = {
        log: function(msg) {
            if (CONFIG.logToConsole) {
                console.log(`[Positions Monitor] ${msg}`);
            }
        },
        warn: function(msg) {
            if (CONFIG.logToConsole) {
                console.warn(`[Positions Monitor] ${msg}`);
            }
        },
        error: function(msg) {
            if (CONFIG.logToConsole) {
                console.error(`[Positions Monitor] ${msg}`);
            }
        }
    };
    
    // Helper function to safely get nested properties
    function getNestedValue(obj, path, defaultValue = null) {
        const travel = (regexp) =>
            String.prototype.split
                .call(path, regexp)
                .filter(Boolean)
                .reduce((res, key) => (res !== null && res !== undefined ? res[key] : res), obj);
        const result = travel(/[,[\]]+?/) || travel(/[,[\].]+?/);
        return result === undefined || result === obj ? defaultValue : result;
    }
    
    // Find the Positions table in the DOM
    function findPositionsTable() {
        // Look for the header element with "Positions" text
        const positionsHeaders = Array.from(document.querySelectorAll('.lm_tab span.lm_title span'))
            .filter(el => el.textContent === 'Positions');
        
        if (!positionsHeaders.length) {
            logger.log("Positions tab not found");
            return null;
        }
        
        // Find the active positions tab
        const activeTab = positionsHeaders.find(header => {
            const parentTab = header.closest('.lm_tab');
            return parentTab && parentTab.classList.contains('lm_active');
        });
        
        if (!activeTab) {
            logger.log("Positions tab is not active");
            
            // If there's at least one positions tab, we can find its container
            const firstTab = positionsHeaders[0];
            const tabContent = firstTab.closest('.lm_tab');
            if (!tabContent) return null;
            
            const itemContainer = tabContent.closest('.lm_item');
            if (!itemContainer) return null;
            
            const tableContainer = itemContainer.querySelector('.module.positions.data-table');
            return tableContainer;
        }
        
        // If the tab is active, find the corresponding table content
        const tabContent = activeTab.closest('.lm_tab');
        if (!tabContent) return null;
        
        const itemContainer = tabContent.closest('.lm_item');
        if (!itemContainer) return null;
        
        const tableContainer = itemContainer.querySelector('.module.positions.data-table');
        return tableContainer;
    }
    
    // Parse the positions data from the table
    function parsePositionsTable() {
        const tableContainer = findPositionsTable();
        if (!tableContainer) {
            logger.warn("Positions table not found in the DOM");
            return {};
        }
        
        // Find all rows in the positions table (excluding header)
        const rows = tableContainer.querySelectorAll('.public_fixedDataTable_bodyRow');
        if (!rows.length) {
            logger.log("No position rows found");
            return {};
        }
        
        const positions = {};
        
        // Process each row
        rows.forEach((row, index) => {
            // Find the symbol name
            const symbolCell = row.querySelector('.symbol-name-cell');
            if (!symbolCell) return;
            
            const symbolElement = symbolCell.querySelector('.subline div:first-child');
            if (!symbolElement) return;
            
            const symbol = symbolElement.textContent.trim();
            
            // Find the position size (Net Pos)
            const cells = row.querySelectorAll('.fixedDataTableCellLayout_alignRight');
            if (cells.length < 1) return;
            
            const netPosElement = cells[0].querySelector('.public_fixedDataTableCell_cellContent');
            const netPos = netPosElement ? netPosElement.textContent.trim() : '0';
            
            // Find the position price
            const priceElement = cells.length > 1 ? cells[1].querySelector('.public_fixedDataTableCell_cellContent') : null;
            const price = priceElement ? priceElement.textContent.trim() : '';
            
            // Find the P/L
            const plElement = cells.length > 2 ? cells[2].querySelector('.public_fixedDataTableCell_cellContent') : null;
            const pnl = plElement ? plElement.textContent.trim() : '$0.00';
            
            // Store the position
            positions[symbol] = {
                symbol: symbol,
                netPos: netPos,
                price: price,
                pnl: pnl,
                rowElement: row
            };
        });
        
        return positions;
    }
    
    // Highlight changes in the position data
    function highlightChanges(currentPositions) {
        if (!CONFIG.highlightChanges) return;
        
        // Compare with previous positions
        Object.entries(currentPositions).forEach(([symbol, pos]) => {
            const prev = previousPositions[symbol];
            if (!prev) {
                // New position
                highlightRow(pos.rowElement, 'New position added');
                return;
            }
            
            // Check for changes
            if (pos.netPos !== prev.netPos) {
                highlightRow(pos.rowElement, `Position size changed: ${prev.netPos} → ${pos.netPos}`);
            } else if (pos.pnl !== prev.pnl) {
                // Only highlight significant P/L changes (more than just pennies)
                const prevValue = parseFloat(prev.pnl.replace(/[$,]/g, ''));
                const currValue = parseFloat(pos.pnl.replace(/[$,]/g, ''));
                if (Math.abs(currValue - prevValue) >= 1.0) {
                    highlightRow(pos.rowElement, `P/L changed: ${prev.pnl} → ${pos.pnl}`);
                }
            }
        });
        
        // Check for removed positions
        Object.entries(previousPositions).forEach(([symbol, prev]) => {
            if (!currentPositions[symbol]) {
                logger.log(`Position closed: ${symbol}`);
            }
        });
    }
    
    // Apply highlight to a row
    function highlightRow(rowElement, reason) {
        if (!rowElement) return;
        
        logger.log(reason);
        
        // Apply background color
        const originalBg = rowElement.style.backgroundColor;
        rowElement.style.backgroundColor = CONFIG.highlightColor;
        rowElement.style.transition = `background-color ${CONFIG.fadeTime/1000}s ease-in-out`;
        
        // Fade back to original color
        setTimeout(() => {
            rowElement.style.backgroundColor = originalBg;
        }, CONFIG.fadeTime);
    }
    
    // Export position data for external use
    function exportPositionData(positions) {
        // Convert positions object to a clean array of position data
        const positionData = Object.values(positions).map(p => ({
            symbol: p.symbol,
            netPos: parseInt(p.netPos) || 0,
            price: p.price,
            pnl: p.pnl
        }));
        
        // Make this data available to other scripts
        window.tradovatePositions = positionData;
        
        // Also provide a custom event for other scripts to listen for
        const event = new CustomEvent('tradovatePositionsUpdated', { 
            detail: { positions: positionData } 
        });
        document.dispatchEvent(event);
    }
    
    // Main function to check positions
    function checkPositions() {
        try {
            const currentPositions = parsePositionsTable();
            
            // Log the positions data
            if (Object.keys(currentPositions).length > 0) {
                logger.log(`Found ${Object.keys(currentPositions).length} positions`);
                
                // Check for changes and highlight
                highlightChanges(currentPositions);
                
                // Export data
                exportPositionData(currentPositions);
                
                // Update previous positions
                previousPositions = JSON.parse(JSON.stringify(currentPositions));
            }
        } catch (error) {
            logger.error(`Error checking positions: ${error.message}`);
        }
    }
    
    // Get all positions (can be called externally)
    window.getTradePositions = function() {
        return parsePositionsTable();
    };
    
    // Start monitoring positions
    function startMonitoring() {
        logger.log("Starting positions monitoring...");
        
        // Look for the Positions table
        if (findPositionsTable()) {
            logger.log("Positions table found, beginning monitoring");
            
            // Do initial check
            checkPositions();
            
            // Setup interval to check positions regularly
            setInterval(checkPositions, CONFIG.checkInterval);
        } else {
            // If table not found on first try, retry after a delay
            logger.log("Positions table not found, will retry in 5 seconds");
            setTimeout(startMonitoring, 5000);
        }
    }
    
    // Start monitoring after a short delay to ensure DOM is fully loaded
    setTimeout(startMonitoring, 2000);
})();