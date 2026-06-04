"""System Dynamics Runtime for SimuBomber.

Provides a lightweight, discrete, frame-based simulator that maintains stocks
(enemies, bombs, explosions, power-ups) and calculates `chaos` and `difficulty`.

The runtime is designed to be **bidirectionally coupled** with the game:
- Each frame the game feeds observed counts via `sync_observed()`.
- The model blends observations with its own predictions to keep feedback
  loops alive (spawn pressure, difficulty scaling, chaos damping).
- The game reads back `get_spawn_rate()` and `get_difficulty()` to drive
  enemy spawning and difficulty scaling.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DinamicaParams:
    """Parameters for the runtime dynamics model.

    All fields are base rates used by `SistemaDinamicoRuntime.step` and are
    expressed as per-second or per-timestep factors (the integrator scales
    by the frame `dt_ms / 1000`). These defaults are tuned for classroom
    demonstration rather than production gameplay.
    """

    spawn_enemigos_base: float = 0.06
    bomb_drop_base: float = 0.12
    explosion_rate_base: float = 0.25
    decay_explosion_base: float = 0.55
    powerup_drop_base: float = 0.04
    powerup_use_base: float = 0.03

    # Blend factor: how much the observed (game) stocks weight vs model
    # prediction.  0.0 = pure model, 1.0 = pure observation.
    observation_blend: float = 0.70


class SistemaDinamicoRuntime:
    """Runtime system-dynamics engine maintaining simple stocks & flows.

    Stocks:
    - `enemigos`: active enemy count estimate
    - `bombas`: rate/level of bomb requests
    - `explosiones`: active explosions
    - `powerups`: available power-ups

    The `step(dt_ms)` method advances the stocks using simple linear rates
    derived from `DinamicaParams`. Use `observe()` to obtain a small snapshot
    suitable for logging or feeding into agent heuristics.

    Feedback loops:
    - **Positive**: more chaos → higher spawn pressure → more enemies → more chaos
    - **Negative**: more power-ups → chaos damping → lower spawn pressure
    """

    def __init__(self, params: DinamicaParams | None = None):
        self.params = params or DinamicaParams()
        # internal model stocks
        self.enemigos = 2.0
        self.bombas = 1.0
        self.explosiones = 0.0
        self.powerups = 0.0
        self.caos = 0.0
        self.dificultad = 1.0
        # latest computed flow rates (available for game_loop queries)
        self._spawn_rate = 0.0

    # ── Observation sync ──────────────────────────────────────────────────

    def sync_observed(self, enemigos: float, bombas: float,
                      explosiones: float, powerups: float) -> None:
        """Blend real game counts with model predictions.

        This avoids overwriting the model's internal state entirely, keeping
        the feedback loops alive while grounding predictions in reality.
        """
        a = self.params.observation_blend
        self.enemigos    = a * enemigos    + (1 - a) * self.enemigos
        self.bombas      = a * bombas      + (1 - a) * self.bombas
        self.explosiones = a * explosiones + (1 - a) * self.explosiones
        self.powerups    = a * powerups    + (1 - a) * self.powerups

    # ── Step ──────────────────────────────────────────────────────────────

    def step(self, dt_ms: int) -> None:
        """Advance the dynamics by a timestep `dt_ms` (milliseconds).

        The formulas are scaled so that dt_ms / 1000 acts as a time-scaling
        factor; given the game runs at ~60 FPS dt_ms will be small.
        """
        scale = dt_ms / 1000.0

        pressure = 1.0 + 0.08 * self.caos
        recovery = 1.0 + 0.10 * self.powerups

        spawn_enemigos = max(0.0, self.params.spawn_enemigos_base * pressure) * scale
        bomb_requests = max(0.0, self.params.bomb_drop_base * pressure) * scale
        bomb_detonation = max(0.0, self.params.explosion_rate_base * self.bombas) * scale
        enemy_removal = max(0.0, (0.12 + 0.03 * self.powerups) * self.enemigos) * scale
        explosion_decay = max(0.0, self.params.decay_explosion_base * self.explosiones) * scale
        powerup_drop = max(0.0, self.params.powerup_drop_base * max(0.0, self.enemigos)) * scale
        powerup_use = max(0.0, self.params.powerup_use_base * recovery) * scale

        self.enemigos = max(0.0, self.enemigos + spawn_enemigos - enemy_removal)
        self.bombas = max(0.0, self.bombas + bomb_requests - bomb_detonation)
        self.explosiones = max(0.0, self.explosiones + bomb_detonation - explosion_decay)
        self.powerups = max(0.0, self.powerups + powerup_drop - powerup_use)

        caos_target = 0.50 * self.enemigos + 1.20 * self.bombas + 1.50 * self.explosiones
        self.caos = max(0.0, min(10.0, 0.62 * self.caos + 0.38 * caos_target - 0.20 * self.powerups))
        self.dificultad = max(1.0, min(10.0, 1.0 + 0.55 * self.caos))

        # Store the instantaneous spawn rate (per-second) for game_loop queries
        self._spawn_rate = max(0.0, self.params.spawn_enemigos_base * pressure)

    # ── Accessors for game_loop ───────────────────────────────────────────

    def get_spawn_rate(self) -> float:
        """Current enemy spawn rate (enemies per second) driven by chaos pressure."""
        return self._spawn_rate

    def get_difficulty(self) -> float:
        """Current difficulty level [1.0 – 10.0]."""
        return self.dificultad

    def reduce_chaos(self, amount: float) -> None:
        """Externally reduce chaos (e.g. when a power-up is collected).

        Implements the negative feedback loop: power-ups → less chaos.
        """
        self.caos = max(0.0, self.caos - amount)

    # ── Snapshot ──────────────────────────────────────────────────────────

    def observe(self) -> dict[str, float]:
        return {
            "enemigos": self.enemigos,
            "bombas": self.bombas,
            "explosiones": self.explosiones,
            "powerups": self.powerups,
            "caos": self.caos,
            "dificultad": self.dificultad,
            "spawn_rate": self._spawn_rate,
        }
