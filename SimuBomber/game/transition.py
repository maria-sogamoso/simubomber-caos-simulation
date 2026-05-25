"""Level transition screen with animated fade + level name."""
from __future__ import annotations
import pygame


def run_transition(screen: pygame.Surface, clock: pygame.time.Clock,
                   level: int, total: int = 3) -> None:
    """Blocking fade-in/out transition between levels."""
    W, H  = screen.get_width(), screen.get_height()
    names = {1:"Nivel 1 — Naturaleza 🌿",
             2:"Nivel 2 — Cementerio ⚰️",
             3:"Nivel 3 — Mazmorra 🔥"}
    text  = names.get(level, f"Nivel {level}")

    font_big = pygame.font.SysFont("Arial", 56, bold=True)
    font_sm  = pygame.font.SysFont("Arial", 24)
    surf_big = font_big.render(text,                  True, (255, 230, 60))
    surf_sm  = font_sm.render(f"Nivel {level} de {total}", True, (180, 180, 200))

    # Quick fade-to-black + text hold + fade-out
    BG = (8, 8, 14)
    PHASES = [("in", 300), ("hold", 800), ("out", 300)]  # ms each
    overlay = pygame.Surface((W, H))

    start = pygame.time.get_ticks()
    total_dur = sum(d for _, d in PHASES)

    while True:
        dt  = clock.tick(60)
        now = pygame.time.get_ticks() - start

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                return

        if now >= total_dur:
            break

        # Compute alpha
        if now < PHASES[0][1]:
            alpha = int(255 * (now / PHASES[0][1]))
        elif now < PHASES[0][1] + PHASES[1][1]:
            alpha = 255
        else:
            elapsed = now - PHASES[0][1] - PHASES[1][1]
            alpha = int(255 * (1 - elapsed / PHASES[2][1]))
        alpha = max(0, min(255, alpha))

        overlay.fill(BG)
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))

        # Text
        if alpha > 100:
            text_alpha = min(255, (alpha - 100) * 3)
            for surf, yoff in [(surf_big, -30), (surf_sm, 40)]:
                ts = surf.copy()
                ts.set_alpha(text_alpha)
                screen.blit(ts, (W//2 - ts.get_width()//2, H//2 + yoff))

        pygame.display.flip()
