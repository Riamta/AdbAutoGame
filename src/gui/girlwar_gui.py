import sys
import os
from typing import Dict, Optional, Any
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.gui.base_gui import BaseGameGUI, create_app
from src.games.girlwars.girlwar import TestADBGameAutomation

class GirlwarGUI(BaseGameGUI):
    def __init__(self):
        super().__init__(title="🌸 Girl Wa", width=1100, height=750)
        
        # Set window icon if available
        try:
            # You can add an icon file here if you have one
            # self.setWindowIcon(QIcon("assets/icon.png"))
            pass
        except:
            pass
            
    def get_game_title(self) -> str:
        return "🌸 Girl War"
        
    def get_handle_functions(self) -> Dict[str, str]:
        return {
            "handle_main_story": "📖 Main Story Mode",
            "handle_atlantis": "🌊 Atlantis Mode", 
            "handle_dock": "⚓ Dock Mode",
            "handle_global_rich": "💰 Global Rich Mode",
            "handle_battle": "⚔️ Battle Mode",
            "handle_elite_stage": "👑 Elite Stage Mode",
            "handle_dungeon_stage": "🏰 Dungeon Stage Mode"
        }
        
    def get_check_functions(self) -> Dict[str, str]:
        return {
            "check_skip_dialog": "💬 Auto Skip Dialog",
            "check_end_battle": "🏁 Auto Handle End Battle"
        }
        
    def create_game_automation(self, device_id: Optional[str], host: str, port: int) -> Any:
        try:
            automation = TestADBGameAutomation()
            # Set connection parameters
            automation.adb.device_id = device_id
            automation.adb.host = host 
            automation.adb.port = port
            
            # Try to connect
            automation.adb.check_adb_connection()
            
            return automation
        except Exception as e:
            self.log_message(f"Failed to create automation: {e}", "ERROR")
            return None
            
    def init_function_mappings(self):
        """Initialize any additional function mappings"""
        # Add custom initialization if needed
        pass
        
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


def main():
    """Main function to run the Girlwar GUI"""
    try:
        app = create_app()
        
        # Set application properties
        app.setApplicationName("Girl War AFK Journey")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Game Automation")
        
        # Apply dark theme to the entire application
        app.setStyle('Fusion')  # Use Fusion style for better dark theme support
        
        # Create and show the main window
        window = GirlwarGUI()
        window.show()
        
        # Log initial messages
        window.log_message("🌸 Girl War GUI started successfully", "SUCCESS")
        window.log_message("📋 Configure your device settings and select automation modes", "INFO")
        window.log_message("🔍 Press 'Test Connection' to verify ADB connection", "INFO")
        window.log_message("💡 Tip: Enable check functions for automatic utilities", "INFO")
        window.log_message("🎮 Select a game mode and click 'Start Automation'", "INFO")
        
        # Start the application event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure PyQt6 is installed:")
        print("pip install PyQt6")
        sys.exit(1)
        
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 