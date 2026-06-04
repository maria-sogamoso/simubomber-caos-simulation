"""
SimuBomber: Caos — Menu system.
Main menu : pixel-art stone bg, story block, chars on sides  (V7).
Sub-menus : dark gradient bg + floating particles, clean panels  (V5 style).
"""
from __future__ import annotations
import math, os
import pygame
import config
from config import WIDTH, HEIGHT, CHARACTER_STATS
from assets_loader import get_char_frames
from game.sounds import play
from game import music

# ── Paths ─────────────────────────────────────────────────────────────────────
_ASSETS    = os.path.join(os.path.dirname(__file__), '..', 'assets')
_FONT_PATH = os.path.join(_ASSETS, 'NormalFont.ttf')

def _pxfont(size):
    if os.path.exists(_FONT_PATH):
        return pygame.font.Font(_FONT_PATH, size)
    return pygame.font.SysFont("Arial", size, bold=True)

def _sf(size, bold=False, italic=False):
    return pygame.font.SysFont("Arial", size, bold=bold, italic=italic)

# ── Colour palette (main menu — stone/gold) ───────────────────────────────────
STONE   = (52, 46, 68)
STONE_D = (32, 26, 46)
STONE_H = (76, 66, 94)
GOLD    = (255, 210, 50)
LGOLD   = (255, 235, 120)
WHITE   = (232, 232, 245)
DIM     = (128, 122, 152)
RED     = (218, 62, 62)
CHAR_C  = {"char1": (100, 195, 255), "char2": (195, 110, 255), "char3": (85, 230, 125)}

# ── Colour palette (sub-menus — V5 style) ─────────────────────────────────────
C_BG1   = (10,   6,  20)
C_BG2   = (26,  16,  48)
C_GOLD  = (255, 215,  60)
C_LGOLD = (255, 235, 120)
C_WHITE = (235, 235, 245)
C_DIM   = (140, 140, 165)
C_BLUE  = (90,  130, 220)
C_PINK  = (240, 140, 200)
C_GREEN = (80,  210, 130)
CHAR_PAL = {"char1": (100, 195, 255),
            "char2": (195, 110, 255),
            "char3": (85,  230, 125)}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU BACKGROUND — stone tiles + vignette  (V7)
# ═══════════════════════════════════════════════════════════════════════════════
_STONE_TILE: pygame.Surface | None = None

def _make_stone_tile(s=48) -> pygame.Surface:
    surf = pygame.Surface((s, s)); surf.fill(STONE)
    pygame.draw.line(surf, STONE_D, (0, s//2), (s, s//2), 1)
    pygame.draw.line(surf, STONE_D, (s//2, 0), (s//2, s//2), 1)
    pygame.draw.line(surf, STONE_H, (0, 0), (s, 0), 1)
    pygame.draw.line(surf, STONE_H, (0, 0), (0, s//2), 1)
    pygame.draw.line(surf, STONE_H, (s//2, s//2), (s//2, s), 1)
    pygame.draw.line(surf, STONE_D, (s-1, 0), (s-1, s), 1)
    pygame.draw.line(surf, STONE_D, (0, s-1), (s, s-1), 1)
    return surf

def _draw_stone_bg(screen: pygame.Surface) -> None:
    global _STONE_TILE
    if _STONE_TILE is None:
        _STONE_TILE = _make_stone_tile()
    ts = 48
    for gy in range(0, HEIGHT, ts):
        for gx in range(0, WIDTH, ts):
            screen.blit(_STONE_TILE, (gx, gy))
    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = WIDTH // 2, HEIGHT // 2
    for band in range(10, 0, -1):
        rx, ry = int(WIDTH * band / 10), int(HEIGHT * band / 10)
        a = int(160 * (1.0 - band / 10.0))
        pygame.draw.ellipse(vig, (0, 0, 0, a), (cx-rx, cy-ry, rx*2, ry*2), 5)
    screen.blit(vig, (0, 0))

# ═══════════════════════════════════════════════════════════════════════════════
# SUB-MENU BACKGROUND — dark gradient + floating particles  (V5)
# ═══════════════════════════════════════════════════════════════════════════════
class _Particle:
    import random as _r
    _rng = _r.Random()

    def __init__(self):
        self.reset()

    def reset(self):
        rng = _Particle._rng
        self.x   = rng.uniform(0, WIDTH)
        self.y   = rng.uniform(0, HEIGHT)
        self.vy  = rng.uniform(-0.3, -0.9)
        self.vx  = rng.uniform(-0.2, 0.2)
        self.r   = rng.uniform(1, 3)
        self.col = rng.choice([(255,215,60),(180,140,255),(100,200,255),(255,140,180)])
        self.life = rng.uniform(0.3, 1.0)
        self.age  = 0.0
        self.dur  = rng.uniform(3.0, 8.0)

    def update(self, dt: float):
        self.x   += self.vx * dt * 40
        self.y   += self.vy * dt * 40
        self.age += dt / self.dur
        if self.age >= 1.0 or self.y < -10:
            self.reset()

    def draw(self, screen: pygame.Surface):
        a = math.sin(self.age * math.pi)
        alpha = int(200 * a * self.life)
        if alpha < 10:
            return
        d = int(self.r * 2 + 1) * 2
        s = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, alpha), (d//2, d//2), int(self.r) + 1)
        screen.blit(s, (int(self.x - self.r), int(self.y - self.r)))


_particles: list[_Particle] = [_Particle() for _ in range(60)]


def _draw_bg(screen: pygame.Surface, tick_ms: int) -> None:
    """Gradient + animated particles + tiled floor strip — used by all sub-menus."""
    for y in range(0, HEIGHT, 2):
        t = y / HEIGHT
        r = int(C_BG1[0] * (1-t) + C_BG2[0] * t)
        g = int(C_BG1[1] * (1-t) + C_BG2[1] * t)
        b = int(C_BG1[2] * (1-t) + C_BG2[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y),   (WIDTH, y))
        pygame.draw.line(screen, (r, g, b), (0, y+1), (WIDTH, y+1))
    dt = 1 / 60
    for p in _particles:
        p.update(dt)
        p.draw(screen)
    tw = 48
    strip_y = HEIGHT - tw - 10
    strip_col = (30, 20, 50)
    for i in range(WIDTH // tw + 2):
        offset = int(tick_ms * 0.02) % tw
        rx = i * tw - offset
        pygame.draw.rect(screen, strip_col, (rx, strip_y, tw-2, tw-2))
        pygame.draw.rect(screen, (50, 35, 80), (rx, strip_y, tw-2, tw-2), 1)


# ── Shared draw helpers ────────────────────────────────────────────────────────
def _px_border(screen, x, y, w, h, color=GOLD, thick=3) -> None:
    """Pixel-art gold border with corner accents — used by main-menu panels."""
    pygame.draw.rect(screen, color, (x, y, w, h), thick)
    C = 6
    for cx, cy in [(x, y), (x+w-C, y), (x, y+h-C), (x+w-C, y+h-C)]:
        pygame.draw.rect(screen, LGOLD, (cx, cy, C, C))

def _panel_main(screen, x, y, w, h, fill=(12, 8, 24, 230), border=GOLD) -> None:
    """Semi-transparent panel with pixel-art border — main menu."""
    s = pygame.Surface((w, h), pygame.SRCALPHA); s.fill(fill)
    screen.blit(s, (x, y))
    _px_border(screen, x, y, w, h, border)

def _panel(screen, x, y, w, h, alpha=215, border=C_BLUE) -> None:
    """Semi-transparent panel with thin border + highlight — sub-menus (V5)."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((14, 10, 28, alpha))
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, border, (x, y, w, h), 2)
    pygame.draw.line(screen, (*border, 80), (x+2, y+2), (x+w-2, y+2))

def _torch(screen, cx, cy, intensity) -> None:
    for r, a in [(90, 12), (55, 22), (32, 38), (16, 55)]:
        a2 = int(a * intensity)
        g = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 175, 55, a2), (r, r), r)
        screen.blit(g, (cx-r, cy-r))
    pygame.draw.circle(screen, (255, 220, 100), (cx, cy), 3)

def _btn(screen, x, y, w, h, text, font, sel, col=GOLD) -> None:
    if sel:
        bg = pygame.Surface((w, h), pygame.SRCALPHA); bg.fill((*col, 38))
        screen.blit(bg, (x, y)); _px_border(screen, x, y, w, h, col, 2)
        ax = x - 18; ay = y + h // 2
        pygame.draw.polygon(screen, col, [(ax, ay), (ax-8, ay-5), (ax-8, ay+5)])
        tc = LGOLD
    else:
        pygame.draw.rect(screen, DIM, (x, y, w, h), 1); tc = WHITE
    t = font.render(text, True, tc)
    screen.blit(t, (x + w//2 - t.get_width()//2, y + h//2 - t.get_height()//2))

def _stat_bar(screen, x, y, w, label, val, mx, color, font) -> None:
    screen.blit(font.render(label, True, C_DIM), (x, y))
    bx = x + 75; bw = w - 79; bh = 13
    pygame.draw.rect(screen, (30, 28, 45), (bx, y+2, bw, bh))
    pygame.draw.rect(screen, color, (bx, y+2, max(1, int(bw * val / mx)), bh))
    pygame.draw.rect(screen, (80, 80, 110), (bx, y+2, bw, bh), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU  (V7 — stone bg, antorchas, personajes animados)
# ═══════════════════════════════════════════════════════════════════════════════
def run_main_menu(screen: pygame.Surface) -> str:
    clock = pygame.time.Clock()
    f_title = _pxfont(44)
    f_opt   = _pxfont(22)
    f_hint  = _sf(15)
    f_clabel = _sf(13)

    OPTS = ["Iniciar Juego", "Ver Personajes", "Controles", "Opciones", "Salir"]
    sel  = 0; tick = 0; torch_ph = 0.0

    char_ids = ["char1", "char2", "char3"]
    cframes = {c: get_char_frames(c, "idle") for c in char_ids}
    cidx    = {c: 0 for c in char_ids}
    ctimer  = {c: 0 for c in char_ids}

    TITLE_Y = 18; TITLE_H = 90
    BTN_W = 300; BTN_H = 40; BTN_GAP = 10
    MENU_H = len(OPTS) * (BTN_H + BTN_GAP) - BTN_GAP + 28
    MENU_Y = TITLE_Y + TITLE_H + 30
    MENU_X = WIDTH // 2 - BTN_W // 2

    music.switch("menu")

    while True:
        dt = clock.tick(60); tick += dt; torch_ph += dt * 0.005
        music.update(dt)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(OPTS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(OPTS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    play("select.wav", 0.55)
                    r = _handle(screen, OPTS[sel])
                    if r: return r
                elif ev.key == pygame.K_ESCAPE:
                    if sel != len(OPTS) - 1: sel = len(OPTS) - 1
                    else: return "quit"
            if ev.type == pygame.MOUSEMOTION:
                for i, r in enumerate(_main_btns(MENU_X, MENU_Y, BTN_W, BTN_H, BTN_GAP, len(OPTS))):
                    if r.collidepoint(ev.pos) and i != sel:
                        sel = i; play("select.wav", 0.2)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i, r in enumerate(_main_btns(MENU_X, MENU_Y, BTN_W, BTN_H, BTN_GAP, len(OPTS))):
                    if r.collidepoint(ev.pos):
                        play("select.wav", 0.55)
                        r2 = _handle(screen, OPTS[i])
                        if r2: return r2

        for c in char_ids:
            ctimer[c] += dt
            if ctimer[c] > 180:
                ctimer[c] = 0
                if cframes[c]: cidx[c] = (cidx[c] + 1) % len(cframes[c])

        # ── Draw ──────────────────────────────────────────────────────────────
        _draw_stone_bg(screen)

        f1 = 0.75 + 0.25 * math.sin(torch_ph * 3.7)
        f2 = 0.75 + 0.25 * math.sin(torch_ph * 2.9 + 1.2)
        _torch(screen, 55, 50, f1); _torch(screen, WIDTH - 55, 50, f2)

        # Characters BEHIND the menu (drawn before menu panel)
        CSCALE = 4
        _draw_char_deco(screen, cframes["char1"], cidx["char1"],
                        CHAR_C["char1"], CSCALE,
                        100, 280, f_clabel, "Guerrera")
        _draw_char_deco(screen, cframes["char2"], cidx["char2"],
                        CHAR_C["char2"], CSCALE,
                        WIDTH - 450, 280, f_clabel, "Hechicera")
        _draw_char_deco(screen, cframes["char3"], cidx["char3"],
                        CHAR_C["char3"], CSCALE,
                        WIDTH - 300, 280, f_clabel, "Lagarto")

        # Title
        TW = 560
        _panel_main(screen, WIDTH//2 - TW//2, TITLE_Y, TW, TITLE_H,
                    fill=(8, 4, 16, 248), border=GOLD)
        t1  = f_title.render("SIMUBOMBER", True, GOLD)
        sep = f_title.render(":", True, STONE_H)
        t2  = f_title.render("CAOS", True, RED)
        totw = t1.get_width() + sep.get_width() + 8 + t2.get_width()
        tx = WIDTH // 2 - totw // 2
        ty = TITLE_Y + TITLE_H // 2 - t1.get_height() // 2
        screen.blit(t1,  (tx, ty))
        screen.blit(sep, (tx + t1.get_width() + 2, ty))
        screen.blit(t2,  (tx + t1.get_width() + sep.get_width() + 8, ty))

        # Menu options
        _panel_main(screen, MENU_X - 30, MENU_Y - 14, BTN_W + 60, MENU_H + 28,
                    fill=(6, 3, 14, 245), border=STONE_H)
        btns = _main_btns(MENU_X, MENU_Y, BTN_W, BTN_H, BTN_GAP, len(OPTS))
        for i, (opt, r) in enumerate(zip(OPTS, btns)):
            _btn(screen, r.x, r.y, r.w, r.h, opt, f_opt, (i == sel), GOLD)

        hint = f_hint.render("↑↓ navegar  ·  ENTER seleccionar", True, DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 22))
        pygame.display.flip()


def _draw_char_deco(screen, frames, idx, col, scale, x, y, font, label):
    if not frames: return
    surf = frames[idx % len(frames)]
    nw = surf.get_width() * scale; nh = surf.get_height() * scale
    scaled = pygame.transform.scale(surf, (nw, nh))
    g = pygame.Surface((nw + 20, 15), pygame.SRCALPHA)
    pygame.draw.ellipse(g, (*col, 30), (0, 0, nw + 20, 15))
    screen.blit(g, (x - 10, y + nh - 8))
    screen.blit(scaled, (x, y))
    ls = font.render(label, True, col)
    screen.blit(ls, (x + nw//2 - ls.get_width()//2, y + nh + 4))

def _main_btns(mx, my, bw, bh, gap, n):
    return [pygame.Rect(mx, my + i * (bh + gap), bw, bh) for i in range(n)]

def _handle(screen, opt):
    if opt == "Iniciar Juego":
        ch = run_character_select(screen)
        if ch: config._chosen_char = ch; return "play"
    elif opt == "Ver Personajes": run_characters_screen(screen)
    elif opt == "Controles":      run_controls_screen(screen)
    elif opt == "Opciones":       run_options_screen(screen)
    elif opt == "Salir":          return "quit"
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CHARACTER SELECT  (V5 style — dark gradient + particles)
# ═══════════════════════════════════════════════════════════════════════════════
def run_character_select(screen: pygame.Surface) -> str | None:
    clock = pygame.time.Clock()
    CHARS = ["char1", "char2", "char3"]
    NAMES = {"char1": "Guerrero Élfico", "char2": "Gran Hechicera", "char3": "Lagarto Veloz"}
    DESCS = {
        "char1": ["Veterano del bosque.", "Equilibrio perfecto."],
        "char2": ["Maga de Lumeria.", "Más vidas, menos velocidad."],
        "char3": ["Explorador veloz.", "Rapidez a cambio de vida."],
    }
    STORY_HINT = {
        "char1": "«Con ingenio y bombas, limpiará el bosque.»",
        "char2": "«Sus hechizos protegen, pero sus pies tardan.»",
        "char3": "«Nadie lo atrapa… si no le dan tiempo.»",
    }

    sel     = 0
    aframes = {c: get_char_frames(c, "idle") for c in CHARS}
    aidx    = {c: 0 for c in CHARS}
    atimer  = {c: 0 for c in CHARS}

    f_t  = pygame.font.SysFont("Arial", 40, bold=True)
    f_n  = pygame.font.SysFont("Arial", 26, bold=True)
    f_d  = pygame.font.SysFont("Arial", 17)
    f_q  = pygame.font.SysFont("Arial", 16, italic=True)
    f_st = pygame.font.SysFont("Arial", 15)
    f_h  = pygame.font.SysFont("Arial", 18)

    CW, CH, GAP = 240, 370, 32
    tick = 0

    def card_rects():
        total = len(CHARS) * CW + (len(CHARS) - 1) * GAP
        sx = WIDTH // 2 - total // 2
        sy = HEIGHT // 2 - CH // 2 + 10
        return [pygame.Rect(sx + i * (CW + GAP), sy, CW, CH) for i in range(len(CHARS))]

    while True:
        dt = clock.tick(60); tick += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return None
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    sel = (sel - 1) % len(CHARS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    sel = (sel + 1) % len(CHARS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    play("select.wav", 0.6); return CHARS[sel]
                elif ev.key == pygame.K_ESCAPE: return None
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i, r in enumerate(card_rects()):
                    if r.collidepoint(ev.pos):
                        if i == sel: play("select.wav", 0.6); return CHARS[i]
                        else: sel = i; play("select.wav", 0.3)
            if ev.type == pygame.MOUSEMOTION:
                for i, r in enumerate(card_rects()):
                    if r.collidepoint(ev.pos) and i != sel:
                        sel = i; play("select.wav", 0.2)

        for c in CHARS:
            atimer[c] += dt
            if atimer[c] > 170:
                atimer[c] = 0
                if aframes[c]: aidx[c] = (aidx[c] + 1) % len(aframes[c])

        _draw_bg(screen, tick)

        t = f_t.render("Elige tu Personaje", True, C_GOLD)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 22))

        rects = card_rects()
        for i, (cid, rect) in enumerate(zip(CHARS, rects)):
            is_sel = (i == sel); col = CHAR_PAL[cid]
            st = CHARACTER_STATS[cid]

            if is_sel:
                halo = pygame.Surface((CW+30, CH+30), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*col, 25), (0, 0, CW+30, CH+30), border_radius=12)
                screen.blit(halo, (rect.x - 15, rect.y - 15))

            card = pygame.Surface((CW, CH), pygame.SRCALPHA)
            if is_sel:
                card.fill((col[0]//4, col[1]//4, col[2]//4, 230))
            else:
                card.fill((18, 12, 32, 210))
            screen.blit(card, rect.topleft)
            pygame.draw.rect(screen, col if is_sel else (60, 55, 90), rect,
                             3 if is_sel else 1, border_radius=4)

            SPRITE_H = 140
            if aframes[cid]:
                fidx = aidx[cid] % len(aframes[cid])
                sf = aframes[cid][fidx]
                sw, sh = sf.get_size()
                sc = min((CW - 20) / sw, SPRITE_H / sh)
                nw, nh = int(sw * sc), int(sh * sc)
                ss = pygame.transform.scale(sf, (nw, nh))
                screen.blit(ss, (rect.x + CW//2 - nw//2, rect.y + 12 + (SPRITE_H - nh)//2))

            ns = f_n.render(NAMES[cid], True, col)
            screen.blit(ns, (rect.x + CW//2 - ns.get_width()//2, rect.y + SPRITE_H + 18))

            dy = rect.y + SPRITE_H + 50
            for line in DESCS[cid]:
                ls = f_d.render(line, True, C_WHITE)
                screen.blit(ls, (rect.x + CW//2 - ls.get_width()//2, dy)); dy += 22

            qs = f_q.render(STORY_HINT[cid], True, C_DIM)
            qw = qs.get_width()
            if qw > CW - 10:
                words = STORY_HINT[cid].split()
                line1 = " ".join(words[:len(words)//2])
                line2 = " ".join(words[len(words)//2:])
                for li, ln in enumerate([line1, line2]):
                    ls2 = f_q.render(ln, True, C_DIM)
                    screen.blit(ls2, (rect.x + CW//2 - ls2.get_width()//2, dy + li*18))
                dy += 36
            else:
                screen.blit(qs, (rect.x + CW//2 - qw//2, dy)); dy += 22

            sy2 = rect.y + CH - 90
            _stat_bar(screen, rect.x+12, sy2,    CW-24, "Vidas",     st["max_lives"], 6, (220, 60, 60),  f_st)
            _stat_bar(screen, rect.x+12, sy2+32, CW-24, "Velocidad", st["speed"],     8, (55, 180, 255), f_st)

            if is_sel:
                cue = f_h.render("[ ENTER ] Jugar", True, col)
                screen.blit(cue, (rect.x + CW//2 - cue.get_width()//2, rect.y + CH + 8))

        hint = pygame.font.SysFont("Arial", 17).render(
            "← → para cambiar  •  ENTER confirmar  •  ESC volver", True, C_DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 28))
        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
# VER PERSONAJES  (V5 style)
# ═══════════════════════════════════════════════════════════════════════════════
def run_characters_screen(screen: pygame.Surface):
    clock = pygame.time.Clock()
    CHARS = ["char1", "char2", "char3"]
    BIOS  = {
        "char1": ("Guerrero Élfico",
                  ["Veterano de las guerras del bosque.",
                   "Domina el equilibrio entre fuerza y agilidad.",
                   "Ideal para jugadores que buscan balance.",
                   "3 vidas  •  Velocidad media"]),
        "char2": ("Gran Hechicera",
                  ["Maga graduada de la academia de Lumeria.",
                   "Sus escudos mágicos le dan más resiliencia.",
                   "Perfecta para jugadores estratégicos.",
                   "5 vidas  •  Velocidad baja"]),
        "char3": ("Lagarto Veloz",
                  ["Explorador de las llanuras del sur.",
                   "Nadie lo supera en rapidez de reacción.",
                   "Para jugadores expertos que confían en su velocidad.",
                   "2 vidas  •  Velocidad alta"]),
    }
    aframes = {c: get_char_frames(c, "idle") for c in CHARS}
    aidx    = {c: 0 for c in CHARS}; atimer = {c: 0 for c in CHARS}
    f_t = pygame.font.SysFont("Arial", 38, bold=True)
    f_n = pygame.font.SysFont("Arial", 22, bold=True)
    f_d = pygame.font.SysFont("Arial", 17)
    f_h = pygame.font.SysFont("Arial", 18)
    tick = 0; running = True

    while running:
        dt = clock.tick(60); tick += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running = False
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                running = False
        for c in CHARS:
            atimer[c] += dt
            if atimer[c] > 190:
                atimer[c] = 0
                aidx[c] = (aidx[c] + 1) % max(1, len(aframes[c]))

        _draw_bg(screen, tick)
        t = f_t.render("Personajes del Juego", True, C_GOLD)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 22))

        CW, CH, GAP = 270, 420, 28
        total = len(CHARS) * CW + (len(CHARS) - 1) * GAP
        sx = WIDTH//2 - total//2; sy = 90

        for i, (cid, (name, lines)) in enumerate(zip(CHARS, BIOS.values())):
            rx = sx + i * (CW + GAP); col = CHAR_PAL[cid]
            _panel(screen, rx, sy, CW, CH, alpha=220, border=col)
            SPRITE_H = 150
            if aframes[cid]:
                f_idx = aidx[cid] % max(1, len(aframes[cid]))
                sf = aframes[cid][f_idx]
                sw, sh = sf.get_size()
                sc = min((CW - 20) / sw, SPRITE_H / sh)
                nw, nh = int(sw * sc), int(sh * sc)
                ss = pygame.transform.scale(sf, (nw, nh))
                screen.blit(ss, (rx + CW//2 - nw//2, sy + 10 + (SPRITE_H - nh)//2))
            ns = f_n.render(name, True, col)
            screen.blit(ns, (rx + CW//2 - ns.get_width()//2, sy + SPRITE_H + 16))
            for j, line in enumerate(lines):
                col2 = C_GOLD if j == 3 else C_WHITE
                ls = f_d.render(line, True, col2)
                screen.blit(ls, (rx + CW//2 - ls.get_width()//2, sy + SPRITE_H + 46 + j * 26))

        hint = f_h.render("ESC / ENTER — Volver", True, C_DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 28))
        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLES  (V5 style)
# ═══════════════════════════════════════════════════════════════════════════════
def run_controls_screen(screen: pygame.Surface):
    clock = pygame.time.Clock()
    CONTROLS = [
        ("Mover",             "↑ ↓ ← →  /  W A S D"),
        ("Colocar bomba",     "ESPACIO"),
        ("Pausar / Reanudar", "ESC  /  P"),
        ("Confirmar menú",    "ENTER"),
        ("Salir al menú",     "ESC (en pausa)"),
    ]
    STORY = [
        "El Algoritmo Ancestral define las reglas de Aeris.",
        "La fractura del Núcleo de Caos desató el caos.",
        "Los guardianes debieron mantener los nodos críticos.",
        "El Guardián de Sellos es la última esperanza.",
        "Recupera los fragmentos. Restaura el equilibrio.",
    ]
    f_t  = pygame.font.SysFont("Arial", 38, bold=True)
    f_l  = pygame.font.SysFont("Arial", 22)
    f_st = pygame.font.SysFont("Arial", 17, italic=True)
    f_sh = pygame.font.SysFont("Arial", 20, bold=True)
    f_h  = pygame.font.SysFont("Arial", 18)
    tick = 0; running = True

    while running:
        dt = clock.tick(60); tick += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running = False
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                running = False

        _draw_bg(screen, tick)
        t = f_t.render("Controles & Historia", True, C_GOLD)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 22))

        # Controls panel
        pw, ph = 520, len(CONTROLS) * 48 + 24
        px, py = WIDTH//2 - pw//2, 82
        _panel(screen, px, py, pw, ph)
        for i, (act, key) in enumerate(CONTROLS):
            y = py + 12 + i * 48
            pygame.draw.line(screen, (50, 45, 80), (px+12, y+40), (px+pw-12, y+40))
            screen.blit(f_l.render(act, True, C_WHITE), (px+20, y+10))
            ks = f_l.render(key, True, C_GOLD)
            screen.blit(ks, (px + pw - ks.get_width() - 20, y+10))

        # Story panel
        sy2 = py + ph + 22; pw2 = 540; ph2 = len(STORY) * 28 + 50; sx2 = WIDTH//2 - pw2//2
        _panel(screen, sx2, sy2, pw2, ph2, border=C_PINK)
        sh_s = f_sh.render("Historia: El Mundo de Aeris", True, C_PINK)
        screen.blit(sh_s, (sx2 + pw2//2 - sh_s.get_width()//2, sy2 + 10))
        for i, line in enumerate(STORY):
            ls = f_st.render(line, True, C_DIM if i < 4 else C_PINK)
            screen.blit(ls, (sx2 + pw2//2 - ls.get_width()//2, sy2 + 42 + i * 28))

        hint = f_h.render("ESC / ENTER — Volver", True, C_DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 28))
        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
# OPCIONES  (V5 style)
# ═══════════════════════════════════════════════════════════════════════════════
def run_options_screen(screen: pygame.Surface):
    clock = pygame.time.Clock()
    f_t = pygame.font.SysFont("Arial", 38, bold=True)
    f_l = pygame.font.SysFont("Arial", 26)
    f_d = pygame.font.SysFont("Arial", 16, italic=True)
    f_h = pygame.font.SysFont("Arial", 18)
    sel = 0; tick = 0; running = True

    OPTS  = ["Mostrar Hitboxes"]
    DESCS = ["Muestra las hitboxes de colisión de todos los personajes durante el juego."]

    def get_val(i): return [config.SHOW_HITBOXES][i]

    def toggle(i):
        if i == 0: config.SHOW_HITBOXES = not config.SHOW_HITBOXES

    def opt_rects():
        return [pygame.Rect(WIDTH//2 - 220, HEIGHT//2 - 30 + i * 60, 440, 48)
                for i in range(len(OPTS))]

    while running:
        dt = clock.tick(60); tick += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: running = False
                elif ev.key in (pygame.K_UP,   pygame.K_w): sel = (sel-1) % len(OPTS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_DOWN, pygame.K_s): sel = (sel+1) % len(OPTS); play("select.wav", 0.3)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER,
                                pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    toggle(sel); play("select.wav", 0.4)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i, r in enumerate(opt_rects()):
                    if r.collidepoint(ev.pos): toggle(i); play("select.wav", 0.4)

        _draw_bg(screen, tick)
        t = f_t.render("Opciones", True, C_GOLD)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 28))

        pw, ph = 500, len(OPTS) * 70 + 40
        px, py = WIDTH//2 - pw//2, HEIGHT//2 - ph//2 - 20
        _panel(screen, px, py, pw, ph)

        for i, (opt, desc, rect) in enumerate(zip(OPTS, DESCS, opt_rects())):
            is_sel = (i == sel)
            col = C_GOLD if is_sel else C_WHITE
            val = get_val(i)
            tog_txt = "[ ON  ]" if val else "[ OFF ]"
            tog_col = (80, 230, 120) if val else (200, 80, 80)

            if is_sel:
                bar = pygame.Surface((pw - 4, 50), pygame.SRCALPHA)
                bar.fill((C_GOLD[0]//6, C_GOLD[1]//6, C_GOLD[2]//6, 100))
                screen.blit(bar, (px + 2, rect.y - 1))

            screen.blit(f_l.render(("▶ " if is_sel else "  ") + opt, True, col), (rect.x+8, rect.y+8))
            ts = f_l.render(tog_txt, True, tog_col)
            screen.blit(ts, (rect.x + rect.w - ts.get_width() - 8, rect.y + 8))

        if 0 <= sel < len(DESCS):
            ds = f_d.render(DESCS[sel], True, C_DIM)
            screen.blit(ds, (WIDTH//2 - ds.get_width()//2, py + ph + 14))

        hint = f_h.render("ENTER / click — cambiar  •  ESC — volver", True, C_DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 28))
        pygame.display.flip()