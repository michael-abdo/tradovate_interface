# Tradovate Market Data Scraper Integration

## Overview

The Tradovate Market Data Scraper is now fully integrated into the trading system, providing real-time capture and persistence of market trades from the Tradovate interface. The scraper runs as a Tampermonkey UserScript that is automatically injected into Chrome instances via the Chrome DevTools Protocol.

## Architecture

### Components

1. **Frontend (JavaScript)**
   - `scripts/tampermonkey/tradovateScraper.user.js` - Main scraper UserScript
   - Automatically injected via Chrome DevTools Protocol
   - Captures DOM data and sends via console logging

2. **Backend (Python)**
   - `src/services/scraper_service.py` - Data persistence and management
   - `src/chrome_logger.py` - Enhanced to parse [SCRAPER_DATA] messages
   - `src/dashboard.py` - Flask API endpoints for scraper control

3. **Configuration**
   - `config/trading_defaults.json` - Contains scraper_config section
   - Configurable parameters: enabled, interval, volume_filter, debug

4. **Data Storage**
   - JSON files in `data/scraped_trades/`
   - Format: `YYYY-MM-DD_trades.json`
   - Automatic persistence every 60 seconds
   - 7-day retention policy (configurable)

## Data Flow

```
1. Tradovate DOM
   ↓
2. tradovateScraper.user.js (extracts data)
   ↓
3. Console log: [SCRAPER_DATA] {json}
   ↓
4. ChromeLogger (detects and parses)
   ↓
5. ScraperService (buffers and persists)
   ↓
6. JSON files + In-memory buffer
   ↓
7. Flask Dashboard API
```

## Configuration

### trading_defaults.json

```json
"scraper_config": {
  "enabled": false,          // Enable/disable scraper
  "interval": 1000,          // Scraping interval in ms
  "volume_filter": 0,        // Min volume to capture (0 = all)
  "debug": false,            // Debug logging
  "persist_interval": 60,    // Auto-save interval (seconds)
  "buffer_size": 1000,       // Max trades in memory
  "days_to_keep": 7,         // Data retention period
  "auto_start": false        // Start on script load
}
```

## Usage

### Starting the Scraper

The scraper is automatically injected when Chrome instances are launched. To control it:

1. **Via Dashboard API:**
   ```bash
   # Enable scraper
   curl -X POST http://localhost:6001/api/scraper/config \
     -H "Content-Type: application/json" \
     -d '{"enabled": true, "interval": 1000}'
   ```

2. **Via Browser Console:**
   ```javascript
   // Start scraping
   TradovateScraperControl.start();
   
   // Stop scraping
   TradovateScraperControl.stop();
   
   // Configure
   TradovateScraperControl.setConfig('volumeFilter', 50);
   ```

3. **Via localStorage (persistent):**
   ```javascript
   localStorage.setItem('scraper_enabled', 'true');
   localStorage.setItem('scraper_interval', '500');
   ```

### Dashboard API Endpoints

- `GET /api/scraper/status` - Get scraper status
- `GET /api/scraper/data` - Get recent trades
- `GET /api/scraper/export` - Export data (JSON/CSV)
- `POST /api/scraper/config` - Update configuration
- `POST /api/scraper/persist` - Force data save

### Exporting Data

```bash
# Export today's data as JSON
curl http://localhost:6001/api/scraper/export?format=json > trades.json

# Export date range as CSV
curl "http://localhost:6001/api/scraper/export?format=csv&start_date=2025-01-01&end_date=2025-01-07" > trades.csv

# Export specific account
curl "http://localhost:6001/api/scraper/data?account=user1&limit=500" > account_trades.json
```

## Data Structure

### Scraped Data Format

```json
{
  "timestamp": "2025-01-08T14:30:00.000Z",
  "account": "user1",
  "tabs": [
    {
      "symbol": "NQZ5",
      "isActive": true
    }
  ],
  "contractInfo": {
    "name": "E-Mini NASDAQ 100",
    "lastPrice": 25145.50,
    "priceDirection": "up",
    "priceChange": 106.25,
    "priceChangePercent": 0.42,
    "totalVolume": 122449
  },
  "trades": [
    {
      "timestamp": "08:52:25.037 10/8/25",
      "price": 25146.00,
      "size": 30,
      "accumulatedVolume": 30,
      "tickDirection": "down",
      "isHighlighted": false,
      "account": "user1",
      "captured_at": "2025-01-08T14:30:00.000Z"
    }
  ]
}
```

### Storage Format

Daily JSON files contain an array of all trades for that day:

```json
[
  {
    "timestamp": "08:52:25.037 10/8/25",
    "price": 25146.00,
    "size": 30,
    "accumulatedVolume": 30,
    "tickDirection": "down",
    "isHighlighted": false,
    "account": "user1",
    "captured_at": "2025-01-08T14:30:00.000Z"
  },
  // ... more trades
]
```

## Integration with Existing Workflow

1. **Auto-injection**: The scraper is automatically injected when `app.py` calls `inject_tampermonkey()`
2. **Account Association**: Each Chrome instance's username is passed to the ChromeLogger for proper account tracking
3. **Reload Support**: Running `python3 reload.py` will reload the scraper along with other scripts
4. **Dashboard Integration**: Scraper status and data are available through the main dashboard

## Monitoring and Debugging

### Check Scraper Status

```javascript
// In browser console
TradovateScraperControl.getConfig()
TradovateScraperControl.getData()
```

### View Chrome Logs

```bash
# Check Chrome console logs for scraper messages
tail -f logs/*/chrome_console_*.log | grep SCRAPER
```

### Debug Mode

Enable debug logging:
```javascript
TradovateScraperControl.setConfig('debug', true);
```

## Best Practices

1. **Volume Filtering**: Set appropriate volume filter to reduce noise
2. **Interval Tuning**: Balance between data freshness and performance
3. **Regular Exports**: Set up automated exports for long-term storage
4. **Monitor Buffer**: Check buffer size to ensure data isn't lost
5. **Clean Old Data**: Use the clean_old_data() method periodically

## Troubleshooting

### Scraper Not Starting
1. Check if script is injected: Look for "[Tradovate Scraper] Initializing" in console
2. Verify configuration: `localStorage.getItem('scraper_enabled')`
3. Check for errors: Look for red errors in browser console

### No Data Being Captured
1. Verify DOM structure matches expectations
2. Check if trades table is visible
3. Enable debug mode and check console logs
4. Verify account name is being passed correctly

### Data Not Persisting
1. Check write permissions on `data/scraped_trades/`
2. Verify scraper service is running
3. Check Flask logs for errors
4. Force persist: `curl -X POST http://localhost:6001/api/scraper/persist`

## Future Enhancements

1. **Real-time WebSocket**: Direct WebSocket connection for lower latency
2. **Advanced Filtering**: More sophisticated trade filtering options
3. **Analytics**: Built-in analysis tools for captured data
4. **Alerts**: Configurable alerts for specific market conditions
5. **Database Storage**: Option to use SQLite/PostgreSQL for large datasets