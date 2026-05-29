"""Sound manager — loads and plays WAV effects, graceful fallback."""
from __future__ import annotations
import os
import pygame

_SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
_cache: dict[str, pygame.mixer.Sound | None] = {}
_enabled = False


def init() -> None:
    global _enabled
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        _enabled = True
    except Exception:
        _enabled = False


def _load(name: str) -> pygame.mixer.Sound | None:
    if name in _cache:
        return _cache[name]
    path = os.path.join(_SOUNDS_DIR, f"{name}.wav")
    if _enabled and os.path.exists(path):
        try:
            snd = pygame.mixer.Sound(path)
            _cache[name] = snd
            return snd
        except Exception:
            pass
    _cache[name] = None
    return None


def play(name: str, volume: float = 0.7) -> None:
    snd = _load(name)
    if snd:
        snd.set_volume(volume)
        snd.play()
