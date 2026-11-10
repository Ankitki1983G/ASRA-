"""
ASRA Application Registry Manager

Provides a single source of truth for the
ASRA application registry.
"""

import json
from pathlib import Path


class AppRegistry:

    def __init__(self):

        self.registry_file = (
            Path(__file__).resolve().parent
            / "registry.json"
        )

        self.registry = self.load_registry()

    def load_registry(self) -> dict:

        if not self.registry_file.exists():

            print(
                f"[ERROR] Registry file not found: "
                f"{self.registry_file}"
            )

            return {}

        with open(
            self.registry_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    def save_registry(self):

        with open(
            self.registry_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.registry,
                file,
                indent=4,
                ensure_ascii=False
            )

    def reload(self):

        self.registry = self.load_registry()

    def get_application(
        self,
        app_name: str
    ) -> dict | None:

        return self.registry.get(
            app_name.lower().strip()
        )

    def find_by_alias(
        self,
        alias: str
    ) -> dict | None:

        alias = alias.lower().strip()

        for app_name, app_data in self.registry.items():

            aliases = app_data.get(
                "aliases",
                []
            )

            for item in aliases:

                if item.lower().strip() == alias:

                    return {
                        "key": app_name,
                        **app_data
                    }

        return None

    def get_application_path(
        self,
        app_name: str
    ) -> str | None:

        app = self.get_application(
            app_name
        )

        if app:

            return app.get("path")

        return None

    def list_applications(self) -> list:

        return list(
            self.registry.keys()
        )