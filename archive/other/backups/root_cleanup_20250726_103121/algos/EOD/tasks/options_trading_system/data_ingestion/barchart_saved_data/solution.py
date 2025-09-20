#!/usr/bin/env python3
"""
TASK: barchart_saved_data
TYPE: Leaf Task
PURPOSE: Load saved Barchart API data from JSON file
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


class BarchartSavedDataLoader:
    """Load and parse saved Barchart options data"""
    
    def __init__(self, file_path: str):
        """
        Initialize with file path
        
        Args:
            file_path: Path to saved JSON data file
        """
        self.file_path = file_path
        self.data = None
        self.metadata = {}
        
    def validate_file_exists(self) -> bool:
        """Check if the data file exists"""
        return os.path.exists(self.file_path) and os.path.isfile(self.file_path)
    
    def load_data(self) -> Dict[str, Any]:
        """
        Load data from JSON file
        
        Returns:
            Dict containing raw Barchart data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not self.validate_file_exists():
            raise FileNotFoundError(f"Data file not found: {self.file_path}")
        
        with open(self.file_path, 'r') as f:
            self.data = json.load(f)
            
        # Extract metadata
        self.metadata = {
            "source": "barchart_saved",
            "file_path": self.file_path,
            "file_size": os.path.getsize(self.file_path),
            "loaded_at": get_utc_timestamp()
        }
        
        return self.data
    
    def get_options_data(self) -> Dict[str, List[Dict]]:
        """
        Extract options data from loaded data
        
        Returns:
            Dict with 'calls' and 'puts' lists
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Extract from Barchart format
        calls = self.data.get('data', {}).get('Call', [])
        puts = self.data.get('data', {}).get('Put', [])
        
        return {
            "calls": calls,
            "puts": puts,
            "total_contracts": len(calls) + len(puts)
        }
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """
        Calculate data quality metrics
        
        Returns:
            Dict with quality metrics
        """
        options = self.get_options_data()
        calls = options['calls']
        puts = options['puts']
        
        # Count contracts with volume/OI data
        calls_with_volume = sum(1 for c in calls if c.get('raw', {}).get('volume') not in [None, 0])
        puts_with_volume = sum(1 for p in puts if p.get('raw', {}).get('volume') not in [None, 0])
        
        calls_with_oi = sum(1 for c in calls if c.get('raw', {}).get('openInterest') not in [None, 0])
        puts_with_oi = sum(1 for p in puts if p.get('raw', {}).get('openInterest') not in [None, 0])
        
        total = len(calls) + len(puts)
        
        return {
            "total_contracts": total,
            "calls_count": len(calls),
            "puts_count": len(puts),
            "volume_coverage": (calls_with_volume + puts_with_volume) / total if total > 0 else 0,
            "oi_coverage": (calls_with_oi + puts_with_oi) / total if total > 0 else 0,
            "calls_with_volume": calls_with_volume,
            "puts_with_volume": puts_with_volume,
            "calls_with_oi": calls_with_oi,
            "puts_with_oi": puts_with_oi
        }
    
    def get_strike_range(self) -> Optional[Dict[str, float]]:
        """Get min and max strikes from the data"""
        options = self.get_options_data()
        all_strikes = []
        
        for contract in options['calls'] + options['puts']:
            strike = contract.get('raw', {}).get('strike')
            if strike:
                all_strikes.append(float(strike))
        
        if all_strikes:
            return {
                "min": min(all_strikes),
                "max": max(all_strikes),
                "count": len(set(all_strikes))
            }
        return None


# Module-level function for easy access
def load_barchart_saved_data(file_path: str) -> Dict[str, Any]:
    """
    Load Barchart saved data and return summary
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dict with data and quality metrics
    """
    loader = BarchartSavedDataLoader(file_path)
    
    # Load the data
    raw_data = loader.load_data()
    
    # Get processed data
    options_data = loader.get_options_data()
    quality_metrics = loader.get_data_quality_metrics()
    strike_range = loader.get_strike_range()
    
    return {
        "loader": loader,
        "metadata": loader.metadata,
        "options_summary": options_data,
        "quality_metrics": quality_metrics,
        "strike_range": strike_range,
        "raw_data_available": True
    }