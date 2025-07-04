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
            'panel_skip_dialog': f"{self.templates_dir}/panel_skip_dialog.png",
            'end_battle': f"{self.templates_dir}/end_battle.png",
            'end_battle_comfirm': f"{self.templates_dir}/end_battle_comfirm.png",
            'chon_doi': f"{self.templates_dir}/chon_doi.png",
            'bat_dau_tran_dau': f"{self.templates_dir}/bat_dau_tran_dau.png",
            'stage_clear': f"{self.templates_dir}/stage_clear.png",
            'thong_tin_nguoi_choi': f"{self.templates_dir}/thong_tin_nguoi_choi.png",
            'gui_di': f"{self.templates_dir}/gui_di.png",
        }
        self.main_story_path = {
            'current_map': f"{self.templates_dir}/current_map.png",
        }
        self.chon_doi = f"{self.templates_dir}/chon_doi_vr.png"
        self.vr_go_to = f"{self.templates_dir}/vr_go_to.png"
        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
        # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)

    
    def process_game_actions(self):
        while self.running:
            current_screen = self.capture_screen()
            self.check_skip_dialog(current_screen)
            self.auto_main_story(current_screen)
            #self.vr(current_screen)
    
    def check_skip_dialog(self, current_screen):
        if self.find_and_tap(current_screen, self.button_paths['skip_dialog'], threshold=0.9):
            self.wait_and_tap(self.button_paths['skip_dialog_confirm'])

    def auto_main_story(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['end_battle'])
        self.find_and_tap(current_screen, self.button_paths['end_battle_comfirm'])
        if self.find_and_tap(current_screen, self.main_story_path['current_map']):
            if self.wait_and_tap(self.button_paths['chon_doi']):
                self.wait_and_tap(self.button_paths['bat_dau_tran_dau'])
        self.find_and_tap(current_screen, self.button_paths['stage_clear'])

        if self.find_and_tap(current_screen, self.button_paths['thong_tin_nguoi_choi']):
            self.find_and_tap(current_screen, self.button_paths['gui_di'])

    def vr(self, current_screen):
        self.find_and_tap(current_screen, self.vr_go_to, threshold=0.8)
        self.find_and_tap(current_screen, self.chon_doi, threshold=0.8)
        self.find_and_tap(current_screen, self.button_paths['bat_dau_tran_dau'])
        self.find_and_tap(current_screen, self.button_paths['end_battle'])
        self.find_and_tap(current_screen, self.button_paths['end_battle_comfirm'])

