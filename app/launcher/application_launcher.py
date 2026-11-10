"""
ASRA Application Launcher

Launches normal Windows executables,
system commands and Windows packaged apps.
"""

import subprocess
from pathlib import Path


class ApplicationLauncher:

    def __init__(self):
        pass

    def launch(
        self,
        application_path: str,
        application_type: str = "desktop"
    ) -> bool:
        """
        Launch an application.
        """

        try:

            # ---------------------------------
            # Windows Packaged Application
            # ---------------------------------

            if application_type == "windows_app":

                command = [
                    "explorer.exe",
                    f"shell:AppsFolder\\{application_path}"
                ]

                subprocess.Popen(command)

                print(
                    "[Launcher] Windows application launched."
                )

                return True

            # ---------------------------------
            # Normal executable path
            # ---------------------------------

            if Path(application_path).exists():

                subprocess.Popen(
                    [application_path]
                )

                print(
                    "[Launcher] Application launched."
                )

                return True

            # ---------------------------------
            # Windows system command
            # ---------------------------------

            subprocess.Popen(
                application_path,
                shell=True
            )

            print(
                "[Launcher] System application launched."
            )

            return True

        except FileNotFoundError:

            print(
                "[Launcher] Application not found."
            )

            return False

        except Exception as error:

            print(
                f"[Launcher Error] {error}"
            )

            return False