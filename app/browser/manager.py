
"""
ASRA AI Browser Manager.

Opens Chrome and performs YouTube searches while
reusing the browser session across multiple tasks.
"""

from pathlib import Path
from urllib.parse import quote_plus
from urllib.parse import quote_plus, urlparse

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


class BrowserManager:
    """Manage a reusable browser session for ASRA AI."""

    def __init__(self):
        self.profile_dir = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "browser_profile"
        )

        self.playwright = None
        self.context = None

    def _ensure_browser(self):
        """Start the browser if no usable session exists."""

        if self.context is not None:
            try:
                if not self.context.pages:
                    self.context.new_page()

                return self.context
            except Exception:
                self.context = None

        self.profile_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.playwright is None:
            self.playwright = sync_playwright().start()

        self.context = (
            self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                channel="chrome",
                headless=False,
            )
        )

        return self.context

    def search_youtube(self, query: str) -> bool:
        """Open YouTube search results without closing the session."""

        query = query.strip()

        if not query:
            print("[ERROR] Search query cannot be empty.")
            return False

        try:
            context = self._ensure_browser()

            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            search_url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print("[SUCCESS] YouTube search page opened.")
            print(f"[INFO] Search query: {query}")

            return True

        except PlaywrightTimeoutError:
            print("[ERROR] Browser navigation timed out.")
            return False

        except Exception as error:
            print(
                f"[ERROR] Browser automation failed: {error}"
            )

            # A later task can try creating a fresh session.
            self.context = None
            return False

    
    def play_youtube(self, query: str, content_type: str = "video") -> bool:
        """Search YouTube and open the first matching video or Short."""

        query = query.strip()

        if content_type == "shorts":
            query = f"{query} shorts".strip()

        if not query:
            query = "trending shorts" if content_type == "shorts" else "popular videos"

        try:
            context = self._ensure_browser()
            page = context.pages[0] if context.pages else context.new_page()

            search_url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            if content_type == "shorts":
                shorts_link = page.locator(
                    'a[href*="/shorts/"]'
                ).first

                try:
                    shorts_link.wait_for(
                        state="visible",
                        timeout=12000,
                    )
                    shorts_link.click(timeout=10000)
                    print("[SUCCESS] Opened a YouTube Short.")
                    return True
                except PlaywrightTimeoutError:
                    print(
                        "[WARNING] A Shorts result was not found; "
                        "trying the first video result."
                    )

            video_link = page.locator(
                "ytd-video-renderer a#thumbnail"
            ).first

            video_link.wait_for(
                state="visible",
                timeout=15000,
            )
            video_link.click(timeout=10000)

            page.wait_for_timeout(2000)

            print("[SUCCESS] Opened a YouTube video.")
            print(f"[INFO] Search query: {query}")
            return True

        except Exception as error:
            print(f"[ERROR] Could not open YouTube content: {error}")
            return False
    
    def _get_page(self):
        """Return the active page, creating a browser session if needed."""
        context = self._ensure_browser()
        return context.pages[0] if context.pages else context.new_page()

    def search_web(self, query: str) -> bool:
        """Search the web using Google in the persistent browser session."""
        query = query.strip()

        if not query:
            print("[ERROR] Web search query cannot be empty.")
            return False

        try:
            page = self._get_page()
            url = "https://www.google.com/search?q=" + quote_plus(query)

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print(f"[SUCCESS] Google search opened: {query}")
            return True

        except Exception as error:
            print(f"[ERROR] Web search failed: {error}")
            return False

    def navigate_to(self, url: str) -> bool:
        """Navigate the managed browser to a website URL."""
        url = url.strip()

        if not url:
            print("[ERROR] Website URL cannot be empty.")
            return False

        if not url.startswith(("https://", "http://")):
            url = "https://" + url

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            print("[ERROR] Invalid website URL.")
            return False

        try:
            page = self._get_page()
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print(f"[SUCCESS] Website opened: {url}")
            return True

        except Exception as error:
            print(f"[ERROR] Website navigation failed: {error}")
            return False

    def click_element(self, selector: str) -> bool:
        """Click a webpage element using a Playwright selector."""
        selector = selector.strip()

        if not selector:
            print("[ERROR] Element selector is missing.")
            return False

        try:
            page = self._get_page()
            page.locator(selector).first.click(timeout=10000)
            print(f"[SUCCESS] Clicked webpage element: {selector}")
            return True

        except Exception as error:
            print(f"[ERROR] Webpage click failed: {error}")
            return False

    def type_into_element(self, selector: str, text: str) -> bool:
        """Fill a webpage input or editable element."""
        if not selector.strip():
            print("[ERROR] Input selector is missing.")
            return False

        try:
            page = self._get_page()
            page.locator(selector).first.fill(text, timeout=10000)
            print("[SUCCESS] Text entered into webpage element.")
            return True

        except Exception as error:
            print(f"[ERROR] Webpage typing failed: {error}")
            return False

    def close(self):
        """Close browser resources when ASRA shuts down."""
        print("[INFO] Closing ASRA browser session...")
        
        if self.context is not None:
            try:
                self.context.close()
            except Exception as error:
                print(f"[WARNING] Browser close error: {error}")
            finally:
                self.context = None

        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception as error:
                print(f"[WARNING] Playwright stop error: {error}")
            finally:
                self.playwright = None
