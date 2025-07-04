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


class DauLa(ADBGameAutomation):
    def __init__(self):
        ADBGameAutomation.__init__(self)

        self.main_path = "assets/dau-la"
        self.templates_dir = "assets/dau-la/templates"
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

    # Method find_all_templates đã được di chuyển sang base_auto.py để tái sử dụng

    def debug_detections(self, screen: np.ndarray, level_str: str, matches: List[Tuple[int, int, float]]):
        """Debug method để kiểm tra detections"""
        if len(matches) > 1:
            log_info(f"DEBUG Level {level_str}: {len(matches)} matches found")
            for i, (x, y, conf) in enumerate(matches):
                log_info(f"  Match {i+1}: ({x:4d}, {y:4d}) conf={conf:.3f}")
            
            # Kiểm tra distances giữa các matches
            for i in range(len(matches)):
                for j in range(i+1, len(matches)):
                    x1, y1, _ = matches[i]
                    x2, y2, _ = matches[j]
                    distance = np.sqrt((x1-x2)**2 + (y1-y2)**2)
                    log_info(f"    Distance {i+1}-{j+1}: {distance:.1f} pixels")

    def find_mergeable_pairs(self, screen: np.ndarray) -> List[Tuple[str, Tuple[int, int], Tuple[int, int]]]:
        mergeable_pairs = []
        for level in range(1, len(self.puzzle_path) + 1):
            level_str = str(level)
            if level_str in self.puzzle_path:
                template_path = self.puzzle_path[level_str]
                # Sử dụng find_template từ base class để kiểm tra trước
                first_match = self.find_template(screen, template_path, threshold=0.7, use_grayscale=False)
                if first_match is None:
                    continue  # Không có object loại này
                # Nếu có ít nhất 1 match, tìm tất cả matches
                matches = self.find_all_templates(screen, template_path, threshold=0.7, use_grayscale=False, debug=False)
                
                # Debug detections
                self.debug_detections(screen, level_str, matches)
                
                # Nếu có ít nhất 2 objects cùng loại, tạo pairs
                if len(matches) >= 2:
                    for i in range(0, len(matches) - 1, 2):  # Ghép từng cặp
                        if i + 1 < len(matches):
                            obj1 = (matches[i][0], matches[i][1])  # (x, y)
                            obj2 = (matches[i + 1][0], matches[i + 1][1])  # (x, y)
                            mergeable_pairs.append((level_str, obj1, obj2))
                            log_info(f"Found mergeable pair: level {level_str} at {obj1} and {obj2}")
        
        return mergeable_pairs

    def merge_objects(self, obj1_pos: Tuple[int, int], obj2_pos: Tuple[int, int]) -> bool:
        try:
            x1, y1 = obj1_pos
            x2, y2 = obj2_pos
            
            log_info(f"Merging objects: dragging from ({x1}, {y1}) to ({x2}, {y2})")
            
            # Thực hiện drag operation với duration dài hơn để đảm bảo merge
            success = self.drag(x1, y1, x2, y2, duration=100)
            
            if success:
                log_success(f"Successfully merged objects")
                time.sleep(1)  # Đợi animation merge hoàn thành
                return True
            else:
                log_error("Failed to drag objects")
                return False
                
        except Exception as e:
            log_error(f"Error merging objects: {e}")
            return False

    def auto_puzzle(self, current_screen):
        self.find_and_tap(current_screen, self.button_paths['get_object'], tap_count=5)
        try:
            log_info("Starting auto puzzle...")
            # Tìm các cặp objects có thể merge
            mergeable_pairs = self.find_mergeable_pairs(current_screen)
            if not mergeable_pairs:
                log_info("No mergeable pairs found")
                return False
            # Thực hiện merge cho từng cặp, ưu tiên level thấp trước
            merged_any = False
            for level, obj1_pos, obj2_pos in mergeable_pairs:
                log_info(f"Attempting to merge level {level} objects")
                
                if self.merge_objects(obj1_pos, obj2_pos):
                    merged_any = True
                    # Chỉ merge 1 cặp mỗi lần để tránh conflict
                    break
                else:
                    log_warning(f"Failed to merge level {level} objects")

            if merged_any:
                log_success("Auto puzzle completed a merge operation")
                current_screen = self.capture_screen()
                self.find_and_tap(current_screen, self.puzzle_button_path['claim_reward'], threshold=0.6)
                self.auto_puzzle(current_screen)
            return merged_any
            
        except Exception as e:
            log_error(f"Error in auto_puzzle: {e}")
            return False

    def process_game_actions(self):
        while self.running:
            try:
                current_screen = self.capture_screen()
                if current_screen is None:
                    time.sleep(1)
                    continue
                self.find_and_tap(current_screen, self.puzzle_button_path['claim_reward'], threshold=0.6)
                self.auto_puzzle(current_screen)

                
            except Exception as e:
                log_error(f"Error in process_game_actions: {e}")
                time.sleep(1)