/**
 * Tradovate Scraper Usage Examples
 * This file demonstrates how to use the TradovateScraper class
 */

// Initialize the scraper
const scraper = new TradovateScraper();

// Basic usage - scrape once
function scrapeOnce() {
  const data = scraper.scrapeData();
  
  console.log('=== TRADOVATE DATA SCRAPED ===');
  console.log('\\nActive Tabs:', data.tabs);
  console.log('\\nContract Info:', data.contractInfo);
  console.log('\\nNumber of trades:', data.trades.length);
  console.log('\\nLatest trades:', data.trades.slice(0, 5));
  
  return data;
}

// Real-time monitoring
function startMonitoring() {
  console.log('Starting real-time monitoring...');
  
  // Initial scrape
  const initialData = scraper.scrapeData();
  console.log('Initial data captured. Trades:', initialData.trades.length);
  
  // Set up observer for real-time updates
  const observer = scraper.startRealTimeUpdates((newData) => {
    console.log(`[${new Date().toLocaleTimeString()}] Data updated!`);
    console.log(`- Active symbol: ${newData.tabs.find(t => t.isActive)?.symbol}`);
    console.log(`- Last price: ${newData.contractInfo.lastPrice}`);
    console.log(`- Total trades: ${newData.trades.length}`);
    
    // Show latest trade
    if (newData.trades.length > 0) {
      const latestTrade = newData.trades[0];
      console.log(`- Latest trade: ${latestTrade.timestamp} - Price: ${latestTrade.price}, Size: ${latestTrade.size}`);
    }
  });
  
  return observer;
}

// Export data to file (for use in console)
function exportData() {
  const data = scraper.scrapeData();
  
  // Export as JSON
  const jsonData = scraper.exportAsJSON();
  console.log('\\n=== JSON Export ===');
  console.log(jsonData);
  
  // Export trades as CSV
  const csvData = scraper.exportAsCSV();
  console.log('\\n=== CSV Export ===');
  console.log(csvData);
  
  // To download as file (in browser console):
  // downloadAsFile(jsonData, 'tradovate_data.json', 'application/json');
  // downloadAsFile(csvData, 'tradovate_trades.csv', 'text/csv');
}

// Helper function to download data as file
function downloadAsFile(content, filename, contentType) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Advanced filtering example
function getHighVolumeTradesOnly(minVolume = 50) {
  const data = scraper.scrapeData();
  const highVolumeTrades = data.trades.filter(trade => trade.size >= minVolume);
  
  console.log(`\\nHigh volume trades (>= ${minVolume}):`);
  highVolumeTrades.forEach(trade => {
    console.log(`${trade.timestamp} - Price: ${trade.price}, Size: ${trade.size}, Direction: ${trade.tickDirection}`);
  });
  
  return highVolumeTrades;
}

// Price movement analysis
function analyzePriceMovement() {
  const data = scraper.scrapeData();
  
  if (data.trades.length < 2) {
    console.log('Not enough trades for analysis');
    return;
  }
  
  const upTicks = data.trades.filter(t => t.tickDirection === 'up' || t.tickDirection === 'cont-up').length;
  const downTicks = data.trades.filter(t => t.tickDirection === 'down' || t.tickDirection === 'cont-down').length;
  
  console.log('\\n=== Price Movement Analysis ===');
  console.log(`Up ticks: ${upTicks}`);
  console.log(`Down ticks: ${downTicks}`);
  console.log(`Trend: ${upTicks > downTicks ? 'BULLISH' : 'BEARISH'}`);
  
  // Calculate price range
  const prices = data.trades.map(t => t.price).filter(p => p);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  
  console.log(`Price range: ${minPrice} - ${maxPrice}`);
  console.log(`Range size: ${(maxPrice - minPrice).toFixed(2)}`);
}

// Console usage instructions
console.log(`
=== TRADOVATE SCRAPER LOADED ===

Available functions:
- scrapeOnce()           : Scrape data once
- startMonitoring()      : Start real-time monitoring
- exportData()           : Export data as JSON/CSV
- getHighVolumeTradesOnly(minVolume) : Filter high volume trades
- analyzePriceMovement() : Analyze price trends

To use in browser console:
1. Copy the scraper code and paste it
2. Copy this usage file and paste it
3. Run any of the functions above
`);