from ppadb.client import Client as AdbClient
from typing import Optional, List, Tuple
import time
import os
from utils import log_error, log_info, log_success, log_warning

# Key codes for ADB input
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_MENU = 82
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_POWER = 26
KEYCODE_ENTER = 66

def _setup_adb_path():
    """Set up ADB path from binaries directory"""
    try:
        # Get the absolute path to the binaries directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        adb_path = os.path.join(root_dir, 'src', 'binaries', 'adb.exe')
        
        if os.path.exists(adb_path):
            os.environ['ADBUTILS_ADB_PATH'] = adb_path
            log_info(f"Using ADB from: {adb_path}")
        else:
            log_error(f"ADB not found at: {adb_path}")
    except Exception as e:
        log_error(f"Error setting up ADB path: {e}")

class ADBController:
    def __init__(self, device_id: str = None, host: str = "127.0.0.1", port: int = 5037):
        _setup_adb_path()  # Set up ADB path before initializing
        self.host = host
        self.port = port
        self.device_id = device_id
        self.client = AdbClient(host=host, port=port)
        self.device = None
        self.check_adb_connection()

    def check_adb_connection(self) -> bool:
        try:
            log_info("Checking ADB connection...")
            devices = self.client.devices()
            log_info(f"Devices: {devices}")
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
            return False
        except Exception as e:
            log_error(f"Error checking ADB connection: {e}")
            raise

    def check_adb_connection_with_ports(self, start_port=5037, end_port=7556) -> bool:
        # Common ports for various emulators
        priority_ports = [
            5037,   # Default ADB
            5555,   # Common Android Debug Bridge
            5565, 5575, 5585,  # BlueStacks
            7555,   # MuMu Player
            16384,  # NoxPlayer
            21503,  # MuMu Player (alternative)
            62001   # LDPlayer
        ]
        
        # Add extended range ports
        extended_ports = (
            list(range(5037, 5100)) +  # ADB and BlueStacks range
            list(range(7555, 7565)) +  # MuMu Player range
            list(range(16380, 16390)) +  # NoxPlayer range
            list(range(21500, 21510)) +  # MuMu Player alternative range
            list(range(62000, 62010))    # LDPlayer range
        )
        
        # Combine and deduplicate ports
        all_ports = list(set(priority_ports + extended_ports))
        log_info(f"Scanning ports: {all_ports}")
        
        # Try priority ports first, then others
        for port in all_ports:
            try:
                log_info(f"Attempting connection on port {port}...")
                client = AdbClient(host=self.host, port=port)
                
                # Try to explicitly connect if it's a device address
                if ':' in str(self.device_id):
                    try:
                        log_info(f"Attempting to connect to device {self.device_id} on port {port}")
                        client.connect(self.device_id)
                    except Exception as connect_err:
                        log_warning(f"Failed to connect to device {self.device_id} on port {port}: {connect_err}")
                        continue
                
                devices = client.devices()
                log_info(f"Found devices on port {port}: {devices}")
                
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
            except Exception as e:
                if "actively refused" in str(e):
                    log_warning(f"Port {port} is not accepting connections. Is the emulator's ADB enabled?")
                elif "No such file or directory" in str(e):
                    log_warning(f"ADB server not running. Try running 'adb start-server'")
                else:
                    log_warning(f"Failed to connect on port {port}: {e}")
                continue
        
        log_error("Failed to connect to any ADB devices. Please check:")
        log_error("1. Is your emulator running?")
        log_error("2. Is ADB enabled in your emulator settings?")
        log_error("3. Try running 'adb kill-server && adb start-server'")
        return False

    def get_screen_size(self) -> Tuple[int, int]:
        try:
            result = self.device.shell("wm size")
            size = result.strip().split()[-1].split('x')
            return int(size[0]), int(size[1])
        except Exception as e:
            log_error(f"Error getting screen size: {e}")
            return (0, 0)

    def tap(self, x: int, y: int, duration: float = 0.1) -> bool:
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