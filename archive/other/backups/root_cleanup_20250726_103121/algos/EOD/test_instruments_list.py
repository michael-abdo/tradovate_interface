#!/usr/bin/env python3
"""
Test the client.instruments.list() approach for NQ options
Based on the exact pattern provided
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Test instruments.list() for options"""
    print("🔍 TESTING client.instruments.list() FOR NQ OPTIONS")
    print("="*60)
    print("Testing the exact pattern provided:")
    print("client.instruments.list(dataset='GLBX.MDP3', stype_in='parent', symbols='Q?.OPT')")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Test 1: Exact pattern provided
    print("\n📋 TEST 1: Exact Pattern from Example")
    print("-" * 40)
    
    try:
        print("🔍 Testing: symbols='Q?.OPT', stype_in='parent'")
        
        instruments = client.instruments.list(
            dataset="GLBX.MDP3",
            stype_in="parent",
            symbols="Q?.OPT",
            start="2025-07-15"
        )
        
        print(f"✅ Method executed successfully!")
        print(f"📊 Type of result: {type(instruments)}")
        
        if hasattr(instruments, '__len__'):
            print(f"📊 Number of results: {len(instruments)}")
        
        if hasattr(instruments, 'to_df'):
            df = instruments.to_df()
            print(f"📊 DataFrame shape: {df.shape}")
            
            if len(df) > 0:
                print(f"🎯 FOUND OPTIONS DATA!")
                print(f"📋 Columns: {list(df.columns)}")
                print(f"📋 Sample symbols: {list(df['symbol'].unique()[:10])}")
                
                # Look for Q3C specifically
                q3c_matches = df[df['symbol'].str.contains('Q3C', na=False)]
                if len(q3c_matches) > 0:
                    print(f"🎯 FOUND Q3C MATCHES: {len(q3c_matches)}")
                    print(q3c_matches[['symbol', 'expiration']].head())
                
                return df
            else:
                print("❌ No data in DataFrame")
        else:
            print(f"📊 Raw result: {instruments}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Variations of the pattern
    print("\n📋 TEST 2: Pattern Variations")
    print("-" * 40)
    
    patterns_to_test = [
        ("Q?.OPT", "parent", "Q wildcard with OPT"),
        ("Q*", "parent", "Q wildcard without OPT"),
        ("Q?.OPT", None, "Q wildcard, no stype_in"),
        ("NQ", "parent", "NQ parent symbol"),
        ("NQ*", "parent", "NQ wildcard"),
        ("Q1A,Q2A,Q3A,Q1C,Q2C,Q3C", "parent", "Explicit weekly symbols"),
        ("Q3C", "parent", "Direct Q3C"),
    ]
    
    for pattern, stype, description in patterns_to_test:
        print(f"\n🔍 Testing: {description}")
        print(f"   Pattern: {pattern}")
        print(f"   stype_in: {stype}")
        
        try:
            kwargs = {
                "dataset": "GLBX.MDP3",
                "symbols": pattern,
                "start": "2025-07-15"
            }
            
            if stype:
                kwargs["stype_in"] = stype
            
            instruments = client.instruments.list(**kwargs)
            
            if hasattr(instruments, 'to_df'):
                df = instruments.to_df()
                if len(df) > 0:
                    print(f"   ✅ Found {len(df)} instruments!")
                    
                    # Check security types
                    if 'security_type' in df.columns:
                        stypes = df['security_type'].unique()
                        print(f"   📊 Security types: {list(stypes)}")
                    
                    # Check for options
                    if 'symbol' in df.columns:
                        sample_symbols = df['symbol'].unique()[:5]
                        print(f"   📋 Sample symbols: {list(sample_symbols)}")
                        
                        # Look for option indicators
                        option_indicators = df['symbol'].str.contains('C|P', na=False).sum()
                        if option_indicators > 0:
                            print(f"   🎯 Potential options: {option_indicators}")
                else:
                    print("   ❌ No instruments found")
            
        except Exception as e:
            print(f"   ⚠️  Error: {str(e)[:60]}...")
    
    # Test 3: Check what IS available
    print("\n📋 TEST 3: What IS Available in instruments.list()")
    print("-" * 40)
    
    try:
        print("🔍 Getting all NQ-related instruments...")
        
        # Try to get any NQ instruments
        instruments = client.instruments.list(
            dataset="GLBX.MDP3",
            symbols="NQ*",
            start="2025-07-15"
        )
        
        if hasattr(instruments, 'to_df'):
            df = instruments.to_df()
            print(f"📊 Found {len(df)} NQ-related instruments")
            
            if len(df) > 0:
                print("📋 Available columns:")
                for col in df.columns:
                    print(f"   • {col}")
                
                # Analyze what we have
                if 'security_type' in df.columns:
                    stypes = df['security_type'].value_counts()
                    print(f"\n📊 Security types breakdown:")
                    for stype, count in stypes.items():
                        print(f"   • {stype}: {count}")
                
                # Show sample data
                print(f"\n📋 Sample instruments:")
                sample_df = df[['symbol', 'security_type', 'expiration']].head(10) if len(df) > 0 else df
                print(sample_df.to_string())
    
    except Exception as e:
        print(f"❌ Error getting available instruments: {e}")
    
    print(f"\n🎯 instruments.list() testing complete!")

if __name__ == "__main__":
    main()