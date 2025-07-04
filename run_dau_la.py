import os
import sys
from pathlib import Path

src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.games.dau_la import DauLa
from src.utils.logging import setup_logger

def main():
    logger = setup_logger("DauLa")
    logger.info("Starting DauLa automation")
    
    try:
        # Initialize automation
        game = DauLa()
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