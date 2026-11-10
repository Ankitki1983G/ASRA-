"""
Start Menu Scanner

Scans Windows Start Menu and returns all shortcut files.
"""

from pathlib import Path


class StartMenuScanner:

    def __init__(self):
        """
        Initialize Start Menu locations.
        """

        self.system_start_menu = Path(
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
        )

        self.user_start_menu = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )

    def get_start_menu_paths(self) -> list:
        """
        Return available Start Menu directories.
        """

        paths = []

        if self.system_start_menu.exists():
            paths.append(self.system_start_menu)

        if self.user_start_menu.exists():
            paths.append(self.user_start_menu)

        return paths

    def scan_shortcuts(self) -> list:
        """
        Scan all .lnk shortcut files.
        """

        shortcuts = []

        for folder in self.get_start_menu_paths():

            for shortcut in folder.rglob("*.lnk"):

                shortcuts.append(shortcut)

        return shortcuts

    def scan(self) -> list:
        """
        Scan Start Menu and return shortcut information.
        """

        shortcut_list = []

        for shortcut in self.scan_shortcuts():

            shortcut_list.append(
                {
                    "name": shortcut.stem,
                    "shortcut": str(shortcut)
                }
            )

        return shortcut_list