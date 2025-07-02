import time
import asyncio
from pathlib import Path
from typing import Optional, Tuple
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
            'exit_result': f"{self.templates_dir}/exit_result.png",
        }
        self.map_check = {
            'mising_star': f"{self.templates_dir}/mising_star.png",
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

        # missing star
        self.missing_check_count = 0
        self.turn_number = 1
        self.check_missing_star = False

        self.turn_position = [
            [345, 1061],
            [443, 1062],
            [545, 1062],
            [654, 1062],
            [740, 1062],
            [840, 1062],
        ]
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen size of the connected device."""
        return self.adb.get_screen_size()
    
    def process_game_actions(self):
        while self.running:
            screen = self.capture_screen()
            if screen is None:
                log_warning("Failed to capture screen, retrying...")
                time.sleep(1)
                continue
            # self.thu_thach(screen)
            # self.cot_chuyen_chinh(screen)
            self.thap_event(screen)
            # self.thi_luyen(screen)
    
    def thu_thach(self, screen):
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['bat_dau_chien_dau'])
        self.find_and_tap(screen, self.button_paths['cua_tiep_theo'])


    def cot_chuyen_chinh(self, screen):
        if self.check_missing_star:
            if not self.find_and_tap(screen, self.map_check['mising_star']):
                self.swipe_up(1550, 626)
                self.missing_check_count += 1
                if self.missing_check_count % 3 == 0:
                    # Reset turn_number if it would exceed array bounds
                    if self.turn_number >= len(self.turn_position):
                        self.turn_number = 1
                        self.check_missing_star = False  # Stop checking for missing stars after cycling through all positions
                    else:
                        self.turn_number += 1
                    self.tap(self.turn_position[self.turn_number - 1][0], self.turn_position[self.turn_number - 1][1])

            self.find_and_tap(screen, self.button_paths['exit_result'])
        else:
            if not self.find_and_tap(screen, self.button_paths['current_map']):
                self.find_and_tap(screen, self.button_paths['current_map_2'])
            self.find_and_tap(screen, self.button_paths['cua_tiep_theo'])

        self.find_and_tap(screen, self.button_paths['skip_dialog'])
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['bat_dau_chien_dau'])
        self.find_and_tap(screen, self.button_paths['conga'])
        self.find_and_tap(screen, self.button_paths['conga_2'])
        self.find_and_tap(screen, self.button_paths['hoan_thanh_chuong'])      
        self.find_and_tap(screen, self.button_paths['hoan_thanh_chuong_check_2'])      
    

    
    def thap_event(self, screen):
        if screen is None:
            return
            
        try:
            template = self.load_template(self.map_check['giang_lam'])
            if template is None:
                log_error(f"Failed to load template: {self.map_check['giang_lam']}")
                return
                
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
            self.find_and_tap(screen, self.button_paths['exit_result'])
        except Exception as e:
            log_error(f"Error in thap_event: {e}")

    def thi_luyen(self, screen):
        self.find_and_tap(screen, self.button_paths['san_sang_chien_dau'])
        self.find_and_tap(screen, self.button_paths['thi_luyen_bat_dau'])
        self.find_and_tap(screen, self.button_thi_luyen['cua_tiep_theo_thi_luyen'])
