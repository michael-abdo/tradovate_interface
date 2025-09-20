#!/usr/bin/env python3
"""
Test validation for DEAD Simple Volume Spike Strategy
Tests the core detection logic with real-world scenarios
"""

import unittest
from datetime import datetime, timezone
from solution import DeadSimpleVolumeSpike, InstitutionalSignal

class TestDeadSimpleStrategy(unittest.TestCase):
    """Test cases for DEAD Simple strategy implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = DeadSimpleVolumeSpike()
        self.current_price = 21870
    
    def test_extreme_volume_spike_detection(self):
        """Test detection of extreme volume spike (55x ratio)"""
        strike_data = {
            'strike': 21840,
            'optionType': 'PUT',
            'volume': 2750,
            'openInterest': 50,
            'lastPrice': 35.5,
            'expirationDate': '2024-01-10'
        }
        
        signal = self.analyzer.analyze_strike(strike_data, self.current_price)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.vol_oi_ratio, 55.0)
        self.assertEqual(signal.confidence, 'EXTREME')
        self.assertEqual(signal.direction, 'SHORT')
        self.assertEqual(signal.target_price, 21840)
        self.assertGreater(signal.dollar_size, 1_000_000)  # $1.95M
    
    def test_minimum_threshold_filtering(self):
        """Test that low volume/OI ratios are filtered out"""
        strike_data = {
            'strike': 21900,
            'optionType': 'CALL',
            'volume': 100,
            'openInterest': 50,  # 2x ratio - should be filtered
            'lastPrice': 40.0,
            'expirationDate': '2024-01-10'
        }
        
        signal = self.analyzer.analyze_strike(strike_data, self.current_price)
        self.assertIsNone(signal)
    
    def test_dollar_size_threshold(self):
        """Test that small dollar volumes are filtered out"""
        strike_data = {
            'strike': 21900,
            'optionType': 'CALL',
            'volume': 600,  # Meets volume threshold
            'openInterest': 50,  # 12x ratio - meets ratio threshold
            'lastPrice': 5.0,  # But only $60K total - below $100K threshold
            'expirationDate': '2024-01-10'
        }
        
        signal = self.analyzer.analyze_strike(strike_data, self.current_price)
        self.assertIsNone(signal)
    
    def test_confidence_levels(self):
        """Test correct confidence level assignment"""
        test_cases = [
            (60, 'EXTREME'),    # 60x ratio
            (45, 'VERY_HIGH'),  # 45x ratio
            (25, 'HIGH'),       # 25x ratio
            (15, 'MODERATE'),   # 15x ratio
        ]
        
        for vol_oi_ratio, expected_confidence in test_cases:
            confidence = self.analyzer._calculate_confidence(vol_oi_ratio)
            self.assertEqual(confidence, expected_confidence)
    
    def test_institutional_flow_detection(self):
        """Test full options chain analysis"""
        options_chain = [
            # Extreme signal - should be first
            {
                'strike': 21840,
                'optionType': 'PUT',
                'volume': 2750,
                'openInterest': 50,
                'lastPrice': 35.5,
            },
            # High signal - should be second
            {
                'strike': 21900,
                'optionType': 'CALL',
                'volume': 2000,
                'openInterest': 80,
                'lastPrice': 25.0,
            },
            # Noise - should be filtered
            {
                'strike': 21820,
                'optionType': 'PUT',
                'volume': 50,
                'openInterest': 100,
                'lastPrice': 20.0,
            },
        ]
        
        signals = self.analyzer.find_institutional_flow(options_chain, self.current_price)
        
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0].strike, 21840)  # Extreme signal first
        self.assertEqual(signals[0].confidence, 'EXTREME')
        self.assertEqual(signals[1].strike, 21900)  # High signal second
        self.assertEqual(signals[1].confidence, 'HIGH')
    
    def test_trade_plan_generation(self):
        """Test trade plan generation for signals"""
        signal = InstitutionalSignal(
            strike=21840,
            option_type='PUT',
            volume=2750,
            open_interest=50,
            vol_oi_ratio=55.0,
            option_price=35.5,
            dollar_size=1_950_000,
            direction='SHORT',
            target_price=21840,
            confidence='EXTREME',
            timestamp=datetime.now(timezone.utc),
            expiration_date='2024-01-10'
        )
        
        trade_plan = self.analyzer.generate_trade_plan(signal, self.current_price)
        
        self.assertEqual(trade_plan['direction'], 'SHORT')
        self.assertEqual(trade_plan['entry_price'], 21870)
        self.assertEqual(trade_plan['take_profit'], 21840)
        self.assertEqual(trade_plan['stop_loss'], 21885)  # Half the distance
        self.assertEqual(trade_plan['size_multiplier'], 3.0)  # Extreme confidence
    
    def test_actionable_signal_filtering(self):
        """Test filtering signals by distance from current price"""
        signals = [
            InstitutionalSignal(
                strike=21850,  # Close to current price
                option_type='PUT',
                volume=1000,
                open_interest=50,
                vol_oi_ratio=20.0,
                option_price=30.0,
                dollar_size=600_000,
                direction='SHORT',
                target_price=21850,
                confidence='HIGH',
                timestamp=datetime.now(timezone.utc),
                expiration_date='2024-01-10'
            ),
            InstitutionalSignal(
                strike=22200,  # Far from current price
                option_type='CALL',
                volume=1500,
                open_interest=50,
                vol_oi_ratio=30.0,
                option_price=40.0,
                dollar_size=1_200_000,
                direction='LONG',
                target_price=22200,
                confidence='VERY_HIGH',
                timestamp=datetime.now(timezone.utc),
                expiration_date='2024-01-10'
            ),
        ]
        
        actionable = self.analyzer.filter_actionable_signals(
            signals, 
            self.current_price,
            max_distance_percent=1.0
        )
        
        self.assertEqual(len(actionable), 1)
        self.assertEqual(actionable[0].strike, 21850)
    
    def test_institutional_summary(self):
        """Test institutional activity summary"""
        signals = [
            InstitutionalSignal(
                strike=21840,
                option_type='PUT',
                volume=2750,
                open_interest=50,
                vol_oi_ratio=55.0,
                option_price=35.5,
                dollar_size=1_950_000,
                direction='SHORT',
                target_price=21840,
                confidence='EXTREME',
                timestamp=datetime.now(timezone.utc),
                expiration_date='2024-01-10'
            ),
            InstitutionalSignal(
                strike=21900,
                option_type='CALL',
                volume=1000,
                open_interest=50,
                vol_oi_ratio=20.0,
                option_price=30.0,
                dollar_size=600_000,
                direction='LONG',
                target_price=21900,
                confidence='HIGH',
                timestamp=datetime.now(timezone.utc),
                expiration_date='2024-01-10'
            ),
        ]
        
        summary = self.analyzer.summarize_institutional_activity(signals)
        
        self.assertEqual(summary['total_signals'], 2)
        self.assertEqual(summary['total_dollar_volume'], 2_550_000)
        self.assertEqual(summary['put_dollar_volume'], 1_950_000)
        self.assertEqual(summary['call_dollar_volume'], 600_000)
        self.assertEqual(summary['net_positioning'], 'BEARISH')  # 76% puts
        self.assertAlmostEqual(summary['put_percentage'], 76.47, places=1)
    
    def test_zero_open_interest_handling(self):
        """Test that strikes with zero OI are handled gracefully"""
        strike_data = {
            'strike': 21900,
            'optionType': 'CALL',
            'volume': 1000,
            'openInterest': 0,  # Zero OI
            'lastPrice': 40.0,
            'expirationDate': '2024-01-10'
        }
        
        signal = self.analyzer.analyze_strike(strike_data, self.current_price)
        self.assertIsNone(signal)

if __name__ == '__main__':
    unittest.main()