#!/usr/bin/env python3
"""
Girl War GUI Launcher
Launch the modern PyQt6 interface for Girl War automation
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n📦 Install them with:")
        print("pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🌸 Starting Girl War GUI...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Import and run the PyQt6 GUI
        from src.gui.girlwar_gui import main as gui_main
        
        print("✅ Dependencies loaded successfully")
        print("🚀 Launching GUI...")
        
        # Run the GUI
        gui_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n📋 Troubleshooting:")
        print("1. Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("2. Check if PyQt6 is properly installed:")
        print("   python -c \"import PyQt6; print('PyQt6 OK')\"")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 