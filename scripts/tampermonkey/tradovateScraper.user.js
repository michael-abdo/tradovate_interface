// ==UserScript==
// @name         Tradovate Market Data Scraper
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Scrapes real-time trading data from Tradovate interface
// @author       Trading System
// @match        https://trader.tradovate.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/tradovateScraper.user.js
// @downloadURL  http://localhost:8080/tradovateScraper.user.js
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('[Tradovate Scraper] Initializing market data scraper...');
    
    // Configuration
    const config = {
        enabled: localStorage.getItem('scraper_enabled') === 'true' || false,
        interval: parseInt(localStorage.getItem('scraper_interval') || '1000'),
        volumeFilter: parseInt(localStorage.getItem('scraper_volume_filter') || '0'),
        debug: localStorage.getItem('scraper_debug') === 'true' || false
    };
    
    // Logger utility
    const logger = {
        log: (msg, data) => {
            if (config.debug) console.log(`[Tradovate Scraper] ${msg}`, data || '');
        },
        info: (msg, data) => console.info(`[Tradovate Scraper] ${msg}`, data || ''),
        warn: (msg, data) => console.warn(`[Tradovate Scraper] ${msg}`, data || ''),
        error: (msg, data) => console.error(`[Tradovate Scraper] ${msg}`, data || ''),
        data: (data) => {
            // Special format for Python backend to parse
            console.log(`[SCRAPER_DATA] ${JSON.stringify(data)}`);
        }
    };
    
    class TradovateScraper {
        constructor() {
            this.data = {
                timestamp: new Date().toISOString(),
                tabs: [],
                contractInfo: {},
                trades: [],
                account: this.getCurrentAccount()
            };
            this.observer = null;
            this.scrapeTimer = null;
        }
        
        getCurrentAccount() {
            // Get current account from the account selector if available
            const accountElement = document.querySelector('.account-selector-value');
            return accountElement ? accountElement.textContent.trim() : 'Unknown';
        }
        
        start() {
            if (!config.enabled) {
                logger.info('Scraper is disabled. Enable via localStorage: scraper_enabled = true');
                return;
            }
            
            logger.info('Starting market data scraper...');
            
            // Initial scrape
            this.scrapeData();
            
            // Set up periodic scraping
            if (config.interval > 0) {
                this.scrapeTimer = setInterval(() => {
                    this.scrapeData();
                }, config.interval);
            }
            
            // Set up DOM observer for real-time updates
            this.setupObserver();
        }
        
        stop() {
            logger.info('Stopping market data scraper...');
            
            if (this.scrapeTimer) {
                clearInterval(this.scrapeTimer);
                this.scrapeTimer = null;
            }
            
            if (this.observer) {
                this.observer.disconnect();
                this.observer = null;
            }
        }
        
        scrapeData() {
            try {
                this.data.timestamp = new Date().toISOString();
                this.data.account = this.getCurrentAccount();
                
                this.scrapeTabs();
                this.scrapeContractInfo();
                this.scrapeTrades();
                
                // Send data to backend via console log
                logger.data(this.data);
                
                logger.log('Data scraped successfully', {
                    tabs: this.data.tabs.length,
                    trades: this.data.trades.length
                });
                
            } catch (error) {
                logger.error('Error during scraping:', error);
            }
        }
        
        scrapeTabs() {
            const tabs = document.querySelectorAll('.lm_tab:not(.tab_add) .lm_title span');
            this.data.tabs = Array.from(tabs).map(tab => ({
                symbol: tab.textContent.trim(),
                isActive: tab.closest('.lm_tab').classList.contains('lm_active')
            }));
            logger.log(`Found ${this.data.tabs.length} tabs`);
        }
        
        scrapeContractInfo() {
            this.data.contractInfo = {};
            
            // Contract name
            const contractName = document.querySelector('.header small.text-muted span');
            if (contractName) {
                this.data.contractInfo.name = contractName.textContent.trim();
            }
            
            // Last price and direction
            const lastPriceElement = document.querySelector('.last-price-info .number');
            if (lastPriceElement) {
                this.data.contractInfo.lastPrice = parseFloat(lastPriceElement.textContent.replace(/,/g, ''));
                this.data.contractInfo.priceDirection = lastPriceElement.classList.contains('text-success') ? 'up' : 'down';
            }
            
            // Price change
            const priceChangeElement = document.querySelector('.last-price-info .small');
            if (priceChangeElement) {
                const changeText = priceChangeElement.textContent.trim();
                const changeMatch = changeText.match(/([\d.-]+)\s*\(([\d.-]+)%\)/);
                if (changeMatch) {
                    this.data.contractInfo.priceChange = parseFloat(changeMatch[1]);
                    this.data.contractInfo.priceChangePercent = parseFloat(changeMatch[2]);
                }
            }
            
            // Total volume
            const volumeElements = document.querySelectorAll('.info-column');
            volumeElements.forEach(elem => {
                const label = elem.querySelector('small.text-muted');
                if (label && label.textContent.includes('Total Volume')) {
                    const volumeNumber = elem.querySelector('.number');
                    if (volumeNumber) {
                        this.data.contractInfo.totalVolume = parseInt(volumeNumber.textContent.replace(/,/g, ''));
                    }
                }
            });
            
            logger.log('Contract info scraped', this.data.contractInfo);
        }
        
        scrapeTrades() {
            const tradeRows = document.querySelectorAll('.fixedDataTableRowLayout_main.public_fixedDataTable_bodyRow');
            
            this.data.trades = Array.from(tradeRows).map(row => {
                const trade = {};
                
                // Check visibility
                const rowWrapper = row.closest('.fixedDataTableRowLayout_rowWrapper');
                if (rowWrapper && rowWrapper.style.visibility === 'hidden') {
                    return null;
                }
                
                // Extract cell data
                const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
                if (cells.length >= 4) {
                    trade.timestamp = cells[0].textContent.trim();
                    trade.price = parseFloat(cells[1].textContent.replace(/,/g, ''));
                    trade.size = parseInt(cells[2].textContent);
                    trade.accumulatedVolume = parseInt(cells[3].textContent);
                }
                
                // Get tick direction
                const priceWrapper = row.querySelector('.fixedDataTableCellLayout_main:nth-child(2) .fixedDataTableCellLayout_wrap1');
                if (priceWrapper) {
                    const classes = priceWrapper.className;
                    if (classes.includes('tick-flip-up')) trade.tickDirection = 'up';
                    else if (classes.includes('tick-flip-down')) trade.tickDirection = 'down';
                    else if (classes.includes('tick-cont-up')) trade.tickDirection = 'cont-up';
                    else if (classes.includes('tick-cont-down')) trade.tickDirection = 'cont-down';
                }
                
                // Check if highlighted
                trade.isHighlighted = row.classList.contains('public_fixedDataTableRow_highlighted');
                
                // Apply volume filter
                if (config.volumeFilter > 0 && trade.size < config.volumeFilter) {
                    return null;
                }
                
                return trade;
            }).filter(trade => trade !== null);
            
            logger.log(`Found ${this.data.trades.length} trades (filter: ${config.volumeFilter})`);
        }
        
        setupObserver() {
            const targetNode = document.querySelector('.fixedDataTableLayout_rowsContainer');
            
            if (!targetNode) {
                logger.warn('Could not find trade table container for monitoring');
                return;
            }
            
            const observerConfig = {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'style']
            };
            
            this.observer = new MutationObserver((mutations) => {
                // Debounce rapid mutations
                if (this.observerTimeout) clearTimeout(this.observerTimeout);
                
                this.observerTimeout = setTimeout(() => {
                    logger.log('DOM mutation detected, re-scraping...');
                    this.scrapeData();
                }, 100);
            });
            
            this.observer.observe(targetNode, observerConfig);
            logger.info('DOM observer set up for real-time monitoring');
        }
    }
    
    // Global scraper instance
    let scraper = null;
    
    // Control functions exposed to window
    window.TradovateScraperControl = {
        start: () => {
            if (scraper) scraper.stop();
            scraper = new TradovateScraper();
            scraper.start();
        },
        
        stop: () => {
            if (scraper) scraper.stop();
        },
        
        setConfig: (key, value) => {
            config[key] = value;
            localStorage.setItem(`scraper_${key}`, value);
            logger.info(`Config updated: ${key} = ${value}`);
        },
        
        getConfig: () => config,
        
        scrapeOnce: () => {
            if (!scraper) scraper = new TradovateScraper();
            scraper.scrapeData();
        },
        
        getData: () => scraper ? scraper.data : null
    };
    
    // Wait for page to be ready
    function waitForTradovate() {
        const checkInterval = setInterval(() => {
            // Look for key Tradovate elements
            if (document.querySelector('.lm_tab') || 
                document.querySelector('.fixedDataTable_main')) {
                
                clearInterval(checkInterval);
                logger.info('Tradovate interface detected, initializing scraper...');
                
                // Auto-start if enabled
                if (config.enabled) {
                    window.TradovateScraperControl.start();
                } else {
                    logger.info('Scraper loaded but not started. Use TradovateScraperControl.start() to begin.');
                }
            }
        }, 1000);
    }
    
    // Start initialization
    waitForTradovate();
    
    logger.info('Tradovate Market Data Scraper loaded successfully');
    
})();