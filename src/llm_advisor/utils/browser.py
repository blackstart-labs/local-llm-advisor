"""Browser utility helpers for opening HTML reports."""

from __future__ import annotations

import os
import webbrowser


def open_in_browser(file_path: str) -> bool:
    """Open local HTML file in default user browser."""
    try:
        abs_path = os.path.abspath(file_path)
        file_url = f"file://{abs_path}"
        return webbrowser.open_new_tab(file_url)
    except Exception:
        return False
