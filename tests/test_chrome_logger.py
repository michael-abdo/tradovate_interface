#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import time
import datetime
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import chrome_logger

class TestChromeLogger:
    
    def test_init(self, mock_tab, tmp_path):
        # Setup
        log_file = str(tmp_path / "test.log")
        
        # Execute
        logger = chrome_logger.ChromeLogger(mock_tab, log_file)
        
        # Assert
        assert logger.tab == mock_tab
        assert logger.log_file == log_file
        assert logger.callbacks == []
        assert logger.is_running is False
        assert logger.log_thread is None
        assert os.path.exists(os.path.dirname(log_file))

    def test_start_stop(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab)
        
        # Execute start - with real thread but mock the start method to avoid actually starting the thread
        with patch.object(threading.Thread, 'start'):
            result = logger.start()
            
            # Assert start
            assert result is True
            assert logger.is_running is True
            assert isinstance(logger.log_thread, threading.Thread)
            mock_tab.Log.enable.assert_called_once()
            mock_tab.Runtime.enable.assert_called_once()
            mock_tab.Console.enable.assert_called_once()
            
            # Execute stop - mock join to avoid waiting
            with patch.object(threading.Thread, 'join'):
                logger.stop()
                
                # Assert stop
                assert logger.is_running is False

    @patch("builtins.open", new_callable=mock_open)
    def test_write_to_file(self, mock_file, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file="test.log")
        entry = {
            "level": "INFO",
            "text": "Test message"
        }
        
        # Execute
        logger._write_to_file(entry)
        
        # Assert
        mock_file.assert_called_once_with("test.log", "a", encoding="utf-8")
        mock_file().write.assert_called_once()
        # Check that the log entry contains the level and text
        write_arg = mock_file().write.call_args[0][0]
        assert "INFO" in write_arg
        assert "Test message" in write_arg

    def test_callbacks(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab)
        callback1 = MagicMock()
        callback2 = MagicMock()
        entry = {"level": "INFO", "text": "Test message"}
        
        # Execute - add callbacks
        id1 = logger.add_callback(callback1)
        id2 = logger.add_callback(callback2)
        
        # Assert - callbacks added
        assert id1 == 0
        assert id2 == 1
        assert len(logger.callbacks) == 2
        
        # Execute - process callbacks
        logger._process_callbacks(entry)
        
        # Assert - callbacks called
        callback1.assert_called_once_with(entry)
        callback2.assert_called_once_with(entry)
        
        # Execute - remove callback
        result = logger.remove_callback(id1)
        
        # Assert - callback removed
        assert result is True
        assert len(logger.callbacks) == 1
        assert logger.callbacks[0] == callback2

    def test_on_log_entry(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file=None)
        callback = MagicMock()
        logger.add_callback(callback)
        
        with patch.object(logger, "_write_to_file") as mock_write:
            # Execute
            logger._on_log_entry(entry={
                "level": "INFO",
                "text": "Test log message",
                "url": "http://example.com"
            })
            
            # Assert
            mock_write.assert_called_once()
            callback.assert_called_once()
            # Check the entry passed to the callback
            entry = callback.call_args[0][0]
            assert entry["source"] == "browser"
            assert entry["level"] == "INFO"
            assert entry["text"] == "Test log message"

    def test_on_console_api(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file=None)
        callback = MagicMock()
        logger.add_callback(callback)
        
        with patch.object(logger, "_write_to_file") as mock_write:
            # Execute
            logger._on_console_api(
                type="log",
                args=[{"value": "Console"}, {"value": "message"}],
                stackTrace={"callFrames": [{"url": "http://example.com"}]}
            )
            
            # Assert
            mock_write.assert_called_once()
            callback.assert_called_once()
            # Check the entry passed to the callback
            entry = callback.call_args[0][0]
            assert entry["source"] == "console"
            assert entry["level"] == "LOG"
            assert entry["text"] == "Console message"

    def test_on_exception(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file=None)
        callback = MagicMock()
        logger.add_callback(callback)
        
        with patch.object(logger, "_write_to_file") as mock_write:
            # Execute
            logger._on_exception(
                exceptionDetails={
                    "exception": {"description": "Test exception"},
                    "url": "http://example.com"
                }
            )
            
            # Assert
            mock_write.assert_called_once()
            callback.assert_called_once()
            # Check the entry passed to the callback
            entry = callback.call_args[0][0]
            assert entry["source"] == "exception"
            assert entry["level"] == "ERROR"
            assert "Test exception" in entry["text"]

    def test_on_console_message(self, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file=None)
        callback = MagicMock()
        logger.add_callback(callback)
        
        with patch.object(logger, "_write_to_file") as mock_write:
            # Execute
            logger._on_console_message(
                message={
                    "level": "warning",
                    "text": "Console warning message",
                    "url": "http://example.com"
                }
            )
            
            # Assert
            mock_write.assert_called_once()
            callback.assert_called_once()
            # Check the entry passed to the callback
            entry = callback.call_args[0][0]
            assert entry["source"] == "console"
            assert entry["level"] == "WARNING"  # Uppercase
            assert entry["text"] == "Console warning message"

    @patch("time.sleep", side_effect=InterruptedError)  # Force exit from the loop
    def test_process_logs(self, mock_sleep, mock_tab):
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab)
        logger.is_running = True
        
        # Execute & Assert (should not raise exception)
        logger._process_logs()
        mock_sleep.assert_called_once()

    def test_create_logger(self, mock_tab):
        # Setup
        callback = MagicMock()
        log_file = "test.log"
        
        with patch("src.chrome_logger.ChromeLogger") as MockLoggerClass:
            mock_logger = MagicMock()
            mock_logger.start.return_value = True
            MockLoggerClass.return_value = mock_logger
            
            # Execute
            logger = chrome_logger.create_logger(mock_tab, log_file, callback)
            
            # Assert
            assert logger == mock_logger
            MockLoggerClass.assert_called_once_with(mock_tab, log_file)
            mock_logger.add_callback.assert_called_once_with(callback)
            mock_logger.start.assert_called_once()

    def test_create_logger_failure(self, mock_tab):
        # Setup
        with patch("src.chrome_logger.ChromeLogger") as MockLoggerClass:
            mock_logger = MagicMock()
            mock_logger.start.return_value = False  # Logger fails to start
            MockLoggerClass.return_value = mock_logger
            
            # Execute
            logger = chrome_logger.create_logger(mock_tab)
            
            # Assert
            assert logger is None
            MockLoggerClass.assert_called_once()
            mock_logger.start.assert_called_once()

    def test_event_handling_integration(self, mock_tab):
        # This test checks the complete flow of events through the logger
        
        # Setup
        logger = chrome_logger.ChromeLogger(mock_tab, log_file=None)
        callback = MagicMock()
        logger.add_callback(callback)
        
        # Start logger and set up event handlers
        with patch("threading.Thread"):
            logger.start()
        
        # Now trigger various events
        
        # 1. Log entry
        logger._on_log_entry(entry={
            "level": "INFO",
            "text": "Log entry message"
        })
        
        # 2. Console API call
        logger._on_console_api(
            type="error",
            args=[{"value": "Console error"}]
        )
        
        # 3. Exception
        logger._on_exception(
            exceptionDetails={
                "exception": {"description": "Test exception"}
            }
        )
        
        # Assert
        assert callback.call_count == 3
        
        # Check individual calls
        calls = callback.call_args_list
        assert calls[0][0][0]["text"] == "Log entry message"
        assert calls[0][0][0]["level"] == "INFO"
        
        assert calls[1][0][0]["text"] == "Console error"
        assert calls[1][0][0]["level"] == "ERROR"
        
        assert "Test exception" in calls[2][0][0]["text"]
        assert calls[2][0][0]["level"] == "ERROR"


if __name__ == "__main__":
    pytest.main(["-v", "test_chrome_logger.py"])