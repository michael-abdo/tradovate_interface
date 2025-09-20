#!/usr/bin/env python3
"""
Comprehensive analysis of ALL NQ option data in Databento:
- All available expirations
- Highest volume options for each expiration
- Complete volume rankings
"""

import databento as db
import pandas as pd
from datetime import datetime

def main():
    """Comprehensive NQ option analysis"""
    print("🔍 COMPREHENSIVE NQ OPTION DATA ANALYSIS")
    print("="*70)
    
    client = db.Historical("db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
    
    try:
        # Get ALL NQ option trades
        print("📋 Getting ALL NQ option trades...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-14",  # Get several days
            end="2025-07-17",
            stype_in="parent",
            limit=5000  # Get comprehensive data
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} total NQ option trades")
        
        # Get definitions to map symbols to expirations
        print("📋 Getting option definitions for expiration mapping...")
        
        definitions = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-15",
            end="2025-07-17",
            stype_in="parent"
        )
        
        def_df = definitions.to_df()
        print(f"✅ Retrieved {len(def_df)} option definitions")
        
        # Create symbol to expiration mapping
        symbol_exp_map = {}
        if len(def_df) > 0:
            for _, row in def_df.iterrows():
                symbol = row['symbol']
                expiration = row['expiration']
                symbol_exp_map[symbol] = expiration
        
        # Analyze volumes by symbol
        print(f"\n📊 ANALYZING VOLUMES BY SYMBOL")
        print("-" * 70)
        
        volume_analysis = []
        unique_symbols = trades_df['symbol'].unique()
        
        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                total_volume = symbol_trades['size'].sum()
                latest_price = symbol_trades['price'].iloc[-1]
                avg_price = symbol_trades['price'].mean()
                trades_count = len(symbol_trades)
                
                # Get expiration
                expiration = symbol_exp_map.get(symbol, 'Unknown')
                expiration_date = str(expiration).split(' ')[0] if expiration != 'Unknown' else 'Unknown'
                
                # Determine option type and strike
                option_type = 'call' if ' C' in symbol else 'put' if ' P' in symbol else 'unknown'
                
                # Extract strike
                strike = None
                try:
                    if ' C' in symbol:
                        strike = int(symbol.split(' C')[1])
                    elif ' P' in symbol:
                        strike = int(symbol.split(' P')[1])
                except:
                    pass
                
                volume_analysis.append({
                    'symbol': symbol,
                    'total_volume': total_volume,
                    'latest_price': latest_price,
                    'avg_price': avg_price,
                    'trades_count': trades_count,
                    'expiration': expiration,
                    'expiration_date': expiration_date,
                    'option_type': option_type,
                    'strike': strike
                })
        
        # Convert to DataFrame for easier analysis
        vol_df = pd.DataFrame(volume_analysis)
        
        # 1. TOP VOLUME OPTIONS OVERALL
        print(f"\n🏆 TOP 20 HIGHEST VOLUME NQ OPTIONS (ALL EXPIRATIONS)")
        print("-" * 70)
        
        top_volume = vol_df.nlargest(20, 'total_volume')
        
        for i, row in top_volume.iterrows():
            print(f"{len(top_volume) - list(top_volume.index).index(i):2d}. {row['symbol']:15s} | "
                  f"Vol: {row['total_volume']:4d} | "
                  f"Price: ${row['latest_price']:7.2f} | "
                  f"Exp: {row['expiration_date']:12s} | "
                  f"{row['option_type']:4s}")
        
        # 2. ANALYZE BY EXPIRATION DATE
        print(f"\n📅 ANALYSIS BY EXPIRATION DATE")
        print("=" * 70)
        
        # Group by expiration date
        exp_groups = vol_df.groupby('expiration_date')
        
        for exp_date in sorted(exp_groups.groups.keys()):
            exp_options = exp_groups.get_group(exp_date)
            
            # Sort by volume within this expiration
            exp_options_sorted = exp_options.sort_values('total_volume', ascending=False)
            
            total_volume_exp = exp_options['total_volume'].sum()
            total_contracts = len(exp_options)
            avg_volume = exp_options['total_volume'].mean()
            
            print(f"\n📅 EXPIRATION: {exp_date}")
            print(f"   📊 Summary: {total_contracts} contracts, {total_volume_exp:,} total volume, {avg_volume:.1f} avg volume")
            print(f"   🏆 Top 10 by volume:")
            
            for i, (_, row) in enumerate(exp_options_sorted.head(10).iterrows()):
                strike_str = str(int(row['strike'])) if pd.notna(row['strike']) else 'N/A'
                print(f"      {i+1:2d}. {row['symbol']:15s} | "
                      f"Vol: {row['total_volume']:4d} | "
                      f"${row['latest_price']:7.2f} | "
                      f"Strike: {strike_str:>5s} | "
                      f"{row['option_type']:4s}")
        
        # 3. SUMMARY STATISTICS BY EXPIRATION
        print(f"\n📊 SUMMARY STATISTICS BY EXPIRATION")
        print("-" * 70)
        
        exp_summary = vol_df.groupby('expiration_date').agg({
            'total_volume': ['count', 'sum', 'mean', 'max'],
            'latest_price': ['mean', 'min', 'max'],
            'strike': ['min', 'max']
        }).round(2)
        
        print(exp_summary)
        
        # 4. CALLS VS PUTS ANALYSIS
        print(f"\n📊 CALLS VS PUTS ANALYSIS")
        print("-" * 70)
        
        calls = vol_df[vol_df['option_type'] == 'call']
        puts = vol_df[vol_df['option_type'] == 'put']
        
        print(f"📈 CALLS:")
        print(f"   Total contracts: {len(calls)}")
        print(f"   Total volume: {calls['total_volume'].sum():,}")
        print(f"   Average volume: {calls['total_volume'].mean():.1f}")
        print(f"   Highest volume: {calls['total_volume'].max()} ({calls.loc[calls['total_volume'].idxmax(), 'symbol']})")
        
        print(f"\n📉 PUTS:")
        print(f"   Total contracts: {len(puts)}")
        print(f"   Total volume: {puts['total_volume'].sum():,}")
        print(f"   Average volume: {puts['total_volume'].mean():.1f}")
        print(f"   Highest volume: {puts['total_volume'].max()} ({puts.loc[puts['total_volume'].idxmax(), 'symbol']})")
        
        # 5. STRIKE PRICE ANALYSIS
        print(f"\n📊 STRIKE PRICE ANALYSIS")
        print("-" * 70)
        
        # Remove non-standard symbols for strike analysis
        standard_options = vol_df[vol_df['strike'].notna()]
        
        if len(standard_options) > 0:
            print(f"📋 Strike price range: {standard_options['strike'].min():,.0f} to {standard_options['strike'].max():,.0f}")
            print(f"📋 Most active strikes (by total volume):")
            
            strike_volumes = standard_options.groupby('strike')['total_volume'].sum().sort_values(ascending=False)
            
            for i, (strike, volume) in enumerate(strike_volumes.head(10).items()):
                print(f"   {i+1:2d}. ${strike:,.0f}: {volume:,} contracts")
        
        # 6. SAVE COMPREHENSIVE DATA
        print(f"\n💾 SAVING COMPREHENSIVE DATA")
        print("-" * 70)
        
        # Save to CSV
        vol_df.to_csv("nq_options_comprehensive_analysis.csv", index=False)
        print(f"✅ Saved comprehensive data to nq_options_comprehensive_analysis.csv")
        
        # Save summary by expiration
        exp_summary_simple = vol_df.groupby('expiration_date').agg({
            'total_volume': ['count', 'sum', 'max'],
            'symbol': lambda x: x[vol_df.loc[x.index, 'total_volume'].idxmax()]  # Highest volume symbol
        })
        
        exp_summary_simple.to_csv("nq_options_expiration_summary.csv")
        print(f"✅ Saved expiration summary to nq_options_expiration_summary.csv")
        
        # 7. FINAL SUMMARY
        print(f"\n🎯 FINAL SUMMARY")
        print("=" * 70)
        
        total_unique_options = len(vol_df)
        total_volume_all = vol_df['total_volume'].sum()
        total_expirations = vol_df['expiration_date'].nunique()
        highest_vol_option = vol_df.loc[vol_df['total_volume'].idxmax()]
        
        print(f"📊 Total unique NQ options: {total_unique_options:,}")
        print(f"📊 Total volume across all options: {total_volume_all:,} contracts")
        print(f"📊 Number of expiration dates: {total_expirations}")
        print(f"📊 Highest volume option: {highest_vol_option['symbol']} ({highest_vol_option['total_volume']:,} contracts)")
        print(f"📊 Price range: ${vol_df['latest_price'].min():.2f} to ${vol_df['latest_price'].max():.2f}")
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()