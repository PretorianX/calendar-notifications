"""Locate bundled resource files (sounds, icons) in source and frozen builds."""

import os
import sys


def resource_path(*parts: str) -> str:
    """Return the absolute path of a bundled resource.

    PyInstaller unpacks data files under ``sys._MEIPASS``. When the app runs
    from source, resources live in the project root (the parent of ``src``).
    """
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base, *parts)
