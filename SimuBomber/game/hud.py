"""HUD — hearts, level label, bomb counter, speed indicator, chaos bar."""
from __future__ import annotations
import pygame
from assets_loader import get_sprite

HEART_SIZE = 28
HEART_GAP  = 5


def draw_hud(screen: pygame.Surface, player, level: int, bomb_system,
             chaos: float = 0.0, difficulty: float = 1.0) -> None:
    font_big = pygame.font.SysFont("Arial", 22, bold=True)
    font_sm  = pygame.font.SysFont("Arial", 16)
    font_xs  = pygame.font.SysFont("Arial", 13)

    hf = get_sprite("powerup_heart_full.png")
    hh = get_sprite("powerup_heart_half.png")

    lives     = float(player.lives)
    max_lives = int(player.max_lives)

    # Draw hearts
    for i in range(max_lives):
        rx = 12 + i * (HEART_SIZE + HEART_GAP)
        ry = 10
        r  = pygame.Rect(rx, ry, HEART_SIZE, HEART_SIZE)
        if lives >= 1.0:
            if hf: screen.blit(pygame.transform.scale(hf, (HEART_SIZE, HEART_SIZE)), r)
            else:  pygame.draw.rect(screen, (220, 40, 40), r)
        elif lives >= 0.5:
            if hh: screen.blit(pygame.transform.scale(hh, (HEART_SIZE, HEART_SIZE)), r)
            else:  pygame.draw.rect(screen, (180, 80, 80), r)
        else:
            pygame.draw.rect(screen, (55, 55, 55), r)
            pygame.draw.rect(screen, (100, 100, 100), r, 1)
        lives -= 1.0

    # Level name centred
    names = {1: "Nivel 1 — Naturaleza", 2: "Nivel 2 — Cementerio", 3: "Nivel 3 — Mazmorra"}
    lsurf = font_big.render(names.get(level, f"Nivel {level}"), True, (220, 220, 80))
    screen.blit(lsurf, (screen.get_width()//2 - lsurf.get_width()//2, 8))

    # Bomb count
    active = sum(1 for b in bomb_system.bombs if b.is_active())
    bsurf  = font_sm.render(f"Bomba: {active}/{3}", True, (200, 200, 200))
    screen.blit(bsurf, (screen.get_width() - bsurf.get_width() - 12, 12))

    # Speed boost indicator
    if getattr(player, "speed_boost_active", False):
        ssurf = font_sm.render("VELOCIDAD x2", True, (80, 230, 80))
        screen.blit(ssurf, (screen.get_width() - ssurf.get_width() - 12, 32))

    # ── Chaos & Difficulty bar (system dynamics feedback) ──────────────
    bar_w, bar_h = 130, 10
    bar_x = screen.get_width() - bar_w - 12
    bar_y = 54

    # Chaos bar: green → yellow → red
    chaos_frac = min(1.0, max(0.0, chaos / 10.0))
    if chaos_frac < 0.5:
        cr = int(60 + 390 * chaos_frac)
        cg = int(200 - 100 * chaos_frac)
        cb = 60
    else:
        cr = min(255, int(255))
        cg = int(150 - 240 * (chaos_frac - 0.5))
        cb = int(60 - 60 * (chaos_frac - 0.5))
    cr, cg, cb = max(0, min(255, cr)), max(0, min(255, cg)), max(0, min(255, cb))

    # Background
    pygame.draw.rect(screen, (40, 40, 50), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
    # Filled portion
    fill_w = int(bar_w * chaos_frac)
    if fill_w > 0:
        pygame.draw.rect(screen, (cr, cg, cb), (bar_x, bar_y, fill_w, bar_h))
    # Border
    pygame.draw.rect(screen, (100, 100, 120), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 1)

    # Label
    chaos_label = font_xs.render(f"Caos: {chaos:.1f}  Dif: {difficulty:.1f}", True, (170, 170, 190))
    screen.blit(chaos_label, (bar_x, bar_y + bar_h + 2))


def draw_message(screen: pygame.Surface, text: str,
                 color=(255,255,100), size=48) -> None:
    font   = pygame.font.SysFont("Arial", size, bold=True)
    shadow = font.render(text, True, (0, 0, 0))
    surf   = font.render(text, True, color)
    cx = screen.get_width()//2  - surf.get_width()//2
    cy = screen.get_height()//2 - surf.get_height()//2
    screen.blit(shadow, (cx+3, cy+3))
    screen.blit(surf,   (cx,   cy))
