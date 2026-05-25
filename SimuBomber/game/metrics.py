"""Metrics sampling system for simulation validation."""

from __future__ import annotations
import pygame


class MetricsSystem:
    """Collects per-frame metrics for analysis."""

    def __init__(self, map_rect: pygame.Rect) -> None:
        self.map_rect = map_rect
        self.samples: list[dict] = []
        self._sample_interval = 500  # ms
        self._last_sample = 0

    def sample_frame(self, tick: int, dt: int, enemies: list,
                     bombs_active: int, explosions_active: int) -> None:
        if tick - self._last_sample < self._sample_interval:
            return
        self._last_sample = tick
        self.samples.append({
            "tick": tick,
            "dt": dt,
            "enemies": len(enemies),
            "bombs": bombs_active,
            "explosions": explosions_active,
        })
