from pathlib import Path
from types import SimpleNamespace

from justice_plutus.cli import _resolve_stock_codes
from src.config import Config, openai_params_for_key


def _load_config(monkeypatch, **env):
    tracked_keys = [
        "ENV_FILE",
        "AIHUBMIX_KEY",
        "OPENAI_API_KEY",
        "OPENAI_API_KEYS",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "LITELLM_MODEL",
        "LITELLM_FALLBACK_MODELS",
        "GEMINI_API_KEY",
        "GEMINI_API_KEYS",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_API_KEYS",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_API_KEYS",
        "STOCK_LIST",
        "IFIND_REFRESH_TOKEN",
        "ENABLE_THS_PRO_DATA",
        "ENABLE_IFIND",
        "ENABLE_IFIND_ANALYSIS_ENHANCEMENT",
        "APPEND_IMAGE_AFTER_TEXT_NOTIFY",
    ]
    for key in tracked_keys:
        monkeypatch.delenv(key, raising=False)

    # Isolate tests from repository .env values.
    monkeypatch.setenv("ENV_FILE", "/tmp/__justice_plutus_test_env__")
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    Config.reset_instance()
    return Config._load_from_env()


def test_openai_keys_keep_order_aihubmix_then_openai(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        AIHUBMIX_KEY="mix-key-12345678",
        OPENAI_API_KEY="openai-key-87654321",
        OPENAI_MODEL="gemini-flash-lite-latest",
    )
    assert cfg.openai_api_keys == ["mix-key-12345678", "openai-key-87654321"]
    assert cfg.openai_api_key == "mix-key-12345678"


def test_openai_keys_deduplicate(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        AIHUBMIX_KEY="same-key-12345678",
        OPENAI_API_KEY="same-key-12345678",
        OPENAI_MODEL="gemini-flash-lite-latest",
    )
    assert cfg.openai_api_keys == ["same-key-12345678"]


def test_empty_openai_model_never_builds_invalid_openai_prefix(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        OPENAI_API_KEY="openai-key-87654321",
        OPENAI_MODEL="",
    )
    assert cfg.litellm_model == "openai/gpt-4o-mini"


def test_openai_params_for_key_prefers_aihubmix_then_official(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        AIHUBMIX_KEY="mix-key-12345678",
        OPENAI_API_KEY="openai-key-87654321",
        OPENAI_MODEL="gemini-flash-lite-latest",
    )

    primary = openai_params_for_key("mix-key-12345678", cfg)
    assert primary.get("api_base") == "https://aihubmix.com/v1"
    assert primary.get("extra_headers") == {"APP-Code": "GPIJ3886"}

    fallback = openai_params_for_key("openai-key-87654321", cfg)
    assert fallback == {}


def test_refresh_stock_list_prefers_env_file_over_environment(monkeypatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("STOCK_LIST=600519,000001\n", encoding="utf-8")

    cfg = _load_config(
        monkeypatch,
        ENV_FILE=str(env_file),
        STOCK_LIST="300750,002594",
    )
    cfg.refresh_stock_list()
    assert cfg.stock_list == ["600519", "000001"]


def test_refresh_stock_list_falls_back_to_environment_when_env_file_missing(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        ENV_FILE="/tmp/__missing_justice_plutus_env__",
        STOCK_LIST="300750,002594",
    )
    cfg.refresh_stock_list()
    assert cfg.stock_list == ["300750", "002594"]


def test_cli_stocks_arg_overrides_config_stock_list():
    args = SimpleNamespace(stocks="600519,000001,600519")

    class DummyConfig:
        stock_list = ["300750"]

        def refresh_stock_list(self):
            raise AssertionError("refresh_stock_list should not be called when --stocks is provided")

    result = _resolve_stock_codes(args, DummyConfig())
    assert result == ["600519", "000001"]


def test_cli_uses_config_stock_list_without_stocks_arg():
    args = SimpleNamespace(stocks=None)

    class DummyConfig:
        def __init__(self):
            self.stock_list = ["000001"]
            self.refresh_called = False

        def refresh_stock_list(self):
            self.refresh_called = True
            self.stock_list = ["600519", "000001"]

    cfg = DummyConfig()
    result = _resolve_stock_codes(args, cfg)
    assert cfg.refresh_called is True
    assert result == ["600519", "000001"]


def test_ifind_flags_default_to_disabled(monkeypatch):
    cfg = _load_config(monkeypatch)

    assert cfg.ifind_refresh_token is None
    assert cfg.enable_ifind is False
    assert cfg.enable_ifind_analysis_enhancement is False


def test_ifind_flags_and_refresh_token_are_loaded(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        IFIND_REFRESH_TOKEN="refresh-token-demo",
        ENABLE_IFIND="true",
        ENABLE_IFIND_ANALYSIS_ENHANCEMENT="true",
    )

    assert cfg.ifind_refresh_token == "refresh-token-demo"
    assert cfg.enable_ifind is True
    assert cfg.enable_ifind_analysis_enhancement is True


def test_ths_pro_data_master_switch_enables_professional_mode(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        ENABLE_THS_PRO_DATA="true",
        IFIND_REFRESH_TOKEN="refresh-token-demo",
    )

    assert cfg.enable_ths_pro_data is True
    assert cfg.is_ths_pro_data_enabled() is True
    assert cfg.is_ifind_financial_enhancement_enabled() is True


def test_legacy_ifind_flags_still_enable_legacy_mode(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        ENABLE_IFIND="true",
        ENABLE_IFIND_ANALYSIS_ENHANCEMENT="false",
    )

    assert cfg.enable_ths_pro_data is False
    assert cfg.is_ths_pro_data_enabled() is True
    assert cfg.is_ifind_financial_enhancement_enabled() is False


def test_append_image_after_text_notify_defaults_to_disabled(monkeypatch):
    cfg = _load_config(monkeypatch)

    assert cfg.append_image_after_text_notify is False


def test_append_image_after_text_notify_can_be_enabled(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        APPEND_IMAGE_AFTER_TEXT_NOTIFY="true",
    )

    assert cfg.append_image_after_text_notify is True
