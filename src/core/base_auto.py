from colorama import Fore
import cv2
import numpy as np
import pyautogui
import time
import keyboard
from mss import mss
import sys
import logging
from typing import Tuple, Optional, Dict, Any, List
import win32gui
import win32con
import ctypes
from ctypes import wintypes
from datetime import datetime

import yaml
from utils import log_with_time, log_error, log_warning, log_success, log_info
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BaseGameAutomation:
    def __init__(self, window_title: str = None, config_file: str = None):
        self.sct = mss()
        self.running = False
        self.window_title = window_title
        self.window_handle = None
        self.monitor = None
        self.window_rect = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_window_check = 0
        self.window_check_interval = 1.0  # Check window position every 1 second
        self.config_file = config_file
        
        # Template caching for performance
        self.template_cache = {}
        self.template_cache_gray = {}
        
    def find_window(self) -> bool:
        """Find the game window by title without focusing it."""
        if not self.window_title:
            log_error("No window title specified")
            return False
            
        current_time = time.time()
        if current_time - self.last_window_check < self.window_check_interval:
            return bool(self.window_handle)
            
        try:
            self.window_handle = win32gui.FindWindow(None, self.window_title)
            
            if self.window_handle:
                try:
                    # Get window position and size
                    self.window_rect = win32gui.GetWindowRect(self.window_handle)
                    x, y, x1, y1 = self.window_rect
                    self.monitor = {
                        "top": y,
                        "left": x,
                        "width": x1 - x,
                        "height": y1 - y
                    }
                    self.last_window_check = current_time
                    return True
                except Exception as e:
                    log_warning(f"Could not get window position: {e}")
                    return False
            else:
                log_warning(f"Could not find window with title: {self.window_title}")
                return False
                
        except Exception as e:
            log_error(f"Error finding window: {e}")
            return False

    def load_template(self, template_path: str, grayscale: bool = False) -> Optional[np.ndarray]:
        cache_key = f"{template_path}_{grayscale}"
        cache = self.template_cache_gray if grayscale else self.template_cache
        
        # Check cache first
        if cache_key in cache:
            return cache[cache_key]
            
        try:
            if grayscale:
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            else:
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                
            if template is None:
                log_error(f"Could not load template {template_path}")
                return None
                
            template = template.astype(np.uint8)
            
            # Cache the template
            cache[cache_key] = template
            return template
            
        except Exception as e:
            log_error(f"Error loading template {template_path}: {e}")
            return None

    def capture_screen(self) -> Optional[np.ndarray]:
        if not self.monitor:
            return None
            
        try:
            # Capture only the game window area
            screenshot = self.sct.grab(self.monitor)
            # Convert from BGRA to BGR format
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            log_error(f"Error capturing screen: {e}")
            return None

    def find_template(self, screen: np.ndarray, template_path: str, threshold: float = 0.8, use_enhanced: bool = False, scale: float = 1.0, roi: Optional[Tuple[int, int, int, int]] = None, use_grayscale: bool = True) -> Optional[Tuple[int, int, float]]:
        if use_enhanced:
            return self.find_template_enhanced(screen, template_path, threshold)
        
        try:
            # Apply ROI if specified (x, y, width, height)
            roi_offset_x, roi_offset_y = 0, 0
            if roi:
                x, y, w, h = roi
                # Ensure ROI is within screen bounds
                x = max(0, min(x, screen.shape[1] - 1))
                y = max(0, min(y, screen.shape[0] - 1))
                w = min(w, screen.shape[1] - x)
                h = min(h, screen.shape[0] - y)
                screen = screen[y:y+h, x:x+w]
                roi_offset_x, roi_offset_y = x, y
            
            # Convert to grayscale for faster processing
            if use_grayscale:
                if len(screen.shape) == 3:
                    if screen.shape[-1] == 4:  # BGRA
                        screen_processed = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)
                    else:  # BGR
                        screen_processed = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                else:  # Already grayscale
                    screen_processed = screen
                    
                template = self.load_template(template_path, grayscale=True)
            else:
                # Color processing
                if screen.shape[-1] == 4:  # If BGRA
                    screen_processed = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
                else:
                    screen_processed = screen
                template = self.load_template(template_path, grayscale=False)
            
            if template is None:
                return None
            
            # Scale template if needed
            if scale != 1.0:
                width = int(template.shape[1] * scale)
                height = int(template.shape[0] * scale)
                if width <= 0 or height <= 0 or width > screen_processed.shape[1] or height > screen_processed.shape[0]:
                    return None
                template = cv2.resize(template, (width, height))
            
            # Ensure same data type
            screen_processed = screen_processed.astype(np.uint8)
            
            # Template matching
            result = cv2.matchTemplate(screen_processed, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Adjust coordinates for ROI offset
                final_x = max_loc[0] + roi_offset_x
                final_y = max_loc[1] + roi_offset_y
                # log_success(f"[{final_x}, {final_y}] {template_path} (confidence: {max_val:.3f})")
                return (final_x, final_y, max_val)
            # else:
            #     log_warning(f"Could not find {template_path} with confidence {max_val:.3f}")
        except Exception as e:
            if e == "'NoneType' object has no attribute 'shape'":
                return None
            log_error(f"Error in template matching: {e}")
        return None

    def find_template_enhanced(self, screen: np.ndarray, template_path: str, threshold: float = 0.8, scales = [1.0, 1.2]) -> Optional[Tuple[int, int, float]]:
        try:
            # Load template with caching (grayscale for speed)
            template_gray = self.load_template(template_path, grayscale=True)
            if template_gray is None:
                return None
            
            # Convert screen to grayscale for faster processing
            if len(screen.shape) == 3:
                if screen.shape[-1] == 4:  # BGRA
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)
                else:  # BGR
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            else:  # Already grayscale
                screen_gray = screen
            
            # Optimized scales - fewer scales for better performance
            best_result = None
            best_confidence = -1
            
            for scale in scales:
                # Resize template
                if scale != 1.0:
                    width = int(template_gray.shape[1] * scale)
                    height = int(template_gray.shape[0] * scale)
                    # Skip invalid sizes
                    if width <= 0 or height <= 0 or width > screen_gray.shape[1] or height > screen_gray.shape[0]:
                        continue
                    scaled_template = cv2.resize(template_gray, (width, height))
                else:
                    scaled_template = template_gray
                
                # Simple template matching without preprocessing variants for speed
                result = cv2.matchTemplate(screen_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence and max_val >= threshold:
                    h, w = scaled_template.shape
                    x = max_loc[0] + w//2
                    y = max_loc[1] + h//2
                    best_result = (x, y, max_val)
                    best_confidence = max_val
            # Early exit if we find a very confident match
                if max_val >= 0.95:
                    log_success(f"Found excellent match of {template_path} at scale {scale:.1f} with confidence {max_val:.3f}")
                    break
                        
            return best_result

        except Exception as e:
            log_error(f"Error in enhanced template matching for {template_path}: {e}")
            return None
    
    def wait_for_template(self, template_path: str, threshold: float = 0.75, timeout: float = 10.0) -> Optional[Tuple[int, int, float]]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            screen = self.capture_screen()  # Capture screen mới mỗi lần check
            if screen is None:
                time.sleep(0.1)
                continue
                
            result = self.find_template(screen, template_path, threshold)
            if result:
                x, y, confidence = result
                return (x, y, confidence)  # Return as tuple to avoid numpy array issues
            time.sleep(0.1)
        return None
    
    def wait_and_click(self, template_path: str, threshold: float = 0.75, timeout: float = 10.0) -> Optional[Tuple[int, int, float]]:
        result = self.wait_for_template(template_path, threshold, timeout)
        if result:
            x, y, confidence = result
            self.click(x, y)
            return True
        return False
    
    def is_point_in_window(self, x: int, y: int) -> bool:
        if not self.monitor:
            return False
        return (self.monitor["left"] <= x <= self.monitor["left"] + self.monitor["width"] and
                self.monitor["top"] <= y <= self.monitor["top"] + self.monitor["height"])

    def scroll(self, x: int, y: int, clicks: int, retries: int = 3) -> bool:
        for attempt in range(retries):
            try:
                # Convert to absolute coordinates
                abs_x = x + self.monitor["left"]
                abs_y = y + self.monitor["top"]
                
                # Only scroll if the point is within the game window
                if self.is_point_in_window(abs_x, abs_y):
                    # Verify we're scrolling in the correct window
                    window_at_point = win32gui.WindowFromPoint((abs_x, abs_y))
                    if window_at_point == self.window_handle:
                        # Move mouse to position first
                        pyautogui.moveTo(abs_x, abs_y)
                        # Perform scroll
                        pyautogui.scroll(clicks)
                        return True
                    else:
                        log_warning(f"Scroll point ({abs_x}, {abs_y}) is not in the game window")
                else:
                    log_warning(f"Scroll point ({abs_x}, {abs_y}) is outside game window bounds")
                
                if attempt < retries - 1:
                    time.sleep(0.5)  # Wait before retry
                    
            except Exception as e:
                log_error(f"Error scrolling at ({x}, {y}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        return False

    def click_image(self,button_path: str, threshold: float = 0.8, offset: Tuple[int, int] = (0, 0), retries: int = 1, duration: float = 0, log:str = "") -> bool:
        screen = self.capture_screen()
        if screen is None:
            return False
        for attempt in range(retries):
            result = self.find_template(screen, button_path, threshold)
            if result:
                x, y, confidence = result
                if self.click(x + offset[0], y + offset[1], duration):
                    if log != "":
                        log_success(log + f" (confidence: {confidence:.2f})")
                    return True
            else:
                self.logger.debug(f"Button {button_path} not found (attempt {attempt + 1}/{retries})")
            
            if attempt < retries - 1:
                time.sleep(0.5)
                screen = self.capture_screen()  # Refresh screen for retry
                
        return False
    
    def click(self, x: int, y: int, duration: float = 0, retries: int = 3):
        for attempt in range(retries):
            try:
                # Convert to absolute coordinates
                abs_x = x + self.monitor["left"]
                abs_y = y + self.monitor["top"]
                
                # Only click if the point is within the game window
                if self.is_point_in_window(abs_x, abs_y):
                    # Verify we're clicking in the correct window
                    window_at_point = win32gui.WindowFromPoint((abs_x, abs_y))
                    if window_at_point == self.window_handle:
                        # Add duration parameter to click
                        pyautogui.click(x=abs_x, y=abs_y, clicks=1, interval=0.0, button='left', duration=duration)
                        return True
                    else:
                        log_warning(f"Click point ({abs_x}, {abs_y}) is not in the game window")
                else:
                    log_warning(f"Click point ({abs_x}, {abs_y}) is outside game window bounds")
                
                if attempt < retries - 1:
                    time.sleep(0.5)  # Wait before retry
                    
            except Exception as e:
                log_error(f"Error clicking at ({x}, {y}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        return False

    def find_and_click(self,screen: np.ndarray, template_path: str, threshold: float = 0.8, offset: Tuple[int, int] = (0, 0), retries: int = 1, duration: float = 0, log:str = "") -> bool:
        if screen is None:
            return False
        result = self.find_template(screen, template_path, threshold)
        if result:
            x, y, confidence = result
            if self.click(x + offset[0], y + offset[1], duration):
                if log != "":
                    log_success(log + f" (confidence: {confidence:.2f})")
                return True
        return False
    def find_and_click_position(self, screen: np.ndarray,template_path: str, x: int, y: int, threshold: float = 0.8, offset: Tuple[int, int] = (0, 0), retries: int = 1, duration: float = 0, log:str = "") -> bool:
        if screen is None:
            return False
        result = self.find_template(screen, template_path, threshold)
        if result:
            if self.click(x, y, duration):
                return True
        return False
    
    def find_and_click_position_with_offset(self, screen: np.ndarray,template_path: str, offset: Tuple[int, int] = (0, 0), threshold: float = 0.8, retries: int = 1, duration: float = 0, log:str = "") -> bool:
        if screen is None:
            return False
        result = self.find_template(screen, template_path, threshold)
        if result:
            x, y, confidence = result
            if self.click(x + offset[0], y + offset[1], duration):
                return True
        return False
    
    def process_game_actions(self):
        """Process game-specific actions. Should be implemented by child classes."""
        raise NotImplementedError("This method should be implemented by child classes")

    def start(self):
        """Start the automation process with improved error handling."""
        if not self.find_window():
            log_error("Failed to find game window")
            return
            
        log_info("Starting automation... Press 'q' to quit")
        self.running = True
        
        last_error_time = 0
        error_cooldown = 5.0  # Minimum time between error messages
        
        while self.running:
            try:
                if keyboard.is_pressed('q'):
                    log_info("Stopping automation...")
                    self.running = False
                    break
                    
                # Re-check window position periodically
                if not self.find_window():
                    current_time = time.time()
                    if current_time - last_error_time >= error_cooldown:
                        log_warning("Window lost, retrying...")
                        last_error_time = current_time
                    time.sleep(1)
                    continue
                    
                # Verify window is active
                foreground_window = win32gui.GetForegroundWindow()
                if foreground_window != self.window_handle:
                    current_time = time.time()
                    if current_time - last_error_time >= error_cooldown:
                        log_warning("Game window is not active, waiting...")
                        last_error_time = current_time
                    time.sleep(1)
                    continue
                    
                # Capture screen
                screen = self.capture_screen()
                if screen is not None:
                    self.process_game_actions(screen)
                else:
                    time.sleep(1)
                    
            except Exception as e:
                current_time = time.time()
                if current_time - last_error_time >= error_cooldown:
                    log_error(f"Error in main loop: {e}")
                    last_error_time = current_time
                time.sleep(1)

    def set_window_size(self, width: int, height: int) -> bool:
        log_info(f"Setting window size to {width}x{height}")
        if not self.window_title:
            log_error("No window title specified")
            return False
        try:
            # Find window by title
            window_handle = win32gui.FindWindow(None, self.window_title)
            if not window_handle:
                log_error(f"Could not find window with title: {self.window_title}")
                return False

            # Get current window position
            x, y, _, _ = win32gui.GetWindowRect(window_handle)
            
            # Calculate the window size including borders and title bar
            window_style = win32gui.GetWindowLong(window_handle, win32con.GWL_STYLE)
            border_rect = wintypes.RECT()
            ctypes.windll.user32.AdjustWindowRectEx(ctypes.byref(border_rect), window_style, False, 0)
            
            # Add border size to requested dimensions
            total_width = width + (border_rect.right - border_rect.left)
            total_height = height + (border_rect.bottom - border_rect.top)
            
            # Set new window size and position
            win32gui.SetWindowPos(
                window_handle,
                win32con.HWND_TOP,
                x, y,
                total_width,
                total_height,
                win32con.SWP_NOMOVE | win32con.SWP_NOZORDER
            )
            
            # Update monitor information
            self.window_rect = win32gui.GetWindowRect(window_handle)
            x, y, x1, y1 = self.window_rect
            self.monitor = {
                "top": y,
                "left": x,
                "width": x1 - x,
                "height": y1 - y
            }
            
            log_success(f"Window size set to {width}x{height}")
            return True
            
        except Exception as e:
            log_error(f"Error setting window size: {e}")
            return False

    def get_center_point(self, screen: np.ndarray) -> Tuple[int, int]:
        screen_width, screen_height = screen.shape[1], screen.shape[0]
        print(screen_width, screen_height)
        return screen_width//2, screen_height//2
    
    def load_config(self, config_path: str):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    def find_template_fast(self, screen: np.ndarray, template_path: str, threshold: float = 0.8, downsample_factor: float = 0.5) -> Optional[Tuple[int, int, float]]:
        """Ultra-fast template matching using downsampling and then refining."""
        try:
            # Load template with caching (grayscale for speed)
            template_gray = self.load_template(template_path, grayscale=True)
            if template_gray is None:
                return None
            
            # Convert screen to grayscale
            if len(screen.shape) == 3:
                if screen.shape[-1] == 4:  # BGRA
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)
                else:  # BGR
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            else:
                screen_gray = screen
            
            # Downsample for fast initial search
            if downsample_factor < 1.0:
                # Downsample screen and template
                down_screen = cv2.resize(screen_gray, 
                                       (int(screen_gray.shape[1] * downsample_factor), 
                                        int(screen_gray.shape[0] * downsample_factor)))
                down_template = cv2.resize(template_gray,
                                         (int(template_gray.shape[1] * downsample_factor),
                                          int(template_gray.shape[0] * downsample_factor)))
                
                # Fast search on downsampled images
                result = cv2.matchTemplate(down_screen, down_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold * 0.8:  # Lower threshold for downsampled
                    # Scale back coordinates for refined search
                    scale_back = 1.0 / downsample_factor
                    approx_x = int(max_loc[0] * scale_back)
                    approx_y = int(max_loc[1] * scale_back)
                    
                    # Define ROI around the approximate location for refined search
                    margin = max(template_gray.shape[0], template_gray.shape[1])
                    roi_x = max(0, approx_x - margin//2)
                    roi_y = max(0, approx_y - margin//2)
                    roi_w = min(screen_gray.shape[1] - roi_x, margin * 2)
                    roi_h = min(screen_gray.shape[0] - roi_y, margin * 2)
                    
                    # Refined search in ROI
                    roi_screen = screen_gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
                    refined_result = cv2.matchTemplate(roi_screen, template_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(refined_result)
                    
                    if max_val >= threshold:
                        final_x = max_loc[0] + roi_x
                        final_y = max_loc[1] + roi_y
                        log_success(f"Found {template_path} at {final_x}, {final_y} with confidence {max_val:.3f} (fast)")
                        return (final_x, final_y, max_val)
            else:
                # No downsampling, direct search
                result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    log_success(f"Found {template_path} at {max_loc[0]}, {max_loc[1]} with confidence {max_val:.3f}")
                    return (max_loc[0], max_loc[1], max_val)
            
        except Exception as e:
            log_error(f"Error in fast template matching: {e}")
        return None

    def clear_template_cache(self):
        """Clear template cache to free memory."""
        self.template_cache.clear()
        self.template_cache_gray.clear()
        log_info("Template cache cleared")

    def get_cache_info(self):
        """Get information about template cache."""
        color_count = len(self.template_cache)
        gray_count = len(self.template_cache_gray)
        log_info(f"Template cache: {color_count} color templates, {gray_count} grayscale templates")
        return color_count, gray_count

def main():
    print("This is a base class. Please use a specific game automation class.")

if __name__ == "__main__":
    main() 