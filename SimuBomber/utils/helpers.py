"""Utility helper functions."""


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Return value constrained to the inclusive [minimum, maximum] range."""
    return max(minimum, min(value, maximum))