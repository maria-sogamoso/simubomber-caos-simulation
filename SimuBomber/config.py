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