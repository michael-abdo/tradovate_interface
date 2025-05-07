#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import login_helper

class TestLoginHelper:
    
    @patch("src.login_helper.inject_login_script")
    @patch("src.login_helper.disable_alerts")
    def test_login_to_existing_chrome_success(self, mock_disable_alerts, mock_inject_login_script, 
                                            mock_browser, mock_tab):
        # Setup
        mock_tab.mock_evaluate_result("https://trader.tradovate.com")
        mock_browser.add_tab(mock_tab)
        
        with patch("src.auto_login.pychrome.Browser", return_value=mock_browser):
            # Execute
            success, tab, browser = login_helper.login_to_existing_chrome(
                username="testuser", 
                password="testpass"
            )
            
            # Assert
            assert success is True
            assert tab == mock_tab
            assert browser == mock_browser
            mock_inject_login_script.assert_called_once_with(mock_tab, "testuser", "testpass")
            mock_disable_alerts.assert_called_once_with(mock_tab)

    @patch("src.login_helper.inject_login_script")
    @patch("src.login_helper.disable_alerts")
    def test_login_to_existing_chrome_no_tabs(self, mock_disable_alerts, mock_inject_login_script, 
                                            mock_browser, mock_tab):
        # Setup - empty browser with no tabs
        mock_browser.new_tab.return_value = mock_tab
        
        with patch("src.auto_login.pychrome.Browser", return_value=mock_browser):
            with patch("time.sleep"):  # Mock sleep to avoid waiting
                # Execute
                success, tab, browser = login_helper.login_to_existing_chrome(
                    username="testuser", 
                    password="testpass"
                )
                
                # Assert
                assert success is True
                assert tab == mock_tab
                assert browser == mock_browser
                mock_browser.new_tab.assert_called_once()
                mock_inject_login_script.assert_called_once_with(mock_tab, "testuser", "testpass")
                mock_disable_alerts.assert_called_once_with(mock_tab)

    def test_login_to_existing_chrome_with_credentials_file(self, mock_browser, mock_tab, mock_credentials):
        # Setup
        mock_tab.mock_evaluate_result("https://trader.tradovate.com")
        mock_browser.add_tab(mock_tab)
        
        # Create a mock file for credentials
        mock_file = mock_open(read_data=json.dumps(mock_credentials))
        
        with patch("src.auto_login.pychrome.Browser", return_value=mock_browser), \
             patch("src.login_helper.inject_login_script") as mock_inject, \
             patch("src.login_helper.disable_alerts"), \
             patch("builtins.open", mock_file), \
             patch("os.path.dirname", return_value="/fake/path"), \
             patch("os.path.abspath", return_value="/fake/path"):
            
            # Execute
            success, tab, browser = login_helper.login_to_existing_chrome()
            
            # Assert
            assert success is True
            # Should have loaded first credential from the file
            mock_inject.assert_called_once()
            # Get the first arg (username) from the call
            username = mock_inject.call_args[0][1]
            assert username in mock_credentials.keys()  # One of our mock users

    def test_login_to_existing_chrome_connection_error(self, mock_browser):
        # Setup - simulate connection error
        with patch("src.auto_login.pychrome.Browser", side_effect=Exception("Connection error")):
            # Execute
            success, tab, browser = login_helper.login_to_existing_chrome(
                username="testuser", 
                password="testpass"
            )
            
            # Assert
            assert success is False
            assert tab is None
            assert browser is None

    def test_wait_for_element_success(self, mock_tab):
        # Setup - element is found immediately
        mock_tab.mock_evaluate_result(True)
        
        with patch("time.sleep"):
            # Execute
            result = login_helper.wait_for_element(mock_tab, "#test-element")
            
            # Assert
            assert result is True
            mock_tab.Runtime.evaluate.assert_called_once()

    def test_wait_for_element_eventually_found(self, mock_tab):
        # Setup - element is found after a few attempts
        mock_tab.Runtime.evaluate.side_effect = [
            {"result": {"value": False}},
            {"result": {"value": False}},
            {"result": {"value": True}}
        ]
        
        with patch("time.sleep"):
            # Execute
            result = login_helper.wait_for_element(mock_tab, "#test-element")
            
            # Assert
            assert result is True
            assert mock_tab.Runtime.evaluate.call_count == 3

    def test_wait_for_element_timeout(self, mock_tab):
        # Setup - element is never found
        mock_tab.mock_evaluate_result(False)
        
        with patch("time.sleep"):
            # Execute
            result = login_helper.wait_for_element(mock_tab, "#test-element", timeout=0.5)
            
            # Assert
            assert result is False
            assert mock_tab.Runtime.evaluate.call_count >= 1

    def test_execute_js_success(self, mock_tab):
        # Setup
        expected_result = {"type": "string", "value": "test result"}
        mock_tab.Runtime.evaluate.return_value = {"result": expected_result}
        
        # Execute
        result = login_helper.execute_js(mock_tab, "return 'test result';")
        
        # Assert
        assert result == expected_result
        mock_tab.Runtime.evaluate.assert_called_once_with(expression="return 'test result';")

    def test_execute_js_error(self, mock_tab):
        # Setup - simulate error in JavaScript execution
        mock_tab.Runtime.evaluate.side_effect = Exception("JS Error")
        
        # Execute
        result = login_helper.execute_js(mock_tab, "invalid code")
        
        # Assert
        assert result is None
        mock_tab.Runtime.evaluate.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "test_login_helper.py"])