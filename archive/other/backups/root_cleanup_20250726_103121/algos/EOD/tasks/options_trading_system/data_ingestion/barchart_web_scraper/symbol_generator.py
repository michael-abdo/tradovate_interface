#!/usr/bin/env python3
"""
Options Contract Symbol Generator

Enhanced symbol generation for NQ options contracts with support for:
- Multiple contract types (MC, MM, MQ)
- 0DTE validation
- Fallback mechanisms
- Weekend/holiday handling

Builds on the existing EOD contract logic but adds validation and robustness.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from common_utils import get_logger, log_and_return_false

from .expiration_validator import ExpirationValidator


class OptionsSymbolGenerator:
    """
    Enhanced options symbol generator with 0DTE validation
    
    Generates and validates options contract symbols, ensuring they
    actually expire on the target date (0DTE functionality).
    """
    
    def __init__(self, validate_0dte: bool = True, headless: bool = True):
        """
        Initialize the symbol generator
        
        Args:
            validate_0dte: Whether to validate symbols are actually 0DTE
            headless: Run validation in headless mode
        """
        self.validate_0dte = validate_0dte
        self.headless = headless
        self.logger = get_logger()
        
        # Contract type prefixes in priority order
        self.CONTRACT_PREFIXES = [
            'MC',  # Micro E-mini Nasdaq-100 futures options (primary)
            'MM',  # E-mini Nasdaq-100 futures options (fallback)
            'MQ'   # Alternative/quarterly options (rare fallback)
        ]
        
        # Futures month codes (standard CME codes)
        self.MONTH_CODES = {
            1: 'F',   # January
            2: 'G',   # February  
            3: 'H',   # March
            4: 'J',   # April
            5: 'K',   # May
            6: 'M',   # June
            7: 'N',   # July
            8: 'Q',   # August
            9: 'U',   # September
            10: 'V',  # October
            11: 'X',  # November
            12: 'Z'   # December
        }
        
        # Day codes for daily options
        self.DAY_CODES = {
            0: 1,  # Monday -> 1
            1: 2,  # Tuesday -> 2
            2: 3,  # Wednesday -> 3
            3: 4,  # Thursday -> 4
            4: 5,  # Friday -> 5
            # Weekends handled separately
        }
    
    def generate_0dte_symbol(self, target_date: datetime = None) -> Optional[str]:
        """
        Generate a validated 0DTE options symbol for the target date
        
        Args:
            target_date: Target expiration date (defaults to today)
            
        Returns:
            Valid 0DTE symbol or None if no valid symbol found
        """
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info(f"🎯 Generating 0DTE symbol for {target_date.strftime('%Y-%m-%d %A')}")
        
        # Handle weekends by shifting to next Monday
        adjusted_date = self._adjust_for_weekends(target_date)
        
        if adjusted_date != target_date:
            self.logger.info(f"📅 Weekend detected, shifted to {adjusted_date.strftime('%Y-%m-%d %A')}")
        
        # Try each contract prefix until we find a valid 0DTE symbol
        for prefix in self.CONTRACT_PREFIXES:
            try:
                symbol = self._generate_symbol_for_prefix(prefix, adjusted_date)
                self.logger.debug(f"Generated candidate symbol: {symbol}")
                
                # Validate if 0DTE validation is enabled
                if self.validate_0dte:
                    if self._validate_symbol_is_0dte(symbol, adjusted_date):
                        self.logger.info(f"✅ Valid 0DTE symbol found: {symbol}")
                        return symbol
                    else:
                        self.logger.debug(f"❌ Symbol {symbol} failed 0DTE validation")
                        continue
                else:
                    # Return first generated symbol if validation disabled
                    self.logger.info(f"📝 Generated symbol (validation disabled): {symbol}")
                    return symbol
                    
            except Exception as e:
                self.logger.warning(f"Error generating symbol with prefix {prefix}: {e}")
                continue
        
        self.logger.error(f"⚠️  No valid 0DTE symbol found for {adjusted_date.strftime('%Y-%m-%d')}")
        return None
    
    def generate_symbol_with_fallbacks(self, target_date: datetime = None) -> Dict[str, any]:
        """
        Generate symbol with comprehensive fallback information
        
        Args:
            target_date: Target expiration date (defaults to today)
            
        Returns:
            Dict with symbol, metadata, and fallback information
        """
        if target_date is None:
            target_date = datetime.now()
        
        result = {
            'requested_date': target_date.strftime('%Y-%m-%d'),
            'is_weekend': target_date.weekday() >= 5,
            'symbol': None,
            'contract_type': None,
            'actual_expiry_date': None,
            'is_0dte': False,
            'fallbacks_tried': [],
            'validation_enabled': self.validate_0dte
        }
        
        # Adjust for weekends
        adjusted_date = self._adjust_for_weekends(target_date)
        result['adjusted_date'] = adjusted_date.strftime('%Y-%m-%d')
        result['date_adjusted'] = adjusted_date != target_date
        
        # Try each contract prefix
        for prefix in self.CONTRACT_PREFIXES:
            try:
                symbol = self._generate_symbol_for_prefix(prefix, adjusted_date)
                
                fallback_info = {
                    'prefix': prefix,
                    'symbol': symbol,
                    'validated': False,
                    'is_0dte': False,
                    'error': None
                }
                
                # Validate if enabled
                if self.validate_0dte:
                    try:
                        is_valid = self._validate_symbol_is_0dte(symbol, adjusted_date)
                        fallback_info['validated'] = True
                        fallback_info['is_0dte'] = is_valid
                        
                        if is_valid and result['symbol'] is None:
                            # First valid symbol found
                            result['symbol'] = symbol
                            result['contract_type'] = prefix
                            result['actual_expiry_date'] = adjusted_date.strftime('%Y-%m-%d')
                            result['is_0dte'] = True
                            
                    except Exception as e:
                        fallback_info['error'] = str(e)
                else:
                    # Use first symbol if validation disabled
                    if result['symbol'] is None:
                        result['symbol'] = symbol
                        result['contract_type'] = prefix
                        result['actual_expiry_date'] = adjusted_date.strftime('%Y-%m-%d')
                        result['is_0dte'] = False  # Unknown without validation
                
                result['fallbacks_tried'].append(fallback_info)
                
            except Exception as e:
                result['fallbacks_tried'].append({
                    'prefix': prefix,
                    'symbol': None,
                    'validated': False,
                    'is_0dte': False,
                    'error': str(e)
                })
        
        return result
    
    def get_legacy_eod_symbol(self, target_date: datetime = None) -> str:
        """
        Get symbol using legacy EOD logic (MC prefix only, no validation)
        
        Compatible with existing BarchartAPIComparator.get_eod_contract_symbol()
        
        Args:
            target_date: Target date (defaults to today)
            
        Returns:
            Symbol using legacy logic
        """
        if target_date is None:
            target_date = datetime.now()
        
        # Use legacy logic: MC prefix only, weekend adjustment
        adjusted_date = self._adjust_for_weekends(target_date)
        return self._generate_symbol_for_prefix('MC', adjusted_date)
    
    def _adjust_for_weekends(self, target_date: datetime) -> datetime:
        """
        Adjust date for weekends (shift to next Monday)
        
        Args:
            target_date: Original target date
            
        Returns:
            Adjusted date (Monday if weekend)
        """
        if target_date.weekday() >= 5:  # Saturday=5, Sunday=6
            days_until_monday = (7 - target_date.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return target_date + timedelta(days=days_until_monday)
        
        return target_date
    
    def _generate_symbol_for_prefix(self, prefix: str, target_date: datetime) -> str:
        """
        Generate symbol for specific prefix and date
        
        Args:
            prefix: Contract prefix (MC, MM, MQ)
            target_date: Target expiration date
            
        Returns:
            Generated symbol (e.g., "MC1M25")
        """
        # Calculate day code
        if target_date.weekday() < 5:  # Weekday
            day_code = target_date.weekday() + 1  # Monday=1, ..., Friday=5
        else:
            # Should not happen due to weekend adjustment, but handle anyway
            day_code = 1  # Default to Monday
        
        # Get month and year codes
        month_code = self.MONTH_CODES[target_date.month]
        year_code = str(target_date.year)[-2:]  # Last 2 digits
        
        return f"{prefix}{day_code}{month_code}{year_code}"
    
    @log_and_return_false(operation="_validate_symbol_is_0dte")
    def _validate_symbol_is_0dte(self, symbol: str, target_date: datetime) -> bool:
        """
        Validate that symbol actually expires on target date
        
        Args:
            symbol: Symbol to validate
            target_date: Expected expiration date
            
        Returns:
            True if symbol expires on target_date
        """
        try:
            with ExpirationValidator(headless=self.headless) as validator:
                return validator.validate_is_0dte(symbol, target_date)
        except Exception as e:
            raise  # Let decorator handle it


class LegacySymbolGenerator:
    """
    Legacy symbol generator for backward compatibility
    
    Mimics the existing BarchartAPIComparator.get_eod_contract_symbol()
    behavior exactly.
    """
    
    @staticmethod
    def get_eod_contract_symbol() -> str:
        """
        Legacy EOD contract symbol generation
        
        Maintains exact compatibility with existing system.
        
        Returns:
            EOD contract symbol using legacy logic
        """
        now = datetime.now()
        
        # Futures month codes
        month_codes = {
            1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
            7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
        }
        
        # Handle weekends (use next Monday)
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            expiry_date = now + timedelta(days=days_until_monday)
            day_code = 1  # Monday
        else:
            # Weekday: use today
            expiry_date = now  
            day_code = now.weekday() + 1  # Monday=1, ..., Friday=5
        
        # Build symbol: MC + day_code + month_code + year_code
        month_code = month_codes[expiry_date.month]
        year_code = str(expiry_date.year)[-2:]
        
        return f"MC{day_code}{month_code}{year_code}"


# Convenience functions for easy integration
def generate_0dte_symbol(target_date: datetime = None, validate: bool = True, headless: bool = True) -> Optional[str]:
    """
    Convenience function to generate 0DTE symbol
    
    Args:
        target_date: Target expiration date (defaults to today)
        validate: Whether to validate the symbol is actually 0DTE
        headless: Run validation in headless mode
        
    Returns:
        Valid 0DTE symbol or None
    """
    generator = OptionsSymbolGenerator(validate_0dte=validate, headless=headless)
    return generator.generate_0dte_symbol(target_date)


def get_symbol_with_fallbacks(target_date: datetime = None, validate: bool = True, headless: bool = True) -> Dict[str, any]:
    """
    Convenience function to get symbol with comprehensive fallback info
    
    Args:
        target_date: Target expiration date (defaults to today)
        validate: Whether to validate symbols are actually 0DTE
        headless: Run validation in headless mode
        
    Returns:
        Dict with symbol and detailed fallback information
    """
    generator = OptionsSymbolGenerator(validate_0dte=validate, headless=headless)
    return generator.generate_symbol_with_fallbacks(target_date)


def get_legacy_eod_symbol() -> str:
    """
    Get symbol using legacy EOD logic for backward compatibility
    
    Returns:
        Symbol using exact legacy logic
    """
    return LegacySymbolGenerator.get_eod_contract_symbol()