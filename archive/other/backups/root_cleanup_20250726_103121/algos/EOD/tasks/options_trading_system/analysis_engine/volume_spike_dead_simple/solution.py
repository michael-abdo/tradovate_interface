#!/usr/bin/env python3
"""
DEAD Simple Strategy - Volume Spike Detection
Detect and follow institutional money flow on expiration days

Core Philosophy:
- Find abnormal volume (Vol/OI > 10, Volume > 500)
- Verify institutional size (Volume × Price × $20 > $100K)
- Follow the direction (Calls = Long, Puts = Short)
- Hold until price hits strike
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
import sys
import os

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from common_utils import get_logger, log_and_return_none

logger = get_logger()

# Import baseline data manager for relative calculations
try:
    try:
        from .baseline_data_manager import BaselineDataManager, VolumeStats, MarketContext
    except ImportError:
        from baseline_data_manager import BaselineDataManager, VolumeStats, MarketContext
    BASELINE_MANAGER_AVAILABLE = True
    logger.info("[ENHANCED_SIGNAL] Baseline data manager imported successfully")
except ImportError as e:
    logger.warning(f"[ENHANCED_SIGNAL] Baseline data manager not available: {e}")
    BASELINE_MANAGER_AVAILABLE = False
    # Create stub classes for backward compatibility
    class VolumeStats:
        pass
    class MarketContext:
        pass

@dataclass
class InstitutionalSignal:
    """
    Enhanced Institutional Flow Signal with Relative Metrics
    
    Maintains backward compatibility while adding relative analysis capabilities
    """
    # Core fields (unchanged for backward compatibility)
    strike: float
    option_type: str  # 'CALL' or 'PUT'
    volume: int
    open_interest: int
    vol_oi_ratio: float
    option_price: float
    dollar_size: float
    direction: str  # 'LONG' or 'SHORT'
    target_price: float
    confidence: str  # 'EXTREME', 'VERY_HIGH', 'HIGH', 'MODERATE'
    timestamp: datetime
    expiration_date: str
    
    # Enhanced fields for relative analysis (optional, default None for compatibility)
    relative_volume_ratio: Optional[float] = None  # Today's volume / 20-day average
    volume_percentile_rank: Optional[float] = None  # Percentile rank vs history (0-100)
    premium_velocity: Optional[float] = None  # 15-min change vs hourly baseline
    dynamic_confidence_score: Optional[float] = None  # Numerical confidence (0-100)
    market_volatility_factor: Optional[float] = None  # Market volatility adjustment
    time_decay_factor: Optional[float] = None  # Days to expiration adjustment
    baseline_data_source: Optional[str] = None  # 'historical', 'smart_defaults', 'absolute'
    institutional_pressure: Optional[str] = None  # 'ACCUMULATING', 'DISTRIBUTING', 'NEUTRAL'
    
    # Cross-strike analysis (future enhancement)
    correlation_score: Optional[float] = None  # Strike correlation strength
    volume_weighted_skew: Optional[float] = None  # Cross-strike premium flow
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization with enhanced fields"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        
        # Log enhanced fields for debugging
        enhanced_fields = {
            'relative_volume_ratio': self.relative_volume_ratio,
            'volume_percentile_rank': self.volume_percentile_rank,
            'premium_velocity': self.premium_velocity,
            'dynamic_confidence_score': self.dynamic_confidence_score,
            'baseline_data_source': self.baseline_data_source
        }
        
        logger.debug(f"[ENHANCED_SIGNAL] Serializing signal for {self.strike}{self.option_type[0]} "
                    f"with enhanced fields: {enhanced_fields}")
        
        return d
    
    def get_enhanced_confidence_description(self) -> str:
        """Get detailed confidence description including relative metrics"""
        if self.dynamic_confidence_score is None:
            return f"{self.confidence} (Absolute thresholds)"
        
        relative_desc = ""
        if self.relative_volume_ratio:
            relative_desc += f", {self.relative_volume_ratio:.1f}x historical avg"
        if self.volume_percentile_rank:
            relative_desc += f", {self.volume_percentile_rank:.0f}th percentile"
        if self.baseline_data_source:
            relative_desc += f" ({self.baseline_data_source})"
            
        logger.debug(f"[ENHANCED_SIGNAL] Enhanced confidence for {self.strike}{self.option_type[0]}: "
                    f"{self.confidence} (score: {self.dynamic_confidence_score:.1f}){relative_desc}")
        
        return f"{self.confidence} (Score: {self.dynamic_confidence_score:.1f}{relative_desc})"
    
    def is_enhanced_analysis(self) -> bool:
        """Check if this signal includes enhanced relative analysis"""
        has_enhanced = self.relative_volume_ratio is not None
        logger.debug(f"[ENHANCED_SIGNAL] Signal {self.strike}{self.option_type[0]} "
                    f"enhanced analysis: {has_enhanced}")
        return has_enhanced

class RelativeThresholdCalculator:
    """
    Dynamic Threshold Calculator for Relative Analysis
    
    Transforms absolute thresholds into dynamic ones based on:
    - Historical volume patterns (20-day averages)
    - Market volatility conditions  
    - Time to expiration effects
    - Cross-strike correlations
    """
    
    def __init__(self, baseline_manager: Optional[BaselineDataManager] = None):
        """Initialize with optional baseline data manager"""
        self.baseline_manager = baseline_manager
        self.calculation_cache = {}  # Cache expensive calculations
        
        # Base multipliers for dynamic calculations
        self.base_multipliers = {
            'volume_ratio': 2.5,      # Base multiplier for relative volume
            'time_decay': 1.5,        # Time decay sensitivity
            'volatility': 1.2,        # Market volatility impact
            'confidence_boost': 1.8   # Confidence boost for good baselines
        }
        
        logger.info(f"[THRESHOLD_CALC] Initialized with baseline_manager: {baseline_manager is not None}")
        logger.debug(f"[THRESHOLD_CALC] Base multipliers: {self.base_multipliers}")
    
    def calculate_dynamic_vol_oi_threshold(self, 
                                         strike_data: Dict, 
                                         contract: str,
                                         market_context: Optional[MarketContext] = None) -> Tuple[float, str]:
        """
        Calculate dynamic volume/OI threshold based on historical patterns
        
        Args:
            strike_data: Current strike information
            contract: Contract identifier
            market_context: Market context for adjustments
            
        Returns:
            Tuple of (dynamic_threshold, calculation_source)
        """
        strike = float(strike_data.get('strike', 0))
        option_type = str(strike_data.get('optionType', '')).upper()
        volume = int(strike_data.get('volume', 0))
        
        cache_key = f"vol_oi_{contract}_{strike}_{option_type}"
        
        logger.debug(f"[THRESHOLD_CALC] Calculating dynamic vol/OI threshold for {strike}{option_type[0]}")
        
        # Check cache first
        if cache_key in self.calculation_cache:
            cached_result = self.calculation_cache[cache_key]
            logger.debug(f"[THRESHOLD_CALC] Cache hit for {strike}{option_type[0]}: {cached_result}")
            return cached_result
        
        # Try to get historical volume statistics
        if self.baseline_manager:
            volume_stats = self.baseline_manager.get_volume_stats(contract, strike, option_type)
            
            if volume_stats:
                # Calculate relative threshold based on historical baseline
                base_threshold = max(2.0, volume_stats.twenty_day_avg * 0.1)  # 10% of historical avg as base
                
                # Apply market context adjustments
                volatility_multiplier = 1.0
                time_multiplier = 1.0
                
                if market_context:
                    # Higher volatility = lower threshold (easier to trigger)
                    volatility_multiplier = market_context.volatility_factor
                    
                    # Closer to expiry = lower threshold (more sensitive)
                    days_to_expiry = market_context.time_to_expiry
                    time_multiplier = max(0.5, min(2.0, 7.0 / max(1, days_to_expiry)))
                
                dynamic_threshold = base_threshold * volatility_multiplier * time_multiplier
                calculation_source = f"historical_baseline"
                
                logger.info(f"[THRESHOLD_CALC] Historical calculation for {strike}{option_type[0]}: "
                           f"base={base_threshold:.1f}, volatility_mult={volatility_multiplier:.2f}, "
                           f"time_mult={time_multiplier:.2f}, final={dynamic_threshold:.1f}")
                
            else:
                # No historical data - use smart defaults
                dynamic_threshold = self._calculate_smart_default_threshold(strike_data)
                calculation_source = "smart_defaults"
                
                logger.info(f"[THRESHOLD_CALC] Smart default for {strike}{option_type[0]}: {dynamic_threshold:.1f}")
        else:
            # No baseline manager - fallback to absolute
            dynamic_threshold = 10.0  # Original absolute threshold
            calculation_source = "absolute_fallback"
            
            logger.info(f"[THRESHOLD_CALC] Absolute fallback for {strike}{option_type[0]}: {dynamic_threshold:.1f}")
        
        # Cache the result
        result = (dynamic_threshold, calculation_source)
        self.calculation_cache[cache_key] = result
        
        logger.debug(f"[THRESHOLD_CALC] Final dynamic vol/OI threshold for {strike}{option_type[0]}: "
                    f"{dynamic_threshold:.1f} (source: {calculation_source})")
        
        return result
    
    def calculate_dynamic_volume_threshold(self, 
                                         strike_data: Dict,
                                         contract: str,
                                         market_context: Optional[MarketContext] = None) -> Tuple[int, str]:
        """
        Calculate dynamic minimum volume threshold
        
        Args:
            strike_data: Current strike information
            contract: Contract identifier  
            market_context: Market context for adjustments
            
        Returns:
            Tuple of (dynamic_threshold, calculation_source)
        """
        strike = float(strike_data.get('strike', 0))
        option_type = str(strike_data.get('optionType', '')).upper()
        
        logger.debug(f"[THRESHOLD_CALC] Calculating dynamic volume threshold for {strike}{option_type[0]}")
        
        # Try to get historical volume statistics
        if self.baseline_manager:
            volume_stats = self.baseline_manager.get_volume_stats(contract, strike, option_type)
            
            if volume_stats:
                # Base threshold as percentage of historical average
                base_threshold = max(100, volume_stats.twenty_day_avg * 0.3)  # 30% of historical avg
                
                # Apply market adjustments
                if market_context:
                    # Higher volatility = lower threshold
                    volatility_adj = 1.0 / max(0.5, market_context.volatility_factor)
                    base_threshold *= volatility_adj
                
                dynamic_threshold = int(base_threshold)
                calculation_source = "historical_baseline"
                
                logger.info(f"[THRESHOLD_CALC] Historical volume threshold for {strike}{option_type[0]}: "
                           f"{dynamic_threshold} (from {volume_stats.twenty_day_avg:.1f} avg)")
                
            else:
                # Smart defaults based on current volume patterns
                volume = int(strike_data.get('volume', 0))
                dynamic_threshold = max(200, int(volume * 0.4))  # 40% of current as threshold
                calculation_source = "smart_defaults"
                
                logger.info(f"[THRESHOLD_CALC] Smart default volume threshold for {strike}{option_type[0]}: "
                           f"{dynamic_threshold}")
        else:
            # Fallback to absolute
            dynamic_threshold = 500  # Original absolute threshold
            calculation_source = "absolute_fallback"
            
            logger.info(f"[THRESHOLD_CALC] Absolute fallback volume threshold: {dynamic_threshold}")
        
        return (dynamic_threshold, calculation_source)
    
    def calculate_dynamic_confidence_score(self,
                                         relative_volume_ratio: Optional[float],
                                         volume_percentile_rank: Optional[float],
                                         vol_oi_ratio: float,
                                         baseline_source: str) -> float:
        """
        Calculate dynamic confidence score (0-100) based on multiple factors
        
        Args:
            relative_volume_ratio: Volume vs historical average
            volume_percentile_rank: Percentile ranking (0-100)
            vol_oi_ratio: Current volume/OI ratio
            baseline_source: Source of baseline data
            
        Returns:
            Dynamic confidence score (0-100)
        """
        logger.debug(f"[THRESHOLD_CALC] Calculating dynamic confidence score: "
                    f"rel_ratio={relative_volume_ratio}, percentile={volume_percentile_rank}, "
                    f"vol_oi={vol_oi_ratio}, source={baseline_source}")
        
        base_score = 0.0
        
        # Base score from vol/OI ratio (traditional confidence)
        if vol_oi_ratio >= 50:
            base_score = 90.0  # EXTREME
        elif vol_oi_ratio >= 30:
            base_score = 75.0  # VERY_HIGH
        elif vol_oi_ratio >= 20:
            base_score = 60.0  # HIGH
        elif vol_oi_ratio >= 10:
            base_score = 45.0  # MODERATE
        else:
            base_score = 25.0  # BELOW_THRESHOLD
        
        # Enhance with relative metrics
        if relative_volume_ratio is not None and relative_volume_ratio > 1.0:
            # Boost score based on how much higher than average
            relative_boost = min(25.0, (relative_volume_ratio - 1.0) * 10.0)
            base_score += relative_boost
            logger.debug(f"[THRESHOLD_CALC] Relative volume boost: +{relative_boost:.1f}")
        
        if volume_percentile_rank is not None and volume_percentile_rank > 50:
            # Boost score based on percentile ranking
            percentile_boost = min(15.0, (volume_percentile_rank - 50) * 0.3)
            base_score += percentile_boost
            logger.debug(f"[THRESHOLD_CALC] Percentile boost: +{percentile_boost:.1f}")
        
        # Adjust based on baseline data quality
        if baseline_source == "historical_baseline":
            base_score += 5.0  # Bonus for having good historical data
        elif baseline_source == "smart_defaults":
            base_score -= 5.0  # Penalty for using defaults
        elif baseline_source == "absolute_fallback":
            base_score -= 10.0  # Larger penalty for fallback
        
        # Cap at 100
        final_score = min(100.0, max(0.0, base_score))
        
        logger.info(f"[THRESHOLD_CALC] Dynamic confidence score calculated: {final_score:.1f} "
                   f"(base: {base_score:.1f}, source: {baseline_source})")
        
        return final_score
    
    def _calculate_smart_default_threshold(self, strike_data: Dict) -> float:
        """Calculate smart default vol/OI threshold when no historical data"""
        volume = int(strike_data.get('volume', 0))
        open_interest = int(strike_data.get('openInterest', 0))
        
        if open_interest > 0:
            current_ratio = volume / open_interest
            # If current ratio is high, use lower threshold to capture it
            smart_threshold = max(5.0, min(10.0, current_ratio * 0.5))
        else:
            smart_threshold = 8.0  # Conservative default
        
        logger.debug(f"[THRESHOLD_CALC] Smart default threshold calculated: {smart_threshold:.1f}")
        
        return smart_threshold
    
    def get_calculation_summary(self, strike_data: Dict, contract: str) -> Dict:
        """
        Get comprehensive summary of all threshold calculations for debugging
        
        Args:
            strike_data: Current strike information
            contract: Contract identifier
            
        Returns:
            Dictionary with all calculation details
        """
        strike = float(strike_data.get('strike', 0))
        option_type = str(strike_data.get('optionType', '')).upper()
        
        logger.debug(f"[THRESHOLD_CALC] Generating calculation summary for {strike}{option_type[0]}")
        
        # Get market context
        market_context = None
        if self.baseline_manager:
            market_context = self.baseline_manager.get_market_context(contract)
        
        # Calculate all thresholds
        vol_oi_threshold, vol_oi_source = self.calculate_dynamic_vol_oi_threshold(
            strike_data, contract, market_context)
        volume_threshold, volume_source = self.calculate_dynamic_volume_threshold(
            strike_data, contract, market_context)
        
        # Get volume stats if available
        volume_stats = None
        if self.baseline_manager:
            volume_stats = self.baseline_manager.get_volume_stats(contract, strike, option_type)
        
        summary = {
            'strike': strike,
            'option_type': option_type,
            'dynamic_vol_oi_threshold': vol_oi_threshold,
            'vol_oi_calculation_source': vol_oi_source,
            'dynamic_volume_threshold': volume_threshold,
            'volume_calculation_source': volume_source,
            'market_context': market_context.to_dict() if market_context else None,
            'volume_stats': volume_stats.to_dict() if volume_stats else None,
            'baseline_data_available': self.baseline_manager is not None,
            'calculation_cache_size': len(self.calculation_cache)
        }
        
        logger.info(f"[THRESHOLD_CALC] Calculation summary for {strike}{option_type[0]}: "
                   f"vol/OI={vol_oi_threshold:.1f} ({vol_oi_source}), "
                   f"volume={volume_threshold} ({volume_source})")
        
        return summary

class CrossStrikeAnalyzer:
    """
    Cross-Strike Correlation and Premium Velocity Analysis
    
    Detects coordinated institutional positioning across multiple strikes
    and tracks premium velocity patterns for enhanced signal confidence
    """
    
    def __init__(self):
        """Initialize cross-strike analyzer"""
        self.correlation_cache = {}
        self.velocity_cache = {}
        
        logger.info("[CROSS_STRIKE] Cross-strike analyzer initialized")
        
    def analyze_cross_strike_correlations(self, options_chain: List[Dict], 
                                        current_price: float) -> Dict:
        """
        Analyze correlations between strikes to detect coordinated flow
        
        Args:
            options_chain: List of option strikes data
            current_price: Current underlying price
            
        Returns:
            Dictionary with correlation analysis results
        """
        logger.info(f"[CROSS_STRIKE] Analyzing correlations across {len(options_chain)} strikes")
        
        # Group by call/put and filter for significant volume
        calls = []
        puts = []
        
        for strike_data in options_chain:
            try:
                volume = int(strike_data.get('volume', 0))
                if volume < 100:  # Skip low volume strikes
                    continue
                    
                option_type = str(strike_data.get('optionType', '')).upper()
                strike = float(strike_data.get('strike', 0))
                
                # Calculate distance from current price
                distance_pct = abs(strike - current_price) / current_price * 100
                
                strike_info = {
                    'strike': strike,
                    'volume': volume,
                    'distance_pct': distance_pct,
                    'dollar_volume': volume * float(strike_data.get('lastPrice', 0)) * 20
                }
                
                if option_type == 'CALL':
                    calls.append(strike_info)
                elif option_type == 'PUT':
                    puts.append(strike_info)
                    
            except Exception as e:
                logger.warning(f"[CROSS_STRIKE] Error processing strike {strike_data}: {e}")
                continue
        
        logger.debug(f"[CROSS_STRIKE] Filtered to {len(calls)} calls, {len(puts)} puts")
        
        # Analyze call correlations
        call_correlation = self._analyze_strike_group_correlation(calls, "CALL")
        put_correlation = self._analyze_strike_group_correlation(puts, "PUT")
        
        # Detect institutional pressure patterns
        institutional_pressure = self._detect_institutional_pressure(calls, puts, current_price)
        
        correlation_analysis = {
            'call_correlation': call_correlation,
            'put_correlation': put_correlation,
            'institutional_pressure': institutional_pressure,
            'coordinated_flow_detected': (
                call_correlation.get('correlation_strength', 0) > 0.6 or
                put_correlation.get('correlation_strength', 0) > 0.6
            ),
            'analysis_timestamp': get_utc_timestamp()
        }
        
        logger.info(f"[CROSS_STRIKE] Correlation analysis complete: "
                   f"calls={call_correlation.get('correlation_strength', 0):.2f}, "
                   f"puts={put_correlation.get('correlation_strength', 0):.2f}, "
                   f"pressure={institutional_pressure}")
        
        return correlation_analysis
    
    def _analyze_strike_group_correlation(self, strikes: List[Dict], option_type: str) -> Dict:
        """Analyze correlation within a group of strikes (calls or puts)"""
        if len(strikes) < 2:
            logger.debug(f"[CROSS_STRIKE] Insufficient {option_type} strikes for correlation")
            return {
                'correlation_strength': 0.0,
                'coordinated_strikes': [],
                'total_coordinated_volume': 0
            }
        
        # Sort by volume (descending)
        strikes.sort(key=lambda x: x['volume'], reverse=True)
        
        # Look for volume concentration patterns
        top_strikes = strikes[:3]  # Top 3 by volume
        total_volume = sum(s['volume'] for s in strikes)
        top_volume = sum(s['volume'] for s in top_strikes)
        
        concentration_ratio = top_volume / total_volume if total_volume > 0 else 0
        
        # Check for strikes with similar distance from current price (coordinated levels)
        distance_groups = {}
        for strike in top_strikes:
            distance_bucket = round(strike['distance_pct'] / 0.5) * 0.5  # 0.5% buckets
            if distance_bucket not in distance_groups:
                distance_groups[distance_bucket] = []
            distance_groups[distance_bucket].append(strike)
        
        # Find largest coordinated group
        largest_group = max(distance_groups.values(), key=len) if distance_groups else []
        coordinated_volume = sum(s['volume'] for s in largest_group)
        
        correlation_strength = min(1.0, concentration_ratio * len(largest_group) * 0.3)
        
        logger.debug(f"[CROSS_STRIKE] {option_type} correlation: strength={correlation_strength:.2f}, "
                    f"coordinated_vol={coordinated_volume}, concentration={concentration_ratio:.2f}")
        
        return {
            'correlation_strength': correlation_strength,
            'coordinated_strikes': [s['strike'] for s in largest_group],
            'total_coordinated_volume': coordinated_volume,
            'concentration_ratio': concentration_ratio
        }
    
    def _detect_institutional_pressure(self, calls: List[Dict], puts: List[Dict], 
                                     current_price: float) -> str:
        """Detect overall institutional pressure direction"""
        call_volume = sum(s['volume'] for s in calls)
        put_volume = sum(s['volume'] for s in puts)
        total_volume = call_volume + put_volume
        
        if total_volume == 0:
            return "NEUTRAL"
        
        call_pct = call_volume / total_volume * 100
        
        # Analyze positioning relative to current price
        otm_calls = [s for s in calls if s['strike'] > current_price]
        itm_puts = [s for s in puts if s['strike'] > current_price]
        
        otm_call_volume = sum(s['volume'] for s in otm_calls)
        itm_put_volume = sum(s['volume'] for s in itm_puts)
        
        # Determine pressure
        if call_pct > 70 and otm_call_volume > call_volume * 0.6:
            pressure = "ACCUMULATING_BULLISH"
        elif call_pct < 30 and itm_put_volume > put_volume * 0.6:
            pressure = "ACCUMULATING_BEARISH"
        elif call_pct > 60:
            pressure = "BULLISH_BIAS"
        elif call_pct < 40:
            pressure = "BEARISH_BIAS"
        else:
            pressure = "NEUTRAL"
        
        logger.debug(f"[CROSS_STRIKE] Institutional pressure: {pressure} "
                    f"(call_pct={call_pct:.1f}%, otm_calls={otm_call_volume}, itm_puts={itm_put_volume})")
        
        return pressure
    
    def calculate_premium_velocity(self, strike_data: Dict, 
                                 historical_premiums: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate premium velocity (rate of change) for institutional flow detection
        
        Args:
            strike_data: Current strike information
            historical_premiums: Historical premium data (if available)
            
        Returns:
            Dictionary with premium velocity metrics
        """
        strike = float(strike_data.get('strike', 0))
        option_type = str(strike_data.get('optionType', '')).upper()
        current_premium = float(strike_data.get('lastPrice', 0))
        
        logger.debug(f"[PREMIUM_VELOCITY] Calculating velocity for {strike}{option_type[0]}")
        
        # If no historical data, return basic metrics
        if not historical_premiums or len(historical_premiums) < 2:
            logger.debug(f"[PREMIUM_VELOCITY] No historical data for {strike}{option_type[0]}")
            return {
                'current_premium': current_premium,
                'velocity_score': 0.0,
                'acceleration': 0.0,
                'velocity_source': 'insufficient_data'
            }
        
        # Calculate velocity from recent premium changes
        try:
            # Sort by timestamp (most recent first)
            sorted_premiums = sorted(historical_premiums, 
                                   key=lambda x: x.get('timestamp', ''), reverse=True)
            
            recent_premiums = sorted_premiums[:5]  # Last 5 data points
            
            if len(recent_premiums) < 2:
                return {
                    'current_premium': current_premium,
                    'velocity_score': 0.0,
                    'acceleration': 0.0,
                    'velocity_source': 'insufficient_recent_data'
                }
            
            # Calculate velocity (change per unit time)
            velocity_changes = []
            for i in range(1, len(recent_premiums)):
                current = float(recent_premiums[i-1].get('premium', 0))
                previous = float(recent_premiums[i].get('premium', 0))
                
                if previous > 0:
                    pct_change = (current - previous) / previous * 100
                    velocity_changes.append(pct_change)
            
            if not velocity_changes:
                velocity_score = 0.0
                acceleration = 0.0
            else:
                # Average velocity
                velocity_score = sum(velocity_changes) / len(velocity_changes)
                
                # Acceleration (change in velocity)
                if len(velocity_changes) >= 2:
                    recent_velocity = velocity_changes[0]
                    older_velocity = velocity_changes[-1]
                    acceleration = recent_velocity - older_velocity
                else:
                    acceleration = 0.0
            
            logger.info(f"[PREMIUM_VELOCITY] {strike}{option_type[0]} velocity: "
                       f"score={velocity_score:.2f}%, acceleration={acceleration:.2f}%")
            
            return {
                'current_premium': current_premium,
                'velocity_score': velocity_score,
                'acceleration': acceleration,
                'velocity_source': 'historical_calculation',
                'data_points_used': len(recent_premiums)
            }
            
        except Exception as e:
            logger.error(f"[PREMIUM_VELOCITY] Error calculating velocity for {strike}{option_type[0]}: {e}")
            return {
                'current_premium': current_premium,
                'velocity_score': 0.0,
                'acceleration': 0.0,
                'velocity_source': 'calculation_error'
            }
    
    def get_volume_weighted_skew(self, options_chain: List[Dict], current_price: float) -> float:
        """
        Calculate volume-weighted premium skew across strikes
        
        Args:
            options_chain: List of option strikes data
            current_price: Current underlying price
            
        Returns:
            Volume-weighted skew score (-1 to 1, negative = put skew, positive = call skew)
        """
        logger.debug(f"[VOLUME_SKEW] Calculating volume-weighted skew for {len(options_chain)} strikes")
        
        total_weighted_distance = 0.0
        total_volume = 0
        
        for strike_data in options_chain:
            try:
                volume = int(strike_data.get('volume', 0))
                if volume == 0:
                    continue
                    
                strike = float(strike_data.get('strike', 0))
                option_type = str(strike_data.get('optionType', '')).upper()
                
                # Calculate signed distance (positive for calls above current, negative for puts below)
                distance = (strike - current_price) / current_price
                
                if option_type == 'PUT':
                    distance = -abs(distance)  # Puts contribute negative skew
                elif option_type == 'CALL':
                    distance = abs(distance)   # Calls contribute positive skew
                
                weighted_distance = distance * volume
                total_weighted_distance += weighted_distance
                total_volume += volume
                
            except Exception as e:
                logger.warning(f"[VOLUME_SKEW] Error processing strike {strike_data}: {e}")
                continue
        
        if total_volume == 0:
            skew_score = 0.0
        else:
            skew_score = total_weighted_distance / total_volume
            # Normalize to -1 to 1 range
            skew_score = max(-1.0, min(1.0, skew_score * 10))
        
        logger.info(f"[VOLUME_SKEW] Volume-weighted skew calculated: {skew_score:.3f} "
                   f"(total_volume={total_volume})")
        
        return skew_score

class DeadSimpleVolumeSpike:
    """
    Enhanced DEAD Simple Strategy Implementation
    
    Detects institutional positioning through abnormal options volume using:
    - Traditional absolute thresholds (backward compatible)
    - Enhanced relative analysis with historical baselines
    - Cross-strike correlation detection
    - Premium velocity tracking
    """
    
    # Traditional strategy parameters (backward compatibility)
    MIN_VOL_OI_RATIO = 10
    MIN_VOLUME = 500
    MIN_DOLLAR_SIZE = 100_000
    CONTRACT_MULTIPLIER = 20  # $20 per point for NQ mini
    
    # Confidence thresholds
    EXTREME_RATIO = 50
    VERY_HIGH_RATIO = 30
    HIGH_RATIO = 20
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Enhanced Dead Simple Strategy
        
        Args:
            config: Configuration dictionary with options:
                - threshold_mode: 'absolute' (default) or 'relative'
                - baseline_db_path: Path to baseline database
                - enable_cross_strike: Enable cross-strike analysis
                - enable_premium_velocity: Enable premium velocity tracking
        """
        self.config = config or {}
        
        # Apply configuration overrides
        self.MIN_VOL_OI_RATIO = self.config.get('min_vol_oi_ratio', self.MIN_VOL_OI_RATIO)
        self.MIN_VOLUME = self.config.get('min_volume', self.MIN_VOLUME)
        self.MIN_DOLLAR_SIZE = self.config.get('min_dollar_size', self.MIN_DOLLAR_SIZE)
        
        # Enhanced analysis configuration
        self.threshold_mode = self.config.get('threshold_mode', 'absolute')  # 'absolute' or 'relative'
        self.enable_cross_strike = self.config.get('enable_cross_strike', True)
        self.enable_premium_velocity = self.config.get('enable_premium_velocity', True)
        
        # Initialize enhanced components
        self.baseline_manager = None
        self.threshold_calculator = None
        self.cross_strike_analyzer = None
        
        # Try to initialize baseline manager for relative analysis
        if self.threshold_mode == 'relative' and BASELINE_MANAGER_AVAILABLE:
            try:
                from .baseline_data_manager import create_baseline_manager
                self.baseline_manager = create_baseline_manager(self.config)
                self.threshold_calculator = RelativeThresholdCalculator(self.baseline_manager)
                logger.info("[ENHANCED_DS] Relative analysis mode enabled with baseline manager")
            except Exception as e:
                logger.warning(f"[ENHANCED_DS] Failed to initialize baseline manager: {e}")
                logger.info("[ENHANCED_DS] Falling back to absolute threshold mode")
                self.threshold_mode = 'absolute'
        
        # Initialize cross-strike analyzer if enabled
        if self.enable_cross_strike:
            self.cross_strike_analyzer = CrossStrikeAnalyzer()
            logger.info("[ENHANCED_DS] Cross-strike analysis enabled")
        
        logger.info(f"[ENHANCED_DS] Enhanced Dead Simple Strategy initialized:")
        logger.info(f"[ENHANCED_DS] - Threshold mode: {self.threshold_mode}")
        logger.info(f"[ENHANCED_DS] - Cross-strike analysis: {self.enable_cross_strike}")
        logger.info(f"[ENHANCED_DS] - Premium velocity: {self.enable_premium_velocity}")
        logger.info(f"[ENHANCED_DS] - Baseline manager: {self.baseline_manager is not None}")
        
        # Log configuration details
        logger.debug(f"[ENHANCED_DS] Configuration: {self.config}")
        logger.debug(f"[ENHANCED_DS] Thresholds: vol/OI={self.MIN_VOL_OI_RATIO}, "
                    f"volume={self.MIN_VOLUME}, dollar=${self.MIN_DOLLAR_SIZE:,}")
    
    def analyze_strike(self, strike_data: Dict, current_price: float, 
                      contract: str = "unknown") -> Optional[InstitutionalSignal]:
        """
        Enhanced strike analysis with both absolute and relative thresholds
        
        Args:
            strike_data: Dictionary containing strike information
            current_price: Current underlying price
            contract: Contract identifier for baseline data lookup
            
        Returns:
            Enhanced InstitutionalSignal if criteria met, None otherwise
        """
        # Dispatch to appropriate analysis method
        if self.threshold_mode == 'relative' and self.threshold_calculator:
            return self._analyze_strike_relative(strike_data, current_price, contract)
        else:
            return self._analyze_strike_absolute(strike_data, current_price)
    
    @log_and_return_none(operation="_analyze_strike_absolute")
    def _analyze_strike_absolute(self, strike_data: Dict, current_price: float) -> Optional[InstitutionalSignal]:
        """
        Traditional absolute threshold analysis (backward compatible)
        
        Args:
            strike_data: Dictionary containing strike information
            current_price: Current underlying price
            
        Returns:
            InstitutionalSignal if criteria met, None otherwise
        """
        try:
            # Extract required fields with proper null handling
            raw_strike = strike_data.get('strike')
            raw_volume = strike_data.get('volume')
            raw_oi = strike_data.get('openInterest')
            raw_price = strike_data.get('lastPrice')
            
            logger.debug(f"[ABSOLUTE_ANALYSIS] Analyzing strike: {raw_strike}, "
                        f"volume: {raw_volume}, OI: {raw_oi}")
            
            # Skip if critical fields are None or empty
            if any(x is None for x in [raw_strike, raw_volume, raw_oi]):
                logger.debug(f"[ABSOLUTE_ANALYSIS] Skipping strike due to missing data")
                return None
            
            strike = float(raw_strike or 0)
            volume = int(raw_volume or 0)
            open_interest = int(raw_oi or 0)
            option_type = str(strike_data.get('optionType', '') or '').upper()
            option_price = float(raw_price or 0)
            
            # Skip if no open interest (avoid division by zero) or zero volume
            if open_interest == 0 or volume == 0:
                logger.debug(f"[ABSOLUTE_ANALYSIS] Skipping {strike}{option_type[0]} "
                           f"due to zero volume or OI")
                return None
            
            # Calculate volume/OI ratio
            vol_oi_ratio = volume / open_interest
            
            logger.debug(f"[ABSOLUTE_ANALYSIS] {strike}{option_type[0]} vol/OI ratio: {vol_oi_ratio:.1f}")
            
            # Apply basic filters
            if vol_oi_ratio < self.MIN_VOL_OI_RATIO or volume < self.MIN_VOLUME:
                logger.debug(f"[ABSOLUTE_ANALYSIS] {strike}{option_type[0]} failed basic filters: "
                           f"vol/OI={vol_oi_ratio:.1f} (min: {self.MIN_VOL_OI_RATIO}), "
                           f"volume={volume} (min: {self.MIN_VOLUME})")
                return None
            
            # Calculate dollar size (institutional footprint)
            dollar_size = volume * option_price * self.CONTRACT_MULTIPLIER
            
            if dollar_size < self.MIN_DOLLAR_SIZE:
                logger.debug(f"[ABSOLUTE_ANALYSIS] {strike}{option_type[0]} failed dollar size: "
                           f"${dollar_size:,.0f} < ${self.MIN_DOLLAR_SIZE:,.0f}")
                return None
            
            # Determine trading direction
            direction = 'LONG' if option_type == 'CALL' else 'SHORT'
            
            # Calculate confidence level (traditional)
            confidence = self._calculate_confidence(vol_oi_ratio)
            
            # Create signal with absolute analysis markers
            signal = InstitutionalSignal(
                strike=strike,
                option_type=option_type,
                volume=volume,
                open_interest=open_interest,
                vol_oi_ratio=vol_oi_ratio,
                option_price=option_price,
                dollar_size=dollar_size,
                direction=direction,
                target_price=strike,  # Target is the strike price
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                expiration_date=strike_data.get('expirationDate', ''),
                # Enhanced fields marked as absolute analysis
                baseline_data_source='absolute_thresholds'
            )
            
            logger.info(f"[ABSOLUTE_ANALYSIS] Institutional signal detected: {strike}{option_type[0]} "
                       f"Vol/OI={vol_oi_ratio:.1f}x ${dollar_size:,.0f} ({confidence})")
            
            return signal
            
        except Exception as e:
            raise  # Let decorator handle it
    
    @log_and_return_none(operation="_analyze_strike_relative")
    def _analyze_strike_relative(self, strike_data: Dict, current_price: float, 
                               contract: str) -> Optional[InstitutionalSignal]:
        """
        Enhanced relative threshold analysis with historical baselines
        
        Args:
            strike_data: Dictionary containing strike information
            current_price: Current underlying price
            contract: Contract identifier for baseline data lookup
            
        Returns:
            Enhanced InstitutionalSignal if criteria met, None otherwise
        """
        try:
            # Extract required fields with proper null handling
            raw_strike = strike_data.get('strike')
            raw_volume = strike_data.get('volume')
            raw_oi = strike_data.get('openInterest')
            raw_price = strike_data.get('lastPrice')
            
            logger.debug(f"[RELATIVE_ANALYSIS] Analyzing strike: {raw_strike}, "
                        f"volume: {raw_volume}, OI: {raw_oi}, contract: {contract}")
            
            # Skip if critical fields are None or empty
            if any(x is None for x in [raw_strike, raw_volume, raw_oi]):
                logger.debug(f"[RELATIVE_ANALYSIS] Skipping strike due to missing data")
                return None
            
            strike = float(raw_strike or 0)
            volume = int(raw_volume or 0)
            open_interest = int(raw_oi or 0)
            option_type = str(strike_data.get('optionType', '') or '').upper()
            option_price = float(raw_price or 0)
            
            # Skip if no open interest (avoid division by zero) or zero volume
            if open_interest == 0 or volume == 0:
                logger.debug(f"[RELATIVE_ANALYSIS] Skipping {strike}{option_type[0]} "
                           f"due to zero volume or OI")
                return None
            
            # Calculate volume/OI ratio
            vol_oi_ratio = volume / open_interest
            
            logger.debug(f"[RELATIVE_ANALYSIS] {strike}{option_type[0]} vol/OI ratio: {vol_oi_ratio:.1f}")
            
            # Calculate dynamic thresholds using relative analysis
            dynamic_vol_oi_threshold, vol_oi_source = self.threshold_calculator.calculate_dynamic_vol_oi_threshold(
                strike_data, contract)
            dynamic_volume_threshold, volume_source = self.threshold_calculator.calculate_dynamic_volume_threshold(
                strike_data, contract)
            
            logger.info(f"[RELATIVE_ANALYSIS] {strike}{option_type[0]} dynamic thresholds: "
                       f"vol/OI={dynamic_vol_oi_threshold:.1f} ({vol_oi_source}), "
                       f"volume={dynamic_volume_threshold} ({volume_source})")
            
            # Apply relative filters
            if vol_oi_ratio < dynamic_vol_oi_threshold or volume < dynamic_volume_threshold:
                logger.debug(f"[RELATIVE_ANALYSIS] {strike}{option_type[0]} failed relative filters: "
                           f"vol/OI={vol_oi_ratio:.1f} < {dynamic_vol_oi_threshold:.1f}, "
                           f"volume={volume} < {dynamic_volume_threshold}")
                return None
            
            # Calculate dollar size (institutional footprint)
            dollar_size = volume * option_price * self.CONTRACT_MULTIPLIER
            
            if dollar_size < self.MIN_DOLLAR_SIZE:
                logger.debug(f"[RELATIVE_ANALYSIS] {strike}{option_type[0]} failed dollar size: "
                           f"${dollar_size:,.0f} < ${self.MIN_DOLLAR_SIZE:,.0f}")
                return None
            
            # Get volume statistics for enhanced metrics
            volume_stats = None
            relative_volume_ratio = None
            volume_percentile_rank = None
            
            if self.baseline_manager:
                volume_stats = self.baseline_manager.get_volume_stats(contract, strike, option_type)
                if volume_stats:
                    relative_volume_ratio = self.baseline_manager.calculate_relative_volume_ratio(
                        volume, volume_stats)
                    volume_percentile_rank = volume_stats.percentile_rank
                    
                    logger.debug(f"[RELATIVE_ANALYSIS] {strike}{option_type[0]} relative metrics: "
                               f"ratio={relative_volume_ratio:.1f}x, percentile={volume_percentile_rank:.0f}%")
            
            # Calculate enhanced confidence score
            dynamic_confidence_score = self.threshold_calculator.calculate_dynamic_confidence_score(
                relative_volume_ratio, volume_percentile_rank, vol_oi_ratio, vol_oi_source)
            
            # Determine traditional confidence level for compatibility
            confidence = self._calculate_confidence(vol_oi_ratio)
            
            # Determine trading direction
            direction = 'LONG' if option_type == 'CALL' else 'SHORT'
            
            # Create enhanced signal
            signal = InstitutionalSignal(
                strike=strike,
                option_type=option_type,
                volume=volume,
                open_interest=open_interest,
                vol_oi_ratio=vol_oi_ratio,
                option_price=option_price,
                dollar_size=dollar_size,
                direction=direction,
                target_price=strike,  # Target is the strike price
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                expiration_date=strike_data.get('expirationDate', ''),
                # Enhanced relative metrics
                relative_volume_ratio=relative_volume_ratio,
                volume_percentile_rank=volume_percentile_rank,
                dynamic_confidence_score=dynamic_confidence_score,
                baseline_data_source=vol_oi_source
            )
            
            logger.info(f"[RELATIVE_ANALYSIS] Enhanced institutional signal detected: "
                       f"{strike}{option_type[0]} Vol/OI={vol_oi_ratio:.1f}x "
                       f"(dynamic threshold: {dynamic_vol_oi_threshold:.1f}), "
                       f"${dollar_size:,.0f}, confidence_score={dynamic_confidence_score:.1f}")
            
            return signal
            
        except Exception as e:
            raise  # Let decorator handle it
    
    def _calculate_confidence(self, vol_oi_ratio: float) -> str:
        """Calculate confidence level based on volume/OI ratio"""
        if vol_oi_ratio >= self.EXTREME_RATIO:
            return 'EXTREME'
        elif vol_oi_ratio >= self.VERY_HIGH_RATIO:
            return 'VERY_HIGH'
        elif vol_oi_ratio >= self.HIGH_RATIO:
            return 'HIGH'
        else:
            return 'MODERATE'
    
    def find_institutional_flow(self, options_chain: List[Dict], current_price: float, 
                              contract: str = "unknown") -> Dict:
        """
        Enhanced institutional flow analysis with cross-strike correlation and comprehensive logging
        
        Args:
            options_chain: List of option strikes data
            current_price: Current underlying price
            contract: Contract identifier for enhanced analysis
            
        Returns:
            Dictionary containing signals, cross-strike analysis, and metadata
        """
        logger.info(f"[INSTITUTIONAL_FLOW] Starting analysis of {len(options_chain)} strikes "
                   f"for contract {contract} at price ${current_price}")
        
        analysis_start_time = datetime.now(timezone.utc)
        
        # Store daily snapshot for baseline data if in relative mode
        if self.baseline_manager and options_chain:
            logger.info(f"[INSTITUTIONAL_FLOW] Storing daily snapshot for baseline calculations")
            self.baseline_manager.store_daily_snapshot(contract, options_chain)
        
        # Analyze individual strikes
        signals = []
        strikes_analyzed = 0
        strikes_passed_filters = 0
        
        for strike_data in options_chain:
            strikes_analyzed += 1
            signal = self.analyze_strike(strike_data, current_price, contract)
            if signal:
                signals.append(signal)
                strikes_passed_filters += 1
                
                # Log signal details
                logger.info(f"[INSTITUTIONAL_FLOW] Signal #{len(signals)}: "
                           f"{signal.strike}{signal.option_type[0]} "
                           f"Vol/OI={signal.vol_oi_ratio:.1f}x "
                           f"${signal.dollar_size:,.0f} ({signal.confidence})")
        
        logger.info(f"[INSTITUTIONAL_FLOW] Strike analysis complete: "
                   f"{strikes_passed_filters}/{strikes_analyzed} signals detected")
        
        # Perform cross-strike correlation analysis if enabled
        cross_strike_analysis = {}
        if self.enable_cross_strike and self.cross_strike_analyzer:
            logger.info(f"[INSTITUTIONAL_FLOW] Performing cross-strike correlation analysis")
            cross_strike_analysis = self.cross_strike_analyzer.analyze_cross_strike_correlations(
                options_chain, current_price)
            
            # Calculate volume-weighted skew
            volume_weighted_skew = self.cross_strike_analyzer.get_volume_weighted_skew(
                options_chain, current_price)
            cross_strike_analysis['volume_weighted_skew'] = volume_weighted_skew
            
            logger.info(f"[INSTITUTIONAL_FLOW] Cross-strike analysis complete: "
                       f"pressure={cross_strike_analysis.get('institutional_pressure')}, "
                       f"skew={volume_weighted_skew:.3f}")
        
        # Enhanced signal enrichment with cross-strike data
        if signals and cross_strike_analysis:
            institutional_pressure = cross_strike_analysis.get('institutional_pressure', 'NEUTRAL')
            volume_weighted_skew = cross_strike_analysis.get('volume_weighted_skew', 0.0)
            
            for signal in signals:
                signal.institutional_pressure = institutional_pressure
                signal.volume_weighted_skew = volume_weighted_skew
                
                # Enhanced logging for enriched signals
                logger.debug(f"[INSTITUTIONAL_FLOW] Enhanced signal {signal.strike}{signal.option_type[0]}: "
                           f"pressure={institutional_pressure}, skew={volume_weighted_skew:.3f}")
        
        # Sort signals by enhanced criteria
        if self.threshold_mode == 'relative':
            # Sort by dynamic confidence score first, then traditional confidence
            signals.sort(key=lambda s: (
                -(s.dynamic_confidence_score or 0),  # Higher dynamic score first
                {'EXTREME': 0, 'VERY_HIGH': 1, 'HIGH': 2, 'MODERATE': 3}.get(s.confidence, 999),
                -s.dollar_size
            ))
            logger.info(f"[INSTITUTIONAL_FLOW] Signals sorted by dynamic confidence scores")
        else:
            # Traditional sorting
            confidence_order = {'EXTREME': 0, 'VERY_HIGH': 1, 'HIGH': 2, 'MODERATE': 3}
            signals.sort(key=lambda s: (confidence_order.get(s.confidence, 999), -s.dollar_size))
            logger.info(f"[INSTITUTIONAL_FLOW] Signals sorted by traditional confidence levels")
        
        # Calculate analysis metadata
        analysis_duration = (datetime.now(timezone.utc) - analysis_start_time).total_seconds()
        
        # Generate comprehensive summary
        summary = self.summarize_institutional_activity(signals)
        
        # Compile comprehensive result
        result = {
            'signals': signals,
            'cross_strike_analysis': cross_strike_analysis,
            'summary': summary,
            'metadata': {
                'contract': contract,
                'current_price': current_price,
                'analysis_mode': self.threshold_mode,
                'strikes_analyzed': strikes_analyzed,
                'signals_detected': len(signals),
                'filter_pass_rate': (strikes_passed_filters / strikes_analyzed * 100) if strikes_analyzed > 0 else 0,
                'analysis_duration_seconds': analysis_duration,
                'timestamp': analysis_start_time.isoformat(),
                'cross_strike_enabled': self.enable_cross_strike,
                'premium_velocity_enabled': self.enable_premium_velocity,
                'baseline_manager_available': self.baseline_manager is not None
            }
        }
        
        logger.info(f"[INSTITUTIONAL_FLOW] Analysis complete for {contract}: "
                   f"{len(signals)} signals, {analysis_duration:.2f}s, "
                   f"{result['metadata']['filter_pass_rate']:.1f}% pass rate")
        
        # Log top signals for immediate visibility
        if signals:
            top_signals = signals[:3]  # Top 3 signals
            logger.info(f"[INSTITUTIONAL_FLOW] Top {len(top_signals)} signals:")
            for i, signal in enumerate(top_signals, 1):
                enhanced_desc = signal.get_enhanced_confidence_description() if signal.is_enhanced_analysis() else signal.confidence
                logger.info(f"[INSTITUTIONAL_FLOW] #{i}: {signal.strike}{signal.option_type[0]} "
                           f"${signal.dollar_size:,.0f} ({enhanced_desc})")
        
        return result
    
    def generate_trade_plan(self, signal: InstitutionalSignal, current_price: float) -> Dict:
        """
        Generate a specific trade plan based on institutional signal
        
        Args:
            signal: The institutional signal to trade
            current_price: Current underlying price
            
        Returns:
            Dictionary containing trade plan details
        """
        # Calculate entry and stops
        distance_to_target = abs(current_price - signal.target_price)
        
        if signal.direction == 'LONG':
            stop_loss = current_price - (distance_to_target * 0.5)
            take_profit = signal.target_price
        else:  # SHORT
            stop_loss = current_price + (distance_to_target * 0.5)
            take_profit = signal.target_price
        
        # Position sizing based on confidence
        confidence_multipliers = {
            'EXTREME': 3.0,
            'VERY_HIGH': 2.0,
            'HIGH': 1.5,
            'MODERATE': 1.0
        }
        
        size_multiplier = confidence_multipliers.get(signal.confidence, 1.0)
        
        trade_plan = {
            'signal': signal.to_dict(),
            'entry_price': current_price,
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'direction': signal.direction,
            'size_multiplier': size_multiplier,
            'risk_reward_ratio': 2.0,  # Fixed 1:2 risk/reward
            'notes': f"Following ${signal.dollar_size:,.0f} institutional flow at {signal.strike}"
        }
        
        return trade_plan
    
    def filter_actionable_signals(self, signals: List[InstitutionalSignal], 
                                 current_price: float,
                                 max_distance_percent: float = 2.0) -> List[InstitutionalSignal]:
        """
        Filter signals for actionable trades based on distance from current price
        
        Args:
            signals: List of institutional signals
            current_price: Current underlying price
            max_distance_percent: Maximum % distance from current price
            
        Returns:
            Filtered list of actionable signals
        """
        actionable = []
        
        for signal in signals:
            distance_percent = abs(signal.target_price - current_price) / current_price * 100
            
            if distance_percent <= max_distance_percent:
                actionable.append(signal)
            else:
                logger.debug(f"Signal at {signal.strike} too far ({distance_percent:.1f}%)")
        
        return actionable
    
    def summarize_institutional_activity(self, signals: List[InstitutionalSignal]) -> Dict:
        """
        Summarize overall institutional positioning
        
        Args:
            signals: List of institutional signals
            
        Returns:
            Summary statistics and positioning
        """
        if not signals:
            return {
                'total_signals': 0,
                'total_dollar_volume': 0,
                'call_dollar_volume': 0,
                'put_dollar_volume': 0,
                'net_positioning': 'NEUTRAL',
                'top_strikes': []
            }
        
        call_volume = sum(s.dollar_size for s in signals if s.option_type == 'CALL')
        put_volume = sum(s.dollar_size for s in signals if s.option_type == 'PUT')
        total_volume = call_volume + put_volume
        
        # Determine net positioning
        if total_volume > 0:
            call_percent = call_volume / total_volume * 100
            if call_percent > 65:
                net_positioning = 'BULLISH'
            elif call_percent < 35:
                net_positioning = 'BEARISH'
            else:
                net_positioning = 'MIXED'
        else:
            net_positioning = 'NEUTRAL'
        
        # Get top 5 strikes by dollar volume
        top_strikes = sorted(signals, key=lambda s: s.dollar_size, reverse=True)[:5]
        
        summary = {
            'total_signals': len(signals),
            'total_dollar_volume': total_volume,
            'call_dollar_volume': call_volume,
            'put_dollar_volume': put_volume,
            'net_positioning': net_positioning,
            'call_percentage': call_volume / total_volume * 100 if total_volume > 0 else 0,
            'put_percentage': put_volume / total_volume * 100 if total_volume > 0 else 0,
            'top_strikes': [
                {
                    'strike': s.strike,
                    'type': s.option_type,
                    'dollar_size': s.dollar_size,
                    'vol_oi_ratio': s.vol_oi_ratio,
                    'confidence': s.confidence
                }
                for s in top_strikes
            ]
        }
        
        return summary

# Integration with pipeline
def create_dead_simple_analyzer(config: Optional[Dict] = None) -> DeadSimpleVolumeSpike:
    """
    Enhanced Factory Function for Dead Simple Analyzer
    
    Creates analyzer instance with comprehensive configuration support
    
    Args:
        config: Configuration dictionary with options:
            - threshold_mode: 'absolute' (default) or 'relative'
            - baseline_db_path: Path to baseline database  
            - enable_cross_strike: Enable cross-strike analysis (default: True)
            - enable_premium_velocity: Enable premium velocity tracking (default: True)
            - min_vol_oi_ratio: Minimum vol/OI ratio (default: 10)
            - min_volume: Minimum volume threshold (default: 500)
            - min_dollar_size: Minimum dollar size (default: 100,000)
            
    Returns:
        Enhanced DeadSimpleVolumeSpike instance
    """
    logger.info(f"[FACTORY] Creating Dead Simple analyzer with config: {config}")
    
    # Create enhanced configuration with smart defaults
    enhanced_config = {
        # Analysis mode configuration
        'threshold_mode': 'absolute',  # Default to backward compatibility
        'enable_cross_strike': True,
        'enable_premium_velocity': True,
        
        # Traditional thresholds
        'min_vol_oi_ratio': 10,
        'min_volume': 500,
        'min_dollar_size': 100_000,
        
        # Enhanced features (optional)
        'baseline_db_path': None,
        'enable_logging': True
    }
    
    # Apply user configuration overrides
    if config:
        enhanced_config.update(config)
        logger.debug(f"[FACTORY] Applied config overrides: {config}")
    
    # Log configuration summary
    logger.info(f"[FACTORY] Enhanced Dead Simple configuration:")
    logger.info(f"[FACTORY] - Threshold mode: {enhanced_config['threshold_mode']}")
    logger.info(f"[FACTORY] - Cross-strike analysis: {enhanced_config['enable_cross_strike']}")
    logger.info(f"[FACTORY] - Premium velocity: {enhanced_config['enable_premium_velocity']}")
    logger.info(f"[FACTORY] - Vol/OI threshold: {enhanced_config['min_vol_oi_ratio']}")
    logger.info(f"[FACTORY] - Volume threshold: {enhanced_config['min_volume']}")
    logger.info(f"[FACTORY] - Dollar threshold: ${enhanced_config['min_dollar_size']:,}")
    
    try:
        analyzer = DeadSimpleVolumeSpike(enhanced_config)
        logger.info(f"[FACTORY] Enhanced Dead Simple analyzer created successfully")
        return analyzer
    except Exception as e:
        logger.error(f"[FACTORY] Failed to create analyzer: {e}")
        logger.info(f"[FACTORY] Falling back to basic configuration")
        # Fallback to basic configuration
        return DeadSimpleVolumeSpike({'threshold_mode': 'absolute'})

# Backward compatibility function (preserves existing API)
def create_enhanced_dead_simple_analyzer(config: Optional[Dict] = None) -> DeadSimpleVolumeSpike:
    """
    Create enhanced analyzer with relative analysis enabled by default
    
    Args:
        config: Enhanced configuration dictionary
        
    Returns:
        DeadSimpleVolumeSpike with enhanced features enabled
    """
    enhanced_config = {
        'threshold_mode': 'relative',  # Enhanced mode by default
        'enable_cross_strike': True,
        'enable_premium_velocity': True,
        'min_vol_oi_ratio': 8,  # Slightly more sensitive for relative mode
        'min_volume': 400,      # Slightly more sensitive for relative mode  
        'min_dollar_size': 75_000  # Slightly more sensitive for relative mode
    }
    
    if config:
        enhanced_config.update(config)
    
    logger.info(f"[ENHANCED_FACTORY] Creating enhanced analyzer in relative mode")
    return create_dead_simple_analyzer(enhanced_config)

# Configuration templates for common use cases
CONFIGURATION_TEMPLATES = {
    'conservative_absolute': {
        'threshold_mode': 'absolute',
        'min_vol_oi_ratio': 15,  # Higher threshold
        'min_volume': 750,       # Higher threshold
        'min_dollar_size': 150_000,  # Higher threshold
        'enable_cross_strike': True,
        'enable_premium_velocity': False
    },
    
    'aggressive_relative': {
        'threshold_mode': 'relative',
        'min_vol_oi_ratio': 5,   # Lower base threshold (dynamic will adjust)
        'min_volume': 250,       # Lower base threshold
        'min_dollar_size': 50_000,   # Lower threshold
        'enable_cross_strike': True,
        'enable_premium_velocity': True
    },
    
    'scalping_mode': {
        'threshold_mode': 'relative',
        'min_vol_oi_ratio': 3,   # Very sensitive
        'min_volume': 100,       # Very sensitive
        'min_dollar_size': 25_000,   # Lower for quick moves
        'enable_cross_strike': True,
        'enable_premium_velocity': True
    },
    
    'institutional_hunting': {
        'threshold_mode': 'relative', 
        'min_vol_oi_ratio': 20,  # High base (looking for extreme moves)
        'min_volume': 1000,      # Large volume only
        'min_dollar_size': 250_000,  # Large institutional size
        'enable_cross_strike': True,
        'enable_premium_velocity': True
    }
}

def create_configured_analyzer(template_name: str, 
                              custom_overrides: Optional[Dict] = None) -> DeadSimpleVolumeSpike:
    """
    Create analyzer using predefined configuration template
    
    Args:
        template_name: Name of configuration template
        custom_overrides: Additional configuration overrides
        
    Returns:
        Configured DeadSimpleVolumeSpike instance
    """
    if template_name not in CONFIGURATION_TEMPLATES:
        available_templates = list(CONFIGURATION_TEMPLATES.keys())
        logger.error(f"[TEMPLATE_FACTORY] Unknown template: {template_name}")
        logger.info(f"[TEMPLATE_FACTORY] Available templates: {available_templates}")
        raise ValueError(f"Unknown template: {template_name}. Available: {available_templates}")
    
    config = CONFIGURATION_TEMPLATES[template_name].copy()
    
    if custom_overrides:
        config.update(custom_overrides)
        logger.debug(f"[TEMPLATE_FACTORY] Applied custom overrides: {custom_overrides}")
    
    logger.info(f"[TEMPLATE_FACTORY] Creating analyzer with template: {template_name}")
    return create_dead_simple_analyzer(config)

# Example usage and testing
if __name__ == "__main__":
    # Example options data (would come from Barchart/Tradovate)
    sample_options = [
        {
            'strike': 21840,
            'optionType': 'PUT',
            'volume': 2750,
            'openInterest': 50,
            'lastPrice': 35.5,
            'expirationDate': '2024-01-10'
        },
        {
            'strike': 21900,
            'optionType': 'CALL',
            'volume': 1200,
            'openInterest': 100,
            'lastPrice': 42.0,
            'expirationDate': '2024-01-10'
        }
    ]
    
    # Initialize analyzer
    analyzer = DeadSimpleVolumeSpike()
    
    # Find institutional flow
    current_price = 21870
    signals = analyzer.find_institutional_flow(sample_options, current_price)
    
    # Display results
    print("\n=== DEAD Simple Strategy Analysis ===")
    print(f"Current Price: ${current_price:,.2f}")
    print(f"\nFound {len(signals)} institutional signals:")
    
    for signal in signals:
        print(f"\n{signal.strike}{signal.option_type[0]}:")
        print(f"  Vol/OI: {signal.vol_oi_ratio:.1f}x")
        print(f"  Dollar Size: ${signal.dollar_size:,.0f}")
        print(f"  Direction: {signal.direction} → {signal.target_price}")
        print(f"  Confidence: {signal.confidence}")
        
        # Generate trade plan
        trade_plan = analyzer.generate_trade_plan(signal, current_price)
        print(f"  Entry: ${trade_plan['entry_price']}")
        print(f"  Stop: ${trade_plan['stop_loss']}")
        print(f"  Target: ${trade_plan['take_profit']}")
    
    # Summary
    summary = analyzer.summarize_institutional_activity(signals)
    print(f"\n=== Institutional Summary ===")
    print(f"Total Dollar Volume: ${summary['total_dollar_volume']:,.0f}")
    print(f"Net Positioning: {summary['net_positioning']}")
    print(f"Call %: {summary['call_percentage']:.1f}%")
    print(f"Put %: {summary['put_percentage']:.1f}%")