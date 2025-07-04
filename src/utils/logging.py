"""
Logging utility module for the AutoZ framework.
Provides consistent logging functionality across the framework.
"""

import logging
import os
from datetime import datetime
from colorama import Fore, Style

# Configure root logger once
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add colored console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    # Get existing logger if it exists
    logger = logging.getLogger(name)
    # Return existing logger if it's already configured
    if logger.handlers:
        return logger
        
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    log_file = os.path.join(
        log_dir, 
        f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    
    return logger

def _get_colored_text(level: str, message: str, color: str) -> str:
    """Internal helper to format colored text."""
    return f"{color}[{level}] {message}{Style.RESET_ALL}"

def log_error(message: str, exc_info: bool = False):
    """Log an error message in red."""
    root_logger.error(_get_colored_text("ERROR", message, Fore.RED), exc_info=exc_info)

def log_warning(message: str):
    """Log a warning message in yellow."""
    root_logger.warning(_get_colored_text("WARNING", message, Fore.YELLOW))

def log_success(message: str):
    """Log a success message in green."""
    root_logger.info(_get_colored_text("SUCCESS", message, Fore.GREEN))

def log_info(message: str):
    """Log an info message in white."""
    root_logger.info(_get_colored_text("INFO", message, Fore.WHITE))

def log_state(logger: logging.Logger, state: dict) -> None:
    """
    Log the current state of the automation.
    
    Args:
        logger: Logger instance
        state: Dictionary containing state information
    """
    logger.debug("Current state:")
    for key, value in state.items():
        logger.debug(f"  {key}: {value}") 