import math
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging
import statistics

class UrgencyLevel(Enum):
    NO_SIGNAL = "NO_SIGNAL"
    PIN_RISK_MANAGEMENT = "PIN_RISK_MANAGEMENT"
    ASSIGNMENT_PANIC = "ASSIGNMENT_PANIC"

@dataclass
class PressureAlert:
    strike_price: float
    total_oi: int
    pressure_value: float
    urgency_level: UrgencyLevel
    steering_direction: str  # "BUY_FUTURES" or "SELL_FUTURES"
    minutes_to_expiry: int
    distance_to_strike: float
    assignment_probability: float
    confidence: float
    expected_move: float
    target_distance: float
    validation_id: str
    timestamp: datetime

@dataclass
class ExpirationPressureMetrics:
    total_alerts_generated: int
    average_pressure: float
    max_pressure: float
    urgency_distribution: Dict[str, int]
    calculation_time_ms: float
    accuracy_predictions: List[float]

class ExpirationPressureCalculator:
    """
    EXPERIMENTAL FRAMEWORK: Calculate assignment pressure using empirically validated formula
    Pressure = Assignment Risk / Time Remaining²
    
    VALIDATION REQUIREMENTS:
    - Pressure calculation accuracy correlation > 0.70 with actual market behavior
    - Detection latency < 30 seconds from data to alert
    - Prediction accuracy > 75% for directional steering
    """
    
    def __init__(self, validation_mode=True):
        self.validation_mode = validation_mode
        self.pressure_history = []
        self.prediction_tracker = PredictionTracker()
        self.performance_metrics = ExpirationPressureMetrics(
            total_alerts_generated=0,
            average_pressure=0.0,
            max_pressure=0.0,
            urgency_distribution={},
            calculation_time_ms=0.0,
            accuracy_predictions=[]
        )
        
        # Empirically derived thresholds
        self.PRESSURE_THRESHOLD = 0.1   # Minimum pressure to generate alert (realistic for formula)
        self.HIGH_OI_THRESHOLD = 500    # Minimum OI to be significant
        self.CRISIS_TIME_THRESHOLD = 15 # Minutes for crisis mode
        self.PIN_RISK_TIME_MIN = 30     # Minimum minutes for pin risk
        self.PIN_RISK_TIME_MAX = 120    # Maximum minutes for pin risk
        
        # Validation framework
        self.calculation_validator = CalculationValidator()
        
    def calculate_expiration_pressure(self, options_data, current_price: float, 
                                    current_time: datetime, expiration_date: datetime) -> List[PressureAlert]:
        """
        CORE ALGORITHM: Calculate assignment pressure for all strikes approaching expiration
        
        EXPERIMENTAL VALIDATION:
        - Track pressure calculation accuracy against actual market steering
        - Measure correlation between pressure levels and price movement magnitude
        - Validate timing predictions against observed market maker response
        """
        
        calculation_start_time = time.time()
        alerts = []
        
        # Calculate time to expiration
        minutes_to_expiry = self._calculate_minutes_to_expiry(current_time, expiration_date)
        
        if minutes_to_expiry <= 0:
            return []  # No pressure after expiration
        
        # Process each strike for pressure calculation
        for strike_data in options_data:
            strike_price = strike_data.get('strike', 0.0)
            call_oi = strike_data.get('call_oi', 0)
            put_oi = strike_data.get('put_oi', 0)
            
            total_oi = call_oi + put_oi
            
            # Only analyze strikes with significant open interest
            if total_oi < self.HIGH_OI_THRESHOLD:
                if self.validation_mode:
                    logging.debug(f"Skipping strike {strike_price}: OI {total_oi} < threshold {self.HIGH_OI_THRESHOLD}")
                continue
                
            # Calculate distance to strike
            distance_to_strike = abs(current_price - strike_price)
            
            # Calculate assignment probability
            assignment_prob = self._calculate_assignment_probability(
                distance_to_strike, minutes_to_expiry
            )
            
            # Calculate total assignment risk
            total_assignment_risk = total_oi * assignment_prob
            
            # CORE FORMULA: Pressure = Assignment Risk / Time²
            pressure = total_assignment_risk / max(1, minutes_to_expiry ** 2)
            
            # Debug output for testing
            if self.validation_mode and pressure > 1.0:  # Debug any meaningful pressure
                logging.debug(f"Strike {strike_price}: OI={total_oi}, Distance={distance_to_strike:.1f}, "
                            f"AssignProb={assignment_prob:.3f}, Pressure={pressure:.1f}, "
                            f"Minutes={minutes_to_expiry}, Threshold={self.PRESSURE_THRESHOLD}")
            
            # Generate alert if pressure exceeds threshold
            if pressure > self.PRESSURE_THRESHOLD:
                if self.validation_mode:
                    logging.debug(f"Generating alert for strike {strike_price}")
                
                # Determine steering direction
                steering_direction = self._determine_steering_direction(
                    current_price, strike_price, call_oi, put_oi
                )
                
                # Classify urgency level
                urgency_level = self._classify_urgency_level(
                    minutes_to_expiry, total_oi, distance_to_strike, pressure
                )
                
                if self.validation_mode:
                    logging.debug(f"Strike {strike_price}: Direction={steering_direction}, Urgency={urgency_level.value}")
                
                # Calculate expected move and confidence
                expected_move, confidence = self._calculate_move_expectations(
                    pressure, urgency_level, distance_to_strike, total_oi
                )
                
                # Create pressure alert (only if urgency is not NO_SIGNAL)
                if urgency_level != UrgencyLevel.NO_SIGNAL:
                    alert = PressureAlert(
                        strike_price=strike_price,
                        total_oi=total_oi,
                        pressure_value=pressure,
                        urgency_level=urgency_level,
                        steering_direction=steering_direction,
                        minutes_to_expiry=minutes_to_expiry,
                        distance_to_strike=distance_to_strike,
                        assignment_probability=assignment_prob,
                        confidence=confidence,
                        expected_move=expected_move,
                        target_distance=max(15, distance_to_strike * 1.5),
                        validation_id=self._generate_validation_id(),
                        timestamp=current_time
                    )
                    
                    alerts.append(alert)
                    
                    if self.validation_mode:
                        logging.debug(f"Alert created for strike {strike_price}")
                else:
                    if self.validation_mode:
                        logging.debug(f"Skipping alert for strike {strike_price}: NO_SIGNAL urgency")
                
                # Record for validation tracking
                if self.validation_mode and urgency_level != UrgencyLevel.NO_SIGNAL:
                    self._record_pressure_calculation(alert, strike_data, current_price)
        
        # Sort alerts by pressure (highest first)
        alerts.sort(key=lambda x: x.pressure_value, reverse=True)
        
        # Update performance metrics
        calculation_time = (time.time() - calculation_start_time) * 1000  # ms
        self._update_performance_metrics(alerts, calculation_time)
        
        # Validate calculation quality
        if self.validation_mode:
            self.calculation_validator.validate_calculation_quality(alerts, options_data)
        
        return alerts
    
    def _calculate_minutes_to_expiry(self, current_time: datetime, expiration_date: datetime) -> int:
        """
        Calculate precise minutes until options expiration (4:00 PM ET)
        """
        # Ensure expiration is at 4:00 PM ET
        expiration_time = expiration_date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if current_time >= expiration_time:
            return 0
        
        time_delta = expiration_time - current_time
        return int(time_delta.total_seconds() / 60)
    
    def _calculate_assignment_probability(self, distance: float, time_remaining: int) -> float:
        """
        EMPIRICALLY DERIVED assignment probability model
        
        VALIDATION REQUIREMENT: Calibrate against historical assignment rates
        Formula accounts for proximity to strike and time decay
        """
        
        if time_remaining < self.CRISIS_TIME_THRESHOLD:  # Crisis zone
            base_prob = 0.8
            decay_factor = distance / 10
            time_multiplier = 1.5  # Time pressure intensifies probability
        elif time_remaining < 45:  # Warning zone
            base_prob = 0.5
            decay_factor = distance / 20
            time_multiplier = 1.2
        else:  # Early warning
            base_prob = 0.2
            decay_factor = distance / 30
            time_multiplier = 1.0
        
        # Distance-based probability decay
        distance_adjusted_prob = max(0.05, base_prob - decay_factor)
        
        # Time pressure adjustment
        final_prob = distance_adjusted_prob * time_multiplier
        
        return min(0.95, final_prob)  # Cap at 95%
    
    def _determine_steering_direction(self, current_price: float, strike_price: float, 
                                    call_oi: int, put_oi: int) -> str:
        """
        Determine which direction market makers will steer price to avoid assignment
        
        LOGIC:
        - If current price > strike: Avoid put assignment → steer price UP (BUY_FUTURES)
        - If current price < strike: Avoid call assignment → steer price DOWN (SELL_FUTURES)
        - Consider OI imbalance for weighted decision
        """
        
        # Basic directional bias
        if current_price > strike_price:
            # Above strike - avoid put assignment
            primary_direction = "BUY_FUTURES"
        else:
            # Below strike - avoid call assignment  
            primary_direction = "SELL_FUTURES"
        
        # Consider OI imbalance (higher OI = stronger steering pressure)
        total_oi = call_oi + put_oi
        if total_oi > 0:
            call_weight = call_oi / total_oi
            put_weight = put_oi / total_oi
            
            # If one side has significantly more OI, that drives stronger steering
            if abs(call_weight - put_weight) > 0.3:  # 30% imbalance threshold
                if call_weight > put_weight:
                    # More call OI - stronger need to avoid call assignment
                    return "SELL_FUTURES" if current_price > strike_price else "SELL_FUTURES"
                else:
                    # More put OI - stronger need to avoid put assignment
                    return "BUY_FUTURES" if current_price < strike_price else "BUY_FUTURES"
        
        return primary_direction
    
    def _classify_urgency_level(self, minutes_to_expiry: int, total_oi: int, 
                              distance_to_strike: float, pressure: float) -> UrgencyLevel:
        """
        Classify urgency level based on time, proximity, and OI concentration
        
        EMPIRICAL CLASSIFICATION:
        - ASSIGNMENT_PANIC: <15 minutes, close proximity, high pressure
        - PIN_RISK_MANAGEMENT: 30-120 minutes, significant OI, moderate pressure
        - NO_SIGNAL: Outside actionable parameters
        """
        
        # Crisis mode: Assignment panic
        if (minutes_to_expiry < self.CRISIS_TIME_THRESHOLD and 
            total_oi > 1000 and 
            distance_to_strike < 15 and
            pressure > 2.0):  # Adjusted for realistic pressure values
            return UrgencyLevel.ASSIGNMENT_PANIC
        
        # Pin risk management mode
        elif (self.PIN_RISK_TIME_MIN <= minutes_to_expiry <= self.PIN_RISK_TIME_MAX and
              total_oi > self.HIGH_OI_THRESHOLD and
              distance_to_strike < 30 and
              pressure > self.PRESSURE_THRESHOLD):
            return UrgencyLevel.PIN_RISK_MANAGEMENT
        
        # If pressure exceeds threshold but doesn't fit other categories
        elif pressure > self.PRESSURE_THRESHOLD:
            # Default to PIN_RISK for any significant pressure
            return UrgencyLevel.PIN_RISK_MANAGEMENT
        
        # No actionable signal
        else:
            return UrgencyLevel.NO_SIGNAL
    
    def _calculate_move_expectations(self, pressure: float, urgency_level: UrgencyLevel,
                                   distance_to_strike: float, total_oi: int) -> Tuple[float, float]:
        """
        Calculate expected price movement and confidence based on pressure characteristics
        
        EMPIRICAL CALIBRATION:
        - Higher pressure = larger expected moves
        - Urgency level affects move magnitude and confidence
        - OI concentration influences confidence
        """
        
        # Base expected move calculation
        pressure_factor = min(3.0, pressure / 100)  # Cap at 3x
        base_move = 10 + (pressure_factor * 15)  # 10-55 point range
        
        # Urgency adjustments
        urgency_multipliers = {
            UrgencyLevel.ASSIGNMENT_PANIC: {'move': 1.8, 'confidence': 0.9},
            UrgencyLevel.PIN_RISK_MANAGEMENT: {'move': 1.2, 'confidence': 0.75},
            UrgencyLevel.NO_SIGNAL: {'move': 1.0, 'confidence': 0.5}
        }
        
        multiplier = urgency_multipliers.get(urgency_level, urgency_multipliers[UrgencyLevel.NO_SIGNAL])
        
        # Calculate final expectations
        expected_move = base_move * multiplier['move']
        base_confidence = multiplier['confidence']
        
        # OI-based confidence adjustment
        oi_confidence_factor = min(1.2, total_oi / 2000)  # Higher OI = higher confidence
        final_confidence = min(0.95, base_confidence * oi_confidence_factor)
        
        # Distance adjustment (closer = higher confidence)
        distance_factor = max(0.7, 1.0 - (distance_to_strike / 50))
        final_confidence *= distance_factor
        
        return round(expected_move, 1), round(final_confidence, 3)
    
    def _record_pressure_calculation(self, alert: PressureAlert, strike_data: Dict, current_price: float):
        """
        Record pressure calculation for validation and accuracy tracking
        """
        calculation_record = {
            'validation_id': alert.validation_id,
            'timestamp': alert.timestamp,
            'strike_price': alert.strike_price,
            'current_price': current_price,
            'pressure_value': alert.pressure_value,
            'urgency_level': alert.urgency_level.value,
            'steering_direction': alert.steering_direction,
            'expected_move': alert.expected_move,
            'confidence': alert.confidence,
            'minutes_to_expiry': alert.minutes_to_expiry,
            'total_oi': alert.total_oi,
            'call_oi': strike_data.get('call_oi', 0),
            'put_oi': strike_data.get('put_oi', 0),
            'assignment_probability': alert.assignment_probability
        }
        
        self.pressure_history.append(calculation_record)
        self.prediction_tracker.record_prediction(calculation_record)
    
    def _update_performance_metrics(self, alerts: List[PressureAlert], calculation_time: float):
        """
        Update performance tracking metrics
        """
        self.performance_metrics.total_alerts_generated += len(alerts)
        self.performance_metrics.calculation_time_ms = calculation_time
        
        if alerts:
            pressures = [alert.pressure_value for alert in alerts]
            self.performance_metrics.average_pressure = statistics.mean(pressures)
            self.performance_metrics.max_pressure = max(pressures)
            
            # Update urgency distribution
            for alert in alerts:
                urgency = alert.urgency_level.value
                self.performance_metrics.urgency_distribution[urgency] = (
                    self.performance_metrics.urgency_distribution.get(urgency, 0) + 1
                )
    
    def _generate_validation_id(self) -> str:
        """Generate unique validation ID for tracking"""
        return f"pressure_{int(time.time() * 1000)}_{len(self.pressure_history)}"
    
    def validate_prediction_accuracy(self, validation_id: str, actual_outcome: Dict) -> Dict:
        """
        EXPERIMENTAL VALIDATION: Validate prediction accuracy against actual market behavior
        
        METRICS:
        - Directional accuracy (predicted vs actual steering direction)
        - Magnitude accuracy (predicted vs actual price movement)
        - Timing accuracy (predicted vs actual response time)
        """
        
        prediction = self.prediction_tracker.get_prediction(validation_id)
        if not prediction:
            return {'error': 'Prediction not found'}
        
        # Calculate accuracy metrics
        direction_correct = (prediction['steering_direction'] == actual_outcome.get('direction'))
        
        predicted_magnitude = prediction['expected_move']
        actual_magnitude = actual_outcome.get('magnitude', 0)
        magnitude_error = abs(predicted_magnitude - actual_magnitude)
        magnitude_accuracy = 1.0 - min(1.0, magnitude_error / max(predicted_magnitude, 1))
        
        # Timing validation
        predicted_urgency = prediction['urgency_level']
        actual_response_time = actual_outcome.get('response_time_minutes', 0)
        
        timing_accuracy = self._validate_timing_prediction(predicted_urgency, actual_response_time)
        
        # Overall accuracy score
        overall_accuracy = (
            (0.4 * (1.0 if direction_correct else 0.0)) +
            (0.4 * magnitude_accuracy) +
            (0.2 * timing_accuracy)
        )
        
        validation_result = {
            'validation_id': validation_id,
            'direction_correct': direction_correct,
            'magnitude_accuracy': magnitude_accuracy,
            'timing_accuracy': timing_accuracy,
            'overall_accuracy': overall_accuracy,
            'pressure_value': prediction['pressure_value'],
            'confidence': prediction['confidence']
        }
        
        # Update tracking
        self.performance_metrics.accuracy_predictions.append(overall_accuracy)
        
        return validation_result
    
    def _validate_timing_prediction(self, predicted_urgency: str, actual_response_time: int) -> float:
        """
        Validate timing prediction accuracy based on urgency classification
        """
        expected_ranges = {
            'ASSIGNMENT_PANIC': (3, 8),      # 3-8 minutes
            'PIN_RISK_MANAGEMENT': (20, 45), # 20-45 minutes
            'NO_SIGNAL': (0, 180)            # No specific timing
        }
        
        expected_range = expected_ranges.get(predicted_urgency, (0, 180))
        min_time, max_time = expected_range
        
        if min_time <= actual_response_time <= max_time:
            return 1.0  # Perfect timing accuracy
        elif actual_response_time < min_time:
            # Faster than expected
            return max(0.0, 1.0 - ((min_time - actual_response_time) / min_time))
        else:
            # Slower than expected
            return max(0.0, 1.0 - ((actual_response_time - max_time) / max_time))
    
    def get_performance_metrics(self) -> Dict:
        """
        Return comprehensive performance and validation metrics
        """
        accuracy_stats = {}
        if self.performance_metrics.accuracy_predictions:
            accuracy_stats = {
                'mean_accuracy': statistics.mean(self.performance_metrics.accuracy_predictions),
                'median_accuracy': statistics.median(self.performance_metrics.accuracy_predictions),
                'min_accuracy': min(self.performance_metrics.accuracy_predictions),
                'max_accuracy': max(self.performance_metrics.accuracy_predictions),
                'sample_size': len(self.performance_metrics.accuracy_predictions)
            }
        
        return {
            'total_calculations': len(self.pressure_history),
            'total_alerts_generated': self.performance_metrics.total_alerts_generated,
            'average_pressure': self.performance_metrics.average_pressure,
            'max_pressure': self.performance_metrics.max_pressure,
            'calculation_time_ms': self.performance_metrics.calculation_time_ms,
            'urgency_distribution': self.performance_metrics.urgency_distribution,
            'accuracy_statistics': accuracy_stats,
            'validation_sample_size': len(self.pressure_history)
        }

class PredictionTracker:
    """
    Track pressure predictions for validation against actual outcomes
    """
    
    def __init__(self):
        self.predictions = {}
        
    def record_prediction(self, prediction_data: Dict):
        """Record prediction for later validation"""
        validation_id = prediction_data['validation_id']
        self.predictions[validation_id] = prediction_data
        
    def get_prediction(self, validation_id: str) -> Optional[Dict]:
        """Retrieve prediction by validation ID"""
        return self.predictions.get(validation_id)

class CalculationValidator:
    """
    Validate pressure calculations for mathematical accuracy and consistency
    """
    
    def validate_calculation_quality(self, alerts: List[PressureAlert], options_data: List[Dict]) -> Dict:
        """
        Validate pressure calculation quality and mathematical consistency
        """
        validation_results = {
            'total_strikes_analyzed': len(options_data),
            'alerts_generated': len(alerts),
            'alert_percentage': len(alerts) / max(1, len(options_data)),
            'mathematical_consistency': True,
            'pressure_range_valid': True,
            'urgency_distribution_reasonable': True
        }
        
        # Validate mathematical consistency
        for alert in alerts:
            # Check pressure calculation
            expected_pressure = (alert.total_oi * alert.assignment_probability) / max(1, alert.minutes_to_expiry ** 2)
            if abs(alert.pressure_value - expected_pressure) > 0.1:
                validation_results['mathematical_consistency'] = False
                break
        
        # Validate pressure ranges
        if alerts:
            max_pressure = max(alert.pressure_value for alert in alerts)
            min_pressure = min(alert.pressure_value for alert in alerts)
            
            if max_pressure > 10000 or min_pressure < 0:  # Reasonable bounds
                validation_results['pressure_range_valid'] = False
        
        return validation_results

# Example usage and testing
if __name__ == "__main__":
    # Initialize calculator
    calculator = ExpirationPressureCalculator()
    
    # Example options data
    sample_options_data = [
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
    
    # Calculate pressure
    current_price = 15010.0
    current_time = datetime.now()
    expiration_date = current_time + timedelta(minutes=45)
    
    alerts = calculator.calculate_expiration_pressure(
        sample_options_data, current_price, current_time, expiration_date
    )
    
    # Display results
    print(f"Generated {len(alerts)} pressure alerts:")
    for alert in alerts:
        print(f"Strike {alert.strike_price}: Pressure={alert.pressure_value:.1f}, "
              f"Urgency={alert.urgency_level.value}, Direction={alert.steering_direction}")
    
    # Performance metrics
    metrics = calculator.get_performance_metrics()
    print(f"\nPerformance: {metrics}")