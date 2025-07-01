#!/usr/bin/env python3
"""
Test script để kiểm tra kết nối ADB với adb_auto.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.adb_auto import ADBGameAutomation
from src.utils.logging import log_info, log_error

def test_adb_connection():
    """Test kết nối ADB"""
    print("🧪 Testing ADB connection với adb_auto.py...")
    print("=" * 60)
    
    try:
        # Tạo instance của ADBGameAutomation mà không cần config file
        print("📱 Đang khởi tạo ADB automation...")
        automation = ADBGameAutomation(config_file=None)
        
        print(f"✅ Kết nối thành công!")
        print(f"   📍 Host: {automation.host}")
        print(f"   🔌 Port: {automation.port}")
        print(f"   📱 Device ID: {automation.device_id}")
        
        # Test lấy kích thước màn hình
        print("\n📏 Đang lấy kích thước màn hình...")
        width, height = automation.get_screen_size()
        print(f"   📐 Kích thước: {width} x {height}")
        
        # Test capture screen
        print("\n📸 Đang thử capture màn hình...")
        screen = automation.capture_screen()
        if screen is not None:
            print(f"   ✅ Capture thành công! Kích thước ảnh: {screen.shape}")
        else:
            print("   ❌ Capture thất bại!")
            
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối ADB: {e}")
        print("\n💡 Gợi ý:")
        print("   1. Chạy 'python scan_adb_servers.py' để kiểm tra ADB servers")
        print("   2. Đảm bảo emulator đang chạy")
        print("   3. Kiểm tra port 16384 có mở không")
        return False

if __name__ == "__main__":
    print("🚀 ADB CONNECTION TESTER")
    print("=" * 60)
    
    success = test_adb_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST THÀNH CÔNG! ADB automation sẵn sàng sử dụng.")
    else:
        print("❌ TEST THẤT BẠI! Cần kiểm tra kết nối ADB.")
    print("=" * 60) 