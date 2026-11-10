"""
ASRA Command Processor
======================

Purpose
-------
Convert English and common Hindi/Hinglish voice or text commands into
structured task dictionaries understood by ASRA's Assistant Controller.

Supported intents
-----------------
- open_application
- web_search
- web_navigate
- youtube_play
- desktop_type
- keyboard_shortcut
- desktop_action

Multi-step commands are returned as:
    {
        "intent": "multi_command",
        "tasks": [task_1, task_2, ...]
    }

Important integration note
---------------------------
The Assistant Controller must implement every emitted intent. In particular,
desktop_action requires a corresponding handler in assistant.py.
"""

import re
from typing import Any, Dict, List, Optional, Union


Command = Dict[str, Any]
ParsedTask = Union[Command, List[Command], None]


class CommandProcessor:
    """Parse English/Hinglish commands into ordered ASRA tasks."""

    APP_NAMES = [
        "visual studio code",
        "android studio",
        "microsoft edge",
        "google chrome",
        "file explorer",
        "microsoft word",
        "ms word",
        "vs code",
        "vscode",
        "notepad",
        "calculator",
        "pycharm",
        "firefox",
        "chrome",
        "brave",
        "edge",
        "word",
        "paint",
    ]

    OPEN_WORDS = (
        r"open|launch|start|run|kholo|khol|chalao|"
        r"shuru\s+karo"
    )

    SEARCH_WORDS = r"search|find|look\s+up|dhundo"
    NAVIGATION_WORDS = (
        r"go\s+to|navigate\s+to|visit|"
        r"open\s+website|website\s+kholo|"
        r"site\s+kholo|website\s+par\s+jao"
    )
    PLAY_WORDS = r"play|watch|chalao|dikhao|dekhao|lecture"
    TYPE_WORDS = r"type|write|enter|likho|likh\s+do|text\s+likho"

    # Connectors are split only when the text after the connector starts
    # another recognizable action.
    CONNECTOR_PATTERN = re.compile(
        r"\s+(?:and|aur|then|phir)\s+|[,;]\s*",
        re.IGNORECASE,
    )

    # Common names that mean opening a website rather than a desktop app.
    WEBSITE_ALIASES = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "wikipedia": "https://www.wikipedia.org",
    }

    def __init__(self) -> None:
        unique_names = sorted(
            set(self.APP_NAMES),
            key=len,
            reverse=True,
        )
        self.app_pattern = "(?:" + "|".join(
            re.escape(name) for name in unique_names
        ) + ")"

        self.action_start_pattern = re.compile(
            rf"^(?:"
            rf"{self.OPEN_WORDS}\b|"
            rf"{self.app_pattern}\s+(?:{self.OPEN_WORDS})\b|"
            rf"{self.SEARCH_WORDS}\b|"
            rf"google\s+(?:par|me)\b|"
            rf"{self.NAVIGATION_WORDS}\b|"
            rf"{self.PLAY_WORDS}\b|"
            rf"type\b|write\b|enter\b|likho\b|likh\s+do\b|"
            rf"press\b|hit\b|shortcut\b|dabao\b|"
            rf"show\s+desktop\b|desktop\s+(?:dikhao|kholo|par\s+jao)|"
            rf"minimize\b|maximize\b|switch\s+window\b|"
            rf"refresh(?:\s+desktop)?\b|"
            rf"close\s+(?:active|current)\s+window\b|"
            rf"youtube\s+(?:par|per|me)\b"
            rf")",
            re.IGNORECASE,
        )

    # ==================================================
    # PUBLIC API
    # ==================================================

    def process(self, text: str) -> Command:
        """
        Parse a complete user utterance.

        Returns:
            A single task dictionary, a multi_command dictionary,
            or an unknown-intent dictionary.
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "intent": "unknown",
                "reason": "empty_input",
            }

        normalized = self._normalize(text)
        if not normalized:
            return {
                "intent": "unknown",
                "reason": "empty_input",
            }

        segments = self._split_commands(normalized)
        tasks: List[Command] = []

        for segment in segments:
            parsed = self._parse_segment(segment)

            if parsed is None:
                print(f"[WARNING] Unsupported task segment: {segment}")
                continue

            if isinstance(parsed, list):
                tasks.extend(parsed)
            else:
                tasks.append(parsed)

        if not tasks:
            print(f"[WARNING] Could not understand command: {normalized}")
            return {
                "intent": "unknown",
                "original_text": normalized,
                "reason": "no_supported_intent",
            }

        if len(tasks) == 1:
            return tasks[0]

        return {
            "intent": "multi_command",
            "tasks": tasks,
            "source_text": normalized,
        }

    def detect_intent(self, text: str) -> Command:
        """Backward-compatible method name used by older ASRA code."""
        return self.process(text)

    # ==================================================
    # NORMALIZATION AND MULTI-COMMAND SPLITTING
    # ==================================================

    @staticmethod
    def _normalize(text: str) -> str:
        # Preserve capitalization for text that ASRA must type verbatim.
        # Parsing expressions use re.IGNORECASE where needed.
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(
            r"^(?:hey\s+)?asra[\s,:]+",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return text.strip(" .,!;")

    def _starts_new_action(self, text: str) -> bool:
        return bool(self.action_start_pattern.search(text.strip()))

    def _split_commands(self, text: str) -> List[str]:
        """
        Split only when a connector is followed by a new action.

        Examples:
            open chrome and search Python
                -> ["open chrome", "search python"]

            search cats and dogs
                -> ["search cats and dogs"]

            Chrome kholo aur YouTube par Python search karo
                -> ["chrome kholo", "youtube par python search karo"]
        """
        segments: List[str] = []
        start = 0

        for match in self.CONNECTOR_PATTERN.finditer(text):
            left = text[start:match.start()].strip(" .,!;")
            right = text[match.end():].lstrip()

            if left and right and self._starts_new_action(right):
                segments.append(left)
                start = match.end()

        tail = text[start:].strip(" .,!;")
        if tail:
            segments.append(tail)

        return segments or [text]

    # ==================================================
    # SINGLE SEGMENT ROUTER
    # ==================================================

    def _parse_segment(self, text: str) -> ParsedTask:
        text = text.strip(" .,!;")
        if not text:
            return None

        # Order matters: specific intents must be checked before generic ones.
        task = self._parse_desktop_action(text)
        if task:
            return task

        task = self._parse_shortcut(text)
        if task:
            return task

        task = self._parse_youtube(text)
        if task:
            return task

        task = self._parse_navigation(text)
        if task:
            return task

        task = self._parse_application_open(text)
        if task:
            return task

        task = self._parse_type(text)
        if task:
            return task

        task = self._parse_search(text)
        if task:
            return task

        return None

    # ==================================================
    # APPLICATION OPENING
    # ==================================================

    def _parse_application_open(self, text: str) -> Optional[Command]:
        """
        Recognize:
            open Chrome
            Chrome kholo
            VS Code start karo
        """
        open_pattern = re.compile(
            rf"\b(?:{self.OPEN_WORDS})\b",
            re.IGNORECASE,
        )

        app_match = re.search(
            rf"(?<![\w])({self.app_pattern})(?![\w])",
            text,
            re.IGNORECASE,
        )
        open_match = open_pattern.search(text)

        if app_match and open_match:
            # Do not interpret a search phrase containing an app name as launch.
            if re.search(
                rf"\b(?:{self.SEARCH_WORDS})\b",
                text,
                re.IGNORECASE,
            ):
                return None

            return {
                "intent": "open_application",
                "target": app_match.group(1).strip(),
            }

        # Website aliases such as "open Google" are browser navigation.
        website_match = re.fullmatch(
            rf"(?:{self.OPEN_WORDS})\s+"
            r"(google|youtube|gmail|facebook|instagram|wikipedia)",
            text,
            re.IGNORECASE,
        )
        if website_match:
            site = website_match.group(1).lower()
            return {
                "intent": "web_navigate",
                "url": self.WEBSITE_ALIASES[site],
            }

        return None

    # ==================================================
    # WEBSITE NAVIGATION
    # ==================================================

    def _parse_navigation(self, text: str) -> Optional[Command]:
        """
        Recognize:
            go to https://example.com
            website kholo example.com
            open example.com
        """
        url_match = re.search(
            r"(?<!@)\b(?:https?://)?(?:www\.)?"
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
            r"(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+"
            r"(?::\d{1,5})?(?:/[^\s]*)?",
            text,
            re.IGNORECASE,
        )

        if not url_match:
            return None

        has_navigation_intent = bool(
            re.search(
                rf"\b(?:{self.NAVIGATION_WORDS}|{self.OPEN_WORDS})\b",
                text,
                re.IGNORECASE,
            )
        )
        if not has_navigation_intent:
            return None

        url = url_match.group(0).rstrip(".,!?;)")
        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url

        return {
            "intent": "web_navigate",
            "url": url,
        }

    # ==================================================
    # YOUTUBE
    # ==================================================

    def _parse_youtube(self, text: str) -> Optional[Command]:
        if not re.search(r"\byoutube\b", text, re.IGNORECASE):
            return None

        is_shorts = bool(re.search(r"\bshorts?\b", text))
        has_play_intent = bool(
            re.search(rf"\b(?:{self.PLAY_WORDS})\b", text)
        )
        has_search_intent = bool(
            re.search(rf"\b(?:{self.SEARCH_WORDS})\b", text)
        )

        query = text
        query = re.sub(r"\byoutube\b", " ", query, flags=re.IGNORECASE)
        query = re.sub(
            r"\b(?:par|per|me|on|please|mujhe)\b",
            " ",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"\b(?:play|watch|chalao|dikhao|dekhao|"
            r"video|videos|lecture|lectures|"
            r"shorts?|open|khol|kholo|"
            r"search|find|look\s+up|dhundo|"
            r"karo|kar\s+do|dikha\s+do)\b",
            " ",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(r"\s+", " ", query).strip(" .,!;")

        # "open YouTube" without a query opens its home page.
        if not query and not is_shorts and not has_play_intent and not has_search_intent:
            return {
                "intent": "web_navigate",
                "url": self.WEBSITE_ALIASES["youtube"],
            }

        if not query and is_shorts:
            query = "trending"

        if not query:
            return None

        # Any query explicitly scoped to YouTube must use the YouTube
        # handler; otherwise a generic web_search would search Google.
        return {
            "intent": "youtube_play",
            "query": query,
            "content_type": "shorts" if is_shorts else "video",
        }

    # ==================================================
    # GENERAL WEB SEARCH
    # ==================================================

    def _parse_search(self, text: str) -> Optional[Command]:
        # "Google par Python tutorials search karo"
        google_match = re.match(
            r"^google\s+(?:par|me)\s+(.+?)"
            r"(?:\s+(?:search(?:\s+karo)?|dhundo|find))?$",
            text,
            re.IGNORECASE,
        )
        if google_match:
            query = self._clean_search_query(google_match.group(1))
            if query:
                return {
                    "intent": "web_search",
                    "query": query,
                }

        # "search for Python", "find Python tutorials", "look up Python"
        search_match = re.search(
            rf"\b(?:{self.SEARCH_WORDS})\s+(?:for\s+)?(.+)$",
            text,
            re.IGNORECASE,
        )
        if not search_match:
            return None

        query = self._clean_search_query(search_match.group(1))
        if not query:
            return None

        return {
            "intent": "web_search",
            "query": query,
        }

    @staticmethod
    def _clean_search_query(query: str) -> str:
        query = re.sub(
            r"\b(?:on\s+google|in\s+google|google\s+par|google\s+me|"
            r"search\s+karo|search|dhundo|please|karo|kar\s+do)\b",
            " ",
            query,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", query).strip(" .,!;")

    # ==================================================
    # DESKTOP TEXT INPUT
    # ==================================================

    def _parse_type(self, text: str) -> Optional[Command]:
        """
        Recognize:
            type Hello world
            write Hello world
            likho Hello world
        """
        match = re.search(
            rf"\b(?:{self.TYPE_WORDS})\s+(.+)$",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None

        content = match.group(1).strip(" .,!;")
        if not content:
            return None

        return {
            "intent": "desktop_type",
            "text": content,
        }

    # ==================================================
    # KEYBOARD SHORTCUTS
    # ==================================================

    def _parse_shortcut(self, text: str) -> Optional[Command]:
        """
        Recognize:
            press Ctrl+C
            hit Alt+Tab
            Ctrl+S dabao
            press Enter
        """
        key_expression = (
            r"(?:(?:ctrl|control|alt|shift|win|windows)"
            r"\s*\+\s*)+[a-z0-9]|"
            r"enter|return|tab|esc|escape|space|"
            r"backspace|delete|del|f(?:[1-9]|1[0-2])|"
            r"home|end|up|down|left|right"
        )

        match = re.search(
            rf"(?:\b(?:press|hit|shortcut|dabao)\s+)?"
            rf"({key_expression})"
            rf"(?:\s+dabao)?\b",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None

        keys = re.sub(r"\s+", "", match.group(1).lower())
        keys = keys.replace("control+", "ctrl+")
        keys = keys.replace("windows+", "win+")

        return {
            "intent": "keyboard_shortcut",
            "keys": keys,
        }

    # ==================================================
    # DESKTOP / WINDOW ACTIONS
    # ==================================================

    def _parse_desktop_action(self, text: str) -> Optional[Command]:
        patterns = [
            (
                r"\b(show\s+desktop|desktop\s+dikhao|"
                r"desktop\s+par\s+jao|desktop\s+kholo|"
                r"minimize\s+all\s+windows)\b",
                "show_desktop",
            ),
            (
                r"\b(refresh\s+desktop|desktop\s+refresh|"
                r"refresh\s+karo|refresh\s+kar\s+do|"
                r"desktop\s+ko\s+refresh\s+karo)\b",
                "refresh",
            ),
            (
                r"\b(minimize\s+window|minimize\s+karo)\b",
                "minimize",
            ),
            (
                r"\b(maximize\s+window|maximize\s+karo)\b",
                "maximize",
            ),
            (
                r"\b(switch\s+window|next\s+window|"
                r"window\s+switch\s+karo)\b",
                "switch_window",
            ),
            (
                r"\b(close\s+active\s+window|"
                r"active\s+window\s+band\s+karo|"
                r"current\s+window\s+band\s+karo)\b",
                "close_active_window",
            ),
        ]

        for pattern, action in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "intent": "desktop_action",
                    "action": action,
                }

        return None
