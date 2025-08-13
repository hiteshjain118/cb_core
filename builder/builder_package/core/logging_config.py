#!/usr/bin/env python3
"""
Centralized logging configuration for QBO application
"""

import logging
import os
import sys

# Global flag to ensure logging is only configured once
_logging_configured = False

class ClickableFileFormatter(logging.Formatter):
    """Custom formatter that creates clickable filename:line references for IDEs"""
    
    def format(self, record):
        # Get the original format
        formatted = super().format(record)
        
        # Add filename:line in a format that IDEs recognize as clickable
        if hasattr(record, 'filename') and hasattr(record, 'lineno'):
            # Format: filename:line - this is the standard format most IDEs recognize
            file_location = f"{record.filename}:{record.lineno}"
            
            # Insert the file location after the level name
            parts = formatted.split(' - ')
            if len(parts) >= 3:
                # Insert file location after level name
                parts.insert(2, file_location)
                formatted = ' - '.join(parts)
        
        return formatted

def setup_logging():
    """Setup logging configuration for the entire application"""
    global _logging_configured
    
    # Only configure logging once
    if not _logging_configured and not logging.getLogger().handlers:
        # Create a custom formatter for clickable file references
        formatter = ClickableFileFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler with custom formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        
        _logging_configured = True
    
    # Set the root logger level
    logging.getLogger().setLevel(logging.INFO)
    
    # Prevent duplicate log messages
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Set specific logger levels for verbose modules
    logging.getLogger('builder_package.model_providers.gpt_provider').setLevel(logging.INFO) 