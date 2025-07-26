#!/usr/bin/env python3
"""
Structured Logger - JSON-based logging with rotation and context
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager
import threading


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': threading.current_thread().name,
            'process': os.getpid()
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class ContextLogger:
    """Logger with context support for structured logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._context = {}
        self._local = threading.local()
    
    def add_context(self, **kwargs):
        """Add permanent context to all logs"""
        self._context.update(kwargs)
    
    def clear_context(self):
        """Clear permanent context"""
        self._context.clear()
    
    @contextmanager
    def context(self, **kwargs):
        """Temporary context for logs within the context manager"""
        if not hasattr(self._local, 'context_stack'):
            self._local.context_stack = []
        
        self._local.context_stack.append(kwargs)
        try:
            yield
        finally:
            self._local.context_stack.pop()
    
    def _get_current_context(self) -> dict:
        """Get combined context from permanent and temporary contexts"""
        combined = self._context.copy()
        
        if hasattr(self._local, 'context_stack'):
            for ctx in self._local.context_stack:
                combined.update(ctx)
        
        return combined
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context"""
        extra_fields = self._get_current_context()
        extra_fields.update(kwargs)
        
        # Create a LogRecord with extra fields
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)


class LoggerFactory:
    """Factory for creating configured loggers"""
    
    def __init__(self, 
                 base_dir: str = "logs",
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 log_level: str = "INFO"):
        self.base_dir = Path(base_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.log_level = getattr(logging, log_level.upper())
        self._loggers = {}
        
        # Ensure log directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, 
                   name: str,
                   log_file: Optional[str] = None,
                   console: bool = True,
                   structured: bool = True) -> Union[ContextLogger, logging.Logger]:
        """Get or create a configured logger"""
        
        if name in self._loggers:
            return self._loggers[name]
        
        # Create base logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        logger.propagate = False
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add file handler with rotation
        if log_file:
            file_path = self.base_dir / log_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            
            if structured:
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
            
            logger.addHandler(file_handler)
        
        # Add console handler
        if console:
            console_handler = logging.StreamHandler()
            
            if structured:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                )
            
            logger.addHandler(console_handler)
        
        # Wrap in ContextLogger if structured
        if structured:
            context_logger = ContextLogger(logger)
            self._loggers[name] = context_logger
            return context_logger
        else:
            self._loggers[name] = logger
            return logger
    
    def get_startup_logger(self) -> ContextLogger:
        """Get logger specifically for startup operations"""
        logger = self.get_logger(
            "chrome_restart.startup",
            log_file=f"startup/startup_{datetime.now().strftime('%Y%m%d')}.log",
            structured=True
        )
        
        # Add standard context
        logger.add_context(
            component="startup_manager",
            version="1.0.0"
        )
        
        return logger
    
    def get_process_logger(self, process_name: str) -> ContextLogger:
        """Get logger for a specific process"""
        logger = self.get_logger(
            f"chrome_restart.process.{process_name}",
            log_file=f"processes/{process_name}_{datetime.now().strftime('%Y%m%d')}.log",
            structured=True
        )
        
        logger.add_context(
            component="process_monitor",
            process=process_name
        )
        
        return logger


# Global logger factory instance
_logger_factory = None


def get_logger_factory() -> LoggerFactory:
    """Get global logger factory instance"""
    global _logger_factory
    if not _logger_factory:
        # Get log level from environment or default
        log_level = os.environ.get('LOGLEVEL', 'INFO')
        _logger_factory = LoggerFactory(log_level=log_level)
    return _logger_factory


def get_logger(name: str, **kwargs) -> ContextLogger:
    """Convenience function to get a logger"""
    factory = get_logger_factory()
    return factory.get_logger(name, **kwargs)


class LogAnalyzer:
    """Analyze structured log files"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.entries = []
        self._load_logs()
    
    def _load_logs(self):
        """Load and parse log entries"""
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    self.entries.append(entry)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    pass
    
    def filter_by_level(self, level: str) -> list:
        """Filter logs by level"""
        return [e for e in self.entries if e.get('level') == level.upper()]
    
    def filter_by_time_range(self, start: datetime, end: datetime) -> list:
        """Filter logs by time range"""
        filtered = []
        for entry in self.entries:
            try:
                timestamp = datetime.fromisoformat(entry['timestamp'].rstrip('Z'))
                if start <= timestamp <= end:
                    filtered.append(entry)
            except (KeyError, ValueError):
                pass
        return filtered
    
    def get_errors(self) -> list:
        """Get all error and critical logs"""
        return [e for e in self.entries if e.get('level') in ['ERROR', 'CRITICAL']]
    
    def get_summary(self) -> dict:
        """Get summary statistics"""
        summary = {
            'total_entries': len(self.entries),
            'levels': {},
            'modules': {},
            'functions': {}
        }
        
        for entry in self.entries:
            # Count by level
            level = entry.get('level', 'UNKNOWN')
            summary['levels'][level] = summary['levels'].get(level, 0) + 1
            
            # Count by module
            module = entry.get('module', 'unknown')
            summary['modules'][module] = summary['modules'].get(module, 0) + 1
            
            # Count by function
            function = entry.get('function', 'unknown')
            summary['functions'][function] = summary['functions'].get(function, 0) + 1
        
        return summary


def main():
    """CLI for testing the logger"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Structured Logger Test")
    parser.add_argument('--analyze', help="Analyze a log file")
    parser.add_argument('--test', action='store_true', help="Run logger test")
    
    args = parser.parse_args()
    
    if args.analyze:
        analyzer = LogAnalyzer(args.analyze)
        summary = analyzer.get_summary()
        
        print("📊 Log Analysis Summary\n")
        print(f"Total entries: {summary['total_entries']}")
        
        print("\nLog levels:")
        for level, count in summary['levels'].items():
            print(f"  {level}: {count}")
        
        print("\nTop modules:")
        for module, count in sorted(summary['modules'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {module}: {count}")
        
        errors = analyzer.get_errors()
        if errors:
            print(f"\nFound {len(errors)} errors:")
            for error in errors[:5]:
                print(f"  [{error['timestamp']}] {error['message']}")
    
    elif args.test:
        # Test the logger
        logger = get_logger("test", log_file="test.log")
        
        logger.info("Starting logger test")
        
        # Test context
        logger.add_context(session_id="test-123", user="test_user")
        logger.info("This log has permanent context")
        
        # Test temporary context
        with logger.context(operation="database_query", query_id="q-456"):
            logger.info("Executing database query")
            logger.warning("Query took longer than expected", duration_ms=1500)
        
        # Test error logging
        try:
            1 / 0
        except Exception as e:
            logger.exception("Division by zero error", 
                           attempted_operation="divide",
                           numerator=1,
                           denominator=0)
        
        logger.info("Logger test completed")
        
        print("✅ Logger test completed. Check logs/test.log")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()