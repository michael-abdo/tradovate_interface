/**
 * Tradovate Scraper Bookmarklet
 * Save this as a browser bookmark to quickly inject the scraper into Tradovate
 */

javascript:(function(){
  /* Inject TradovateScraper class */
  window.TradovateScraper = class {
    constructor() {
      this.data = {tabs: [], contractInfo: {}, trades: []};
    }
    
    scrapeData() {
      this.scrapeTabs();
      this.scrapeContractInfo();
      this.scrapeTrades();
      return this.data;
    }
    
    scrapeTabs() {
      const tabs = document.querySelectorAll('.lm_tab:not(.tab_add) .lm_title span');
      this.data.tabs = Array.from(tabs).map(tab => ({
        symbol: tab.textContent.trim(),
        isActive: tab.closest('.lm_tab').classList.contains('lm_active')
      }));
    }
    
    scrapeContractInfo() {
      const contractName = document.querySelector('.header small.text-muted span');
      if (contractName) this.data.contractInfo.name = contractName.textContent.trim();
      
      const lastPriceElement = document.querySelector('.last-price-info .number');
      if (lastPriceElement) {
        this.data.contractInfo.lastPrice = parseFloat(lastPriceElement.textContent.trim());
        this.data.contractInfo.priceDirection = lastPriceElement.classList.contains('text-success') ? 'up' : 'down';
      }
      
      const volumeElements = document.querySelectorAll('.info-column');
      volumeElements.forEach(elem => {
        const label = elem.querySelector('small.text-muted');
        if (label && label.textContent.includes('Total Volume')) {
          const volumeNumber = elem.querySelector('.number');
          if (volumeNumber) this.data.contractInfo.totalVolume = parseInt(volumeNumber.textContent.trim());
        }
      });
    }
    
    scrapeTrades() {
      const tradeRows = document.querySelectorAll('.fixedDataTableRowLayout_main.public_fixedDataTable_bodyRow');
      this.data.trades = Array.from(tradeRows).map(row => {
        const trade = {};
        const rowWrapper = row.closest('.fixedDataTableRowLayout_rowWrapper');
        if (rowWrapper && rowWrapper.style.visibility === 'hidden') return null;
        
        const timestampCell = row.querySelector('.fixedDataTableCellLayout_main:first-child .public_fixedDataTableCell_cellContent');
        if (timestampCell) trade.timestamp = timestampCell.textContent.trim();
        
        const priceCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(2) .public_fixedDataTableCell_cellContent');
        if (priceCell) trade.price = parseFloat(priceCell.textContent.trim());
        
        const sizeCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(3) .public_fixedDataTableCell_cellContent');
        if (sizeCell) trade.size = parseInt(sizeCell.textContent.trim());
        
        const accCell = row.querySelector('.fixedDataTableCellLayout_main:nth-child(4) .public_fixedDataTableCell_cellContent');
        if (accCell) trade.accumulatedVolume = parseInt(accCell.textContent.trim());
        
        return trade;
      }).filter(trade => trade !== null);
    }
  };
  
  /* Create scraper instance and show data */
  const scraper = new TradovateScraper();
  const data = scraper.scrapeData();
  
  console.log('🎯 Tradovate Data Scraped:', data);
  alert(`Tradovate Scraper Loaded!\\n\\nActive Symbol: ${data.tabs.find(t => t.isActive)?.symbol || 'None'}\\nLast Price: ${data.contractInfo.lastPrice || 'N/A'}\\nTrades Captured: ${data.trades.length}\\n\\nCheck console for full data.`);
  
  /* Make scraper available globally */
  window.tradovateScraper = scraper;
  console.log('Scraper available as: window.tradovateScraper');
})();