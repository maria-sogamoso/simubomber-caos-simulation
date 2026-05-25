"""Global configuration — SimuBomber: Caos."""
import pygame
pygame.init()
_info = pygame.display.Info()
WIDTH  = min(1280, int(_info.current_w * 0.95))
HEIGHT = min(800,  int(_info.current_h * 0.90))
FPS = 60
WINDOW_TITLE = "SimuBomber: Caos"

BACKGROUND_COLOR = (18, 18, 24)
TILE_SIZE = 48
BOMB_SIZE = 48
MAP_COLS  = 15
MAP_ROWS  = 11

# Hitbox inner margin (pixels shrunk on each side)
HB = 10   # entities use a (TILE_SIZE - 2*HB) x (TILE_SIZE - 2*HB) inner box

CHARACTER_STATS = {
    "char1": {"max_lives": 3, "speed": 3, "label": "Guerrero Élfico",
              "desc": "Equilibrado — vidas y velocidad medias."},
    "char2": {"max_lives": 5, "speed": 2, "label": "Gran Hechicera",
              "desc": "Resistente — más vidas, pero más lento."},
    "char3": {"max_lives": 2, "speed": 5, "label": "Lagarto Veloz",
              "desc": "Ágil — muy veloz, pero pocas vidas."},
}
DEFAULT_CHARACTER = "char1"

ENEMY1_SPEED = 2;  ENEMY1_MOVE_INTERVAL = 40
ENEMY2_SPEED = 3;  ENEMY2_MOVE_INTERVAL = 18
ENEMY3_SPEED = 2;  ENEMY3_MOVE_INTERVAL = 28

MAX_ACTIVE_BOMBS      = 3
BOMB_COOLDOWN_MS      = 500
BOMB_FUSE_MS          = 2200
EXPLOSION_DURATION_MS = 600
EXPLOSION_RANGE       = 2

LEVEL_MAPS = {
    1:[
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,2,0,0,0,2,0,0,0,2,0,0,1],
        [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
        [1,0,0,0,0,2,0,0,0,2,0,0,0,0,1],
        [1,2,1,0,1,0,1,2,1,0,1,0,1,2,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,2,1,0,1,0,1,2,1,0,1,0,1,2,1],
        [1,0,0,0,0,2,0,0,0,2,0,0,0,0,1],
        [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
        [1,0,0,2,0,0,0,2,0,0,0,2,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],
    2:[
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,2,0,2,0,0,0,2,0,2,0,0,1],
        [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
        [1,2,0,0,0,0,0,2,0,0,0,0,0,2,1],
        [1,0,1,2,1,0,1,0,1,0,1,2,1,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,1,2,1,0,1,0,1,0,1,2,1,0,1],
        [1,2,0,0,0,0,0,2,0,0,0,0,0,2,1],
        [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
        [1,0,0,2,0,2,0,0,0,2,0,2,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],
    3:[
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,2,0,0,0,0,0,2,0,0,0,1],
        [1,0,1,0,1,0,1,2,1,0,1,0,1,0,1],
        [1,0,0,2,0,0,0,0,0,0,0,2,0,0,1],
        [1,2,1,0,1,2,1,0,1,2,1,0,1,2,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,2,1,0,1,2,1,0,1,2,1,0,1,2,1],
        [1,0,0,2,0,0,0,0,0,0,0,2,0,0,1],
        [1,0,1,0,1,0,1,2,1,0,1,0,1,0,1],
        [1,0,0,0,2,0,0,0,0,0,2,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ],
}
TOTAL_LEVELS = 3

# Global options (mutated at runtime by options menu)
SHOW_HITBOXES = False
