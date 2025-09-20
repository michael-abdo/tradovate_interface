# Legacy Scripts Archive

These scripts were moved from the root directory during the transition to the Hierarchical Pipeline Analysis Framework.

## Files Archived

### Analysis Scripts
- `analyze_nearby_strikes.py` - Analyzed strikes within a range of a target price
- `analyze_strike.py` - Individual strike risk analysis tool
- `quick_risk_check.py` - Quick risk assessment utility

### Execution Scripts  
- `simple_run.py` - Simple interface for running the trading system
- `run_trading_system.py` - Main system execution script with configuration
- `fast_run.py` - Optimized execution with parallel analysis and caching
- `performance_test.py` - Performance benchmarking and comparison tool

### Utility Scripts
- `cleanup_old_docs.sh` - Documentation cleanup script

## Replacement

These scripts have been superseded by the new Hierarchical Pipeline Analysis Framework located in `/tasks/options_trading_system/`.

The new system provides:
- Configuration-driven analysis strategies
- Modular pipeline architecture  
- Better performance and scalability
- ML-ready scoring system

## Historical Context

These scripts were part of the original task-based implementation that used parallel execution of risk and EV analyses. The new system uses sequential pipeline execution with enrichment and filtering.