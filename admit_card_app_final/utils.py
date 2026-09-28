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


# ---------------------------------------------------------------
# Optional subjects (by class)
# ---------------------------------------------------------------
OPTIONAL_SUBJECTS_BY_CLASS = {
    10: ["Arts"],
    11: ["Physical Education", "Computer Science", "Informatics Practices", "Music"],
    12: ["Physical Education", "Computer Science", "Informatics Practices", "Music"],
}

_ROMAN = {"X": 10, "XI": 11, "XII": 12}


def parse_class_number(class_section):
    """
    Extracts the class number from text like '10', '10-A', 'Class 11 B',
    '12th C' or 'XII-A'. Returns an int, or None if it can't be found.
    """
    import re
    text = (class_section or "").strip().upper()
    if not text:
        return None
    m = re.search(r"\d+", text)
    if m:
        return int(m.group())
    m = re.match(r"^(?:CLASS\s*)?(XII|XI|X)\b", text)
    if m:
        return _ROMAN[m.group(1)]
    return None


def get_optional_subject_choices(class_section):
    """Returns the list of optional subjects for a class (empty for other classes)."""
    n = parse_class_number(class_section)
    return list(OPTIONAL_SUBJECTS_BY_CLASS.get(n, []))


def all_known_optional_subjects():
    seen = []
    for lst in OPTIONAL_SUBJECTS_BY_CLASS.values():
        for name in lst:
            if name.lower() not in [x.lower() for x in seen]:
                seen.append(name)
    return seen


def split_optional_subjects(value):
    """'Music, Arts' -> ['Music', 'Arts'] (empty items removed)."""
    return [p.strip() for p in (value or "").split(",") if p.strip()]
