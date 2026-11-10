"""
Voice Engine
Speech to Text using SpeechRecognition
"""

import speech_recognition as sr


class VoiceEngine:

    def __init__(self):
        self.recognizer = sr.Recognizer()

        # Better speech detection
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.8

    def listen(self):

        try:
            with sr.Microphone() as source:
                print("=" * 50)
                print(" Adjusting for background noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)

                print("Speak now...")

                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )

           

            text = self.recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            print(f"You said: {text}")
            return text

        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None

        except sr.UnknownValueError:
            print(" Could not understand the audio.")
            return None

        except sr.RequestError as e:
            print(f" Google Speech Recognition Error: {e}")
            return None

        except Exception as e:
            print(f" Unexpected Error: {e}")
            return None


if __name__ == "__main__":
    engine = VoiceEngine()

    while True:
        text = engine.listen()

        if text:
            print("Recognized:", text)

        choice = input("\nPress Enter to continue or type 'q' to quit: ")

        if choice.lower() == "q":
            break