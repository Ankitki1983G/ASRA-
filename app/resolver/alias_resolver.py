"""
ASRA Alias Resolver
"""

class AliasResolver:

    def __init__(self, registry):
        self.registry = registry

    def normalize(self, text: str) -> str:
        return (
            text
            .lower()
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

    def resolve(self, user_input: str) -> str | None:

        normalized_input = self.normalize(
            user_input
        )

        # Direct application key
        for app_name in self.registry.registry.keys():

            if self.normalize(app_name) == normalized_input:

                return app_name

        # Alias search
        for app_name, app_data in self.registry.registry.items():

            aliases = app_data.get(
                "aliases",
                []
            )

            for alias in aliases:

                if self.normalize(alias) == normalized_input:

                    return app_name

        return None