# -*- coding: utf-8 -*-
"""
===================================
WencaiFetcher - 问财筹码数据源
===================================

通过 pywencai 查询筹码字段，作为 AkShare 失效时的降级源。
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from src.config import get_config
from .base import BaseFetcher, normalize_stock_code
from .realtime_types import ChipDistribution, safe_float

logger = logging.getLogger(__name__)


def _normalize_ratio(val: Any) -> float:
    """将比例字段统一到 0-1。"""
    v = safe_float(val, 0.0) or 0.0
    if v <= 1:
        return float(v)
    if v <= 100:
        return float(v) / 100.0
    if v <= 10000:
        return float(v) / 10000.0
    return float(v)


def _is_empty_value(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip().lower()
    return s in ("", "-", "--", "nan", "none", "null", "n/a", "na")


class WencaiFetcher(BaseFetcher):
    """iWencai 筹码抓取器（cookie 鉴权）。"""

    name = "WencaiFetcher"
    priority = 91  # 不参与主数据源优先级，仅用于筹码分布降级链

    def __init__(self) -> None:
        cfg = get_config()
        self.cookie = (cfg.wencai_cookie or "").strip()
        self.user_agent = (cfg.wencai_user_agent or "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.cookie)

    # --- BaseFetcher abstract methods (unused in this fetcher) ---
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame()

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        return df

    # --- Chip distribution path ---
    def get_chip_distribution(self, stock_code: str) -> Optional[ChipDistribution]:
        stock_code = normalize_stock_code(stock_code)

        if not self.enabled:
            logger.debug("[Wencai筹码] 未配置 WENCAI_COOKIE，跳过")
            return None

        try:
            import pywencai  # 延迟导入，避免未安装时影响主流程
        except Exception as e:
            logger.warning("[Wencai筹码] pywencai 不可用，跳过: %s", e)
            return None

        # 使用专题词触发问财的筹码结构化返回（dict: barline3/txt1/...）
        query = f"{stock_code} 筹码分布"

        kwargs: Dict[str, Any] = {
            "query": query,
            "query_type": "stock",
            "loop": False,
            "cookie": self.cookie,
        }
        if self.user_agent:
            kwargs["user_agent"] = self.user_agent

        try:
            df = pywencai.get(**kwargs)
        except Exception as e:
            logger.warning("[Wencai筹码] %s 查询失败: %s", stock_code, e)
            return None

        chip = self._build_chip_from_result(stock_code, df)
        if chip is None:
            logger.debug("[Wencai筹码] %s 返回结果无法提取有效筹码字段", stock_code)
            return None

        logger.info("[Wencai筹码] %s 获取成功", stock_code)
        return chip

    def _build_chip_from_result(self, stock_code: str, result: Any) -> Optional[ChipDistribution]:
        """
        兼容 pywencai 常见返回：
        - DataFrame（标准股票列表）
        - dict（如「筹码分布」专题结果，包含 barline3/txt1）
        """
        if result is None:
            return None

        if isinstance(result, pd.DataFrame):
            if result.empty:
                return None
            row = self._select_row(result, stock_code)
            if row is None:
                return None
            return self._build_chip(stock_code, row)

        if isinstance(result, dict):
            return self._build_chip_from_dict(stock_code, result)

        return None

    @staticmethod
    def _normalize_col_name(name: Any) -> str:
        s = str(name or "").strip().lower()
        # 去掉常见分隔符与日期后缀噪声，保留中英文和数字
        s = re.sub(r"[\s\[\]\(\)（）:：/_\-]+", "", s)
        return s

    @classmethod
    def _extract_value_by_patterns(cls, row: pd.Series, patterns: list[str]) -> Optional[Any]:
        for col, val in row.items():
            if _is_empty_value(val):
                continue
            col_name = cls._normalize_col_name(col)
            for pattern in patterns:
                if re.search(pattern, col_name):
                    return val
        return None

    @classmethod
    def _select_row(cls, df: pd.DataFrame, stock_code: str) -> Optional[pd.Series]:
        if df is None or df.empty:
            return None

        code_patterns = ("代码", "证券代码", "股票代码", "symbol", "code")
        for _, row in df.iterrows():
            for col, val in row.items():
                col_name = cls._normalize_col_name(col)
                if not any(p in col_name for p in code_patterns):
                    continue
                if _is_empty_value(val):
                    continue
                candidate = normalize_stock_code(str(val).strip().split(".")[0])
                if candidate == stock_code:
                    return row

        # 找不到精确代码时，回退第一行
        return df.iloc[0]

    @classmethod
    def _build_chip(cls, stock_code: str, row: pd.Series) -> Optional[ChipDistribution]:
        profit_ratio = cls._extract_value_by_patterns(
            row,
            [
                r"获利比例",
                r"获利盘占比",
            ],
        )
        avg_cost = cls._extract_value_by_patterns(
            row,
            [
                r"平均成本",
                r"成本均价",
                r"筹码平均成本",
            ],
        )
        cost_90_low = cls._extract_value_by_patterns(row, [r"90.*成本.*低", r"90.*成本下"])
        cost_90_high = cls._extract_value_by_patterns(row, [r"90.*成本.*高", r"90.*成本上"])
        concentration_90 = cls._extract_value_by_patterns(row, [r"90.*集中度"])
        cost_70_low = cls._extract_value_by_patterns(row, [r"70.*成本.*低", r"70.*成本下"])
        cost_70_high = cls._extract_value_by_patterns(row, [r"70.*成本.*高", r"70.*成本上"])
        concentration_70 = cls._extract_value_by_patterns(row, [r"70.*集中度"])

        has_any_value = any(
            not _is_empty_value(v)
            for v in (
                profit_ratio,
                avg_cost,
                cost_90_low,
                cost_90_high,
                concentration_90,
                cost_70_low,
                cost_70_high,
                concentration_70,
            )
        )
        if not has_any_value:
            return None

        chip = ChipDistribution(
            code=stock_code,
            date=datetime.now().strftime("%Y-%m-%d"),
            source="wencai",
            profit_ratio=_normalize_ratio(profit_ratio),
            avg_cost=safe_float(avg_cost, 0.0) or 0.0,
            cost_90_low=safe_float(cost_90_low, 0.0) or 0.0,
            cost_90_high=safe_float(cost_90_high, 0.0) or 0.0,
            concentration_90=_normalize_ratio(concentration_90),
            cost_70_low=safe_float(cost_70_low, 0.0) or 0.0,
            cost_70_high=safe_float(cost_70_high, 0.0) or 0.0,
            concentration_70=_normalize_ratio(concentration_70),
        )
        return chip

    @classmethod
    def _build_chip_from_dict(cls, stock_code: str, payload: Dict[str, Any]) -> Optional[ChipDistribution]:
        """
        解析问财「筹码分布」专题结构：
        - barline3: 近一段时间 平均成本 / 收盘获利
        - txt1: 文案里通常包含 90%成本区间与获利比例
        """
        bar_df = payload.get("barline3")
        if not isinstance(bar_df, pd.DataFrame):
            # 某些场景 barline 可能在子对象里
            for value in payload.values():
                if isinstance(value, dict) and isinstance(value.get("barline3"), pd.DataFrame):
                    bar_df = value.get("barline3")
                    break

        row = None
        if isinstance(bar_df, pd.DataFrame) and not bar_df.empty:
            row = cls._select_row(bar_df, stock_code)
            if row is None:
                row = bar_df.iloc[-1]

        avg_cost = None
        profit_ratio = None
        if row is not None:
            avg_cost = row.get("平均成本")
            profit_ratio = row.get("收盘获利")

        txt = str(payload.get("txt1") or "")
        txt_plain = re.sub(r"<[^>]+>", "", txt)

        # 示例：平均成本为11.37，90%股民成本价在10.80-11.73，有21.86%的人收盘是盈利的
        avg_m = re.search(r"平均成本为\s*([0-9]+(?:\.[0-9]+)?)", txt_plain)
        range_m = re.search(r"90%股民成本价在\s*([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)", txt_plain)
        profit_m = re.search(r"有\s*([0-9]+(?:\.[0-9]+)?)%\s*的人.*?盈利", txt_plain)

        if avg_m:
            avg_cost = avg_m.group(1)
        if profit_m:
            profit_ratio = profit_m.group(1)

        cost_90_low = float(range_m.group(1)) if range_m else None
        cost_90_high = float(range_m.group(2)) if range_m else None

        avg_cost_f = safe_float(avg_cost, 0.0) or 0.0
        concentration_90 = 0.0
        if cost_90_low is not None and cost_90_high is not None and avg_cost_f > 0:
            concentration_90 = max(0.0, (cost_90_high - cost_90_low) / avg_cost_f)

        has_any_value = any(
            not _is_empty_value(v)
            for v in (
                avg_cost,
                profit_ratio,
                cost_90_low,
                cost_90_high,
            )
        )
        if not has_any_value:
            return None

        return ChipDistribution(
            code=stock_code,
            date=datetime.now().strftime("%Y-%m-%d"),
            source="wencai",
            profit_ratio=_normalize_ratio(profit_ratio),
            avg_cost=avg_cost_f,
            cost_90_low=safe_float(cost_90_low, 0.0) or 0.0,
            cost_90_high=safe_float(cost_90_high, 0.0) or 0.0,
            concentration_90=concentration_90,
            concentration_70=0.0,
        )
