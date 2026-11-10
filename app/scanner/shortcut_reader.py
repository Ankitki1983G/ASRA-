"""
Shortcut Reader

Reads Windows shortcut (.lnk) files and
returns the target executable path.
"""

from pathlib import Path
import win32com.client


class ShortcutReader:

    def get_target(self, shortcut_path: Path) -> str | None:
        """
        Return executable path from a shortcut.
        """

        try:

            shell = win32com.client.Dispatch("WScript.Shell")

            shortcut = shell.CreateShortcut(str(shortcut_path))

            return shortcut.Targetpath

        except Exception:

            return None