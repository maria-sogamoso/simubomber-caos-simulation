"""Simple random-moving enemy with state-based directional bias driven by custom LCG."""

from __future__ import annotations

import math
import sys
import os
import pygame

from config import ENEMY_COLOR, ENEMY_MOVE_INTERVAL, ENEMY_SIZE, ENEMY_SPEED
from utils.helpers import clamp

# Ajuste dinámico de rutas para importar de forma limpia la librería de generadores desde el juego
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if RAIZ_PROYECTO not in sys.path:
    sys.path.append(RAIZ_PROYECTO)

from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal

KEEP_DIRECTION_PROBABILITY = 0.6

ALLOWED_DIRECTIONS = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


class Enemy:
    """Enemy with a discrete random walk and lightweight state-based biasing.

    Driven by the custom Linear Congruential Generator (LCG) developed in the course.
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

        # # --- INTEGRACIÓN DEL GENERADOR PSEUDOALEATORIO (PRNG) ---
        # # Inicializamos una semilla pseudo-única usando propiedades físicas/temporales iniciales de Python
        # # para que cada enemigo tenga un patrón de caminata desincronizado y orgánico.
        # import random as python_seed_bridge
        # semilla_enemigo = python_seed_bridge.randint(1, 2**31 - 1)
        # self.lcg = GeneradorCongruenciaLineal(semilla_enemigo)

# --- INTEGRACIÓN DEL GENERADOR PSEUDOALEATORIO (PRNG) ---
        import time
        
        # Usamos el reloj del sistema + la dirección de memoria del objeto (id) 
        # para asegurar una semilla única por enemigo y evitar clonación de movimientos,
        # sin tocar la librería 'random' nativa de Python.
        semilla_base = (int(time.time() * 1000000) + id(self)) % (2**32 - 1)
        
        # Si por alguna razón da 0, la ajustamos a 1 (los LCG a veces fallan con semilla 0)
        if semilla_base == 0:
            semilla_base = 1
            
        self.lcg = GeneradorCongruenciaLineal(semilla_base)

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
        """Adjust behavior based on system chaos level (0-10)."""
        self.move_interval = max(4, int(self.base_move_interval - chaos * 0.5))
        self.chase_threshold = self.base_chase_threshold + chaos * 8
        self.bias_strength = min(0.8, chaos / 10.0)

    # Perception

    def perceive(self, player=None, bomb_system=None) -> None:
        """Compute distances to player and threats (safe optional input)."""
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
                else:
                    dx = bomb.rect.centerx - self.rect.centerx
                    dy = bomb.rect.centery - self.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance < self.dist_to_threat:
                        self.dist_to_threat = distance
                        self.threat_pos = (bomb.rect.centerx, bomb.rect.centery)

    # State decision

    def decide_state(self) -> None:
        """Select state based on simple distance thresholds."""
        if self.threat_pos is not None and self.dist_to_threat < self.flee_threshold:
            self.state = "flee"
        elif self.player_pos is not None and self.dist_to_player < self.chase_threshold:
            self.state = "chase"
        else:
            self.state = "wander"

    # Direction biasing

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

    # Core movement INTEGRADO GENERADOR CONGRUENCIA LINEAL

    def _choose_direction(self) -> None:
        """Random walk base behavior (WANDER) usando el método de Congruencia Lineal."""
        valid_directions = self._get_valid_directions()

        if not valid_directions:
            self.direction = (0, 0)
            return

        current_is_valid = self.direction in valid_directions
        
        # INTEGRACIÓN LCG: evaluamos la probabilidad de mantener dirección con tu generador
        ri_mantener = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
        keep_current = current_is_valid and ri_mantener < KEEP_DIRECTION_PROBABILITY

        if keep_current:
            return

        candidates = [d for d in valid_directions if d != self.direction]
        if not candidates:
            candidates = valid_directions

        # Mapeamos de forma uniforme el número [0, 1) al rango de índices de los candidatos legales
        ri_seleccion = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
        indice_candidato = int(ri_seleccion * len(candidates))
        
        self.direction = candidates[indice_candidato]

    # Update loop
    def update(self, player=None, bomb_system=None) -> None:
        """Main update cycle driven by custom math parameters."""
        self.frame_counter += 1

        self.perceive(player, bomb_system)
        self.decide_state()

        if self.frame_counter % self.move_interval == 1:
            # Caminata aleatoria base controlada por el LCG
            self._choose_direction()

            # INTEGRACIÓN LCG: El sesgo probabilístico por caos también usa tu generador matemático
            if self.state == "chase" and self.player_pos is not None:
                ri_caos = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
                if ri_caos < self.bias_strength:
                    self._bias_direction(self.player_pos, flee=False)

            elif self.state == "flee" and self.threat_pos is not None:
                ri_caos = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
                if ri_caos < self.bias_strength:
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