from solution import ExpirationPressureCalculator
from datetime import datetime, timedelta
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Initialize calculator
calculator = ExpirationPressureCalculator(validation_mode=True)

# Simple test data
test_data = [
    {
        'strike': 15000.0,
        'call_oi': 2500,
        'put_oi': 1800
    }
]

current_price = 15010.0
current_time = datetime.now()
expiration_date = current_time + timedelta(minutes=30)

print("=== DEBUGGING PRESSURE CALCULATION ===")
print(f"Current price: {current_price}")
print(f"Minutes to expiry: 30")
print(f"Strike: 15000.0")
print(f"Total OI: 4300")
print(f"Distance to strike: {abs(current_price - 15000.0)}")

# Test assignment probability directly
distance = abs(current_price - 15000.0)
assignment_prob = calculator._calculate_assignment_probability(distance, 30)
print(f"Assignment probability: {assignment_prob:.3f}")

total_oi = 4300
assignment_risk = total_oi * assignment_prob
pressure = assignment_risk / (30 ** 2)
print(f"Assignment risk: {assignment_risk:.1f}")
print(f"Calculated pressure: {pressure:.1f}")
print(f"Pressure threshold: {calculator.PRESSURE_THRESHOLD}")
print(f"Pressure > threshold: {pressure > calculator.PRESSURE_THRESHOLD}")

# Run full calculation
alerts = calculator.calculate_expiration_pressure(
    test_data, current_price, current_time, expiration_date
)

print(f"\nAlerts generated: {len(alerts)}")
for alert in alerts:
    print(f"Alert: {alert}")