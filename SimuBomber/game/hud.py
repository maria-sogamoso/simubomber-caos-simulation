"""HUD — hearts, level label, bomb counter, speed indicator."""
from __future__ import annotations
import pygame
from assets_loader import get_sprite

HEART_SIZE = 28
HEART_GAP  = 5


def draw_hud(screen: pygame.Surface, player, level: int, bomb_system) -> None:
    font_big = pygame.font.SysFont("Arial", 22, bold=True)
    font_sm  = pygame.font.SysFont("Arial", 16)

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
    bsurf  = font_sm.render(f"💣 {active}/{3}", True, (200, 200, 200))
    screen.blit(bsurf, (screen.get_width() - bsurf.get_width() - 12, 12))

    # Speed boost indicator
    if getattr(player, "speed_boost_active", False):
        ssurf = font_sm.render("⚡ VELOCIDAD", True, (80, 230, 80))
        screen.blit(ssurf, (screen.get_width() - ssurf.get_width() - 12, 32))


def draw_message(screen: pygame.Surface, text: str,
                 color=(255,255,100), size=48) -> None:
    font   = pygame.font.SysFont("Arial", size, bold=True)
    shadow = font.render(text, True, (0, 0, 0))
    surf   = font.render(text, True, color)
    cx = screen.get_width()//2  - surf.get_width()//2
    cy = screen.get_height()//2 - surf.get_height()//2
    screen.blit(shadow, (cx+3, cy+3))
    screen.blit(surf,   (cx,   cy))
