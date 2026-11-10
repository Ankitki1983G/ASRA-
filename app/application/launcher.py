
import subprocess

from app.application.registry import ApplicationRegistry


class ApplicationLauncher:
  
    def __init__(self):
        self.registry = ApplicationRegistry()


    def open_application(self, application_name: str):
       
        command = self.registry.get_application(
            application_name
        )


        if command:

            print(
                f"[Application Launcher] Opening {application_name}"
            )

            subprocess.Popen(
                command,
                shell=True
            )

        else:

            print(
                f"[Application Launcher] "
                f"Application not found: {application_name}"
            )