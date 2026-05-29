"""
Grid-aligned movement — the single source of truth for all entity physics.

Key guarantees:
1. Snap is applied BEFORE collision so entities enter corridors naturally.
2. Collision is checked per-axis using the PREVIOUSLY resolved position
   so entities cannot phase through walls or bombs on either axis.
3. Bomb collision uses the VISUAL rect (not hitbox) to catch bombs reliably.
"""
from __future__ import annotations
import pygame
from config import TILE_SIZE, HB

SNAP_SPEED  = 4    # px nudged per frame toward corridor centre
SNAP_MARGIN = 18   # activate snap within this many px of tile centre


def hitbox_of(rect: pygame.Rect) -> pygame.Rect:
    """Centered inner collision rect — always in the middle of the entity."""
    size = TILE_SIZE - HB * 2
    return pygame.Rect(rect.centerx - size // 2, rect.centery - size // 2,
                       size, size)


def _snap(val: int, origin: int) -> int:
    """Return nudge (-SNAP_SPEED..+SNAP_SPEED) toward the nearest tile centre."""
    offset = val - origin
    idx    = offset // TILE_SIZE
    centre = origin + idx * TILE_SIZE + TILE_SIZE // 2
    diff   = centre - val
    if abs(diff) <= SNAP_MARGIN:
        return max(-SNAP_SPEED, min(SNAP_SPEED, diff))
    return 0


def _wall_hit(rect: pygame.Rect, game_map) -> bool:
    """True when the hitbox of rect overlaps a solid tile."""
    hb = hitbox_of(rect)
    mr = game_map.rect
    lc = max(0, (hb.left       - mr.left) // TILE_SIZE)
    rc = min(game_map.cols - 1, (hb.right  - 1 - mr.left) // TILE_SIZE)
    tr = max(0, (hb.top        - mr.top)  // TILE_SIZE)
    br = min(game_map.rows - 1, (hb.bottom - 1 - mr.top)  // TILE_SIZE)
    for r in range(tr, br + 1):
        for c in range(lc, rc + 1):
            if game_map.tile_at(r, c) != 0:
                return True
    return False


def _bomb_hit(new_rect: pygame.Rect, old_rect: pygame.Rect,
              bomb_system) -> bool:
    """
    True when new_rect would collide with a bomb that old_rect was NOT
    already touching (so it can exit freely).
    ALL bombs block immediately — no grace period for anyone.
    """
    for b in bomb_system.bombs:
        if old_rect.colliderect(b.rect):
            continue          # already inside → let it escape
        if new_rect.colliderect(b.rect):
            return True
    return False


def move_and_collide(entity, dx: int, dy: int,
                     game_map, bomb_system) -> None:
    """
    Move entity by (dx, dy) with:
      • Corridor-assist snap on the perpendicular axis
      • Axis-separated wall + bomb collision
      • Map-bounds clamp

    Each axis is resolved independently using the position left by the
    previous axis so entities cannot phase through obstacles diagonally.
    """
    mr  = game_map.rect

    # ── Snap assist (applied before movement so snap itself isn't blocked) ──
    if dx != 0 and dy == 0:
        ny = _snap(entity.rect.centery, mr.top)
        entity.rect.y += ny

    if dy != 0 and dx == 0:
        nx = _snap(entity.rect.centerx, mr.left)
        entity.rect.x += nx

    # ── X axis ───────────────────────────────────────────────────────────────
    old_x = entity.rect.x
    entity.rect.x += dx
    if _wall_hit(entity.rect, game_map) or \
       _bomb_hit(entity.rect, pygame.Rect(old_x, entity.rect.y, entity.rect.width, entity.rect.height), bomb_system):
        entity.rect.x = old_x

    # ── Y axis ───────────────────────────────────────────────────────────────
    old_y = entity.rect.y
    entity.rect.y += dy
    if _wall_hit(entity.rect, game_map) or \
       _bomb_hit(entity.rect, pygame.Rect(entity.rect.x, old_y, entity.rect.width, entity.rect.height), bomb_system):
        entity.rect.y = old_y

    # ── Bounds clamp ─────────────────────────────────────────────────────────
    entity.rect.x = max(mr.left, min(entity.rect.x, mr.right  - TILE_SIZE))
    entity.rect.y = max(mr.top,  min(entity.rect.y, mr.bottom - TILE_SIZE))
