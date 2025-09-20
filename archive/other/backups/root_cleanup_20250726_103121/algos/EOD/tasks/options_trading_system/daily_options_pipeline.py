#!/usr/bin/env python3
"""
Daily Options Pipeline with 0DTE Validation

Specialized pipeline for daily 0DTE options processing that:
1. Generates candidate 0DTE symbols
2. Validates they actually expire today
3. Fetches data only for valid symbols
4. Provides abort mechanisms for invalid symbols
5. Integrates with existing analysis pipeline

This pipeline extends the base options trading system with 0DTE-specific logic.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Import PathManager after path setup
sys.path.insert(0, parent_dir)  # For common_utils
from common_utils import PathManager

# Import existing pipeline components
from integration import NQOptionsTradingSystem
from data_ingestion.barchart_web_scraper.symbol_generator import (
    OptionsSymbolGenerator, 
    generate_0dte_symbol,
    get_symbol_with_fallbacks
)
from data_ingestion.barchart_web_scraper.expiration_validator import ExpirationValidator


class DailyOptionsPipeline:
    """
    Daily 0DTE options processing pipeline with validation
    
    Orchestrates the complete flow from symbol generation through
    analysis with 0DTE validation at each step.
    """
    
    def __init__(self, config: Dict[str, Any] = None, enable_validation: bool = True):
        """
        Initialize the daily pipeline
        
        Args:
            config: Base configuration (extends with 0DTE settings)
            enable_validation: Whether to enable 0DTE validation (default: True)
        """
        self.config = config or self._get_default_config()
        self.enable_validation = enable_validation
        self.logger = get_logger()
        
        # Pipeline state
        self.pipeline_state = {
            'symbol_generation': {'status': 'pending'},
            'symbol_validation': {'status': 'pending'},
            'data_ingestion': {'status': 'pending'},
            'analysis': {'status': 'pending'},
            'output': {'status': 'pending'}
        }
        
        # Results storage
        self.results = {
            'symbol_info': None,
            'validation_results': None,
            'pipeline_results': None,
            'abort_reason': None
        }
    
    def run_daily_pipeline(self, target_date: datetime = None, force_symbol: str = None) -> Dict[str, Any]:
        """
        Execute the complete daily 0DTE pipeline
        
        Args:
            target_date: Target expiration date (defaults to today)
            force_symbol: Force specific symbol (bypasses generation/validation)
            
        Returns:
            Complete pipeline results with 0DTE validation info
        """
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info("🚀 DAILY 0DTE OPTIONS PIPELINE STARTED")
        self.logger.info("=" * 60)
        self.logger.info(f"Target Date: {target_date.strftime('%Y-%m-%d %A')}")
        self.logger.info(f"Validation Enabled: {self.enable_validation}")
        self.logger.info(f"Force Symbol: {force_symbol or 'None (auto-generate)'}")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Symbol Generation & Validation
            if force_symbol:
                symbol_result = self._handle_forced_symbol(force_symbol, target_date)
            else:
                symbol_result = self._generate_and_validate_symbol(target_date)
            
            if not symbol_result['success']:
                return self._create_abort_result(symbol_result['reason'], symbol_result)
            
            # Step 2: Update configuration with validated symbol
            self._update_config_with_symbol(symbol_result['symbol'])
            
            # Step 3: Run main trading system with validated symbol
            main_results = self._run_main_pipeline()
            
            # Step 4: Combine results
            return self._create_success_result(symbol_result, main_results)
            
        except Exception as e:
            self.logger.error(f"💥 Pipeline failed with exception: {e}")
            return self._create_error_result(str(e))
    
    def run_symbol_validation_only(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        Run only symbol generation and validation (no data fetching)
        
        Useful for testing and validation without full pipeline execution.
        
        Args:
            target_date: Target expiration date (defaults to today)
            
        Returns:
            Symbol validation results
        """
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info(f"🔍 Symbol validation only for {target_date.strftime('%Y-%m-%d')}")
        
        return self._generate_and_validate_symbol(target_date)
    
    def _generate_and_validate_symbol(self, target_date: datetime) -> Dict[str, Any]:
        """
        Generate and validate 0DTE symbol
        
        Args:
            target_date: Target expiration date
            
        Returns:
            Dict with success status, symbol, and validation info
        """
        self.logger.info("🎯 Step 1: Symbol Generation & Validation")
        
        # Update pipeline state
        self.pipeline_state['symbol_generation']['status'] = 'in_progress'
        
        try:
            # Generate symbol with comprehensive fallback info
            symbol_generator = OptionsSymbolGenerator(
                validate_0dte=self.enable_validation,
                headless=True
            )
            
            symbol_info = symbol_generator.generate_symbol_with_fallbacks(target_date)
            
            self.results['symbol_info'] = symbol_info
            self.pipeline_state['symbol_generation']['status'] = 'completed'
            
            # Log generation results
            self.logger.info(f"  📅 Requested: {symbol_info.get('requested_date', 'Unknown')}")
            self.logger.info(f"  📅 Adjusted: {symbol_info.get('adjusted_date', 'Unknown')}")
            self.logger.info(f"  🔄 Date Adjusted: {symbol_info.get('date_adjusted', False)}")
            self.logger.info(f"  🏷️  Generated Symbol: {symbol_info.get('symbol', 'None')}")
            self.logger.info(f"  🔧 Contract Type: {symbol_info.get('contract_type', 'None')}")
            self.logger.info(f"  ✅ Is 0DTE: {symbol_info.get('is_0dte', False)}")
            self.logger.info(f"  🧪 Fallbacks Tried: {len(symbol_info.get('fallbacks_tried', []))}")
            
            # Check if we found a valid symbol
            if symbol_info.get('symbol') is None:
                reason = "No valid 0DTE symbol found for target date"
                self.logger.error(f"  ❌ {reason}")
                return {
                    'success': False,
                    'reason': reason,
                    'symbol_info': symbol_info,
                    'fallbacks_tried': symbol_info.get('fallbacks_tried', [])
                }
            
            # Additional validation if enabled
            if self.enable_validation and not symbol_info.get('is_0dte', False):
                reason = f"Symbol {symbol_info['symbol']} failed 0DTE validation"
                self.logger.error(f"  ❌ {reason}")
                return {
                    'success': False,
                    'reason': reason,
                    'symbol_info': symbol_info,
                    'symbol': symbol_info['symbol']
                }
            
            self.logger.info(f"  ✅ Valid 0DTE symbol confirmed: {symbol_info['symbol']}")
            self.pipeline_state['symbol_validation']['status'] = 'completed'
            
            return {
                'success': True,
                'symbol': symbol_info['symbol'],
                'contract_type': symbol_info.get('contract_type'),
                'symbol_info': symbol_info,
                'is_validated': symbol_info.get('is_0dte', False)
            }
            
        except Exception as e:
            self.pipeline_state['symbol_generation']['status'] = 'failed'
            reason = f"Symbol generation failed: {str(e)}"
            self.logger.error(f"  💥 {reason}")
            return {
                'success': False,
                'reason': reason,
                'error': str(e)
            }
    
    def _handle_forced_symbol(self, symbol: str, target_date: datetime) -> Dict[str, Any]:
        """
        Handle forced symbol with optional validation
        
        Args:
            symbol: Forced symbol
            target_date: Target expiration date
            
        Returns:
            Validation results for forced symbol
        """
        self.logger.info(f"🔒 Using forced symbol: {symbol}")
        
        if self.enable_validation:
            self.logger.info("🧪 Validating forced symbol...")
            
            try:
                with ExpirationValidator(headless=True) as validator:
                    is_0dte = validator.validate_is_0dte(symbol, target_date)
                
                if is_0dte:
                    self.logger.info(f"  ✅ Forced symbol {symbol} is valid 0DTE")
                    return {
                        'success': True,
                        'symbol': symbol,
                        'contract_type': symbol[:2],  # Extract prefix
                        'is_validated': True,
                        'forced': True
                    }
                else:
                    self.logger.warning(f"  ⚠️  Forced symbol {symbol} is NOT 0DTE")
                    return {
                        'success': True,  # Still proceed with forced symbol
                        'symbol': symbol,
                        'contract_type': symbol[:2],
                        'is_validated': False,
                        'forced': True,
                        'warning': 'Forced symbol is not 0DTE'
                    }
                    
            except Exception as e:
                self.logger.error(f"  💥 Validation of forced symbol failed: {e}")
                return {
                    'success': True,  # Still proceed with forced symbol
                    'symbol': symbol,
                    'contract_type': symbol[:2],
                    'is_validated': False,
                    'forced': True,
                    'error': f'Validation failed: {str(e)}'
                }
        else:
            self.logger.info("  ✅ Using forced symbol (validation disabled)")
            return {
                'success': True,
                'symbol': symbol,
                'contract_type': symbol[:2],
                'is_validated': False,
                'forced': True
            }
    
    def _update_config_with_symbol(self, symbol: str):
        """
        Update pipeline configuration with validated symbol
        
        Args:
            symbol: Validated 0DTE symbol
        """
        self.logger.info(f"⚙️  Updating configuration with symbol: {symbol}")
        
        # Update Barchart configuration
        if 'data' not in self.config:
            self.config['data'] = {}
        if 'barchart' not in self.config['data']:
            self.config['data']['barchart'] = {}
        
        # Set the target symbol
        self.config['data']['barchart']['target_symbol'] = symbol
        
        self.logger.debug(f"  📝 Configuration updated: target_symbol = {symbol}")
    
    def _run_main_pipeline(self) -> Dict[str, Any]:
        """
        Execute the main NQ trading system pipeline
        
        Returns:
            Main pipeline results
        """
        self.logger.info("🔧 Step 2: Running Main Trading Pipeline")
        
        try:
            # Update pipeline states
            self.pipeline_state['data_ingestion']['status'] = 'in_progress'
            self.pipeline_state['analysis']['status'] = 'in_progress'
            self.pipeline_state['output']['status'] = 'in_progress'
            
            # Run the main system
            system = NQOptionsTradingSystem(self.config)
            results = system.run_complete_system()
            
            # Update states based on results
            if results.get('status') == 'success':
                pipeline_results = results.get('pipeline_results', {})
                
                self.pipeline_state['data_ingestion']['status'] = pipeline_results.get('data', {}).get('status', 'unknown')
                self.pipeline_state['analysis']['status'] = pipeline_results.get('analysis', {}).get('status', 'unknown') 
                self.pipeline_state['output']['status'] = pipeline_results.get('output', {}).get('status', 'unknown')
                
                self.logger.info("  ✅ Main pipeline completed successfully")
            else:
                self.logger.error(f"  ❌ Main pipeline failed: {results.get('error', 'Unknown error')}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"  💥 Main pipeline exception: {e}")
            raise
    
    def _create_success_result(self, symbol_result: Dict[str, Any], main_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create successful pipeline result
        
        Args:
            symbol_result: Symbol generation/validation results
            main_results: Main pipeline results
            
        Returns:
            Combined success result
        """
        return {
            'status': 'success',
            'timestamp': get_utc_timestamp(),
            'pipeline_type': 'daily_0dte',
            'validation_enabled': self.enable_validation,
            'symbol_validation': symbol_result,
            'main_pipeline': main_results,
            'pipeline_state': self.pipeline_state,
            'results': self.results
        }
    
    def _create_abort_result(self, reason: str, symbol_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create abort result when pipeline cannot proceed
        
        Args:
            reason: Reason for abort
            symbol_result: Symbol generation results
            
        Returns:
            Abort result
        """
        self.results['abort_reason'] = reason
        
        return {
            'status': 'aborted',
            'timestamp': get_utc_timestamp(),
            'pipeline_type': 'daily_0dte',
            'abort_reason': reason,
            'validation_enabled': self.enable_validation,
            'symbol_validation': symbol_result,
            'pipeline_state': self.pipeline_state,
            'results': self.results
        }
    
    def _create_error_result(self, error: str) -> Dict[str, Any]:
        """
        Create error result for unexpected failures
        
        Args:
            error: Error message
            
        Returns:
            Error result
        """
        return {
            'status': 'error',
            'timestamp': get_utc_timestamp(),
            'pipeline_type': 'daily_0dte',
            'error': error,
            'validation_enabled': self.enable_validation,
            'pipeline_state': self.pipeline_state,
            'results': self.results
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for daily pipeline
        
        Returns:
            Default configuration dict
        """
        return {
            "data": {
                "barchart": {
                    "use_live_api": True,
                    "futures_symbol": "NQM25",
                    "headless": True,
                    # target_symbol will be set by validation
                },
                "tradovate": {
                    "mode": "demo",
                    "cid": "6540",
                    "secret": "f7a2b8f5-8348-424f-8ffa-047ab7502b7c",
                    "use_mock": True
                }
            },
            "analysis": {
                "expected_value": {
                    "weights": {
                        "oi_factor": 0.35,
                        "vol_factor": 0.25,
                        "pcr_factor": 0.25,
                        "distance_factor": 0.15
                    },
                    "min_ev": 15,
                    "min_probability": 0.60,
                    "max_risk": 150,
                    "min_risk_reward": 1.0
                },
                "momentum": {
                    "volume_threshold": 100,
                    "price_change_threshold": 0.05,
                    "momentum_window": 5,
                    "min_momentum_score": 0.6
                }
            },
            "output": {
                "report": {
                    "style": "professional",
                    "include_details": True,
                    "include_market_context": True
                },
                "json": {
                    "include_raw_data": False,
                    "include_metadata": True,
                    "format_pretty": True,
                    "include_analysis_details": True
                }
            },
            "save": {
                "save_report": True,
                "save_json": True,
                "output_dir": "outputs",
                "timestamp_suffix": True
            }
        }


# Convenience functions for easy usage
def run_daily_0dte_pipeline(target_date: datetime = None, config: Dict[str, Any] = None, enable_validation: bool = True) -> Dict[str, Any]:
    """
    Convenience function to run daily 0DTE pipeline
    
    Args:
        target_date: Target expiration date (defaults to today)
        config: Custom configuration (uses defaults if None)
        enable_validation: Whether to enable 0DTE validation
        
    Returns:
        Complete pipeline results
    """
    pipeline = DailyOptionsPipeline(config=config, enable_validation=enable_validation)
    return pipeline.run_daily_pipeline(target_date=target_date)


def validate_0dte_symbol_only(target_date: datetime = None) -> Dict[str, Any]:
    """
    Convenience function to validate 0DTE symbol without running full pipeline
    
    Args:
        target_date: Target expiration date (defaults to today)
        
    Returns:
        Symbol validation results
    """
    pipeline = DailyOptionsPipeline(enable_validation=True)
    return pipeline.run_symbol_validation_only(target_date)


def run_with_forced_symbol(symbol: str, target_date: datetime = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to run pipeline with forced symbol
    
    Args:
        symbol: Forced symbol to use
        target_date: Target expiration date (defaults to today)
        config: Custom configuration (uses defaults if None)
        
    Returns:
        Complete pipeline results with forced symbol
    """
    pipeline = DailyOptionsPipeline(config=config, enable_validation=True)
    return pipeline.run_daily_pipeline(target_date=target_date, force_symbol=symbol)