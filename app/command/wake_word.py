class WakeWordRemover:
    # Removes wake words from user commands.

    def __init__(self):
        self.wake_words = [
            "hey asra",
            "hi asra",
            "hello asra",
            "ok asra",
            "asra"
        ]

    def remove(self, text: str) -> str:

        cleaned_text = text

        for wake_word in self.wake_words:
            cleaned_text = cleaned_text.replace(wake_word, "")

        cleaned_text = " ".join(cleaned_text.split())

        return cleaned_text