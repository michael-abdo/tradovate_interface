"""
Databento API Connection Module for Interactive Brokers Data

Simple connection test for Databento API to access IB market data.
Provides basic connectivity testing and historical data retrieval capabilities.
"""

import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import databento as db
    DATABENTO_AVAILABLE = True
except ImportError:
    DATABENTO_AVAILABLE = False
    print("Databento library not installed. Run: pip install databento")


class DatabentoAPIConnection:
    """Simple Databento API connection handler for IB data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Databento API connection.
        
        Args:
            api_key: Databento API key (or uses DATABENTO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('DATABENTO_API_KEY')
        self.client = None
        self.connected = False
        
    def connect_api(self) -> bool:
        """
        Connect to Databento API.
        
        Returns:
            bool: True if connection successful
        """
        if not DATABENTO_AVAILABLE:
            print("Databento library not available")
            return False
            
        if not self.api_key:
            print("No API key provided. Set DATABENTO_API_KEY environment variable or pass api_key parameter")
            return False
            
        try:
            # Create historical client
            self.client = db.Historical(self.api_key)
            self.connected = True
            print("Successfully connected to Databento API")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection and return status.
        
        Returns:
            dict: Connection test results
        """
        if not self.connected:
            return {
                "connected": False,
                "error": "Not connected to Databento API",
                "test_timestamp": time.time()
            }
            
        try:
            # Test with a simple data request (small sample)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            # Request minimal data to test connection
            data = self.client.timeseries.get_range(
                dataset="GLBX.MDP3",  # CME Globex
                symbols="ESH4",       # E-mini S&P 500 futures (sample)
                schema="trades",
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                limit=10  # Only get 10 records for testing
            )
            
            # Convert to dataframe to verify data structure
            df = data.to_df()
            
            return {
                "connected": True,
                "test_successful": True,
                "sample_data_count": len(df),
                "data_columns": list(df.columns) if not df.empty else [],
                "test_timestamp": time.time(),
                "dataset_tested": "GLBX.MDP3"
            }
            
        except Exception as e:
            return {
                "connected": True,
                "test_successful": False,
                "error": str(e),
                "test_timestamp": time.time()
            }
    
    def get_sample_options_data(self, symbol: str = "SPY", limit: int = 100) -> Dict[str, Any]:
        """
        Get sample options data for testing.
        
        Args:
            symbol: Options symbol to retrieve
            limit: Maximum number of records
            
        Returns:
            dict: Sample data results
        """
        if not self.connected:
            return {"error": "Not connected to Databento API"}
            
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            # Request options data
            data = self.client.timeseries.get_range(
                dataset="OPRA.PILLAR",  # Options data
                symbols=f"{symbol}*",   # Wildcard for options
                schema="trades",
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                limit=limit
            )
            
            df = data.to_df()
            
            return {
                "success": True,
                "symbol": symbol,
                "record_count": len(df),
                "data_preview": df.head().to_dict() if not df.empty else {},
                "columns": list(df.columns) if not df.empty else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def disconnect_api(self):
        """Disconnect from Databento API."""
        self.connected = False
        self.client = None
        print("Disconnected from Databento API")


def simple_connection_test(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform a simple connection test to Databento API.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
        
    Returns:
        dict: Test results with success status
    """
    print("Testing Databento API connection...")
    
    # Create connection instance
    api = DatabentoAPIConnection(api_key)
    
    # Attempt connection
    connection_success = api.connect_api()
    
    if connection_success:
        # Test the connection with sample data
        test_results = api.test_connection()
        
        # Clean disconnect
        api.disconnect_api()
        
        return {
            "success": True,
            "message": "Databento API connection test successful",
            "connection_details": test_results,
            "api_available": DATABENTO_AVAILABLE
        }
    else:
        return {
            "success": False,
            "message": "Databento API connection test failed",
            "connection_details": None,
            "api_available": DATABENTO_AVAILABLE
        }


if __name__ == "__main__":
    # Run simple connection test
    result = simple_connection_test()
    print(f"Test Result: {result}")
    
    if result["success"]:
        print("\nConnection test passed! Ready for market data integration.")
        print("Next steps:")
        print("1. Set up DATABENTO_API_KEY environment variable")
        print("2. Install databento: pip install databento") 
        print("3. Configure data feeds for options trading")
    else:
        print("\nConnection test failed. Check:")
        print("1. API key is valid and set")
        print("2. Databento library is installed")
        print("3. Network connectivity")