import time
from typing import Optional, Tuple

import requests


class IFindAuthProvider:
    TOKEN_URL = "https://quantapi.51ifind.com/api/v1/get_access_token"

    def __init__(self, refresh_token: str, timeout: float = 20.0, session: Optional[requests.Session] = None):
        self.refresh_token = refresh_token
        self.timeout = timeout
        self.session = session or requests.Session()
        self._cached_token: Optional[str] = None
        self._expires_at: float = 0.0

    def get_access_token(self) -> str:
        if not self.refresh_token:
            raise ValueError("iFinD refresh token is required before requesting access token")
        if self._cached_token and time.time() < self._expires_at:
            return self._cached_token

        token, expires_in = self._exchange_token()
        self._cached_token = token
        self._expires_at = time.time() + max(expires_in - 60, 60)
        return token

    def _exchange_token(self) -> Tuple[str, int]:
        response = self.session.post(
            self.TOKEN_URL,
            headers={
                "Content-Type": "application/json",
                "refresh_token": self.refresh_token,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        token = data.get("access_token")
        if not token:
            raise RuntimeError(payload.get("errmsg") or "iFinD access token exchange failed")
        expires_in = int(data.get("expires_in") or data.get("expiresIn") or 1800)
        return token, expires_in
