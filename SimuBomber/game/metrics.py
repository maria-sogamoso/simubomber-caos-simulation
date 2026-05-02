"""Lightweight metrics and logging for SimuBomber simulation.

Responsibilities:
- Collect per-frame logs for enemies (tick, enemy_id, position, direction, changed)
- Maintain per-enemy counters (direction changes, total active time)
- Maintain transition counts between directions (approximate Markov matrix)
- Compute distribution of positions on the grid
- Compute simple `system_chaos_level`

Designed for in-memory collection and minimal runtime overhead.
"""

from __future__ import annotations

from collections import defaultdict, deque
import math
import time
from typing import Iterable

import pygame

from config import PLAYER_SIZE


class MetricsSystem:
    """Collects logs and metrics for enemies and bombs.

    Usage:
    - instantiate once in `GameLoop` with the map rect
    - call `sample_frame(dt, enemies, bomb_counts)` once per frame
    """

    def __init__(self, map_rect: pygame.Rect, grid_size: int = PLAYER_SIZE) -> None:
        self.map_rect = map_rect.copy()
        self.grid_size = grid_size

        # Logs: deque to bound memory; each entry is a dict
        self.logs: deque[dict] = deque(maxlen=20000)

        # Enemy id mapping (stable small ids)
        self._enemy_map: dict[int, int] = {}
        self._next_enemy_id = 1

        # Per-enemy stats
        self.per_enemy: dict[int, dict] = defaultdict(lambda: {
            "direction_changes": 0,
            "frames_seen": 0,
            "first_seen_time": None,
            "last_direction": None,
        })

        # Transition counts: prev_dir -> new_dir -> count
        self.transition_counts: dict = defaultdict(lambda: defaultdict(int))

        # Position distribution grid counts
        self.position_counts: dict[tuple[int, int], int] = defaultdict(int)

        # Global metric
        self.system_chaos_level = 0.0

    def _get_eid(self, enemy_obj: object) -> int:
        key = id(enemy_obj)
        if key not in self._enemy_map:
            self._enemy_map[key] = self._next_enemy_id
            self._next_enemy_id += 1
        return self._enemy_map[key]

    def _pos_to_cell(self, x: int, y: int) -> tuple[int, int]:
        col = (x - self.map_rect.left) // self.grid_size
        row = (y - self.map_rect.top) // self.grid_size
        return (int(col), int(row))

    def sample_frame(self, tick_time_ms: int, dt: int, enemies: Iterable[object], bombs_active: int, explosions_active: int) -> None:
        """Sample current frame: record enemy states and update metrics.

        Parameters:
        - tick_time_ms: current tick (ms)
        - dt: milliseconds elapsed since last frame
        - enemies: iterable of enemy objects (expected to have `rect` and `direction`)
        - bombs_active: integer count of bombs (active)
        - explosions_active: integer count of currently exploding bombs
        """
        for e in enemies:
            if e is None:
                continue
            eid = self._get_eid(e)
            st = self.per_enemy[eid]

            # Initialize first seen time
            if st["first_seen_time"] is None:
                st["first_seen_time"] = tick_time_ms

            # Direction tracking
            prev = st["last_direction"]
            curr = getattr(e, "direction", (0, 0))
            changed = prev is not None and prev != curr
            if changed:
                st["direction_changes"] += 1
                self.transition_counts[prev][curr] += 1
            # For first observation, do not count as change but record transition from None
            if prev is None:
                # record initial transition from idle
                self.transition_counts[(0, 0)][curr] += 1

            st["last_direction"] = curr
            st["frames_seen"] += 1

            # Log entry
            log = {
                "tick_ms": tick_time_ms,
                "enemy_id": eid,
                "x": e.rect.x,
                "y": e.rect.y,
                "direction": curr,
                "changed_direction": bool(changed),
            }
            self.logs.append(log)

            # Position distribution
            cell = self._pos_to_cell(e.rect.x, e.rect.y)
            self.position_counts[cell] += 1

        # Update global metrics
        num_enemies = sum(1 for _ in filter(lambda x: x is not None, enemies))
        # Simple chaos formula: enemies + 0.5*bombs + 1.5*explosions
        self.system_chaos_level = float(num_enemies) + 0.5 * float(bombs_active) + 1.5 * float(explosions_active)

    def get_enemy_stats(self, enemy_obj: object) -> dict:
        eid = self._enemy_map.get(id(enemy_obj))
        if eid is None:
            return {}
        st = self.per_enemy[eid]
        seconds = (st["frames_seen"] * 1.0) / 60.0 if st["frames_seen"] > 0 else 0.0
        avg_changes_per_sec = st["direction_changes"] / seconds if seconds > 0 else 0.0
        lifespan = None
        if st["first_seen_time"] is not None:
            lifespan = st["frames_seen"] / 60.0
        return {
            "enemy_id": eid,
            "direction_changes": st["direction_changes"],
            "frames_seen": st["frames_seen"],
            "avg_changes_per_sec": avg_changes_per_sec,
            "lifespan_sec": lifespan,
        }

    def get_transition_matrix(self) -> dict:
        """Return the transition counts mapping for analysis."""
        return {k: dict(v) for k, v in self.transition_counts.items()}

    def clear(self) -> None:
        """Clear collected logs and counters (useful between experiments)."""
        self.logs.clear()
        self._enemy_map.clear()
        self._next_enemy_id = 1
        self.per_enemy.clear()
        self.transition_counts.clear()
        self.position_counts.clear()
        self.system_chaos_level = 0.0
