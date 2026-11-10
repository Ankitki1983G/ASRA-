
from app.core.assistant import AsraAssistant


def main():
    assistant = AsraAssistant()

    try:
        assistant.run()

    except KeyboardInterrupt:
        print("\n[INFO] ASRA stopped by user.")

    except Exception as error:
        print(f"[ERROR] ASRA failed: {error}")

    finally:
        browser_manager = getattr(assistant, "browser_manager", None)

        if browser_manager:
            try:
                browser_manager.close()
                print("[INFO] Browser resources closed.")

            except Exception as error:
                print(f"[WARNING] Browser cleanup failed: {error}")


if __name__ == "__main__":
    main()
