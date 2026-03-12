"""Minimal thinking-mode helpers required by the analyzer."""

from typing import Optional


def get_thinking_extra_body(model: str) -> Optional[dict]:
    """Return the optional thinking payload for compatible models."""
    if not model:
        return None
    normalized = model.lower().strip()
    if normalized.startswith("deepseek-chat"):
        return {"thinking": {"type": "enabled"}}
    return None
