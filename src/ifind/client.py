from typing import Any, Dict, Optional

import requests

from src.ifind.auth import IFindAuthProvider


class IFindAPIError(RuntimeError):
    """Raised when the iFinD API reports an application-level error."""


class IFindClient:
    def __init__(
        self,
        auth_provider: IFindAuthProvider,
        base_url: str = "https://quantapi.51ifind.com/api/v1",
        timeout: float = 20.0,
        language: str = "cn",
        session: Optional[requests.Session] = None,
    ):
        self.auth_provider = auth_provider
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.language = language
        self.session = session or requests.Session()

    def smart_stock_picking(self, searchstring: str, searchtype: str = "stock") -> Dict[str, Any]:
        return self._post(
            "/smart_stock_picking",
            {
                "searchstring": searchstring,
                "searchtype": searchtype,
            },
        )

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        access_token = self.auth_provider.get_access_token()
        response = self.session.post(
            f"{self.base_url}{path}",
            headers={
                "Content-Type": "application/json",
                "access_token": access_token,
                "ifindlang": self.language,
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("errorcode") not in (None, 0):
            raise IFindAPIError(data.get("errmsg") or f"iFinD request failed: {data.get('errorcode')}")
        return data
