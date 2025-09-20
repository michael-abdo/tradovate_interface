#!/usr/bin/env python3
"""
0DTE Options Expiration Validator

Validates that options contracts actually expire today (0 Days to Expiration)
using Selenium-based web scraping to check actual expiration dates on Barchart.

This module extends the existing EOD symbol generation logic to ensure
contracts are truly 0DTE by validating against live market data.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys
import os

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from common_utils import get_logger, log_and_return_false, log_and_return_none

# Add project root for test_utils
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)
from tasks.test_utils import setup_chrome_driver

class ExpirationValidator:
    """
    Selenium-based validator for 0DTE options contracts
    
    Verifies that generated contract symbols actually expire today
    by checking expiration dates on Barchart.com options pages.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the expiration validator
        
        Args:
            headless: Run browser in headless mode for production use
        """
        self.headless = headless
        self.driver = None
        self.wait_time = 10  # seconds
        self.logger = get_logger()
        
        # Contract prefixes to try in order
        self.CONTRACT_PREFIXES = ['MC', 'MM', 'MQ']
        
        # Futures month codes
        self.MONTH_CODES = {
            1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
            7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
        }
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        Setup Chrome WebDriver with appropriate options for validation
        """
        # Use canonical implementation from test_utils
        return setup_chrome_driver(self.headless)
    
    def _generate_contract_symbol(self, prefix: str, target_date: datetime = None) -> str:
        """
        Generate contract symbol for given prefix and date
        
        Args:
            prefix: Contract prefix (MC, MM, MQ)
            target_date: Date to generate symbol for (defaults to today)
            
        Returns:
            Contract symbol (e.g., "MC1M25")
        """
        if target_date is None:
            target_date = datetime.now()
        
        # Calculate day code (1-5 for Mon-Fri)
        if target_date.weekday() < 5:  # Monday=0 to Friday=4
            day_code = target_date.weekday() + 1  # Convert to 1-5
        else:
            # Weekend: use next Monday
            days_until_monday = (7 - target_date.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            target_date = target_date + timedelta(days=days_until_monday)
            day_code = 1
        
        # Get month and year codes
        month_code = self.MONTH_CODES[target_date.month]
        year_code = str(target_date.year)[-2:]  # Last 2 digits
        
        return f"{prefix}{day_code}{month_code}{year_code}"
    
    def find_0dte_symbol(self, target_date: datetime = None) -> Optional[str]:
        """
        Find a valid 0DTE symbol by trying different contract prefixes
        
        Args:
            target_date: Target expiration date (defaults to today)
            
        Returns:
            Valid 0DTE symbol or None if no valid symbol found
        """
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info(f"🔍 Searching for 0DTE symbol for {target_date.strftime('%Y-%m-%d')}")
        
        for prefix in self.CONTRACT_PREFIXES:
            try:
                symbol = self._generate_contract_symbol(prefix, target_date)
                self.logger.debug(f"Testing symbol: {symbol}")
                
                if self.validate_is_0dte(symbol, target_date):
                    self.logger.info(f"✅ Found valid 0DTE symbol: {symbol}")
                    return symbol
                else:
                    self.logger.debug(f"❌ Symbol {symbol} is not 0DTE")
                    
            except Exception as e:
                self.logger.warning(f"Error testing prefix {prefix}: {e}")
                continue
        
        self.logger.warning(f"⚠️  No valid 0DTE symbol found for {target_date.strftime('%Y-%m-%d')}")
        return None
    
    def validate_is_0dte(self, symbol: str, target_date: datetime = None) -> bool:
        """
        Validate that a specific symbol expires today (0DTE)
        
        Args:
            symbol: Contract symbol to validate
            target_date: Expected expiration date (defaults to today)
            
        Returns:
            True if symbol expires on target_date, False otherwise
        """
        if target_date is None:
            target_date = datetime.now()
        
        try:
            # Setup driver if not already done
            if self.driver is None:
                self.driver = self.setup_driver()
            
            # Navigate to options page for this symbol
            url = f"https://www.barchart.com/futures/quotes/NQM25/options/{symbol}?futuresOptionsView=merged"
            
            self.logger.debug(f"Validating {symbol} at: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.wait_time)
            
            # Look for expiration date information
            expiration_date = self._extract_expiration_date()
            
            if expiration_date:
                # Check if expiration date matches target date
                target_date_str = target_date.strftime('%Y-%m-%d')
                is_0dte = expiration_date == target_date_str
                
                self.logger.debug(f"Symbol {symbol}: expires {expiration_date}, target {target_date_str}, 0DTE: {is_0dte}")
                return is_0dte
            else:
                self.logger.warning(f"Could not determine expiration date for {symbol}")
                return False
                
        except Exception as e:
            raise  # Let decorator handle it
    
    @log_and_return_none(operation="_extract_expiration_date")
    def _extract_expiration_date(self) -> Optional[str]:
        """
        Extract expiration date from current Barchart options page
        
        Returns:
            Expiration date as YYYY-MM-DD string or None if not found
        """
        try:
            # Multiple selectors to try for expiration date
            expiration_selectors = [
                # Header area
                '.bc-table__header .expiration-date',
                '.option-chain-header .expiration',
                '.futures-options-header .expiry-date',
                
                # Table metadata
                '.table-metadata .expiration',
                '.option-info .expiry',
                
                # Page title or breadcrumb area
                '.page-title .expiration',
                '.breadcrumb .expiry',
                
                # Generic patterns
                '[data-expiration]',
                '.expiry-date',
                '.expiration-date'
            ]
            
            for selector in expiration_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        date_text = element.text.strip()
                        if date_text:
                            # Try to parse the date
                            parsed_date = self._parse_date_string(date_text)
                            if parsed_date:
                                return parsed_date
                except Exception:
                    continue
            
            # Fallback: look for date patterns in page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            return self._extract_date_from_text(page_text)
            
        except Exception as e:
            raise  # Let decorator handle it
    
    def _parse_date_string(self, date_text: str) -> Optional[str]:
        """
        Parse various date string formats to YYYY-MM-DD
        
        Args:
            date_text: Raw date text from page
            
        Returns:
            Standardized date string or None if unparseable
        """
        import re
        
        # Common date patterns
        patterns = [
            # 2025-01-15, 2025/01/15
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            # 01/15/2025, 01-15-2025
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # Jan 15, 2025 or January 15, 2025
            r'([A-Za-z]{3,})\s+(\d{1,2}),?\s+(\d{4})'
        ]
        
        month_names = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
            'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
            'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        for pattern in patterns:
            match = re.search(pattern, date_text.lower())
            if match:
                try:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        if groups[0].isdigit() and len(groups[0]) == 4:
                            # YYYY-MM-DD format
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        elif groups[2].isdigit() and len(groups[2]) == 4:
                            if groups[0].isdigit():
                                # MM-DD-YYYY format
                                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                            else:
                                # Month name format
                                month_str = groups[0].lower()
                                if month_str in month_names:
                                    month = month_names[month_str]
                                    day, year = int(groups[1]), int(groups[2])
                                else:
                                    continue
                        else:
                            continue
                        
                        # Validate date
                        if 1 <= month <= 12 and 1 <= day <= 31 and 2020 <= year <= 2030:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                            
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """
        Extract expiration date from general page text
        
        Args:
            text: Full page text
            
        Returns:
            Expiration date string or None
        """
        import re
        
        # Look for phrases like "Expires: 2025-01-15" or "Expiration: Jan 15, 2025"
        expiry_patterns = [
            r'expir(?:es|ation)[:\s]+([^\n\r,;]+)',
            r'exp(?:iry)?[:\s]+([^\n\r,;]+)',
            r'settl(?:es|ement)[:\s]+([^\n\r,;]+)'
        ]
        
        for pattern in expiry_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                date_candidate = match.group(1).strip()
                parsed_date = self._parse_date_string(date_candidate)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.debug(f"Error cleaning up driver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience functions for easy integration
def find_0dte_symbol(target_date: datetime = None, headless: bool = True) -> Optional[str]:
    """
    Convenience function to find a valid 0DTE symbol
    
    Args:
        target_date: Target expiration date (defaults to today)
        headless: Run browser in headless mode
        
    Returns:
        Valid 0DTE symbol or None
    """
    with ExpirationValidator(headless=headless) as validator:
        return validator.find_0dte_symbol(target_date)


def validate_is_0dte(symbol: str, target_date: datetime = None, headless: bool = True) -> bool:
    """
    Convenience function to validate if symbol is 0DTE
    
    Args:
        symbol: Contract symbol to validate
        target_date: Expected expiration date (defaults to today)
        headless: Run browser in headless mode
        
    Returns:
        True if symbol expires on target_date
    """
    with ExpirationValidator(headless=headless) as validator:
        return validator.validate_is_0dte(symbol, target_date)