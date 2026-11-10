"""
Windows Packaged Applications Scanner

Detects Windows applications that may not have
normal .lnk shortcuts in the Start Menu.
"""

import subprocess
import json


class WindowsAppsScanner:

    def __init__(self):
        pass

    def scan(self) -> list:
        """
        Scan Windows packaged applications.
        """

        applications = []

        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            """
            Get-StartApps |
            Select-Object Name, AppID |
            ConvertTo-Json -Compress
            """
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            if result.returncode != 0:

                print(
                    "[Windows Apps Scanner] "
                    "PowerShell scan failed."
                )

                return []

            output = result.stdout.strip()

            if not output:

                return []

            data = json.loads(output)

            if isinstance(data, dict):

                data = [data]

            for app in data:

                name = app.get("Name")
                app_id = app.get("AppID")

                if not name or not app_id:

                    continue

                applications.append(
                    {
                        "name": name.lower().strip(),
                        "path": app_id,
                        "type": "windows_app"
                    }
                )

            print(
                f"[Windows Apps Scanner] "
                f"Found {len(applications)} apps."
            )

            return applications

        except Exception as error:

            print(
                f"[Windows Apps Scanner Error] "
                f"{error}"
            )

            return []