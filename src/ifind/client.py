from typing import Any, Dict, Optional

import requests

from src.ifind.auth import IFindAuthProvider


class IFindAPIError(RuntimeError):
    """Raised when the iFinD API reports an application-level error."""


_ETF_SH_PREFIXES = ("50", "51", "52", "56", "58")
_ETF_SZ_PREFIXES = ("15", "16", "18")


def _is_bse_code(code: str) -> bool:
    return len(code) == 6 and code.isdigit() and code.startswith(("4", "8", "92"))


class IFindClient:
    HISTORY_INDICATORS = "open,high,low,close,volume,amount,changeRatio"
    REALTIME_INDICATORS = (
        "open,high,low,latest,changeRatio,change,preClose,"
        "volume,amount,turnoverRatio,volumeRatio,amplitude,pb"
    )

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

    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> Dict[str, Any]:
        return self._post(
            "/cmd_history_quotation",
            {
                "codes": self._to_ifind_code(stock_code),
                "indicators": self.HISTORY_INDICATORS,
                "startdate": start_date,
                "enddate": end_date,
            },
        )

    def get_realtime_quote(self, stock_code: str) -> Dict[str, Any]:
        return self._post(
            "/real_time_quotation",
            {
                "codes": self._to_ifind_code(stock_code),
                "indicators": self.REALTIME_INDICATORS,
            },
        )

    def _to_ifind_code(self, stock_code: str) -> str:
        code = (stock_code or "").strip().upper()
        if not code or code.startswith("__"):
            return code
        if "." in code:
            return code
        if code.startswith(("SH", "SZ", "BJ")) and code[2:].isdigit():
            return f"{code[2:]}.{code[:2]}"
        if not code.isdigit() or len(code) != 6:
            return code
        if code.startswith(_ETF_SH_PREFIXES):
            return f"{code}.SH"
        if code.startswith(_ETF_SZ_PREFIXES):
            return f"{code}.SZ"
        if _is_bse_code(code):
            return f"{code}.BJ"
        if code.startswith(("600", "601", "603", "605", "688")):
            return f"{code}.SH"
        return f"{code}.SZ"

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
