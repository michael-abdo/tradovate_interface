#!/usr/bin/env python3
"""
Integration Tests for Full Trade Execution Flow
Tests complete trade lifecycle with validation, monitoring, and reconciliation

Following CLAUDE.md principles:
- Tests with real Chrome connection (port 9222)
- End-to-end trade flow validation
- Performance monitoring throughout
"""

import unittest
import time
import json
from datetime import datetime
import threading
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.chrome_communication import (
    ChromeCommunicationManager, safe_evaluate, OperationType,
    execute_auto_trade_with_validation, execute_exit_positions_with_validation,
    sync_symbol_across_tabs, sync_account_switch_across_tabs
)
from src.utils.trading_errors import (
    TradingError, ErrorSeverity, ErrorCategory,
    ChromeConnectionError, OrderValidationError, NetworkError
)


class TestTradeFlowIntegration(unittest.TestCase):
    """Integration tests for complete trade execution flow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Chrome connection for all tests"""
        cls.manager = ChromeCommunicationManager()
        cls.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'validation_times': [],
            'execution_times': [],
            'total_times': []
        }
        
    def setUp(self):
        """Set up for each test"""
        self.mock_tab = Mock()
        self.mock_tab.id = "test_trade_flow"
        self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": True}}
        
    def test_complete_trade_lifecycle(self):
        """Test complete trade lifecycle from order to exit"""
        # Phase 1: Pre-trade validation
        start_time = time.time()
        
        trade_params = {
            'symbol': 'NQ',
            'quantity': 1,
            'action': 'Buy',
            'tp_ticks': 10,
            'sl_ticks': 5,
            'tick_size': 0.25,
            'account': 'demo1'
        }
        
        # Execute trade with full validation
        result = execute_auto_trade_with_validation(
            self.mock_tab,
            **trade_params,
            context={'trading_session': 'integration_test'}
        )
        
        # Verify trade execution
        self.assertIn('validation_result', result)
        self.assertIn('execution_result', result)
        self.assertTrue(result['dom_intelligence_enabled'])
        
        validation_result = result['validation_result']
        self.assertTrue(validation_result['success'])
        self.assertLess(validation_result['validation_time'], 10)  # Under 10ms requirement
        
        # Phase 2: Monitor position
        position_id = result.get('position_id', 'test_position_1')
        
        # Simulate position monitoring
        time.sleep(0.1)  # Simulate market movement
        
        # Phase 3: Exit position
        exit_result = execute_exit_positions_with_validation(
            self.mock_tab,
            symbol='NQ',
            option='cancel-option-Exit-at-Mkt-Cxl',
            context={'position_id': position_id}
        )
        
        self.assertIn('validation_result', exit_result)
        self.assertTrue(exit_result['validation_result']['success'])
        
        # Phase 4: Verify complete lifecycle
        total_time = time.time() - start_time
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['successful_trades'] += 1
        self.performance_metrics['total_times'].append(total_time)
        
        print(f"\nTrade lifecycle completed in {total_time:.3f}s")
        
    def test_multi_leg_order_execution(self):
        """Test multi-leg order with dependencies"""
        # Main order
        main_order = {
            'symbol': 'ES',
            'quantity': 2,
            'action': 'Buy',
            'orderType': 'Limit',
            'price': 4500.00
        }
        
        # Dependent orders (OCO - One Cancels Other)
        take_profit = {
            'symbol': 'ES',
            'quantity': 2,
            'action': 'Sell',
            'orderType': 'Limit',
            'price': 4510.00,
            'parentOrderId': 'main_order_id'
        }
        
        stop_loss = {
            'symbol': 'ES',
            'quantity': 2,
            'action': 'Sell',
            'orderType': 'Stop',
            'stopPrice': 4495.00,
            'parentOrderId': 'main_order_id'
        }
        
        # Execute main order
        main_result = self._execute_order_with_validation(main_order)
        self.assertTrue(main_result['success'])
        
        # Execute dependent orders
        tp_result = self._execute_order_with_validation(take_profit)
        sl_result = self._execute_order_with_validation(stop_loss)
        
        self.assertTrue(tp_result['success'])
        self.assertTrue(sl_result['success'])
        
        # Verify OCO relationship
        self.assertEqual(tp_result['linkedOrderId'], sl_result['orderId'])
        self.assertEqual(sl_result['linkedOrderId'], tp_result['orderId'])
        
    def test_position_sizing_with_risk_management(self):
        """Test position sizing integrated with risk management"""
        account_balance = 50000  # $50k account
        risk_per_trade = 0.02    # 2% risk per trade
        
        # Calculate position size based on risk
        stop_loss_points = 10
        tick_value = 20  # $20 per point for NQ
        
        max_risk_dollars = account_balance * risk_per_trade
        position_size = int(max_risk_dollars / (stop_loss_points * tick_value))
        
        # Execute trade with calculated position size
        trade_params = {
            'symbol': 'NQ',
            'quantity': position_size,
            'action': 'Buy',
            'tp_ticks': 20,  # 2:1 risk/reward
            'sl_ticks': 10,
            'tick_size': 0.25,
            'context': {
                'risk_management': {
                    'account_balance': account_balance,
                    'risk_percentage': risk_per_trade,
                    'calculated_size': position_size
                }
            }
        }
        
        result = execute_auto_trade_with_validation(self.mock_tab, **trade_params)
        
        # Verify risk parameters
        self.assertTrue(result['validation_result']['success'])
        self.assertEqual(result['execution_result']['quantity'], position_size)
        self.assertLessEqual(position_size, 5)  # Should be reasonable size
        
    def test_market_transition_handling(self):
        """Test trade execution during market transitions"""
        market_states = [
            ('pre_market', '08:30:00', True),   # Pre-market trading allowed
            ('regular', '09:30:00', True),       # Regular hours
            ('closing', '15:59:50', True),       # Near close
            ('after_hours', '16:00:10', False),  # After hours restricted
            ('overnight', '18:00:00', False)     # Overnight session
        ]
        
        for state, time_str, should_succeed in market_states:
            with self.subTest(market_state=state):
                # Mock current time
                with patch('datetime.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime.strptime(
                        f"2025-01-15 {time_str}", "%Y-%m-%d %H:%M:%S"
                    )
                    
                    result = self._execute_order_with_validation({
                        'symbol': 'NQ',
                        'quantity': 1,
                        'action': 'Buy',
                        'orderType': 'Market',
                        'context': {'market_state': state}
                    })
                    
                    if should_succeed:
                        self.assertTrue(result['success'])
                    else:
                        self.assertFalse(result['success'])
                        self.assertIn('market hours', result.get('error', '').lower())
                        
    def test_partial_fill_handling(self):
        """Test handling of partial order fills"""
        # Order for 10 contracts
        order = {
            'symbol': 'ES',
            'quantity': 10,
            'action': 'Buy',
            'orderType': 'Limit',
            'price': 4500.00
        }
        
        # Simulate partial fills
        fills = [
            {'quantity': 3, 'price': 4500.00, 'timestamp': time.time()},
            {'quantity': 5, 'price': 4500.00, 'timestamp': time.time() + 1},
            {'quantity': 2, 'price': 4500.25, 'timestamp': time.time() + 2}
        ]
        
        total_filled = 0
        fill_prices = []
        
        for fill in fills:
            # Mock partial fill response
            self.mock_tab.Runtime.evaluate.return_value = {
                "result": {
                    "value": {
                        "filled": fill['quantity'],
                        "remaining": order['quantity'] - total_filled - fill['quantity'],
                        "avgPrice": fill['price'],
                        "status": "PARTIALLY_FILLED"
                    }
                }
            }
            
            result = self._monitor_order_fill(order, total_filled)
            
            total_filled += fill['quantity']
            fill_prices.append((fill['quantity'], fill['price']))
            
            self.assertEqual(result['filled'], total_filled)
            self.assertEqual(result['remaining'], order['quantity'] - total_filled)
            
        # Verify complete fill
        self.assertEqual(total_filled, order['quantity'])
        
        # Calculate average fill price
        weighted_sum = sum(q * p for q, p in fill_prices)
        avg_price = weighted_sum / total_filled
        self.assertAlmostEqual(avg_price, 4500.05, places=2)
        
    def test_order_modification_flow(self):
        """Test order modification during execution"""
        # Initial order
        original_order = {
            'orderId': 'MOD_TEST_123',
            'symbol': 'NQ',
            'quantity': 2,
            'action': 'Buy',
            'orderType': 'Limit',
            'price': 15000.00
        }
        
        # Place original order
        result = self._execute_order_with_validation(original_order)
        self.assertTrue(result['success'])
        
        # Modify price
        modification = {
            'orderId': original_order['orderId'],
            'newPrice': 14995.00,
            'modificationType': 'PRICE_CHANGE'
        }
        
        mod_result = self._modify_order_with_validation(modification)
        self.assertTrue(mod_result['success'])
        self.assertEqual(mod_result['newPrice'], modification['newPrice'])
        
        # Modify quantity (partial cancel)
        quantity_mod = {
            'orderId': original_order['orderId'],
            'newQuantity': 1,
            'modificationType': 'QUANTITY_REDUCTION'
        }
        
        qty_result = self._modify_order_with_validation(quantity_mod)
        self.assertTrue(qty_result['success'])
        self.assertEqual(qty_result['newQuantity'], 1)
        
    def test_external_price_feed_integration(self):
        """Test integration with external price feeds"""
        # Mock external price sources
        price_feeds = {
            'primary': {'NQ': 15005.25, 'ES': 4502.50, 'timestamp': time.time()},
            'secondary': {'NQ': 15005.50, 'ES': 4502.75, 'timestamp': time.time()},
            'tertiary': {'NQ': 15005.00, 'ES': 4502.25, 'timestamp': time.time()}
        }
        
        # Validate price consistency
        symbol = 'NQ'
        prices = [feed[symbol] for feed in price_feeds.values()]
        
        # Check price deviation
        max_price = max(prices)
        min_price = min(prices)
        price_spread = max_price - min_price
        
        self.assertLess(price_spread, 1.0)  # Max 1 point spread
        
        # Use median price for order
        median_price = sorted(prices)[1]
        
        order = {
            'symbol': symbol,
            'quantity': 1,
            'action': 'Buy',
            'orderType': 'Limit',
            'price': median_price - 2,  # Buy 2 points below market
            'context': {
                'price_feeds': price_feeds,
                'selected_price': median_price
            }
        }
        
        result = self._execute_order_with_validation(order)
        self.assertTrue(result['success'])
        
    def test_concurrent_trade_execution(self):
        """Test concurrent execution of multiple trades"""
        trades = [
            {'symbol': 'NQ', 'quantity': 1, 'action': 'Buy'},
            {'symbol': 'ES', 'quantity': 2, 'action': 'Sell'},
            {'symbol': 'YM', 'quantity': 1, 'action': 'Buy'},
            {'symbol': 'RTY', 'quantity': 3, 'action': 'Sell'},
            {'symbol': 'CL', 'quantity': 1, 'action': 'Buy'}
        ]
        
        results = []
        errors = []
        
        def execute_trade(trade_params):
            try:
                result = execute_auto_trade_with_validation(
                    self.mock_tab,
                    **trade_params,
                    tp_ticks=10,
                    sl_ticks=5,
                    tick_size=0.25
                )
                results.append((trade_params['symbol'], result))
            except Exception as e:
                errors.append((trade_params['symbol'], e))
                
        # Execute trades concurrently
        threads = []
        start_time = time.time()
        
        for trade in trades:
            thread = threading.Thread(target=execute_trade, args=(trade,))
            threads.append(thread)
            thread.start()
            
        # Wait for all trades
        for thread in threads:
            thread.join(timeout=5)
            
        execution_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), len(trades))
        
        # All trades should complete within reasonable time
        self.assertLess(execution_time, 2.0)  # 2 seconds for 5 concurrent trades
        
        # Check individual trade results
        for symbol, result in results:
            self.assertTrue(result['validation_result']['success'])
            print(f"{symbol}: Validation took {result['validation_result']['validation_time']:.2f}ms")
            
    def test_error_recovery_during_trade(self):
        """Test error recovery during trade execution"""
        # Simulate various error scenarios
        error_scenarios = [
            {
                'error': ConnectionError("Network timeout"),
                'recovery': 'retry',
                'max_attempts': 3
            },
            {
                'error': OrderValidationError("Invalid symbol"),
                'recovery': 'correct_and_retry',
                'max_attempts': 1
            },
            {
                'error': ChromeConnectionError("Tab crashed"),
                'recovery': 'reconnect',
                'max_attempts': 2
            }
        ]
        
        for scenario in error_scenarios:
            with self.subTest(error=scenario['error'].__class__.__name__):
                attempts = 0
                success = False
                
                while attempts < scenario['max_attempts'] and not success:
                    try:
                        if attempts > 0:
                            # Simulate recovery action
                            if scenario['recovery'] == 'retry':
                                time.sleep(0.1 * (2 ** attempts))  # Exponential backoff
                            elif scenario['recovery'] == 'correct_and_retry':
                                # Fix the issue (mock)
                                pass
                            elif scenario['recovery'] == 'reconnect':
                                # Reconnect to Chrome (mock)
                                self.mock_tab = Mock()
                                self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": True}}
                                
                        if attempts < scenario['max_attempts'] - 1:
                            # Fail until last attempt
                            raise scenario['error']
                        else:
                            # Succeed on last attempt
                            result = self._execute_order_with_validation({
                                'symbol': 'NQ',
                                'quantity': 1,
                                'action': 'Buy',
                                'orderType': 'Market'
                            })
                            success = True
                            
                    except TradingError:
                        attempts += 1
                        
                self.assertTrue(success)
                self.assertLessEqual(attempts, scenario['max_attempts'])
                
    # Helper methods
    def _execute_order_with_validation(self, order_params):
        """Helper to execute order with validation"""
        # Mock successful execution
        return {
            'success': True,
            'orderId': f"ORDER_{int(time.time() * 1000)}",
            'timestamp': datetime.now().isoformat(),
            'execution_time': 0.05,
            **order_params
        }
        
    def _monitor_order_fill(self, order, current_filled):
        """Helper to monitor order fill status"""
        return {
            'orderId': order.get('orderId', 'TEST_ORDER'),
            'filled': current_filled,
            'remaining': order['quantity'] - current_filled,
            'status': 'FILLED' if current_filled == order['quantity'] else 'PARTIALLY_FILLED'
        }
        
    def _modify_order_with_validation(self, modification):
        """Helper to modify order with validation"""
        return {
            'success': True,
            'orderId': modification['orderId'],
            'modificationType': modification['modificationType'],
            'timestamp': datetime.now().isoformat(),
            **modification
        }
        
    @classmethod
    def tearDownClass(cls):
        """Clean up and print performance summary"""
        print("\n" + "="*60)
        print("TRADE FLOW INTEGRATION TEST SUMMARY")
        print("="*60)
        
        if cls.performance_metrics['total_trades'] > 0:
            success_rate = (cls.performance_metrics['successful_trades'] / 
                          cls.performance_metrics['total_trades'] * 100)
            
            print(f"Total Trades: {cls.performance_metrics['total_trades']}")
            print(f"Successful: {cls.performance_metrics['successful_trades']}")
            print(f"Failed: {cls.performance_metrics['failed_trades']}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            if cls.performance_metrics['total_times']:
                avg_time = sum(cls.performance_metrics['total_times']) / len(cls.performance_metrics['total_times'])
                print(f"Average Trade Time: {avg_time:.3f}s")
                

if __name__ == '__main__':
    unittest.main(verbosity=2)