#!/usr/bin/env python3
"""
TASK: tradovate_api_data
TYPE: Leaf Task
PURPOSE: Fetch options data from Tradovate API (or simulate for demo)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib


class TradovateAPIDataLoader:
    """Load options data from Tradovate API or simulate"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with configuration
        
        Args:
            config: Dict containing:
                - mode: "demo" or "live" 
                - cid: Client ID
                - secret: Client secret
                - use_mock: Whether to use mock data for testing
        """
        self.config = config
        self.mode = config.get("mode", "demo")
        self.cid = config.get("cid", "6540")
        self.secret = config.get("secret", "f7a2b8f5-8348-424f-8ffa-047ab7502b7c")
        self.use_mock = config.get("use_mock", True)  # Default to mock for safety
        self.data = None
        self.metadata = {}
        
    def validate_credentials(self) -> bool:
        """Validate API credentials are present"""
        return bool(self.cid and self.secret)
    
    def connect_api(self) -> bool:
        """
        Test API connection (or mock connection)
        
        Returns:
            bool: True if connection successful
        """
        if self.use_mock:
            # Simulate successful connection
            self.metadata["connection_status"] = "mock_connected"
            return True
        else:
            # In real implementation, would test actual API connection
            # For now, simulate based on credentials
            if self.validate_credentials():
                self.metadata["connection_status"] = "credentials_valid"
                return True
            return False
    
    def load_data(self) -> Dict[str, Any]:
        """
        Load options data from Tradovate API or mock
        
        Returns:
            Dict containing options data
        """
        if not self.connect_api():
            raise ConnectionError("Failed to connect to Tradovate API")
        
        if self.use_mock:
            # Generate realistic mock data
            self.data = self._generate_mock_data()
        else:
            # In real implementation, would fetch from API
            # For now, return empty structure
            self.data = {
                "status": "api_not_implemented",
                "message": "Real API integration pending",
                "mock_available": True
            }
        
        # Add metadata
        self.metadata.update({
            "source": "tradovate_api",
            "mode": self.mode,
            "use_mock": self.use_mock,
            "loaded_at": get_utc_timestamp(),
            "data_hash": self._calculate_data_hash()
        })
        
        return self.data
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock options data"""
        # NQ current price around 21,376
        current_price = 21376.75
        
        # Generate strikes around current price
        strikes = []
        for i in range(-10, 11):  # -$1000 to +$1000 in $100 increments
            strike = current_price + (i * 100)
            strikes.append(strike)
        
        # Generate mock options
        calls = []
        puts = []
        
        for strike in strikes:
            # Calculate realistic values based on moneyness
            moneyness = strike / current_price
            
            # Calls
            call_volume = max(10, int(500 * (1.5 - abs(moneyness - 1))))
            call_oi = call_volume * 5
            call_price = max(5, current_price - strike + 50) if strike < current_price else max(5, 50 - (strike - current_price) * 0.5)
            
            calls.append({
                "symbol": f"NQ{int(strike)}C",
                "strike": strike,
                "expiration": "2025-06-30",
                "volume": call_volume,
                "openInterest": call_oi,
                "lastPrice": call_price,
                "bid": call_price - 2,
                "ask": call_price + 2
            })
            
            # Puts
            put_volume = max(10, int(500 * (1.5 - abs(moneyness - 1))))
            put_oi = put_volume * 4
            put_price = max(5, strike - current_price + 50) if strike > current_price else max(5, 50 - (current_price - strike) * 0.5)
            
            puts.append({
                "symbol": f"NQ{int(strike)}P",
                "strike": strike,
                "expiration": "2025-06-30", 
                "volume": put_volume,
                "openInterest": put_oi,
                "lastPrice": put_price,
                "bid": put_price - 2,
                "ask": put_price + 2
            })
        
        return {
            "underlying": {
                "symbol": "NQ",
                "price": current_price,
                "timestamp": get_utc_timestamp()
            },
            "options": {
                "calls": calls,
                "puts": puts,
                "total": len(calls) + len(puts)
            },
            "metadata": {
                "source": "mock_generator",
                "version": "1.0"
            }
        }
    
    def get_options_data(self) -> Dict[str, List[Dict]]:
        """
        Extract options data in standard format
        
        Returns:
            Dict with 'calls' and 'puts' lists
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if self.use_mock:
            return {
                "calls": self.data["options"]["calls"],
                "puts": self.data["options"]["puts"],
                "total_contracts": self.data["options"]["total"]
            }
        else:
            # Handle real API format when implemented
            return {
                "calls": [],
                "puts": [],
                "total_contracts": 0
            }
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        options = self.get_options_data()
        calls = options['calls']
        puts = options['puts']
        
        # All mock data has volume/OI by design
        total = len(calls) + len(puts)
        
        return {
            "total_contracts": total,
            "calls_count": len(calls),
            "puts_count": len(puts),
            "volume_coverage": 1.0 if self.use_mock else 0.0,  # 100% for mock
            "oi_coverage": 1.0 if self.use_mock else 0.0,      # 100% for mock
            "price_coverage": 1.0 if self.use_mock else 0.0,   # 100% for mock
            "data_source": "mock" if self.use_mock else "api"
        }
    
    def get_strike_range(self) -> Optional[Dict[str, float]]:
        """Get min and max strikes from the data"""
        options = self.get_options_data()
        all_strikes = []
        
        for contract in options['calls'] + options['puts']:
            strike = contract.get('strike')
            if strike:
                all_strikes.append(float(strike))
        
        if all_strikes:
            return {
                "min": min(all_strikes),
                "max": max(all_strikes),
                "count": len(set(all_strikes))
            }
        return None
    
    def _calculate_data_hash(self) -> str:
        """Calculate hash of loaded data for verification"""
        if self.data:
            data_str = json.dumps(self.data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
        return "no_data"


# Module-level function for easy access
def load_tradovate_api_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load Tradovate API data and return summary
    
    Args:
        config: Configuration dict
        
    Returns:
        Dict with data and quality metrics
    """
    loader = TradovateAPIDataLoader(config)
    
    # Load the data
    raw_data = loader.load_data()
    
    # Get processed data
    options_data = loader.get_options_data()
    quality_metrics = loader.get_data_quality_metrics()
    strike_range = loader.get_strike_range()
    
    return {
        "loader": loader,
        "metadata": loader.metadata,
        "options_summary": options_data,
        "quality_metrics": quality_metrics,
        "strike_range": strike_range,
        "raw_data_available": True
    }