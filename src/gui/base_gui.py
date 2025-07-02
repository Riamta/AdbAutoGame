import sys
import time
import threading
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QRadioButton, QCheckBox, QButtonGroup, QSplitter, QFrame,
    QScrollArea, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QIcon

# Create compatible metaclass for PyQt6 and ABC
class QtABCMeta(type(QMainWindow), type(ABC)):
    pass

class BaseGameGUI(QMainWindow, ABC, metaclass=QtABCMeta):
    # Signals for thread communication
    log_signal = pyqtSignal(str, str)  # message, level
    
    def __init__(self, title: str = "Game Automation", width: int = 1000, height: int = 700):
        super().__init__()
        
        # Game automation instance
        self.game_automation = None
        self.automation_thread = None
        self.is_running = False
        
        # GUI state variables
        self.check_functions = {}  # Checkboxes for check functions
        self.handle_button_group = QButtonGroup()  # Radio button group for handle functions
        self.selected_handle = "none"  # Only one handle function active
        
        # Setup window
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        
        # Setup UI
        self.init_ui()
        self.setup_styles()
        self.connect_signals()
        
        # Initialize function mappings
        self.init_function_mappings()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        self.title_label = QLabel(self.get_game_title())
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (controls)
        self.left_panel = self.create_left_panel()
        splitter.addWidget(self.left_panel)
        
        # Right panel (logs)
        self.right_panel = self.create_right_panel()
        splitter.addWidget(self.right_panel)
        
        # Set splitter sizes (60% left, 40% right)
        splitter.setSizes([600, 400])
        
    def create_left_panel(self) -> QWidget:
        """Create the left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Device settings section
        device_group = self.create_device_section()
        layout.addWidget(device_group)
        
        # Handle functions section (Game Modes)
        handle_group = self.create_handle_functions_section()
        layout.addWidget(handle_group)
        
        # Check functions section (Events & Other)
        check_group = self.create_check_functions_section()
        layout.addWidget(check_group)
        
        # Control section
        control_group = self.create_control_section()
        layout.addWidget(control_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right log panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Log section
        log_group = self.create_log_section()
        layout.addWidget(log_group)
        
        return panel
        
    def create_device_section(self) -> QGroupBox:
        """Create device connection section"""
        group = QGroupBox("🔧 Device Settings")
        group.setObjectName("deviceGroup")
        layout = QVBoxLayout(group)
        
        # Device ID
        device_layout = QVBoxLayout()
        device_label = QLabel("Device ID:")
        self.device_id_input = QLineEdit()
        self.device_id_input.setPlaceholderText("Leave empty for auto-detect")
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_id_input)
        
        # Host and Port
        host_port_layout = QHBoxLayout()
        
        host_label = QLabel("Host:")
        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setFixedWidth(120)
        
        port_label = QLabel("Port:")
        self.port_input = QLineEdit("5037")
        self.port_input.setFixedWidth(80)
        
        host_port_layout.addWidget(host_label)
        host_port_layout.addWidget(self.host_input)
        host_port_layout.addWidget(port_label)
        host_port_layout.addWidget(self.port_input)
        host_port_layout.addStretch()
        
        # Test connection button
        self.test_btn = QPushButton("🔍 Test Connection")
        self.test_btn.setObjectName("testButton")
        self.test_btn.clicked.connect(self.test_connection)
        
        layout.addLayout(device_layout)
        layout.addLayout(host_port_layout)
        layout.addWidget(self.test_btn)
        
        return group
        
    def create_handle_functions_section(self) -> QGroupBox:
        """Create section for handle functions (radio buttons)"""
        group = QGroupBox("🎮 Game Modes (Select One)")
        group.setObjectName("gameModeGroup")
        layout = QVBoxLayout(group)
        
        # None option
        none_radio = QRadioButton("None (Manual Control)")
        none_radio.setChecked(True)
        none_radio.setObjectName("noneRadio")
        self.handle_button_group.addButton(none_radio, 0)
        layout.addWidget(none_radio)
        
        # Get handle functions from child class
        handle_functions = self.get_handle_functions()
        for i, (func_name, func_display) in enumerate(handle_functions.items(), 1):
            radio = QRadioButton(func_display)
            radio.setObjectName("handleRadio")
            radio.func_name = func_name  # Store function name
            self.handle_button_group.addButton(radio, i)
            layout.addWidget(radio)
            
        # Connect signal
        self.handle_button_group.buttonClicked.connect(self.on_handle_function_changed)
        
        return group
        
    def create_check_functions_section(self) -> QGroupBox:
        """Create section for check functions (checkboxes)"""
        group = QGroupBox("⚡ Events & Other (Select Multiple)")
        group.setObjectName("eventsGroup")
        layout = QVBoxLayout(group)
        
        # Get check functions from child class
        check_functions = self.get_check_functions()
        for func_name, func_display in check_functions.items():
            checkbox = QCheckBox(func_display)
            checkbox.setChecked(True)  # Default enabled
            checkbox.setObjectName("checkFunction")
            checkbox.func_name = func_name  # Store function name
            self.check_functions[func_name] = checkbox
            layout.addWidget(checkbox)
            
        return group
        
    def create_control_section(self) -> QGroupBox:
        """Create automation control section"""
        group = QGroupBox("🎯 Control")
        group.setObjectName("controlGroup")
        layout = QVBoxLayout(group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start Automation")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_automation)
        
        self.stop_btn = QPushButton("⏹️ Stop Automation")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_automation)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        
        return group
        
    def create_log_section(self) -> QGroupBox:
        """Create log display section"""
        group = QGroupBox("🔥 System Logs")
        group.setObjectName("logGroup")
        layout = QVBoxLayout(group)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_logs)
        
        self.auto_scroll_cb = QCheckBox("Auto Scroll")
        self.auto_scroll_cb.setChecked(True)
        
        log_controls.addWidget(clear_btn)
        log_controls.addStretch()
        log_controls.addWidget(self.auto_scroll_cb)
        
        layout.addLayout(log_controls)
        
        return group
        
    def setup_styles(self):
        """Setup clean dark theme styles"""
        style = """
        QMainWindow {
            background-color: #2b2b2b;
        }
        
        #titleLabel {
            color: #ffffff;
            padding: 15px;
            background: transparent;
            font-size: 18px;
            font-weight: bold;
        }
        
        QGroupBox {
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #3b3b3b;
            font-size: 12px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: #87ceeb;
            background: transparent;
            font-size: 12px;
            font-weight: bold;
        }
        
        QLabel {
            color: #ffffff;
            background: transparent;
            font-size: 11px;
        }
        
        QLineEdit {
            background-color: #404040;
            border: 1px solid #666666;
            border-radius: 4px;
            padding: 8px;
            color: #ffffff;
            font-size: 11px;
        }
        
        QLineEdit:focus {
            border-color: #87ceeb;
        }
        
        QPushButton {
            background-color: #505050;
            border: 1px solid #666666;
            border-radius: 4px;
            color: #ffffff;
            padding: 10px 18px;
            min-height: 24px;
            font-size: 11px;
        }
        
        QPushButton:hover {
            background-color: #606060;
            border-color: #87ceeb;
        }
        
        QPushButton:pressed {
            background-color: #404040;
        }
        
        #startButton {
            background-color: #228b22;
            border-color: #32cd32;
        }
        
        #startButton:hover {
            background-color: #32cd32;
        }
        
        #startButton:pressed {
            background-color: #1e6b1e;
        }
        
        #stopButton {
            background-color: #dc143c;
            border-color: #ff6347;
        }
        
        #stopButton:hover {
            background-color: #ff6347;
        }
        
        #stopButton:pressed {
            background-color: #b22222;
        }
        
        QPushButton:disabled {
            background-color: #2d2d2d;
            border-color: #444444;
            color: #888888;
        }
        
        QRadioButton, QCheckBox {
            color: #ffffff;
            spacing: 8px;
            font-size: 11px;
        }
        
        QRadioButton::indicator, QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QRadioButton::indicator::unchecked {
            border: 1px solid #666666;
            border-radius: 8px;
            background-color: #404040;
        }
        
        QRadioButton::indicator::checked {
            border: 1px solid #87ceeb;
            border-radius: 8px;
            background-color: #87ceeb;
        }
        
        QCheckBox::indicator::unchecked {
            border: 1px solid #666666;
            border-radius: 2px;
            background-color: #404040;
        }
        
        QCheckBox::indicator::checked {
            border: 1px solid #87ceeb;
            border-radius: 2px;
            background-color: #87ceeb;
        }
        
        #logText {
            background-color: #1e1e1e;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
            selection-background-color: #87ceeb;
            selection-color: #000000;
            font-size: 10px;
        }
        
        #statusLabel {
            color: #87ceeb;
            padding: 6px;
            background-color: rgba(135, 206, 235, 0.1);
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #666666;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #87ceeb;
        }
        """
        
        self.setStyleSheet(style)
        
    def connect_signals(self):
        """Connect signals for thread communication"""
        self.log_signal.connect(self.append_log)
        
    def on_handle_function_changed(self, button):
        """Handle radio button selection change"""
        if hasattr(button, 'func_name'):
            self.selected_handle = button.func_name
        else:
            self.selected_handle = "none"
            
    @pyqtSlot(str, str)
    def append_log(self, message: str, level: str):
        """Append log message to the display"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Format message with emojis
        level_emojis = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        
        emoji = level_emojis.get(level, "📝")
        formatted_message = f"[{timestamp}] {emoji} {message}"
        
        # Color formatting
        if level == "ERROR":
            color_message = f'<span style="color: #ff6347; font-weight: bold;">{formatted_message}</span>'
        elif level == "SUCCESS":
            color_message = f'<span style="color: #32cd32; font-weight: bold;">{formatted_message}</span>'
        elif level == "WARNING":
            color_message = f'<span style="color: #ffa500; font-weight: bold;">{formatted_message}</span>'
        else:
            color_message = f'<span style="color: #87ceeb;">{formatted_message}</span>'
        
        self.log_text.append(color_message)
        
        # Auto scroll if enabled
        if self.auto_scroll_cb.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log display (thread-safe)"""
        self.log_signal.emit(message, level)
        
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.clear()
        
    def test_connection(self):
        """Test ADB connection"""
        try:
            device_id = self.device_id_input.text() or None
            host = self.host_input.text()
            port = int(self.port_input.text())
            
            self.log_message(f"Testing connection to {host}:{port} (device: {device_id or 'auto'})")
            
            # Create temporary game automation instance for testing
            temp_automation = self.create_game_automation(device_id, host, port)
            
            if temp_automation and temp_automation.adb.device:
                self.log_message("Connection successful!", "SUCCESS")
                QMessageBox.information(self, "Success", "ADB connection successful!")
            else:
                self.log_message("Connection failed!", "ERROR")
                QMessageBox.critical(self, "Error", "Failed to connect to ADB device")
                
        except Exception as e:
            self.log_message(f"Connection error: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Connection error: {e}")
            
    def start_automation(self):
        """Start the automation"""
        if self.is_running:
            return
            
        try:
            # Get connection parameters
            device_id = self.device_id_input.text() or None
            host = self.host_input.text()
            port = int(self.port_input.text())
            
            # Create game automation instance
            self.game_automation = self.create_game_automation(device_id, host, port)
            
            if not self.game_automation or not self.game_automation.adb.device:
                QMessageBox.critical(self, "Error", "Failed to connect to ADB device")
                return
            
            # Setup custom process_game_actions method
            self.setup_custom_automation()
            
            # Start automation in separate thread
            self.is_running = True
            self.automation_thread = AutomationThread(self.game_automation)
            self.automation_thread.start()
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Running...")
            self.status_label.setStyleSheet("color: #32cd32; background-color: rgba(50, 205, 50, 0.2);")
            
            self.log_message("Automation started", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Failed to start automation: {e}", "ERROR")
            QMessageBox.critical(self, "Error", f"Failed to start automation: {e}")
            
    def stop_automation(self):
        """Stop the automation"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.game_automation:
            self.game_automation.running = False
            
        if self.automation_thread:
            self.automation_thread.terminate()
            
        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: #ff6347; background-color: rgba(255, 99, 71, 0.2);")
        
        self.log_message("Automation stopped", "WARNING")
        
    def setup_custom_automation(self):
        """Setup custom process_game_actions method based on selected functions"""
        def custom_process_game_actions():
            if not self.is_running:
                return
                
            try:
                current_screen = self.game_automation.capture_screen()
                if current_screen is None:
                    return
                    
                # Execute enabled check functions first (these are utilities)
                for func_name, checkbox in self.check_functions.items():
                    if checkbox.isChecked():
                        try:
                            method = getattr(self.game_automation, func_name)
                            method(current_screen)
                        except Exception as e:
                            self.log_message(f"Error in {func_name}: {e}", "ERROR")
                
                # Execute selected handle function (main game mode)
                if self.selected_handle != "none":
                    try:
                        method = getattr(self.game_automation, self.selected_handle)
                        method(current_screen)
                    except Exception as e:
                        self.log_message(f"Error in {self.selected_handle}: {e}", "ERROR")
                        
            except Exception as e:
                self.log_message(f"Error in automation loop: {e}", "ERROR")
                     
        # Replace the original method
        self.game_automation.process_game_actions = custom_process_game_actions
        
        # Override the logging to show in GUI
        self.setup_logging_redirect()
        
    def setup_logging_redirect(self):
        """Redirect game automation logging to GUI"""
        try:
            import src.utils.logging as logging_module
            
            # Create wrapper functions that also log to GUI
            def gui_log_info(message):
                self.log_message(message, "INFO")
                
            def gui_log_error(message, exc_info=False):
                self.log_message(message, "ERROR")
                
            def gui_log_success(message):
                self.log_message(message, "SUCCESS")
                
            def gui_log_warning(message):
                self.log_message(message, "WARNING")
                
            # Replace logging functions
            logging_module.log_info = gui_log_info
            logging_module.log_error = gui_log_error  
            logging_module.log_success = gui_log_success
            logging_module.log_warning = gui_log_warning
                 
        except ImportError as e:
            self.log_message(f"Could not setup logging redirect: {e}", "WARNING")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_running:
            self.stop_automation()
        event.accept()
        
    # Abstract methods to be implemented by child classes
    @abstractmethod
    def get_game_title(self) -> str:
        """Return the game title for the GUI"""
        pass
        
    @abstractmethod
    def get_handle_functions(self) -> Dict[str, str]:
        """Return dictionary of handle function names and their display names"""
        pass
        
    @abstractmethod
    def get_check_functions(self) -> Dict[str, str]:
        """Return dictionary of check function names and their display names"""
        pass
        
    @abstractmethod
    def create_game_automation(self, device_id: Optional[str], host: str, port: int) -> Any:
        """Create and return game automation instance"""
        pass
        
    @abstractmethod
    def init_function_mappings(self):
        """Initialize any additional function mappings"""
        pass


class AutomationThread(QThread):
    """Thread for running automation"""
    
    def __init__(self, automation):
        super().__init__()
        self.automation = automation
        
    def run(self):
        """Run the automation"""
        try:
            self.automation.start()
        except Exception as e:
            print(f"Automation thread error: {e}")


def create_app():
    """Create QApplication if it doesn't exist"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app 