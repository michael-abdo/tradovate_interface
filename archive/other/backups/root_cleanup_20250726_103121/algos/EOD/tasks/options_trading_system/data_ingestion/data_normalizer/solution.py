#!/usr/bin/env python3
"""
TASK: data_normalizer
TYPE: Leaf Task
PURPOSE: Normalize data from different sources into standard format
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)

# Import sibling tasks
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from barchart_saved_data.solution import load_barchart_saved_data
from tradovate_api_data.solution import load_tradovate_api_data


class DataNormalizer:
    """Normalize options data from various sources into standard format"""
    
    def __init__(self):
        """Initialize the data normalizer"""
        self.sources = {}
        self.normalized_data = None
        self.metadata = {
            "normalizer_version": "1.0",
            "normalized_at": None
        }
    
    def load_barchart_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from Barchart source"""
        result = load_barchart_saved_data(file_path)
        self.sources['barchart'] = result
        return result
    
    def load_tradovate_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load data from Tradovate source"""
        result = load_tradovate_api_data(config)
        self.sources['tradovate'] = result
        return result
    
    def normalize_contract(self, contract_data: Dict, source: str, contract_type: str) -> Dict[str, Any]:
        """
        Normalize a single contract to standard format
        
        Args:
            contract_data: Raw contract data
            source: Data source name
            contract_type: 'call' or 'put'
            
        Returns:
            Normalized contract dict
        """
        normalized = {
            "source": source,
            "type": contract_type,
            "symbol": None,
            "strike": None,
            "expiration": None,
            "volume": None,
            "open_interest": None,
            "last_price": None,
            "bid": None,
            "ask": None,
            "underlying_price": None,
            "timestamp": get_utc_timestamp()
        }
        
        if source == "barchart":
            # Extract from Barchart format
            raw = contract_data.get('raw', {})
            normalized.update({
                "symbol": contract_data.get('symbol', ''),
                "strike": float(raw.get('strike', 0)),
                "expiration": "2025-06-30",  # Default for now
                "volume": raw.get('volume'),
                "open_interest": raw.get('openInterest'),
                "last_price": raw.get('lastPrice'),
                "underlying_price": 21376.75  # From saved data
            })
            
        elif source == "tradovate":
            # Extract from Tradovate format
            normalized.update({
                "symbol": contract_data.get('symbol', ''),
                "strike": contract_data.get('strike'),
                "expiration": contract_data.get('expiration'),
                "volume": contract_data.get('volume'),
                "open_interest": contract_data.get('openInterest'),
                "last_price": contract_data.get('lastPrice'),
                "bid": contract_data.get('bid'),
                "ask": contract_data.get('ask')
            })
        
        return normalized
    
    def normalize_all_sources(self) -> Dict[str, Any]:
        """
        Normalize data from all loaded sources
        
        Returns:
            Dict with normalized data from all sources
        """
        if not self.sources:
            raise ValueError("No data sources loaded")
        
        normalized = {
            "sources": [],
            "contracts": [],
            "summary": {
                "total_contracts": 0,
                "sources_count": 0,
                "timestamp": get_utc_timestamp()
            }
        }
        
        # Process each source
        for source_name, source_data in self.sources.items():
            normalized["sources"].append(source_name)
            
            if source_name == "barchart":
                # Get the loader from result
                loader = source_data['loader']
                options = loader.get_options_data()
                
                # Normalize calls
                for call in options['calls']:
                    norm_contract = self.normalize_contract(call, "barchart", "call")
                    if norm_contract['strike'] > 0:  # Valid contract
                        normalized["contracts"].append(norm_contract)
                
                # Normalize puts
                for put in options['puts']:
                    norm_contract = self.normalize_contract(put, "barchart", "put")
                    if norm_contract['strike'] > 0:  # Valid contract
                        normalized["contracts"].append(norm_contract)
                        
            elif source_name == "tradovate":
                # Get the loader from result
                loader = source_data['loader']
                options = loader.get_options_data()
                
                # Normalize calls
                for call in options['calls']:
                    norm_contract = self.normalize_contract(call, "tradovate", "call")
                    if norm_contract['strike'] > 0:  # Valid contract
                        normalized["contracts"].append(norm_contract)
                
                # Normalize puts
                for put in options['puts']:
                    norm_contract = self.normalize_contract(put, "tradovate", "put")
                    if norm_contract['strike'] > 0:  # Valid contract
                        normalized["contracts"].append(norm_contract)
        
        # Update summary
        normalized["summary"]["total_contracts"] = len(normalized["contracts"])
        normalized["summary"]["sources_count"] = len(normalized["sources"])
        
        # Group by source for summary
        by_source = {}
        for contract in normalized["contracts"]:
            source = contract["source"]
            if source not in by_source:
                by_source[source] = {"calls": 0, "puts": 0, "total": 0}
            
            by_source[source]["total"] += 1
            if contract["type"] == "call":
                by_source[source]["calls"] += 1
            else:
                by_source[source]["puts"] += 1
        
        normalized["summary"]["by_source"] = by_source
        
        self.normalized_data = normalized
        self.metadata["normalized_at"] = get_utc_timestamp()
        
        return normalized
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Calculate quality metrics for normalized data"""
        if not self.normalized_data:
            raise ValueError("No normalized data available")
        
        contracts = self.normalized_data["contracts"]
        total = len(contracts)
        
        # Count contracts with data
        with_volume = sum(1 for c in contracts if c["volume"] is not None and c["volume"] > 0)
        with_oi = sum(1 for c in contracts if c["open_interest"] is not None and c["open_interest"] > 0)
        with_price = sum(1 for c in contracts if c["last_price"] is not None and c["last_price"] > 0)
        
        # Calculate metrics by source
        source_metrics = {}
        for source in self.normalized_data["sources"]:
            source_contracts = [c for c in contracts if c["source"] == source]
            source_total = len(source_contracts)
            
            if source_total > 0:
                source_metrics[source] = {
                    "total": source_total,
                    "volume_coverage": sum(1 for c in source_contracts if c["volume"] and c["volume"] > 0) / source_total,
                    "oi_coverage": sum(1 for c in source_contracts if c["open_interest"] and c["open_interest"] > 0) / source_total,
                    "price_coverage": sum(1 for c in source_contracts if c["last_price"] and c["last_price"] > 0) / source_total
                }
        
        return {
            "total_contracts": total,
            "overall_volume_coverage": with_volume / total if total > 0 else 0,
            "overall_oi_coverage": with_oi / total if total > 0 else 0,
            "overall_price_coverage": with_price / total if total > 0 else 0,
            "by_source": source_metrics,
            "sources": list(source_metrics.keys())
        }


# Module-level function for easy integration
def normalize_options_data(sources_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize options data from configured sources
    
    Args:
        sources_config: Dict with source configurations
        
    Returns:
        Dict with normalized data and metrics
    """
    normalizer = DataNormalizer()
    
    # Load data from each configured source
    if "barchart" in sources_config:
        normalizer.load_barchart_data(sources_config["barchart"]["file_path"])
    
    if "tradovate" in sources_config:
        normalizer.load_tradovate_data(sources_config["tradovate"])
    
    # Normalize all data
    normalized = normalizer.normalize_all_sources()
    
    # Get quality metrics
    quality_metrics = normalizer.get_quality_metrics()
    
    return {
        "normalizer": normalizer,
        "normalized_data": normalized,
        "quality_metrics": quality_metrics,
        "metadata": normalizer.metadata
    }