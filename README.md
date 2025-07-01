# Game Auto Framework

Framework tự động hóa (auto) cho các game mobile sử dụng ADB và xử lý ảnh. Framework này cho phép bạn dễ dàng tạo auto cho bất kỳ game mobile nào bằng cách sử dụng template matching và ADB controls.

## Tính năng

- Hệ thống core linh hoạt:
  - ADB controller cho tương tác với thiết bị
  - Template matching engine để nhận diện UI elements
  - Hệ thống logging đầy đủ
  - Xử lý đa luồng cho performance tốt hơn
  - Dễ dàng mở rộng cho game mới

- Các thao tác cơ bản:
  - Click/Tap tọa độ
  - Swipe/Drag
  - Tìm và click theo template
  - Capture màn hình
  - Xử lý keyboard input
  - Điều khiển thiết bị (back, home, etc.)

## Yêu cầu

- Python 3.7+
- ADB (Android Debug Bridge) - đã được đính kèm trong thư mục `src/binaries`
- Thiết bị Android hoặc Emulator (hỗ trợ nhiều emulator: MuMu, NoxPlayer, BlueStacks, etc.)

## Cài đặt

1. Clone repository này về máy
2. Cài đặt các thư viện Python cần thiết:
```bash
pip install -r requirements.txt
```

## Cấu hình

1. Đảm bảo thiết bị Android/Emulator đã bật chế độ USB Debugging
2. Kết nối thiết bị với máy tính qua USB hoặc qua mạng (ADB over network)
3. Kiểm tra kết nối ADB:
```bash
.\src\binaries\adb.exe devices
```

## Cấu trúc thư mục

```
├── assets/
│   ├── game1/
│   │   └── templates/        # Template ảnh cho game1
│   ├── game2/
│   │   └── templates/        # Template ảnh cho game2
│   └── ...
├── src/
│   ├── binaries/            # ADB và các file binary
│   ├── core/                # Core modules
│   │   ├── adb.py          # ADB controller
│   │   ├── adb_auto.py     # Game automation base class
│   │   └── base_auto.py    # Base automation class
│   ├── games/              # Game-specific implementations
│   │   ├── game1.py
│   │   ├── game2.py
│   │   └── ...
│   └── utils/              # Utility functions
│       ├── image.py        # Image processing
│       ├── input.py        # Input handling
│       └── logging.py      # Logging system
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
└── run_*.py               # Runner scripts cho từng game
```

## Tạo Auto cho Game Mới

1. Tạo thư mục templates:
```
assets/your_game/templates/
```

2. Thu thập templates:
- Chụp ảnh các UI element cần nhận diện
- Lưu vào thư mục templates với tên mô tả

3. Tạo game class:
```python
from src.core.adb_auto import ADBGameAutomation

class YourGameAutomation(ADBGameAutomation):
    def __init__(self):
        super().__init__()
        self.templates_dir = "assets/your_game/templates"
        
    def process_game_actions(self):
        while self.running:
            screen = self.capture_screen()
            # Implement your game logic here
```

4. Tạo runner script:
```python
from src.games.your_game import YourGameAutomation

def main():
    game = YourGameAutomation()
    game.start()

if __name__ == "__main__":
    main()
```

## License

MIT License 