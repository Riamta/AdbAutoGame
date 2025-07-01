import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ppadb.client import Client as AdbClient

def check_port(host, port, timeout=2):
    """Kiểm tra xem port có đang mở không"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_adb_info(host, port):
    """Lấy thông tin ADB từ host:port"""
    try:
        client = AdbClient(host=host, port=port)
        devices = client.devices()
        return {
            'host': host,
            'port': port,
            'status': 'connected',
            'devices': devices,
            'device_count': len(devices)
        }
    except Exception as e:
        return {
            'host': host,
            'port': port,
            'status': 'error',
            'error': str(e),
            'devices': [],
            'device_count': 0
        }

def scan_adb_servers():
    """Quét tất cả ADB server đang chạy"""
    print("🔍 Đang quét ADB servers...")
    print("=" * 60)
    
    # Danh sách host để kiểm tra
    hosts = [
        "127.0.0.1",      # localhost
        "10.0.2.15",      # emulator IP
        "192.168.1.1",    # router IP thường gặp
        "192.168.0.1",    # router IP khác
    ]
    
    # Danh sách port thường gặp
    common_ports = [5037, 5555, 5565, 5575, 5585, 16384, 21503, 62001]
    
    # Mở rộng range port để quét
    extended_ports = list(range(5037, 5100)) + list(range(16380, 16390)) + list(range(21500, 21510)) + list(range(62000, 62010))
    all_ports = list(set(common_ports + extended_ports))
    
    active_servers = []
    
    # Quét port song song để nhanh hơn
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Tạo tasks cho tất cả host:port combinations
        tasks = []
        for host in hosts:
            for port in all_ports:
                future = executor.submit(check_port, host, port, 1)
                tasks.append((future, host, port))
        
        # Kiểm tra kết quả
        for future, host, port in tasks:
            try:
                if future.result():
                    print(f"✅ Tìm thấy port mở: {host}:{port}")
                    # Kiểm tra xem có phải ADB server không
                    adb_info = get_adb_info(host, port)
                    if adb_info['status'] == 'connected':
                        active_servers.append(adb_info)
                        print(f"   📱 ADB Server hoạt động - {adb_info['device_count']} thiết bị")
                    else:
                        print(f"   ❌ Không phải ADB server: {adb_info.get('error', 'Unknown')}")
            except:
                pass
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ QUÉT:")
    print("=" * 60)
    
    if not active_servers:
        print("❌ Không tìm thấy ADB server nào đang chạy!")
        print("\n💡 Gợi ý:")
        print("   1. Khởi động emulator (BlueStacks, NoxPlayer, MuMu, v.v.)")
        print("   2. Kết nối thiết bị Android qua USB")
        print("   3. Chạy lệnh 'adb start-server'")
        return []
    
    for i, server in enumerate(active_servers, 1):
        print(f"\n🖥️  ADB SERVER #{i}")
        print(f"   📍 Host: {server['host']}")
        print(f"   🔌 Port: {server['port']}")
        print(f"   📱 Số thiết bị: {server['device_count']}")
        
        if server['devices']:
            print(f"   📋 Danh sách thiết bị:")
            for j, device in enumerate(server['devices'], 1):
                try:
                    model = device.shell('getprop ro.product.model').strip()
                    android_ver = device.shell('getprop ro.build.version.release').strip()
                    print(f"      {j}. Serial: {device.serial}")
                    print(f"         Model: {model}")
                    print(f"         Android: {android_ver}")
                except Exception as e:
                    print(f"      {j}. Serial: {device.serial}")
                    print(f"         (Không thể lấy thông tin chi tiết: {e})")
        else:
            print(f"   📋 Không có thiết bị nào được kết nối")
    
    print(f"\n🎉 Tổng cộng tìm thấy {len(active_servers)} ADB server đang hoạt động!")
    return active_servers

def monitor_adb_servers(interval=5):
    """Theo dõi ADB servers liên tục"""
    print("🔄 Chế độ theo dõi liên tục (Nhấn Ctrl+C để dừng)")
    print(f"⏱️  Cập nhật mỗi {interval} giây\n")
    
    try:
        while True:
            servers = scan_adb_servers()
            print(f"\n⏰ Lần quét tiếp theo sau {interval} giây...")
            print("-" * 60)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng theo dõi!")

if __name__ == "__main__":
    print("🚀 ADB SERVER SCANNER")
    print("=" * 60)
    
    # Hiển thị menu
    print("Chọn chế độ:")
    print("1. Quét một lần")
    print("2. Theo dõi liên tục")
    
    try:
        choice = input("\nNhập lựa chọn (1 hoặc 2): ").strip()
        
        if choice == "1":
            scan_adb_servers()
        elif choice == "2":
            interval = input("Nhập khoảng thời gian quét (giây, mặc định 5): ").strip()
            try:
                interval = int(interval) if interval else 5
            except:
                interval = 5
            monitor_adb_servers(interval)
        else:
            print("❌ Lựa chọn không hợp lệ!")
            scan_adb_servers()
            
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 