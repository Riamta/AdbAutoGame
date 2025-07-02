import time
import asyncio
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from src.core.adb_auto import ADBGameAutomation
from src.utils.logging import setup_logger, log_error, log_state, log_warning, log_success, log_info
from enum import Enum, auto

class GameState(Enum):
    UNKNOWN = auto()
    MAIN_MENU = auto()
    BATTLE = auto()


class ArkRecode(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/ark-recode"
        self.templates_dir = "assets/ark-recode/templates"
        # Setup game specific paths
        self.button_paths = {
            'skip_dialog': f"{self.templates_dir}/skip_dialog.png",
            'skip_dialog_confirm': f"{self.templates_dir}/skip_dialog_confirm.png",
        }

        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
        # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)

    
    def process_game_actions(self):
        while self.running:
            current_screen = self.capture_screen()
            self.check_skip_dialog(current_screen)
    
    def check_skip_dialog(self, current_screen):
        if self.find_and_tap(current_screen, self.button_paths['skip_dialog']):
            self.wait_and_tap(self.button_paths['skip_dialog_confirm'])