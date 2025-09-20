#!/usr/bin/env python3
"""
Barchart API Client - Direct API calls using reverse-engineered endpoints
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from urllib.parse import urlencode

# Add tasks directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from common_utils import save_json, get_logger, get_utc_timestamp, PathManager

class BarchartAPIClient:
    """Direct API client for Barchart options data"""
    
    def __init__(self):
        self.base_url = "https://www.barchart.com/proxies/core-api/v1"
        self.session = requests.Session()
        self.logger = get_logger()
        
        # Default headers based on browser requests
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Sec-Ch-Ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    def set_cookies(self, cookies: Dict[str, str]):
        """
        Set cookies for authentication
        
        Args:
            cookies: Dictionary of cookie name/value pairs
        """
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
    
    def set_cookies_from_string(self, cookie_string: str):
        """
        Set cookies from a cookie string (from browser)
        
        Args:
            cookie_string: Cookie string from browser (name=value; name2=value2)
        """
        cookies = {}
        for cookie in cookie_string.split('; '):
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                cookies[name] = value
        self.set_cookies(cookies)
    
    def get_options_data(self, symbol: str, referer_futures: str = "NQM25") -> Dict[str, Any]:
        """
        Fetch options data for a specific symbol
        
        Args:
            symbol: Options symbol (e.g., "MC7M25", "MC1M25")
            referer_futures: Underlying futures symbol for referer URL
            
        Returns:
            JSON response with options data
        """
        # Build query parameters
        params = {
            'symbol': symbol,
            'list': 'futures.options',
            'fields': 'strike,openPrice,highPrice,lowPrice,lastPrice,priceChange,bidPrice,askPrice,volume,openInterest,premium,tradeTime,longSymbol,optionType,symbol,symbolCode,symbolType',
            'meta': 'field.shortName,field.description,field.type,lists.lastUpdate',
            'groupBy': 'optionType',
            'orderBy': 'strike',
            'orderDir': 'asc',
            'raw': '1'
        }
        
        # Log the full URL for debugging
        from urllib.parse import urlencode
        full_url = f"{self.base_url}/quotes/get?{urlencode(params)}"
        self.logger.debug(f"Full API URL: {full_url}")
        
        # Set referer header
        referer = f"https://www.barchart.com/futures/quotes/{referer_futures}/options/{symbol}?futuresOptionsView=merged"
        headers = self.headers.copy()
        headers['Referer'] = referer
        
        # Add XSRF token if available in cookies
        xsrf_token = None
        for cookie in self.session.cookies:
            if cookie.name == 'XSRF-TOKEN':
                xsrf_token = cookie.value
                break
        
        if xsrf_token:
            # URL decode the token
            import urllib.parse
            headers['X-XSRF-TOKEN'] = urllib.parse.unquote(xsrf_token)
            self.logger.debug("Added X-XSRF-TOKEN header")
        
        # Make the request
        url = f"{self.base_url}/quotes/get"
        
        self.logger.info(f"Fetching options data for {symbol}")
        self.logger.debug(f"URL: {url}")
        self.logger.debug(f"Params: {params}")
        
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"Successfully fetched {data.get('count', 0)} contracts")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching options data: {e}")
            raise
    
    def save_api_response(self, data: Dict[str, Any], symbol: str, output_dir: str = None) -> str:
        """
        Save API response to file with metadata
        
        Args:
            data: API response data
            symbol: Options symbol
            output_dir: Directory to save files
            
        Returns:
            Path to saved file
        """
        import os
        
        # Create organized directory structure
        if output_dir is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_dir = f"outputs/{date_str}/api_data"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f'barchart_api_{symbol}_{timestamp}.json'
        filepath = os.path.join(output_dir, filename)
        
        # Save data
        with open(filepath, 'w') as f:
            save_json(data, f).result
        
        # Save metadata
        metadata = {
            'symbol': symbol,
            'timestamp': get_utc_timestamp(),
            'api_endpoint': 'proxies/core-api/v1/quotes/get',
            'contracts_count': data.get('count', 0),
            'total_contracts': data.get('total', 0),
            'file_path': filepath
        }
        
        metadata_file = filepath.replace('.json', '_metadata.json')
        with open(metadata_file, 'w') as f:
            save_json(metadata, f).result
        
        self.logger.info(f"API response saved: {filepath}")
        
        return filepath


def main():
    """Test the API client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch Barchart options data')
    parser.add_argument('symbol', help='Options symbol (e.g., MC7M25)')
    parser.add_argument('--futures', default='NQM25', help='Underlying futures symbol')
    parser.add_argument('--save', action='store_true', help='Save response to file')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create client and fetch data
    client = BarchartAPIClient()
    
    try:
        data = client.get_options_data(args.symbol, args.futures)
        
        print(f"\nOptions Data for {args.symbol}:")
        print(f"Total contracts: {data.get('total', 0)}")
        print(f"Count returned: {data.get('count', 0)}")
        
        # Show sample data
        if 'data' in data and 'Call' in data['data'] and data['data']['Call']:
            first_call = data['data']['Call'][0]
            print(f"\nSample Call Option:")
            print(f"  Strike: {first_call.get('strike')}")
            print(f"  Last Price: {first_call.get('lastPrice')}")
            print(f"  Symbol: {first_call.get('symbol')}")
        
        if args.save:
            filepath = client.save_api_response(data, args.symbol)
            print(f"\nData saved to: {filepath}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())