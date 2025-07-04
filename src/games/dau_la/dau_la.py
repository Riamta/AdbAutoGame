import time
import asyncio
import os
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import cv2
from src.core.adb_auto import ADBGameAutomation
from src.utils.logging import setup_logger, log_error, log_state, log_warning, log_success, log_info
from enum import Enum, auto

class GameState(Enum):
    UNKNOWN = auto()
    MAIN_MENU = auto()
    BATTLE = auto()
    DUONG_MON = auto()


class DauLa(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/dau-la"
        self.templates_dir = "assets/dau-la/templates"
        self.check_state_path = {
            'is_duon_mon': f"{self.templates_dir}/is_duon_mon.png",
        }
        # Setup game specific paths
        self.button_paths = {
            'get_object': f"{self.templates_dir}/puzzle/get_object.png",
        }
        self.puzzle_button_path = {
            'claim_reward': f"{self.templates_dir}/puzzle/claim_reward.png",
        }
        self.puzzle_path = {
            '1': f"{self.templates_dir}/puzzle/1.png",
            '2': f"{self.templates_dir}/puzzle/2.png",
            '3': f"{self.templates_dir}/puzzle/3.png",
            '4': f"{self.templates_dir}/puzzle/4.png",
            '5': f"{self.templates_dir}/puzzle/5.png",
            '6': f"{self.templates_dir}/puzzle/6.png",
            '7': f"{self.templates_dir}/puzzle/7.png",
            '8': f"{self.templates_dir}/puzzle/8.png",
            '9': f"{self.templates_dir}/puzzle/9.png",
            '10': f"{self.templates_dir}/puzzle/10.png",
            '11': f"{self.templates_dir}/puzzle/11.png",
            '12': f"{self.templates_dir}/puzzle/12.png",
            '13': f"{self.templates_dir}/puzzle/13.png",
            '14': f"{self.templates_dir}/puzzle/14.png",
            '15': f"{self.templates_dir}/puzzle/15.png",
            '16': f"{self.templates_dir}/puzzle/16.png",
            '17': f"{self.templates_dir}/puzzle/17.png",
            '18': f"{self.templates_dir}/puzzle/18.png",
            '19': f"{self.templates_dir}/puzzle/19.png",
            '20': f"{self.templates_dir}/puzzle/20.png",
        } 


        # Initialize game state tracking
        self.current_state = GameState.UNKNOWN
        self.last_state_change = time.time()
                # Create a thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)

        self.duong_mon_path = {
            'duong_mon': f"{self.templates_dir}/duong_mon.png",
            'duong_mon_reward': f"{self.templates_dir}/duong_mon_reward.png",
            'duong_mon_reward_2': f"{self.templates_dir}/duong_mon_reward_2.png",
            'duong_mon_vo_duong': f"{self.templates_dir}/duong_mon_vo_duong.png",
            'duong_mon_vo_duong_quest': f"{self.templates_dir}/duong_mon_vo_duong_quest.png",
            'duong_mon_vo_duong_back': f"{self.templates_dir}/duong_mon_vo_duong_back.png",
            'duong_mon_vo_duong_quick_quest': f"{self.templates_dir}/duong_mon_vo_duong_quick_quest.png",
            'duong_mon_man_duong': f"{self.templates_dir}/duong_mon_man_duong.png",

            'duong_mon_dai_ngo': f"{self.templates_dir}/duong_mon_dai_ngo.png",
            'muc_tieu_dai_ngo': f"{self.templates_dir}/muc_tieu_dai_ngo.png",
            'dai_ngo_x5': f"{self.templates_dir}/dai_ngo_x5.png",
            'thu_thach_dai_ngo': f"{self.templates_dir}/thu_thach_dai_ngo.png",
        }
        self.duong_mon_vo_duong = False
        self.duong_mon_man_duong = False
        self.duong_mon_dai_ngo = False

    def process_game_actions(self):
        print("process_game_actions")
        self.check_state()
        self.auto_duong_mon()
    
    def check_state(self):
        print("check_state")
        if self.find_template(self.check_state_path['is_duon_mon']):
            self.current_state = GameState.DUONG_MON
            self.last_state_change = time.time()
        else:
            self.current_state = GameState.MAIN_MENU
            self.last_state_change = time.time()

    def auto_duong_mon(self):
        if self.current_state != GameState.DUONG_MON:
            self.find_and_tap(self.duong_mon_path['duong_mon'])
            time.sleep(1.5)
        else:
            if self.find_template(self.duong_mon_path['duong_mon_reward']):
                for i in range(1, 10):
                    self.find_and_tap(self.duong_mon_path['duong_mon_reward'])
                    time.sleep(0.5)
            elif self.find_template(self.duong_mon_path['duong_mon_reward_2']):
                for i in range(1, 5):
                    self.find_and_tap(self.duong_mon_path['duong_mon_reward_2'])
                    time.sleep(0.5)

            if self.find_template(self.duong_mon_path['duong_mon_vo_duong']) and self.duong_mon_vo_duong == False:
                self.find_and_tap(self.duong_mon_path['duong_mon_vo_duong'])
                time.sleep(1.5)
                while self.duong_mon_vo_duong == False:
                    if not self.find_template(self.duong_mon_path['duong_mon_vo_duong_quest']):
                        self.find_and_tap(self.duong_mon_path['duong_mon_vo_duong_back'])
                        self.duong_mon_vo_duong = True
                        time.sleep(0.5)
                    else:
                        while self.find_template(self.duong_mon_path['duong_mon_vo_duong_quest']):
                            if self.find_and_tap(self.duong_mon_path['duong_mon_vo_duong_quest']): 
                                 self.wait_and_tap(self.duong_mon_path['duong_mon_vo_duong_quick_quest'])
                            time.sleep(0.5)
                            break
            elif self.find_template(self.duong_mon_path['duong_mon_dai_ngo']) and self.duong_mon_dai_ngo == False:
                self.thang_cap = False
                self.find_and_tap(self.duong_mon_path['duong_mon_dai_ngo'])
                time.sleep(1.5)
                while self.thang_cap == False:
                    time.sleep(0.5)
                    if not self.find_template(self.duong_mon_path['muc_tieu_dai_ngo']):
                        self.find_and_tap(self.duong_mon_path['duong_mon_vo_duong_back'])
                        self.duong_mon_dai_ngo = True
                    else:
                        self.find_and_tap(self.duong_mon_path['muc_tieu_dai_ngo'])
                        self.tap(1692, 930)
                        self.thang_cap = True
                        break
                    


