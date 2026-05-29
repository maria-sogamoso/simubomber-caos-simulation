"""Pause screen overlay."""
from __future__ import annotations
import pygame


def run_pause(screen: pygame.Surface, clock: pygame.time.Clock) -> bool:
    """Show pause overlay. Returns True to resume, False to quit to menu."""
    W, H    = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))

    font_big = pygame.font.SysFont("Arial", 52, bold=True)
    font_med = pygame.font.SysFont("Arial", 26)

    items = [
        ("Continuar",   True),
        ("Menú principal", False),
    ]
    selected = 0

    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return True
                if ev.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(items)
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(items)
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return items[selected][1]
            if ev.type == pygame.MOUSEMOTION:
                for i, (_, _) in enumerate(items):
                    if _item_rect(W, H, i, len(items)).collidepoint(ev.pos):
                        selected = i
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i, (_, val) in enumerate(items):
                    if _item_rect(W, H, i, len(items)).collidepoint(ev.pos):
                        return val

        screen.blit(overlay, (0, 0))

        title = font_big.render("PAUSA", True, (255, 230, 60))
        screen.blit(title, (W//2 - title.get_width()//2, H//2 - 100))

        for i, (label, _) in enumerate(items):
            col   = (255, 230, 60) if i == selected else (200, 200, 200)
            txt   = font_med.render(("▶ " if i == selected else "   ") + label, True, col)
            r     = _item_rect(W, H, i, len(items))
            screen.blit(txt, (r.x, r.y))

        hint = pygame.font.SysFont("Arial", 18).render("ESC para continuar  |  ↑↓ para navegar", True, (120,120,140))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 40))

        pygame.display.flip()


def _item_rect(W, H, i, n):
    total_h = n * 46
    y0      = H//2 - total_h//2 + 10
    return pygame.Rect(W//2 - 120, y0 + i*46, 240, 40)
