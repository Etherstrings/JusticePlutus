# -*- coding: utf-8 -*-
"""
===================================
HSCloudFetcher - HS 云筹码数据源
===================================

仅用于筹码分布获取，不参与日线/实时行情主路径。
"""

import logging
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.config import get_config
from .base import BaseFetcher, normalize_stock_code
from .realtime_types import ChipDistribution, safe_float

logger = logging.getLogger(__name__)


def _is_etf_code(stock_code: str) -> bool:
    """判断是否为 ETF/指数基金代码。"""
    etf_prefixes = ("51", "52", "56", "58", "15", "16", "18")
    return stock_code.startswith(etf_prefixes) and len(stock_code) == 6


def _is_us_code(stock_code: str) -> bool:
    """判断是否为美股代码。"""
    code = (stock_code or "").strip().upper()
    if not code:
        return False
    if len(code) == 6 and code.isdigit():
        return False
    return code[0].isalpha()


def _normalize_ratio(val: Any) -> float:
    """
    将不同量纲的比例值统一到 0-1。

    兼容常见返回：
    - 0~1（无需转换）
    - 0~100（百分比）
    - 0~10000（万分比）
    """
    v = safe_float(val, 0.0) or 0.0
    if v <= 1:
        return float(v)
    if v <= 100:
        return float(v) / 100.0
    if v <= 10000:
        return float(v) / 10000.0
    return float(v)


class HSCloudFetcher(BaseFetcher):
    """HS Cloud 筹码数据抓取器。"""

    name = "HSCloudFetcher"
    priority = 90  # 不参与主数据源优先级，仅用于筹码分布降级链

    def __init__(self) -> None:
        cfg = get_config()

        self.base_url = (
            (getattr(cfg, "hscloud_base_url", "") or "").strip()
            or "https://sandbox.hscloud.cn"
        ).rstrip("/")
        self.auth_token = (getattr(cfg, "hscloud_auth_token", "") or "").strip()
        self.cookie = (getattr(cfg, "hscloud_cookie", "") or "").strip()
        self.timeout = max(1.0, float(getattr(cfg, "hscloud_timeout_seconds", 8)))
        self.app_key = (getattr(cfg, "hscloud_app_key", "") or "").strip()
        self.app_secret = (getattr(cfg, "hscloud_app_secret", "") or "").strip()
        self.session = requests.Session()

    @property
    def enabled(self) -> bool:
        """是否已配置可用鉴权信息。"""
        return bool(self.auth_token or self.cookie or (self.app_key and self.app_secret))

    # --- BaseFetcher abstract methods (unused in this fetcher) ---
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame()

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        return df

    # --- Chip distribution path ---
    def get_chip_distribution(self, stock_code: str) -> Optional[ChipDistribution]:
        """
        获取筹码分布（HSCloud）。

        接口：POST /quote/v2/qplus/cost_distribution/get_stock_chip
        """
        stock_code = normalize_stock_code(stock_code)

        if not self.enabled:
            logger.debug("[HSCloud筹码] 未配置 HSCLOUD_AUTH_TOKEN/HSCLOUD_COOKIE/HSCLOUD_APP_KEY+SECRET，跳过")
            return None

        # 若未显式配置 token，尝试用 app_key/app_secret 自动换取
        self._ensure_access_token()

        if _is_us_code(stock_code):
            logger.debug("[HSCloud筹码] %s 为美股代码，跳过", stock_code)
            return None
        if _is_etf_code(stock_code):
            logger.debug("[HSCloud筹码] %s 为 ETF/指数，跳过", stock_code)
            return None

        hq_type_code = self._infer_hq_type_code(stock_code)
        if not hq_type_code:
            logger.debug("[HSCloud筹码] %s 无法识别市场类型，跳过", stock_code)
            return None

        endpoint = f"{self.base_url}/quote/v2/qplus/cost_distribution/get_stock_chip"
        headers = self._build_headers()
        payload_candidates = self._build_payload_candidates(stock_code, hq_type_code)

        for idx, payload in enumerate(payload_candidates, start=1):
            try:
                data = self._post_json(endpoint, payload, headers=headers)
            except Exception as e:
                # token 失效时，若有 app_key/app_secret，尝试刷新一次
                if self._is_invalid_token_error(e):
                    if self._refresh_access_token():
                        headers = self._build_headers()
                        try:
                            data = self._post_json(endpoint, payload, headers=headers)
                            chip = self._parse_chip_from_response(stock_code, data)
                            if chip is not None:
                                logger.info("[HSCloud筹码] %s 获取成功（token已自动刷新）", stock_code)
                                return chip
                        except Exception as refresh_err:
                            logger.warning("[HSCloud筹码] %s 刷新 token 后仍失败: %s", stock_code, refresh_err)
                logger.warning("[HSCloud筹码] %s 请求失败(尝试%d/%d): %s", stock_code, idx, len(payload_candidates), e)
                continue

            chip = self._parse_chip_from_response(stock_code, data)
            if chip is not None:
                logger.info("[HSCloud筹码] %s 获取成功", stock_code)
                return chip

        logger.warning("[HSCloud筹码] %s 获取失败（所有请求体均无有效返回）", stock_code)
        return None

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

        if self.auth_token:
            token = self.auth_token
            if token.lower().startswith("bearer "):
                headers["Authorization"] = token
            else:
                headers["Authorization"] = f"Bearer {token}"

        if self.cookie:
            headers["Cookie"] = self.cookie

        return headers

    def _ensure_access_token(self) -> None:
        if self.auth_token:
            return
        self._refresh_access_token()

    def _refresh_access_token(self) -> bool:
        if not (self.app_key and self.app_secret):
            return False

        token_url = f"{self.base_url}/oauth2/oauth2/token"
        basic = base64.b64encode(f"{self.app_key}:{self.app_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"grant_type": "client_credentials"}

        try:
            resp = self.session.post(token_url, headers=headers, data=data, timeout=self.timeout)
            resp.raise_for_status()
            obj = resp.json()
            token = str(obj.get("access_token", "")).strip()
            if not token:
                logger.warning("[HSCloud筹码] oauth2/token 未返回 access_token")
                return False
            self.auth_token = token
            logger.info("[HSCloud筹码] 已自动获取新的 access_token")
            return True
        except Exception as e:
            logger.warning("[HSCloud筹码] 自动获取 access_token 失败: %s", e)
            return False

    @staticmethod
    def _is_invalid_token_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return "401" in text or "invalid_token" in text or "访问令牌无效" in text

    def _post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("HSCloud response is not JSON object")
        return data

    @staticmethod
    def _infer_hq_type_code(stock_code: str) -> Optional[str]:
        if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
            return None
        if stock_code.startswith(("6", "5", "9")):
            return "XSHG"
        if stock_code.startswith(("0", "1", "2", "3")):
            return "XSHE"
        if stock_code.startswith(("8", "4", "92")):
            return "XBSE"
        return None

    @staticmethod
    def _build_payload_candidates(stock_code: str, hq_type_code: str) -> List[Dict[str, Any]]:
        """
        多形态请求体兜底，避免接口参数定义歧义导致失败。
        """
        return [
            {
                "prod_code_obj_grp": [
                    {"prod_code": stock_code, "hq_type_code": hq_type_code}
                ]
            },
            {
                "prod_code_obj_grp": {
                    "prod_code": [stock_code],
                    "hq_type_code": [hq_type_code],
                }
            },
            {
                "prod_code_obj_grp": {
                    "prod_code": stock_code,
                    "hq_type_code": hq_type_code,
                }
            },
        ]

    @staticmethod
    def _pick_target_record(stock_code: str, records: Any) -> Optional[Dict[str, Any]]:
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list) or not records:
            return None

        target = None
        for item in records:
            if not isinstance(item, dict):
                continue
            code = normalize_stock_code(str(item.get("prod_code", "")).strip())
            if code == stock_code:
                target = item
                break
            if target is None:
                target = item
        return target

    @classmethod
    def _parse_chip_from_response(cls, stock_code: str, data: Dict[str, Any]) -> Optional[ChipDistribution]:
        if not isinstance(data, dict):
            return None

        error_no = str(data.get("error_no", "")).strip()
        if error_no and error_no.upper() != "OK":
            logger.debug("[HSCloud筹码] 返回错误: error_no=%s, error_info=%s", error_no, data.get("error_info", ""))
            return None

        record = cls._pick_target_record(stock_code, data.get("chip_grp"))
        if not record:
            return None

        ratio_grp = record.get("chip_ratio_grp", [])
        ratio_map: Dict[int, float] = {}
        if isinstance(ratio_grp, dict):
            ratio_grp = [ratio_grp]
        if isinstance(ratio_grp, list):
            for item in ratio_grp:
                if not isinstance(item, dict):
                    continue
                ratio_key = safe_float(item.get("chip_ratio"), None)
                if ratio_key is None:
                    continue
                ratio_map[int(round(ratio_key))] = _normalize_ratio(item.get("chip_concentration"))

        chip = ChipDistribution(
            code=stock_code,
            date=datetime.now().strftime("%Y-%m-%d"),
            source="hscloud",
            profit_ratio=_normalize_ratio(record.get("profit_ratio")),
            avg_cost=safe_float(record.get("average_cost"), 0.0) or 0.0,
            concentration_70=ratio_map.get(70, 0.0),
            concentration_90=ratio_map.get(90, 0.0),
        )

        return chip
