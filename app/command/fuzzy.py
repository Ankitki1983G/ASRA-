"""
ASRA Fuzzy Matcher

Safely finds the closest application name.
"""

from difflib import SequenceMatcher


class FuzzyMatcher:

    def normalize(self, text: str) -> str:
        """
        Normalize application names.
        """

        text = text.lower().strip()

        # Remove common separators/spaces
        text = (
            text
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .replace(".", "")
        )

        return text

    def similarity(
        self,
        target: str,
        candidate: str
    ) -> float:
        """
        Calculate similarity between target
        and candidate.
        """

        target = self.normalize(target)
        candidate = self.normalize(candidate)

        return SequenceMatcher(
            None,
            target,
            candidate
        ).ratio()

    def find_best_match(
        self,
        target: str,
        available_apps: list
    ) -> str | None:
        """
        Find the safest closest application.

        Returns None when confidence is too low.
        """

        if not target:
            return None

        if not available_apps:
            return None

        best_match = None
        best_score = 0.0

        for app in available_apps:

            score = self.similarity(
                target,
                app
            )

            if score > best_score:

                best_score = score
                best_match = app

        print(
            f"[Fuzzy] {target} -> "
            f"{best_match} "
            f"(score={best_score:.2f})"
        )

        # ---------------------------------
        # SAFETY THRESHOLD
        # ---------------------------------

        if best_score < 0.70:

            return None

        return best_match