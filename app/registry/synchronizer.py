import json
from pathlib import Path

from app.registry.app_registry import AppRegistry
from app.scanner.installed_apps import InstalledAppsScanner


class RegistrySynchronizer:

    def __init__(self):

        self.registry = AppRegistry()

        self.scanner = InstalledAppsScanner()

    def synchronize(self):

        scanned_apps = self.scanner.scan()

        registry = self.registry.registry

        for app_name, shortcut_path in scanned_apps.items():

            if app_name in registry:

                registry[app_name]["installed"] = True

                registry[app_name]["path"] = shortcut_path

            else:

                registry[app_name] = {

                    "name": app_name.title(),

                    "aliases": [

                        app_name

                    ],

                    "path": shortcut_path,

                    "category": "unknown",

                    "priority": 5,

                    "installed": True

                }

        with open(

            self.registry.registry_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                registry,

                file,

                indent=4

            )

        print("Registry synchronized successfully.")