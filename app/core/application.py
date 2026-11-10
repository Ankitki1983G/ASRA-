
"""
ASRA AI Application Controller.

Provides the official entry point for the assistant.
"""

from app.config.settings import APP_NAME, VERSION
from app.core.assistant import AsraAssistant
from app.utils.logger import get_logger


class Application:
    """Manage ASRA AI application startup."""

    def __init__(self):
        self.logger = get_logger()
        self.app_name = APP_NAME
        self.version = VERSION
        self.assistant = AsraAssistant()

    def run(self):
        """Start the ASRA assistant."""

        self.logger.info("=" * 50)
        self.logger.info("Welcome to %s", self.app_name)
        self.logger.info("Starting ASRA assistant...")
        self.logger.info("=" * 50)

        self.assistant.run()
