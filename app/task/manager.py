"""
ASRA Task Manager

Routes processed commands to the appropriate ASRA module.
"""

from app.registry.app_registry import AppRegistry
from app.resolver.alias_resolver import AliasResolver
from app.scanner.app_scanner import AppScanner
from app.command.fuzzy import FuzzyMatcher
from app.launcher.application_launcher import ApplicationLauncher


class TaskManager:
    """
    Handles task routing based on command intent.
    """

    def __init__(self):

        # Application Registry
        self.registry = AppRegistry()

        # Alias Resolver
        self.alias_resolver = AliasResolver(
            self.registry
        )

        # Fuzzy Matcher
        self.fuzzy_matcher = FuzzyMatcher()

        # Application Scanner
        self.scanner = AppScanner()

        # Application Launcher
        self.launcher = ApplicationLauncher()

    def route(self, command: dict):
        """
        Route a processed command to the
        appropriate ASRA task.
        """

        if not command:
            print("[Task Manager] No command received.")
            return

        intent = command.get("intent")

        # ---------------------------------
        # Open Application
        # ---------------------------------

        if intent == "open_application":

            application_name = command.get(
                "target",
                ""
            ).lower().strip()

            if not application_name:

                print(
                    "[Task Manager] "
                    "Application name missing."
                )

                return

            self.open_application(
                application_name
            )

        # ---------------------------------
        # Web Search
        # ---------------------------------

        elif intent == "web_search":

            print(
                "[Task Manager] "
                "Web search module not available yet."
            )

        # ---------------------------------
        # Unknown Intent
        # ---------------------------------

        else:

            print(
                f"[Task Manager] "
                f"Unknown command: {intent}"
            )

    def open_application(
        self,
        application_name: str
    ):
        """
        Find and launch an application.
        """

        print(
            f"[Task Manager] "
            f"Opening: {application_name}"
        )

        # ---------------------------------
        # Step 1: Alias Resolution
        # ---------------------------------

        resolved_name = self.alias_resolver.resolve(
            application_name
        )

        if resolved_name:

            application_name = resolved_name

            print(
                f"[Task Manager] Alias resolved: "
                f"{application_name}"
            )

        # ---------------------------------
        # Step 2: Registry Search
        # ---------------------------------

        app_path = (
            self.registry.get_application_path(
                application_name
            )
        )

        if app_path:

            print(
                f"[Task Manager] "
                f"Found in registry: "
                f"{application_name}"
            )

            self.launcher.launch(
                app_path
            )

            return

        # ---------------------------------
        # Step 3: Application Scanner
        # ---------------------------------

        print(
            "[Task Manager] "
            "Registry path not found."
        )

        print(
            "[Task Manager] "
            "Scanning installed applications..."
        )

        applications = self.scanner.scan()

        if not applications:

            print(
                "[Task Manager] "
                "No applications detected."
            )

            return

        # ---------------------------------
        # Step 4: Fuzzy Matching
        # ---------------------------------

        application_names = [
            app["name"]
            for app in applications
        ]

        best_match = (
            self.fuzzy_matcher.find_best_match(
                application_name,
                application_names
            )
        )

        if not best_match:

            print(
                f"[Task Manager] "
                f"Application not found: "
                f"{application_name}"
            )

            return

        print(
            f"[Task Manager] "
            f"Best match: {best_match}"
        )

        # ---------------------------------
        # Step 5: Find Path
        # ---------------------------------

        for app in applications:

            if app["name"] == best_match:

                path = app.get("path")

                if not path:

                    print(
                        "[Task Manager] "
                        "Application path missing."
                    )

                    return

                # ---------------------------------
                # Step 6: Launch
                # ---------------------------------

                print(
                    f"[Task Manager] "
                    f"Launching: {path}"
                )

                self.launcher.launch(path)

                return

        print(
            "[Task Manager] "
            "Application path not found."
        )