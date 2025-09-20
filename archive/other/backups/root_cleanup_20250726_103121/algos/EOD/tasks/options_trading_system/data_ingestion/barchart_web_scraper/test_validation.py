import unittest
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from solution import (
    BarchartWebScraper, BarchartAPIComparator, OptionsContract, 
    OptionsChainData
)

class TestBarchartWebScraper(unittest.TestCase):
    """
    EXPERIMENTAL VALIDATION: Test barchart web scraping functionality
    and data comparison accuracy
    """
    
    def setUp(self):
        self.scraper = BarchartWebScraper(headless=True)
        self.comparator = BarchartAPIComparator()
        
    def test_driver_setup(self):
        """
        HYPOTHESIS: Chrome driver can be setup with appropriate options
        SUCCESS CRITERIA: Driver initializes without errors
        """
        try:
            driver = self.scraper.setup_driver()
            self.assertIsNotNone(driver)
            driver.quit()
        except Exception as e:
            self.skipTest(f"Chrome driver not available: {e}")
    
    def test_options_contract_parsing(self):
        """
        HYPOTHESIS: Options contract data can be parsed from table rows
        SUCCESS CRITERIA: Valid OptionsContract objects created from sample data
        """
        
        # Sample table row data (strike, call_bid, call_ask, call_last, call_vol, put_bid, put_ask, put_last, put_vol)
        sample_cells = ["19000.0", "148.0", "152.0", "150.0", "100", "48.0", "52.0", "50.0", "80"]
        headers = ["strike", "call_bid", "call_ask", "call_last", "call_vol", "put_bid", "put_ask", "put_last", "put_vol"]
        
        contract = self.scraper._parse_options_row(sample_cells, headers, 19100.0, "2025-06-20")
        
        # VALIDATION: Contract correctly parsed
        self.assertIsNotNone(contract)
        self.assertEqual(contract.strike, 19000.0)
        self.assertEqual(contract.call_bid, 148.0)
        self.assertEqual(contract.call_ask, 152.0)
        self.assertEqual(contract.call_last, 150.0)
        self.assertEqual(contract.call_volume, 100)
        self.assertEqual(contract.put_bid, 48.0)
        self.assertEqual(contract.put_ask, 52.0)
        self.assertEqual(contract.put_last, 50.0)
        self.assertEqual(contract.put_volume, 80)
        self.assertEqual(contract.underlying_price, 19100.0)
        self.assertEqual(contract.source, 'web_scrape')
        
    def test_invalid_data_handling(self):
        """
        HYPOTHESIS: Parser handles invalid or missing data gracefully
        SUCCESS CRITERIA: No errors thrown, None values for invalid fields
        """
        
        # Invalid data samples
        invalid_samples = [
            ["not_a_number", "N/A", "--", "", "abc"],  # Invalid numeric data
            ["15000", "", "N/A", "--", ""],             # Missing values
            []                                          # Empty row
        ]
        
        for sample in invalid_samples:
            try:
                contract = self.scraper._parse_options_row(sample, [], None, "2025-06-20")
                # Should either return None or valid contract with None fields
                if contract is not None:
                    self.assertIsInstance(contract, OptionsContract)
            except Exception as e:
                self.fail(f"Parser should handle invalid data gracefully, got error: {e}")
    
    def test_data_comparison_logic(self):
        """
        HYPOTHESIS: Data comparison accurately identifies differences between sources
        SUCCESS CRITERIA: Correct identification of discrepancies and similarities
        """
        
        # Create test data with known differences
        web_contracts = [
            OptionsContract(
                strike=19000.0,
                call_last=150.0, call_bid=148.0, call_ask=152.0, call_volume=100,
                put_last=50.0, put_bid=48.0, put_ask=52.0, put_volume=80,
                call_change=None, call_open_interest=None, call_implied_volatility=None,
                put_change=None, put_open_interest=None, put_implied_volatility=None,
                expiration_date="2025-06-20", underlying_price=19100.0,
                source='web_scrape', timestamp=datetime.now()
            )
        ]
        
        api_contracts = [
            OptionsContract(
                strike=19000.0,
                call_last=151.0, call_bid=149.0, call_ask=153.0, call_volume=105,  # Slight differences
                put_last=49.0, put_bid=47.0, put_ask=51.0, put_volume=85,
                call_change=None, call_open_interest=None, call_implied_volatility=None,
                put_change=None, put_open_interest=None, put_implied_volatility=None,
                expiration_date="2025-06-20", underlying_price=19105.0,  # Different underlying
                source='api', timestamp=datetime.now()
            )
        ]
        
        web_data = OptionsChainData(
            underlying_symbol="NQM25", expiration_date="2025-06-20",
            underlying_price=19100.0, contracts=web_contracts,
            source='web_scrape', timestamp=datetime.now(), total_contracts=1
        )
        
        api_data = OptionsChainData(
            underlying_symbol="NQM25", expiration_date="2025-06-20",
            underlying_price=19105.0, contracts=api_contracts,
            source='api', timestamp=datetime.now(), total_contracts=1
        )
        
        # Perform comparison
        comparison = self.comparator.compare_data_sources(web_data, api_data)
        
        # VALIDATION: Comparison detects differences
        self.assertEqual(comparison['differences']['contract_count_diff'], 0)  # Same count
        self.assertAlmostEqual(comparison['differences']['underlying_price_diff'], -5.0, places=1)  # Price difference
        self.assertEqual(len(comparison['differences']['price_discrepancies']), 1)  # One contract compared
        
        # Check that discrepancies were found
        discrepancies = comparison['differences']['price_discrepancies'][0]['discrepancies']
        self.assertIn('call_last', discrepancies)  # Should detect call_last difference
        self.assertIn('call_bid', discrepancies)   # Should detect call_bid difference
        
    def test_quality_metrics_calculation(self):
        """
        HYPOTHESIS: Data quality metrics accurately reflect data completeness
        SUCCESS CRITERIA: Quality scores reflect actual data completeness
        """
        
        # High completeness data
        complete_contract = OptionsContract(
            strike=19000.0,
            call_last=150.0, call_bid=148.0, call_ask=152.0, call_volume=100,
            put_last=50.0, put_bid=48.0, put_ask=52.0, put_volume=80,
            call_change=5.0, call_open_interest=500, call_implied_volatility=0.25,
            put_change=-2.0, put_open_interest=300, put_implied_volatility=0.23,
            expiration_date="2025-06-20", underlying_price=19100.0,
            source='complete', timestamp=datetime.now()
        )
        
        # Incomplete data
        incomplete_contract = OptionsContract(
            strike=19000.0,
            call_last=None, call_bid=None, call_ask=None, call_volume=None,
            put_last=50.0, put_bid=48.0, put_ask=None, put_volume=None,
            call_change=None, call_open_interest=None, call_implied_volatility=None,
            put_change=None, put_open_interest=None, put_implied_volatility=None,
            expiration_date="2025-06-20", underlying_price=19100.0,
            source='incomplete', timestamp=datetime.now()
        )
        
        complete_data = OptionsChainData(
            underlying_symbol="NQM25", expiration_date="2025-06-20",
            underlying_price=19100.0, contracts=[complete_contract],
            source='complete', timestamp=datetime.now(), total_contracts=1
        )
        
        incomplete_data = OptionsChainData(
            underlying_symbol="NQM25", expiration_date="2025-06-20",
            underlying_price=19100.0, contracts=[incomplete_contract],
            source='incomplete', timestamp=datetime.now(), total_contracts=1
        )
        
        comparison = self.comparator.compare_data_sources(complete_data, incomplete_data)
        
        # VALIDATION: Quality metrics reflect completeness differences
        complete_quality = comparison['data_quality']['web_completeness']
        incomplete_quality = comparison['data_quality']['api_completeness']
        
        self.assertGreater(complete_quality, incomplete_quality, 
                          "Complete data should have higher quality score")
        self.assertGreater(complete_quality, 0.8, "Complete data should score > 80%")
        self.assertLess(incomplete_quality, 0.6, "Incomplete data should score < 60%")

class TestBarchartIntegration(unittest.TestCase):
    """
    INTEGRATION TESTS: Test full workflow without actual web scraping
    """
    
    @patch('solution.webdriver.Chrome')
    def test_scraping_workflow_mock(self, mock_chrome):
        """
        HYPOTHESIS: Full scraping workflow executes without errors
        SUCCESS CRITERIA: Complete data processing pipeline works
        """
        
        # Mock driver and web elements
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock table element
        mock_table = MagicMock()
        mock_table.get_attribute.return_value = """
        <table>
            <tr><th>Strike</th><th>Call Bid</th><th>Call Ask</th><th>Put Bid</th><th>Put Ask</th></tr>
            <tr><td>19000</td><td>148</td><td>152</td><td>48</td><td>52</td></tr>
            <tr><td>19025</td><td>125</td><td>129</td><td>65</td><td>69</td></tr>
        </table>
        """
        
        mock_driver.find_element.return_value = mock_table
        mock_driver.title = "NQM25 Options"
        
        # Create scraper and test
        scraper = BarchartWebScraper(headless=True)
        
        try:
            # This would normally scrape but will use mocked data
            with patch.object(scraper, 'setup_driver', return_value=mock_driver):
                with patch.object(scraper, '_extract_underlying_info', return_value={'symbol': 'NQM25', 'price': 19100.0, 'expiration': '2025-06-20'}):
                    # Should complete without error
                    result = scraper.scrape_barchart_options("http://test.url")
                    
                    self.assertIsInstance(result, OptionsChainData)
                    self.assertEqual(result.underlying_symbol, "NQM25")
                    self.assertGreater(result.total_contracts, 0)
                    
        except Exception as e:
            self.fail(f"Scraping workflow should complete without error: {e}")

class TestDataFormats(unittest.TestCase):
    """
    Test data structure formats and serialization
    """
    
    def test_options_contract_serialization(self):
        """
        HYPOTHESIS: OptionsContract can be serialized to JSON
        SUCCESS CRITERIA: No serialization errors, valid JSON output
        """
        
        contract = OptionsContract(
            strike=19000.0,
            call_last=150.0, call_bid=148.0, call_ask=152.0, call_volume=100,
            put_last=50.0, put_bid=48.0, put_ask=52.0, put_volume=80,
            call_change=5.0, call_open_interest=500, call_implied_volatility=0.25,
            put_change=-2.0, put_open_interest=300, put_implied_volatility=0.23,
            expiration_date="2025-06-20", underlying_price=19100.0,
            source='test', timestamp=datetime.now()
        )
        
        try:
            # Test serialization
            from dataclasses import asdict
            contract_dict = asdict(contract)
            json_str = json.dumps(contract_dict, default=str)
            
            # Test deserialization
            loaded_dict = json.loads(json_str)
            
            # VALIDATION: Key fields preserved
            self.assertEqual(loaded_dict['strike'], 19000.0)
            self.assertEqual(loaded_dict['call_last'], 150.0)
            self.assertEqual(loaded_dict['source'], 'test')
            
        except Exception as e:
            self.fail(f"OptionsContract serialization failed: {e}")
    
    def test_comparison_result_format(self):
        """
        HYPOTHESIS: Comparison results have consistent format
        SUCCESS CRITERIA: All required fields present in comparison output
        """
        
        # Create minimal test data
        contract = OptionsContract(
            strike=19000.0, call_last=150.0, put_last=50.0,
            call_bid=None, call_ask=None, call_volume=None, call_open_interest=None,
            put_bid=None, put_ask=None, put_volume=None, put_open_interest=None,
            call_change=None, call_implied_volatility=None,
            put_change=None, put_implied_volatility=None,
            expiration_date="2025-06-20", underlying_price=19100.0,
            source='test', timestamp=datetime.now()
        )
        
        data = OptionsChainData(
            underlying_symbol="NQM25", expiration_date="2025-06-20",
            underlying_price=19100.0, contracts=[contract],
            source='test', timestamp=datetime.now(), total_contracts=1
        )
        
        comparator = BarchartAPIComparator()
        comparison = comparator.compare_data_sources(data, data)  # Compare with itself
        
        # VALIDATION: Required fields present
        required_fields = [
            'comparison_timestamp', 'web_data_summary', 'api_data_summary',
            'differences', 'data_quality'
        ]
        
        for field in required_fields:
            self.assertIn(field, comparison, f"Missing required field: {field}")
        
        # VALIDATION: Differences structure
        diff_fields = ['contract_count_diff', 'underlying_price_diff', 'missing_strikes_web', 'missing_strikes_api', 'price_discrepancies']
        for field in diff_fields:
            self.assertIn(field, comparison['differences'], f"Missing difference field: {field}")
        
        # VALIDATION: Quality structure  
        quality_fields = ['web_completeness', 'api_completeness', 'overall_similarity']
        for field in quality_fields:
            self.assertIn(field, comparison['data_quality'], f"Missing quality field: {field}")

def run_performance_test():
    """
    Performance validation for data processing
    """
    print("\n=== BARCHART SCRAPER PERFORMANCE TEST ===")
    
    # Test data processing speed
    comparator = BarchartAPIComparator()
    
    # Generate large dataset
    contracts = []
    for i in range(1000):  # 1000 contracts
        contract = OptionsContract(
            strike=15000.0 + i*25,
            call_last=100.0 + i, call_bid=99.0 + i, call_ask=101.0 + i, call_volume=100,
            put_last=50.0 + i, put_bid=49.0 + i, put_ask=51.0 + i, put_volume=80,
            call_change=None, call_open_interest=None, call_implied_volatility=None,
            put_change=None, put_open_interest=None, put_implied_volatility=None,
            expiration_date="2025-06-20", underlying_price=19100.0,
            source='test', timestamp=datetime.now()
        )
        contracts.append(contract)
    
    large_dataset = OptionsChainData(
        underlying_symbol="NQM25", expiration_date="2025-06-20",
        underlying_price=19100.0, contracts=contracts,
        source='test', timestamp=datetime.now(), total_contracts=len(contracts)
    )
    
    # Test comparison performance
    start_time = time.time()
    comparison = comparator.compare_data_sources(large_dataset, large_dataset)
    processing_time = time.time() - start_time
    
    print(f"Processed {len(contracts)} contracts in {processing_time:.3f} seconds")
    print(f"Processing rate: {len(contracts)/processing_time:.0f} contracts/second")
    
    # VALIDATION: Performance requirements
    assert processing_time < 10.0, f"Processing too slow: {processing_time:.3f}s"
    assert comparison['data_quality']['overall_similarity'] > 0.9, "Self-comparison should be highly similar"
    
    print("✓ Performance test passed")

if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(verbosity=2, exit=False)
    
    # Run performance test
    try:
        run_performance_test()
    except Exception as e:
        print(f"Performance test failed: {e}")
    
    print("\n=== TEST SUMMARY ===")
    print("Unit tests completed")
    print("Performance validation completed")
    print("Ready for live data scraping validation")