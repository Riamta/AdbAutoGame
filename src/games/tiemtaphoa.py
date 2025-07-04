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


class TiemTapHoa(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/tiemtaphoa"
        self.templates_dir = "assets/tiemtaphoa/templates"
        # Setup game specific paths
        self.food_path = {
            'banh_bao_icon' : f"{self.templates_dir}/banh_bao_icon.png",
            'noi_banh_bao' : f"{self.templates_dir}/noi_banh_bao.png",
            'banh_goi' : f"{self.templates_dir}/banh_goi.png",
            'banh_goi_icon' : f"{self.templates_dir}/banh_goi_icon.png",
            'khoai_icon' : f"{self.templates_dir}/khoai_icon.png",
            'noi_khoai' : f"{self.templates_dir}/noi_khoai.png",
            'quay_icon' : f"{self.templates_dir}/quay_icon.png",
            'noi_quay' : f"{self.templates_dir}/noi_quay.png",
        }
        self.button_paths = {

        }
        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()

        # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)

    
    def process_game_actions(self):
        while self.running:
            current_screen = self.capture_screen()
            self.quan_do_an_sang(current_screen)

    def quan_do_an_sang(self, current_screen):
        if self.find_template(current_screen, self.food_path['banh_goi_icon'], 0.2):
            self.find_and_tap(current_screen, self.food_path['banh_goi'], log="banh_goi", threshold=0.2)

        if self.find_template(current_screen, self.food_path['khoai_icon'], 0.2):
            self.find_and_tap(current_screen, self.food_path['noi_khoai'], log="khoai", threshold=0.6)

        if self.find_template(current_screen, self.food_path['quay_icon'], 0.2):
            self.find_and_tap(current_screen, self.food_path['noi_quay'], log="quay", threshold=0.6)

        if self.find_template(current_screen, self.food_path['banh_bao_icon'], 0):
            self.find_and_tap(current_screen, self.food_path['noi_banh_bao'], log="banh_bao", threshold=0.2)
