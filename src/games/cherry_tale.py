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


class CherryTale(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/cherry_tale"
        self.templates_dir = "assets/cherry_tale/templates"
        # Setup game specific paths
        self.button_paths = {
            'cua_tiep_theo': f"{self.templates_dir}/cua_tiep_theo.png",
            'stats': f"{self.templates_dir}/stats.png",
            'san_sang_chien_dau': f"{self.templates_dir}/san_sang_chien_dau.png",
            'check': f"{self.templates_dir}/check.png",
            'thi_luyen_bat_dau': f"{self.templates_dir}/thi_luyen_bat_dau.png",
            'bat_dau_chien_dau': f"{self.templates_dir}/bat_dau_chien_dau.png",
            'skip_dialog': f"{self.templates_dir}/skip_dialog.png",
            'conga': f"{self.templates_dir}/conga.png",
            'conga_2': f"{self.templates_dir}/conga_2.png",
            'hoan_thanh_chuong': f"{self.templates_dir}/hoan_thanh_chuong.png",
            'hoan_thanh_chuong_check_2': f"{self.templates_dir}/hoan_thanh_chuong_check_2.png",
            'current_map': f"{self.templates_dir}/current_map.png",
            'current_map_2': f"{self.templates_dir}/current_map_2.png",
            'tang_thap': f"{self.templates_dir}/tang_thap.png",
            'tang_thap_2': f"{self.templates_dir}/tang_thap_2.png",
            'tang_thap_3': f"{self.templates_dir}/tang_thap_3.png",
            'exit_tang_thap': f"{self.templates_dir}/exit_tang_thap.png",
        }
        self.map_check = {
            'giang_lam': f"{self.templates_dir}/giang_lam.png",
        }
        self.button_thi_luyen = {
            'cua_tiep_theo_thi_luyen': f"{self.templates_dir}/cua_tiep_theo_thi_luyen.png",
        }
        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
        # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.is_scroll_up = False
        # Add pause functionality for GUI
        self.paused = False
    
    def process_game_actions(self):
        while self.running:
            screen = self.capture_screen()
            self.thu_thach(screen)
            # self.cot_chuyen_chinh(screen)
            # self.thap_event(screen)
            # self.thi_luyen(screen)
    
    def thu_thach(self, screen):
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['bat_dau_chien_dau'])
        self.find_and_tap(screen, self.button_paths['cua_tiep_theo'])


    def cot_chuyen_chinh(self, screen):
        if not self.find_and_tap(screen, self.button_paths['current_map']):
            self.find_and_tap(screen, self.button_paths['current_map_2'])

        self.find_and_tap(screen, self.button_paths['skip_dialog'])
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['bat_dau_chien_dau'])
        self.find_and_tap(screen, self.button_paths['cua_tiep_theo'])
        self.find_and_tap(screen, self.button_paths['conga'])
        self.find_and_tap(screen, self.button_paths['conga_2'])
        self.find_and_tap(screen, self.button_paths['hoan_thanh_chuong'])      
        self.find_and_tap(screen, self.button_paths['hoan_thanh_chuong_check_2'])      
    
    def thap_event(self, screen):
        if self.find_template(screen, self.map_check['giang_lam']):
            if not self.find_and_tap(screen, self.button_paths['tang_thap_2']) and not self.find_and_tap(screen, self.button_paths['tang_thap_3']) and not self.find_and_tap(screen, self.button_paths['tang_thap']):
                if self.is_scroll_up:
                    self.swipe_up(1498, 626)
                else:
                    self.swipe_down(1498, 626) 
                self.is_scroll_up = not self.is_scroll_up
        self.find_and_tap(screen, self.button_paths['skip_dialog'])
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['bat_dau_chien_dau'])
        self.find_and_tap(screen, self.button_paths['hoan_thanh_chuong_check_2'])
        self.find_and_tap(screen, self.button_paths['exit_tang_thap'])    

    def thi_luyen(self, screen):
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['thi_luyen_bat_dau'])
        self.find_and_tap(screen, self.button_thi_luyen['cua_tiep_theo_thi_luyen'])
