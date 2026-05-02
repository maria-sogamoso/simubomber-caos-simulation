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
        enemy_start_x = self.game_map.rect.right - 80
        enemy_start_y = self.game_map.rect.bottom - 80

        self.player = Player(player_start_x, player_start_y, self.game_map.rect)
        self.enemy = Enemy(enemy_start_x, enemy_start_y, self.game_map.rect)

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
        if self.enemy is not None:
            self.enemy.update(self.player, self.bomb_system)

        # Update bomb system and handle explosion collisions
        self.bomb_system.update(dt)

        # Sample metrics
        bombs_active = len(self.bomb_system.bombs)
        explosions_active = sum(1 for b in self.bomb_system.bombs if b.is_exploding)
        tick = pygame.time.get_ticks()

        enemies = [self.enemy] if self.enemy is not None else []

        self.metrics.sample_frame(
            tick,
            dt,
            enemies,
            bombs_active,
            explosions_active
        )

        if self.enemy is not None and self.bomb_system.check_enemy_collision(self.enemy.rect):
            self.enemy = None

    def render(self) -> None:
        """Draw the current frame."""
        self.screen.fill(BACKGROUND_COLOR)
        self.game_map.draw(self.screen)
        self.player.draw(self.screen)
        if self.enemy is not None:
            self.enemy.draw(self.screen)

        # Draw bombs and explosions
        self.bomb_system.draw(self.screen)

        pygame.display.flip()

    def run(self) -> None:
        """Run the main loop until the window is closed."""
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()