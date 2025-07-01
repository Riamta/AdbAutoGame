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


class TestADBGameAutomation(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/girlwar"
        self.templates_dir = "assets/girlwar/templates"
        # Setup game specific paths
        self.button_paths = {
            'skip_dialog': f"{self.templates_dir}/skip_dialog.png",
            'skip_battle': f"{self.templates_dir}/skip_battle.png",
            'start_battle': f"{self.templates_dir}/start_battle.png",
            'tap_to_continue': f"{self.templates_dir}/tap_to_continue.png",
            'auto_guide': f"{self.templates_dir}/auto_guide.png",
            'challenge': f"{self.templates_dir}/challenge.png",
            'check_start_battle': f"{self.templates_dir}/check_start_battle.png",
            'elite_join_battle': f"{self.templates_dir}/elite_join_battle.png",
            'restraining_enenemy_hero': f"{self.templates_dir}/restraining_enenemy_hero.png",
            'victory': f"{self.templates_dir}/victory.png",
            'dungeon_floor': f"{self.templates_dir}/dungeon_floor.png",
            'continue_battling': f"{self.templates_dir}/continue_battling.png",
            'before_battle': f"{self.templates_dir}/before_battle.png",
            'congrats': f"{self.templates_dir}/congrats.png",
            'levelup': f"{self.templates_dir}/levelup.png",
        }
        self.global_rich_path = {
            'go': f"{self.templates_dir}/go.png",
        }
        self.dock_path = {
            'boar': f"{self.templates_dir}/boar.png",
        }
        self.atlantis_path = {
            'atlantis_go': f"{self.templates_dir}/atlantis_go.png",
        }
        self.end_battle = {
            'win_1': f"{self.templates_dir}/win_1.png",
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
            # self.handle_global_rich(current_screen)
            # self.handle_dock(current_screen)
            # self.elite_stage(current_screen)
            self.handle_dungeon_stage(current_screen)
            # self.handle_battle(current_screen)
            # self.handle_main_story(current_screen)

    def check_skip_dialog(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['skip_dialog'],  log="skip_dialog")
        self.find_and_tap(current_screen, self.button_paths['skip_battle'],  log="skip_battle")
        
    def check_end_battle(self, current_screen):
        self.find_and_tap_position(current_screen, self.end_battle['win_1'], 1920/2, 1080/5, threshold=0.8)

    def handle_atlantis(self, current_screen):
        self.find_and_tap(current_screen, self.atlantis_path['atlantis_go'], log="atlantis_go", threshold=0.5)

    def handle_dock(self, current_screen):
        self.tap(1600/2, 900/5)
        self.find_and_tap(current_screen, self.dock_path['boar'], log="boar", threshold=0.5)

    def handle_global_rich(self, current_screen):
        self.find_and_tap(current_screen, self.global_rich_path['go'], log="go",threshold=0.4)

    def handle_battle(self, current_screen):
        try:
            self.check_end_battle(current_screen)
            self.find_and_tap_position(current_screen, self.button_paths['before_battle'], 1920/2, 1080/2, log="before_battle", threshold=0.8)
            # Submit all find_and_tap operations to run in parallel
            self.find_and_tap(current_screen, self.button_paths['congrats'],  log="congrats", threshold=0.8)
            self.find_and_tap(current_screen, self.button_paths['start_battle'],  log="start_battle", threshold=0.7)
            self.find_and_tap(current_screen, self.button_paths['auto_guide'],  log="auto_guide", threshold=0.8)
            if self.find_template(self.capture_screen(), self.button_paths['check_start_battle']):
                self.tap(1600/2, 900/2)

        except Exception as e:
            log_error(f"Error in game actions: {e}", exc_info=True)

    def handle_main_story(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['levelup'], log="levelup", threshold=0.6)
        self.find_and_tap(current_screen, self.button_paths['challenge'], log="challenge", threshold=0.8)

    def handle_elite_stage(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['elite_join_battle'], use_enhanced=False, log="elite_join_battle", threshold=0.8)
        self.find_and_tap_position(current_screen, self.button_paths['restraining_enenemy_hero'], 1920/2, 1080/2, log="restraining_enenemy_hero")
        self.find_and_tap_position(current_screen, self.button_paths['victory'], 1920/2, 1080/5, log="victory")
        self.find_and_tap(current_screen, self.button_paths['skip_battle'], use_enhanced=False, log="skip_battle")
        self.find_and_tap(current_screen, self.button_paths['start_battle'], use_enhanced=False, log="start_battle", threshold=0.7)
        self.find_and_tap(current_screen, self.button_paths['tap_to_continue'], use_enhanced=False, log="tap_to_continue", threshold=0.8)

    def handle_dungeon_stage(self, current_screen):
        self.find_and_tap_position(current_screen, self.button_paths['dungeon_floor'], 1579, 985, log="dungeon_floor")
        self.find_and_tap_position(current_screen, self.button_paths['check_start_battle'], 1600/2, 900/2, log="check_start_battle")
        self.find_and_tap(current_screen, self.button_paths['continue_battling'],  log="continue_battling")
        self.handle_battle(current_screen)
