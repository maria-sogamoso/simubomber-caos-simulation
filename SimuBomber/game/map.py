"""Tile-based map — visually distinct floor/wall/breakable, blue-border breakables."""
from __future__ import annotations
import random
import pygame
from config import TILE_SIZE, WIDTH, HEIGHT, MAP_COLS, MAP_ROWS, LEVEL_MAPS
from assets_loader import get_tile

BLUE_BORDER = (55, 120, 255)
BLUE_CORNER = (80, 160, 255)

THEME = {
    1: {"bg":(55,95,38),  "floor":(88,142,55), "floor2":(78,130,48),
        "fixed":(40,72,26),"break":(110,82,44)},
    2: {"bg":(50,58,45),  "floor":(72,85,60),  "floor2":(62,75,52),
        "fixed":(42,50,38),"break":(92,74,55)},
    3: {"bg":(20,14,28),  "floor":(52,40,65),  "floor2":(44,32,55),
        "fixed":(16,10,24),"break":(78,58,42)},
}


class Map:
    def __init__(self, level: int = 1) -> None:
        self.level = level
        self.cols  = MAP_COLS
        self.rows  = MAP_ROWS
        map_w = self.cols * TILE_SIZE
        map_h = self.rows * TILE_SIZE
        self.rect = pygame.Rect((WIDTH-map_w)//2, (HEIGHT-map_h)//2, map_w, map_h)

        self.grid: list[list[int]] = [row[:] for row in LEVEL_MAPS.get(level, LEVEL_MAPS[1])]
        self._trects = [
            [pygame.Rect(self.rect.left + c*TILE_SIZE, self.rect.top + r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
             for c in range(self.cols)]
            for r in range(self.rows)
        ]
        th = THEME[level]; self._theme = th
        rng = random.Random(level * 1337)
        self._alt  = [[rng.random()<0.22 for _ in range(self.cols)] for _ in range(self.rows)]
        self._wvar = [[rng.random()<0.45 for _ in range(self.cols)] for _ in range(self.rows)]

        self._fl  = self._build_floor(level, "floor",          th["floor"])
        self._fl2 = self._build_floor(level, "floor_alt",      th["floor2"])
        self._fl_v  = self._build_floor(level, "floor_path_v", th["floor"])
        self._fl_h  = self._build_floor(level, "floor_path_h", th["floor"])
        self._fl_c  = self._build_floor(level, "floor_path_c", th["floor"])
        self._fl_c2 = self._build_floor(level, "floor_path_c2",th["floor"])
        self._fl_c3 = self._build_floor(level, "floor_path_c3",th["floor"])
        self._fl_c4 = self._build_floor(level, "floor_path_c4",th["floor"])
        self._fl_x  = self._build_floor(level, "floor_path_x", th["floor"])
        self._wf  = self._build_wall (level, "wall_fixed",     th["fixed"], False)
        self._wf2 = self._build_wall (level, "wall_fixed2",    th["fixed"], False)
        self._wb  = self._build_wall (level, "wall_breakable",  th["break"], True)
        self._wb2 = self._build_wall (level, "wall_breakable2", th["break"], True)
        self._wb_broken  = self._build_broken(level, "wall_breakable")
        self._wb2_broken = self._build_broken(level, "wall_breakable2")
        self._wp1 = self._build_path(level, "wall_path_1")
        self._wp2 = self._build_path(level, "wall_path_2")
        self._wp3 = self._build_path(level, "wall_path_3")
        self._wp4 = self._build_path(level, "wall_path_4")

    def _build_floor(self, level, name, fallback):
        TS = TILE_SIZE
        surf = pygame.Surface((TS, TS))
        bg = get_tile(level, f"{name}_bg")
        if bg:
            surf.blit(pygame.transform.smoothscale(bg, (TS, TS)), (0, 0))
        else:
            surf.fill(fallback)
        tile = get_tile(level, name)
        if tile:
            surf.blit(pygame.transform.smoothscale(tile, (TS, TS)), (0, 0))
        else:
            surf.fill(fallback)
        return surf

    def _build_wall(self, level, name, fallback, is_break):
        TS = TILE_SIZE
        surf = pygame.Surface((TS, TS))
        base = get_tile(level, "wall_bg")
        if base:
            surf.blit(pygame.transform.smoothscale(base, (TS, TS)), (0, 0))
        else:
            surf.fill(self._theme["floor"])
        bg = get_tile(level, f"{name}_bg")
        if bg:
            surf.blit(pygame.transform.smoothscale(bg, (TS, TS)), (0, 0))
        tile = get_tile(level, name)
        if tile:
            surf.blit(pygame.transform.smoothscale(tile, (TS, TS)), (0, 0))
        else:
            surf.fill(fallback)
        if is_break and level != 1:
            for i in range(3):
                pygame.draw.rect(surf, BLUE_BORDER, (i, i, TS-2*i, TS-2*i), 1)
            for cx, cy in [(0,0),(TS-7,0),(0,TS-7),(TS-7,TS-7)]:
                pygame.draw.rect(surf, BLUE_CORNER, (cx, cy, 7, 7))
        return surf

    def _build_broken(self, level, name):
        TS = TILE_SIZE
        surf = pygame.Surface((TS, TS))
        base = get_tile(level, "wall_bg")
        if base:
            surf.blit(pygame.transform.smoothscale(base, (TS, TS)), (0, 0))
        else:
            surf.fill(self._theme["floor"])
        bg = get_tile(level, f"{name}_bg")
        if bg:
            surf.blit(pygame.transform.smoothscale(bg, (TS, TS)), (0, 0))
        return surf

    def _build_path(self, level, name):
        TS = TILE_SIZE
        surf = pygame.Surface((TS, TS))
        base = get_tile(level, "wall_bg")
        if base:
            surf.blit(pygame.transform.smoothscale(base, (TS, TS)), (0, 0))
        else:
            surf.fill(self._theme["floor"])
        tile = get_tile(level, name)
        if tile:
            surf.blit(pygame.transform.smoothscale(tile, (TS, TS)), (0, 0))
        return surf

    # ── accessors ────────────────────────────────────────────────────────────
    def tile_at(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            v = self.grid[row][col]
            return 0 if v >= 3 else v
        return 1
    def pixel_to_tile(self, px, py):
        col = (px - self.rect.left) // TILE_SIZE
        row = (py - self.rect.top)  // TILE_SIZE
        return (max(0, min(self.rows-1, row)), max(0, min(self.cols-1, col)))
    def tile_rect(self, row, col):
        return self._trects[row][col]
    def break_tile(self, row, col):
        if 0<=row<self.rows and 0<=col<self.cols and self.grid[row][col]==2:
            self.grid[row][col]=99; return True
        return False
    def is_solid(self, row, col): return self.tile_at(row, col) != 0

    # ── drawing ──────────────────────────────────────────────────────────────
    def draw(self, screen):
        pygame.draw.rect(screen, self._theme["bg"], self.rect)
        for r in range(self.rows):
            for c in range(self.cols):
                rect = self._trects[r][c]; val = self.grid[r][c]
                if   val == 0: screen.blit(self._fl2 if self._alt[r][c] else self._fl, rect)
                elif val == 1: screen.blit(self._wf2 if self._wvar[r][c] else self._wf, rect)
                elif val == 2: screen.blit(self._wb2 if self._wvar[r][c] else self._wb, rect)
                elif val == 3: screen.blit(self._fl_v, rect)
                elif val == 4: screen.blit(self._fl_h, rect)
                elif val == 5: screen.blit(self._fl_c, rect)
                elif val == 6: screen.blit(self._fl_c2, rect)
                elif val == 7: screen.blit(self._fl_c3, rect)
                elif val == 8: screen.blit(self._fl_c4, rect)
                elif val == 9: screen.blit(self._fl_x, rect)
                elif val == 10: screen.blit(self._wp1, rect)
                elif val == 11: screen.blit(self._wp2, rect)
                elif val == 12: screen.blit(self._wp3, rect)
                elif val == 13: screen.blit(self._wp4, rect)
                elif val == 99: screen.blit(self._wb2_broken if self._wvar[r][c] else self._wb_broken, rect)
        pygame.draw.rect(screen, (55, 65, 85), self.rect, 2)
