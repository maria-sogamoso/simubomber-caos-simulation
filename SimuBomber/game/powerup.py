"""Power-up entities and spawning system for the game."""

from __future__ import annotations

import random

import pygame

POWERUP_SIZE = 24
HEALTH_COLOR = (220, 60, 60)
SPEED_COLOR = (60, 180, 90)
OUTLINE_COLOR = (160, 160, 160)


class PowerUp:
    """A simple collectible power-up."""

    def __init__(self, x: int, y: int, powerup_type: str) -> None:
        self.rect = pygame.Rect(x, y, POWERUP_SIZE, POWERUP_SIZE)
        self.type = powerup_type
        self.active = True

    def apply(self, player, current_time: int) -> None:
        """Apply the power-up effect to the player once."""
        if not self.active:
            return

        if self.type == "health":
            player.lives = min(player.max_lives, player.lives + 0.5)
        elif self.type == "speed":
            player.speed = player.base_speed + 2
            player.speed_boost_active = True
            player.speed_boost_end_time = current_time + 3000

        self.active = False

    def draw(self, screen: pygame.Surface) -> None:
        """Render the power-up using simple colored rectangles."""
        if self.type == "health":
            color = HEALTH_COLOR
        else:
            color = SPEED_COLOR

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, OUTLINE_COLOR, self.rect, 1)


class PowerUpSystem:
    """Manage spawning, collection and rendering of power-ups."""

    def __init__(self) -> None:
        self.powerups: list[PowerUp] = []

    def spawn_from_enemy(self, position: tuple[int, int]) -> None:
        """Spawn a power-up from a defeated enemy using Monte Carlo sampling."""
        r = random.random()
        if r < 0.65:
            return
        if r < 0.85:
            powerup_type = "health"
        else:
            powerup_type = "speed"

        center_x, center_y = position
        x = center_x - POWERUP_SIZE // 2
        y = center_y - POWERUP_SIZE // 2
        self.powerups.append(PowerUp(x, y, powerup_type))

    def update(self, player) -> None:
        """Apply collected power-ups and remove inactive ones."""
        current_time = pygame.time.get_ticks()

        for powerup in self.powerups:
            if powerup.active and powerup.rect.colliderect(player.rect):
                powerup.apply(player, current_time)

        self.powerups = [powerup for powerup in self.powerups if powerup.active]

    def draw(self, screen: pygame.Surface) -> None:
        """Render active power-ups."""
        for powerup in self.powerups:
            powerup.draw(screen)
