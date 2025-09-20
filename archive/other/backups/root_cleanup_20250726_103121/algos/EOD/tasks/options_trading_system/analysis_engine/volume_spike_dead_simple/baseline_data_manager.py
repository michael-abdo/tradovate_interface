#!/usr/bin/env python3
"""
Baseline Data Manager for Enhanced Dead Simple Strategy
Manages historical data collection and relative threshold calculations
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import sys
import os

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from common_utils import get_logger, log_and_return_false, log_and_return_none

logger = get_logger()

class BaseDataClass:
    """Base class for dataclasses with common to_dict method"""
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class VolumeStats(BaseDataClass):
    """Historical volume statistics for a strike"""
    daily_volume: int
    twenty_day_avg: float
    rolling_std: float
    percentile_rank: float  # Where today's volume ranks vs history

@dataclass 
class PremiumVelocity(BaseDataClass):
    """Premium velocity tracking for a strike"""
    fifteen_min_change: float
    hourly_baseline: float
    velocity_ratio: float  # 15min change / hourly baseline

@dataclass
class MarketContext(BaseDataClass):
    """Overall market context for threshold adjustments"""
    vix_level: Optional[float]
    volatility_factor: float  # Market volatility adjustment (1.0 = normal)
    time_to_expiry: int  # Days to expiration
    session_volume_factor: float  # Intraday volume pattern adjustment

class BaselineDataManager:
    """
    Manages historical baseline data for relative threshold calculations
    
    Responsibilities:
    1. Collect and store daily volume/premium data
    2. Calculate 20-day rolling averages
    3. Provide relative threshold calculations
    4. Handle smart defaults when insufficient data
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize baseline data manager with optional custom database path"""
        self.db_path = db_path or self._get_default_db_path()
        self.cache = {}  # In-memory cache for fast access
        
        logger.info(f"[BASELINE_MANAGER] Initializing with database: {self.db_path}")
        self._init_database()
        
    def _get_default_db_path(self) -> str:
        """Get default database path in volume_spike_dead_simple directory"""
        base_dir = Path(__file__).parent
        db_path = base_dir / "baseline_data.db"
        logger.debug(f"[BASELINE_MANAGER] Default database path: {db_path}")
        return str(db_path)
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        logger.info(f"[BASELINE_MANAGER] Creating database tables")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Daily volume data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_volume_data (
                    date TEXT,
                    contract TEXT,
                    strike REAL,
                    option_type TEXT,
                    volume INTEGER,
                    open_interest INTEGER,
                    premium REAL,
                    PRIMARY KEY (date, contract, strike, option_type)
                )
            """)
            
            # Premium velocity tracking table  
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS premium_velocity_data (
                    timestamp TEXT,
                    contract TEXT,
                    strike REAL,
                    option_type TEXT,
                    premium REAL,
                    volume INTEGER,
                    PRIMARY KEY (timestamp, contract, strike, option_type)
                )
            """)
            
            # Market context table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_context_data (
                    date TEXT,
                    contract TEXT,
                    vix_level REAL,
                    volatility_factor REAL,
                    time_to_expiry INTEGER,
                    session_volume_factor REAL,
                    PRIMARY KEY (date, contract)
                )
            """)
            
            conn.commit()
            logger.info(f"[BASELINE_MANAGER] Database tables created successfully")
    
    @log_and_return_false(operation="store_daily_snapshot")
    def store_daily_snapshot(self, contract: str, options_data: List[Dict]) -> bool:
        """
        Store daily snapshot of options data for baseline calculations
        
        Args:
            contract: Contract identifier (e.g., 'MC7M25')
            options_data: List of option strike data
            
        Returns:
            Success status
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        stored_count = 0
        
        logger.info(f"[BASELINE_MANAGER] Storing daily snapshot for {contract} on {date_str}")
        logger.debug(f"[BASELINE_MANAGER] Processing {len(options_data)} option strikes")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for strike_data in options_data:
                    try:
                        strike = float(strike_data.get('strike', 0))
                        option_type = str(strike_data.get('optionType', '')).upper()
                        volume = int(strike_data.get('volume', 0))
                        open_interest = int(strike_data.get('openInterest', 0))
                        premium = float(strike_data.get('lastPrice', 0))
                        
                        # Skip invalid data
                        if strike == 0 or not option_type:
                            logger.debug(f"[BASELINE_MANAGER] Skipping invalid strike: {strike_data}")
                            continue
                            
                        cursor.execute("""
                            INSERT OR REPLACE INTO daily_volume_data 
                            (date, contract, strike, option_type, volume, open_interest, premium)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (date_str, contract, strike, option_type, volume, open_interest, premium))
                        
                        stored_count += 1
                        
                        if stored_count % 50 == 0:
                            logger.debug(f"[BASELINE_MANAGER] Stored {stored_count} strikes...")
                            
                    except Exception as e:
                        logger.warning(f"[BASELINE_MANAGER] Error storing strike {strike_data}: {e}")
                        continue
                
                conn.commit()
                
            logger.info(f"[BASELINE_MANAGER] Successfully stored {stored_count} strikes for {contract}")
            return True
            
        except Exception as e:
            raise  # Let decorator handle it
    
    @log_and_return_none(operation="get_volume_stats")
    def get_volume_stats(self, contract: str, strike: float, option_type: str) -> Optional[VolumeStats]:
        """
        Get volume statistics for a specific strike
        
        Args:
            contract: Contract identifier
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            
        Returns:
            VolumeStats if sufficient data available, None otherwise
        """
        cache_key = f"{contract}_{strike}_{option_type}_volume"
        
        # Check cache first
        if cache_key in self.cache:
            logger.debug(f"[BASELINE_MANAGER] Volume stats cache hit for {strike}{option_type[0]}")
            return self.cache[cache_key]
        
        logger.debug(f"[BASELINE_MANAGER] Calculating volume stats for {strike}{option_type[0]}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get last 20 days of volume data
                cursor.execute("""
                    SELECT volume FROM daily_volume_data 
                    WHERE contract = ? AND strike = ? AND option_type = ?
                    ORDER BY date DESC 
                    LIMIT 20
                """, (contract, strike, option_type))
                
                rows = cursor.fetchall()
                
                if len(rows) < 5:  # Need at least 5 days of data
                    logger.debug(f"[BASELINE_MANAGER] Insufficient data for {strike}{option_type[0]} (only {len(rows)} days)")
                    return None
                
                volumes = [row[0] for row in rows]
                daily_volume = volumes[0]  # Most recent (today's) volume
                twenty_day_avg = statistics.mean(volumes)
                rolling_std = statistics.stdev(volumes) if len(volumes) > 1 else 0.0
                
                # Calculate percentile rank
                sorted_volumes = sorted(volumes)
                percentile_rank = (sorted_volumes.index(daily_volume) / len(sorted_volumes)) * 100
                
                stats = VolumeStats(
                    daily_volume=daily_volume,
                    twenty_day_avg=twenty_day_avg,
                    rolling_std=rolling_std,
                    percentile_rank=percentile_rank
                )
                
                # Cache the result
                self.cache[cache_key] = stats
                
                logger.debug(f"[BASELINE_MANAGER] Volume stats for {strike}{option_type[0]}: "
                           f"daily={daily_volume}, avg={twenty_day_avg:.1f}, "
                           f"percentile={percentile_rank:.1f}%")
                
                return stats
                
        except Exception as e:
            raise  # Let decorator handle it
    
    def calculate_relative_volume_ratio(self, current_volume: int, volume_stats: VolumeStats) -> float:
        """
        Calculate relative volume ratio vs historical baseline
        
        Args:
            current_volume: Current volume for the strike
            volume_stats: Historical volume statistics
            
        Returns:
            Relative volume ratio (current / baseline)
        """
        if volume_stats.twenty_day_avg == 0:
            logger.warning(f"[BASELINE_MANAGER] Zero baseline average, using current volume")
            return float(current_volume)
        
        relative_ratio = current_volume / volume_stats.twenty_day_avg
        
        logger.debug(f"[BASELINE_MANAGER] Relative volume ratio: {current_volume} / {volume_stats.twenty_day_avg:.1f} = {relative_ratio:.2f}x")
        
        return relative_ratio
    
    def get_market_context(self, contract: str) -> MarketContext:
        """
        Get current market context for threshold adjustments
        
        Args:
            contract: Contract identifier
            
        Returns:
            MarketContext with adjustment factors
        """
        cache_key = f"{contract}_market_context"
        
        if cache_key in self.cache:
            logger.debug(f"[BASELINE_MANAGER] Market context cache hit for {contract}")
            return self.cache[cache_key]
        
        logger.debug(f"[BASELINE_MANAGER] Calculating market context for {contract}")
        
        try:
            # Calculate time to expiry (simplified - extract from contract)
            # MC7M25 = July 2025, MC1M25 = January 2025, etc.
            time_to_expiry = self._calculate_time_to_expiry(contract)
            
            # Time decay factor: closer to expiry = higher sensitivity
            time_factor = max(0.5, min(2.0, 7.0 / max(1, time_to_expiry)))
            
            # Default market context (would be enhanced with real VIX data)
            context = MarketContext(
                vix_level=None,  # Would fetch from API in production
                volatility_factor=1.0,  # Normal volatility
                time_to_expiry=time_to_expiry,
                session_volume_factor=1.0  # Normal session volume
            )
            
            # Cache the result
            self.cache[cache_key] = context
            
            logger.debug(f"[BASELINE_MANAGER] Market context for {contract}: "
                        f"time_to_expiry={time_to_expiry}, volatility_factor={context.volatility_factor}")
            
            return context
            
        except Exception as e:
            logger.error(f"[BASELINE_MANAGER] Error calculating market context: {e}")
            # Return safe defaults
            return MarketContext(
                vix_level=None,
                volatility_factor=1.0,
                time_to_expiry=7,
                session_volume_factor=1.0
            )
    
    def _calculate_time_to_expiry(self, contract: str) -> int:
        """Calculate days to expiry from contract identifier"""
        try:
            # Extract month/year from contract (e.g., MC7M25 = July 2025)
            # This is a simplified calculation - would be enhanced with real expiry dates
            month_map = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                        '7': 7, '8': 8, '9': 9, '0': 10, 'N': 11, 'Z': 12}
            
            if len(contract) >= 5:
                month_char = contract[2]  # Third character
                year_str = contract[3:5]  # Last two characters
                
                if month_char in month_map:
                    month = month_map[month_char]
                    year = 2000 + int(year_str)
                    
                    # Approximate expiry calculation
                    today = datetime.now()
                    expiry_approx = datetime(year, month, 15)  # Assume mid-month expiry
                    
                    days_to_expiry = (expiry_approx - today).days
                    return max(1, days_to_expiry)
            
            # Default to 7 days if parsing fails
            return 7
            
        except Exception as e:
            logger.warning(f"[BASELINE_MANAGER] Error calculating time to expiry for {contract}: {e}")
            return 7
    
    @log_and_return_false(operation="has_sufficient_baseline_data")
    def has_sufficient_baseline_data(self, contract: str, min_days: int = 5) -> bool:
        """
        Check if we have sufficient baseline data for relative calculations
        
        Args:
            contract: Contract identifier
            min_days: Minimum days of data required
            
        Returns:
            True if sufficient data available
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT date) as day_count
                    FROM daily_volume_data 
                    WHERE contract = ?
                """, (contract,))
                
                result = cursor.fetchone()
                day_count = result[0] if result else 0
                
                has_sufficient = day_count >= min_days
                
                logger.debug(f"[BASELINE_MANAGER] Baseline data check for {contract}: "
                           f"{day_count} days available, minimum required: {min_days}, sufficient: {has_sufficient}")
                
                return has_sufficient
                
        except Exception as e:
            raise  # Let decorator handle it
    
    def get_smart_defaults(self, strike_data: Dict) -> Dict:
        """
        Generate smart default thresholds when insufficient historical data
        
        Args:
            strike_data: Current strike information
            
        Returns:
            Dictionary with default threshold calculations
        """
        volume = int(strike_data.get('volume', 0))
        open_interest = int(strike_data.get('openInterest', 0))
        
        # Smart defaults based on current session patterns
        estimated_daily_avg = max(100, volume * 0.3)  # Assume current is 3x normal
        relative_volume_ratio = volume / estimated_daily_avg if estimated_daily_avg > 0 else 1.0
        
        defaults = {
            'relative_volume_ratio': relative_volume_ratio,
            'confidence_multiplier': 1.0,  # No historical confidence boost
            'baseline_source': 'smart_defaults',
            'estimated_baseline': estimated_daily_avg
        }
        
        logger.debug(f"[BASELINE_MANAGER] Smart defaults generated: {defaults}")
        
        return defaults

# Factory function for pipeline integration
def create_baseline_manager(config: Optional[Dict] = None) -> BaselineDataManager:
    """Factory function to create baseline manager instance"""
    db_path = None
    if config and 'baseline_db_path' in config:
        db_path = config['baseline_db_path']
    
    logger.info(f"[BASELINE_MANAGER] Creating baseline manager with config: {config}")
    return BaselineDataManager(db_path)