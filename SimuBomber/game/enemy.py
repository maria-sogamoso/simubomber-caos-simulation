"""Simple random-moving enemy."""

from __future__ import annotations

import random

import pygame

from config import ENEMY_COLOR, ENEMY_MOVE_INTERVAL, ENEMY_SIZE, ENEMY_SPEED
from utils.helpers import clamp

KEEP_DIRECTION_PROBABILITY = 0.6
ALLOWED_DIRECTIONS = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


class Enemy:
    """Enemy with a discrete random walk and simple transition memory."""

    def __init__(self, x: int, y: int, bounds: pygame.Rect) -> None:
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.speed = ENEMY_SPEED
        self.bounds = bounds.copy()
        self.move_interval = ENEMY_MOVE_INTERVAL
        self.direction = (0, 0)
        self.frame_counter = 0

    def _get_valid_directions(self) -> list[tuple[int, int]]:
        """Return the directions that keep the enemy inside the map bounds."""
        valid_directions: list[tuple[int, int]] = []

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
        """Choose the next direction using a Markov-like transition rule."""
        valid_directions = self._get_valid_directions()

        if not valid_directions:
            self.direction = (0, 0)
            return

        current_is_valid = self.direction in valid_directions
        keep_current = current_is_valid and random.random() < KEEP_DIRECTION_PROBABILITY

        if keep_current:
            return

        candidate_directions = [direction for direction in valid_directions if direction != self.direction]
        if not candidate_directions:
            candidate_directions = valid_directions

        index = int(random.random() * len(candidate_directions))
        if index >= len(candidate_directions):
            index = len(candidate_directions) - 1

        self.direction = candidate_directions[index]

    def update(self) -> None:
        """Advance the enemy using a discrete random walk."""
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