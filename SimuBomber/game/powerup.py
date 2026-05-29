"""Power-up system: speed (rayo), full-heart, half-heart — with sounds and LCG."""
from __future__ import annotations
import os, sys, time
import pygame
from config import TILE_SIZE
from assets_loader import get_sprite

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
try:
    from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
    _HAS_LCG = True
except ImportError:
    _HAS_LCG = False

POWERUP_SIZE = 32


def _make_lcg(seed=None):
    if seed is None:
        seed = (int(time.time()*1_000_000)+id(object())) % (2**32-1) or 1
    if _HAS_LCG: return GeneradorCongruenciaLineal(seed)
    import random as _r
    class _F:
        def siguiente_Ri_Congruencia_Lineal(self,pasos=1): return [_r.random() for _ in range(pasos)]
    return _F()


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
    NO_DROP_PROBABILITY = 0.65
    HEALTH_FULL_DROP_PROBABILITY = 0.15
    HEALTH_HALF_DROP_PROBABILITY = 0.10
    SPEED_DROP_PROBABILITY = 0.10

    def __init__(self, seed: int | None = None) -> None:
        self.powerups: list[PowerUp] = []
        self.lcg = _make_lcg(seed)

    def _sample_drop_type(self) -> str | None:
        """Sample a power-up outcome using the project PRNG."""
        r = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
        if r < self.NO_DROP_PROBABILITY:
            return None
        r2 = r - self.NO_DROP_PROBABILITY
        if r2 < self.HEALTH_FULL_DROP_PROBABILITY:
            return "health_full"
        if r2 < self.HEALTH_FULL_DROP_PROBABILITY + self.HEALTH_HALF_DROP_PROBABILITY:
            return "health_half"
        return "speed"

    def spawn_from_enemy(self, pos: tuple[int,int]) -> None:
        """Monte Carlo drop using LCG."""
        ptype = self._sample_drop_type()
        if ptype is None:
            return
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
