# Tradovate Trading Data Scraper

A JavaScript scraper for extracting real-time trading data from the Tradovate interface.

## Features

- **Tab Extraction**: Captures all active trading symbols/contracts
- **Contract Information**: Extracts current price, volume, and price changes
- **Trade History**: Scrapes time & sales data including timestamp, price, size, and accumulated volume
- **Real-time Updates**: Optional MutationObserver for live data monitoring
- **Export Options**: JSON and CSV export functionality
- **Tick Direction Tracking**: Identifies up/down price movements

## Files

- `tradovate_scraper.js` - Main scraper class
- `scraper_usage.js` - Usage examples and helper functions
- `bookmarklet.js` - Browser bookmarklet version

## Usage

### Browser Console Method

1. Open Tradovate in your browser
2. Open Developer Tools (F12)
3. Copy and paste the contents of `tradovate_scraper.js` into the console
4. Copy and paste the contents of `scraper_usage.js` into the console
5. Use the provided functions:

```javascript
// Scrape data once
scrapeOnce();

// Start real-time monitoring
const observer = startMonitoring();

// Export data
exportData();

// Get high volume trades only (size >= 50)
getHighVolumeTradesOnly(50);

// Analyze price movement
analyzePriceMovement();
```

### Bookmarklet Method

1. Create a new bookmark in your browser
2. Set the URL to the entire contents of `bookmarklet.js`
3. Click the bookmarklet while on the Tradovate page
4. The scraper will load and show an alert with basic info
5. Use `window.tradovateScraper` in the console

## Data Structure

```javascript
{
  tabs: [
    {
      symbol: "NQZ5",
      isActive: true
    }
  ],
  contractInfo: {
    name: "E-Mini NASDAQ 100",
    lastPrice: 25145.50,
    priceDirection: "up",
    priceChange: 106.25,
    priceChangePercent: 0.42,
    totalVolume: 122449,
    volumeFilter: 20
  },
  trades: [
    {
      timestamp: "08:52:25.037 10/8/25",
      price: 25146.00,
      size: 30,
      accumulatedVolume: 30,
      tickDirection: "down",
      isHighlighted: false
    }
  ]
}
```

## Real-time Monitoring

The scraper can monitor DOM changes for live updates:

```javascript
const observer = scraper.startRealTimeUpdates((newData) => {
  console.log('Data updated:', newData);
});

// To stop monitoring:
observer.disconnect();
```

## Export Functions

```javascript
// Get JSON string
const jsonData = scraper.exportAsJSON();

// Get CSV of trades
const csvData = scraper.exportAsCSV();

// Download as file (browser only)
downloadAsFile(jsonData, 'tradovate_data.json', 'application/json');
```

## Notes

- The scraper is designed for the specific DOM structure shown in the example
- Real-time monitoring may impact performance on busy trading days
- Volume filter captures the UI setting but doesn't filter the scraped data
- Highlighted trades are marked in the data structure