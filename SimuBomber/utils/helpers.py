"""Utility helpers for SimuBomber."""

from __future__ import annotations


def clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    """Return value clamped to [minimum, maximum]."""
    return max(minimum, min(maximum, value))
