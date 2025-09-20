# Tradovate Options Data Integration

## Overview
This integration connects to the Tradovate API to retrieve full options chain data for NQ (E-mini NASDAQ-100) futures options.

## API Credentials
- **Client ID (CID)**: 6540
- **Secret**: f7a2b8f5-8348-424f-8ffa-047ab7502b7c

## Requirements
- Tradovate account (demo or live)
- Username and password for authentication
- For live trading: Account with >$1,000 and API Access subscription ($25/month)

## Scripts

### 1. `tradovate_options_client.py`
Main client for retrieving NQ options chain data.

**Features:**
- OAuth authentication
- REST API integration
- WebSocket support for real-time data
- Full options chain retrieval
- Data saving to JSON format

**Usage:**
```bash
python scripts/tradovate_options_client.py
# Enter username and password when prompted
```

### 2. `tradovate_api_explorer.py`
Exploration tool to discover available endpoints and data structures.

**Features:**
- Comprehensive API exploration
- Product discovery
- Contract group analysis
- Automatic data saving for analysis

**Usage:**
```bash
python scripts/tradovate_api_explorer.py
# Enter username and password when prompted
```

## API Endpoints

### Authentication
- **POST** `/v1/auth/accesstokenrequest` - Get access token

### Contracts
- **GET** `/v1/contract/find?name={symbol}` - Find contracts by symbol
- **GET** `/v1/contract/item?id={id}` - Get contract details
- **GET** `/v1/contract/ldeps?ids={productId}` - Get contracts for product
- **GET** `/v1/contract/deps?masterid={contractId}` - Get related contracts

### Products
- **GET** `/v1/product/list` - List all products
- **GET** `/v1/product/find?name={name}` - Find products by name

### WebSocket URLs
- **Demo API**: `wss://demo.tradovateapi.com/v1/websocket`
- **Demo Market Data**: `wss://md-demo.tradovateapi.com/v1/websocket`
- **Live API**: `wss://live.tradovateapi.com/v1/websocket`
- **Live Market Data**: `wss://md.tradovateapi.com/v1/websocket`

## Contract Symbol Format

### Futures
- Format: `{BASE}{MONTH}{YEAR}`
- Example: `NQM5` (NQ June 2025)

### Month Codes
- H = March
- M = June
- U = September
- Z = December

### Options (Expected Format)
- Calls: `C{STRIKE}` (e.g., `C21500`)
- Puts: `P{STRIKE}` (e.g., `P21500`)

## Data Output
The scripts save data to:
- `data/tradovate_options/` - Options chain data
- `data/tradovate_exploration/` - API exploration results

## Next Steps
1. Run the explorer script to discover exact option product codes
2. Analyze the saved JSON files to understand data structure
3. Update the options client with correct product/contract queries
4. Implement real-time data streaming via WebSocket

## Notes
- The demo environment may have limited options data
- Options on futures may require specific product codes (e.g., NQO, ONQ)
- Check exploration results for exact product names and IDs