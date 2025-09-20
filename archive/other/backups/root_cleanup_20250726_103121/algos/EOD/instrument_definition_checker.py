#!/usr/bin/env python3
"""
Deep dive into Databento instrument definitions
Goal: Understand what NQ-related instruments are actually available
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Check instrument definitions in detail"""
    print("🔍 DEEP INSTRUMENT DEFINITION ANALYSIS")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Get definition data for NQU5 to understand the structure
    print("📋 Analyzing NQU5 definition structure...")
    
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQU5",
            schema="definition",
            start=today - timedelta(days=1),
            end=today,
            limit=100
        )
        
        df = data.to_df()
        print(f"✅ Found {len(df)} definition records")
        
        if len(df) > 0:
            # Examine the structure
            print("\n📊 Column structure:")
            for col in df.columns:
                print(f"   • {col}")
            
            # Look at the actual definition data
            if not df.empty:
                sample = df.iloc[0]
                print("\n📋 Sample definition record:")
                for key, value in sample.items():
                    print(f"   {key}: {value}")
                
                # Save the definition structure
                definition_data = df.to_dict('records')
                with open("nq_definition_sample.json", "w") as f:
                    json.dump(definition_data, f, indent=2, default=str)
                print("\n✅ Saved definition sample to nq_definition_sample.json")
        
    except Exception as e:
        print(f"❌ Failed to get definition data: {e}")
    
    # Try to find any options-related instruments
    print("\n" + "="*60)
    print("🔍 SEARCHING FOR OPTIONS PATTERNS")
    print("="*60)
    
    # Try different patterns that might indicate options
    option_patterns = [
        "NQU5C",    # Call options on NQU5
        "NQU5P",    # Put options on NQU5
        "ONQ",      # Options on NQ
        "1NQ",      # Alternative NQ symbol
        "0NQ",      # Another alternative
    ]
    
    for pattern in option_patterns:
        print(f"\n🔍 Testing pattern: {pattern}")
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=pattern,
                schema="trades",
                start=today - timedelta(days=1),
                end=today,
                limit=10
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ Found {len(df)} records!")
                if 'symbol' in df.columns:
                    symbols = df['symbol'].unique()
                    print(f"   📊 Symbols: {list(symbols)}")
            else:
                print(f"   ❌ No data found")
                
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Error: {str(e)[:100]}")
    
    print("\n🎯 Analysis complete!")

if __name__ == "__main__":
    main()