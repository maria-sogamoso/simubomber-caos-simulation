"""Main game loop and orchestration."""

from __future__ import annotations

import pygame

from config import BACKGROUND_COLOR, FPS, HEIGHT, WINDOW_TITLE, WIDTH, PLAYER_SIZE
from game.enemy import Enemy
from game.map import Map
from game.player import Player
from game.bomb import BombSystem
from game.metrics import MetricsSystem


class GameLoop:
    """Encapsulates the main loop, update, and render cycle."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.game_map = Map()

        player_start_x = self.game_map.rect.left + 48
        player_start_y = self.game_map.rect.top + 48

        self.player = Player(player_start_x, player_start_y, self.game_map.rect)

        # Spawn 3 enemies at different positions
        self.enemies = [
            Enemy(
                self.game_map.rect.right - 80,
                self.game_map.rect.bottom - 80,
                self.game_map.rect
            ),
            Enemy(
                self.game_map.rect.left + 80,
                self.game_map.rect.bottom - 80,
                self.game_map.rect
            ),
            Enemy(
                self.game_map.rect.centerx,
                self.game_map.rect.top + 80,
                self.game_map.rect
            ),
        ]
        self.system_chaos_level = 0.0

        # Bomb system: encapsulates placement rules and bombs
        self.bomb_system = BombSystem()
        # Metrics system for logging and validation
        self.metrics = MetricsSystem(self.game_map.rect)

    def handle_events(self) -> None:
        """Process pygame events and detect quit requests."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Send player's raw position; BombSystem will align internally
                    now = pygame.time.get_ticks()
                    px, py = self.player.rect.x, self.player.rect.y
                    self.bomb_system.try_place_bomb(now, (px, py))

    def update(self, dt: int) -> None:
        """Advance game state by dt milliseconds."""
        self.player.update()
        # Update bomb system and handle explosion collisions

        self.bomb_system.update(dt)

        # Check for player damage from explosions (own bombs = 0.5, others = 1.0)
        damage = self.bomb_system.get_player_explosion_damage(self.player.rect)
        if damage > 0.0:
            self.player.take_damage(damage, pygame.time.get_ticks())
        # Calculate system chaos level

        bombs_active = len(self.bomb_system.bombs)
        explosions_active = sum(1 for b in self.bomb_system.bombs if b.is_exploding)
        enemies_count = len(self.enemies)
        raw_chaos = enemies_count + bombs_active + explosions_active
        self.system_chaos_level = min(10.0, raw_chaos)

        # Apply chaos to all enemies
        for enemy in self.enemies:
            enemy.apply_chaos(self.system_chaos_level)

        # Update all enemies
        for enemy in self.enemies:
            enemy.update(self.player, self.bomb_system)

        # Handle enemy-bomb collisions
        self.enemies = [
            enemy for enemy in self.enemies
            if not self.bomb_system.check_enemy_collision(enemy.rect)
        ]

        # Handle player-enemy collisions with temporary invulnerability
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                self.player.take_damage(1.0, pygame.time.get_ticks())
                break

        if self.player.lives <= 0:
            self.running = False

        # Sample metrics
        tick = pygame.time.get_ticks()
        self.metrics.sample_frame(
            tick,
            dt,
            self.enemies,
            bombs_active,
            explosions_active
        )

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

        self.draw_ui()

        pygame.display.flip()

    def run(self) -> None:
        """Run the main loop until the window is closed."""
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()