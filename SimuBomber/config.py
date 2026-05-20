"""Global configuration values for the game."""

import pygame
pygame.init()
_info = pygame.display.Info()
WIDTH = int(_info.current_w * 0.95)
HEIGHT = int(_info.current_h * 0.90)

FPS = 60

WINDOW_TITLE = "SimuBomber: Caos"

BACKGROUND_COLOR = (18, 18, 24)
MAP_COLOR = (44, 52, 66)
MAP_BORDER_COLOR = (92, 105, 126)
PLAYER_COLOR = (80, 190, 255)
ENEMY_COLOR = (255, 104, 104)

MAP_MARGIN = 48

PLAYER_SIZE = 32
PLAYER_SPEED = 4

ENEMY_SIZE = 32
ENEMY_SPEED = 2
ENEMY_MOVE_INTERVAL = 30

# Bomb configuration
MAX_ACTIVE_BOMBS = 3
BOMB_COOLDOWN_MS = 400
BOMB_FUSE_MS = 2000
EXPLOSION_DURATION_MS = 400
EXPLOSION_RANGE = 2  # tiles in each direction
BOMB_SIZE = 32
BOMB_COLOR = (240, 200, 80)
EXPLOSION_COLOR = (255, 140, 60)
# Internal queue service time (ms) used only for observational modeling.
# It is not exposed to the player and does not delay bomb placement.
BOMB_QUEUE_SERVICE_MS = 250