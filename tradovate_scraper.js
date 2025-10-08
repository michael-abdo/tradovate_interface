/**
 * Tradovate Trading Data Scraper
 * Extracts trading information from the Tradovate interface DOM
 */

class TradovateScraper {
  constructor() {
    this.data = {
      tabs: [],
      contractInfo: {},
      trades: []
    };
  }

  /**
   * Main scraping function - extracts all relevant data from the DOM
   */
  scrapeData() {
    // Extract tab information
    this.scrapeTabs();
    
    // Extract contract information from header
    this.scrapeContractInfo();
    
    // Extract trade data from the table
    this.scrapeTrades();
    
    return this.data;
  }

  /**
   * Extract tab information (symbols being tracked)
   */
  scrapeTabs() {
    const tabs = document.querySelectorAll('.lm_tab:not(.tab_add) .lm_title span');
    this.data.tabs = Array.from(tabs).map(tab => ({
      symbol: tab.textContent.trim(),
      isActive: tab.closest('.lm_tab').classList.contains('lm_active')
    }));
  }

  /**
   * Extract contract information from the header section
   */
  scrapeContractInfo() {
    // Get contract name
    const contractName = document.querySelector('.header small.text-muted span');
    if (contractName) {
      this.data.contractInfo.name = contractName.textContent.trim();
    }

    // Get last price information
    const lastPriceElement = document.querySelector('.last-price-info .number');
    if (lastPriceElement) {
      this.data.contractInfo.lastPrice = parseFloat(lastPriceElement.textContent.trim());
      
      // Check if price is up or down
      this.data.contractInfo.priceDirection = lastPriceElement.classList.contains('text-success') ? 'up' : 'down';
    }

    // Get price change info
    const priceChangeElement = document.querySelector('.last-price-info .small span:last-child');
    if (priceChangeElement) {
      const changeText = priceChangeElement.textContent.trim();
      const changeMatch = changeText.match(/([\d.-]+)\s*\(([\d.-]+)%\)/);
      if (changeMatch) {
        this.data.contractInfo.priceChange = parseFloat(changeMatch[1]);
        this.data.contractInfo.priceChangePercent = parseFloat(changeMatch[2]);
      }
    }

    // Get total volume
    const volumeElements = document.querySelectorAll('.info-column');
    volumeElements.forEach(elem => {
      const label = elem.querySelector('small.text-muted');
      if (label && label.textContent.includes('Total Volume')) {
        const volumeNumber = elem.querySelector('.number');
        if (volumeNumber) {
          this.data.contractInfo.totalVolume = parseInt(volumeNumber.textContent.trim());
        }
      }
    });

    // Get volume filter setting
    const volumeFilterInput = document.querySelector('.info-column-qty input.form-control');
    if (volumeFilterInput) {
      this.data.contractInfo.volumeFilter = parseInt(volumeFilterInput.value);
    }
  }

  /**
   * Extract trade data from the data table
   */
  scrapeTrades() {
    const tradeRows = document.querySelectorAll('.fixedDataTableRowLayout_main.public_fixedDataTable_bodyRow');
    
    this.data.trades = Array.from(tradeRows).map(row => {
      const trade = {};
      
      // Check if row is visible
      const rowWrapper = row.closest('.fixedDataTableRowLayout_rowWrapper');
      if (rowWrapper && rowWrapper.style.visibility === 'hidden') {
        return null;
      }
      
      // Extract timestamp
      const timestampCell = row.querySelector('.fixedDataTableCellLayout_main:first-child .public_fixedDataTableCell_cellContent');
      if (timestampCell) {
        trade.timestamp = timestampCell.textContent.trim();
        // Extract the actual date value if available
        const timestampValue = row.querySelector('.fixedDataTableCellLayout_main:first-child .fixedDataTableCellLayout_wrap1');
        if (timestampValue && timestampValue.getAttribute('value')) {
          trade.timestampRaw = timestampValue.getAttribute('value');
        }
      }
      
      // Extract price
      const priceCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(2) .public_fixedDataTableCell_cellContent');
      if (priceCell) {
        trade.price = parseFloat(priceCell.textContent.trim());
        // Check tick direction
        const priceWrapper = row.querySelector('.fixedDataTableCellLayout_main:nth-child(2) .fixedDataTableCellLayout_wrap1');
        if (priceWrapper) {
          if (priceWrapper.classList.contains('tick-flip-up')) {
            trade.tickDirection = 'up';
          } else if (priceWrapper.classList.contains('tick-flip-down')) {
            trade.tickDirection = 'down';
          } else if (priceWrapper.classList.contains('tick-cont-up')) {
            trade.tickDirection = 'cont-up';
          } else if (priceWrapper.classList.contains('tick-cont-down')) {
            trade.tickDirection = 'cont-down';
          }
        }
      }
      
      // Extract size
      const sizeCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(3) .public_fixedDataTableCell_cellContent');
      if (sizeCell) {
        trade.size = parseInt(sizeCell.textContent.trim());
      }
      
      // Extract accumulated volume
      const accCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(4) .public_fixedDataTableCell_cellContent');
      if (accCell) {
        trade.accumulatedVolume = parseInt(accCell.textContent.trim());
      }
      
      // Check if this is a highlighted row
      trade.isHighlighted = row.classList.contains('public_fixedDataTableRow_highlighted');
      
      return trade;
    }).filter(trade => trade !== null);
  }

  /**
   * Get real-time updates by setting up a MutationObserver
   */
  startRealTimeUpdates(callback) {
    const targetNode = document.querySelector('.fixedDataTableLayout_rowsContainer');
    
    if (!targetNode) {
      console.error('Could not find table container for real-time updates');
      return null;
    }
    
    const config = {
      childList: true,
      subtree: true,
      attributes: true,
      attributeOldValue: true
    };
    
    const observer = new MutationObserver((mutationsList) => {
      // Re-scrape data on mutations
      const newData = this.scrapeData();
      callback(newData);
    });
    
    observer.observe(targetNode, config);
    
    return observer; // Return observer so it can be disconnected later
  }
  
  /**
   * Export data as JSON
   */
  exportAsJSON() {
    return JSON.stringify(this.data, null, 2);
  }
  
  /**
   * Export data as CSV (trades only)
   */
  exportAsCSV() {
    if (this.data.trades.length === 0) return '';
    
    const headers = ['Timestamp', 'Price', 'Size', 'Accumulated Volume', 'Tick Direction', 'Highlighted'];
    const rows = this.data.trades.map(trade => [
      trade.timestamp || '',
      trade.price || '',
      trade.size || '',
      trade.accumulatedVolume || '',
      trade.tickDirection || '',
      trade.isHighlighted ? 'Yes' : 'No'
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\\n');
    
    return csvContent;
  }
}

// Usage example:
// const scraper = new TradovateScraper();
// const data = scraper.scrapeData();
// console.log(data);

// For real-time updates:
// const observer = scraper.startRealTimeUpdates((newData) => {
//   console.log('Data updated:', newData);
// });

// To stop real-time updates:
// observer.disconnect();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TradovateScraper;
}