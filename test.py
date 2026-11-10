
from app.core.assistant import AsraAssistant


def main():
    assistant = AsraAssistant()

    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n[INFO] ASRA stopped by user.")
    except Exception as error:
        print(f"[ERROR] ASRA failed: {error}")


if __name__ == "__main__":
    main()
