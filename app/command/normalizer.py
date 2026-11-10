# regular expression 
import re


class TextNormalizer:
 
    def normalize(self, text: str) -> str:
     
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation
        text = re.sub(r"[^\w\s]", "", text)

        # Remove extra spaces
        text = " ".join(text.split())

        return text