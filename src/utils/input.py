"""
Input simulation utility module for the AutoZ framework.
Provides functions for mouse and keyboard control.
"""

import time
import random
import pyautogui
import win32gui
import win32con
from typing import Tuple, Optional, List
from src.utils.logging import log_error, log_warning

# Configure PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

def safe_click(x: int, y: int, window_handle: Optional[int] = None, duration: float = 0) -> bool:
    """Safely click at specified coordinates with window validation."""
    try:
        if window_handle:
            # Verify we're clicking in the correct window
            window_at_point = win32gui.WindowFromPoint((x, y))
            if window_at_point != window_handle:
                log_warning(f"Click point ({x}, {y}) is not in the target window")
                return False
                
        pyautogui.click(x=x, y=y, clicks=1, interval=0.0, button='left', duration=duration)
        return True
        
    except Exception as e:
        log_error(f"Error clicking at ({x}, {y}): {e}")
        return False

def safe_move(x: int, y: int, duration: float = 0) -> bool:
    """Safely move mouse to specified coordinates."""
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return True
    except Exception as e:
        log_error(f"Error moving to ({x}, {y}): {e}")
        return False

def safe_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> bool:
    """Safely drag from start to end coordinates."""
    try:
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
        return True
    except Exception as e:
        log_error(f"Error dragging from ({start_x}, {start_y}) to ({end_x}, {end_y}): {e}")
        return False

def safe_scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """Safely scroll at specified coordinates."""
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
        pyautogui.scroll(clicks)
        return True
    except Exception as e:
        log_error(f"Error scrolling: {e}")
        return False

def safe_type(text: str, interval: float = 0.1) -> bool:
    """Safely type text with specified interval between keystrokes."""
    try:
        pyautogui.write(text, interval=interval)
        return True
    except Exception as e:
        log_error(f"Error typing text: {e}")
        return False

def safe_press(key: str) -> bool:
    """Safely press a key."""
    try:
        pyautogui.press(key)
        return True
    except Exception as e:
        log_error(f"Error pressing key {key}: {e}")
        return False

def safe_hotkey(*args: str) -> bool:
    """Safely press a combination of keys."""
    try:
        pyautogui.hotkey(*args)
        return True
    except Exception as e:
        log_error(f"Error pressing hotkey {args}: {e}")
        return False

def get_screen_size() -> Tuple[int, int]:
    """Get the screen size."""
    return pyautogui.size()

def get_mouse_position() -> Tuple[int, int]:
    """Get the current mouse position."""
    return pyautogui.position()

def is_point_visible(x: int, y: int) -> bool:
    """Check if a point is within the visible screen area."""
    screen_width, screen_height = get_screen_size()
    return 0 <= x < screen_width and 0 <= y < screen_height 

def move_to(
    x: int,
    y: int,
    duration: Optional[float] = None,
    humanize: bool = True
) -> None:
    """
    Move the mouse cursor to specified coordinates.
    
    Args:
        x: Target x coordinate
        y: Target y coordinate
        duration: Movement duration in seconds
        humanize: Add human-like randomness to movement
    """
    if humanize:
        duration = duration or random.uniform(0.2, 0.5)
        # Add slight offset to target position
        x += random.randint(-2, 2)
        y += random.randint(-2, 2)
    else:
        duration = duration or 0.1
    
    pyautogui.moveTo(x, y, duration=duration)

def click(
    x: Optional[int] = None,
    y: Optional[int] = None,
    button: str = 'left',
    clicks: int = 1,
    interval: float = 0.25
) -> None:
    """
    Click at the specified coordinates or current mouse position.
    
    Args:
        x: Target x coordinate (optional)
        y: Target y coordinate (optional)
        button: Mouse button to click ('left', 'right', 'middle')
        clicks: Number of clicks
        interval: Time between clicks in seconds
    """
    if x is not None and y is not None:
        move_to(x, y)
    
    pyautogui.click(button=button, clicks=clicks, interval=interval)

def drag_to(
    start: Tuple[int, int],
    end: Tuple[int, int],
    duration: float = 0.5,
    button: str = 'left'
) -> None:
    """
    Drag from start coordinates to end coordinates.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        duration: Drag duration in seconds
        button: Mouse button to use for dragging
    """
    pyautogui.moveTo(*start)
    pyautogui.dragTo(*end, duration=duration, button=button)

def type_text(
    text: str,
    interval: Optional[float] = None,
    humanize: bool = True
) -> None:
    """
    Type text with optional human-like timing.
    
    Args:
        text: Text to type
        interval: Time between keystrokes in seconds
        humanize: Add human-like randomness to typing
    """
    if humanize and interval is None:
        # Random interval between keystrokes
        for char in text:
            pyautogui.write(char, interval=random.uniform(0.05, 0.15))
    else:
        pyautogui.write(text, interval=interval or 0.1)

def press_key(
    key: str,
    presses: int = 1,
    interval: float = 0.1
) -> None:
    """
    Press a keyboard key.
    
    Args:
        key: Key to press
        presses: Number of times to press the key
        interval: Time between presses in seconds
    """
    pyautogui.press(key, presses=presses, interval=interval)

def hold_key(key: str, duration: float = 1.0) -> None:
    """
    Hold a keyboard key for a specified duration.
    
    Args:
        key: Key to hold
        duration: Duration to hold the key in seconds
    """
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)

def scroll(
    clicks: int,
    x: Optional[int] = None,
    y: Optional[int] = None
) -> None:
    """
    Scroll the mouse wheel.
    
    Args:
        clicks: Number of clicks (positive for up, negative for down)
        x: X coordinate to scroll at (optional)
        y: Y coordinate to scroll at (optional)
    """
    if x is not None and y is not None:
        move_to(x, y)
    
    pyautogui.scroll(clicks) 