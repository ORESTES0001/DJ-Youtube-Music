import json
import os
import threading
from pathlib import Path

import ytmusicapi
from PySide6.QtCore import QObject, Signal


_BROWSER_FILE = "browser.json"


def _init_with_timeout(*args, timeout=10):
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = ytmusicapi.YTMusic(*args)
        except Exception as e:
            exception[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError("ytmusicapi.YTMusic init timed out")
    if exception[0]:
        raise exception[0]
    return result[0]


class GoogleAuthService(QObject):
    login_success = Signal()
    logout_success = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = ytmusicapi.YTMusic()
        self._user_info = None
        self._has_auth = False
        browser_path = self.filepath
        if os.path.exists(browser_path):
            try:
                self._api = _init_with_timeout(browser_path, timeout=10)
                self._has_auth = True
                self._refresh_user_name()
                print("[AUTH] Loaded session from browser.json")
            except Exception as e:
                print(f"❌ [AUTH SERVICE ERROR] {e}")
                self._fallback_to_public()

    def _fetch_user_name(self) -> str:
        try:
            if hasattr(self._api, 'get_account_info'):
                info = self._api.get_account_info()
                if info and isinstance(info, dict):
                    return info.get("accountName") or info.get("channelName") or "Oyente"
        except Exception:
            pass
        return "Oyente"

    def _refresh_user_name(self):
        self._user_info = {"display_name": self._fetch_user_name()}

    @property
    def is_authenticated(self) -> bool:
        return self._has_auth

    @property
    def user_display_name(self) -> str:
        if self._user_info:
            return self._user_info.get("display_name", "Oyente")
        return "Oyente"

    @property
    def api(self):
        return self._api

    @staticmethod
    def _root() -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def filepath(self) -> str:
        return str(GoogleAuthService._root() / _BROWSER_FILE)

    @staticmethod
    def _browser_path() -> str:
        return str(GoogleAuthService._root() / _BROWSER_FILE)

    @staticmethod
    def get_auth_instructions() -> str:
        return (
            "To authenticate with YouTube Music:\n\n"
            "1. Open Chrome and go to https://music.youtube.com\n"
            "2. Press F12 to open DevTools, go to the Network tab\n"
            "3. Refresh the page and click on any POST request\n"
            "4. Right-click the request -> Copy as cURL\n"
            "5. Paste the full cURL command below\n\n"
            "Your session cookies are stored locally and never sent anywhere."
        )

    def initialize_from_cookies(self, cookies: dict) -> bool:
        cookie_str = cookies.get("cookie_str", "")
        if not cookie_str:
            return False
        browser_data = [
            {
                "cookies": cookie_str,
                "x-goog-authuser": cookies.get("x-goog-authuser", "0"),
                "authorization": cookies.get("authorization", ""),
                "user-agent": cookies.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ),
            }
        ]
        browser_path = self._browser_path()
        try:
            with open(browser_path, "w") as f:
                json.dump(browser_data, f, indent=2)
        except OSError:
            return False
        try:
            self._api = _init_with_timeout(browser_path, timeout=10)
            self._refresh_user_name()
            self._has_auth = True
            return True
        except Exception as e:
            print(f"❌ [AUTH SERVICE ERROR] {e}")
            self._fallback_to_public()
            return False

    def _fallback_to_public(self, reason: str = ""):
        msg = reason or "Cookie auth failed, falling back to Public Mode."
        print(f"[AUTH] {msg}")
        self._api = ytmusicapi.YTMusic()
        self._user_info = None
        self._has_auth = False

    def try_restore_session(self) -> bool:
        browser_path = self._browser_path()
        if not os.path.exists(browser_path):
            print(f"[AUTH] No session file at {browser_path}")
            return False
        try:
            self._api = _init_with_timeout(browser_path, timeout=10)
            self._refresh_user_name()
            self._has_auth = True
            print(f"[AUTH] Session restored from {browser_path}")
            return True
        except Exception as e:
            print(f"❌ [AUTH SERVICE ERROR] try_restore_session: {e}")
            self._fallback_to_public()
            return False

    def initialize_from_headers(self, headers_raw: str) -> bool:
        try:
            clean = headers_raw.replace('\r\n', '\n')
            lower = clean.lower()
            browser_path = self._browser_path()

            if 'cookie:' in lower and 'x-goog-authuser:' in lower:
                cookie = self._grab(clean, 'cookie')
                authuser = self._grab(clean, 'x-goog-authuser')
                ua = self._grab(clean, 'user-agent') or \
                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                browser_data = [{
                    "cookies": cookie,
                    "x-goog-authuser": authuser,
                    "authorization": "",
                    "user-agent": ua,
                }]
                with open(browser_path, "w") as f:
                    json.dump(browser_data, f, indent=2)
            else:
                ytmusicapi.setup(browser_path, clean)

            self._api = _init_with_timeout(browser_path, timeout=10)
            self._api.get_library_playlists(limit=1)
            self._refresh_user_name()
            self._has_auth = True
            self.login_success.emit()
            return True
        except Exception as e:
            print(f"❌ [AUTH SERVICE ERROR] {e}")
            self._fallback_to_public()
            return False

    @staticmethod
    def _grab(text: str, name: str) -> str:
        import re
        pat = re.compile(
            r"-H\s+['\"]?" + re.escape(name) + r":\s*([^'\"\\\n]+)",
            re.IGNORECASE
        )
        m = pat.search(text)
        if m:
            return m.group(1).strip().rstrip("'\"")
        for line in text.split('\n'):
            if line.lower().lstrip().startswith(name.lower() + ':'):
                _, val = line.split(':', 1)
                return val.strip()
        return ""

    def logout(self) -> None:
        browser_path = self._browser_path()
        if os.path.exists(browser_path):
            try:
                os.remove(browser_path)
            except OSError:
                pass
        self._fallback_to_public("User logged out, returning to Public Mode.")
        self.logout_success.emit()
