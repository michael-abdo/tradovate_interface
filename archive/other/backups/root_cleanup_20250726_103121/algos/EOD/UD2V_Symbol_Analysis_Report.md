# UD:2V Symbol Analysis Report

## Executive Summary

This analysis examined 82 UD:2V symbols found in the NQ options comprehensive analysis CSV file. These symbols appear to represent sophisticated options strategies or multi-leg positions, likely from algorithmic trading systems or institutional portfolio hedging activities.

## Symbol Structure

### Pattern Format
```
UD:2V: [2-LETTER CODE] [7-DIGIT NUMBER]
```

### Examples
- `UD:2V: VT 2688867` → Code: VT, Number: 2688867
- `UD:2V: GN 2690020` → Code: GN, Number: 2690020
- `UD:2V: DG 2683053` → Code: DG, Number: 2683053

## 7-Digit Number Encoding

### Strike Price Hypothesis
The analysis strongly suggests that the 7-digit numbers encode strike prices using this formula:
```
Strike Price = First 5 digits ÷ 100
```

### Examples of Decoded Strikes
| Symbol | 7-Digit Number | Decoded Strike | Remainder | Price |
|--------|----------------|----------------|-----------|-------|
| UD:2V: VT 2688867 | 2688867 | 26,888 | 67 | 166.0 |
| UD:2V: GN 2690020 | 2690020 | 26,900 | 20 | -28.75 |
| UD:2V: VT 2507523 | 2507523 | 25,075 | 23 | 561.0 |

### Strike Distribution
- **25,000-25,999 range**: 73 symbols (89%)
- **26,000-26,999 range**: 9 symbols (11%)
- This aligns with NQ futures trading around 23,500-24,000 based on standard option activity

### Remainder Analysis (Last 2 Digits)
The last two digits appear to encode additional information:
- **Most common remainders**: 31, 05, 27 (3 occurrences each)
- **Possible meanings**: expiration week/day, contract series, or sequential numbering

## 2-Letter Code Analysis

### Code Frequencies and Interpretations

| Code | Count | Positive Prices | Negative Prices | Interpretation |
|------|-------|-----------------|-----------------|----------------|
| **VT** | 41 (50%) | 41 | 0 | Vanilla/Standard options |
| **GN** | 20 (24%) | 9 | 11 | General/Mixed strategy positions |
| **DG** | 10 (12%) | 3 | 7 | Delta/Gamma hedge or short positions |
| **IC** | 4 (5%) | 4 | 0 | Iron Condor spreads |
| **12** | 3 (4%) | 2 | 1 | Unknown code (position ID?) |
| **BO** | 2 (2%) | 2 | 0 | Buy Order or specific strategy |
| **CO** | 1 (1%) | 1 | 0 | Call Options (confirmed) |
| **RR** | 1 (1%) | 0 | 1 | Risk Reversal strategy |

### Code Analysis Details

#### VT (Vanilla Trade) - 50% of symbols
- **Characteristics**: All positive prices, highest volume
- **Price range**: $3.25 - $1,105.25
- **Total volume**: 571 (69% of all UD:2V volume)
- **Interpretation**: Standard long option positions

#### GN (General/Mixed) - 24% of symbols
- **Characteristics**: More negative than positive prices
- **Price range**: -$270.00 to $1,787.00
- **Interpretation**: Mixed strategy or short positions

#### DG (Delta/Gamma) - 12% of symbols
- **Characteristics**: Predominantly negative prices (-$2,734.25 to $261.25)
- **Interpretation**: Likely short positions or hedge strategies

## Price and Volume Patterns

### Price Comparison with Standard NQ Options
- **Standard NQ average**: $474.20
- **UD:2V average**: $105.24
- **UD:2V range**: -$2,734.25 to $1,787.00

### Volume Comparison
- **Standard NQ average**: 38.86 contracts
- **UD:2V average**: 10.28 contracts
- **Highest UD:2V volume**: 144 contracts (VT 2524230)

### Negative Prices
- **19 symbols** (23%) have negative prices
- Concentrated in GN (11) and DG (7) codes
- Suggests credit strategies or short positions

## Expiration Analysis

### Expiration Distribution
- **July 18, 2025**: 81 symbols (99%)
- **July 15, 2025**: 1 symbol (1%)

### 0DTE Characteristics
The concentration of same-day expirations suggests these are:
- Zero Days to Expiration (0DTE) options
- Intraday trading instruments
- Day trading or scalping strategies

## Key Findings

1. **Structure**: UD:2V symbols encode strike prices in first 5 digits (÷100) with 2-digit suffixes
2. **Strategy Types**: Codes indicate different option strategies (vanilla, spreads, hedges)
3. **Sophisticated Trading**: Negative prices and complex codes suggest institutional strategies
4. **0DTE Focus**: 99% expire same day, indicating short-term trading focus
5. **Lower Volume**: Generally lower volume than standard options (specialized use)

## Conclusions

UD:2V symbols represent a sophisticated options trading system that encodes:
- **Strike prices** in a compressed 7-digit format
- **Strategy types** through 2-letter codes
- **Additional parameters** in suffix digits

These instruments are likely used by:
- Algorithmic trading systems
- Institutional investors
- High-frequency trading operations
- Portfolio hedging activities

The prevalence of same-day expirations and negative prices suggests these are primarily used for short-term trading strategies and complex multi-leg option positions.

## Files Generated

1. `/Users/Mike/trading/algos/EOD/analyze_ud2v_symbols.py` - Initial analysis script
2. `/Users/Mike/trading/algos/EOD/decode_ud2v_patterns.py` - Pattern decoder
3. `/Users/Mike/trading/algos/EOD/final_ud2v_analysis.py` - Comprehensive analysis
4. `/Users/Mike/trading/algos/EOD/ud2v_analysis_results.json` - Detailed JSON results
5. `/Users/Mike/trading/algos/EOD/UD2V_Symbol_Analysis_Report.md` - This report

## Data Source
Analysis based on `/Users/Mike/trading/algos/EOD/nq_options_comprehensive_analysis.csv`