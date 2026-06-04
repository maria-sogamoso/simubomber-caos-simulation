"""
Music manager — background music with fade transitions.
All tracks loop indefinitely. Crossfade via fadeout + delayed load.
"""
from __future__ import annotations
import os
import pygame

_MUSIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music')

TRACKS = {
    "menu":   "menu.wav",
    "level1": "level1.wav",
    "level2": "level2.wav",
    "level3": "level3.wav",
    "ending": "ending.wav",
}

_current: str | None = None
_pending: str | None = None
_fading = False
FADE_MS = 1500
MUSIC_VOL = 0.35


def switch(track_name: str) -> None:
    """Switch to a new music track with fade transition."""
    global _pending, _fading
    if track_name == _current:
        return
    _pending = track_name
    if pygame.mixer.music.get_busy():
        _fading = True
        pygame.mixer.music.fadeout(FADE_MS)
    else:
        _load_and_play(track_name)


def _load_and_play(track_name: str) -> None:
    global _current
    filename = TRACKS.get(track_name, "")
    if not filename:
        return
    path = os.path.join(_MUSIC_DIR, filename)
    if not os.path.exists(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(MUSIC_VOL)
        pygame.mixer.music.play(-1)
        _current = track_name
    except Exception:
        pass


def update(dt: int = 0) -> None:
    """Call every frame to complete pending fade transitions."""
    global _fading, _pending
    if _fading and not pygame.mixer.music.get_busy():
        _fading = False
        if _pending:
            _load_and_play(_pending)
            _pending = None


def stop() -> None:
    """Fade out and stop all music."""
    global _current, _pending, _fading
    pygame.mixer.music.fadeout(FADE_MS)
    _current = None
    _pending = None
    _fading = False
