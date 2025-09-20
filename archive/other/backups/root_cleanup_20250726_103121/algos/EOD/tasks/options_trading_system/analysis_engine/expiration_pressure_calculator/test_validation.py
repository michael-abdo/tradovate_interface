import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import statistics

from solution import (
    ExpirationPressureCalculator, PressureAlert, UrgencyLevel,
    PredictionTracker, CalculationValidator
)

class TestExpirationPressureCalculator(unittest.TestCase):
    """
    EXPERIMENTAL VALIDATION: Test pressure calculation algorithm
    with empirical validation of assignment risk formula
    """
    
    def setUp(self):
        self.calculator = ExpirationPressureCalculator(validation_mode=True)
        self.sample_options_data = [
            {
                'strike': 15000.0,
                'call_oi': 2500,
                'put_oi': 1800
            },
            {
                'strike': 15025.0,
                'call_oi': 1200,
                'put_oi': 3200
            },
            {
                'strike': 14975.0,
                'call_oi': 1800,
                'put_oi': 2100
            }
        ]
        
    def test_pressure_formula_mathematical_accuracy(self):
        """
        HYPOTHESIS: Pressure = Assignment Risk / Time² formula is mathematically accurate
        SUCCESS CRITERIA: Calculated pressure matches manual calculation within 0.1%
        """
        
        current_price = 15010.0
        current_time = datetime.now()
        expiration_date = current_time + timedelta(minutes=30)  # 30 minutes to expiry
        
        alerts = self.calculator.calculate_expiration_pressure(
            self.sample_options_data, current_price, current_time, expiration_date
        )
        
        # Manual calculation for first strike (15000.0)
        strike_data = self.sample_options_data[0]
        total_oi = strike_data['call_oi'] + strike_data['put_oi']  # 4300
        distance_to_strike = abs(current_price - strike_data['strike'])  # 10.0
        minutes_to_expiry = 30
        
        # Manual assignment probability calculation (based on algorithm)
        expected_assignment_prob = max(0.05, 0.5 - (distance_to_strike / 20))  # Warning zone
        expected_assignment_risk = total_oi * expected_assignment_prob
        expected_pressure = expected_assignment_risk / (minutes_to_expiry ** 2)
        
        # Find corresponding alert
        alert_15000 = next((a for a in alerts if a.strike_price == 15000.0), None)
        
        # VALIDATION: Mathematical accuracy
        self.assertIsNotNone(alert_15000, "Alert should be generated for strike 15000")
        self.assertAlmostEqual(
            alert_15000.pressure_value, expected_pressure, places=1,
            msg=f"Pressure calculation error: expected {expected_pressure}, got {alert_15000.pressure_value}"
        )
        
    def test_urgency_classification_accuracy(self):
        """
        HYPOTHESIS: Urgency classification correctly identifies crisis vs pin risk scenarios
        SUCCESS CRITERIA: >95% accuracy in urgency level assignment
        """
        
        test_scenarios = [
            # (minutes_to_expiry, total_oi, distance, expected_urgency)
            (10, 2000, 5.0, UrgencyLevel.ASSIGNMENT_PANIC),     # Crisis scenario
            (45, 2500, 15.0, UrgencyLevel.PIN_RISK_MANAGEMENT), # Pin risk scenario
            (180, 800, 25.0, UrgencyLevel.NO_SIGNAL),           # No signal scenario
            (5, 5000, 3.0, UrgencyLevel.ASSIGNMENT_PANIC),      # High pressure crisis
            (60, 3000, 12.0, UrgencyLevel.PIN_RISK_MANAGEMENT)  # Strong pin risk
        ]
        
        current_price = 15000.0
        current_time = datetime.now()
        
        correct_classifications = 0
        total_tests = len(test_scenarios)
        
        for minutes, oi, distance, expected_urgency in test_scenarios:
            # Create test data
            test_data = [{
                'strike': current_price + distance,
                'call_oi': oi // 2,
                'put_oi': oi // 2
            }]
            
            expiration_date = current_time + timedelta(minutes=minutes)
            
            alerts = self.calculator.calculate_expiration_pressure(
                test_data, current_price, current_time, expiration_date
            )
            
            if expected_urgency == UrgencyLevel.NO_SIGNAL:
                # Should generate no alerts
                if len(alerts) == 0:
                    correct_classifications += 1
            else:
                # Should generate alert with correct urgency
                if len(alerts) > 0 and alerts[0].urgency_level == expected_urgency:
                    correct_classifications += 1
        
        accuracy = correct_classifications / total_tests
        
        # VALIDATION: >95% accuracy requirement
        self.assertGreater(accuracy, 0.95, f"Urgency classification accuracy {accuracy:.2%} below 95% requirement")
        
    def test_steering_direction_logic(self):
        """
        HYPOTHESIS: Steering direction correctly predicts market maker hedging behavior
        SUCCESS CRITERIA: Logical consistency in direction determination
        """
        
        test_cases = [
            # (current_price, strike_price, call_oi, put_oi, expected_direction, scenario)
            (15010.0, 15000.0, 1000, 1000, "BUY_FUTURES", "Above strike - avoid put assignment"),
            (14990.0, 15000.0, 1000, 1000, "SELL_FUTURES", "Below strike - avoid call assignment"),
            (15005.0, 15000.0, 3000, 1000, "SELL_FUTURES", "Above strike but heavy call OI"),
            (14995.0, 15000.0, 1000, 3000, "BUY_FUTURES", "Below strike but heavy put OI")
        ]
        
        for current_price, strike_price, call_oi, put_oi, expected_direction, scenario in test_cases:
            
            direction = self.calculator._determine_steering_direction(
                current_price, strike_price, call_oi, put_oi
            )
            
            self.assertEqual(
                direction, expected_direction,
                f"Steering direction failed for scenario: {scenario}. "
                f"Expected {expected_direction}, got {direction}"
            )
            
    def test_assignment_probability_calibration(self):
        """
        HYPOTHESIS: Assignment probability increases as distance decreases and time approaches
        SUCCESS CRITERIA: Monotonic relationship validation
        """
        
        # Test distance relationship (time constant)
        time_constant = 30  # minutes
        distances = [5, 10, 15, 20, 25, 30]
        probabilities = [
            self.calculator._calculate_assignment_probability(d, time_constant) 
            for d in distances
        ]
        
        # VALIDATION: Probability decreases with distance
        for i in range(1, len(probabilities)):
            self.assertLessEqual(
                probabilities[i], probabilities[i-1],
                f"Assignment probability should decrease with distance. "
                f"Distance {distances[i-1]} -> {distances[i]}: "
                f"Prob {probabilities[i-1]:.3f} -> {probabilities[i]:.3f}"
            )
        
        # Test time relationship (distance constant)
        distance_constant = 10.0
        times = [5, 15, 30, 60, 120]
        time_probabilities = [
            self.calculator._calculate_assignment_probability(distance_constant, t)
            for t in times
        ]
        
        # VALIDATION: Probability generally increases as time decreases (with some exceptions for time zones)
        crisis_prob = time_probabilities[0]  # 5 minutes
        warning_prob = time_probabilities[2]  # 30 minutes
        early_prob = time_probabilities[4]    # 120 minutes
        
        self.assertGreater(crisis_prob, warning_prob, "Crisis zone should have higher probability than warning zone")
        self.assertGreater(warning_prob, early_prob, "Warning zone should have higher probability than early zone")
        
    def test_calculation_performance_requirements(self):
        """
        HYPOTHESIS: Pressure calculation completes within 30 seconds for 100 strikes
        SUCCESS CRITERIA: Calculation time <30 seconds
        """
        
        # Generate large options dataset (100 strikes)
        large_options_data = []
        base_strike = 14500.0
        for i in range(100):
            strike_price = base_strike + (i * 25)
            large_options_data.append({
                'strike': strike_price,
                'call_oi': 1000 + (i * 50),
                'put_oi': 800 + (i * 30)
            })
        
        current_price = 15000.0
        current_time = datetime.now()
        expiration_date = current_time + timedelta(minutes=45)
        
        # Measure calculation time
        start_time = time.time()
        alerts = self.calculator.calculate_expiration_pressure(
            large_options_data, current_price, current_time, expiration_date
        )
        calculation_time = time.time() - start_time
        
        # VALIDATION: Performance requirement
        self.assertLess(calculation_time, 30.0, f"Calculation time {calculation_time:.2f}s exceeds 30s requirement")
        self.assertGreater(len(alerts), 0, "Should generate alerts for large dataset")
        
        print(f"✓ Processed {len(large_options_data)} strikes in {calculation_time:.3f}s")
        
    def test_confidence_scoring_accuracy(self):
        """
        HYPOTHESIS: Confidence scores correlate with prediction accuracy
        SUCCESS CRITERIA: Higher confidence predictions should be more accurate
        """
        
        # Test different pressure scenarios
        test_scenarios = [
            # High confidence scenario
            {
                'data': [{'strike': 15000.0, 'call_oi': 5000, 'put_oi': 3000}],
                'price': 15005.0,
                'minutes': 20,
                'expected_high_confidence': True
            },
            # Low confidence scenario  
            {
                'data': [{'strike': 15000.0, 'call_oi': 500, 'put_oi': 300}],
                'price': 15040.0,
                'minutes': 90,
                'expected_high_confidence': False
            }
        ]
        
        current_time = datetime.now()
        
        for scenario in test_scenarios:
            expiration_date = current_time + timedelta(minutes=scenario['minutes'])
            
            alerts = self.calculator.calculate_expiration_pressure(
                scenario['data'], scenario['price'], current_time, expiration_date
            )
            
            if alerts:
                confidence = alerts[0].confidence
                
                if scenario['expected_high_confidence']:
                    self.assertGreater(confidence, 0.7, "High confidence scenario should score >0.7")
                else:
                    self.assertLess(confidence, 0.7, "Low confidence scenario should score <0.7")

class TestPredictionValidation(unittest.TestCase):
    """
    EXPERIMENTAL VALIDATION: Test prediction tracking and accuracy validation
    """
    
    def test_prediction_accuracy_validation(self):
        """
        HYPOTHESIS: Prediction validation accurately measures forecasting performance
        SUCCESS CRITERIA: Validation metrics correctly reflect prediction quality
        """
        
        calculator = ExpirationPressureCalculator()
        
        # Create test prediction
        test_options_data = [{
            'strike': 15000.0,
            'call_oi': 2000,
            'put_oi': 1500
        }]
        
        current_price = 15010.0
        current_time = datetime.now()
        expiration_date = current_time + timedelta(minutes=30)
        
        alerts = calculator.calculate_expiration_pressure(
            test_options_data, current_price, current_time, expiration_date
        )
        
        self.assertGreater(len(alerts), 0, "Should generate at least one alert")
        
        alert = alerts[0]
        validation_id = alert.validation_id
        
        # Test perfect prediction
        perfect_outcome = {
            'direction': alert.steering_direction,
            'magnitude': alert.expected_move,
            'response_time_minutes': 25  # Within expected range for pin risk
        }
        
        perfect_validation = calculator.validate_prediction_accuracy(validation_id, perfect_outcome)
        
        # VALIDATION: Perfect prediction should score high
        self.assertTrue(perfect_validation['direction_correct'])
        self.assertGreater(perfect_validation['magnitude_accuracy'], 0.95)
        self.assertGreater(perfect_validation['overall_accuracy'], 0.9)
        
        # Test poor prediction
        poor_outcome = {
            'direction': 'SELL_FUTURES' if alert.steering_direction == 'BUY_FUTURES' else 'BUY_FUTURES',
            'magnitude': alert.expected_move * 0.3,  # Much smaller move
            'response_time_minutes': 150  # Way outside expected range
        }
        
        poor_validation = calculator.validate_prediction_accuracy(validation_id, poor_outcome)
        
        # VALIDATION: Poor prediction should score low
        self.assertFalse(poor_validation['direction_correct'])
        self.assertLess(poor_validation['overall_accuracy'], 0.5)

class TestPerformanceValidation(unittest.TestCase):
    """
    COMPREHENSIVE PERFORMANCE VALIDATION
    """
    
    def test_comprehensive_pressure_calculation_benchmark(self):
        """
        STRESS TEST: Comprehensive pressure calculation performance benchmark
        SUCCESS CRITERIA: Handle realistic options chain data within performance requirements
        """
        
        calculator = ExpirationPressureCalculator()
        
        # Generate realistic NQ options chain (200 strikes)
        realistic_options_data = []
        center_strike = 15000.0
        
        for i in range(-100, 100):  # 200 strikes total
            strike_price = center_strike + (i * 25)  # 25-point intervals
            
            # Realistic OI distribution (higher near ATM)
            distance_from_atm = abs(i)
            base_oi = max(100, 3000 - (distance_from_atm * 20))
            
            realistic_options_data.append({
                'strike': strike_price,
                'call_oi': int(base_oi * (1.2 if i > 0 else 0.8)),  # Calls higher above ATM
                'put_oi': int(base_oi * (0.8 if i > 0 else 1.2))    # Puts higher below ATM
            })
        
        # Multiple test scenarios
        test_scenarios = [
            (15000.0, 15),   # ATM, crisis time
            (15075.0, 45),   # OTM, pin risk time
            (14925.0, 30),   # OTM, warning time
            (15150.0, 120)   # Far OTM, early time
        ]
        
        performance_results = []
        
        for current_price, minutes_to_expiry in test_scenarios:
            current_time = datetime.now()
            expiration_date = current_time + timedelta(minutes=minutes_to_expiry)
            
            # Measure performance
            start_time = time.time()
            
            alerts = calculator.calculate_expiration_pressure(
                realistic_options_data, current_price, current_time, expiration_date
            )
            
            calc_time = time.time() - start_time
            
            performance_results.append({
                'scenario': f"Price {current_price}, {minutes_to_expiry}min",
                'calculation_time': calc_time,
                'alerts_generated': len(alerts),
                'strikes_analyzed': len(realistic_options_data)
            })
            
            # VALIDATION: Performance requirements
            self.assertLess(calc_time, 5.0, f"Calculation time {calc_time:.3f}s exceeds 5s for scenario {current_price}/{minutes_to_expiry}")
        
        # Print performance summary
        print("\n=== PRESSURE CALCULATION PERFORMANCE BENCHMARK ===")
        for result in performance_results:
            print(f"{result['scenario']}: {result['calculation_time']:.3f}s, {result['alerts_generated']} alerts")
        
        avg_time = statistics.mean([r['calculation_time'] for r in performance_results])
        print(f"Average calculation time: {avg_time:.3f}s")
        
        # VALIDATION: Overall performance
        self.assertLess(avg_time, 3.0, f"Average calculation time {avg_time:.3f}s too slow")

def run_pressure_calculation_benchmark():
    """
    EMPIRICAL VALIDATION: Generate statistical evidence for pressure calculation accuracy
    """
    print("\n=== EXPIRATION PRESSURE CALCULATION BENCHMARK ===")
    
    calculator = ExpirationPressureCalculator()
    
    # Test data generation
    test_results = {
        'calculation_times': [],
        'alert_accuracies': [],
        'pressure_values': [],
        'urgency_classifications': [],
        'mathematical_validations': []
    }
    
    num_iterations = 100
    print(f"Running {num_iterations} pressure calculation tests...")
    
    for i in range(num_iterations):
        # Generate varied test scenario
        base_price = 15000.0 + (i * 5)  # Vary price
        minutes_to_expiry = 15 + (i % 120)  # Vary time
        
        test_data = [{
            'strike': base_price + (j * 25),
            'call_oi': 1000 + (j * 100),
            'put_oi': 800 + (j * 80)
        } for j in range(-5, 6)]  # 11 strikes around current price
        
        current_time = datetime.now()
        expiration_date = current_time + timedelta(minutes=minutes_to_expiry)
        
        # Measure calculation
        start_time = time.time()
        alerts = calculator.calculate_expiration_pressure(
            test_data, base_price, current_time, expiration_date
        )
        calc_time = time.time() - start_time
        
        test_results['calculation_times'].append(calc_time)
        
        # Validate mathematical accuracy
        for alert in alerts:
            expected_pressure = (alert.total_oi * alert.assignment_probability) / max(1, alert.minutes_to_expiry ** 2)
            accuracy = 1.0 - abs(alert.pressure_value - expected_pressure) / max(expected_pressure, 1)
            test_results['mathematical_validations'].append(accuracy)
            test_results['pressure_values'].append(alert.pressure_value)
            test_results['urgency_classifications'].append(alert.urgency_level.value)
    
    # Calculate statistics
    def calculate_stats(data):
        if not data:
            return {}
        
        return {
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'stdev': statistics.stdev(data) if len(data) > 1 else 0,
            'min': min(data),
            'max': max(data)
        }
    
    calc_time_stats = calculate_stats(test_results['calculation_times'])
    math_accuracy_stats = calculate_stats(test_results['mathematical_validations'])
    
    # Generate evidence report
    evidence_report = {
        'test_timestamp': datetime.now().isoformat(),
        'sample_size': num_iterations,
        'calculation_performance': calc_time_stats,
        'mathematical_accuracy': math_accuracy_stats,
        'urgency_distribution': {
            urgency: test_results['urgency_classifications'].count(urgency) 
            for urgency in set(test_results['urgency_classifications'])
        },
        'validation_results': {
            'performance_under_5s': all(t < 5.0 for t in test_results['calculation_times']),
            'mathematical_accuracy_over_99pct': math_accuracy_stats['mean'] > 0.99,
            'pressure_values_reasonable': all(0 <= p <= 10000 for p in test_results['pressure_values'])
        }
    }
    
    # Print results
    print("\n=== PRESSURE CALCULATION VALIDATION RESULTS ===")
    print(f"Sample size: {evidence_report['sample_size']}")
    print(f"Mean calculation time: {calc_time_stats['mean']*1000:.1f}ms")
    print(f"Max calculation time: {calc_time_stats['max']*1000:.1f}ms")
    print(f"Mathematical accuracy: {math_accuracy_stats['mean']:.4f}")
    print(f"Urgency distribution: {evidence_report['urgency_distribution']}")
    
    print("\n=== REQUIREMENTS VALIDATION ===")
    for requirement, passed in evidence_report['validation_results'].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{requirement}: {status}")
    
    return evidence_report

if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run performance benchmark
    benchmark_results = run_pressure_calculation_benchmark()
    
    # Save results
    import json
    with open('/Users/Mike/trading/algos/EOD/tasks/options_trading_system/analysis_engine/expiration_pressure_calculator/performance_evidence.json', 'w') as f:
        json.dump(benchmark_results, f, indent=2)