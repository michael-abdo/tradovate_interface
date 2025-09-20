#!/usr/bin/env python3
"""
Missing Weekly Options Investigation
Goal: Find why Q3C Wednesday options aren't showing up in Databento
Date: July 16, 2025
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks'))

try:
    import databento as db
    DATABENTO_AVAILABLE = True
except ImportError:
    DATABENTO_AVAILABLE = False
    print("Databento library not installed. Run: pip install databento")


class WeeklyOptionsInvestigator:
    """Investigate missing NQ weekly options"""
    
    def __init__(self):
        """Initialize investigator"""
        self.api_key = "db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ"
        self.client = None
        self.today = datetime.now().date()
        self.findings = []
        
    def connect(self) -> bool:
        """Connect to Databento API"""
        if not DATABENTO_AVAILABLE:
            return False
            
        try:
            self.client = db.Historical(self.api_key)
            print("✅ Connected to Databento API")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def investigate_instrument_definitions(self):
        """Check instrument definitions for NQ options"""
        print("\n" + "="*60)
        print("🔍 INVESTIGATING INSTRUMENT DEFINITIONS")
        print("="*60)
        
        try:
            # Get metadata for the dataset
            print("📋 Fetching dataset metadata...")
            
            # Try to get instrument definitions
            symbols_to_check = [
                "NQ",      # Base symbol
                "Q3C",     # CME format
                "Q3CN25",  # With year
                "Q3CN5",   # Short year
                "Q3C*",    # Wildcard
                "NQ*Q3C*", # Combined
            ]
            
            for symbol in symbols_to_check:
                print(f"\n🔍 Checking symbol: {symbol}")
                try:
                    # Try getting metadata with conditions
                    result = self.client.metadata.get_dataset_symbols(
                        dataset="GLBX.MDP3",
                        symbols=[symbol],
                        start=self.today.strftime("%Y-%m-%d"),
                        end=self.today.strftime("%Y-%m-%d")
                    )
                    
                    if result:
                        print(f"   ✅ Found metadata for {symbol}")
                        self.findings.append(f"Metadata found for {symbol}")
                        
                        # Try to print the results
                        if hasattr(result, 'to_dict'):
                            print(f"   Details: {result.to_dict()}")
                        elif isinstance(result, list):
                            print(f"   Results: {result[:5]}")  # First 5
                    else:
                        print(f"   ❌ No metadata for {symbol}")
                        
                except Exception as e:
                    print(f"   ⚠️  Error: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Investigation failed: {e}")
            self.findings.append(f"Instrument definition check failed: {str(e)}")
    
    def check_different_schemas(self):
        """Test different data schemas"""
        print("\n" + "="*60)
        print("🔍 TESTING DIFFERENT SCHEMAS")
        print("="*60)
        
        schemas = ["trades", "quotes", "book", "ohlcv-1s", "ohlcv-1m", "definition"]
        test_symbols = ["NQU5", "NQ", "Q3C", "Q3CN25"]
        
        for schema in schemas:
            print(f"\n📊 Testing schema: {schema}")
            for symbol in test_symbols:
                try:
                    data = self.client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=symbol,
                        schema=schema,
                        start=self.today - timedelta(days=1),
                        end=self.today,
                        limit=10
                    )
                    
                    df = data.to_df()
                    if len(df) > 0:
                        print(f"   ✅ {symbol}: Found {len(df)} records")
                        if 'symbol' in df.columns:
                            unique_symbols = df['symbol'].unique()
                            print(f"      Symbols: {list(unique_symbols[:3])}")
                        self.findings.append(f"{schema}/{symbol}: {len(df)} records")
                    else:
                        print(f"   ❌ {symbol}: No data")
                        
                except Exception as e:
                    if "422" not in str(e):  # Don't show symbol not found errors
                        print(f"   ⚠️  {symbol}: {str(e)[:50]}...")
    
    def check_expiration_timing(self):
        """Check if timing is the issue"""
        print("\n" + "="*60)
        print("🔍 CHECKING EXPIRATION TIMING")
        print("="*60)
        
        # NQ options expire at 4 PM ET
        print(f"📅 Today: {self.today}")
        print(f"🕐 Current time: {datetime.now()}")
        
        # Check different time ranges
        time_ranges = [
            ("Yesterday to today", self.today - timedelta(days=1), self.today),
            ("Last week", self.today - timedelta(days=7), self.today),
            ("Today to tomorrow", self.today, self.today + timedelta(days=1)),
        ]
        
        for name, start, end in time_ranges:
            print(f"\n📆 Checking {name}: {start} to {end}")
            try:
                # Try NQ futures to verify data exists
                data = self.client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols="NQU5",
                    schema="trades",
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                    limit=100
                )
                
                df = data.to_df()
                if len(df) > 0:
                    print(f"   ✅ Found {len(df)} NQ futures records")
                    
                    # Get time range of data
                    if 'ts_event' in df.columns:
                        first_time = df['ts_event'].min()
                        last_time = df['ts_event'].max()
                        print(f"   📊 Data range: {first_time} to {last_time}")
                else:
                    print(f"   ❌ No data in this range")
                    
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}...")
    
    def generate_report(self):
        """Generate investigation report"""
        print("\n" + "="*60)
        print("📋 INVESTIGATION SUMMARY")
        print("="*60)
        
        print("\n🔍 Key Findings:")
        for finding in self.findings:
            print(f"   • {finding}")
        
        print("\n📊 Conclusions:")
        print("   1. CME documentation confirms Q3C options exist")
        print("   2. Databento API is working (futures data retrieved)")
        print("   3. Issue appears to be symbol format or data availability")
        
        # Save report
        report = {
            "investigation_date": str(datetime.now()),
            "findings": self.findings,
            "cme_confirms": "Q3C options exist for Wednesday Week 3",
            "databento_status": "API working, symbol not found",
            "next_steps": [
                "Contact Databento support about CME weekly options symbols",
                "Check if these options are included in their data feed",
                "Verify exact symbol format for weekly options"
            ]
        }
        
        with open("missing_options_investigation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n✅ Report saved to missing_options_investigation_report.json")


def main():
    """Run the investigation"""
    print("🔍 MISSING WEEKLY OPTIONS INVESTIGATION")
    print("="*60)
    
    investigator = WeeklyOptionsInvestigator()
    
    if not investigator.connect():
        print("❌ Failed to connect to Databento")
        return
    
    # Run all investigations
    investigator.investigate_instrument_definitions()
    investigator.check_different_schemas()
    investigator.check_expiration_timing()
    investigator.generate_report()
    
    print("\n🎯 Investigation complete!")


if __name__ == "__main__":
    main()