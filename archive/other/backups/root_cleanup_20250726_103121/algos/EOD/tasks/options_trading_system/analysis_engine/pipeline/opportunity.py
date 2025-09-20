#!/usr/bin/env python3
"""
Trading Opportunity Data Structure
The common data format that flows through the analysis pipeline
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class TradingOpportunity:
    """
    Core data structure that flows through the analysis pipeline.
    Each analysis enriches this object with its own data and scoring.
    """
    
    # === CORE IDENTIFICATION ===
    opportunity_id: str                    # Unique identifier
    strike_price: float                    # Options strike price
    underlying_price: float                # Current underlying price
    expiration_date: str                   # Options expiration
    
    # === RAW OPTIONS DATA ===
    call_open_interest: int = 0
    call_volume: int = 0
    call_mark_price: float = 0.0
    call_bid: float = 0.0
    call_ask: float = 0.0
    
    put_open_interest: int = 0
    put_volume: int = 0
    put_mark_price: float = 0.0
    put_bid: float = 0.0
    put_ask: float = 0.0
    
    # === TRADE SETUP DATA ===
    trade_direction: Optional[str] = None      # "LONG" or "SHORT"
    entry_price: Optional[float] = None        # Proposed entry price
    target_price: Optional[float] = None       # Take profit target
    stop_price: Optional[float] = None         # Stop loss price
    position_size: Optional[str] = None        # Position sizing recommendation
    
    # === ANALYSIS ENRICHMENT DATA ===
    # Each analysis adds its own section to this dict
    analysis_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # === SCORING & RANKING ===
    # Each analysis adds its own scores here
    scores: Dict[str, float] = field(default_factory=dict)
    
    # === COMPOSITE SCORING ===
    composite_score: float = 0.0              # Final weighted score across analyses
    confidence_level: str = "UNKNOWN"         # "HIGH", "MEDIUM", "LOW"
    
    # === METADATA ===
    created_at: str = field(default_factory=lambda: get_utc_timestamp())
    last_updated: str = field(default_factory=lambda: get_utc_timestamp())
    pipeline_stage: str = "raw"               # Current pipeline stage
    analysis_history: List[str] = field(default_factory=list)  # Track which analyses processed this
    
    def add_analysis_data(self, analysis_name: str, data: Dict[str, Any]):
        """Add analysis-specific data to this opportunity"""
        self.analysis_data[analysis_name] = data
        self.analysis_history.append(analysis_name)
        self.last_updated = get_utc_timestamp()
        self.pipeline_stage = analysis_name.lower()
    
    def add_score(self, analysis_name: str, score: float):
        """Add analysis-specific score"""
        self.scores[analysis_name] = score
        self.last_updated = get_utc_timestamp()
    
    def get_analysis_data(self, analysis_name: str) -> Dict[str, Any]:
        """Get analysis-specific data"""
        return self.analysis_data.get(analysis_name, {})
    
    def get_score(self, analysis_name: str) -> float:
        """Get analysis-specific score"""
        return self.scores.get(analysis_name, 0.0)
    
    def calculate_composite_score(self, weights: Dict[str, float]) -> float:
        """Calculate weighted composite score across all analyses"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for analysis_name, weight in weights.items():
            if analysis_name in self.scores:
                weighted_sum += self.scores[analysis_name] * weight
                total_weight += weight
        
        self.composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        return self.composite_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'opportunity_id': self.opportunity_id,
            'strike_price': self.strike_price,
            'underlying_price': self.underlying_price,
            'expiration_date': self.expiration_date,
            'call_data': {
                'open_interest': self.call_open_interest,
                'volume': self.call_volume,
                'mark_price': self.call_mark_price,
                'bid': self.call_bid,
                'ask': self.call_ask
            },
            'put_data': {
                'open_interest': self.put_open_interest,
                'volume': self.put_volume,
                'mark_price': self.put_mark_price,
                'bid': self.put_bid,
                'ask': self.put_ask
            },
            'trade_setup': {
                'direction': self.trade_direction,
                'entry_price': self.entry_price,
                'target_price': self.target_price,
                'stop_price': self.stop_price,
                'position_size': self.position_size
            },
            'analysis_data': self.analysis_data,
            'scores': self.scores,
            'composite_score': self.composite_score,
            'confidence_level': self.confidence_level,
            'metadata': {
                'created_at': self.created_at,
                'last_updated': self.last_updated,
                'pipeline_stage': self.pipeline_stage,
                'analysis_history': self.analysis_history
            }
        }
    
    @classmethod
    def from_normalized_contract(cls, contract: Dict[str, Any], underlying_price: float) -> 'TradingOpportunity':
        """Create TradingOpportunity from normalized contract data"""
        return cls(
            opportunity_id=f"strike_{contract['strike']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            strike_price=contract['strike'],
            underlying_price=underlying_price,
            expiration_date=contract.get('expiration', 'unknown'),
            call_open_interest=contract.get('call_open_interest', 0),
            call_volume=contract.get('call_volume', 0),
            call_mark_price=contract.get('call_mark_price', 0.0),
            call_bid=contract.get('call_bid', 0.0),
            call_ask=contract.get('call_ask', 0.0),
            put_open_interest=contract.get('put_open_interest', 0),
            put_volume=contract.get('put_volume', 0),
            put_mark_price=contract.get('put_mark_price', 0.0),
            put_bid=contract.get('put_bid', 0.0),
            put_ask=contract.get('put_ask', 0.0)
        )


class OpportunityDataset:
    """
    Container for managing a collection of TradingOpportunity objects
    Provides utilities for filtering, sorting, and pipeline operations
    """
    
    def __init__(self, opportunities: List[TradingOpportunity] = None):
        self.opportunities = opportunities or []
        self.pipeline_metadata = {
            'total_processed': 0,
            'filtered_count': 0,
            'analysis_stages': [],
            'execution_time': 0.0
        }
    
    def add_opportunity(self, opportunity: TradingOpportunity):
        """Add a trading opportunity to the dataset"""
        self.opportunities.append(opportunity)
    
    def filter_by_score(self, analysis_name: str, min_score: float) -> 'OpportunityDataset':
        """Filter opportunities by minimum score from specific analysis"""
        filtered = [opp for opp in self.opportunities 
                   if opp.get_score(analysis_name) >= min_score]
        
        result = OpportunityDataset(filtered)
        result.pipeline_metadata['filtered_count'] = len(self.opportunities) - len(filtered)
        return result
    
    def filter_by_criteria(self, filter_func) -> 'OpportunityDataset':
        """Filter opportunities using custom function"""
        filtered = [opp for opp in self.opportunities if filter_func(opp)]
        
        result = OpportunityDataset(filtered)
        result.pipeline_metadata['filtered_count'] = len(self.opportunities) - len(filtered)
        return result
    
    def sort_by_score(self, analysis_name: str, reverse: bool = True) -> 'OpportunityDataset':
        """Sort opportunities by specific analysis score"""
        sorted_opps = sorted(self.opportunities, 
                            key=lambda opp: opp.get_score(analysis_name),
                            reverse=reverse)
        return OpportunityDataset(sorted_opps)
    
    def sort_by_composite(self, reverse: bool = True) -> 'OpportunityDataset':
        """Sort opportunities by composite score"""
        sorted_opps = sorted(self.opportunities,
                            key=lambda opp: opp.composite_score,
                            reverse=reverse)
        return OpportunityDataset(sorted_opps)
    
    def limit(self, max_count: int) -> 'OpportunityDataset':
        """Limit to top N opportunities"""
        return OpportunityDataset(self.opportunities[:max_count])
    
    def size(self) -> int:
        """Get number of opportunities in dataset"""
        return len(self.opportunities)
    
    def is_empty(self) -> bool:
        """Check if dataset is empty"""
        return len(self.opportunities) == 0
    
    def get_top(self, n: int = 1) -> List[TradingOpportunity]:
        """Get top N opportunities"""
        return self.opportunities[:n]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all opportunities to list of dictionaries"""
        return [opp.to_dict() for opp in self.opportunities]
    
    @classmethod
    def from_normalized_data(cls, normalized_data: Dict[str, Any]) -> 'OpportunityDataset':
        """Create OpportunityDataset from normalized options data"""
        contracts = normalized_data.get('contracts', [])
        underlying_price = normalized_data.get('summary', {}).get('underlying_price', 0.0)
        
        opportunities = []
        for contract in contracts:
            opp = TradingOpportunity.from_normalized_contract(contract, underlying_price)
            opportunities.append(opp)
        
        return cls(opportunities)


# === EXAMPLE ANALYSIS DATA STRUCTURES ===

class RiskAnalysisData:
    """Standard data structure that Risk Analysis adds to opportunities"""
    def __init__(self):
        self.call_risk = 0.0              # Dollar risk for call holders
        self.put_risk = 0.0               # Dollar risk for put holders  
        self.total_risk = 0.0             # Combined risk exposure
        self.risk_ratio = 0.0             # Call risk / Put risk
        self.battle_zone = False          # Is this a battle zone strike?
        self.dominance = "NEUTRAL"        # "BULL", "BEAR", "NEUTRAL"
        self.urgency = "LOW"              # "IMMEDIATE", "HIGH", "MODERATE", "LOW"
        self.institutional_commitment = 0.0  # Strength of institutional positioning


class EVAnalysisData:
    """Standard data structure that EV Analysis adds to opportunities"""
    def __init__(self):
        self.probability = 0.0            # Win probability
        self.expected_value = 0.0         # Expected value in points
        self.risk_reward_ratio = 0.0      # Reward/Risk ratio
        self.quality_grade = "C"          # "A", "B", "C", "D", "F"
        self.trade_direction = None       # "LONG", "SHORT"
        self.entry_price = 0.0           # Calculated entry price
        self.target_price = 0.0          # Calculated target
        self.stop_price = 0.0            # Calculated stop loss


class MomentumAnalysisData:
    """Standard data structure that Momentum Analysis adds to opportunities"""
    def __init__(self):
        self.momentum_score = 0.0         # Overall momentum strength
        self.direction_alignment = False  # Does momentum align with trade direction?
        self.volume_confirmation = False  # Volume supports momentum?
        self.momentum_duration = 0        # How long momentum has persisted
        self.momentum_acceleration = 0.0  # Rate of momentum change