"""Simple random-moving enemy."""

from __future__ import annotations

import random

import pygame

from config import ENEMY_COLOR, ENEMY_MOVE_INTERVAL, ENEMY_SIZE, ENEMY_SPEED
from utils.helpers import clamp


class Enemy:
    """Enemy with a lightweight random walk implementation."""

    def __init__(self, x: int, y: int, bounds: pygame.Rect) -> None:
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.speed = ENEMY_SPEED
        self.bounds = bounds.copy()
        self.move_interval = ENEMY_MOVE_INTERVAL
        self.direction = (0, 0)
        self.frame_counter = 0

    def _choose_direction(self) -> None:
        """Pick a new random direction from a small neighborhood."""
        choices = [-1, 0, 1]
        self.direction = (random.choice(choices), random.choice(choices))

    def update(self) -> None:
        """Advance the enemy using a simple random walk."""
        self.frame_counter += 1
        if self.frame_counter % self.move_interval == 1:
            self._choose_direction()

        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed

        self.rect.x = clamp(self.rect.x + dx, self.bounds.left, self.bounds.right - self.rect.width)
        self.rect.y = clamp(self.rect.y + dy, self.bounds.top, self.bounds.bottom - self.rect.height)

    def draw(self, screen: pygame.Surface) -> None:
        """Render the enemy."""
        pygame.draw.rect(screen, ENEMY_COLOR, self.rect)