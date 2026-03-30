import pytest

from src.ifind.auth import IFindAuthProvider


def test_auth_provider_reuses_cached_access_token(monkeypatch):
    provider = IFindAuthProvider(refresh_token="rt-demo")
    calls = []

    def fake_exchange():
        calls.append("exchange")
        return "access-1", 3600

    monkeypatch.setattr(provider, "_exchange_token", fake_exchange)

    assert provider.get_access_token() == "access-1"
    assert provider.get_access_token() == "access-1"
    assert calls == ["exchange"]


def test_auth_provider_requires_refresh_token():
    provider = IFindAuthProvider(refresh_token="")

    with pytest.raises(ValueError, match="refresh token"):
        provider.get_access_token()
