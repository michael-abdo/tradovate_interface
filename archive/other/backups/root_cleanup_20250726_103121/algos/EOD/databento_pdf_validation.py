#!/usr/bin/env python3
"""
Databento PDF Claims Validation
Test the specific claims made in the PDF document
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Validate PDF claims systematically"""
    print("🔍 VALIDATING DATABENTO PDF CLAIMS")
    print("="*60)
    print("PDF Claims:")
    print("1. Q3C options exist for Week-3 Wednesday expiry")
    print("2. Parent symbology works for option chains")
    print("3. All weekly options (Q1A, Q3C, etc.) are supported")
    print("4. Full tick-level options data available")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    findings = []
    
    # Test 1: Direct Q3C testing (PDF specific example)
    print("\n📋 TEST 1: Direct Q3C Symbol (PDF Example)")
    print("-" * 40)
    
    q3c_variations = [
        "Q3C",        # Exact PDF example
        "Q3CN25",     # With year
        "Q3C N25",    # With space and year
        "Q3C25",      # Different format
    ]
    
    for symbol in q3c_variations:
        print(f"🔍 Testing Q3C variation: {symbol}")
        try:
            # Try with extended date range (options might be historical)
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=symbol,
                schema="trades",
                start=today - timedelta(days=30),  # Extended range
                end=today + timedelta(days=30),    # Future dates
                limit=10
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ FOUND DATA for {symbol}!")
                findings.append(f"Q3C variation {symbol}: SUCCESS")
                
                # Get details
                if 'symbol' in df.columns:
                    symbols = df['symbol'].unique()
                    print(f"   📊 Actual symbols: {list(symbols)}")
                    
                print(f"   📈 Records: {len(df)}")
                print(f"   📅 Date range: {df['ts_event'].min()} to {df['ts_event'].max()}")
            else:
                print(f"   ❌ No data for {symbol}")
                
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Error: {str(e)[:60]}...")
    
    # Test 2: Parent symbology (PDF claims this works)
    print("\n📋 TEST 2: Parent Symbology for Options (PDF Claims)")
    print("-" * 40)
    
    parent_symbols = [
        "NQ.OPT",     # Standard parent format
        "NQ",         # Simple parent (PDF suggests this)
        "NQU5.OPT",   # Specific contract options
        "NQU5",       # Contract-specific parent
    ]
    
    for parent in parent_symbols:
        print(f"🔍 Testing parent symbol: {parent}")
        try:
            # Try to get instrument definitions first
            def_data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=parent,
                schema="definition",
                start=today - timedelta(days=7),
                end=today,
                limit=100
            )
            
            def_df = def_data.to_df()
            if len(def_df) > 0:
                print(f"   ✅ Found {len(def_df)} instrument definitions!")
                
                # Check if any are options
                if 'security_type' in def_df.columns:
                    sec_types = def_df['security_type'].unique()
                    print(f"   📊 Security types: {list(sec_types)}")
                    
                    # Look for option-related types
                    option_types = [t for t in sec_types if 'OPT' in str(t) or 'OPTION' in str(t)]
                    if option_types:
                        print(f"   🎯 FOUND OPTION TYPES: {option_types}")
                        findings.append(f"Parent {parent}: Found option types {option_types}")
                
                # Save sample definition
                sample = def_df.iloc[0]
                print(f"   📋 Sample instrument: {sample.get('symbol', 'N/A')}")
                
            else:
                print(f"   ❌ No definitions for {parent}")
                
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Error: {str(e)[:60]}...")
    
    # Test 3: Check for options in extended timeframes
    print("\n📋 TEST 3: Extended Historical Search")
    print("-" * 40)
    
    # Test historical periods when options might have been active
    historical_periods = [
        ("Last month", today - timedelta(days=60), today - timedelta(days=30)),
        ("This year", datetime(2025, 1, 1).date(), today),
        ("Last year", datetime(2024, 1, 1).date(), datetime(2024, 12, 31).date()),
    ]
    
    for period_name, start_date, end_date in historical_periods:
        print(f"🔍 Testing {period_name}: {start_date} to {end_date}")
        try:
            # Look for any NQ-related options in this period
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="Q3C",
                schema="trades",
                start=start_date,
                end=end_date,
                limit=5
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ FOUND HISTORICAL DATA: {len(df)} records!")
                findings.append(f"Historical Q3C data found in {period_name}")
                break
            else:
                print(f"   ❌ No data in {period_name}")
                
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Error in {period_name}: {str(e)[:50]}...")
    
    # Test 4: Check API capabilities
    print("\n📋 TEST 4: API Capabilities Check")
    print("-" * 40)
    
    try:
        # Check what datasets are available
        print("🔍 Testing dataset access...")
        
        # Try a simple request to understand our access level
        test_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQU5",
            schema="definition",
            start=today - timedelta(days=1),
            end=today,
            limit=1
        )
        
        test_df = test_data.to_df()
        if len(test_df) > 0:
            sample = test_df.iloc[0]
            print("✅ API working correctly")
            print(f"   📊 Available columns: {len(test_df.columns)}")
            print(f"   🏢 Exchange: {sample.get('exchange', 'N/A')}")
            print(f"   📝 Security type: {sample.get('security_type', 'N/A')}")
            
            # Check if we have any options-related fields
            options_fields = [col for col in test_df.columns if 'option' in col.lower() or 'strike' in col.lower()]
            if options_fields:
                print(f"   🎯 Options-related fields found: {options_fields}")
        
    except Exception as e:
        print(f"⚠️  API capability check failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 VALIDATION SUMMARY")
    print("="*60)
    
    if findings:
        print(f"✅ Found {len(findings)} positive results:")
        for finding in findings:
            print(f"   • {finding}")
    else:
        print("❌ NO options data found despite PDF claims")
        print("\nPossible explanations:")
        print("   1. Options data requires different API tier/permissions")
        print("   2. Different authentication needed")
        print("   3. Historical data only (not current)")
        print("   4. Documentation outdated/incorrect")
    
    # Save results
    results = {
        "validation_date": str(datetime.now()),
        "pdf_claims": [
            "Q3C options exist for Week-3 Wednesday expiry",
            "Parent symbology works for option chains",
            "All weekly options (Q1A, Q3C, etc.) supported",
            "Full tick-level options data available"
        ],
        "api_findings": findings,
        "conclusion": "PDF claims not validated by API testing" if not findings else "Some PDF claims validated"
    }
    
    with open("pdf_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: pdf_validation_results.json")

if __name__ == "__main__":
    main()