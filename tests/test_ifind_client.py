from src.ifind.client import IFindClient


class _StaticAuthProvider:
    def get_access_token(self):
        return "access-demo"


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _RecordingSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return _FakeResponse(self.payload)


def test_client_calls_history_quotation_endpoint_with_normalized_code():
    session = _RecordingSession(
        {
            "errorcode": 0,
            "tables": [{"thscode": "600519.SH", "time": ["2026-03-31"], "table": {"close": [1450.0]}}],
        }
    )
    client = IFindClient(auth_provider=_StaticAuthProvider(), session=session)

    payload = client.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31")

    assert payload["tables"][0]["thscode"] == "600519.SH"
    assert session.calls == [
        {
            "url": "https://quantapi.51ifind.com/api/v1/cmd_history_quotation",
            "headers": {
                "Content-Type": "application/json",
                "access_token": "access-demo",
                "ifindlang": "cn",
            },
            "json": {
                "codes": "600519.SH",
                "indicators": "open,high,low,close,volume,amount,changeRatio",
                "startdate": "2026-03-01",
                "enddate": "2026-03-31",
            },
            "timeout": 20.0,
        }
    ]


def test_client_calls_realtime_quotation_endpoint_with_official_indicators():
    session = _RecordingSession(
        {
            "errorcode": 0,
            "tables": [{"thscode": "000001.SZ", "time": ["2026-04-01 15:00:00"], "table": {"latest": [12.34]}}],
        }
    )
    client = IFindClient(auth_provider=_StaticAuthProvider(), session=session)

    payload = client.get_realtime_quote("000001")

    assert payload["tables"][0]["thscode"] == "000001.SZ"
    assert session.calls == [
        {
            "url": "https://quantapi.51ifind.com/api/v1/real_time_quotation",
            "headers": {
                "Content-Type": "application/json",
                "access_token": "access-demo",
                "ifindlang": "cn",
            },
            "json": {
                "codes": "000001.SZ",
                "indicators": "open,high,low,latest,changeRatio,change,preClose,volume,amount,turnoverRatio,volumeRatio,amplitude,pb",
            },
            "timeout": 20.0,
        }
    ]
