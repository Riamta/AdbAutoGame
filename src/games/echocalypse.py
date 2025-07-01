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


class Echocalypse(ADBGameAutomation):
    def __init__(self, config_path: Optional[str] = None, window_title: str = "echocalypse"):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'games' / 'echocalypse.yaml'
            
        # Initialize ADB automation with config
        ADBGameAutomation.__init__(self, config_file=str(config_path))
        
        # Load game specific config
        self.config = self.load_config(config_path)
        self.main_path = self.config['game']['assets_dir']
        self.templates_dir = self.config['game']['templates_dir']
        
        # Setup game specific paths
        self.button_paths = {
            'skip_dialog': f"{self.templates_dir}/skip_dialog.png",
            'confirm_skip': f"{self.templates_dir}/confirm_skip.png",
            'skip_battle': f"{self.templates_dir}/skip_battle.png",
            'current_battle': f"{self.templates_dir}/current_battle.png",
            'confirm_battle': f"{self.templates_dir}/confirm_battle.png",
            'check_end_battle': f"{self.templates_dir}/check_end_battle.png",
            'new_char_appear': f"{self.templates_dir}/new_char_appear.png",
            'clearneance_rewards': f"{self.templates_dir}/clearneance_rewards.png",
            'switch_map': f"{self.templates_dir}/switch_map.png",
            'before_switch_map': f"{self.templates_dir}/before_switch_map.png",
        }
        self.abyss = {
            'abyss_battle': f"{self.templates_dir}/abyss_battle.png",
            'abyss_slect_card': f"{self.templates_dir}/abyss_slect_card.png",
            'abyss_z': f"{self.templates_dir}/abyss_z.png",
        }
        
        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
        # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def process_game_actions(self):
        while self.running:
            current_screen = self.capture_screen()
            self.check_skip_dialog(current_screen)
            self.handle_in_map(current_screen)

    def handle_in_map(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['confirm_battle'], threshold=0.8)
        self.find_and_tap(current_screen, self.button_paths['new_char_appear'], threshold=0.8)
        self.find_and_tap(current_screen, self.button_paths['clearneance_rewards'], threshold=0.8)
        self.find_and_tap(current_screen, self.button_paths['before_switch_map'], threshold=0.8)
        self.find_and_tap_position_with_offset(self.button_paths['current_battle'], offset=(0, 100), threshold=0.8, screen=current_screen)
        self.find_and_tap_position_with_offset(self.button_paths['switch_map'], offset=(0, -100), threshold=0.8, screen=current_screen)
        self.check_end_battle(current_screen)
    
    def handle_abyss(self, current_screen):
        if not self.find_and_tap(current_screen, self.abyss['abyss_battle'], threshold=0.8):
            self.find_and_tap(current_screen, self.abyss['abyss_slect_card'], threshold=0.8)
            self.find_and_tap(current_screen, self.abyss['abyss_z'], threshold=0.8)
        self.check_end_battle(current_screen)

    def check_skip_dialog(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['skip_dialog'], threshold=0.8)
        self.find_and_tap(current_screen, self.button_paths['confirm_skip'], threshold=0.9)

    def check_end_battle(self, current_screen):
        if self.find_template(current_screen, self.button_paths['check_end_battle'], threshold=0.8):
            self.tap(500, 500)