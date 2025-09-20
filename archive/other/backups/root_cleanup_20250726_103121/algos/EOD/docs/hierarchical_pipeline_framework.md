# Hierarchical Pipeline Analysis Framework

## Philosophy & Architecture

### Core Philosophy
The **Hierarchical Pipeline Analysis Framework** treats market analysis as a **data refinement pipeline** where each analysis acts as a **filter, enricher, and sorter** of trading opportunities. This approach enables:

- **Scalable Analysis Chaining**: Add 5-10 analyses in sequence without exponential complexity
- **Configuration-Driven Strategy**: Change analysis order and parameters via config files
- **ML-Ready Architecture**: Each analysis contributes weighted scores for optimization
- **Modular Development**: Add new analyses by implementing a simple 3-method interface

### Data Flow Philosophy
```
Raw Market Data (1000 strikes) 
    ↓ [Transform to TradingOpportunity objects]
Risk Analysis: "Enrich with risk data → Filter significant exposure → Sort by risk"
    ↓ (100 opportunities remain)
EV Analysis: "Enrich with EV data → Filter positive EV → Sort by expected value"  
    ↓ (50 opportunities remain)
Momentum Analysis: "Enrich with momentum → Filter aligned momentum → Sort by strength"
    ↓ (25 opportunities remain)
Pattern Analysis: "Enrich with patterns → Filter strong patterns → Sort by confidence"
    ↓ (10 opportunities remain)
Final Results: Top-ranked trading opportunities
```

### Key Architectural Principles

1. **Common Data Currency**: All analyses operate on `TradingOpportunity` objects
2. **Additive Enrichment**: Each analysis adds data without overwriting previous analysis
3. **Independent Filtering**: Each analysis filters based on its own criteria + previous enrichment
4. **Scoring Contribution**: Each analysis contributes a score for final composite ranking
5. **Order Independence**: Analyses can be reordered via configuration without code changes
6. **Failure Isolation**: One analysis failure doesn't break the entire pipeline

---

## Core Components

### 1. TradingOpportunity Data Structure

**Purpose**: The common data object that flows through the pipeline, accumulating analysis data and scores.

**Key Fields**:
```python
class TradingOpportunity:
    # Core identification
    opportunity_id: str
    strike_price: float
    underlying_price: float
    
    # Raw options data
    call_open_interest: int
    put_open_interest: int
    call_mark_price: float
    put_mark_price: float
    # ... other options fields
    
    # Accumulating analysis data
    analysis_data: Dict[str, Dict[str, Any]]  # {"RiskAnalysis": {...}, "EVAnalysis": {...}}
    scores: Dict[str, float]                  # {"RiskAnalysis": 0.85, "EVAnalysis": 0.92}
    composite_score: float                    # Weighted final score
    
    # Pipeline metadata
    analysis_history: List[str]              # Track processing history
    pipeline_stage: str                      # Current stage name
```

**Critical Methods**:
- `add_analysis_data(analysis_name, data)`: Add analysis-specific enrichment
- `add_score(analysis_name, score)`: Add analysis-specific score (0.0-1.0)
- `get_analysis_data(analysis_name)`: Retrieve previous analysis data
- `calculate_composite_score(weights)`: Compute weighted final score

### 2. Pipeline Analysis Interface

**Purpose**: Standard interface that all analyses must implement for pipeline compatibility.

```python
class PipelineAnalysis:
    def process(self, dataset: OpportunityDataset) -> OpportunityDataset:
        # Step 1: Enrich each opportunity with analysis-specific data
        enriched = self.enrich_dataset(dataset)
        
        # Step 2: Filter opportunities that don't meet criteria  
        filtered = self.filter_dataset(enriched)
        
        # Step 3: Sort by analysis-specific scoring
        sorted_data = self.sort_dataset(filtered)
        
        return sorted_data
    
    def enrich_dataset(self, dataset) -> OpportunityDataset:
        """Add analysis-specific data to each opportunity"""
        
    def filter_dataset(self, dataset) -> OpportunityDataset:
        """Remove opportunities that don't meet criteria"""
        
    def sort_dataset(self, dataset) -> OpportunityDataset:
        """Sort opportunities by analysis-specific scoring"""
```

**Implementation Pattern**:
1. **Enrich**: Calculate analysis-specific metrics, add to `opportunity.analysis_data[analysis_name]`
2. **Filter**: Apply thresholds from config, remove opportunities that don't qualify
3. **Sort**: Rank remaining opportunities by analysis score, add to `opportunity.scores[analysis_name]`

### 3. Pipeline Orchestrator

**Purpose**: Manages the sequential execution of analyses according to configuration.

```python
class AnalysisPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.analyses: List[PipelineAnalysis] = []
        self.config = config
        
    def add_analysis(self, analysis: PipelineAnalysis):
        """Add analysis to pipeline in execution order"""
        
    def execute(self, raw_data: Dict[str, Any]) -> OpportunityDataset:
        """Execute full pipeline on raw market data"""
        
        # Convert raw data to TradingOpportunity objects
        dataset = OpportunityDataset.from_normalized_data(raw_data)
        
        # Execute each analysis in sequence
        for analysis in self.analyses:
            dataset = analysis.process(dataset)
            
            # Early termination if no opportunities remain
            if dataset.is_empty():
                break
                
        return dataset
```

### 4. Configuration-Driven Strategy Selection

**Purpose**: Define different analysis strategies via JSON configuration without code changes.

**Configuration Structure**:
```json
{
  "pipeline_strategies": {
    "conservative": {
      "analyses": [
        {
          "name": "RiskAnalysis",
          "config": {
            "min_risk_exposure": 50000,
            "sort_by": "total_risk",
            "sort_direction": "desc"
          }
        },
        {
          "name": "EVAnalysis", 
          "config": {
            "min_ev": 20,
            "min_probability": 0.70,
            "sort_by": "expected_value"
          }
        }
      ]
    }
  }
}
```

**Usage Pattern**:
```python
# Load strategy from config
strategy_config = load_config("conservative")

# Build pipeline
pipeline = AnalysisPipeline(strategy_config)
for analysis_spec in strategy_config["analyses"]:
    analysis_class = ANALYSIS_REGISTRY[analysis_spec["name"]]
    analysis = analysis_class(analysis_spec["config"])
    pipeline.add_analysis(analysis)

# Execute
results = pipeline.execute(market_data)
```

---

## Implementation Patterns

### Adding New Analysis

**Step 1**: Implement the Pipeline Interface
```python
class MomentumAnalysis(PipelineAnalysis):
    def __init__(self, config: Dict[str, Any]):
        self.min_momentum_score = config.get("min_momentum_score", 0.6)
        self.sort_by = config.get("sort_by", "momentum_score")
        
    def enrich_dataset(self, dataset: OpportunityDataset) -> OpportunityDataset:
        for opportunity in dataset.opportunities:
            # Calculate momentum metrics
            momentum_score = self.calculate_momentum(opportunity)
            direction_alignment = self.check_direction_alignment(opportunity)
            
            # Add to opportunity
            opportunity.add_analysis_data("MomentumAnalysis", {
                "momentum_score": momentum_score,
                "direction_alignment": direction_alignment,
                "momentum_duration": self.calculate_duration(opportunity)
            })
            
            # Add score
            opportunity.add_score("MomentumAnalysis", momentum_score)
            
        return dataset
        
    def filter_dataset(self, dataset: OpportunityDataset) -> OpportunityDataset:
        def momentum_filter(opp):
            momentum_data = opp.get_analysis_data("MomentumAnalysis")
            return momentum_data.get("momentum_score", 0) >= self.min_momentum_score
            
        return dataset.filter_by_criteria(momentum_filter)
        
    def sort_dataset(self, dataset: OpportunityDataset) -> OpportunityDataset:
        return dataset.sort_by_score("MomentumAnalysis", reverse=True)
```

**Step 2**: Register in Analysis Registry
```python
ANALYSIS_REGISTRY = {
    "RiskAnalysis": "risk_analysis.solution.RiskPipelineAnalysis",
    "EVAnalysis": "expected_value_analysis.solution.EVPipelineAnalysis",
    "MomentumAnalysis": "momentum_analysis.solution.MomentumAnalysis"  # Add new analysis
}
```

**Step 3**: Add to Pipeline Configuration
```json
{
  "name": "MomentumAnalysis",
  "config": {
    "min_momentum_score": 0.7,
    "momentum_window": 5,
    "sort_by": "momentum_score"
  }
}
```

### Reordering Analyses

**Via Configuration**: Simply change the order in the config file
```json
{
  "conservative": {
    "analyses": [
      {"name": "RiskAnalysis", "config": {...}},
      {"name": "EVAnalysis", "config": {...}},
      {"name": "MomentumAnalysis", "config": {...}}
    ]
  },
  "aggressive": {
    "analyses": [
      {"name": "EVAnalysis", "config": {...}},      // EV first
      {"name": "MomentumAnalysis", "config": {...}},
      {"name": "RiskAnalysis", "config": {...}}     // Risk last
    ]
  }
}
```

**Runtime Impact**: Different orders produce different results and performance characteristics:
- **Risk-First**: Conservative filtering, fewer opportunities, faster execution
- **EV-First**: More opportunities preserved, broader search space, slower execution
- **Pattern-First**: Technical focus, different opportunity set entirely

### Cross-Analysis Dependencies

**Reading Previous Analysis Data**:
```python
def enrich_dataset(self, dataset: OpportunityDataset) -> OpportunityDataset:
    for opportunity in dataset.opportunities:
        # Get data from previous analyses
        risk_data = opportunity.get_analysis_data("RiskAnalysis")
        ev_data = opportunity.get_analysis_data("EVAnalysis")
        
        # Use previous data to inform current analysis
        if risk_data.get("battle_zone", False):
            momentum_adjustment = 0.8  # Reduce momentum confidence in battle zones
        else:
            momentum_adjustment = 1.0
            
        momentum_score = self.calculate_momentum(opportunity) * momentum_adjustment
        
        # Continue with analysis...
```

**Conditional Filtering Based on Previous Analysis**:
```python
def filter_dataset(self, dataset: OpportunityDataset) -> OpportunityDataset:
    def smart_filter(opp):
        momentum_data = opp.get_analysis_data("MomentumAnalysis")
        ev_data = opp.get_analysis_data("EVAnalysis")
        
        # More lenient momentum requirements for high EV opportunities
        if ev_data.get("expected_value", 0) > 30:
            return momentum_data.get("momentum_score", 0) >= 0.5  # Lower threshold
        else:
            return momentum_data.get("momentum_score", 0) >= 0.7  # Normal threshold
            
    return dataset.filter_by_criteria(smart_filter)
```

---

## ML Optimization Integration

### Score-Based Optimization

**Problem**: How to optimally weight different analysis scores for best trading performance.

**Solution**: Each analysis contributes a normalized score (0.0-1.0). ML can optimize the composite weights:

```python
# ML optimizable weights
composite_weights = {
    "RiskAnalysis": 0.25,      # Weight for risk score
    "EVAnalysis": 0.40,        # Weight for EV score  
    "MomentumAnalysis": 0.35   # Weight for momentum score
}

# Calculate final opportunity ranking
for opportunity in opportunities:
    opportunity.calculate_composite_score(composite_weights)

# Sort by composite score
final_ranking = sorted(opportunities, key=lambda o: o.composite_score, reverse=True)
```

**ML Training Data Structure**:
```python
training_sample = {
    "opportunity_features": {
        "strike_price": 21750,
        "underlying_price": 21376.75,
        "risk_score": 0.85,
        "ev_score": 0.92, 
        "momentum_score": 0.78
    },
    "composite_weights": [0.25, 0.40, 0.35],
    "final_score": 0.864,
    "actual_outcome": {
        "profit_loss": 156.50,
        "win": True,
        "days_to_exit": 3
    }
}
```

### Filter Threshold Optimization

**Problem**: What thresholds should each analysis use for filtering?

**ML Approach**: Optimize filter thresholds for maximum Sharpe ratio:
```python
optimizable_config = {
    "RiskAnalysis": {
        "min_risk_exposure": 25000,     # ML optimizable: 10k-100k range
        "max_risk_ratio": 3.5           # ML optimizable: 1.5-10.0 range
    },
    "EVAnalysis": {
        "min_ev": 12,                   # ML optimizable: 5-25 range
        "min_probability": 0.58         # ML optimizable: 0.5-0.8 range
    }
}
```

### Pipeline Order Optimization

**Problem**: What analysis order produces the best results?

**ML Approach**: Treat order as a permutation optimization problem:
```python
analysis_orders = [
    ["RiskAnalysis", "EVAnalysis", "MomentumAnalysis"],      # Conservative
    ["EVAnalysis", "MomentumAnalysis", "RiskAnalysis"],      # Aggressive  
    ["MomentumAnalysis", "EVAnalysis", "RiskAnalysis"]       # Technical
]

# ML can test different orders and optimize for performance metrics
```

---

## Performance & Scalability Characteristics

### Execution Time Scaling
- **Linear Growth**: Each additional analysis adds ~2 seconds execution time
- **Dataset Shrinkage**: Early analyses filter aggressively, reducing load on later analyses
- **10 Analysis Estimate**: ~20 seconds total execution (acceptable for EOD analysis)

### Memory Usage
- **Bounded Growth**: TradingOpportunity objects accumulate data but dataset size shrinks
- **Worst Case**: 1000 opportunities × 10 analyses × average 2KB data = ~20MB RAM
- **Typical Case**: Heavy early filtering keeps memory usage under 5MB

### Configuration Complexity
- **Linear Config Growth**: Each analysis adds one config section
- **Independent Tuning**: Analysis parameters don't interact exponentially
- **10 Analysis Config**: ~30-50 parameters total (manageable)

---

## Error Handling & Debugging

### Pipeline Failure Isolation
```python
def execute_with_error_handling(self, raw_data: Dict[str, Any]) -> OpportunityDataset:
    dataset = OpportunityDataset.from_normalized_data(raw_data)
    
    for analysis in self.analyses:
        try:
            dataset = analysis.process(dataset)
            
            # Log pipeline state after each analysis
            self.log_pipeline_state(analysis.__class__.__name__, dataset)
            
        except Exception as e:
            # Log error but continue pipeline with previous dataset
            self.log_error(f"Analysis {analysis.__class__.__name__} failed: {e}")
            
            # Optional: Skip analysis or use degraded mode
            continue
            
    return dataset
```

### Debugging Pipeline State
```python
def log_pipeline_state(self, analysis_name: str, dataset: OpportunityDataset):
    print(f"After {analysis_name}:")
    print(f"  Opportunities remaining: {dataset.size()}")
    
    if not dataset.is_empty():
        top_opp = dataset.get_top(1)[0]
        print(f"  Top opportunity: Strike {top_opp.strike_price}")
        print(f"  Analysis history: {top_opp.analysis_history}")
        print(f"  Current scores: {top_opp.scores}")
        print(f"  Composite score: {top_opp.composite_score}")
```

### Common Issues & Solutions

1. **All Opportunities Filtered Out**: 
   - **Cause**: Too aggressive filtering in early analyses
   - **Solution**: Relax thresholds or reorder analyses

2. **Poor Final Rankings**:
   - **Cause**: Suboptimal composite score weights
   - **Solution**: ML optimization of weights or manual tuning

3. **Slow Execution**:
   - **Cause**: Heavy analysis early in pipeline
   - **Solution**: Reorder to put fast filters first

4. **Inconsistent Results**:
   - **Cause**: Analysis order dependency not accounted for
   - **Solution**: Make analyses more independent or document dependencies

---

## Future Extensions

### Multi-Timeframe Analysis
```python
class MultiTimeframeAnalysis(PipelineAnalysis):
    """Analyze opportunities across multiple timeframes"""
    def enrich_dataset(self, dataset):
        for opportunity in dataset.opportunities:
            # Add 1D, 1W, 1M momentum analysis
            timeframe_data = {
                "1D_momentum": self.calculate_momentum(opportunity, "1D"),
                "1W_momentum": self.calculate_momentum(opportunity, "1W"),
                "1M_momentum": self.calculate_momentum(opportunity, "1M")
            }
            opportunity.add_analysis_data("MultiTimeframeAnalysis", timeframe_data)
```

### Market Regime Adaptation
```python
class RegimeAdaptiveAnalysis(PipelineAnalysis):
    """Adjust analysis based on current market regime"""
    def filter_dataset(self, dataset):
        market_regime = self.detect_market_regime()
        
        if market_regime == "HIGH_VOLATILITY":
            # Use more conservative thresholds
            return self.apply_conservative_filter(dataset)
        elif market_regime == "TRENDING":
            # Use momentum-focused filtering
            return self.apply_momentum_filter(dataset)
        else:
            # Use standard filtering
            return self.apply_standard_filter(dataset)
```

### Portfolio-Level Analysis
```python
class PortfolioOptimizationAnalysis(PipelineAnalysis):
    """Optimize opportunities at portfolio level"""
    def sort_dataset(self, dataset):
        # Instead of ranking individual opportunities,
        # find optimal portfolio combination
        optimal_portfolio = self.optimize_portfolio_selection(dataset.opportunities)
        return self.rank_by_portfolio_contribution(dataset, optimal_portfolio)
```

---

## Summary for AI Implementation

**Key Implementation Priorities**:
1. **Start with TradingOpportunity data structure** - This is the foundation everything builds on
2. **Implement PipelineAnalysis interface** - Simple 3-method pattern for all analyses  
3. **Create configuration loader** - JSON-driven strategy selection
4. **Convert existing Risk/EV analyses** - Prove the pattern works
5. **Add pipeline orchestrator** - Sequential execution with error handling
6. **Scale to 5-10 analyses** - Each following the same pattern

**Critical Success Factors**:
- **Data Structure Consistency**: All analyses use TradingOpportunity objects
- **Interface Compliance**: All analyses implement enrich/filter/sort pattern
- **Configuration Flexibility**: Easy to reorder and retune via config files
- **Error Isolation**: Pipeline continues even if individual analyses fail
- **Performance Monitoring**: Track filtering ratios and execution times

**Architecture Benefits**:
- **Scalable**: Linear complexity growth with number of analyses
- **Maintainable**: Simple interface pattern for all analyses
- **Configurable**: Strategy changes via config files, not code changes
- **Debuggable**: Clear pipeline state logging and error isolation
- **ML-Ready**: Score-based optimization and threshold tuning