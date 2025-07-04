from ppadb.client import Client as AdbClient
from typing import Optional, List, Tuple
import time
import os
import subprocess
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import log_error, log_info, log_success, log_warning, log

# Key codes for ADB input
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_MENU = 82
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_POWER = 26
KEYCODE_ENTER = 66
# Generate host range from 16000 to 17000
HOSTS_MUMU = [f"127.0.0.1:{port}" for port in range(16000, 17001)]

def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quickly check if a port is open"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def _setup_adb_path():
    try:
        # Get the absolute path to the binaries directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        adb_path = os.path.join(root_dir, 'src', 'binaries', 'adb.exe')
        
        if os.path.exists(adb_path):
            os.environ['ADBUTILS_ADB_PATH'] = adb_path
            log(f"Using ADB from: {adb_path}")
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

    # Check ADB connection
    def check_adb_connection(self) -> bool:
        try:
            log("Checking ADB connection...")
            devices = self.client.devices()
            log(f"Devices: {devices}")
            if devices:
                # Log all available devices and their ports
                log("Available devices:")
                for device in devices:
                    log(f"Device: {device.serial}")
                    
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
                                    log_success(f"Connected to device: {self.device_id}")
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
                        log_success(f"Connected to device: {self.device_id}")
                        return True
                else:
                    # Find specified device
                    for device in devices:
                        if device.serial == self.device_id:
                            self.device = device
                            log_success(f"Connected to device: {self.device_id}")
                            return True
            log_warning("Can't find device, trying to connect with ports")            
            if self.check_adb_connection_with_ports():
                return True
            
            return False
                    
        except Exception as e:
            log_error(f"Error checking ADB connection: {e}")
            # Try port scanning as fallback
            if self.check_adb_connection_with_ports():
                return True
            raise

    def _try_connect_to_host(self, host: str, adb_exe_path: str) -> Optional[str]:
        """Try to connect to a single host and return device serial if successful"""
        try:
            # First, quickly check if port is open
            host_ip, port_str = host.split(':')
            port = int(port_str)
            log("Try connect to host: " + host)
            if not _is_port_open(host_ip, port, timeout=0.5):
                return None
            # Try ADB connect with shorter timeout
            result = subprocess.run(
                [adb_exe_path, "connect", host],
                capture_output=True,
                text=True,
                timeout=3  # Reduced from 10 to 3 seconds
            )
            # Check if devices are available
            client = AdbClient(host=self.host, port=self.port)
            devices = client.devices()
            
            if devices:
                # Return first matching device
                for device in devices:
                    if device.serial == host or (self.device_id and device.serial == self.device_id):
                        return device.serial
                # If no specific match, return first device
                return devices[0].serial
                        
        except Exception as e:
            log_error(f"Lỗi khi thử kết nối với {host}: {e}")
        return None

    def check_adb_connection_with_ports(self) -> bool:
        # Lấy đường dẫn tới file thực thi ADB
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        adb_exe_path = os.path.join(root_dir, 'src', 'binaries', 'adb.exe')
        # Kiểm tra file ADB có tồn tại không
        if not os.path.exists(adb_exe_path):
            log_error(f"Không tìm thấy file ADB tại: {adb_exe_path}")
            return False
        try:
            log_info(f"Scanning {len(HOSTS_MUMU)} ports with parallel threading...")
            
            found_devices = []  # Store all found devices
            
            # Use ThreadPoolExecutor for parallel scanning
            with ThreadPoolExecutor(max_workers=30) as executor:  # Limit concurrent connections
                # Submit all tasks
                future_to_host = {
                    executor.submit(self._try_connect_to_host, host, adb_exe_path): host 
                    for host in HOSTS_MUMU
                }
                # Process results as they complete - but don't stop early
                for future in as_completed(future_to_host):
                    host = future_to_host[future]
                    try:
                        device_serial = future.result()
                        if device_serial:
                            log_success(f"Found device {device_serial} on {host}")
                            found_devices.append((device_serial, host))
                    except Exception as e:
                        log_error(f"Error processing result for {host}: {e}")
            
            # After scanning all ports, connect to the first found device
            if found_devices:
                device_serial, host = found_devices[0]  # Use first found device
                log_info(f"Total devices found: {len(found_devices)}")
                for serial, host_addr in found_devices:
                    log_info(f"  - Device {serial} on {host_addr}")
                
                # Set up connection to the first device
                client = AdbClient(host=self.host, port=self.port)
                devices = client.devices()
                for device in devices:
                    if device.serial == device_serial:
                        self.client = client
                        self.device = device
                        self.device_id = device.serial
                        log_success(f"Successfully connected to device: {self.device_id}")
                        return True
                        
            log_warning("No devices found on any port")
            return False
            
        except Exception as e:
            log_error(f"Lỗi khi thử kết nối: {e}")
            return False

    # Get screen size
    def get_screen_size(self) -> Tuple[int, int]:
        try:
            result = self.device.shell("wm size")
            size = result.strip().split()[-1].split('x')
            return int(size[0]), int(size[1])
        except Exception as e:
            log_error(f"Error getting screen size: {e}")
            return (0, 0)

    def tap(self, x: int, y: int, duration: float = 0.1, tap_count: int = 1) -> bool:
        try:
            for i in range(tap_count):
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

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        try:
            self.device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            return True
        except Exception as e:
            log_error(f"Error dragging: {e}")
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
        try:
            return self.device.screencap()
        except Exception as e:
            log_error(f"Error capturing screen: {e}")
            return None