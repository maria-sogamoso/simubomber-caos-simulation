"""RandomEnemy: pure stochastic movement using BaseEnemy utilities."""

from __future__ import annotations

import os
import sys
import time

import pygame

from game.base_enemy import BaseEnemy

# Path to import the pseudorandom generator.
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if RAIZ_PROYECTO not in sys.path:
    sys.path.append(RAIZ_PROYECTO)

from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import (
    GeneradorCongruenciaLineal,
)

KEEP_DIRECTION_PROBABILITY = 0.6


class RandomEnemy(BaseEnemy):
    """Enemy that performs a pure random walk.

    It does not perceive the player nor bombs, and ignores chaos.
    """

    def __init__(self, x: int, y: int, bounds: pygame.Rect, seed: int | None = None) -> None:
        super().__init__(x, y, bounds, seed=seed)

        # If a seed was provided via BaseEnemy, prefer it; otherwise fallback
        # to the previous time-derived seed for non-reproducible runs.
        if getattr(self, 'lcg', None) is None:
            semilla_base = seed
            if semilla_base is None:
                semilla_base = (int(time.time() * 1000000) + id(self)) % (2**32 - 1)
                if semilla_base == 0:
                    semilla_base = 1

            self.lcg = GeneradorCongruenciaLineal(semilla_base)

    def _choose_direction(self) -> None:
        """Choose a random valid direction using the course PRNG."""
        valid_directions = self._get_valid_directions()

        if not valid_directions:
            self.direction = (0, 0)
            return

        current_is_valid = self.direction in valid_directions
        ri_mantener = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
        keep_current = current_is_valid and ri_mantener < KEEP_DIRECTION_PROBABILITY

        if keep_current:
            return

        candidates = [d for d in valid_directions if d != self.direction]
        if not candidates:
            candidates = valid_directions

        ri_seleccion = self.lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]
        indice_candidato = int(ri_seleccion * len(candidates))
        self.direction = candidates[indice_candidato]

    def update(self) -> None:
        """Advance internal counters and perform a random decision periodically."""
        self.frame_counter += 1

        if self.frame_counter % self.move_interval == 1:
            self._choose_direction()

        self.update_movement()

