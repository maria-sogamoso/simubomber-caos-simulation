"""Sound manager — centralises all audio playback."""
from __future__ import annotations
import pygame
from assets_loader import get_sound

_mixer_ok = False


def init_sound() -> None:
    global _mixer_ok
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        _mixer_ok = True
    except Exception:
        _mixer_ok = False


def play(name: str, volume: float = 0.7) -> None:
    if not _mixer_ok:
        return
    snd = get_sound(name)
    if snd:
        snd.set_volume(volume)
        snd.play()
