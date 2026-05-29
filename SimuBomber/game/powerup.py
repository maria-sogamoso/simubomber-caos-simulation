"""Power-up system: speed (rayo), full-heart, half-heart — with sounds."""
from __future__ import annotations
import random
import pygame
from config import TILE_SIZE
from assets_loader import get_sprite

POWERUP_SIZE = 32


class PowerUp:
    def __init__(self, x: int, y: int, ptype: str) -> None:
        self.rect  = pygame.Rect(x, y, POWERUP_SIZE, POWERUP_SIZE)
        self.type  = ptype
        self.active = True
        self._bob_offset = 0
        self._bob_dir    = 1
        self._bob_timer  = 0
        surf_map = {
            "health_full": "powerup_heart_full.png",
            "health_half": "powerup_heart_half.png",
            "speed":       "powerup_speed.png",
        }
        self._surf = get_sprite(surf_map.get(ptype, "powerup_heart_full.png"))
        self._fb   = {"health_full": (220,40,40),
                      "health_half": (180,80,80),
                      "speed":       (60,220,90)}.get(ptype, (200,200,80))

    def apply(self, player, now: int) -> None:
        if not self.active:
            return
        if self.type == "health_full":
            player.lives = min(player.max_lives, player.lives + 1.0)
        elif self.type == "health_half":
            player.lives = min(player.max_lives, player.lives + 0.5)
        elif self.type == "speed":
            player.speed = player.base_speed + 3
            player.speed_boost_active   = True
            player.speed_boost_end_time = now + 4000
        self.active = False
        try:
            from game.sounds import play
            play("powerup.wav", 0.65)
        except Exception:
            pass

    def update(self, dt: int) -> None:
        self._bob_timer += dt
        if self._bob_timer > 35:
            self._bob_timer = 0
            self._bob_offset += self._bob_dir
            if abs(self._bob_offset) >= 4:
                self._bob_dir *= -1

    def draw(self, screen: pygame.Surface) -> None:
        dr = self.rect.move(0, self._bob_offset)
        if self._surf:
            screen.blit(pygame.transform.scale(self._surf, (POWERUP_SIZE, POWERUP_SIZE)),
                        dr.topleft)
        else:
            pygame.draw.rect(screen, self._fb, dr)
            pygame.draw.rect(screen, (255,255,255), dr, 1)


class PowerUpSystem:
    def __init__(self) -> None:
        self.powerups: list[PowerUp] = []

    def spawn_from_enemy(self, pos: tuple[int,int]) -> None:
        """Monte Carlo drop: 35% total chance, weighted types."""
        r = random.random()
        if r < 0.65:
            return
        ptype = "health_full" if r < 0.80 else ("health_half" if r < 0.90 else "speed")
        cx, cy = pos
        self.powerups.append(PowerUp(cx - POWERUP_SIZE//2, cy - POWERUP_SIZE//2, ptype))

    def update(self, player, dt: int = 16) -> None:
        now = pygame.time.get_ticks()
        for pu in self.powerups:
            pu.update(dt)
            if pu.active and pu.rect.colliderect(player.rect):
                pu.apply(player, now)
        self.powerups = [pu for pu in self.powerups if pu.active]

    def draw(self, screen: pygame.Surface) -> None:
        for pu in self.powerups:
            pu.draw(screen)
