"""Main game loop and orchestration."""

from __future__ import annotations

import pygame

import os
import time
from config import BACKGROUND_COLOR, FPS, HEIGHT, WINDOW_TITLE, WIDTH, PLAYER_SIZE
from game.random_enemy import RandomEnemy
from game.agent_enemy import AgentEnemy
from game.map import Map
from game.player import Player
from game.bomb import BombSystem
from game.powerup import PowerUpSystem
from game.metrics import MetricsSystem
from game.dynamics import SistemaDinamicoRuntime


class GameLoop:
    """Encapsulates the main loop, update, and render cycle."""

    STATE_PLAYING = "playing"
    STATE_VICTORY = "victory"
    STATE_DEFEAT = "defeat"

    def __init__(self, master_seed: int | None = None) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = self.STATE_PLAYING

        self.game_map = Map()

        player_start_x = self.game_map.rect.left + 48
        player_start_y = self.game_map.rect.top + 48

        self.player = Player(player_start_x, player_start_y, self.game_map.rect)

        # Spawn 2 RandomEnemy and 1 AgentEnemy using per-enemy derived seeds
        base = master_seed if master_seed is not None else int(time.time() * 1000000)
        enemies_positions = [
            (self.game_map.rect.right - 80, self.game_map.rect.bottom - 80),
            (self.game_map.rect.left + 80, self.game_map.rect.bottom - 80),
            (self.game_map.rect.centerx, self.game_map.rect.top + 80),
        ]

        self.enemies = []
        for i, (ex, ey) in enumerate(enemies_positions):
            salt = int.from_bytes(os.urandom(4), 'little')
            seed = (base + i * 1009 + salt) & 0xFFFFFFFF
            if i < 2:
                # RandomEnemy
                self.enemies.append(RandomEnemy(ex, ey, self.game_map.rect, seed=seed))
            else:
                # AgentEnemy
                self.enemies.append(AgentEnemy(ex, ey, self.game_map.rect, seed=seed))
        self.system_chaos_level = 0.0

        # Bomb system: encapsulates placement rules and bombs
        self.bomb_system = BombSystem()
        self.powerup_system = PowerUpSystem()
        # Runtime system dynamics (stocks & flows)
        self.dynamics = SistemaDinamicoRuntime()
        # Metrics system for logging and validation
        self.metrics = MetricsSystem(self.game_map.rect)

        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 34)

    def handle_events(self) -> None:
        """Process pygame events and detect quit requests."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state != self.STATE_PLAYING:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Send player's raw position; BombSystem will align internally
                    now = pygame.time.get_ticks()
                    px, py = self.player.rect.x, self.player.rect.y
                    # The bomb system records the request internally and resolves it immediately.
                    self.bomb_system.request_place_bomb(now, (px, py))

    def update(self, dt: int) -> None:
        """Advance game state by dt milliseconds."""
        if self.state != self.STATE_PLAYING:
            return

        # Player movement with collision resolution against bombs
        old_pos = self.player.rect.topleft
        self.player.update()
        # Player may pass bombs only during their initial grace window; pass True
        # to indicate the player type that can pass recently-placed bombs.
        self.resolve_collisions(self.player.rect, old_pos, can_pass_bombs=True)
        # Update bomb system and handle explosion collisions

        self.bomb_system.update(dt)

        # Check for player damage from explosions (own bombs = 0.5, others = 1.0)
        damage = self.bomb_system.get_player_explosion_damage(self.player.rect)
        if damage > 0.0:
            self.player.take_damage(damage, pygame.time.get_ticks())
        self.powerup_system.update(self.player)
        # Calculate system chaos level

        bombs_active = len(self.bomb_system.bombs)
        explosions_active = sum(1 for b in self.bomb_system.bombs if b.is_exploding)
        enemies_count = len(self.enemies)
        powerups_count = len(self.powerup_system.powerups)

        # Feed observed counts into the runtime dynamics and advance it
        self.dynamics.enemigos = float(enemies_count)
        self.dynamics.bombas = float(bombs_active)
        self.dynamics.explosiones = float(explosions_active)
        self.dynamics.powerups = float(powerups_count)
        self.dynamics.step(dt)
        self.system_chaos_level = min(10.0, self.dynamics.caos)

        # Update all enemies. Only AgentEnemy uses chaos and perception.
        for enemy in self.enemies:
            if isinstance(enemy, AgentEnemy):
                enemy.apply_chaos(self.system_chaos_level)

            old_pos = enemy.rect.topleft

            if isinstance(enemy, AgentEnemy):
                enemy.update(self.player, self.bomb_system)
            else:
                enemy.update()

            # Enemies must never pass through bombs
            self.resolve_collisions(enemy.rect, old_pos, can_pass_bombs=False)

        previous_enemies = self.enemies.copy()
        # Handle enemy-bomb collisions
        self.enemies = [
            enemy for enemy in self.enemies
            if not self.bomb_system.check_enemy_collision(enemy.rect)
        ]

        removed_enemies = [enemy for enemy in previous_enemies if enemy not in self.enemies]
        for enemy in removed_enemies:
            self.powerup_system.spawn_from_enemy(enemy.rect.center)

        # Handle player-enemy collisions with temporary invulnerability
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                self.player.take_damage(1.0, pygame.time.get_ticks())
                break

        self._update_game_state()

        # Sample metrics
        tick = pygame.time.get_ticks()
        self.metrics.sample_frame(
            tick,
            dt,
            self.enemies,
            bombs_active,
            explosions_active
        )
        self.metrics.sample_bomb_queue(tick, self.bomb_system.observe_queue())
        # Optionally log dynamics snapshot
        self.metrics.sample_dynamics(tick, self.dynamics.observe())

    def _update_game_state(self) -> None:
        """Resolve end conditions after each simulation step."""
        if self.player.lives <= 0:
            self.state = self.STATE_DEFEAT
        elif not self.enemies:
            self.state = self.STATE_VICTORY

    def draw_ui(self) -> None:
        """Draw the player's lives as simple heart rectangles."""
        start_x = 10
        start_y = 10
        heart_size = 20
        spacing = 5

        lives = float(self.player.lives)
        max_lives = int(self.player.max_lives)

        for index in range(max_lives):
            x = start_x + index * (heart_size + spacing)
            rect = pygame.Rect(x, start_y, heart_size, heart_size)

            if lives >= 1.0:
                pygame.draw.rect(self.screen, (220, 40, 40), rect)
            elif lives >= 0.5:
                half_rect = pygame.Rect(x, start_y, heart_size // 2, heart_size)
                pygame.draw.rect(self.screen, (220, 40, 40), half_rect)
                pygame.draw.rect(self.screen, (130, 130, 130), rect, 1)
            else:
                pygame.draw.rect(self.screen, (130, 130, 130), rect, 1)

            lives -= 1.0

    def render(self) -> None:
        """Draw the current frame."""
        self.screen.fill(BACKGROUND_COLOR)
        self.game_map.draw(self.screen)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw bombs and explosions
        self.bomb_system.draw(self.screen)

        self.powerup_system.draw(self.screen)

        self.draw_ui()

        if self.state != self.STATE_PLAYING:
            self._draw_end_screen()

        pygame.display.flip()

    def _draw_end_screen(self) -> None:
        """Render the victory/defeat overlay."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        if self.state == self.STATE_VICTORY:
            title = "VICTORIA"
            subtitle = "Super bien de pollo! , todos los enemigos derrotados"
            accent = (70, 200, 120)
        else:
            title = "DERROTA"
            subtitle = "Apague y vamonos , el jugador ha perdido todas sus vidas"
            accent = (220, 70, 70)

        title_surface = self.title_font.render(title, True, accent)
        subtitle_surface = self.subtitle_font.render(subtitle, True, (240, 240, 240))
        hint_surface = self.subtitle_font.render("Presione Esc, Enter, o Space para salir", True, (210, 210, 210))

        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        self.screen.blit(title_surface, title_surface.get_rect(center=(center_x, center_y - 50)))
        self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(center_x, center_y + 10)))
        self.screen.blit(hint_surface, hint_surface.get_rect(center=(center_x, center_y + 55)))

    def resolve_collisions(self, rect: pygame.Rect, old_pos: tuple[int, int], can_pass_bombs: bool) -> None:
        """Resolve collisions against blocking objects (currently bombs only).
        If an entity's rect collides with a bomb that is currently blocking,
        reset its position to `old_pos`. Players can optionally pass bombs
        during the short grace period after placement by setting
        `can_pass_bombs=True`.
        """
        now = pygame.time.get_ticks()

        for bomb in self.bomb_system.bombs:
            # If this caller allows passing bombs (player grace window), skip
            # only during the bomb's short non-blocking window.
            if can_pass_bombs and not bomb.is_blocking(now):
                continue

            was_inside = pygame.Rect(old_pos, rect.size).colliderect(bomb.rect)
            is_inside = rect.colliderect(bomb.rect)

            if was_inside:
                continue

            if is_inside:
                rect.x, rect.y = old_pos
                return

    def run(self) -> None:
        """Run the main loop until the window is closed."""
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()