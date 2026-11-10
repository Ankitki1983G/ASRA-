"""
Application Scanner

Combines:
- Start Menu Scanner
- Shortcut Reader
- Windows Packaged Apps Scanner
"""

import json
from pathlib import Path

from app.scanner.startmenu_scanner import StartMenuScanner
from app.scanner.shortcut_reader import ShortcutReader
from app.scanner.windows_apps_scanner import WindowsAppsScanner


class AppScanner:

    def __init__(self):

        # Start Menu shortcuts
        self.start_menu = StartMenuScanner()

        # Read .lnk targets
        self.shortcut_reader = ShortcutReader()

        # Windows packaged applications
        self.windows_apps = WindowsAppsScanner()

    def scan(self) -> list:
        """
        Scan all available applications.
        """

        applications = []

        # =================================
        # 1. Start Menu Applications
        # =================================

        shortcuts = self.start_menu.scan_shortcuts()

        for shortcut in shortcuts:

            target = self.shortcut_reader.get_target(
                shortcut
            )

            if target:

                applications.append(
                    {
                        "name": shortcut.stem.lower(),
                        "path": target,
                        "type": "desktop"
                    }
                )

        # =================================
        # 2. Windows Packaged Applications
        # =================================

        windows_apps = self.windows_apps.scan()

        applications.extend(
            windows_apps
        )

        print(
            f"[App Scanner] Found "
            f"{len(applications)} applications."
        )

        return applications

    def update_registry(self):
        """
        Update registry.json with detected
        desktop application paths.
        """

        registry_file = (
            Path(__file__).resolve().parent.parent
            / "registry"
            / "registry.json"
        )

        if not registry_file.exists():

            print(
                f"[ERROR] Registry not found: "
                f"{registry_file}"
            )

            return

        with open(
            registry_file,
            "r",
            encoding="utf-8"
        ) as file:

            registry = json.load(file)

        applications = self.scan()

        updated_count = 0

        for app in applications:

            # Windows packaged apps are not stored
            # as normal executable paths in registry.
            if app.get("type") == "windows_app":

                continue

            app_name = (
                app.get("name", "")
                .lower()
                .strip()
            )

            app_path = app.get("path")

            if not app_name or not app_path:

                continue

            matched_key = None

            # -----------------------------
            # Exact Match
            # -----------------------------

            if app_name in registry:

                matched_key = app_name

            # -----------------------------
            # Alias Match
            # -----------------------------

            else:

                for key, value in registry.items():

                    aliases = value.get(
                        "aliases",
                        []
                    )

                    normalized_aliases = [
                        alias.lower().strip()
                        for alias in aliases
                    ]

                    if app_name in normalized_aliases:

                        matched_key = key

                        break

            # -----------------------------
            # Update Registry
            # -----------------------------

            if matched_key:

                registry[matched_key]["path"] = app_path

                registry[matched_key]["installed"] = True

                updated_count += 1

                print(
                    f"[UPDATED] {matched_key}"
                )

        with open(
            registry_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                registry,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(
            "[INFO] Registry updated successfully."
        )

        print(
            f"[INFO] Applications updated: "
            f"{updated_count}"
        )