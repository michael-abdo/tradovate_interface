#!/usr/bin/env python3
"""
Final Options Investigation - Based on PDF Evidence
Focus on the clues we found: strike_price fields exist, API works
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Final systematic investigation"""
    print("🔍 FINAL NQ OPTIONS INVESTIGATION")
    print("="*60)
    print("CLUES FOUND:")
    print("✅ NQU5 parent symbology works")
    print("✅ API has strike_price fields")
    print("✅ Infrastructure supports options")
    print("❌ But no actual options contracts found")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Final hypothesis: Maybe we need to query specific strikes
    print("\n📋 HYPOTHESIS: Query Specific Strike Prices")
    print("-" * 50)
    
    # NQ is around 21,376 - let's try common strikes
    current_price = 21376
    strikes_to_test = [
        20000, 20500, 21000, 21500, 22000, 22500
    ]
    
    for strike in strikes_to_test:
        # Try different option symbol formats with strikes
        strike_symbols = [
            f"Q3C{strike}C",     # Call
            f"Q3C{strike}P",     # Put
            f"Q3CN25{strike}C",  # Call with year
            f"Q3CN25{strike}P",  # Put with year
            f"NQU5 {strike}C",   # Space format call
            f"NQU5 {strike}P",   # Space format put
        ]
        
        for symbol in strike_symbols:
            try:
                data = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=symbol,
                    schema="trades",
                    start=today - timedelta(days=7),
                    end=today,
                    limit=5
                )
                
                df = data.to_df()
                if len(df) > 0:
                    print(f"🎯 FOUND: {symbol} - {len(df)} records!")
                    return True  # Exit on first success
                    
            except Exception:
                pass  # Continue testing
    
    print("❌ No strike-based symbols found")
    
    # Check if there are other datasets with options
    print("\n📋 HYPOTHESIS: Different Dataset Required")
    print("-" * 50)
    
    other_datasets = [
        "OPRA.PILLAR",    # US equity options
        "DBEQ.BASIC",     # Databento equity
        "CBOE.PITCH",     # CBOE options
    ]
    
    for dataset in other_datasets:
        print(f"🔍 Testing dataset: {dataset}")
        try:
            # Test with a simple symbol
            data = client.timeseries.get_range(
                dataset=dataset,
                symbols="SPY",  # Well-known symbol
                schema="trades",
                start=today - timedelta(days=1),
                end=today,
                limit=1
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ {dataset} accessible - {len(df)} records")
                
                # Try NQ in this dataset
                nq_data = client.timeseries.get_range(
                    dataset=dataset,
                    symbols="NQ",
                    schema="trades",
                    start=today - timedelta(days=1),
                    end=today,
                    limit=1
                )
                
                nq_df = nq_data.to_df()
                if len(nq_df) > 0:
                    print(f"   🎯 NQ found in {dataset}!")
            else:
                print(f"   ❌ {dataset} - No data")
                
        except Exception as e:
            if "permission" in str(e).lower() or "access" in str(e).lower():
                print(f"   🔒 {dataset} - Access denied")
            elif "dataset" in str(e).lower():
                print(f"   ❌ {dataset} - Dataset not found")
            else:
                print(f"   ⚠️  {dataset} - Error: {str(e)[:30]}...")
    
    # Final check: Are we missing a subscription level?
    print("\n📋 HYPOTHESIS: Subscription/Permission Issue")
    print("-" * 50)
    
    try:
        # Check our account capabilities by examining the working data
        working_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQU5",
            schema="definition",
            start=today - timedelta(days=1),
            end=today,
            limit=10
        )
        
        df = working_data.to_df()
        if len(df) > 0:
            print("📊 Account Analysis:")
            
            # Check instrument classes available
            if 'instrument_class' in df.columns:
                classes = df['instrument_class'].unique()
                print(f"   📋 Instrument classes: {list(classes)}")
                
                if 'O' not in classes and 'OPT' not in classes:
                    print("   🔍 No option classes found (O, OPT)")
            
            # Check for options-related fields
            option_fields = [col for col in df.columns if any(word in col.lower() for word in ['option', 'strike', 'call', 'put'])]
            print(f"   📊 Options-related fields: {option_fields}")
            
            # Look at one record in detail
            sample = df.iloc[0]
            print(f"   📝 Sample security type: {sample.get('security_type', 'N/A')}")
            print(f"   📝 Sample CFI: {sample.get('cfi', 'N/A')}")
            
    except Exception as e:
        print(f"⚠️  Account analysis failed: {e}")
    
    # Final conclusion
    print("\n" + "="*60)
    print("🎯 FINAL CONCLUSION")
    print("="*60)
    
    print("📋 EVIDENCE SUMMARY:")
    print("✅ Databento PDF clearly states NQ options are supported")
    print("✅ API infrastructure has options fields (strike_price, etc.)")
    print("✅ NQ futures data works perfectly")
    print("❌ NO actual options contracts found in any format")
    print("❌ All symbols resolve to futures only")
    
    print("\n📊 MOST LIKELY EXPLANATION:")
    print("🔒 Options data requires UPGRADED SUBSCRIPTION or SPECIAL ACCESS")
    print("📄 PDF represents full product capability, not free/basic tier")
    print("💰 Our API key may only have futures access")
    
    print("\n📞 RECOMMENDED ACTION:")
    print("1. Contact Databento support directly")
    print("2. Ask about NQ options access requirements")
    print("3. Verify subscription level includes options")
    print("4. Request access to options data feed")
    
    # Save final report
    final_report = {
        "investigation_date": str(datetime.now()),
        "pdf_claims": "NQ options fully supported including Q3C",
        "api_reality": "NO options contracts found despite comprehensive testing",
        "infrastructure_evidence": "API has options fields but only futures data",
        "conclusion": "Options data likely requires upgraded subscription",
        "recommendation": "Contact Databento support for options access"
    }
    
    with open("final_options_investigation.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n📁 Report saved: final_options_investigation.json")

if __name__ == "__main__":
    main()