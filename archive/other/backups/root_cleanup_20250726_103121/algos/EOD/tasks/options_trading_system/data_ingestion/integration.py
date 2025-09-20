#!/usr/bin/env python3
"""
TASK: data_ingestion
TYPE: Parent Task Integration
PURPOSE: Integrate all data source children into unified data pipeline
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common_utils import PathManager, get_utc_timestamp, create_success_response, create_failure_response

# Add child tasks to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import validated child solutions
from barchart_saved_data.solution import load_barchart_saved_data
from tradovate_api_data.solution import load_tradovate_api_data
from data_normalizer.solution import normalize_options_data
from polygon_api.solution import load_polygon_api_data

# Import new live API client
try:
    from barchart_web_scraper.hybrid_scraper import HybridBarchartScraper
    from barchart_web_scraper.solution import BarchartAPIComparator
    LIVE_API_AVAILABLE = True
except ImportError:
    LIVE_API_AVAILABLE = False


def load_barchart_live_data(futures_symbol: str = "NQM25", headless: bool = True, target_symbol: str = None) -> Dict[str, Any]:
    """
    Load live Barchart options data for today's EOD contract
    
    Args:
        futures_symbol: Underlying futures symbol
        headless: Run browser in headless mode
        target_symbol: Specific contract symbol to fetch (overrides EOD calculation)
        
    Returns:
        Dict with Barchart data in same format as saved data
    """
    if not LIVE_API_AVAILABLE:
        raise ImportError("Live API components not available")
    
    try:
        # Get target symbol (either specified or today's EOD)
        if target_symbol:
            eod_symbol = target_symbol
            print(f"🎯 Using specified target symbol: {eod_symbol}")
        else:
            comparator = BarchartAPIComparator()
            eod_symbol = comparator.get_eod_contract_symbol()
            print(f"📅 Calculated EOD symbol: {eod_symbol}")
        
        # Use hybrid scraper to get live data
        scraper = HybridBarchartScraper(headless=headless)
        
        # Authenticate and fetch data
        if not scraper.authenticate(futures_symbol):
            raise Exception("Failed to authenticate with Barchart")
        
        api_data = scraper.fetch_options_data(eod_symbol, futures_symbol)
        
        if not api_data or api_data.get('total', 0) == 0:
            # Try monthly options as fallback
            print(f"⚠️  EOD contract {eod_symbol} not available, trying monthly option MC6M25")
            api_data = scraper.fetch_options_data("MC6M25", futures_symbol)
            
            if not api_data or api_data.get('total', 0) == 0:
                raise Exception(f"❌ No live options data available for {eod_symbol} or MC6M25. Market may be closed or contracts not listed.")
        
        return {
            "raw_data": api_data,
            "source": "barchart_live_api",
            "symbol": eod_symbol if api_data.get('total', 0) > 0 else "MC6M25",
            "timestamp": get_utc_timestamp(),
            "total_contracts": api_data.get('total', 0)
        }
        
    except Exception as e:
        print(f"❌ Live API failed: {e}")
        print("🛑 STOPPING: Cannot proceed without live data.")
        raise e


class DataIngestionPipeline:
    """Integrated data ingestion pipeline combining all data sources"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pipeline with configuration
        
        Args:
            config: Dict with source configurations
        """
        self.config = config
        self.sources = {}
        self.normalized_data = None
        self.pipeline_metadata = {
            "pipeline_version": "1.0",
            "created_at": get_utc_timestamp(),
            "sources_configured": list(config.keys())
        }
    
    def load_all_sources(self) -> Dict[str, Any]:
        """Load data from all configured sources"""
        results = {}
        
        # Load Barchart if configured
        if "barchart" in self.config:
            try:
                # Try live API first, fallback to saved data
                use_live_api = self.config["barchart"].get("use_live_api", True)
                print(f"🔧 Live API config: use_live_api={use_live_api}, available={LIVE_API_AVAILABLE}")
                
                if use_live_api and LIVE_API_AVAILABLE:
                    print("🌐 Fetching live Barchart options data...")
                    barchart_data = load_barchart_live_data(
                        futures_symbol=self.config["barchart"].get("futures_symbol", "NQM25"),
                        headless=self.config["barchart"].get("headless", True),
                        target_symbol=self.config["barchart"].get("target_symbol")
                    )
                    print(f"✅ Got {barchart_data.get('total_contracts', 0)} contracts from live API")
                    
                    # Convert live data to expected format
                    if "raw_data" in barchart_data:
                        # Process live API data into expected format
                        api_data = barchart_data["raw_data"]
                        total_contracts = api_data.get('total', 0)
                        results["barchart"] = {
                            "status": "success",
                            "contracts": total_contracts,
                            "quality": {
                                "live_api": True, 
                                "symbol": barchart_data.get("symbol"),
                                "volume_coverage": 1.0 if total_contracts > 0 else 0.0,
                                "oi_coverage": 1.0 if total_contracts > 0 else 0.0
                            },
                            "data": {
                                "source": "live_api",
                                "raw_data": api_data,
                                "options_summary": {"total_contracts": total_contracts},
                                "quality_metrics": {
                                    "data_source": "live", 
                                    "total_contracts": total_contracts,
                                    "volume_coverage": 1.0 if total_contracts > 0 else 0.0,
                                    "oi_coverage": 1.0 if total_contracts > 0 else 0.0
                                }
                            }
                        }
                    else:
                        # Fallback format from saved data
                        results["barchart"] = {
                            "status": "success", 
                            "contracts": barchart_data["options_summary"]["total_contracts"],
                            "quality": barchart_data["quality_metrics"],
                            "data": barchart_data
                        }
                else:
                    print("📁 Loading saved Barchart data...")
                    barchart_data = load_barchart_saved_data(
                        self.config["barchart"]["file_path"]
                    )
                    results["barchart"] = {
                        "status": "success",
                        "contracts": barchart_data["options_summary"]["total_contracts"],
                        "quality": barchart_data["quality_metrics"],
                        "data": barchart_data
                    }
                    
            except Exception as e:
                # If live API is required and fails, stop the entire pipeline
                if self.config["barchart"].get("use_live_api", True):
                    print(f"🛑 PIPELINE STOPPED: Live API required but failed: {str(e)}")
                    raise Exception(f"Live API required but failed: {str(e)}")
                else:
                    results["barchart"] = {
                        "status": "failed",
                        "error": str(e)
                    }
        
        # Load Tradovate if configured
        if "tradovate" in self.config:
            try:
                tradovate_data = load_tradovate_api_data(
                    self.config["tradovate"]
                )
                results["tradovate"] = {
                    "status": "success",
                    "contracts": tradovate_data["options_summary"]["total_contracts"],
                    "quality": tradovate_data["quality_metrics"],
                    "data": tradovate_data
                }
            except Exception as e:
                results["tradovate"] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Load Polygon.io if configured
        if "polygon" in self.config:
            try:
                print("📡 Fetching Polygon.io Nasdaq-100 options data...")
                polygon_data = load_polygon_api_data(
                    self.config["polygon"]
                )
                results["polygon"] = {
                    "status": "success",
                    "contracts": polygon_data["options_summary"]["total_contracts"],
                    "quality": polygon_data["quality_metrics"],
                    "data": polygon_data
                }
                print(f"✅ Got {polygon_data['options_summary']['total_contracts']} contracts from Polygon.io")
            except Exception as e:
                results["polygon"] = {
                    "status": "failed",
                    "error": str(e)
                }
                print(f"❌ Polygon.io failed: {str(e)}")
        
        self.sources = results
        return results
    
    def normalize_pipeline_data(self) -> Dict[str, Any]:
        """Normalize all loaded data into standard format"""
        if not self.sources:
            raise ValueError("No data sources loaded. Call load_all_sources() first.")
        
        # Use the data_normalizer to normalize all sources
        normalized_result = normalize_options_data(self.config)
        
        self.normalized_data = normalized_result
        return normalized_result
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of the entire data pipeline"""
        if not self.normalized_data:
            raise ValueError("No normalized data available. Run pipeline first.")
        
        summary = {
            "pipeline_metadata": self.pipeline_metadata,
            "sources_loaded": len([s for s in self.sources.values() if s["status"] == "success"]),
            "sources_failed": len([s for s in self.sources.values() if s["status"] == "failed"]),
            "total_contracts": self.normalized_data["normalized_data"]["summary"]["total_contracts"],
            "data_quality": self.normalized_data["quality_metrics"],
            "timestamp": get_utc_timestamp()
        }
        
        # Add per-source summaries
        summary["source_details"] = {}
        for source_name, source_data in self.sources.items():
            if source_data["status"] == "success":
                summary["source_details"][source_name] = {
                    "contracts": source_data["contracts"],
                    "volume_coverage": source_data["quality"]["volume_coverage"],
                    "oi_coverage": source_data["quality"]["oi_coverage"]
                }
        
        return summary
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Execute the complete data ingestion pipeline"""
        # Step 1: Load all sources
        load_results = self.load_all_sources()
        
        # Step 2: Normalize data
        normalized = self.normalize_pipeline_data()
        
        # Step 3: Get summary
        summary = self.get_pipeline_summary()
        
        return {
            "pipeline_status": "success",
            "load_results": load_results,
            "normalized_data": normalized["normalized_data"],
            "quality_metrics": normalized["quality_metrics"],
            "summary": summary
        }


# Module-level integration function
def create_data_ingestion_pipeline(config: Dict[str, Any]) -> DataIngestionPipeline:
    """
    Create and return configured data ingestion pipeline
    
    Args:
        config: Configuration for data sources
        
    Returns:
        Configured DataIngestionPipeline instance
    """
    return DataIngestionPipeline(config)


def run_data_ingestion(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete data ingestion pipeline
    
    Args:
        config: Configuration for data sources
        
    Returns:
        Dict with pipeline results
    """
    pipeline = create_data_ingestion_pipeline(config)
    return pipeline.run_full_pipeline()