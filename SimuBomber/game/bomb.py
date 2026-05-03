"""Bomb entities and lightweight system for placement and explosions.

This module provides:
- `Bomb`: a bomb with fuse, explosion duration and cross-shaped blast area.
- `BombSystem`: a minimal controller that enforces cooldown and capacity
  and exposes `try_place_bomb`, `update`, `draw`, and collision checks.
"""

from __future__ import annotations

import pygame

from config import (
    BOMB_SIZE,
    BOMB_COLOR,
    BOMB_FUSE_MS,
    EXPLOSION_COLOR,
    EXPLOSION_DURATION_MS,
    EXPLOSION_RANGE,
    PLAYER_SIZE,
    MAX_ACTIVE_BOMBS,
    BOMB_COOLDOWN_MS,
    MAP_MARGIN,
    WIDTH,
    HEIGHT,
)


class Bomb:
    """Represents an active bomb with fuse and explosion area.

    States:
    - active (counting down)
    - exploding (area active for `EXPLOSION_DURATION_MS`)
    - finished (ready for removal)
    """

    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, BOMB_SIZE, BOMB_SIZE)
        self.fuse_time = BOMB_FUSE_MS
        self.explosion_time = EXPLOSION_DURATION_MS
        self.elapsed = 0
        self.is_exploding = False
        self.range = EXPLOSION_RANGE
        # Timestamp when bomb was placed and grace period before it becomes solid
        self.spawn_time = pygame.time.get_ticks()
        self.blocking_delay = 700  # milliseconds

    def update(self, dt: int) -> None:
        """Advance bomb timers by dt milliseconds."""
        self.elapsed += dt
        if not self.is_exploding and self.elapsed >= self.fuse_time:
            self.is_exploding = True

    def is_active(self) -> bool:
        return not self.is_exploding

    def is_exploding_now(self) -> bool:
        if not self.is_exploding:
            return False
        return (self.elapsed - self.fuse_time) < self.explosion_time

    def should_remove(self) -> bool:
        if not self.is_exploding:
            return False
        return (self.elapsed - self.fuse_time) >= self.explosion_time

    def get_explosion_rects(self) -> list[pygame.Rect]:
        """Return rects forming a cross-shaped blast centered on the bomb.

        NOTE: This method is deprecated in favor of `get_explosion_rects_clamped(map_rect)`
        which ensures explosion tiles are clipped to the map boundaries.
        Kept for backwards compatibility (calls clamped variant with full-map bounds).
        """
        full_map = pygame.Rect(MAP_MARGIN, MAP_MARGIN, WIDTH - MAP_MARGIN * 2, HEIGHT - MAP_MARGIN * 2)
        return self.get_explosion_rects_clamped(full_map)

    def get_explosion_rects_clamped(self, map_rect: pygame.Rect) -> list[pygame.Rect]:
        """Return explosion rects (center + cross) clipped to `map_rect`.

        Expansion in each direction stops when the next tile would be outside `map_rect`.
        Uses `PLAYER_SIZE` as tile size.
        """
        rects: list[pygame.Rect] = [self.rect.copy()]
        # For each direction, expand step by step and stop at map edge
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for step in range(1, self.range + 1):
                nx = self.rect.x + dx * step * PLAYER_SIZE
                ny = self.rect.y + dy * step * PLAYER_SIZE
                candidate = pygame.Rect(nx, ny, PLAYER_SIZE, PLAYER_SIZE)
                if map_rect.contains(candidate):
                    rects.append(candidate)
                else:
                    # stop expansion in this direction when hitting the boundary
                    break
        return rects

    def draw(self, screen: pygame.Surface) -> None:
        if self.is_exploding:
            # draw center
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            s.fill((*EXPLOSION_COLOR, 200))
            screen.blit(s, (self.rect.x, self.rect.y))
            # draw directional tiles, but we don't have map here; caller should use
            # BombSystem.draw which supplies the map_rect. For safety, draw only center.
            # (BombSystem will draw the full clamped area.)
        else:
            pygame.draw.rect(screen, BOMB_COLOR, self.rect)

    def is_blocking(self, current_time: int) -> bool:
        """Return True if the bomb should block movement at `current_time`.

        Bombs are non-blocking for a short delay after placement to allow the
        player to step away; after `blocking_delay` they become solid.
        """
        return (current_time - getattr(self, "spawn_time", 0)) >= getattr(self, "blocking_delay", 700)


class BombSystem:
    """Minimal system enforcing cooldown and finite active bombs.

    Provides a simple API the game loop can call without embedding logic.
    """

    def __init__(self) -> None:
        self.bombs: list[Bomb] = []
        self.last_place_time = 0
        # derive map rect from config so system can clamp explosion areas
        self.map_rect = pygame.Rect(MAP_MARGIN, MAP_MARGIN, WIDTH - MAP_MARGIN * 2, HEIGHT - MAP_MARGIN * 2)

    def try_place_bomb(self, current_time: int, position: tuple[int, int]) -> bool:
        """Attempt to place a bomb; returns True if placed, False otherwise."""
        # position is expected to be the player's current coordinates (not grid-aligned)
        px, py = position

        # Enforce cooldown
        if current_time - self.last_place_time < BOMB_COOLDOWN_MS:
            return False

        # Enforce active bombs limit
        active = sum(1 for b in self.bombs if b.is_active())
        if active >= MAX_ACTIVE_BOMBS:
            return False

        # Align to grid inside map bounds
        gx = ((px - self.map_rect.left) // PLAYER_SIZE) * PLAYER_SIZE + self.map_rect.left
        gy = ((py - self.map_rect.top) // PLAYER_SIZE) * PLAYER_SIZE + self.map_rect.top

        # Ensure the aligned tile is fully inside the map_rect (safety clamp)
        gx = max(self.map_rect.left, min(gx, self.map_rect.right - PLAYER_SIZE))
        gy = max(self.map_rect.top, min(gy, self.map_rect.bottom - PLAYER_SIZE))

        # Create bomb at aligned grid position and tag owner as player
        bomb = Bomb(gx, gy)
        bomb.owner = "player"
        self.bombs.append(bomb)
        self.last_place_time = current_time
        return True

    def get_player_explosion_damage(self, player_rect: pygame.Rect) -> float:
        """
        Returns damage to player based on explosion collision.
        0.0 -> no damage
        0.5 -> own bomb
        1.0 -> other source
        """
        for bomb in self.bombs:
            if bomb.is_exploding_now():
                if hasattr(bomb, "get_explosion_rects_clamped"):
                    areas = bomb.get_explosion_rects_clamped(self.map_rect)
                else:
                    areas = [bomb.rect]

                for area in areas:
                    if area.colliderect(player_rect):
                        if getattr(bomb, "owner", None) == "player":
                            return 0.5
                        else:
                            return 1.0

        return 0.0

    def update(self, dt: int) -> None:
        for b in self.bombs:
            b.update(dt)
        self.bombs = [b for b in self.bombs if not b.should_remove()]

    def draw(self, screen: pygame.Surface) -> None:
        for b in self.bombs:
            if b.is_exploding:
                areas = b.get_explosion_rects_clamped(self.map_rect)
                for i, r in enumerate(areas):
                    s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
                    alpha = 200 if i == 0 else 160
                    s.fill((*EXPLOSION_COLOR, alpha))
                    screen.blit(s, (r.x, r.y))
            else:
                b.draw(screen)

    def check_enemy_collision(self, enemy_rect: pygame.Rect) -> bool:
        for b in self.bombs:
            if b.is_exploding_now():
                for area in b.get_explosion_rects_clamped(self.map_rect):
                    if area.colliderect(enemy_rect):
                        return True
        return False
