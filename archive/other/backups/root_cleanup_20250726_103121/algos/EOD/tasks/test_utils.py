#!/usr/bin/env python3
"""
Canonical test utilities for the options trading system.
Eliminates duplicated test helper functions across the codebase.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_project_root() -> str:
    """
    Get the project root directory (EOD).
    Works from any file location within the project.
    
    Returns:
        Absolute path to project root
    """
    current_file = os.path.abspath(__file__)
    # Navigate up from tasks/test_utils.py to project root
    return os.path.dirname(os.path.dirname(current_file))


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()


def save_evidence(validation_results: Dict[str, Any], evidence_filename: str = "evidence.json") -> None:
    """
    Save validation evidence to JSON file.
    
    Args:
        validation_results: Dictionary containing validation results
        evidence_filename: Name of the evidence file (default: evidence.json)
    """
    # Get the calling module's directory
    import inspect
    caller_frame = inspect.stack()[1]
    caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))
    
    evidence_path = os.path.join(caller_dir, evidence_filename)
    
    with open(evidence_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\nEvidence saved to: {evidence_path}")


def estimate_underlying_price(contracts: List[Dict[str, Any]]) -> float:
    """
    Estimate underlying price from option contracts.
    Used when underlying price is not directly available.
    
    Args:
        contracts: List of option contract dictionaries
        
    Returns:
        Estimated underlying price
    """
    if not contracts:
        return 21376.75  # Default NQ price
    
    # Try to get from contract metadata first
    for contract in contracts[:10]:  # Check first 10 contracts
        if contract.get('underlying_price'):
            return float(contract['underlying_price'])
    
    # Fallback: estimate from strike distribution
    strikes = [float(c.get('strike', 0)) for c in contracts if c.get('strike')]
    if strikes:
        return sum(strikes) / len(strikes)
    
    return 21376.75  # Final fallback


def setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with appropriate options for web scraping.
    
    Args:
        headless: Whether to run browser in headless mode
        
    Returns:
        Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
        
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Speed up loading
    
    # User agent to avoid detection
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert value to float, handling various formats and edge cases.
    
    Args:
        value: Value to convert (string, number, or None)
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None or value == '' or value in ['N/A', '-', '--']:
        return None
    
    try:
        # Handle string values with currency/formatting
        if isinstance(value, str):
            clean_value = value.replace('$', '').replace(',', '').replace('%', '')
            if clean_value in ['-', '--', '', 'N/A']:
                return None
            return float(clean_value)
        else:
            return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """
    Safely convert value to int, handling various formats and edge cases.
    
    Args:
        value: Value to convert (string, number, or None)
        
    Returns:
        Int value or None if conversion fails
    """
    if value is None or value == '' or value in ['N/A', '-', '--']:
        return None
    
    try:
        # Handle string values with formatting
        if isinstance(value, str):
            clean_value = value.replace(',', '')
            if clean_value in ['-', '--', '', 'N/A']:
                return None
            # Convert through float to handle decimals
            return int(float(clean_value))
        else:
            return int(float(value))
    except (ValueError, TypeError):
        return None


class ValidationResults:
    """Helper class for consistent validation result formatting"""
    
    def __init__(self):
        self.results = {
            "validation_time": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_results": []
        }
    
    def add_test(self, test_name: str, passed: bool, details: Dict[str, Any] = None):
        """Add a test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            result["details"] = details
            
        self.results["test_results"].append(result)
        
        if passed:
            self.results["tests_passed"] += 1
        else:
            self.results["tests_failed"] += 1
    
    def get_results(self) -> Dict[str, Any]:
        """Get the validation results dictionary"""
        self.results["total_tests"] = self.results["tests_passed"] + self.results["tests_failed"]
        self.results["status"] = "VALIDATED" if self.results["tests_failed"] == 0 else "FAILED"
        return self.results
    
    def save(self, filename: str = "evidence.json"):
        """Save results using the canonical save_evidence function"""
        save_evidence(self.get_results(), filename)