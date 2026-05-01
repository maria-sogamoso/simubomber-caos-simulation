"""Player entity and controls."""

from __future__ import annotations

import pygame

from config import PLAYER_COLOR, PLAYER_SIZE, PLAYER_SPEED
from utils.helpers import clamp


class Player:
    """Controllable player square."""

    def __init__(self, x: int, y: int, bounds: pygame.Rect) -> None:
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = PLAYER_SPEED
        self.bounds = bounds.copy()

    def handle_input(self) -> tuple[int, int]:
        """Translate keyboard state into a movement vector."""
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed

        return dx, dy

    def update(self) -> None:
        """Update the player position and keep it inside the map bounds."""
        dx, dy = self.handle_input()
        self.rect.x = clamp(self.rect.x + dx, self.bounds.left, self.bounds.right - self.rect.width)
        self.rect.y = clamp(self.rect.y + dy, self.bounds.top, self.bounds.bottom - self.rect.height)

    def draw(self, screen: pygame.Surface) -> None:
        """Render the player."""
        pygame.draw.rect(screen, PLAYER_COLOR, self.rect)