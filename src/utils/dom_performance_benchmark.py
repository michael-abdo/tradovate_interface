#!/usr/bin/env python3
"""
DOM Intelligence System Performance Benchmarking
Ensures <10ms overhead for critical trading operations
"""

import time
import json
import statistics
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Tuple
import concurrent.futures
import psutil
import os

# Import DOM Intelligence components
from src.utils.chrome_communication import (
    DOMValidator, DOMOperation, ValidationTier,
    SelectorEvolution, TradovateElementRegistry,
    DOMOperationQueue, DOMHealthMonitor,
    CriticalOperationValidator, DOMStateSynchronizer,
    execute_auto_trade_with_validation,
    execute_exit_positions_with_validation
)


class DOMPerformanceBenchmark:
    """Performance benchmarking for DOM Intelligence System"""
    
    def __init__(self):
        self.results = defaultdict(list)
        self.system_metrics = {
            'cpu_percent': [],
            'memory_mb': [],
            'thread_count': []
        }
        self.benchmark_config = {
            'warmup_iterations': 10,
            'test_iterations': 100,
            'parallel_operations': 5,
            'latency_thresholds': {
                ValidationTier.ZERO_LATENCY: 10.0,     # <10ms
                ValidationTier.LOW_LATENCY: 25.0,      # <25ms  
                ValidationTier.STANDARD_LATENCY: 50.0, # <50ms
                ValidationTier.HIGH_LATENCY: 100.0     # <100ms
            }
        }
        
    def benchmark_validation_tiers(self) -> Dict[str, Any]:
        """Benchmark performance across all validation tiers"""
        print("\n🔬 Benchmarking Validation Tiers...")
        
        validator = DOMValidator()
        results = {}
        
        for tier in ValidationTier:
            print(f"\n  Testing {tier.name}...")
            
            # Create test operation
            operation = DOMOperation(
                operation_id=f"bench_{tier.name}",
                tab_id="bench_tab",
                element_type="order_submit_button" if tier == ValidationTier.ZERO_LATENCY else "symbol_input",
                selector=".btn-primary" if tier == ValidationTier.ZERO_LATENCY else "#symbolInput",
                operation_type="click",
                validation_tier=tier
            )
            
            # Warmup
            for _ in range(self.benchmark_config['warmup_iterations']):
                validator.validate_operation(operation)
            
            # Benchmark
            times = []
            for i in range(self.benchmark_config['test_iterations']):
                start = time.perf_counter()
                result = validator.validate_operation(operation)
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
                
            # Calculate statistics
            results[tier.name] = {
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'stdev_ms': statistics.stdev(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'p95_ms': sorted(times)[int(len(times) * 0.95)],
                'p99_ms': sorted(times)[int(len(times) * 0.99)],
                'threshold_ms': self.benchmark_config['latency_thresholds'][tier],
                'within_threshold': statistics.mean(times) < self.benchmark_config['latency_thresholds'][tier]
            }
            
            # Print results
            stats = results[tier.name]
            status = "✅" if stats['within_threshold'] else "❌"
            print(f"    {status} Mean: {stats['mean_ms']:.2f}ms (threshold: {stats['threshold_ms']}ms)")
            print(f"    📊 P95: {stats['p95_ms']:.2f}ms, P99: {stats['p99_ms']:.2f}ms")
            
        return results
        
    def benchmark_emergency_bypass(self) -> Dict[str, Any]:
        """Benchmark emergency bypass decision performance"""
        print("\n🚨 Benchmarking Emergency Bypass...")
        
        validator = CriticalOperationValidator()
        results = {}
        
        # Test different scenarios
        scenarios = [
            ("normal_conditions", {"market_volatility": 0.02}),
            ("high_volatility", {"market_volatility": 0.08}),
            ("manual_override", {"manual_override": True}),
            ("system_stress", {"cpu_usage": 95, "memory_usage": 90})
        ]
        
        for scenario_name, context in scenarios:
            print(f"\n  Testing {scenario_name}...")
            
            # Enable manual override for manual_override scenario
            if scenario_name == "manual_override":
                validator.enable_manual_emergency_override("Benchmark test")
            
            # Warmup
            for _ in range(self.benchmark_config['warmup_iterations']):
                validator.should_bypass_validation("auto_trade", context)
            
            # Benchmark
            times = []
            bypass_count = 0
            
            for _ in range(self.benchmark_config['test_iterations']):
                start = time.perf_counter()
                should_bypass, reason = validator.should_bypass_validation("auto_trade", context)
                end = time.perf_counter()
                times.append((end - start) * 1000)
                if should_bypass:
                    bypass_count += 1
            
            # Calculate statistics
            results[scenario_name] = {
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'max_ms': max(times),
                'bypass_rate': bypass_count / self.benchmark_config['test_iterations'],
                'within_1ms': statistics.mean(times) < 1.0
            }
            
            # Print results
            stats = results[scenario_name]
            status = "✅" if stats['within_1ms'] else "⚠️"
            print(f"    {status} Mean: {stats['mean_ms']:.3f}ms (target: <1ms)")
            print(f"    🔄 Bypass rate: {stats['bypass_rate']*100:.1f}%")
            
        return results
        
    def benchmark_selector_evolution(self) -> Dict[str, Any]:
        """Benchmark adaptive selector performance"""
        print("\n🔄 Benchmarking Selector Evolution...")
        
        evolution = SelectorEvolution()
        results = {}
        
        # Pre-populate with realistic data
        element_types = ["order_submit_button", "symbol_input", "account_selector", "position_table"]
        for element_type in element_types:
            for i in range(50):
                selector = f"#{element_type}_{i % 3}"
                if i % 10 < 7:  # 70% success rate
                    evolution.record_success(selector, element_type, {"page": "trading"})
                else:
                    evolution.record_failure(selector, element_type, "Not found", {"page": "trading"})
        
        # Benchmark operations
        operations = [
            ("get_optimal_selector", lambda et: evolution.get_optimal_selector_chain(et)),
            ("record_success", lambda et: evolution.record_success(f"#{et}_test", et)),
            ("record_failure", lambda et: evolution.record_failure(f"#{et}_test", et, "Error")),
            ("learn_patterns", lambda et: evolution.learn_selector_patterns(et))
        ]
        
        for op_name, op_func in operations:
            print(f"\n  Testing {op_name}...")
            
            times = []
            for _ in range(self.benchmark_config['test_iterations']):
                element_type = element_types[_ % len(element_types)]
                start = time.perf_counter()
                op_func(element_type)
                end = time.perf_counter()
                times.append((end - start) * 1000)
            
            results[op_name] = {
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'max_ms': max(times)
            }
            
            print(f"    ⏱️  Mean: {results[op_name]['mean_ms']:.2f}ms")
            
        return results
        
    def benchmark_parallel_operations(self) -> Dict[str, Any]:
        """Benchmark parallel DOM operations across multiple tabs"""
        print("\n🔀 Benchmarking Parallel Operations...")
        
        queue = DOMOperationQueue(max_workers=5)
        results = {}
        
        try:
            # Register test tabs
            for i in range(5):
                queue.tab_sync_manager.register_tab(f"tab_{i}", f"account_{i % 2}")
            
            # Create operations
            operations = []
            for i in range(self.benchmark_config['parallel_operations']):
                op = DOMOperation(
                    operation_id=f"parallel_{i}",
                    tab_id=f"tab_{i % 5}",
                    element_type="symbol_input",
                    selector="#symbolInput",
                    operation_type="input",
                    parameters={"value": f"TEST{i}"}
                )
                operations.append(op)
            
            # Benchmark sequential execution
            print("\n  Sequential execution...")
            start = time.perf_counter()
            for op in operations:
                queue.queue_operation(op)
            end = time.perf_counter()
            sequential_time = (end - start) * 1000
            
            # Benchmark parallel execution
            print("  Parallel execution...")
            start = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(queue.queue_operation, op) for op in operations]
                concurrent.futures.wait(futures)
            end = time.perf_counter()
            parallel_time = (end - start) * 1000
            
            results = {
                'sequential_ms': sequential_time,
                'parallel_ms': parallel_time,
                'speedup': sequential_time / parallel_time if parallel_time > 0 else 0,
                'operations_count': len(operations)
            }
            
            print(f"    📈 Sequential: {sequential_time:.2f}ms")
            print(f"    ⚡ Parallel: {parallel_time:.2f}ms")
            print(f"    🚀 Speedup: {results['speedup']:.2f}x")
            
        finally:
            queue.shutdown()
            
        return results
        
    def benchmark_state_synchronization(self) -> Dict[str, Any]:
        """Benchmark DOM state synchronization performance"""
        print("\n🔄 Benchmarking State Synchronization...")
        
        synchronizer = DOMStateSynchronizer()
        results = {}
        
        # Register test tabs
        for i in range(10):
            synchronizer.tab_sync_manager.register_tab(f"tab_{i}", f"account_{i % 3}")
            synchronizer.enable_auto_sync(f"tab_{i}")
        
        # Test different sync scenarios
        scenarios = [
            ("symbol_change", {"symbol": "ES"}),
            ("account_switch", {"account_name": "account_new"}),
            ("position_update", {"positions": [{"symbol": "NQ", "qty": 1}]}),
            ("order_update", {"orders": [{"id": "123", "status": "filled"}]})
        ]
        
        for state_type, state_data in scenarios:
            print(f"\n  Testing {state_type}...")
            
            times = []
            sync_counts = []
            
            for i in range(self.benchmark_config['test_iterations']):
                source_tab = f"tab_{i % 10}"
                
                start = time.perf_counter()
                result = synchronizer.sync_dom_state_across_tabs(
                    source_tab, state_type, state_data, priority="normal"
                )
                end = time.perf_counter()
                
                times.append((end - start) * 1000)
                sync_counts.append(len(result.get('synced_tabs', [])))
            
            results[state_type] = {
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'max_ms': max(times),
                'avg_synced_tabs': statistics.mean(sync_counts)
            }
            
            print(f"    ⏱️  Mean: {results[state_type]['mean_ms']:.2f}ms")
            print(f"    📡 Avg synced tabs: {results[state_type]['avg_synced_tabs']:.1f}")
            
        return results
        
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage of DOM Intelligence components"""
        print("\n💾 Benchmarking Memory Usage...")
        
        process = psutil.Process(os.getpid())
        results = {}
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test component memory usage
        components = [
            ("DOMValidator", lambda: DOMValidator()),
            ("SelectorEvolution", lambda: SelectorEvolution()),
            ("TradovateElementRegistry", lambda: TradovateElementRegistry()),
            ("DOMOperationQueue", lambda: DOMOperationQueue()),
            ("DOMHealthMonitor", lambda: DOMHealthMonitor()),
            ("CriticalOperationValidator", lambda: CriticalOperationValidator()),
            ("DOMStateSynchronizer", lambda: DOMStateSynchronizer())
        ]
        
        for comp_name, comp_factory in components:
            print(f"\n  Testing {comp_name}...")
            
            # Create multiple instances
            instances = []
            memory_before = process.memory_info().rss / 1024 / 1024
            
            for _ in range(100):
                instances.append(comp_factory())
            
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_per_instance = (memory_after - memory_before) / 100
            
            results[comp_name] = {
                'memory_per_instance_mb': memory_per_instance,
                'total_memory_100_instances_mb': memory_after - memory_before
            }
            
            print(f"    📊 Per instance: {memory_per_instance:.3f} MB")
            print(f"    💾 100 instances: {memory_after - memory_before:.1f} MB")
            
            # Cleanup
            del instances
            
        return results
        
    def benchmark_end_to_end_trading(self, mock_tab=None) -> Dict[str, Any]:
        """Benchmark complete trading operations with DOM Intelligence"""
        print("\n🎯 Benchmarking End-to-End Trading Operations...")
        
        if not mock_tab:
            # Create a mock tab for testing
            class MockTab:
                id = "test_tab"
                def Runtime(self):
                    class Runtime:
                        @staticmethod
                        def evaluate(expression):
                            return {"result": {"value": "Success"}}
                    return Runtime()
            mock_tab = MockTab()
        
        results = {}
        
        # Test trading operations
        operations = [
            ("auto_trade", lambda: execute_auto_trade_with_validation(
                mock_tab, "NQ", 1, "Buy", 10, 5, 0.25, 
                context={"market_volatility": 0.02}
            )),
            ("exit_positions", lambda: execute_exit_positions_with_validation(
                mock_tab, "NQ", "cancel-option-Exit-at-Mkt-Cxl",
                context={"position_exit": True}
            ))
        ]
        
        for op_name, op_func in operations:
            print(f"\n  Testing {op_name}...")
            
            times = []
            validation_times = []
            execution_times = []
            
            for _ in range(20):  # Fewer iterations for end-to-end
                start = time.perf_counter()
                result = op_func()
                end = time.perf_counter()
                
                total_time = (end - start) * 1000
                times.append(total_time)
                
                # Extract component times if available
                if isinstance(result, dict):
                    val_result = result.get('validation_result', {})
                    if 'validation_time' in val_result:
                        validation_times.append(val_result['validation_time'])
                    if 'execution_time' in result:
                        execution_times.append(result['execution_time'])
            
            results[op_name] = {
                'mean_total_ms': statistics.mean(times),
                'median_total_ms': statistics.median(times),
                'max_total_ms': max(times),
                'mean_validation_ms': statistics.mean(validation_times) if validation_times else 0,
                'mean_execution_ms': statistics.mean(execution_times) if execution_times else 0
            }
            
            print(f"    ⏱️  Total: {results[op_name]['mean_total_ms']:.2f}ms")
            if validation_times:
                print(f"    🔍 Validation: {results[op_name]['mean_validation_ms']:.2f}ms")
            
        return results
        
    def generate_performance_report(self, all_results: Dict[str, Any]) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("DOM INTELLIGENCE SYSTEM PERFORMANCE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        
        # Check critical thresholds
        critical_pass = True
        warnings = []
        
        # Validation tier performance
        if 'validation_tiers' in all_results:
            for tier_name, stats in all_results['validation_tiers'].items():
                if not stats['within_threshold']:
                    critical_pass = False
                    warnings.append(f"❌ {tier_name} exceeds threshold: {stats['mean_ms']:.2f}ms > {stats['threshold_ms']}ms")
                else:
                    report.append(f"✅ {tier_name}: {stats['mean_ms']:.2f}ms (threshold: {stats['threshold_ms']}ms)")
        
        # Emergency bypass performance
        if 'emergency_bypass' in all_results:
            for scenario, stats in all_results['emergency_bypass'].items():
                if not stats['within_1ms']:
                    warnings.append(f"⚠️  {scenario} bypass decision: {stats['mean_ms']:.3f}ms > 1ms")
        
        if critical_pass:
            report.append("\n✅ ALL CRITICAL PERFORMANCE THRESHOLDS MET")
        else:
            report.append("\n❌ CRITICAL PERFORMANCE ISSUES DETECTED")
            for warning in warnings:
                report.append(f"   {warning}")
        
        # Detailed Results
        report.append("\n" + "=" * 80)
        report.append("DETAILED PERFORMANCE METRICS")
        report.append("=" * 80)
        
        # Format all results
        for category, results in all_results.items():
            report.append(f"\n{category.upper().replace('_', ' ')}")
            report.append("-" * 40)
            
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict):
                        report.append(f"\n  {key}:")
                        for k, v in value.items():
                            if isinstance(v, (int, float)):
                                if 'ms' in k or 'time' in k:
                                    report.append(f"    {k}: {v:.3f}")
                                else:
                                    report.append(f"    {k}: {v:.2f}")
                            else:
                                report.append(f"    {k}: {v}")
                    else:
                        if isinstance(value, (int, float)):
                            report.append(f"  {key}: {value:.3f}")
                        else:
                            report.append(f"  {key}: {value}")
        
        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        
        if warnings:
            report.append("\n⚠️  Performance Optimization Needed:")
            for i, warning in enumerate(warnings, 1):
                report.append(f"   {i}. {warning}")
            report.append("\n   Consider:")
            report.append("   - Enable more aggressive caching")
            report.append("   - Reduce validation complexity for affected tiers")
            report.append("   - Increase emergency bypass thresholds")
        else:
            report.append("\n✅ System performing within all specified limits")
            report.append("   No immediate optimization required")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
        
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite"""
        print("\n🚀 Starting DOM Intelligence Performance Benchmark Suite")
        print("=" * 60)
        
        all_results = {}
        
        # Run all benchmarks
        benchmarks = [
            ("validation_tiers", self.benchmark_validation_tiers),
            ("emergency_bypass", self.benchmark_emergency_bypass),
            ("selector_evolution", self.benchmark_selector_evolution),
            ("parallel_operations", self.benchmark_parallel_operations),
            ("state_synchronization", self.benchmark_state_synchronization),
            ("memory_usage", self.benchmark_memory_usage),
            ("end_to_end_trading", self.benchmark_end_to_end_trading)
        ]
        
        for name, benchmark_func in benchmarks:
            try:
                all_results[name] = benchmark_func()
            except Exception as e:
                print(f"\n❌ Error in {name} benchmark: {e}")
                all_results[name] = {"error": str(e)}
        
        # Generate report
        report = self.generate_performance_report(all_results)
        
        # Save report
        report_path = f"/Users/Mike/trading/tests/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Performance report saved to: {report_path}")
        print("\n" + "=" * 60)
        print(report)
        
        return all_results


def run_continuous_monitoring(duration_minutes: int = 60):
    """Run continuous performance monitoring"""
    print(f"\n📊 Starting continuous performance monitoring for {duration_minutes} minutes...")
    
    monitor = DOMHealthMonitor()
    benchmark = DOMPerformanceBenchmark()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    results_history = []
    
    while datetime.now() < end_time:
        # Run mini benchmark
        validator = DOMValidator()
        operation = DOMOperation(
            operation_id="monitor_test",
            tab_id="monitor_tab",
            element_type="order_submit_button",
            selector=".btn-primary",
            operation_type="click",
            validation_tier=ValidationTier.ZERO_LATENCY
        )
        
        # Measure performance
        times = []
        for _ in range(10):
            start = time.perf_counter()
            validator.validate_operation("monitor_tab", operation)
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        # Record metrics
        current_metrics = {
            'timestamp': datetime.now(),
            'mean_validation_ms': statistics.mean(times),
            'max_validation_ms': max(times),
            'health_status': monitor.check_system_health(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_mb': psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        }
        
        results_history.append(current_metrics)
        
        # Print status
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        remaining = duration_minutes - elapsed
        print(f"\r⏱️  {elapsed:.1f}/{duration_minutes} min | "
              f"Validation: {current_metrics['mean_validation_ms']:.2f}ms | "
              f"Health: {current_metrics['health_status'].name} | "
              f"CPU: {current_metrics['cpu_percent']:.1f}% | "
              f"Memory: {current_metrics['memory_mb']:.1f}MB", end='')
        
        # Sleep before next measurement
        time.sleep(30)  # Measure every 30 seconds
    
    print("\n\n✅ Monitoring complete!")
    
    # Analyze results
    print("\nPERFORMANCE SUMMARY:")
    print("-" * 40)
    
    validation_times = [r['mean_validation_ms'] for r in results_history]
    print(f"Validation Performance:")
    print(f"  Mean: {statistics.mean(validation_times):.2f}ms")
    print(f"  Min: {min(validation_times):.2f}ms")
    print(f"  Max: {max(validation_times):.2f}ms")
    print(f"  StdDev: {statistics.stdev(validation_times):.2f}ms")
    
    # Check for degradation
    first_half = validation_times[:len(validation_times)//2]
    second_half = validation_times[len(validation_times)//2:]
    
    if statistics.mean(second_half) > statistics.mean(first_half) * 1.2:
        print("\n⚠️  Performance degradation detected over time!")
    else:
        print("\n✅ Performance remained stable")
    
    return results_history


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='DOM Intelligence Performance Benchmark')
    parser.add_argument('--full', action='store_true', help='Run full benchmark suite')
    parser.add_argument('--monitor', type=int, help='Run continuous monitoring for N minutes')
    parser.add_argument('--quick', action='store_true', help='Run quick performance check')
    
    args = parser.parse_args()
    
    if args.monitor:
        run_continuous_monitoring(args.monitor)
    elif args.quick:
        # Quick performance check
        benchmark = DOMPerformanceBenchmark()
        benchmark.benchmark_config['test_iterations'] = 20  # Fewer iterations
        results = benchmark.benchmark_validation_tiers()
        
        print("\n✅ Quick check complete!")
        for tier, stats in results.items():
            status = "✅" if stats['within_threshold'] else "❌"
            print(f"{status} {tier}: {stats['mean_ms']:.2f}ms")
    else:
        # Default: run full benchmark
        benchmark = DOMPerformanceBenchmark()
        benchmark.run_full_benchmark()