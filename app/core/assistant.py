"""
ASRA Assistant Core Controller
------------------------------
Central controller for voice/text commands, task execution,
application launching, browser automation, and desktop input.

Features:
- Input/command validation
- Sequential multi-task execution
- Per-task execution reports (SUCCESS / FAILED / SKIPPED)
- Consistent exception handling
- Browser method capability checks
- Application registry + scanner fallback
- Desktop actions and keyboard shortcuts
- Browser resource cleanup
"""

from typing import Any, Dict, List, Optional


class AsraAssistant:
    """Central controller of ASRA AI."""

    def __init__(self):
        from app.voice.engine import VoiceEngine
        from app.command.processor import CommandProcessor
        from app.registry.app_registry import AppRegistry
        from app.command.fuzzy import FuzzyMatcher
        from app.launcher.application_launcher import ApplicationLauncher
        from app.scanner.app_scanner import AppScanner
        from app.resolver.alias_resolver import AliasResolver
        from app.browser.manager import BrowserManager

        self.voice_engine = VoiceEngine()
        self.command_processor = CommandProcessor()

        self.registry = AppRegistry()
        self.alias_resolver = AliasResolver(self.registry)

        self.fuzzy_matcher = FuzzyMatcher()
        self.scanner = AppScanner()
        self.launcher = ApplicationLauncher()
        self.browser_manager = BrowserManager()

        self._closed = False

        print("[INFO] ASRA Assistant Initialized Successfully")

    # --------------------------------------------------
    # COMMAND EXECUTION CONTROLLER
    # --------------------------------------------------

    def execute_command(self, text: str):
        """Convert natural language into a command and execute it."""

        if not isinstance(text, str) or not text.strip():
            print("[INFO] No command received.")
            return False

        try:
            command = self.command_processor.process(text)
        except Exception as error:
            print(f"[ERROR] Command processing failed: {error}")
            return False

        if not isinstance(command, dict):
            print("[ERROR] CommandProcessor must return a dictionary.")
            return False

        print(f"[Assistant] {command}")

        intent = command.get("intent")

        if intent == "multi_command":
            return self._execute_multiple_tasks(command)

        success = self.execute_single_command(command)

        if success:
            print("[SUCCESS] Command completed.")
        else:
            print("[ERROR] Command failed.")

        return success

    def _execute_multiple_tasks(
        self,
        command: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute tasks sequentially and stop after the first failure."""

        tasks = command.get("tasks")

        if not isinstance(tasks, list) or not tasks:
            print("[ERROR] No valid tasks found.")
            return []

        results: List[Dict[str, Any]] = []
        total = len(tasks)

        print(f"[INFO] Starting execution of {total} tasks.")

        for index, task in enumerate(tasks, start=1):

            print(f"\n[TASK {index}/{total}] Executing: {task}")

            if not isinstance(task, dict):
                print(f"[ERROR] Task {index} has an invalid format.")

                results.append({
                    "task_number": index,
                    "command": task,
                    "success": False,
                    "status": "FAILED",
                    "error": "Task must be a dictionary."
                })

                self._append_skipped_tasks(tasks, index, results)
                break

            try:
                success = bool(self.execute_single_command(task))
                error_message = None

            except Exception as error:
                success = False
                error_message = str(error)

                print(
                    f"[ERROR] Task {index} raised an exception: {error}"
                )

            results.append({
                "task_number": index,
                "command": task,
                "success": success,
                "status": "SUCCESS" if success else "FAILED",
                "error": error_message
            })

            if success:
                print(f"[SUCCESS] Task {index} completed.")

            else:
                print(f"[FAILED] Task {index} failed.")

                self._append_skipped_tasks(
                    tasks,
                    index,
                    results
                )
                break

        self._print_task_report(tasks, results)

        return results

    @staticmethod
    def _append_skipped_tasks(
        tasks: List[Any],
        failed_index: int,
        results: List[Dict[str, Any]]
    ) -> None:
        """Mark tasks after a failed task as skipped."""

        for task_number in range(
            failed_index + 1,
            len(tasks) + 1
        ):

            task = tasks[task_number - 1]

            results.append({
                "task_number": task_number,
                "command": task,
                "success": False,
                "status": "SKIPPED",
                "error": "A previous task failed."
            })

            print(
                f"[SKIPPED] Task {task_number} was not executed."
            )

    @staticmethod
    def _print_task_report(
        tasks: List[Any],
        results: List[Dict[str, Any]]
    ) -> None:
        """Print a summary of the complete workflow."""

        successful = sum(
            r["status"] == "SUCCESS" for r in results
        )

        failed = sum(
            r["status"] == "FAILED" for r in results
        )

        skipped = sum(
            r["status"] == "SKIPPED" for r in results
        )

        print("\n========== ASRA TASK REPORT ==========")
        print(f"Total tasks: {len(tasks)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")

        for result in results:

            print(
                f"Task {result['task_number']}: "
                f"{result['status']} - {result['command']}"
            )

            if result.get("error"):
                print(f"  Reason: {result['error']}")

        if failed == 0 and skipped == 0:
            print("[SUCCESS] All tasks completed.")
        else:
            print(
                "[WARNING] Workflow stopped before "
                "all tasks completed."
            )

    # --------------------------------------------------
    # EXECUTE ONE TASK
    # --------------------------------------------------

    def execute_single_command(
        self,
        command: Dict[str, Any]
    ) -> bool:
        """Route a structured task to its responsible module."""

        if not isinstance(command, dict):
            print("[ERROR] Invalid command. Expected a dictionary.")
            return False

        intent = command.get("intent")

        if not isinstance(intent, str) or not intent.strip():
            print("[ERROR] Command intent is missing.")
            return False

        intent = intent.strip().lower()

        # ----------------------------------------------
        # APPLICATION LAUNCHING
        # ----------------------------------------------

        if intent == "open_application":
            return self.open_application(
                command.get("target", "")
            )

        # ----------------------------------------------
        # YOUTUBE PLAYBACK
        # ----------------------------------------------

        if intent == "youtube_play":

            query = self._get_string(command, "query")

            if not query:
                print("[ERROR] YouTube search query is missing.")
                return False

            method = getattr(
                self.browser_manager,
                "play_youtube",
                None
            )

            if not callable(method):
                print(
                    "[ERROR] BrowserManager.play_youtube() "
                    "is unavailable."
                )
                return False

            return bool(
                method(
                    query,
                    content_type=command.get(
                        "content_type",
                        "video"
                    )
                )
            )

        # ----------------------------------------------
        # GENERAL WEB SEARCH
        # ----------------------------------------------

        if intent == "web_search":

            query = self._get_string(command, "query")

            if not query:
                print("[ERROR] Search query is missing.")
                return False

            return self._call_browser_method(
                "search_web",
                query
            )

        # ----------------------------------------------
        # WEBSITE NAVIGATION
        # ----------------------------------------------

        if intent == "web_navigate":

            url = self._get_string(command, "url")

            if not url:
                print("[ERROR] Navigation URL is missing.")
                return False

            return self._call_browser_method(
                "navigate_to",
                url
            )

        # ----------------------------------------------
        # DESKTOP ACTIONS
        # ----------------------------------------------

        if intent == "desktop_action":

            return self._execute_desktop_action(
                command.get("action", "")
            )

        # ----------------------------------------------
        # DESKTOP TEXT INPUT
        # ----------------------------------------------

        if intent == "desktop_type":

            content = command.get("text")

            if not isinstance(content, str) or not content:
                print("[ERROR] No text was provided.")
                return False

            try:
                import pyautogui

                pyautogui.write(
                    content,
                    interval=0.02
                )

                return True

            except ImportError:
                print(
                    "[ERROR] Install pyautogui "
                    "in the active .venv."
                )
                return False

            except Exception as error:
                print(
                    f"[ERROR] Could not type text: {error}"
                )
                return False

        # ----------------------------------------------
        # KEYBOARD SHORTCUT
        # ----------------------------------------------

        if intent == "keyboard_shortcut":

            keys = self._get_string(
                command,
                "keys"
            ).lower()

            if not keys:
                print("[ERROR] Keyboard shortcut is missing.")
                return False

            key_map = {
                "ctrl": "ctrl",
                "control": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "enter": "enter",
                "return": "enter",
                "tab": "tab",
                "esc": "esc",
                "escape": "esc",
                "space": "space",
                "backspace": "backspace",
                "delete": "delete",
                "del": "delete",
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right",
                "home": "home",
                "end": "end",
            }

            try:
                import pyautogui

                parts = [
                    part.strip()
                    for part in keys.split("+")
                    if part.strip()
                ]

                parts = [
                    key_map.get(part, part)
                    for part in parts
                ]

                if not parts:
                    print(
                        "[ERROR] No valid keys were provided."
                    )
                    return False

                if len(parts) == 1:
                    pyautogui.press(parts[0])
                else:
                    pyautogui.hotkey(*parts)

                return True

            except ImportError:
                print(
                    "[ERROR] Install pyautogui "
                    "in the active .venv."
                )
                return False

            except Exception as error:
                print(
                    f"[ERROR] Keyboard action failed: {error}"
                )
                return False

        print(
            f"[ERROR] Unsupported command intent: {intent}"
        )

        return False

    # --------------------------------------------------
    # DESKTOP ACTION HANDLER
    # --------------------------------------------------

    def _execute_desktop_action(
        self,
        action: str
    ) -> bool:
        """Execute supported Windows desktop/window actions."""

        if not isinstance(action, str) or not action.strip():
            print("[ERROR] Desktop action is missing.")
            return False

        action = action.strip().lower()

        shortcuts = {
            "show_desktop": ("win", "d"),
            "refresh": ("f5",),
            "minimize": ("win", "down"),
            "maximize": ("win", "up"),
            "switch_window": ("alt", "tab"),
            "close_active_window": ("alt", "f4"),
        }

        keys = shortcuts.get(action)

        if not keys:
            print(
                f"[ERROR] Unsupported desktop action: {action}"
            )
            return False

        try:
            import pyautogui

            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)

            return True

        except ImportError:
            print(
                "[ERROR] Install pyautogui "
                "in the active .venv."
            )
            return False

        except Exception as error:
            print(
                f"[ERROR] Desktop action '{action}' failed: {error}"
            )
            return False

    # --------------------------------------------------
    # HELPER METHODS
    # --------------------------------------------------

    @staticmethod
    def _get_string(
        command: Dict[str, Any],
        key: str
    ) -> str:
        """Safely read a string parameter."""

        value = command.get(key, "")

        return (
            value.strip()
            if isinstance(value, str)
            else ""
        )

    def _call_browser_method(
        self,
        method_name: str,
        value: str
    ) -> bool:
        """Call a BrowserManager method if available."""

        method = getattr(
            self.browser_manager,
            method_name,
            None
        )

        if not callable(method):
            print(
                f"[ERROR] BrowserManager.{method_name}() "
                "is not implemented."
            )
            return False

        try:
            return bool(method(value))

        except Exception as error:
            print(
                f"[ERROR] Browser operation "
                f"'{method_name}' failed: {error}"
            )
            return False

    # --------------------------------------------------
    # APPLICATION LAUNCHING
    # --------------------------------------------------

    def open_application(
        self,
        raw_name: str
    ) -> bool:
        """
        Resolve and launch an application using:

        1. Alias resolver
        2. Application registry
        3. Installed-application scanner
        4. Exact/fuzzy name matching
        """

        if not isinstance(raw_name, str) or not raw_name.strip():
            print("[ERROR] Application name missing.")
            return False

        raw_name = raw_name.strip().lower()

        # ----------------------------------------------
        # ALIAS RESOLUTION
        # ----------------------------------------------

        try:
            resolved_name = self.alias_resolver.resolve(
                raw_name
            )

        except Exception as error:
            print(
                f"[WARNING] Alias resolution failed: {error}"
            )
            resolved_name = None

        app_name = (
            resolved_name.strip().lower()
            if isinstance(resolved_name, str)
            and resolved_name.strip()
            else raw_name
        )

        if app_name != raw_name:
            print(
                f"[INFO] Alias Resolved: "
                f"{raw_name} -> {app_name}"
            )

        # ----------------------------------------------
        # REGISTRY LOOKUP
        # ----------------------------------------------

        try:
            app_path = self.registry.get_application_path(
                app_name
            )

        except Exception as error:
            print(
                f"[WARNING] Registry lookup failed: {error}"
            )
            app_path = None

        if app_path:

            print(
                f"[INFO] Found in Registry: {app_name}"
            )

            try:
                success = self.launcher.launch(
                    app_path
                )

            except Exception as error:
                print(
                    f"[WARNING] Registry launch raised "
                    f"an error: {error}"
                )
                success = False

            if success:
                return True

            print(
                "[WARNING] Registry launch failed; "
                "trying scanner fallback."
            )

        # ----------------------------------------------
        # SCANNER FALLBACK
        # ----------------------------------------------

        print(
            "[INFO] Scanning installed applications..."
        )

        try:
            applications = self.scanner.scan()

        except Exception as error:
            print(
                f"[ERROR] Application scan failed: {error}"
            )
            return False

        if not applications:
            print(
                "[ERROR] No applications detected."
            )
            return False

        valid_applications = [
            app
            for app in applications
            if isinstance(app, dict)
            and isinstance(app.get("name"), str)
        ]

        if not valid_applications:
            print(
                "[ERROR] Scanner returned no valid "
                "application entries."
            )
            return False

        # ----------------------------------------------
        # EXACT MATCH
        # ----------------------------------------------

        matched_app: Optional[Dict[str, Any]] = None

        for app in valid_applications:

            if app["name"].strip().lower() == app_name:

                matched_app = app

                print(
                    f"[INFO] Exact Match Found: {app['name']}"
                )

                break

        # ----------------------------------------------
        # FUZZY MATCH
        # ----------------------------------------------

        if matched_app is None:

            app_names = [
                app["name"]
                for app in valid_applications
            ]

            try:
                best_match = self.fuzzy_matcher.find_best_match(
                    app_name,
                    app_names
                )

            except Exception as error:
                print(
                    f"[ERROR] Fuzzy matching failed: {error}"
                )
                return False

            if not best_match:
                print(
                    f"[ERROR] Application "
                    f"'{app_name}' not found."
                )
                return False

            matched_app = next(
                (
                    app
                    for app in valid_applications
                    if app["name"] == best_match
                ),
                None
            )

            if matched_app is None:
                print(
                    "[ERROR] Matched application "
                    "data not found."
                )
                return False

            print(
                f"[INFO] Best Match Found: {best_match}"
            )

        # ----------------------------------------------
        # APPLICATION LAUNCH
        # ----------------------------------------------

        path = matched_app.get("path")

        if not path:
            print(
                "[ERROR] Application path missing."
            )
            return False

        app_type = matched_app.get(
            "type",
            "desktop"
        )

        print(f"[INFO] Launching: {path}")
        print(f"[INFO] Application Type: {app_type}")

        try:
            success = self.launcher.launch(
                path,
                app_type
            )

        except TypeError:
            try:
                success = self.launcher.launch(path)

            except Exception as error:
                print(
                    f"[ERROR] Application launch failed: {error}"
                )
                return False

        except Exception as error:
            print(
                f"[ERROR] Application launch failed: {error}"
            )
            return False

        if not success:
            print(
                "[ERROR] Failed to launch application."
            )
            return False

        return True

    # --------------------------------------------------
    # TEXT INPUT
    # --------------------------------------------------

    def run_text(self, text: str):
        """Execute ASRA using typed text instead of voice input."""

        return self.execute_command(text)

    # --------------------------------------------------
    # VOICE INPUT
    # --------------------------------------------------

    def run(self):
        """Run ASRA continuously using voice input."""

        print("[INFO] ASRA is running.")
        print("[INFO] Listening for command...")

        try:
            while True:

                try:
                    text = self.voice_engine.listen()

                except KeyboardInterrupt:
                    raise

                except Exception as error:
                    print(
                        f"[ERROR] Voice input failed: {error}"
                    )
                    print(
                        "[INFO] Listening will continue."
                    )
                    continue

                if not isinstance(text, str) or not text.strip():
                    print(
                        "[INFO] No command received."
                    )
                    continue

                self.execute_command(text)

                print(
                    "\n[INFO] Command processing finished."
                )
                print(
                    "[INFO] Listening for the next command..."
                )

        except KeyboardInterrupt:
            print(
                "\n[INFO] ASRA stopped by user."
            )

    # --------------------------------------------------
    # RESOURCE CLEANUP
    # --------------------------------------------------

    def close(self):
        """
        Release browser resources.

        This method is safe to call more than once.
        """

        if self._closed:
            return

        self._closed = True

        browser_manager = getattr(
            self,
            "browser_manager",
            None
        )

        close_method = getattr(
            browser_manager,
            "close",
            None
        )

        if callable(close_method):

            try:
                close_method()

                print(
                    "[INFO] Browser resources closed."
                )

            except Exception as error:
                print(
                    f"[WARNING] Browser cleanup failed: {error}"
                )