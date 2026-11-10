# This module loads application information from configuration files.

import json
import os


class ApplicationRegistry:
    def __init__(self):
        self.apps = self.load_apps()

    def load_apps(self) -> dict:

        config_path = os.path.join(
            "app",
            "config",
            "apps.json"
        )

        with open(config_path, "r") as file:
            return json.load(file)


    def get_application(self, name: str):
        """
        Find application command using name.
        """

        name = name.lower()

        for app_name, details in self.apps.items():

            if name in details["aliases"]:

                return details["command"]

        return None