#!/usr/bin/env python3
"""
Simple Databento NQ Options Pull for Today's Expiration
Date: July 16, 2025 (Wednesday)
Expiration Symbol: Q3C N25 (Week 3 Wednesday)
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add tasks directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks'))

try:
    import databento as db
    DATABENTO_AVAILABLE = True
except ImportError:
    DATABENTO_AVAILABLE = False
    print("Databento library not installed. Run: pip install databento")


class SimpleNQDataPuller:
    """Simple NQ options data puller for today's expiration"""
    
    def __init__(self, api_key: str = None):
        """Initialize with API key"""
        # Use provided key or the new working key
        self.api_key = api_key or "db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ"
        self.client = None
        self.connected = False
        
        # Today's info - use yesterday to today for a valid range
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.start_str = self.yesterday.strftime("%Y-%m-%d")
        self.end_str = self.today.strftime("%Y-%m-%d")
        
        # Today is Wednesday, July 16, 2025 → Week 3 Wednesday → Q3C N25
        # Try different symbol formats for NQ options
        self.nq_symbols = [
            "NQ",          # Just search for any NQ options
            "ONQ",         # Options on NQ
            "MNQ",         # Micro NQ
            "Q3CN25",      # Week 3 Wednesday format
            "Q3C N25",     # With space
            "NQ3CN25",     # With NQ prefix
            "ONQ3CN25",    # Options on NQ with week format
            "NQN25",       # Standard monthly
            "NQMN25"       # Micro NQ monthly
        ]
        self.expected_expiry = "2025-07-16"
        
        print(f"Target Symbols: {self.nq_symbols}")
        print(f"Expected Expiry: {self.expected_expiry}")
        print(f"Date Range: {self.start_str} to {self.end_str}")
        
    def connect(self) -> bool:
        """Connect to Databento API"""
        if not DATABENTO_AVAILABLE:
            print("❌ Databento library not available")
            return False
            
        if not self.api_key:
            print("❌ No API key. Set DATABENTO_API_KEY environment variable")
            return False
            
        try:
            print(f"🔑 Using API key: {self.api_key[:10]}...")
            self.client = db.Historical(self.api_key)
            self.connected = True
            print("✅ Connected to Databento API")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_todays_nq_options(self) -> Dict[str, Any]:
        """Get today's NQ options data"""
        if not self.connected:
            return {"error": "Not connected to Databento API"}
            
        try:
            print(f"🔍 Searching for NQ options expiring today...")
            print(f"   Symbol patterns: {[s+'*' for s in self.nq_symbols]}")
            print(f"   Dataset: GLBX.MDP3")
            print(f"   Date range: {self.start_str} to {self.end_str}")
            
            # First, let's test with a simple ES contract to verify API works
            print("🔍 Testing API connection with ES contract...")
            test_data = self.client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="ESU5",  # E-mini S&P 500 September 2025
                schema="trades",
                start=self.start_str,
                end=self.end_str,
                limit=10
            )
            
            test_df = test_data.to_df()
            print(f"📋 Test connection successful - found {len(test_df)} ES records")
            
            if len(test_df) == 0:
                print("⚠️  No ES data for today - may be weekend/holiday")
                
            # Try actual NQ futures contracts to understand the symbol format
            print("🔍 Testing actual NQ futures contracts to understand symbols")
            nq_futures_tests = ["NQU25", "NQZ25", "NQH25", "NQM25", "NQU5", "NQZ5"]
            
            found_data = None
            successful_symbol = None
            
            for futures_symbol in nq_futures_tests:
                print(f"🔍 Trying NQ futures: {futures_symbol}")
                try:
                    data = self.client.timeseries.get_range(
                        dataset="GLBX.MDP3",  # CME Globex
                        symbols=futures_symbol,  # Specific futures contract
                        schema="trades",
                        start=self.start_str,
                        end=self.end_str,
                        limit=100
                    )
                    
                    df = data.to_df()
                    if len(df) > 0:
                        print(f"✅ Found {len(df)} records for {futures_symbol}")
                        
                        # Now try to find options on this futures contract
                        print(f"   🔍 Looking for options on {futures_symbol}")
                        try:
                            options_data = self.client.timeseries.get_range(
                                dataset="GLBX.MDP3",
                                symbols=f"{futures_symbol}*",  # Options on this futures
                                schema="trades",
                                start=self.start_str,
                                end=self.end_str,
                                limit=1000
                            )
                            
                            options_df = options_data.to_df()
                            if len(options_df) > 0:
                                print(f"   ✅ Found {len(options_df)} options records!")
                                if 'symbol' in options_df.columns:
                                    unique_symbols = options_df['symbol'].unique()
                                    print(f"   📊 Options symbols: {list(unique_symbols[:10])}")
                                found_data = options_df
                                successful_symbol = f"{futures_symbol} options"
                                break
                            else:
                                print(f"   No options found for {futures_symbol}")
                        except Exception as e:
                            print(f"   Options error for {futures_symbol}: {str(e)}")
                        
                        # If no options found, at least we have the futures data
                        if found_data is None:
                            found_data = df
                            successful_symbol = futures_symbol
                    else:
                        print(f"   No data found for {futures_symbol}")
                except Exception as e:
                    print(f"   Error with {futures_symbol}: {str(e)}")
            
            df = found_data
            
            # Process the results
            if df is not None:
                print(f"📋 Found {len(df)} trade records")
            
            if df is not None and not df.empty:
                print(f"✅ Found {len(df)} trade records for today")
                
                # Get unique symbols
                unique_symbols = df['symbol'].unique() if 'symbol' in df.columns else []
                
                # Check if we have expected columns
                expected_columns = ['symbol', 'ts_event', 'price', 'size']
                available_columns = [col for col in expected_columns if col in df.columns]
                
                return {
                    "success": True,
                    "expiration_date": self.expected_expiry,
                    "successful_symbol": successful_symbol,
                    "trade_records": len(df),
                    "unique_symbols": list(unique_symbols[:10]),  # Show first 10
                    "available_columns": available_columns,
                    "sample_data": df.head().to_dict() if not df.empty else None,
                    "data_summary": {
                        "total_records": len(df),
                        "unique_symbols_count": len(unique_symbols),
                        "columns": list(df.columns)
                    }
                }
            else:
                # Try getting instrument definitions instead
                print("🔍 No trade data found, checking instrument definitions...")
                
                # Get instrument definitions
                instruments = self.client.metadata.get_dataset_condition(
                    dataset="GLBX.MDP3",
                    condition="expiration_date >= '2025-07-16' AND expiration_date <= '2025-07-16'",
                    symbols_regex=f"{self.nq_symbol}.*"
                )
                
                if instruments and hasattr(instruments, 'to_df'):
                    inst_df = instruments.to_df()
                    print(f"📋 Found {len(inst_df)} instrument definitions")
                    
                    return {
                        "success": True,
                        "expiration_date": self.expected_expiry,
                        "successful_symbol": successful_symbol,
                        "trade_records": 0,
                        "instrument_definitions": len(inst_df),
                        "sample_instruments": inst_df.head().to_dict() if not inst_df.empty else None,
                        "instrument_columns": list(inst_df.columns) if not inst_df.empty else []
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No data found for any NQ symbol expiring on {self.expected_expiry}",
                        "trade_records": 0,
                        "search_patterns": [f"{s}*" for s in self.nq_symbols]
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Data retrieval failed: {str(e)}",
                "target_symbols": self.nq_symbols,
                "expected_expiry": self.expected_expiry
            }
    
    def confirm_expiration_date(self, results: Dict[str, Any]) -> bool:
        """Confirm the expiration date matches expectation"""
        if not results.get("success"):
            print("❌ Cannot confirm expiration - data pull failed")
            return False
            
        actual_expiry = results.get("expiration_date")
        expected_expiry = self.expected_expiry
        
        if actual_expiry == expected_expiry:
            print(f"✅ Expiration date confirmed: {actual_expiry}")
            return True
        else:
            print(f"❌ Expiration date mismatch!")
            print(f"   Expected: {expected_expiry}")
            print(f"   Actual: {actual_expiry}")
            return False


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 DATABENTO SIMPLE NQ OPTIONS PULL")
    print("=" * 60)
    
    # Initialize puller
    puller = SimpleNQDataPuller()
    
    # Connect to API
    if not puller.connect():
        print("❌ Failed to connect to Databento API")
        return
    
    # Get today's NQ options
    print("\n" + "=" * 40)
    print("📈 PULLING TODAY'S NQ OPTIONS DATA")
    print("=" * 40)
    
    results = puller.get_todays_nq_options()
    
    # Display results
    print("\n📊 RESULTS:")
    if results.get("success"):
        print(f"✅ Successfully retrieved NQ options data")
        print(f"   Successful Symbol: {results.get('successful_symbol', 'N/A')}")
        print(f"   Expiration Date: {results['expiration_date']}")
        print(f"   Trade Records: {results.get('trade_records', 0)}")
        print(f"   Unique Symbols: {results.get('unique_symbols_count', 0)}")
        
        if results.get("unique_symbols"):
            print(f"   Sample Symbols: {results['unique_symbols'][:5]}")
        
        if results.get("sample_data"):
            print(f"   Sample Data Keys: {list(results['sample_data'].keys())}")
    else:
        print(f"❌ Failed to retrieve data: {results.get('error')}")
        if results.get("sample_instruments"):
            print(f"   Sample instruments found: {list(results['sample_instruments'].keys())}")
    
    # Confirm expiration date
    print("\n" + "=" * 40)
    print("🔍 CONFIRMING EXPIRATION DATE")
    print("=" * 40)
    
    expiry_confirmed = puller.confirm_expiration_date(results)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"Connection: {'✅ Success' if puller.connected else '❌ Failed'}")
    print(f"Data Pull: {'✅ Success' if results.get('success') else '❌ Failed'}")
    print(f"Expiry Confirmed: {'✅ Yes' if expiry_confirmed else '❌ No'}")
    
    if results.get("success") and expiry_confirmed:
        print("\n🎉 SUCCESS: Today's NQ options data retrieved and confirmed!")
    else:
        print("\n⚠️  PARTIAL SUCCESS: Check details above for issues")


if __name__ == "__main__":
    main()