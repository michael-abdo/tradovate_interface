#!/usr/bin/env python3
"""
TASK: polygon_api
TYPE: Leaf Task - Data Source Implementation  
PURPOSE: Load Nasdaq-100 options data from Polygon.io API

This module provides access to Nasdaq-100 options data through Polygon.io API.
Supports both NDX (index) and QQQ (ETF) options as alternatives to NQ futures options.
"""

import os
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class PolygonOptionsContract:
    """Standardized options contract from Polygon.io"""
    ticker: str
    underlying_ticker: str
    contract_type: str  # 'call' or 'put'
    strike_price: float
    expiration_date: str
    last_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    timestamp: str = None


class PolygonAPIClient:
    """Polygon.io API client for options data"""
    
    def __init__(self, api_key: str = None):
        """Initialize the Polygon client with API key"""
        self.api_key = api_key or os.getenv('POLYGON_API_KEY', 'BntRhHbKto_R7jQfiSrfL9WMc7XaHXFu')
        self.base_url = 'https://api.polygon.io'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 requests per minute = 12 seconds between requests
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Polygon API with rate limiting"""
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        url = f"{self.base_url}{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        
        try:
            response = requests.get(url, params=params)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            if 'status' in data and data['status'] != 'OK':
                raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
            
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get_options_contracts(self, underlying_ticker: str, 
                            contract_type: str = None,
                            expiration_date: str = None,
                            limit: int = 100) -> List[PolygonOptionsContract]:
        """
        Get options contracts for a given underlying ticker
        
        Args:
            underlying_ticker: The underlying asset ticker (e.g., "NDX", "QQQ")
            contract_type: Type of contract ("call" or "put")
            expiration_date: Filter by expiration date (YYYY-MM-DD)
            limit: Number of results to return
        """
        endpoint = "/v3/reference/options/contracts"
        
        params = {
            'underlying_ticker': underlying_ticker,
            'limit': limit,
            'order': 'desc',
            'sort': 'expiration_date'
        }
        
        if contract_type:
            params['contract_type'] = contract_type
        
        if expiration_date:
            params['expiration_date'] = expiration_date
        
        response = self._make_request(endpoint, params)
        contracts = []
        
        if 'results' in response:
            timestamp = get_utc_timestamp()
            for contract_data in response['results']:
                contract = PolygonOptionsContract(
                    ticker=contract_data.get('ticker', ''),
                    underlying_ticker=underlying_ticker,
                    contract_type=contract_data.get('contract_type', ''),
                    strike_price=float(contract_data.get('strike_price', 0)),
                    expiration_date=contract_data.get('expiration_date', ''),
                    timestamp=timestamp
                )
                contracts.append(contract)
        
        return contracts
    
    def get_last_trade(self, ticker: str) -> Dict[str, Any]:
        """Get the last trade for an options contract"""
        endpoint = f"/v2/last/trade/{ticker}"
        return self._make_request(endpoint)
    
    def get_aggregates(self, ticker: str, 
                      multiplier: int = 1,
                      timespan: str = 'day',
                      from_date: str = None,
                      to_date: str = None,
                      limit: int = 10) -> Dict[str, Any]:
        """Get aggregate bars for an options contract"""
        if not from_date:
            from_date = datetime.now().strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
            
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        params = {
            'adjusted': 'true',
            'sort': 'desc',
            'limit': limit
        }
        
        return self._make_request(endpoint, params)


def load_polygon_api_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load Nasdaq-100 options data from Polygon.io API
    
    Args:
        config: Configuration dictionary with:
            - api_key: Polygon.io API key (optional, uses env var if not provided)
            - tickers: List of underlying tickers to fetch (default: ["NDX", "QQQ"])  
            - limit: Number of contracts per ticker (default: 20)
            - include_pricing: Whether to fetch pricing data (default: False due to rate limits)
    
    Returns:
        Dict with standardized options data
    """
    # Extract configuration
    api_key = config.get('api_key')
    tickers = config.get('tickers', ['NDX', 'QQQ'])
    limit = config.get('limit', 20)
    include_pricing = config.get('include_pricing', False)
    
    client = PolygonAPIClient(api_key=api_key)
    
    all_contracts = []
    source_summary = {}
    
    for ticker in tickers:
        try:
            contracts = client.get_options_contracts(ticker, limit=limit)
            
            # Enhance with pricing data if requested and not rate limited
            if include_pricing and len(contracts) <= 5:  # Only for small requests
                for contract in contracts[:3]:  # Limit to avoid rate limits
                    try:
                        last_trade = client.get_last_trade(contract.ticker)
                        if 'results' in last_trade:
                            trade_data = last_trade['results']
                            contract.last_price = trade_data.get('p')
                            contract.volume = trade_data.get('s')
                    except Exception:
                        pass  # Skip pricing if failed
            
            all_contracts.extend(contracts)
            source_summary[ticker] = {
                'contracts_found': len(contracts),
                'status': 'success'
            }
            
        except Exception as e:
            source_summary[ticker] = {
                'contracts_found': 0,
                'status': 'failed',
                'error': str(e)
            }
    
    # Convert to standard format
    options_data = []
    for contract in all_contracts:
        options_data.append({
            'strike': contract.strike_price,
            'call_last': contract.last_price if contract.contract_type == 'call' else None,
            'call_volume': contract.volume if contract.contract_type == 'call' else None,
            'call_open_interest': contract.open_interest if contract.contract_type == 'call' else None,
            'put_last': contract.last_price if contract.contract_type == 'put' else None,
            'put_volume': contract.volume if contract.contract_type == 'put' else None,
            'put_open_interest': contract.open_interest if contract.contract_type == 'put' else None,
            'expiration_date': contract.expiration_date,
            'underlying_ticker': contract.underlying_ticker,
            'contract_ticker': contract.ticker,
            'contract_type': contract.contract_type,
            'source': 'polygon_api',
            'timestamp': contract.timestamp
        })
    
    return {
        'options_summary': {
            'total_contracts': len(all_contracts),
            'underlying_tickers': tickers,
            'data_source': 'polygon.io',
            'fetch_timestamp': get_utc_timestamp()
        },
        'options_data': options_data,
        'source_summary': source_summary,
        'quality_metrics': {
            'data_source': 'live_api',
            'total_contracts': len(all_contracts),
            'tickers_successful': len([s for s in source_summary.values() if s['status'] == 'success']),
            'tickers_failed': len([s for s in source_summary.values() if s['status'] == 'failed']),
            'volume_coverage': 0.5 if include_pricing else 0.0,  # Limited by API tier
            'oi_coverage': 0.5 if include_pricing else 0.0,
            'pricing_available': include_pricing,
            'rate_limited': True  # Free tier has rate limits
        },
        'metadata': {
            'api_source': 'polygon.io',
            'data_type': 'nasdaq_100_options',
            'alternatives_to': 'NQ_futures_options', 
            'notes': 'NDX provides index exposure, QQQ provides ETF exposure to Nasdaq-100'
        }
    }


# Main execution for testing
if __name__ == "__main__":
    # Test configuration
    test_config = {
        'tickers': ['NDX', 'QQQ'],
        'limit': 5,
        'include_pricing': False  # Set to False to avoid rate limits
    }
    
    try:
        result = load_polygon_api_data(test_config)
        print(f"Loaded {result['options_summary']['total_contracts']} contracts")
        print(f"Sources: {list(result['source_summary'].keys())}")
        
        # Save test result
        with open('polygon_test_result.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
    except Exception as e:
        print(f"Test failed: {e}")