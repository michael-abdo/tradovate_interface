#!/usr/bin/env python3
"""
DOM Intelligence Live Trading Validation
Tests DOM Intelligence System in live trading environment with emergency failsafe scenarios
"""

import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import TradovateConnection, TradovateController
from utils.chrome_communication import (
    DOMValidator, DOMOperation, ValidationTier,
    CriticalOperationValidator, DOMHealthMonitor,
    default_dom_validator, default_critical_validator,
    default_dom_health_monitor, execute_auto_trade_with_validation,
    execute_exit_positions_with_validation
)


class DOMIntelligenceLiveValidator:
    """Validates DOM Intelligence System in live trading environment"""
    
    def __init__(self, controller: TradovateController = None):
        self.controller = controller
        self.validation_results = []
        self.test_scenarios = []
        
    def validate_connection_health(self) -> Dict[str, Any]:
        """Validate that connections are healthy before testing"""
        print("\n🏥 Validating Connection Health...")
        
        results = {
            'total_connections': len(self.controller.connections),
            'healthy_connections': 0,
            'connection_details': []
        }
        
        for conn in self.controller.connections:
            try:
                # Check tab health
                if conn.tab:
                    health = conn.check_connection_health()
                    is_healthy = health.get('healthy', False)
                    
                    if is_healthy:
                        results['healthy_connections'] += 1
                    
                    results['connection_details'].append({
                        'account': conn.account_name,
                        'port': conn.port,
                        'healthy': is_healthy,
                        'errors': health.get('errors', [])
                    })
                    
                    print(f"  {conn.account_name}: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
                else:
                    results['connection_details'].append({
                        'account': conn.account_name,
                        'port': conn.port,
                        'healthy': False,
                        'errors': ['No tab available']
                    })
                    print(f"  {conn.account_name}: ❌ No tab")
                    
            except Exception as e:
                results['connection_details'].append({
                    'account': conn.account_name,
                    'port': conn.port,
                    'healthy': False,
                    'errors': [str(e)]
                })
                print(f"  {conn.account_name}: ❌ Error: {str(e)}")
        
        return results
        
    def test_dom_validation_basic(self, connection: TradovateConnection) -> Dict[str, Any]:
        """Test basic DOM validation without trading"""
        print(f"\n🔍 Testing Basic DOM Validation for {connection.account_name}...")
        
        test_results = {
            'account': connection.account_name,
            'tests': []
        }
        
        # Test 1: Symbol input validation
        try:
            operation = DOMOperation(
                operation_id=f"test_symbol_{connection.account_name}",
                tab_id=getattr(connection.tab, 'id', 'unknown'),
                element_type="symbol_input",
                selector="#symbolInput",
                operation_type="input",
                validation_tier=ValidationTier.LOW_LATENCY,
                parameters={'value': 'NQ'}
            )
            
            result = default_dom_validator.validate_operation(operation)
            
            test_results['tests'].append({
                'test': 'symbol_input_validation',
                'success': result.success,
                'message': result.message,
                'validation_time': result.validation_time
            })
            
            print(f"  Symbol Input: {'✅' if result.success else '❌'} - {result.message}")
            
        except Exception as e:
            test_results['tests'].append({
                'test': 'symbol_input_validation',
                'success': False,
                'error': str(e)
            })
            print(f"  Symbol Input: ❌ Error - {str(e)}")
            
        # Test 2: Order button validation
        try:
            operation = DOMOperation(
                operation_id=f"test_order_{connection.account_name}",
                tab_id=getattr(connection.tab, 'id', 'unknown'),
                element_type="order_submit_button",
                selector=".btn-primary",
                operation_type="click",
                validation_tier=ValidationTier.ZERO_LATENCY
            )
            
            result = default_dom_validator.validate_operation(operation)
            
            test_results['tests'].append({
                'test': 'order_button_validation',
                'success': result.success,
                'message': result.message,
                'validation_time': result.validation_time
            })
            
            print(f"  Order Button: {'✅' if result.success else '❌'} - {result.message}")
            
        except Exception as e:
            test_results['tests'].append({
                'test': 'order_button_validation',
                'success': False,
                'error': str(e)
            })
            print(f"  Order Button: ❌ Error - {str(e)}")
            
        return test_results
        
    def test_emergency_bypass_scenarios(self, connection: TradovateConnection) -> Dict[str, Any]:
        """Test emergency bypass functionality"""
        print(f"\n🚨 Testing Emergency Bypass for {connection.account_name}...")
        
        test_results = {
            'account': connection.account_name,
            'scenarios': []
        }
        
        # Scenario 1: High volatility bypass
        try:
            should_bypass, reason = default_critical_validator.should_bypass_validation(
                'auto_trade',
                {'market_volatility': 0.08}  # 8% volatility
            )
            
            test_results['scenarios'].append({
                'scenario': 'high_volatility',
                'should_bypass': should_bypass,
                'reason': reason
            })
            
            print(f"  High Volatility (8%): {'✅ Bypassed' if should_bypass else '❌ Not Bypassed'}")
            
        except Exception as e:
            test_results['scenarios'].append({
                'scenario': 'high_volatility',
                'error': str(e)
            })
            
        # Scenario 2: Manual override
        try:
            # Enable manual override
            default_critical_validator.enable_manual_emergency_override("Testing emergency")
            
            should_bypass, reason = default_critical_validator.should_bypass_validation(
                'exit_positions',
                {}
            )
            
            test_results['scenarios'].append({
                'scenario': 'manual_override',
                'should_bypass': should_bypass,
                'reason': reason
            })
            
            print(f"  Manual Override: {'✅ Bypassed' if should_bypass else '❌ Not Bypassed'}")
            
            # Disable manual override
            default_critical_validator.disable_manual_emergency_override()
            
        except Exception as e:
            test_results['scenarios'].append({
                'scenario': 'manual_override',
                'error': str(e)
            })
            
        return test_results
        
    def test_symbol_update_with_validation(self, connection: TradovateConnection, symbol: str) -> Dict[str, Any]:
        """Test symbol update with DOM validation"""
        print(f"\n📊 Testing Symbol Update with Validation for {connection.account_name}...")
        
        try:
            result = connection.update_symbol(symbol)
            
            test_result = {
                'account': connection.account_name,
                'symbol': symbol,
                'success': result.get('overall_success', False),
                'validation_result': result.get('validation_result', {}),
                'sync_result': result.get('sync_result', {}),
                'error': result.get('error')
            }
            
            if test_result['success']:
                print(f"  ✅ Symbol updated to {symbol}")
                if 'sync_result' in result and result['sync_result'].get('success'):
                    print(f"  📡 Synced to {len(result['sync_result'].get('synced_tabs', []))} tabs")
            else:
                print(f"  ❌ Symbol update failed: {test_result['error']}")
                
            return test_result
            
        except Exception as e:
            return {
                'account': connection.account_name,
                'symbol': symbol,
                'success': False,
                'error': str(e)
            }
            
    def test_health_monitoring(self) -> Dict[str, Any]:
        """Test DOM health monitoring system"""
        print("\n📊 Testing DOM Health Monitoring...")
        
        # Get current health status
        health_status = default_dom_health_monitor.check_system_health()
        metrics = default_dom_health_monitor.get_performance_summary()
        
        results = {
            'health_status': health_status.name,
            'metrics': metrics,
            'degradation_alerts': []
        }
        
        # Check for any degradation
        for operation_type in ['order_submit_button_click', 'symbol_input_input']:
            alerts = default_dom_health_monitor.degradation_detector.detect_degradation(operation_type)
            if alerts:
                results['degradation_alerts'].extend(alerts)
        
        print(f"  System Health: {health_status.name}")
        print(f"  Total Operations: {metrics.get('total_operations', 0)}")
        print(f"  Success Rate: {metrics.get('success_rate', 0)*100:.1f}%")
        print(f"  Avg Execution Time: {metrics.get('avg_execution_time', 0):.2f}ms")
        
        if results['degradation_alerts']:
            print(f"  ⚠️  Degradation Alerts: {len(results['degradation_alerts'])}")
            
        return results
        
    def run_live_validation_suite(self, test_trade: bool = False) -> Dict[str, Any]:
        """Run complete live validation suite"""
        print("\n" + "="*60)
        print("🚀 DOM INTELLIGENCE LIVE VALIDATION SUITE")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Trading: {'ENABLED' if test_trade else 'DISABLED'}")
        
        overall_results = {
            'start_time': datetime.now().isoformat(),
            'test_trade_enabled': test_trade,
            'connection_health': {},
            'dom_validation_tests': [],
            'emergency_bypass_tests': [],
            'symbol_update_tests': [],
            'health_monitoring': {},
            'test_trades': [] if test_trade else None
        }
        
        # Step 1: Validate connection health
        overall_results['connection_health'] = self.validate_connection_health()
        
        if overall_results['connection_health']['healthy_connections'] == 0:
            print("\n❌ No healthy connections found. Aborting tests.")
            return overall_results
            
        # Step 2: Run DOM validation tests on first healthy connection
        for conn in self.controller.connections:
            if conn.tab:
                # Basic DOM validation
                dom_test = self.test_dom_validation_basic(conn)
                overall_results['dom_validation_tests'].append(dom_test)
                
                # Emergency bypass
                bypass_test = self.test_emergency_bypass_scenarios(conn)
                overall_results['emergency_bypass_tests'].append(bypass_test)
                
                # Symbol update
                symbol_test = self.test_symbol_update_with_validation(conn, "ES")
                overall_results['symbol_update_tests'].append(symbol_test)
                
                # Only test on first connection
                break
                
        # Step 3: Test health monitoring
        overall_results['health_monitoring'] = self.test_health_monitoring()
        
        # Step 4: Optional test trades
        if test_trade and overall_results['connection_health']['healthy_connections'] > 0:
            print("\n⚠️  EXECUTING TEST TRADES...")
            print("   (Using minimal quantity on first healthy connection)")
            
            for conn in self.controller.connections:
                if conn.tab:
                    try:
                        # Test trade with DOM validation
                        trade_result = conn.auto_trade(
                            symbol="MNQ",  # Micro E-mini for testing
                            quantity=1,
                            action="Buy",
                            tp_ticks=10,
                            sl_ticks=5,
                            tick_size=0.25
                        )
                        
                        overall_results['test_trades'].append({
                            'account': conn.account_name,
                            'symbol': 'MNQ',
                            'action': 'Buy',
                            'quantity': 1,
                            'success': trade_result.get('trade_executed', False),
                            'dom_validation': trade_result.get('validation_result', {}),
                            'emergency_bypass': trade_result.get('validation_result', {}).get('emergency_bypass', False)
                        })
                        
                        if trade_result.get('trade_executed'):
                            print(f"  ✅ Test trade executed on {conn.account_name}")
                            
                            # Wait a moment then exit the position
                            time.sleep(2)
                            
                            exit_result = conn.exit_positions("MNQ")
                            print(f"  🔄 Position exited: {'✅' if exit_result.get('exit_executed') else '❌'}")
                        else:
                            print(f"  ❌ Test trade failed on {conn.account_name}")
                            
                    except Exception as e:
                        print(f"  ❌ Test trade error on {conn.account_name}: {str(e)}")
                        
                    # Only test on first connection
                    break
                    
        # Summary
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        
        # Connection health
        ch = overall_results['connection_health']
        print(f"Connections: {ch['healthy_connections']}/{ch['total_connections']} healthy")
        
        # DOM validation
        if overall_results['dom_validation_tests']:
            dom_success = sum(1 for test in overall_results['dom_validation_tests'][0]['tests'] if test.get('success', False))
            dom_total = len(overall_results['dom_validation_tests'][0]['tests'])
            print(f"DOM Validation: {dom_success}/{dom_total} passed")
        
        # Emergency bypass
        if overall_results['emergency_bypass_tests']:
            bypass_working = sum(1 for test in overall_results['emergency_bypass_tests'][0]['scenarios'] 
                               if test.get('should_bypass', False))
            print(f"Emergency Bypass: {bypass_working} scenarios triggered correctly")
        
        # Health status
        health = overall_results['health_monitoring']
        print(f"System Health: {health['health_status']}")
        print(f"Success Rate: {health['metrics'].get('success_rate', 0)*100:.1f}%")
        
        overall_results['end_time'] = datetime.now().isoformat()
        
        # Save results
        results_file = f"dom_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"logs/{results_file}", 'w') as f:
            json.dump(overall_results, f, indent=2)
        print(f"\n📄 Results saved to: logs/{results_file}")
        
        return overall_results


def main():
    parser = argparse.ArgumentParser(description='DOM Intelligence Live Trading Validation')
    parser.add_argument('--test-trade', action='store_true', 
                       help='Execute actual test trades (USE WITH CAUTION)')
    parser.add_argument('--max-instances', type=int, default=5,
                       help='Maximum Chrome instances to check')
    
    args = parser.parse_args()
    
    if args.test_trade:
        print("\n⚠️  WARNING: Test trading is ENABLED!")
        print("This will execute real trades on your account.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Validation cancelled.")
            return
    
    # Initialize controller
    controller = TradovateController(max_instances=args.max_instances)
    
    if len(controller.connections) == 0:
        print("❌ No Tradovate connections found.")
        print("Please ensure Chrome instances are running with auto_login.py")
        return 1
        
    # Run validation
    validator = DOMIntelligenceLiveValidator(controller)
    results = validator.run_live_validation_suite(test_trade=args.test_trade)
    
    # Return success/failure based on results
    if results['connection_health']['healthy_connections'] > 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())