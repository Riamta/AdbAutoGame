"""
Core automation module.
"""

from .base_auto import BaseGameAutomation
from .adb_auto import ADBGameAutomation

__all__ = ['BaseGameAutomation', 'ADBGameAutomation']
