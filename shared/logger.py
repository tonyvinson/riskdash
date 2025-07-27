import logging
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any

class KSIStructuredLogger:
    """
    Structured logger for KSI validation platform
    Provides consistent logging format across all Lambda functions
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create structured formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._create_formatter())
        self.logger.addHandler(handler)
        
        self.logger.propagate = False
    
    def _create_formatter(self):
        """Create structured JSON formatter"""
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add extra fields if present
                if hasattr(record, 'execution_id'):
                    log_entry['execution_id'] = record.execution_id
                if hasattr(record, 'tenant_id'):
                    log_entry['tenant_id'] = record.tenant_id
                if hasattr(record, 'ksi_id'):
                    log_entry['ksi_id'] = record.ksi_id
                    
                return json.dumps(log_entry)
        
        return StructuredFormatter()
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context"""
        extra = {k: v for k, v in kwargs.items() if k in ['execution_id', 'tenant_id', 'ksi_id']}
        self.logger.log(level, message, extra=extra)

def get_logger(name: str, level: str = "INFO") -> KSIStructuredLogger:
    """Get a structured logger instance"""
    return KSIStructuredLogger(name, level)

# Convenience functions for Lambda usage
def lambda_logger(function_name: str) -> KSIStructuredLogger:
    """Get logger for Lambda function"""
    return get_logger(f"ksi.{function_name}")
