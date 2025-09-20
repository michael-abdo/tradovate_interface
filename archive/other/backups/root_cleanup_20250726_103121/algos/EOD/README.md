# NQ Options Trading System

## Quick Start
```bash
# Run with today's contract
python3 run_pipeline.py

# Run with specific contract  
python3 run_pipeline.py MC7M25

# Show help
python3 run_pipeline.py --help
```

## 0DTE Pipeline
```bash
# Run 0DTE with auto-validation
python3 -c "from tasks.options_trading_system.daily_options_pipeline import run_daily_0dte_pipeline; print(run_daily_0dte_pipeline())"
```

**Features**: Smart symbol generation (MC/MM/MQ prefixes), expiration validation, weekend handling

## Architecture
Hierarchical pipeline: Raw Data → Risk Analysis → EV Analysis → Trading Opportunities

## Key Files
- `run_pipeline.py` - Main entry point
- `tasks/options_trading_system/daily_options_pipeline.py` - 0DTE processing
- `tasks/options_trading_system/analysis_engine/pipeline_config.json` - Configuration
- `docs/hierarchical_pipeline_framework.md` - Detailed documentation

## Structure
```
EOD/
├── run_pipeline.py                     # Main entry point
├── tasks/options_trading_system/       # Pipeline framework
│   ├── analysis_engine/                # Analysis modules
│   ├── data_ingestion/                 # Data loading (Barchart, Polygon, IB)
│   └── output_generation/              # Results output
├── outputs/YYYYMMDD/                   # Date-organized outputs
│   ├── analysis_exports/               # JSON analysis 
│   ├── reports/                        # Trading reports
│   └── logs/                           # System logs
└── docs/                               # Documentation
```

## Configuration
Edit `pipeline_config.json` for strategies: Conservative, Aggressive, Technical, Scalping

## Algorithm  
NQ Options EV with Risk Analysis (35% OI, 25% Volume, 25% PCR, 15% Distance), Institutional Positioning, Quality Filtering (Min EV: 15 points, Min Probability: 60%)

## Development
- Add analysis: Implement `PipelineAnalysis` interface
- Reorder pipeline: Change configuration file
- Optimize: Tune weights/thresholds via config

**Automated output organization by date/type - no manual file management required**