class GoogleAuthService:
    def __init__(self):
        self._token = None
        self._user_info = None

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def user_display_name(self) -> str:
        if self._user_info:
            return self._user_info.get("display_name", "User")
        return "User"

    def authenticate(self, auth_code: str = "") -> bool:
        self._token = {"access_token": "stub", "refresh_token": "stub"}
        self._user_info = {
            "google_id": "stub-google-id",
            "email": "user@example.com",
            "display_name": "Stub User",
        }
        return True

    def refresh_token(self) -> bool:
        if not self._token:
            return False
        return True

    def get_user_id(self) -> str | None:
        if self._user_info:
            return self._user_info.get("google_id")
        return None
