"""Asset loader — loads and caches sprites, tiles, fonts, sounds."""
from __future__ import annotations
import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_surf_cache: dict[str, pygame.Surface | None] = {}
_sound_cache: dict[str, pygame.mixer.Sound | None] = {}


def _load_surf(path: str) -> pygame.Surface | None:
    if path in _surf_cache:
        return _surf_cache[path]
    surf = None
    if os.path.exists(path):
        try:
            surf = pygame.image.load(path).convert_alpha()
        except Exception:
            pass
    _surf_cache[path] = surf
    return surf


def get_sprite(subpath: str) -> pygame.Surface | None:
    return _load_surf(os.path.join(ASSETS_DIR, "sprites", subpath))


def get_tile(level: int, name: str) -> pygame.Surface | None:
    return _load_surf(os.path.join(ASSETS_DIR, "tiles", f"level{level}", f"{name}.png"))


def get_char_frames(char_id: str, anim: str = "idle") -> list[pygame.Surface]:
    frames = []
    for i in range(4):
        s = get_sprite(f"characters/{char_id}_{anim}_f{i}.png")
        if s:
            frames.append(s)
    return frames


def get_enemy_frames(enemy_id: str, anim: str = "idle") -> list[pygame.Surface]:
    frames = []
    for i in range(4):
        s = get_sprite(f"enemies/{enemy_id}_{anim}_f{i}.png")
        if s:
            frames.append(s)
    return frames


def get_sound(name: str) -> pygame.mixer.Sound | None:
    """Load a sound from assets/sounds/. Returns None if mixer not ready."""
    if name in _sound_cache:
        return _sound_cache[name]
    snd = None
    try:
        path = os.path.join(ASSETS_DIR, "sounds", name)
        if os.path.exists(path):
            snd = pygame.mixer.Sound(path)
    except Exception:
        pass
    _sound_cache[name] = snd
    return snd
