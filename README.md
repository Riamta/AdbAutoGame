# Game Auto Framework

A mobile game automation framework using ADB and image processing. This framework allows you to easily create automation scripts for any mobile game using template matching and ADB controls.

## Features

- Flexible core system:
  - ADB controller for device interaction
  - Template matching engine for UI element recognition
  - Comprehensive logging system
  - Multi-threading for better performance
  - Easy to extend for new games

- Basic operations:
  - Click/Tap coordinates
  - Swipe/Drag
  - Find and click by template
  - Screen capture
  - Keyboard input handling
  - Device control (back, home, etc.)

## Requirements

- Python 3.7+
- ADB (Android Debug Bridge) - included in `src/binaries`
- Android device or Emulator (supports multiple emulators: MuMu, NoxPlayer, BlueStacks, etc.)

## Installation

1. Clone this repository
2. Install required Python libraries:
```bash
pip install -r requirements.txt
```

## Configuration

1. Ensure Android device/Emulator has USB Debugging enabled
2. Connect device to computer via USB or network (ADB over network)
3. Check ADB connection:
```bash
.\src\binaries\adb.exe devices
```

## Directory Structure

```
├── assets/
│   ├── game1/
│   │   └── templates/        # Image templates for game1
│   ├── game2/
│   │   └── templates/        # Image templates for game2
│   └── ...
├── src/
│   ├── binaries/            # ADB and binary files
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
└── run_*.py               # Runner scripts for each game
```

## Creating Auto for New Game

1. Create templates directory:
```
assets/your_game/templates/
```

2. Collect templates:
- Take screenshots of UI elements to recognize
- Save them in templates directory with descriptive names

3. Create game class:
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

4. Create runner script:
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