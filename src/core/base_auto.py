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
import os
import threading

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
        
        # Continuous screen capture
        self.capture_interval = 0.5  # Capture every 0.5 seconds
        self.latest_screen = None
        self.screen_lock = threading.Lock()
        self.capture_thread = None
        self.capture_running = False
        
    def _continuous_capture_worker(self):
        """Background thread worker for continuous screen capture."""
        log_info("Starting continuous screen capture thread")
        while self.capture_running:
            try:
                if self.monitor:
                    # Capture screen
                    screenshot = self.sct.grab(self.monitor)
                    # Convert from BGRA to BGR format
                    img = np.array(screenshot)
                    screen = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Update latest screen with thread safety
                    with self.screen_lock:
                        self.latest_screen = screen
                        
                time.sleep(self.capture_interval)
            except Exception as e:
                log_error(f"Error in continuous capture: {e}")
                time.sleep(self.capture_interval)
        log_info("Continuous screen capture thread stopped")
    
    def start_continuous_capture(self):
        """Start the continuous screen capture thread."""
        if not self.capture_running:
            self.capture_running = True
            self.capture_thread = threading.Thread(target=self._continuous_capture_worker, daemon=True)
            self.capture_thread.start()
            log_info("Continuous screen capture started")
    
    def stop_continuous_capture(self):
        """Stop the continuous screen capture thread."""
        if self.capture_running:
            self.capture_running = False
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2.0)
            log_info("Continuous screen capture stopped")
    
   
   
    def get_latest_screen(self) -> Optional[np.ndarray]:
        """Get the latest captured screen with thread safety."""
        with self.screen_lock:
            return self.latest_screen.copy() if self.latest_screen is not None else None

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
        try:
            if grayscale:
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            else:
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                
            if template is None:
                log_error(f"Could not load template {template_path}")
                return None
                
            template = template.astype(np.uint8)
            return template
            
        except Exception as e:
            log_error(f"Error loading template {template_path}: {e}")
            return None

    def capture_screen(self) -> Optional[np.ndarray]:
        """Get screen - either latest from continuous capture or capture new one."""
        if self.capture_running:
            return self.get_latest_screen()
        else:
            # Fallback to direct capture if continuous capture is disabled
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

    def find_template(self, template_path: str, threshold: float = 0.8, use_grayscale: bool = False, debug: bool = True) -> Optional[Tuple[int, int, float]]:
        screen = self.get_latest_screen()
        if screen is None:
            log_info("No screen available from continuous capture")
            return None
        try:
            roi_offset_x, roi_offset_y = 0, 0
            
            if use_grayscale:
                # Convert screen to grayscale
                if len(screen.shape) == 3:
                    screen_processed = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                else:  # Already grayscale
                    screen_processed = screen
                    
                template = self.load_template(template_path, grayscale=True)
            else:
                # Color processing - screen is already in BGR format from capture_screen()
                screen_processed = screen.copy()  # Screen is already BGR from capture_screen()
                template = self.load_template(template_path, grayscale=False)
            
            if template is None:
                return None
                
            # Ensure both images have the same data type
            screen_processed = screen_processed.astype(np.uint8)
            template = template.astype(np.uint8)
            
            # Perform template matching
            result = cv2.matchTemplate(screen_processed, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                final_x = max_loc[0] + roi_offset_x
                final_y = max_loc[1] + roi_offset_y
                
                if debug: # debug mode
                    # Create debug image with rectangle
                    debug_img = screen_processed.copy()
                    cv2.rectangle(debug_img, 
                                (max_loc[0], max_loc[1]), 
                                (max_loc[0] + template.shape[1], max_loc[1] + template.shape[0]), 
                                (0, 0, 255), 2)
                    
                    # Add confidence text
                    cv2.putText(debug_img, f'Conf: {max_val:.3f}' + f' {template_path}' , 
                              (max_loc[0]-20, max_loc[1] - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Save debug image
                    os.makedirs("logs/screen_processed", exist_ok=True)
                    template_filename = os.path.basename(template_path)
                    save_path = f"logs/screen_processed/{template_filename}"
                    cv2.imwrite(save_path, debug_img)
                    
                    # Display resized image to avoid large windows
                    display_img = cv2.resize(debug_img, (0,0), fx=0.5, fy=0.5)
                    cv2.imshow("Template Matching Debug", display_img)
                    cv2.waitKey(1)  # Process GUI events
                    
                return (final_x, final_y, max_val)

        except Exception as e:
            if str(e) == "'NoneType' object has no attribute 'shape'":
                return None
            log_error(f"Error in template matching: {e}")
        return None

    def wait_for_template(self, template_path: str, threshold: float = 0.75, timeout: float = 10.0) -> Optional[Tuple[int, int, float]]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.find_template(template_path, threshold)
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
        for attempt in range(retries):
            result = self.find_template(button_path, threshold)
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

    def find_and_click(self, template_path: str, threshold: float = 0.8, offset: Tuple[int, int] = (0, 0), retries: int = 1, duration: float = 0, log:str = "") -> bool:
        result = self.find_template(template_path, threshold)
        if result:
            x, y, confidence = result
            if self.click(x + offset[0], y + offset[1], duration):
                if log != "":
                    log_success(log + f" (confidence: {confidence:.2f})")
                return True
        return False
  
    def find_and_click_position(self, template_path: str, x: int, y: int, threshold: float = 0.8, offset: Tuple[int, int] = (0, 0), retries: int = 1, duration: float = 0, log:str = "") -> bool:
        result = self.find_template(template_path, threshold)
        if result:
            if self.click(x, y, duration):
                return True
        return False
    
    def find_and_click_position_with_offset(self, template_path: str, offset: Tuple[int, int] = (0, 0), threshold: float = 0.8, retries: int = 1, duration: float = 0, log:str = "") -> bool:
        result = self.find_template(template_path, threshold)
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
        
        # Start continuous screen capture
        self.start_continuous_capture()
        
        last_error_time = 0
        error_cooldown = 5.0  # Minimum time between error messages
        
        try:
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
                        
                    # Process game actions (screen capture is now handled by background thread)
                    self.process_game_actions()
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.1)
                        
                except Exception as e:
                    current_time = time.time()
                    if current_time - last_error_time >= error_cooldown:
                        log_error(f"Error in main loop: {e}")
                        last_error_time = current_time
                    time.sleep(1)
        finally:
            # Stop continuous capture when exiting
            if self.capture_running:
                self.stop_continuous_capture()

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
            # Load template (grayscale for speed)
            template_gray = self.load_template(template_path, grayscale=True)
            if template_gray is None:
                return None
            
            # Convert screen to grayscale (screen is already BGR from capture_screen)
            if len(screen.shape) == 3:
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            else:
                screen_gray = screen
            
            # Ensure data types are consistent
            screen_gray = screen_gray.astype(np.uint8)
            template_gray = template_gray.astype(np.uint8)
            
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
                        log_success(f"Found {os.path.basename(template_path)} at {final_x}, {final_y} with confidence {max_val:.3f} (fast)")
                        return (final_x, final_y, max_val)
            else:
                # No downsampling, direct search
                result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    log_success(f"Found {os.path.basename(template_path)} at {max_loc[0]}, {max_loc[1]} with confidence {max_val:.3f}")
                    return (max_loc[0], max_loc[1], max_val)
            
        except Exception as e:
            log_error(f"Error in fast template matching: {e}")
        return None

    def find_all_templates(self, screen: np.ndarray, template_path: str, threshold: float = 0.8, use_grayscale: bool = True, debug: bool = False) -> List[Tuple[int, int, float]]:
        try:
            # Use consistent preprocessing logic like find_template method
            roi_offset_x, roi_offset_y = 0, 0
            
            if use_grayscale:
                # Convert screen to grayscale (screen is already BGR from capture_screen)
                if len(screen.shape) == 3:
                    screen_processed = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                else:  # Already grayscale
                    screen_processed = screen
                    
                template = self.load_template(template_path, grayscale=True)
            else:
                # Color processing - screen is already in BGR format from capture_screen()
                screen_processed = screen.copy()
                template = self.load_template(template_path, grayscale=False)
            
            if template is None:
                return []
            
            # Ensure data types are consistent
            screen_processed = screen_processed.astype(np.uint8)
            template = template.astype(np.uint8)
            
            result = cv2.matchTemplate(screen_processed, template, cv2.TM_CCOEFF_NORMED)
            
            # Find all locations with confidence >= threshold  
            locations = np.where(result >= threshold)
            matches = []
            
            # Filter out nearby matches (improved non-maximum suppression)
            template_h, template_w = template.shape[:2]
            
            # Create list of all candidates first
            candidates = []
            for pt in zip(*locations[::-1]):  # Switch x and y
                x, y = pt
                confidence = result[y, x]
                final_x = x + roi_offset_x + template_w // 2  # Center point
                final_y = y + roi_offset_y + template_h // 2  # Center point
                candidates.append((final_x, final_y, confidence))
            
            # Sort candidates by confidence descending
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            # Non-maximum suppression with larger threshold
            min_distance = max(template_w, template_h) * 0.8  # Increased from 0.5 to 0.8
            
            for candidate in candidates:
                x, y, confidence = candidate
                
                # Check if there's any nearby match (avoid duplicates)
                is_duplicate = False
                for existing_match in matches:
                    existing_x, existing_y, _ = existing_match
                    distance = np.sqrt((x - existing_x)**2 + (y - existing_y)**2)
                    if distance < min_distance:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    matches.append((x, y, confidence))
            
            # Logging based on debug parameter
            if debug or len(matches) > 10:
                log_info(f"Found {len(matches)} instances of {os.path.basename(template_path)} with threshold {threshold}")
                
                if debug:
                    # Debug mode: log all matches
                    for i, (x, y, conf) in enumerate(matches):
                        log_info(f"  Match {i+1}: ({x}, {y}) confidence={conf:.3f}")
                elif len(matches) > 10:
                    # Warning mode: too many matches
                    log_warning(f"Too many matches ({len(matches)}) found - possible false positives")
                    for i, (x, y, conf) in enumerate(matches[:5]):  # Only log first 5 matches
                        log_warning(f"  Match {i+1}: ({x}, {y}) confidence={conf:.3f}")
                    log_warning("  ...")
            else:
                # Normal mode: only log summary
                log_info(f"Found {len(matches)} instances of {os.path.basename(template_path)}")
                
            return matches

        except Exception as e:
            log_error(f"Error finding all templates: {e}")
            return []

def main():
    print("This is a base class. Please use a specific game automation class.")

if __name__ == "__main__":
    main() 