"""Simple random-moving enemy with state-based directional bias."""

from __future__ import annotations

import math
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
    """Enemy with a discrete random walk and lightweight state-based biasing.

    States:
    - wander: pure random walk (baseline behavior)
    - chase: biased movement towards player
    - flee: biased movement away from threats

    This model keeps the original stochastic random walk and adds
    minimal state-driven directional bias without changing core mechanics.
    """

    def __init__(self, x: int, y: int, bounds: pygame.Rect) -> None:
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.speed = ENEMY_SPEED
        self.bounds = bounds.copy()

        self.move_interval = ENEMY_MOVE_INTERVAL
        self.direction = (0, 0)
        self.frame_counter = 0

        # --- State system (simple, non-Markov explicit) ---
        self.state = "wander"

        # --- Perception values ---
        self.dist_to_player = float("inf")
        self.dist_to_threat = float("inf")
        self.player_pos: tuple[int, int] | None = None
        self.threat_pos: tuple[int, int] | None = None

        # --- Thresholds ---
        self.chase_threshold = 150
        self.flee_threshold = 100

        # --- Chaos system (baseline values for recovery) ---
        self.base_move_interval = self.move_interval
        self.base_chase_threshold = self.chase_threshold
        self.bias_strength = 0.0

    # Movement utilities

    def _get_valid_directions(self) -> list[tuple[int, int]]:
        """Return directions that keep the enemy inside map bounds."""
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

    # Chaos system

    def apply_chaos(self, chaos: float) -> None:
        """Adjust behavior based on system chaos level (0-10).

        Higher chaos = faster decisions, longer chase ranges, more aggressive bias.
        Always computed from base values (not cumulative).
        """
        # 1. Faster decision-making under chaos
        self.move_interval = max(4, int(self.base_move_interval - chaos * 0.5))

        # 2. Extended chase range
        self.chase_threshold = self.base_chase_threshold + chaos * 8

        # 3. Reduced randomness (deterministic bias)
        self.bias_strength = min(0.8, chaos / 10.0)

    # Perception

    def perceive(self, player=None, bomb_system=None) -> None:
        """Compute distances to player and threats (safe optional input)."""

        self.dist_to_player = float("inf")
        self.dist_to_threat = float("inf")
        self.player_pos = None
        self.threat_pos = None

        # ---------------- Player perception ----------------
        if player is not None and hasattr(player, "rect"):
            self.player_pos = (player.rect.centerx, player.rect.centery)

            dx = self.player_pos[0] - self.rect.centerx
            dy = self.player_pos[1] - self.rect.centery
            self.dist_to_player = math.sqrt(dx * dx + dy * dy)

        # ---------------- Threat perception ----------------
        if bomb_system is not None:
            bombs = getattr(bomb_system, "bombs", [])

            for bomb in bombs:
                if not hasattr(bomb, "rect"):
                    continue

                # Exploding bombs
                if getattr(bomb, "is_exploding", False):
                    areas = []

                    if hasattr(bomb, "get_explosion_rects_clamped"):
                        map_rect = getattr(bomb_system, "map_rect", None)
                        if map_rect is not None:
                            areas = bomb.get_explosion_rects_clamped(map_rect)
                    elif hasattr(bomb, "get_explosion_rects"):
                        areas = bomb.get_explosion_rects()
                    else:
                        areas = [bomb.rect]

                    for area in areas:
                        dx = area.centerx - self.rect.centerx
                        dy = area.centery - self.rect.centery
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance < self.dist_to_threat:
                            self.dist_to_threat = distance
                            self.threat_pos = (area.centerx, area.centery)

                # Active bombs
                else:
                    dx = bomb.rect.centerx - self.rect.centerx
                    dy = bomb.rect.centery - self.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < self.dist_to_threat:
                        self.dist_to_threat = distance
                        self.threat_pos = (bomb.rect.centerx, bomb.rect.centery)

    # State decision (simple heuristic, no Markov matrix)

    def decide_state(self) -> None:
        """Select state based on simple distance thresholds."""

        if self.threat_pos is not None and self.dist_to_threat < self.flee_threshold:
            self.state = "flee"
        elif self.player_pos is not None and self.dist_to_player < self.chase_threshold:
            self.state = "chase"
        else:
            self.state = "wander"

    # Direction biasing (light modification, not full override)

    def _bias_direction(self, target: tuple[int, int], flee: bool = False) -> None:
        """Choose best grid direction towards or away from target."""

        valid_directions = self._get_valid_directions()
        if not valid_directions:
            self.direction = (0, 0)
            return

        best_dir = None
        best_score = None

        for dx, dy in valid_directions:
            next_x = self.rect.centerx + dx * self.speed
            next_y = self.rect.centery + dy * self.speed

            score = math.sqrt((target[0] - next_x) ** 2 + (target[1] - next_y) ** 2)

            if best_score is None:
                best_score = score
                best_dir = (dx, dy)
                continue

            if flee:
                if score > best_score:
                    best_score = score
                    best_dir = (dx, dy)
            else:
                if score < best_score:
                    best_score = score
                    best_dir = (dx, dy)

        if best_dir is not None:
            self.direction = best_dir

    # Core movement

    def _choose_direction(self) -> None:
        """Random walk base behavior (WANDER only)."""

        valid_directions = self._get_valid_directions()

        if not valid_directions:
            self.direction = (0, 0)
            return

        current_is_valid = self.direction in valid_directions
        keep_current = current_is_valid and random.random() < KEEP_DIRECTION_PROBABILITY

        if keep_current:
            return

        candidates = [d for d in valid_directions if d != self.direction]
        if not candidates:
            candidates = valid_directions

        self.direction = random.choice(candidates)

    # Update loop
    def update(self, player=None, bomb_system=None) -> None:
        """Main update cycle: perceive → decide → act."""

        self.frame_counter += 1

        self.perceive(player, bomb_system)
        self.decide_state()

        if self.frame_counter % self.move_interval == 1:

            # Base decision (random walk)
            self._choose_direction()

            # Chaos-influenced bias: apply only with bias_strength probability
            if self.state == "chase" and self.player_pos is not None:
                if random.random() < self.bias_strength:
                    self._bias_direction(self.player_pos, flee=False)

            elif self.state == "flee" and self.threat_pos is not None:
                if random.random() < self.bias_strength:
                    self._bias_direction(self.threat_pos, flee=True)

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

    # Rendering

    def draw(self, screen: pygame.Surface) -> None:
        """Render enemy."""
        pygame.draw.rect(screen, ENEMY_COLOR, self.rect)