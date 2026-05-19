"""RandomEnemy: pure stochastic movement using BaseEnemy utilities."""

from __future__ import annotations

import pygame

from game.base_enemy import BaseEnemy


class RandomEnemy(BaseEnemy):
    """Enemy that performs a pure random walk.

    It does not perceive the player nor bombs, and ignores chaos.
    """

    def __init__(self, x: int, y: int, bounds: pygame.Rect) -> None:
        super().__init__(x, y, bounds)

    def update(self) -> None:
        """Advance internal counters and perform a random decision periodically."""
        self.frame_counter += 1

        if self.frame_counter % self.move_interval == 1:
            self._choose_direction()

        self.update_movement()

