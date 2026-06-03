"""
Story presentation — animated typewriter text, floating particles,
crystal visualization. Displayed between levels in SimuBomber: Caos.
"""
from __future__ import annotations
import math, random
import pygame
from config import WIDTH, HEIGHT


# ═══════════════════════════════════════════════════════════════════════════════
# STORY CONTENT — Aeris & Algoritmo Ancestral
# ═══════════════════════════════════════════════════════════════════════════════

STORY_INTRO = [
    {
        "title": "AERIS",
        "lines": [
            "Un plano cuya existencia depende de",
            "un sistema de reglas probabilísticas:",
            "el Algoritmo Ancestral.",
        ],
        "theme": (40, 25, 70),
    },
    {
        "title": "EL NÚCLEO DE CAOS",
        "lines": [
            "En el centro geométrico de Aeris,",
            "el Núcleo de Caos mantenía el equilibrio.",
            "Cada pulso redistribuía las probabilidades.",
        ],
        "theme": (25, 35, 60),
    },
    {
        "title": "LA FRACTURA",
        "lines": [
            "Guardianes intentaron reprogramar el Algoritmo.",
            "El Núcleo se fracturó en tres fragmentos.",
            "Los caminos se deformaron. El caos creció.",
        ],
        "theme": (60, 20, 25),
    },
    {
        "title": "TU MISIÓN",
        "lines": [
            "Eres el último Guardián de Sellos.",
            "Recupera los tres fragmentos.",
            "Restaura el equilibrio de Aeris.",
        ],
        "theme": (30, 55, 40),
    },
]

STORY_TRANSITIONS = {
    1: [
        {
            "title": "PRIMER FRAGMENTO",
            "lines": [
                "El fragmento del Bosque ha sido recuperado.",
                "La naturaleza comienza a respirar.",
                "Los zombies deambulan sin patrón.",
            ],
            "theme": (45, 75, 35),
        },
        {
            "title": "EL CEMENTERIO OSCURO",
            "lines": [
                "El segundo fragmento yace en el Cementerio.",
                "Los imps detectan tu presencia.",
                "Sombras rápidas acechan entre las lápidas.",
            ],
            "theme": (35, 30, 45),
        },
    ],
    2: [
        {
            "title": "SEGUNDO FRAGMENTO",
            "lines": [
                "Las sombras del Cementerio se disipan.",
                "El último fragmento tiene",
                "un guardián más peligroso.",
            ],
            "theme": (45, 30, 55),
        },
        {
            "title": "EL DRAGÓN DEL CAOS",
            "lines": [
                "No es una criatura corrompida.",
                "Es la defensa autónoma del propio caos.",
                "Su existencia depende del Núcleo abierto.",
            ],
            "theme": (65, 20, 20),
        },
    ],
}

STORY_ENDING = [
    {
        "title": "LOS TRES FRAGMENTOS",
        "lines": [
            "Los fragmentos están reunidos.",
            "El Núcleo de Caos comienza",
            "a reensamblarse.",
        ],
        "theme": (35, 45, 55),
    },
    {
        "title": "EQUILIBRIO RESTAURADO",
        "lines": [
            "El Algoritmo Ancestral vibrate a regular",
            "las probabilidades de Aeris.",
            "Los caminos se restauran.",
        ],
        "theme": (25, 55, 40),
    },
    {
        "title": "EL ÚLTIMO GUARDIÁN",
        "lines": [
            "Tu misión ha terminado.",
            "Aeris sobrevive.",
        ],
        "theme": (45, 35, 55),
    },
]

CHARACTER_INTRO = {
    "char1": "El Guerrero Élfico empuña sus bombas con determinación.",
    "char2": "La Gran Hechicera lee los patrones del Algoritmo.",
    "char3": "El Lagarto Veloz se mueve entre las sombras.",
}

CHARACTER_ENDING = {
    "char1": "El Guerrero Élfico restauró el equilibrio con honor.",
    "char2": "La Hechicera comprendió el Algoritmo y lo sanó.",
    "char3": "El Lagarto Veloz superó cada obstáculo con agilidad.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FLOATING PARTICLES
# ═══════════════════════════════════════════════════════════════════════════════

class _Particle:
    def __init__(self, theme):
        self._reset(theme, init=True)

    def _reset(self, theme, init=False):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT) if init else HEIGHT + random.uniform(0, 30)
        self.vy = random.uniform(-0.3, -0.9)
        self.vx = random.uniform(-0.2, 0.2)
        self.r = random.uniform(1.5, 3.0)
        f = random.uniform(0.5, 1.3)
        self.col = tuple(min(255, int(c * f)) for c in theme)
        self.life = random.uniform(0.3, 1.0)
        self.age = 0.0
        self.dur = random.uniform(5.0, 10.0)

    def update(self, dt, theme):
        self.x += self.vx * dt * 40
        self.y += self.vy * dt * 40
        self.age += dt / self.dur
        if self.age >= 1.0 or self.y < -10:
            self._reset(theme)

    def draw(self, screen):
        a = math.sin(min(self.age, 1.0) * math.pi)
        alpha = int(160 * a * self.life)
        if alpha < 6:
            return
        d = int(self.r * 2 + 4)
        s = pygame.Surface((d * 2, d * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, alpha), (d, d), int(self.r) + 1)
        screen.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ═══════════════════════════════════════════════════════════════════════════════
# CRYSTAL VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_crystal(screen, cx, cy, size, phase, color):
    pulse = 1.0 + 0.12 * math.sin(phase * 2.5)
    s = int(size * pulse)

    # Outer glow
    gr = int(s * 2.0)
    glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
    ga = int(30 + 15 * math.sin(phase * 1.8))
    pygame.draw.circle(glow, (*color, ga), (gr, gr), gr)
    screen.blit(glow, (cx - gr, cy - gr))

    # Diamond shape
    pts = [(cx, cy - s), (cx + int(s * 0.6), cy),
           (cx, cy + int(s * 0.8)), (cx - int(s * 0.6), cy)]
    hl = tuple(min(255, c + 80) for c in color)
    pygame.draw.polygon(screen, (*color, 160), pts)
    pygame.draw.polygon(screen, (*hl, 200), pts, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# STORY PRESENTER
# ═══════════════════════════════════════════════════════════════════════════════

class StoryPresenter:
    TYPE_SPEED = 28

    def __init__(self, screen, pages, char_id="char1", story_type="transition"):
        self.screen = screen
        self.pages = pages
        self.char_id = char_id
        self.story_type = story_type
        self.page_idx = 0
        self.done = False

        self._type_timer = 0.0
        self._line_idx = 0
        self._char_idx = 0
        self._all_typed = False

        self._fade = 0
        self._tick = 0.0

        self._particles = [_Particle(self._theme()) for _ in range(45)]
        self._crystal_phase = 0.0

        self._ft = pygame.font.SysFont("Arial", 40, bold=True)
        self._fl = pygame.font.SysFont("Arial", 22)
        self._fh = pygame.font.SysFont("Arial", 17, italic=True)
        self._fp = pygame.font.SysFont("Arial", 15)
        self._fc = pygame.font.SysFont("Arial", 18, italic=True)

    def _theme(self):
        if self.page_idx < len(self.pages):
            return self.pages[self.page_idx].get("theme", (40, 40, 60))
        return (40, 40, 60)

    def handle_event(self, event):
        if self.done or event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if not self._all_typed:
                self._line_idx = len(self.pages[self.page_idx]["lines"])
                self._char_idx = 0
                self._all_typed = True
            else:
                self._next_page()
        elif event.key == pygame.K_ESCAPE:
            self.done = True

    def _next_page(self):
        self.page_idx += 1
        if self.page_idx >= len(self.pages):
            self.done = True
            return
        self._line_idx = 0
        self._char_idx = 0
        self._all_typed = False
        self._type_timer = 0.0
        self._fade = 0
        self._particles = [_Particle(self._theme()) for _ in range(45)]

    def update(self, dt):
        if self.done:
            return
        self._tick += dt
        self._crystal_phase += dt * 0.003

        for p in self._particles:
            p.update(dt, self._theme())

        self._fade = min(255, self._fade + int(dt * 1.8))

        if not self._all_typed:
            self._type_timer += dt
            while self._type_timer >= self.TYPE_SPEED and not self._all_typed:
                self._type_timer -= self.TYPE_SPEED
                lines = self.pages[self.page_idx]["lines"]
                if self._line_idx < len(lines):
                    if self._char_idx < len(lines[self._line_idx]):
                        self._char_idx += 1
                    else:
                        self._line_idx += 1
                        self._char_idx = 0
                        self._type_timer -= 250
                else:
                    self._all_typed = True

    def draw(self):
        if self.done:
            return

        page = self.pages[self.page_idx]
        theme = page.get("theme", (40, 40, 60))
        alpha = self._fade

        self._draw_bg(theme)

        for p in self._particles:
            p.draw(self.screen)

        _draw_crystal(self.screen, WIDTH // 2, 95, 28, self._crystal_phase, theme)

        # Title
        ts = self._ft.render(page["title"], True, (255, 230, 100))
        ts.set_alpha(alpha)
        self.screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, 140))

        # Underline
        uw = ts.get_width() + 40
        us = pygame.Surface((uw, 2), pygame.SRCALPHA)
        us.fill((255, 230, 100, int(alpha * 0.4)))
        self.screen.blit(us, (WIDTH // 2 - uw // 2, 190))

        # Typewriter lines
        lines = page["lines"]
        y0 = 215
        for i, txt in enumerate(lines):
            if i < self._line_idx:
                vis = txt
            elif i == self._line_idx and not self._all_typed:
                vis = txt[:self._char_idx]
            else:
                break
            if vis:
                col = (220, 220, 235) if i > 0 else (255, 240, 180)
                ls = self._fl.render(vis, True, col)
                ls.set_alpha(alpha)
                self.screen.blit(ls, (WIDTH // 2 - ls.get_width() // 2, y0 + i * 36))

        # Character-specific line (last page only)
        if self._all_typed and self.page_idx == len(self.pages) - 1:
            char_line = ""
            if self.story_type == "intro":
                char_line = CHARACTER_INTRO.get(self.char_id, "")
            elif self.story_type == "ending":
                char_line = CHARACTER_ENDING.get(self.char_id, "")
            if char_line:
                cs = self._fc.render(char_line, True, (180, 160, 220))
                cs.set_alpha(int(alpha * 0.8))
                self.screen.blit(cs, (WIDTH // 2 - cs.get_width() // 2,
                                      y0 + len(lines) * 36 + 20))

        # Continue hint
        if self._all_typed:
            ha = int(160 + 60 * math.sin(self._tick * 0.004))
            h = self._fh.render("ENTER continuar  •  ESC saltar", True, (160, 160, 180))
            h.set_alpha(ha)
            self.screen.blit(h, (WIDTH // 2 - h.get_width() // 2, HEIGHT - 45))

        # Page indicator
        pn = f"{self.page_idx + 1}/{len(self.pages)}"
        ps = self._fp.render(pn, True, (100, 100, 120))
        ps.set_alpha(alpha)
        self.screen.blit(ps, (WIDTH - 50, HEIGHT - 28))

    def _draw_bg(self, theme):
        for y in range(0, HEIGHT, 3):
            t = y / HEIGHT
            r = max(0, min(255, int(5 + theme[0] * 0.12 * t)))
            g = max(0, min(255, int(3 + theme[1] * 0.12 * t)))
            b = max(0, min(255, int(10 + theme[2] * 0.12 * t)))
            c = (r, g, b)
            pygame.draw.line(self.screen, c, (0, y), (WIDTH, y))
            pygame.draw.line(self.screen, c, (0, y + 1), (WIDTH, y + 1))
            pygame.draw.line(self.screen, c, (0, y + 2), (WIDTH, y + 2))
