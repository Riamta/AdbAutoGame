import cv2
import keyboard
import numpy as np
import time
import asyncio
import threading
from typing import Tuple, Optional
from ppadb.client import Client as AdbClient
from utils import log_error, log_info, log_success, log_warning
from .base_auto import BaseGameAutomation
from .adb import ADBController

class ADBGameAutomation(BaseGameAutomation):
    def __init__(self, config_file: Optional[str] = None, device_id: str = None, host: str = "127.0.0.1", port: int = 5037):
        # Initialize with None window_title since we don't need window handling for ADB
        super().__init__(window_title=None, config_file=config_file)
        # Initialize ADB controller
        self.adb = ADBController(device_id=device_id, host=host, port=port)
        self.window_handle = 1  # Dummy value to prevent None checks
        self.monitor = {"top": 0, "left": 0, "width": 0, "height": 0}  # Will be updated with device screen size
        width, height = self.adb.get_screen_size()
        if width > 0 and height > 0:
            self.monitor["width"] = width
            self.monitor["height"] = height
        
        # Override continuous capture settings for ADB
        self.capture_interval = 0.5  # Capture every 0.5 seconds for ADB
    
    def _continuous_capture_worker(self):
        log_info("Starting continuous ADB screen capture thread")
        while self.capture_running:
            try:
                result = self.adb.capture_screen_raw()
                if result:
                    nparr = np.frombuffer(result, np.uint8)
                    screen = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if screen is not None:
                        # Update latest screen with thread safety
                        with self.screen_lock:
                            self.latest_screen = screen
                        
                time.sleep(self.capture_interval)
            except Exception as e:
                log_error(f"Error in continuous ADB capture: {e}")
                time.sleep(self.capture_interval)
        log_info("Continuous ADB screen capture thread stopped")

    def find_window(self) -> bool:
        return True

    def capture_screen(self) -> Optional[np.ndarray]:
        """Get screen - either latest from continuous capture or capture new one."""
        if self.capture_running:
            return self.get_latest_screen()
        else:
            # Fallback to direct capture if continuous capture is disabled
            try:
                result = self.adb.capture_screen_raw()
                if not result:
                    log_warning("Empty screencap result")
                    return None
                nparr = np.frombuffer(result, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if image is None:
                    log_error("Failed to decode screenshot")
                    return None

                return image

            except Exception as e:
                log_error(f"Error capturing screen: {e}")
                return None
    
    # Tap gesture
    def tap(self, x: int, y: int, duration: float = 0.1, tap_count: int = 1) -> bool:
        return self.adb.tap(x, y, duration, tap_count)
        
    def find_and_tap(self, template_name: str, log: str = "", threshold = 0.8, tap_count: int = 1) -> bool:
        start_time = time.time()
        template = self.load_template(template_name)
        if template is None:
            log_error(f"Failed to load template {template_name}")
            return False
        
        result = self.find_template(template_name, threshold=threshold)
        if result:
            x, y, confidence = result
            tap_start = time.time()
            if self.tap(x, y, tap_count = tap_count):
                tap_time = time.time() - tap_start
                total_time = time.time() - start_time
                log_success(f"[FIND TAP] - [{x}, {y}] - [{template_name.replace(self.templates_dir, '').replace('/', '')}] - [confidence: {confidence:.2f}, tap: {tap_time:.2f}s, total: {total_time:.2f}s]")
                return True
        return False
    
    def find_and_tap_position(self, template_name: str, x: int, y: int, log: str = "", threshold = 0.9) -> bool:
        start_time = time.time()
        # If no template specified, just tap at coordinates
        if not template_name:
            if self.tap(x, y):
                if log:
                    log_info(f"{log} (direct tap at {x}, {y})")
                return True
            return False
        
        # Pre-load template to avoid loading it multiple times
        template = self.load_template(template_name)
        if template is None:
            log_warning(f"Failed to load template {template_name}")
            return False
        
        result = self.find_template(template_name, threshold=threshold)
        if result:
            if self.tap(x, y):
                total_time = time.time() - start_time
                log_success(f"[FIND TAP POSITION] - [{x}, {y}] - [{template_name.replace(self.templates_dir, '').replace('/', '')}] - [confidence: {result[2]:.2f}, total: {total_time:.2f}s]")
                return True
                
        total_time = time.time() - start_time
        return False
    
    def find_and_tap_position_with_offset(self, template_name: str, offset: Tuple[int, int] = (0, 0),  threshold = 0.6,) -> bool:
        start_time = time.time()
        result = self.find_template(template_name, threshold=threshold)
        if result:
            x, y, confidence = result
            if self.tap(x + offset[0], y + offset[1]):
                total_time = time.time() - start_time
                return True
        return False

    def wait_and_tap(self, template_name: str, timeout: float = 30.0, interval: float = 0.5, threshold: float = 0.9, tap_delay: float = 0.1) -> bool:
        result = self.wait_for_template(template_name, timeout, interval, threshold)
        if result:
            x, y, confidence = result
            if self.tap(x, y, tap_delay):
                return True
            else:
                return False
        
        return False

    # Send text gesture
    def send_text(self, text: str) -> bool:
        return self.adb.send_text(text)

    # Press key gesture
    def press_key(self, keycode: int) -> bool:
        return self.adb.press_key(keycode)
    
    # Swipe gesture
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        return self.adb.swipe(x1, y1, x2, y2, duration)
 
    def swipe_up(self,x: int, y: int, duration: int = 300) -> bool:
        width, height = self.get_screen_size()
        return self.swipe(x, y, x, y -200, duration)
        
    def swipe_down(self,x: int, y: int, duration: int = 300) -> bool:
        """Scroll down gesture"""
        width, height = self.get_screen_size()
        return self.swipe(x, y, x, y + 200, duration)

    # Drag gesture
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        return self.adb.drag(x1, y1, x2, y2, duration)
    
    # Common gestures
    def go_back(self) -> bool:
        """Press back button"""
        return self.adb.go_back()
        
    def go_home(self) -> bool:
        """Press home button"""
        return self.adb.go_home()

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

    def get_performance_info(self) -> dict:
        return {
            "capture_interval": self.capture_interval
        }

    def batch_find_templates(self, template_names: list, threshold: float = 0.9) -> dict:
        results = {}
        
        for template_name in template_names:
            result = self.find_template(template_name, threshold=threshold)
            if result:
                results[template_name] = result
        
        return results

    def wait_for_template(self, template_name: str, timeout: float = 30.0, interval: float = 0.5, 
                         threshold: float = 0.9, log_progress: bool = True) -> Optional[Tuple[int, int, float]]:
        start_time = time.time()
        attempts = 0
        
        if log_progress:
            log_info(f"Waiting for template: {template_name} (timeout: {timeout}s, threshold: {threshold})")
        
        # Pre-load template to avoid loading it repeatedly
        template = self.load_template(template_name)
        if template is None:
            log_error(f"Failed to load template for waiting: {template_name}")
            return None
            
        while time.time() - start_time < timeout:
            attempts += 1
            
            # Check for template using continuous capture
            result = self.find_template(template_name, threshold=threshold)
            
            if result:
                elapsed_time = time.time() - start_time
                x, y, confidence = result
                if log_progress:
                    log_info(f"Template found after {elapsed_time:.2f}s ({attempts} attempts): {template_name} at ({x}, {y}) with confidence {confidence:.3f}")
                return result
            
            # Log progress every 5 seconds
            elapsed_time = time.time() - start_time
            if log_progress and elapsed_time > 0 and int(elapsed_time) % 5 == 0 and elapsed_time - int(elapsed_time) < interval:
                log_info(f"Still waiting for {template_name}... ({elapsed_time:.1f}s elapsed)")
            
            # Wait before next attempt
            time.sleep(interval)
        
        # Timeout reached
        elapsed_time = time.time() - start_time
        if log_progress:
            log_warning(f"Timeout waiting for template: {template_name} after {elapsed_time:.2f}s ({attempts} attempts)")
        return None

    def wait_for_any_template(self, template_names: list, timeout: float = 30.0, interval: float = 0.5,
                             threshold: float = 0.9, log_progress: bool = True) -> Optional[Tuple[str, int, int, float]]:
        start_time = time.time()
        attempts = 0
        
        if log_progress:
            log_info(f"Waiting for any of {len(template_names)} templates (timeout: {timeout}s)")
        
        # Pre-load all templates
        templates = {}
        for template_name in template_names:
            template = self.load_template(template_name)
            if template is not None:
                templates[template_name] = template
            else:
                log_warning(f"Failed to load template: {template_name}")
        
        if not templates:
            log_error("No valid templates to wait for")
            return None
            
        while time.time() - start_time < timeout:
            attempts += 1
            
            # Check each template using continuous capture
            for template_name in templates.keys():
                result = self.find_template(template_name, threshold=threshold)
                
                if result:
                    elapsed_time = time.time() - start_time
                    x, y, confidence = result
                    if log_progress:
                        log_info(f"Template found after {elapsed_time:.2f}s ({attempts} attempts): {template_name} at ({x}, {y}) with confidence {confidence:.3f}")
                    return (template_name, x, y, confidence)
            
            # Log progress every 5 seconds
            elapsed_time = time.time() - start_time
            if log_progress and elapsed_time > 0 and int(elapsed_time) % 5 == 0 and elapsed_time - int(elapsed_time) < interval:
                log_info(f"Still waiting for any template... ({elapsed_time:.1f}s elapsed)")
            
            # Wait before next attempt
            time.sleep(interval)
        
        # Timeout reached
        elapsed_time = time.time() - start_time
        if log_progress:
            log_warning(f"Timeout waiting for any template after {elapsed_time:.2f}s ({attempts} attempts)")
        return None

    def check_adb_connection_with_ports(self, start_port=5037, end_port=7556):
        priority_ports = [5037, 5555, 5565, 5575, 5585]  # Common ports for ADB and BlueStacks
        all_ports = list(set(priority_ports + list(range(start_port, end_port + 1))))
        
        for port in all_ports:
            try:
                # Try to create client and connect
                client = AdbClient(host=self.adb.host, port=port)
                try:
                    # Explicitly try to connect if it's a device address
                    if ':' in str(self.adb.device_id):
                        client.connect(self.adb.device_id)
                except Exception as connect_err:
                    log_warning(f"Connection attempt failed on port {port}: {connect_err}")
                    continue

                # Check for devices
                devices = client.devices()
                if not devices:
                    continue

                # Log available devices
                log_info(f"Available devices on port {port}:")
                for device in devices:
                    log_info(f"Device: {device.serial}")

                # Try to find our specific device or use first available
                if self.adb.device_id is None:
                    self.adb.device = devices[0]
                    self.adb.device_id = self.adb.device.serial
                else:
                    self.adb.device = None
                    for d in devices:
                        if d.serial == self.adb.device_id:
                            self.adb.device = d
                            break
                    if not self.adb.device:
                        continue

                # If we got here and have a device, we succeeded
                self.adb.client = client
                self.adb.port = port
                log_success(f"Successfully connected to device {self.adb.device_id} on port {port}")
                return True

            except Exception as e:
                log_warning(f"Failed to connect on port {port}: {e}")
                continue

        # If we get here, we failed to connect on any port
        log_error(f"Failed to connect to any ADB device on ports {start_port}-{end_port}")
        raise Exception("ADB connection failed on all tried ports")
    
    def start(self):
        if not self.adb.device:
            self.adb.check_adb_connection()
            
        if not self.adb.device:
            log_error("Failed to connect to ADB device")
            return
            
        # Get and update screen size
        width, height = self.adb.get_screen_size()
        if width > 0 and height > 0:
            self.monitor["width"] = width
            self.monitor["height"] = height
            
        log_info("Starting ADB automation... Press 'q' to quit")
        self.running = True
        
        self.start_continuous_capture()
        
        last_error_time = 0
        error_cooldown = 5.0
        
        try:
            while self.running:
                try:
                    if keyboard.is_pressed('q'):
                        log_info("Stopping automation...")
                        self.running = False
                        break

                    # Verify device is still connected
                    if not self.adb.device:
                        current_time = time.time()
                        if current_time - last_error_time >= error_cooldown:
                            log_warning("ADB device disconnected, attempting to reconnect...")
                            try:
                                self.adb.check_adb_connection()
                            except Exception as e:
                                log_error(f"Failed to reconnect: {e}")
                            last_error_time = current_time
                        time.sleep(1)
                        continue
                    
                    # Check if process_game_actions is a coroutine
                    if asyncio.iscoroutinefunction(self.process_game_actions):
                        asyncio.run(self.process_game_actions())
                    else:
                        self.process_game_actions()
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.1)
                        
                except Exception as e:
                    current_time = time.time()
                    if current_time - last_error_time >= error_cooldown:
                        log_error(f"Error in ADB automation loop: {e}")
                        last_error_time = current_time
                    time.sleep(0.5)
        finally:
            # Stop continuous capture when exiting
            if self.capture_running:
                self.stop_continuous_capture()
