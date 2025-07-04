"""
Run Girlwar automation.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.games.cherry_tale.cherry_tale import CherryTale
from utils import log_error, log_info, log_success, log_warning

def main():
    # Set up logging
    log_success("Starting Cherry Tale automation")
    
    try:
        # Initialize automation
        game = CherryTale()
        # Start automation
        game.start()
        
    except KeyboardInterrupt:
        log_info("Automation stopped by user")
    except Exception as e:
        log_error(f"Error running automation: {e}", exc_info=True)
    finally:
        log_info("Automation ended")

if __name__ == "__main__":
    main() 