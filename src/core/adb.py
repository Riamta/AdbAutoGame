from ppadb.client import Client as AdbClient
from typing import Optional, List, Tuple
import time
from utils import log_error, log_info, log_success, log_warning

# Key codes for ADB input
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_MENU = 82
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_POWER = 26
KEYCODE_ENTER = 66

class ADBController:
    def __init__(self, device_id: str = None, host: str = "127.0.0.1", port: int = 5037):
        self.host = host
        self.port = port
        self.device_id = device_id
        self.client = AdbClient(host=host, port=port)
        self.device = None
        self.check_adb_connection()

    def check_adb_connection(self) -> bool:
        try:
            devices = self.client.devices()
            if devices:
                # Log all available devices and their ports
                log_info("Available devices:")
                for device in devices:
                    log_info(f"Device: {device.serial}")
                    
                if self.device_id is None:
                    # If multiple devices, let user choose
                    if len(devices) > 1:
                        print("\nMultiple devices found:")
                        for i, device in enumerate(devices):
                            print(f"{i + 1}. {device.serial}")
                        
                        while True:
                            try:
                                choice = input(f"\nSelect device (1-{len(devices)}): ").strip()
                                device_index = int(choice) - 1
                                if 0 <= device_index < len(devices):
                                    self.device = devices[device_index]
                                    self.device_id = self.device.serial
                                    log_info(f"Connected to device: {self.device_id}")
                                    return True
                                else:
                                    print(f"Invalid choice. Please enter a number between 1 and {len(devices)}")
                            except ValueError:
                                print("Invalid input. Please enter a number.")
                            except KeyboardInterrupt:
                                log_error("User cancelled device selection")
                                raise Exception("Device selection cancelled")
                    else:
                        # Use first device if only one available
                        self.device = devices[0]
                        self.device_id = self.device.serial
                        log_info(f"Connected to device: {self.device_id}")
                        return True
                else:
                    # Find specified device
                    for device in devices:
                        if device.serial == self.device_id:
                            self.device = device
                            log_info(f"Connected to device: {self.device_id}")
                            return True
                            
            # If we get here, either no devices found or specified device not found
            # Try connection with port scanning
            if self.check_adb_connection_with_ports():
                return True
            
            return False
                    
        except Exception as e:
            log_error(f"Error checking ADB connection: {e}")
            # Try port scanning as fallback
            if self.check_adb_connection_with_ports():
                return True
            raise

    def check_adb_connection_with_ports(self, start_port=5037, end_port=7556) -> bool:
        """Try to connect to ADB server on different ports."""
        for port in range(start_port, end_port + 1):
            try:
                client = AdbClient(host=self.host, port=port)
                devices = client.devices()
                if devices:
                    self.client = client
                    self.port = port
                    if self.device_id:
                        for device in devices:
                            if device.serial == self.device_id:
                                self.device = device
                                log_success(f"Connected to device {self.device_id} on port {port}")
                                return True
                    else:
                        self.device = devices[0]
                        self.device_id = self.device.serial
                        log_success(f"Connected to device {self.device_id} on port {port}")
                        return True
            except:
                continue
        return False

    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen size of the connected device."""
        try:
            result = self.device.shell("wm size")
            size = result.strip().split()[-1].split('x')
            return int(size[0]), int(size[1])
        except Exception as e:
            log_error(f"Error getting screen size: {e}")
            return (0, 0)

    def tap(self, x: int, y: int, duration: float = 0.1) -> bool:
        """Tap at the specified coordinates."""
        try:
            self.device.shell(f"input touchscreen tap {x} {y}")
            time.sleep(duration)
            return True
        except Exception as e:
            log_error(f"Error tapping at ({x}, {y}): {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """Swipe from one point to another."""
        try:
            self.device.shell(f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")
            return True
        except Exception as e:
            log_error(f"Error swiping: {e}")
            return False

    def send_text(self, text: str) -> bool:
        """Send text input to the device."""
        try:
            self.device.shell(f"input text '{text}'")
            return True
        except Exception as e:
            log_error(f"Error sending text: {e}")
            return False

    def press_key(self, keycode: int) -> bool:
        """Press a key using its keycode."""
        try:
            self.device.shell(f"input keyevent {keycode}")
            return True
        except Exception as e:
            log_error(f"Error pressing key {keycode}: {e}")
            return False

    def go_back(self) -> bool:
        """Press the back button."""
        return self.press_key(KEYCODE_BACK)

    def go_home(self) -> bool:
        """Press the home button."""
        return self.press_key(KEYCODE_HOME)

    def capture_screen_raw(self) -> Optional[bytes]:
        """Capture the screen and return raw bytes."""
        try:
            return self.device.screencap()
        except Exception as e:
            log_error(f"Error capturing screen: {e}")
            return None

    def optimize_adb_connection(self):
        """Optimize ADB connection settings."""
        try:
            # Set higher USB buffer size
            self.device.shell("setprop sys.usb.ffs.max_write 524288")
            self.device.shell("setprop sys.usb.ffs.max_read 524288")
            # Disable animations for better performance
            self.device.shell("settings put global window_animation_scale 0.0")
            self.device.shell("settings put global transition_animation_scale 0.0")
            self.device.shell("settings put global animator_duration_scale 0.0")
        except Exception as e:
            log_error(f"Error optimizing ADB connection: {e}") 