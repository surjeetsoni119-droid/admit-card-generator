"""
utils.py
Shared helpers for resolving file paths correctly whether the app is
running as a normal Python script or as a packaged .exe (PyInstaller).
"""

import sys
import os


def get_base_dir():
    """
    Folder for the app's WRITABLE data (database, generated PDFs, photos).
    - When packaged as a .exe: the folder containing the .exe itself,
      so data persists between runs.
    - When running as a script: the folder containing this file.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_dir():
    """
    Folder for bundled READ-ONLY resources (default logo, icon).
    - When packaged as a .exe: PyInstaller's temporary extraction folder.
    - When running as a script: the folder containing this file.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", get_base_dir())
    return os.path.dirname(os.path.abspath(__file__))
