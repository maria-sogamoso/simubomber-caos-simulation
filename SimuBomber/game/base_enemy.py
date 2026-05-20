"""Base enemy movement utilities shared by different enemy models.

This module provides `BaseEnemy` which implements generic grid-based
movement, valid-direction checks, and rendering. It intentionally
contains no perception, state, or chaos logic so it can be reused by
both purely-random and agent-driven enemy implementations.
"""

from __future__ import annotations

import random
import pygame
import os
import time
import sys
from typing import List, Tuple

from config import ENEMY_COLOR, ENEMY_SIZE, ENEMY_SPEED, ENEMY_MOVE_INTERVAL
from utils.helpers import clamp

# Lazy import of the project LCG when needed
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if RAIZ_PROYECTO not in sys.path:
    sys.path.append(RAIZ_PROYECTO)
try:
    from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
except Exception:
    GeneradorCongruenciaLineal = None

# Movement helpers
KEEP_DIRECTION_PROBABILITY = 0.6
ALLOWED_DIRECTIONS: Tuple[Tuple[int, int], ...] = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


class BaseEnemy:
    """Generic enemy implementing grid-constrained movement.

    Responsibilities:
    - Initialize `rect`, `speed` and `bounds`.
    - Provide `_get_valid_directions` and `_choose_direction`.
    - Expose `update_movement()` to actually move the entity.
    - Render via `draw()`.

    Subclasses must implement their own decision-making and call
    `_choose_direction()` when appropriate.
    """

    def __init__(self, x: int, y: int, bounds: pygame.Rect, seed: int | None = None) -> None:
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.speed = ENEMY_SPEED
        self.bounds = bounds.copy()

        self.move_interval = ENEMY_MOVE_INTERVAL
        self.direction: Tuple[int, int] = (0, 0)
        self.frame_counter = 0

        # Base values retained for subclasses that implement chaos
        self.base_move_interval = self.move_interval
        # Optional project LCG for reproducible decisions; if seed is None
        # behaviour falls back to Python's random (unchanged).
        self.seed = seed
        self.lcg = None
        if seed is not None and GeneradorCongruenciaLineal is not None:
            if seed == 0:
                seed = 1
            self.lcg = GeneradorCongruenciaLineal(seed)

    def _get_valid_directions(self) -> List[Tuple[int, int]]:
        """Return directions that keep the enemy inside map bounds."""
        valid_directions: List[Tuple[int, int]] = []

        for dx, dy in ALLOWED_DIRECTIONS:
            next_x = clamp(
                self.rect.x + dx * self.speed,
                self.bounds.left,
                self.bounds.right - self.rect.width,
            )
            next_y = clamp(
                self.rect.y + dy * self.speed,
                self.bounds.top,
                self.bounds.bottom - self.rect.height,
            )

            if next_x == self.rect.x + dx * self.speed and next_y == self.rect.y + dy * self.speed:
                valid_directions.append((dx, dy))

        return valid_directions

    def _choose_direction(self) -> None:
        """Choose a new random valid direction (with some inertia)."""
        valid_directions = self._get_valid_directions()

        if not valid_directions:
            self.direction = (0, 0)
            return

        current_is_valid = self.direction in valid_directions
        if self.lcg is not None:
            ri = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
            keep_current = current_is_valid and ri < KEEP_DIRECTION_PROBABILITY
        else:
            keep_current = current_is_valid and random.random() < KEEP_DIRECTION_PROBABILITY

        if keep_current:
            return

        candidates = [d for d in valid_directions if d != self.direction]
        if not candidates:
            candidates = valid_directions

        if self.lcg is not None:
            ri2 = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
            idx = int(ri2 * len(candidates))
            self.direction = candidates[idx]
        else:
            self.direction = random.choice(candidates)

    def update_movement(self) -> None:
        """Apply `direction` to the rect, clamped within `bounds`.

        This method does not change `direction` — subclasses decide when
        to call `_choose_direction()` and when to call this method.
        """
        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed

        self.rect.x = clamp(
            self.rect.x + dx,
            self.bounds.left,
            self.bounds.right - self.rect.width,
        )
        self.rect.y = clamp(
            self.rect.y + dy,
            self.bounds.top,
            self.bounds.bottom - self.rect.height,
        )

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, ENEMY_COLOR, self.rect)
