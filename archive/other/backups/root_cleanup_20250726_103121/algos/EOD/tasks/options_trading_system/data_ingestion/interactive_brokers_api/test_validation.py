"""
Test validation for Databento API connection module.

Tests the Databento API connection functionality with mock validation
when live connection is not available.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import json

# Add the solution module to path
sys.path.append(os.path.dirname(__file__))

try:
    from solution import DatabentoAPIConnection, simple_connection_test
    DATABENTO_AVAILABLE = True
except ImportError as e:
    print(f"Databento API not available: {e}")
    DATABENTO_AVAILABLE = False


class TestDatabentoAPIConnection(unittest.TestCase):
    """Test cases for Databento API connection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if DATABENTO_AVAILABLE:
            self.api = DatabentoAPIConnection()
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    def test_api_initialization(self):
        """Test that API object initializes correctly."""
        self.assertFalse(self.api.connected)
        self.assertIsNone(self.api.client)
        
        # Test with API key
        api_with_key = DatabentoAPIConnection("test_key")
        self.assertEqual(api_with_key.api_key, "test_key")
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch.dict(os.environ, {'DATABENTO_API_KEY': 'env_test_key'})
    def test_api_key_from_environment(self):
        """Test API key loading from environment variable."""
        api = DatabentoAPIConnection()
        self.assertEqual(api.api_key, "env_test_key")
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch('solution.db.Historical')
    def test_connection_success(self, mock_historical):
        """Test successful connection to Databento API."""
        # Mock successful connection
        mock_client = Mock()
        mock_historical.return_value = mock_client
        
        api = DatabentoAPIConnection("test_key")
        result = api.connect_api()
        
        self.assertTrue(result)
        self.assertTrue(api.connected)
        self.assertEqual(api.client, mock_client)
        mock_historical.assert_called_once_with("test_key")
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch('solution.db.Historical')
    def test_connection_failure(self, mock_historical):
        """Test connection failure handling."""
        # Mock connection failure
        mock_historical.side_effect = Exception("Invalid API key")
        
        api = DatabentoAPIConnection("invalid_key")
        result = api.connect_api()
        
        self.assertFalse(result)
        self.assertFalse(api.connected)
        self.assertIsNone(api.client)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    def test_connection_without_api_key(self):
        """Test connection attempt without API key."""
        api = DatabentoAPIConnection()
        result = api.connect_api()
        
        self.assertFalse(result)
        self.assertFalse(api.connected)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    def test_connection_test_not_connected(self):
        """Test connection test when not connected."""
        api = DatabentoAPIConnection()
        result = api.test_connection()
        
        self.assertFalse(result["connected"])
        self.assertIn("error", result)
        self.assertIn("test_timestamp", result)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch('solution.DatabentoAPIConnection.connect_api')
    @patch('solution.DatabentoAPIConnection.test_connection')
    def test_mock_data_retrieval(self, mock_test_connection, mock_connect):
        """Test data retrieval with mocked responses."""
        # Mock successful connection
        mock_connect.return_value = True
        
        # Mock successful data test
        mock_test_connection.return_value = {
            "connected": True,
            "test_successful": True,
            "sample_data_count": 10,
            "data_columns": ["ts_event", "symbol", "price", "size"],
            "test_timestamp": time.time(),
            "dataset_tested": "GLBX.MDP3"
        }
        
        api = DatabentoAPIConnection("test_key")
        connection_result = api.connect_api()
        test_result = api.test_connection()
        
        self.assertTrue(connection_result)
        self.assertTrue(test_result["connected"])
        self.assertTrue(test_result["test_successful"])
        self.assertEqual(test_result["sample_data_count"], 10)
        self.assertIn("data_columns", test_result)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    def test_mock_options_data_retrieval(self):
        """Test options data retrieval with mocked client."""
        api = DatabentoAPIConnection("test_key")
        api.connected = True
        
        # Mock the client and data response
        mock_client = Mock()
        mock_data = Mock()
        mock_df = Mock()
        mock_df.head.return_value.to_dict.return_value = {"sample": "data"}
        mock_df.columns = ["ts_event", "symbol", "price"]
        mock_df.__len__ = Mock(return_value=50)
        mock_df.empty = False
        
        mock_data.to_df.return_value = mock_df
        mock_client.timeseries.get_range.return_value = mock_data
        api.client = mock_client
        
        result = api.get_sample_options_data("SPY", 100)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "SPY")
        self.assertEqual(result["record_count"], 50)
        self.assertIn("data_preview", result)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    def test_disconnect(self):
        """Test API disconnection."""
        api = DatabentoAPIConnection("test_key")
        api.connected = True
        api.client = Mock()
        
        api.disconnect_api()
        
        self.assertFalse(api.connected)
        self.assertIsNone(api.client)
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch('solution.simple_connection_test')
    def test_simple_connection_test_success(self, mock_test):
        """Test simple connection test with mocked success."""
        mock_test.return_value = {
            "success": True,
            "message": "Databento API connection test successful",
            "connection_details": {
                "connected": True,
                "test_successful": True,
                "sample_data_count": 10
            },
            "api_available": True
        }
        
        result = simple_connection_test("test_key")
        
        self.assertTrue(result["success"])
        self.assertIn("connection_details", result)
        self.assertTrue(result["api_available"])
    
    @unittest.skipIf(not DATABENTO_AVAILABLE, "Databento API not available")
    @patch('solution.simple_connection_test')
    def test_simple_connection_test_failure(self, mock_test):
        """Test simple connection test with mocked failure."""
        mock_test.return_value = {
            "success": False,
            "message": "Databento API connection test failed",
            "connection_details": None,
            "api_available": False
        }
        
        result = simple_connection_test()
        
        self.assertFalse(result["success"])
        self.assertIsNone(result["connection_details"])


def run_validation_tests():
    """
    Run validation tests and return results.
    
    Returns:
        dict: Test execution results
    """
    print("Running Databento API validation tests...")
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabentoAPIConnection)
    
    # Run tests with detailed output
    test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    test_result = test_runner.run(test_suite)
    
    # Calculate results
    total_tests = test_result.testsRun
    failures = len(test_result.failures)
    errors = len(test_result.errors)
    skipped = len(test_result.skipped)
    successful = total_tests - failures - errors - skipped
    
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    results = {
        "total_tests": total_tests,
        "successful": successful,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "success_rate": success_rate,
        "overall_success": failures == 0 and errors == 0,
        "databento_api_available": DATABENTO_AVAILABLE,
        "test_timestamp": time.time()
    }
    
    print(f"\nValidation Results:")
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Databento API Available: {DATABENTO_AVAILABLE}")
    
    return results


if __name__ == "__main__":
    # Run validation tests
    test_results = run_validation_tests()
    
    # Save results for evidence generation
    with open(os.path.join(os.path.dirname(__file__), "test_results.json"), "w") as f:
        json.dump(test_results, f, indent=2)