"""AgentEnemy: intelligent behavior moved from the original Enemy class.

Implements perception, state decision, chaos response, and biased
direction selection (chase/flee). Relies on `BaseEnemy` for movement
and rendering utilities.
"""

from __future__ import annotations

import math
import random
import pygame
from typing import Optional

from game.base_enemy import BaseEnemy
from utils.helpers import clamp


class AgentEnemy(BaseEnemy):
    """Enemy using simple agent logic: wander, chase, flee.

    This class was extracted from the previous monolithic `Enemy`
    implementation and keeps the original perception and decision
    heuristics. Movement and drawing are delegated to `BaseEnemy`.
    """

    def __init__(self, x: int, y: int, bounds: pygame.Rect, seed: int | None = None) -> None:
        super().__init__(x, y, bounds, seed=seed)

        # State system
        self.state = "wander"

        # Perception values
        self.dist_to_player = float("inf")
        self.dist_to_threat = float("inf")
        self.player_pos: Optional[tuple[int, int]] = None
        self.threat_pos: Optional[tuple[int, int]] = None

        # Thresholds and chaos-related base values
        self.chase_threshold = 150
        self.flee_threshold = 100

        self.base_move_interval = self.move_interval
        self.base_chase_threshold = self.chase_threshold
        self.bias_strength = 0.0

    def apply_chaos(self, chaos: float) -> None:
        """Adjust behaviour parameters based on global chaos level."""
        self.move_interval = max(4, int(self.base_move_interval - chaos * 0.5))
        self.chase_threshold = self.base_chase_threshold + chaos * 8
        self.bias_strength = min(0.8, chaos / 10.0)

    def perceive(self, player=None, bomb_system=None) -> None:
        """Compute distances to player and threats (bombs/explosions)."""
        self.dist_to_player = float("inf")
        self.dist_to_threat = float("inf")
        self.player_pos = None
        self.threat_pos = None

        if player is not None and hasattr(player, "rect"):
            self.player_pos = (player.rect.centerx, player.rect.centery)
            dx = self.player_pos[0] - self.rect.centerx
            dy = self.player_pos[1] - self.rect.centery
            self.dist_to_player = math.sqrt(dx * dx + dy * dy)

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

    def decide_state(self) -> None:
        """Set `self.state` based on distances computed in `perceive`."""
        if self.threat_pos is not None and self.dist_to_threat < self.flee_threshold:
            self.state = "flee"
        elif self.player_pos is not None and self.dist_to_player < self.chase_threshold:
            self.state = "chase"
        else:
            self.state = "wander"

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

    def update(self, player=None, bomb_system=None) -> None:
        """Main update cycle: perceive → decide → act (uses BaseEnemy movement)."""
        self.frame_counter += 1

        self.perceive(player, bomb_system)
        self.decide_state()

        if self.frame_counter % self.move_interval == 1:
            # Base random walk
            self._choose_direction()

            # Apply bias with probability `bias_strength`
            if self.state == "chase" and self.player_pos is not None:
                r = None
                if getattr(self, 'lcg', None) is not None:
                    r = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
                else:
                    r = random.random()
                if r < self.bias_strength:
                    self._bias_direction(self.player_pos, flee=False)

            elif self.state == "flee" and self.threat_pos is not None:
                r = None
                if getattr(self, 'lcg', None) is not None:
                    r = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
                else:
                    r = random.random()
                if r < self.bias_strength:
                    self._bias_direction(self.threat_pos, flee=True)

        # Movement is handled by BaseEnemy
        self.update_movement()
