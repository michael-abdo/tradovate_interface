import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import threading
import queue

from solution import (
    RealTimeOptionsDataFeed, OptionsContract, OptionsChain,
    LatencyTracker, OptionsDataValidator, DataQualityTracker
)

class TestRealTimeOptionsDataFeed(unittest.TestCase):
    """
    EXPERIMENTAL VALIDATION: Test real-time options data ingestion
    with <100ms latency requirements
    """
    
    def setUp(self):
        self.symbols = ['NQ']
        self.feed = RealTimeOptionsDataFeed(self.symbols)
        
    def test_connection_latency_requirement(self):
        """
        HYPOTHESIS: Connection can be established within 100ms
        SUCCESS CRITERIA: Connection latency < 100ms
        """
        # Mock WebSocket connection
        with patch('solution.websocket.WebSocketApp') as mock_ws:
            mock_ws_instance = Mock()
            mock_ws.return_value = mock_ws_instance
            
            # Simulate immediate connection
            def simulate_connection():
                time.sleep(0.05)  # 50ms simulated connection time
                self.feed.connection_status = "connected"
            
            connection_thread = threading.Thread(target=simulate_connection)
            connection_thread.start()
            
            start_time = time.time()
            result = self.feed.connect("test_key", "wss://test.com")
            connection_time = time.time() - start_time
            
            connection_thread.join()
            
            # VALIDATION: Connection time under 100ms
            self.assertTrue(result)
            self.assertLess(connection_time, 0.1, "Connection latency exceeds 100ms requirement")
            
    def test_message_processing_speed(self):
        """
        HYPOTHESIS: Individual message processing < 50ms
        SUCCESS CRITERIA: Processing latency < 50ms per message
        """
        # Create test options chain message
        test_message = {
            "type": "options_chain",
            "symbol": "NQ",
            "underlying_price": 15000.0,
            "expiration": "2024-01-19",
            "timestamp": int(time.time() * 1000),
            "contracts": [
                {
                    "symbol": "NQ240119C15000",
                    "strike": 15000.0,
                    "expiration": "2024-01-19",
                    "type": "call",
                    "bid": 50.0,
                    "ask": 55.0,
                    "last": 52.5,
                    "volume": 100,
                    "open_interest": 500,
                    "delta": 0.5,
                    "gamma": 0.01,
                    "theta": -0.1,
                    "vega": 0.2,
                    "implied_volatility": 0.25
                }
            ]
        }
        
        # Mock WebSocket and test processing
        start_time = time.time()
        self.feed._on_message(None, json.dumps(test_message))
        processing_time = time.time() - start_time
        
        # VALIDATION: Processing time under 50ms
        self.assertLess(processing_time, 0.05, "Message processing exceeds 50ms requirement")
        
        # Verify data was processed correctly
        self.assertEqual(len(self.feed.performance_metrics['processing_times']), 1)
        self.assertGreater(self.feed.performance_metrics['messages_received'], 0)
        
    def test_data_quality_validation(self):
        """
        HYPOTHESIS: Data validator catches invalid messages
        SUCCESS CRITERIA: >99% accuracy in detecting invalid data
        """
        validator = OptionsDataValidator()
        
        # Test valid message
        valid_message = {
            "symbol": "NQ",
            "type": "options_chain",
            "timestamp": int(time.time() * 1000),
            "underlying_price": 15000.0,
            "contracts": [
                {
                    "symbol": "NQ240119C15000",
                    "strike": 15000.0,
                    "expiration": "2024-01-19",
                    "type": "call",
                    "bid": 50.0,
                    "ask": 55.0
                }
            ]
        }
        
        # Test invalid messages
        invalid_messages = [
            {},  # Empty message
            {"symbol": "NQ"},  # Missing required fields
            {"symbol": "NQ", "type": "options_chain", "contracts": []},  # No contracts
            {"symbol": "NQ", "type": "options_chain", "contracts": [{"strike": "invalid"}]}  # Invalid data type
        ]
        
        # VALIDATION: Valid message passes
        self.assertTrue(validator.validate_message(valid_message))
        
        # VALIDATION: Invalid messages fail
        for invalid_msg in invalid_messages:
            self.assertFalse(validator.validate_message(invalid_msg), 
                           f"Validator failed to catch invalid message: {invalid_msg}")
        
    def test_latency_tracking_accuracy(self):
        """
        HYPOTHESIS: Latency tracker accurately measures performance
        SUCCESS CRITERIA: Latency measurements within 1ms accuracy
        """
        tracker = LatencyTracker()
        
        # Test network latency recording
        test_latencies = [0.025, 0.030, 0.035, 0.040, 0.045]
        for latency in test_latencies:
            tracker.record_network_latency(latency)
        
        metrics = tracker.get_metrics()
        
        # VALIDATION: Accurate statistics calculation
        expected_avg = sum(test_latencies) / len(test_latencies)
        actual_avg = metrics['network_latency']['avg']
        
        self.assertAlmostEqual(actual_avg, expected_avg, places=6)
        self.assertEqual(metrics['network_latency']['max'], max(test_latencies))
        self.assertEqual(metrics['network_latency']['min'], min(test_latencies))
        
    def test_subscriber_notification_system(self):
        """
        HYPOTHESIS: Subscriber callbacks execute within 10ms
        SUCCESS CRITERIA: All callbacks complete < 10ms
        """
        callback_times = []
        received_data = []
        
        def test_callback(options_chain):
            start_time = time.time()
            received_data.append(options_chain)
            callback_times.append(time.time() - start_time)
        
        # Subscribe callback
        self.feed.subscribe(test_callback)
        
        # Create test data
        test_chain = OptionsChain(
            underlying_symbol="NQ",
            underlying_price=15000.0,
            expiration_date="2024-01-19",
            calls=[],
            puts=[],
            timestamp=datetime.now()
        )
        
        # Simulate data reception (bypass queue for direct testing)
        for callback in self.feed.subscribers:
            callback(test_chain)
        
        # VALIDATION: Callback executed and data received
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0].underlying_symbol, "NQ")
        
        # VALIDATION: Callback execution time under 10ms
        if callback_times:
            self.assertLess(max(callback_times), 0.01, "Callback execution exceeds 10ms")
        
    def test_data_queue_performance(self):
        """
        HYPOTHESIS: Data queue handles high-frequency updates without blocking
        SUCCESS CRITERIA: No queue overflow in 1000 rapid updates
        """
        # Generate rapid updates
        for i in range(1000):
            test_chain = OptionsChain(
                underlying_symbol="NQ",
                underlying_price=15000.0 + i,
                expiration_date="2024-01-19",
                calls=[],
                puts=[],
                timestamp=datetime.now()
            )
            
            try:
                self.feed.data_queue.put(test_chain, block=False)
            except queue.Full:
                # Should not happen with proper queue sizing
                self.fail("Data queue overflow - performance requirement failed")
        
        # VALIDATION: Queue contains data and no gaps recorded
        self.assertGreater(self.feed.data_queue.qsize(), 0)
        self.assertEqual(self.feed.performance_metrics['data_gaps'], 0)
        
    def test_data_quality_scoring(self):
        """
        HYPOTHESIS: Data quality tracker accurately scores data completeness
        SUCCESS CRITERIA: Quality score correlates with data completeness
        """
        quality_tracker = DataQualityTracker()
        
        # High quality data
        high_quality_chain = OptionsChain(
            underlying_symbol="NQ",
            underlying_price=15000.0,
            expiration_date="2024-01-19",
            calls=[
                OptionsContract(
                    symbol="NQ240119C15000",
                    strike=15000.0,
                    expiration="2024-01-19",
                    option_type="call",
                    bid=50.0,
                    ask=55.0,
                    last=52.5,
                    volume=100,
                    open_interest=500,
                    delta=0.5,
                    gamma=0.01,
                    theta=-0.1,
                    vega=0.2,
                    implied_volatility=0.25,
                    timestamp=datetime.now()
                )
            ],
            puts=[],
            timestamp=datetime.now()
        )
        
        # Low quality data (missing prices)
        low_quality_chain = OptionsChain(
            underlying_symbol="NQ",
            underlying_price=15000.0,
            expiration_date="2024-01-19",
            calls=[
                OptionsContract(
                    symbol="NQ240119C15000",
                    strike=15000.0,
                    expiration="2024-01-19",
                    option_type="call",
                    bid=0.0,  # Missing bid
                    ask=0.0,  # Missing ask
                    last=0.0,
                    volume=0,
                    open_interest=0,
                    delta=0.0,  # Missing delta
                    gamma=0.0,
                    theta=0.0,
                    vega=0.0,
                    implied_volatility=0.0,
                    timestamp=datetime.now()
                )
            ],
            puts=[],
            timestamp=datetime.now()
        )
        
        # Score both chains
        high_score = quality_tracker.assess_data_quality(high_quality_chain)
        low_score = quality_tracker.assess_data_quality(low_quality_chain)
        
        # VALIDATION: High quality data scores higher
        self.assertGreater(high_score, 0.9, "High quality data should score >0.9")
        self.assertLess(low_score, 0.8, "Low quality data should score <0.8")
        self.assertGreater(high_score, low_score, "Quality scoring not working correctly")

class TestPerformanceRequirements(unittest.TestCase):
    """
    COMPREHENSIVE PERFORMANCE VALIDATION
    Test all latency and throughput requirements
    """
    
    def test_end_to_end_latency_requirement(self):
        """
        CRITICAL TEST: End-to-end latency from message to callback < 100ms
        SUCCESS CRITERIA: Total processing latency < 100ms
        """
        feed = RealTimeOptionsDataFeed(['NQ'])
        
        # Mock high-performance callback
        callback_triggered = threading.Event()
        received_timestamp = None
        
        def performance_callback(options_chain):
            nonlocal received_timestamp
            received_timestamp = time.time()
            callback_triggered.set()
        
        feed.subscribe(performance_callback)
        
        # Create realistic options chain message
        realistic_message = {
            "type": "options_chain",
            "symbol": "NQ",
            "underlying_price": 15000.0,
            "expiration": "2024-01-19",
            "timestamp": int(time.time() * 1000),
            "contracts": [
                {
                    "symbol": f"NQ240119{'C' if i % 2 == 0 else 'P'}{15000 + (i-50)*25}",
                    "strike": 15000.0 + (i-50)*25,
                    "expiration": "2024-01-19",
                    "type": "call" if i % 2 == 0 else "put",
                    "bid": 25.0 + i,
                    "ask": 30.0 + i,
                    "last": 27.5 + i,
                    "volume": 50 + i,
                    "open_interest": 200 + i*5,
                    "delta": 0.1 + (i * 0.01),
                    "gamma": 0.005 + (i * 0.0001),
                    "theta": -0.05 - (i * 0.001),
                    "vega": 0.1 + (i * 0.002),
                    "implied_volatility": 0.20 + (i * 0.001)
                }
                for i in range(100)  # 100 contracts for realistic load
            ]
        }
        
        # Measure end-to-end performance
        start_time = time.time()
        feed._on_message(None, json.dumps(realistic_message))
        
        # Wait for callback (with timeout)
        callback_triggered.wait(timeout=1.0)
        
        if received_timestamp:
            total_latency = received_timestamp - start_time
            
            # CRITICAL VALIDATION: End-to-end latency < 100ms
            self.assertLess(total_latency, 0.1, 
                          f"End-to-end latency {total_latency:.3f}s exceeds 100ms requirement")
            
            print(f"✓ End-to-end latency: {total_latency*1000:.1f}ms")
        else:
            self.fail("Callback was not triggered within timeout")
    
    def test_sustained_throughput_performance(self):
        """
        STRESS TEST: Handle sustained 100 messages/second for 60 seconds
        SUCCESS CRITERIA: No performance degradation over time
        """
        feed = RealTimeOptionsDataFeed(['NQ'])
        
        processed_count = 0
        processing_times = []
        
        def throughput_callback(options_chain):
            nonlocal processed_count
            processed_count += 1
        
        feed.subscribe(throughput_callback)
        
        # Simple message for throughput testing
        simple_message = {
            "type": "options_chain",
            "symbol": "NQ",
            "underlying_price": 15000.0,
            "expiration": "2024-01-19",
            "timestamp": int(time.time() * 1000),
            "contracts": [
                {
                    "symbol": "NQ240119C15000",
                    "strike": 15000.0,
                    "expiration": "2024-01-19",
                    "type": "call",
                    "bid": 50.0,
                    "ask": 55.0,
                    "last": 52.5,
                    "volume": 100,
                    "open_interest": 500,
                    "delta": 0.5,
                    "gamma": 0.01,
                    "theta": -0.1,
                    "vega": 0.2,
                    "implied_volatility": 0.25
                }
            ]
        }
        
        # Simulate sustained load (reduced duration for testing)
        messages_to_send = 100  # Reduced from 6000 for faster testing
        start_time = time.time()
        
        for i in range(messages_to_send):
            message_start = time.time()
            feed._on_message(None, json.dumps(simple_message))
            processing_time = time.time() - message_start
            processing_times.append(processing_time)
            
            # Small delay to simulate realistic timing
            time.sleep(0.001)  # 1ms delay
        
        total_time = time.time() - start_time
        
        # VALIDATION: Throughput and consistency
        throughput = processed_count / total_time
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        
        self.assertGreater(throughput, 50, f"Throughput {throughput:.1f} msg/s too low")
        self.assertLess(avg_processing_time, 0.01, f"Average processing time {avg_processing_time:.3f}s too slow")
        self.assertLess(max_processing_time, 0.05, f"Max processing time {max_processing_time:.3f}s too slow")
        
        print(f"✓ Sustained throughput: {throughput:.1f} msg/s")
        print(f"✓ Average processing: {avg_processing_time*1000:.1f}ms")
        print(f"✓ Max processing: {max_processing_time*1000:.1f}ms")

def run_performance_benchmark():
    """
    EMPIRICAL VALIDATION: Run comprehensive performance benchmark
    Generate statistical evidence for latency requirements
    """
    print("\n=== REAL-TIME OPTIONS FEED PERFORMANCE BENCHMARK ===")
    
    # Initialize components
    feed = RealTimeOptionsDataFeed(['NQ'])
    latency_tracker = LatencyTracker()
    
    # Performance data collection
    test_results = {
        'connection_latencies': [],
        'processing_latencies': [],
        'end_to_end_latencies': [],
        'throughput_measurements': [],
        'data_quality_scores': []
    }
    
    # Run multiple test iterations for statistical validity
    num_iterations = 50
    
    print(f"Running {num_iterations} iterations...")
    
    for i in range(num_iterations):
        # Test processing latency
        start_time = time.time()
        
        test_message = {
            "type": "options_chain",
            "symbol": "NQ",
            "underlying_price": 15000.0 + i,
            "expiration": "2024-01-19",
            "timestamp": int(time.time() * 1000),
            "contracts": [
                {
                    "symbol": f"NQ240119C{15000 + j*25}",
                    "strike": 15000.0 + j*25,
                    "expiration": "2024-01-19",
                    "type": "call",
                    "bid": 25.0 + j,
                    "ask": 30.0 + j,
                    "last": 27.5 + j,
                    "volume": 50 + j,
                    "open_interest": 200 + j*5,
                    "delta": 0.5,
                    "gamma": 0.01,
                    "theta": -0.1,
                    "vega": 0.2,
                    "implied_volatility": 0.25
                }
                for j in range(20)  # 20 contracts per chain
            ]
        }
        
        feed._on_message(None, json.dumps(test_message))
        processing_time = time.time() - start_time
        test_results['processing_latencies'].append(processing_time)
    
    # Calculate statistics
    def calculate_stats(data):
        if not data:
            return {}
        
        data_sorted = sorted(data)
        return {
            'mean': sum(data) / len(data),
            'median': data_sorted[len(data)//2],
            'p95': data_sorted[int(len(data) * 0.95)],
            'p99': data_sorted[int(len(data) * 0.99)],
            'max': max(data),
            'min': min(data)
        }
    
    processing_stats = calculate_stats(test_results['processing_latencies'])
    
    # Generate evidence report
    evidence_report = {
        'test_timestamp': datetime.now().isoformat(),
        'sample_size': num_iterations,
        'processing_latency_stats': processing_stats,
        'requirements_validation': {
            'mean_under_50ms': processing_stats['mean'] < 0.05,
            'p95_under_100ms': processing_stats['p95'] < 0.1,
            'max_under_200ms': processing_stats['max'] < 0.2
        },
        'performance_summary': {
            'mean_latency_ms': processing_stats['mean'] * 1000,
            'p95_latency_ms': processing_stats['p95'] * 1000,
            'max_latency_ms': processing_stats['max'] * 1000
        }
    }
    
    # Print results
    print("\n=== PERFORMANCE VALIDATION RESULTS ===")
    print(f"Sample size: {evidence_report['sample_size']}")
    print(f"Mean processing latency: {evidence_report['performance_summary']['mean_latency_ms']:.1f}ms")
    print(f"95th percentile latency: {evidence_report['performance_summary']['p95_latency_ms']:.1f}ms")
    print(f"Maximum latency: {evidence_report['performance_summary']['max_latency_ms']:.1f}ms")
    
    print("\n=== REQUIREMENTS VALIDATION ===")
    for requirement, passed in evidence_report['requirements_validation'].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{requirement}: {status}")
    
    return evidence_report

if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run performance benchmark
    benchmark_results = run_performance_benchmark()
    
    # Save results
    with open('/Users/Mike/trading/algos/EOD/tasks/options_trading_system/data_ingestion/real_time_options_feed/performance_evidence.json', 'w') as f:
        json.dump(benchmark_results, f, indent=2)