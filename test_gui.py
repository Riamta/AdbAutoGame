#!/usr/bin/env python3
"""
Test script for PyQt6 GUI system
This script tests the PyQt6 GUI without requiring ADB connection
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pyqt6_import():
    """Test if PyQt6 can be imported successfully"""
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        print("✅ PyQt6 imports successful")
        return True
    except Exception as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False

def test_gui_import():
    """Test if GUI can be imported successfully"""
    try:
        from src.gui.girlwar_gui import GirlwarGUI
        from src.gui.base_gui import BaseGameGUI
        print("✅ GUI imports successful")
        return True
    except Exception as e:
        print(f"❌ GUI import failed: {e}")
        return False

def test_gui_creation():
    """Test if GUI can be created (but not run)"""
    try:
        from src.gui.base_gui import create_app
        from src.gui.girlwar_gui import GirlwarGUI
        
        # Create QApplication
        app = create_app()
        
        # Create GUI instance
        gui = GirlwarGUI()
        print("✅ GUI creation successful")
        
        # Test function mappings
        handle_funcs = gui.get_handle_functions()
        check_funcs = gui.get_check_functions()
        
        print(f"✅ Handle functions: {len(handle_funcs)}")
        for name, display in handle_funcs.items():
            print(f"  - {name}: {display}")
            
        print(f"✅ Check functions: {len(check_funcs)}")
        for name, display in check_funcs.items():
            print(f"  - {name}: {display}")
            
        # Test logging
        gui.log_message("Test message", "INFO")
        gui.log_message("Test success", "SUCCESS") 
        gui.log_message("Test warning", "WARNING")
        gui.log_message("Test error", "ERROR")
        print("✅ Logging system working")
        
        # Clean up (don't show window or start event loop)
        gui.close()
        return True
        
    except Exception as e:
        print(f"❌ GUI creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    deps = {
        'PyQt6': 'PyQt6',
        'OpenCV': 'cv2', 
        'NumPy': 'numpy',
        'Pure Python ADB': 'ppadb'
    }
    
    success = True
    for name, module in deps.items():
        try:
            __import__(module)
            print(f"✅ {name} available")
        except ImportError:
            print(f"❌ {name} missing (pip install {module})")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("🧪 Testing Girl War GUI System")
    print("=" * 40)
    
    success = True
    
    print("1. Testing dependencies...")
    success &= test_dependencies()
    
    print("\n2. Testing PyQt6 imports...")
    success &= test_pyqt6_import()
    
    print("\n3. Testing GUI imports...")
    success &= test_gui_import()
    
    print("\n4. Testing GUI creation...")
    success &= test_gui_creation()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! GUI is ready to use.")
        print("\n🚀 To run the GUI:")
        print("python run_girlwar_gui.py")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n📦 Install missing dependencies:")
        print("pip install PyQt6 opencv-python numpy pure-python-adb")
        sys.exit(1)

if __name__ == "__main__":
    main() 