"""
Run Girlwar automation.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.games.ark_recode import TestADBGameAutomation
from src.utils.logging import setup_logger

def main():
    # Set up logging
    logger = setup_logger("yeuquai")
    logger.info("Starting Yeuquaichaydidau automation")
    
    try:
        # Initialize automation
        game = TestADBGameAutomation()
        
        # Start automation
        game.start()
        
    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Error running automation: {e}", exc_info=True)
    finally:
        logger.info("Automation ended")

if __name__ == "__main__":
    main() 