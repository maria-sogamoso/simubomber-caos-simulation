"""
Main game loop — 3 levels, pause, transition, tile-snap movement,
exact bomb placement, returns to menu on game over / victory.
Integrates system dynamics and comprehensive metrics from feature-UI branch.
"""
from __future__ import annotations
import pygame
import config
from config import (BACKGROUND_COLOR, FPS, HEIGHT, WIDTH, TILE_SIZE, TOTAL_LEVELS,
                    ENEMY1_SPEED, ENEMY1_MOVE_INTERVAL,
                    ENEMY2_SPEED, ENEMY2_MOVE_INTERVAL,
                    ENEMY3_SPEED, ENEMY3_MOVE_INTERVAL)
from game.map      import Map
from game.player   import Player
from game.enemy    import Enemy, ImpEnemy, FireEnemy
from game.bomb     import BombSystem
from game.powerup  import PowerUpSystem
from game.metrics  import MetricsSystem
from game.dynamics import SistemaDinamicoRuntime
from game.hud      import draw_hud, draw_message
from game.sounds   import play
from game.movement import move_and_collide, hitbox_of
from game.story    import StoryPresenter, STORY_INTRO, STORY_TRANSITIONS, STORY_ENDING
from game import music


def _find_free(gm, pref_c, pref_r):
    for dc in range(-4, 5):
        for dr in range(-4, 5):
            c, r = pref_c+dc, pref_r+dr
            if 0<=c<gm.cols and 0<=r<gm.rows and gm.tile_at(r,c)==0:
                return (gm.rect.left+c*TILE_SIZE, gm.rect.top+r*TILE_SIZE)
    return None


class GameLoop:
    ST_INTRO      = "intro"
    ST_PLAYING    = "playing"
    ST_PAUSED     = "paused"
    ST_STORY      = "story"
    ST_GAME_OVER  = "game_over"
    ST_VICTORY    = "victory"
    PAUSE_OPTS    = ["Continuar", "Reiniciar nivel", "Salir al menú"]

    def __init__(self, screen, char_id="char1"):
        self.screen = screen; self.clock = pygame.time.Clock()
        self.char_id = char_id; self.current_level = 1
        self.state = self.ST_INTRO; self._state_timer = 0
        self._pause_sel = 0; self.result = None
        self._pf = pygame.font.SysFont("Arial",32,bold=True)
        self._sf = pygame.font.SysFont("Arial",22)
        self._hf = pygame.font.SysFont("Arial",16)
        self._bomb_hit_log: dict[int, set[int]] = {}
        self.dynamics = SistemaDinamicoRuntime()
        self.story = StoryPresenter(screen, STORY_INTRO, char_id, "intro")
        self._mission_fade = 255

    def _load_level(self, level):
        self.game_map       = Map(level)
        mr                  = self.game_map.rect
        sx, sy              = _find_free(self.game_map,1,1) or (mr.left+TILE_SIZE,mr.top+TILE_SIZE)
        self.player         = Player(sx, sy, mr, self.char_id)
        self.bomb_system    = BombSystem(mr, self.game_map)
        self.powerup_system = PowerUpSystem()
        self.metrics        = MetricsSystem(mr)
        self.enemies        = self._spawn_enemies(level, mr)
        self.chaos          = 0.0
        self._bomb_hit_log  = {}
        self._mission_fade = 255
        music.switch(f"level{level}")

    def _spawn_enemies(self, level, mr):
        gm=self.game_map; c,r=gm.cols,gm.rows; out=[]
        for pc,pr in [(c-2,r-2),(c//2,r-2),(c-2,r//2)]:
            if level>=1:
                p=_find_free(gm,pc,pr)
                if p: out.append(Enemy(*p,mr,"enemy1",ENEMY1_SPEED,ENEMY1_MOVE_INTERVAL))
        for pc,pr in [(1,r-2),(c-2,1)]:
            if level>=2:
                p=_find_free(gm,pc,pr)
                if p: out.append(ImpEnemy(*p,mr))
        for pc,pr in [(c-2,1),(1,r-2)]:
            if level>=3:
                p=_find_free(gm,pc,pr)
                if p: out.append(FireEnemy(*p,mr))
        return out

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: self.result="quit"; return
            if ev.type==pygame.KEYDOWN:
                if   self.state==self.ST_PLAYING:   self._play_key(ev.key)
                elif self.state==self.ST_PAUSED:     self._pause_key(ev.key)
                elif self.state==self.ST_INTRO:
                    self.story.handle_event(ev)
                    if self.story.done:
                        self._load_level(1)
                        self.state=self.ST_PLAYING
                elif self.state==self.ST_STORY:
                    self.story.handle_event(ev)
                    if self.story.done:
                        self._advance_level()
                elif self.state==self.ST_GAME_OVER:
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_KP_ENTER): self.result="menu"
                elif self.state==self.ST_VICTORY:
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_ESCAPE,pygame.K_KP_ENTER): self.result="menu"

    def _play_key(self, key):
        if key in (pygame.K_ESCAPE,pygame.K_p):
            self.state=self.ST_PAUSED; self._pause_sel=0; play("select.wav",0.4)
        elif key==pygame.K_SPACE:
            self.bomb_system.try_place_bomb(pygame.time.get_ticks(), self.player.bomb_tile_pos())

    def _pause_key(self, key):
        n=len(self.PAUSE_OPTS)
        if   key in (pygame.K_UP,  pygame.K_w): self._pause_sel=(self._pause_sel-1)%n; play("select.wav",0.3)
        elif key in (pygame.K_DOWN,pygame.K_s): self._pause_sel=(self._pause_sel+1)%n; play("select.wav",0.3)
        elif key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_KP_ENTER): self._exec_pause()
        elif key in (pygame.K_ESCAPE,pygame.K_p): self.state=self.ST_PLAYING

    def _exec_pause(self):
        play("select.wav",0.5); s=self._pause_sel
        if   s==0: self.state=self.ST_PLAYING
        elif s==1: self._load_level(self.current_level); self.state=self.ST_PLAYING
        elif s==2: self.result="menu"

    def update(self, dt):
        music.update(dt)
        if self._mission_fade > 0:
            self._mission_fade = max(0, self._mission_fade - int(dt * 2.5))
        if self.state == self.ST_INTRO:
            self.story.update(dt)
            if self.story.done:
                self._load_level(1)
                self.state = self.ST_PLAYING
            return
        if self.state == self.ST_STORY:
            self.story.update(dt)
            if self.story.done:
                self._advance_level()
            return
        if self.state != self.ST_PLAYING:
            self._state_timer += dt
            return

        # Player movement
        dx, dy = self.player.desired_delta()
        move_and_collide(self.player, dx, dy, self.game_map, self.bomb_system)
        self.player.update(dx, dy, dt)

        # Bombs
        self.bomb_system.update(dt)
        if self.bomb_system.get_player_explosion_damage(hitbox_of(self.player.rect)) > 0:
            self.player.take_damage(0.5, pygame.time.get_ticks())

        # Clean up hit log for removed bombs
        active_bomb_ids = {id(b) for b in self.bomb_system.bombs}
        self._bomb_hit_log = {k:v for k,v in self._bomb_hit_log.items() if k in active_bomb_ids}

        # Power-ups
        self.powerup_system.update(self.player, dt)

        # Chaos calculation
        nb=sum(1 for b in self.bomb_system.bombs if b.is_active())
        ne=sum(1 for b in self.bomb_system.bombs if b.is_exploding)
        enemies_count = len(self.enemies)
        powerups_count = len(self.powerup_system.powerups)

        # Feed observed counts into the runtime dynamics and advance it
        self.dynamics.enemigos = float(enemies_count)
        self.dynamics.bombas = float(nb)
        self.dynamics.explosiones = float(ne)
        self.dynamics.powerups = float(powerups_count)
        self.dynamics.step(dt)
        self.chaos = min(10.0, self.dynamics.caos)

        # Enemy movement
        all_e_rects = [e.rect for e in self.enemies]
        for en in self.enemies:
            en.apply_chaos(self.chaos)
            dx_e, dy_e = en.desired_delta()
            move_and_collide(en, dx_e, dy_e, self.game_map, self.bomb_system)
            en.update(self.player, self.bomb_system, dt)

        # Bomb hits — ONE hit per enemy per bomb explosion
        surviving = []
        for en in self.enemies:
            hit_this_frame = False
            for bomb in self.bomb_system.bombs:
                if not bomb.is_exploding_now():
                    continue
                bomb_id   = id(bomb)
                enemy_id  = id(en)
                if bomb_id not in self._bomb_hit_log:
                    self._bomb_hit_log[bomb_id] = set()
                if enemy_id in self._bomb_hit_log[bomb_id]:
                    continue  # already registered this bomb hit for this enemy
                # Check if THIS bomb hits THIS enemy (ray-aware)
                if self.bomb_system.check_enemy_hit_single(bomb, en.rect, all_e_rects):
                    self._bomb_hit_log[bomb_id].add(enemy_id)
                    hit_this_frame = True
                    break  # one bomb hit is enough per frame

            if hit_this_frame:
                if isinstance(en, FireEnemy):
                    dead = en.hit()
                    if not dead:
                        surviving.append(en)
                    else:
                        self.powerup_system.spawn_from_enemy(en.rect.center)
                        play("enemy_die.wav", 0.6)
                else:
                    self.powerup_system.spawn_from_enemy(en.rect.center)
                    play("enemy_die.wav", 0.6)
            else:
                surviving.append(en)
        self.enemies = surviving

        # Enemy touch damage
        now=pygame.time.get_ticks()
        player_hb = hitbox_of(self.player.rect)
        for en in self.enemies:
            if hitbox_of(en.rect).colliderect(player_hb):
                self.player.take_damage(1.0,now); break

        # Sample metrics
        self.metrics.sample_frame(now,dt,self.enemies,nb,ne)
        self.metrics.sample_dynamics(now, self.dynamics.observe())
        self.metrics.sample_bomb_queue(now, self.bomb_system.observe_queue())

        if self.player.lives<=0:
            self.state=self.ST_GAME_OVER; self._state_timer=0; play("game_over.wav",0.7)
        elif not self.enemies:
            self._begin_transition()

    def _begin_transition(self):
        if self.current_level < TOTAL_LEVELS:
            pages = STORY_TRANSITIONS.get(self.current_level, [])
            story_type = "transition"
        else:
            pages = STORY_ENDING
            story_type = "ending"
            music.switch("ending")
        if not pages:
            pages = [{"title": f"Nivel {self.current_level} Completado",
                      "lines": ["Prepárate para el siguiente nivel."],
                      "theme": (40, 40, 60)}]
            story_type = "transition"
        self.state = self.ST_STORY
        self.story = StoryPresenter(self.screen, pages, self.char_id, story_type)
        play("level_clear.wav", 0.75)

    def _advance_level(self):
        if self.current_level<TOTAL_LEVELS:
            self.current_level+=1; self._load_level(self.current_level)
            self.state=self.ST_PLAYING; self._state_timer=0
        else:
            self.state=self.ST_VICTORY; self._state_timer=0

    def render(self):
        self.screen.fill(BACKGROUND_COLOR)

        if self.state == self.ST_INTRO:
            self.story.draw()
        elif self.state == self.ST_STORY:
            self.story.draw()
        else:
            self.game_map.draw(self.screen)
            self.powerup_system.draw(self.screen)
            self.bomb_system.draw(self.screen)
            for en in self.enemies: en.draw(self.screen)
            self.player.draw(self.screen)
            draw_hud(self.screen, self.player, self.current_level, self.bomb_system)

            if   self.state==self.ST_PAUSED:     self._draw_pause()
            elif self.state==self.ST_GAME_OVER:  self._draw_game_over()
            elif self.state==self.ST_VICTORY:    self._draw_victory()

        if self._mission_fade > 0:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, self._mission_fade))
            self.screen.blit(ov, (0, 0))

        pygame.display.flip()

    def _draw_pause(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,155))
        self.screen.blit(ov,(0,0))
        pw,ph=400,310; px,py=WIDTH//2-pw//2,HEIGHT//2-ph//2
        panel=pygame.Surface((pw,ph),pygame.SRCALPHA); panel.fill((18,18,35,235))
        self.screen.blit(panel,(px,py)); pygame.draw.rect(self.screen,(90,110,200),(px,py,pw,ph),2)
        t=self._pf.render("PAUSA",True,(220,220,80))
        self.screen.blit(t,(WIDTH//2-t.get_width()//2,py+18))
        # Level hint
        names={1:"El Bosque Maldito",2:"El Cementerio Oscuro",3:"La Mazmorra del Dragón"}
        lv=names.get(self.current_level,f"Nivel {self.current_level}")
        sl=self._hf.render(f"Nivel {self.current_level}: {lv}",True,(180,180,220))
        self.screen.blit(sl,(WIDTH//2-sl.get_width()//2,py+60))
        for i,opt in enumerate(self.PAUSE_OPTS):
            sel=(i==self._pause_sel); c=(255,220,60) if sel else (175,175,195)
            s=self._sf.render(("▶ " if sel else "  ")+opt,True,c)
            self.screen.blit(s,(WIDTH//2-s.get_width()//2,py+100+i*54))
        h=self._hf.render("↑↓ navegar • ENTER confirmar • ESC/P reanudar",True,(110,110,135))
        self.screen.blit(h,(WIDTH//2-h.get_width()//2,py+ph-26))

    def _draw_game_over(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,170))
        self.screen.blit(ov,(0,0)); draw_message(self.screen,"GAME OVER",(255,60,60))
        hint=self._sf.render("ENTER / ESPACIO — Volver al menú",True,(200,200,200))
        self.screen.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT//2+65))
        f18=pygame.font.SysFont("Arial",18,italic=True)
        sl=f18.render("El Guardián ha caído… pero el Algoritmo persiste.",True,(180,140,140))
        self.screen.blit(sl,(WIDTH//2-sl.get_width()//2,HEIGHT//2+100))

    def _draw_victory(self):
        import math
        progress = min(1.0, self._state_timer / 2000)
        alpha = int(255 * progress)

        # Themed background (emerald/green — equilibrium restored)
        theme = (25, 55, 40)
        for y_bg in range(0, HEIGHT, 3):
            t = y_bg / HEIGHT
            r = max(0, min(255, int(5 + theme[0] * 0.12 * t)))
            g = max(0, min(255, int(3 + theme[1] * 0.12 * t)))
            b = max(0, min(255, int(10 + theme[2] * 0.12 * t)))
            c = (r, g, b)
            pygame.draw.line(self.screen, c, (0, y_bg), (WIDTH, y_bg))
            pygame.draw.line(self.screen, c, (0, y_bg + 1), (WIDTH, y_bg + 1))
            pygame.draw.line(self.screen, c, (0, y_bg + 2), (WIDTH, y_bg + 2))

        if progress < 0.15:
            return

        text_alpha = min(255, int(255 * (progress - 0.15) / 0.4))

        ft = pygame.font.SysFont("Arial", 40, bold=True)
        fl = pygame.font.SysFont("Arial", 22)
        fh = pygame.font.SysFont("Arial", 17, italic=True)

        # Crystal
        from game.story import _draw_crystal, _Particle
        phase = self._state_timer * 0.003
        _draw_crystal(self.screen, WIDTH // 2, 95, 28, phase, theme)

        # Title
        ts = ft.render("EQUILIBRIO RESTAURADO", True, (255, 230, 100))
        ts.set_alpha(text_alpha)
        self.screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, 140))

        # Underline
        uw = ts.get_width() + 40
        us = pygame.Surface((uw, 2), pygame.SRCALPHA)
        us.fill((255, 230, 100, int(text_alpha * 0.4)))
        self.screen.blit(us, (WIDTH // 2 - uw // 2, 190))

        # Lines
        lines = [
            "El Algoritmo Ancestral vibrate a regular",
            "las probabilidades de Aeris.",
            "El último Guardián de Sellos cumplió su misión.",
            "Los caminos se restauran.",
        ]
        y0 = 220
        for i, txt in enumerate(lines):
            col = (220, 220, 235) if i > 0 else (255, 240, 180)
            ls = fl.render(txt, True, col)
            ls.set_alpha(text_alpha)
            self.screen.blit(ls, (WIDTH // 2 - ls.get_width() // 2, y0 + i * 36))

        # Hint
        ha = int(160 + 60 * math.sin(self._state_timer * 0.004))
        h = fh.render("ENTER / ESC — Volver al menú", True, (160, 160, 180))
        h.set_alpha(ha)
        self.screen.blit(h, (WIDTH // 2 - h.get_width() // 2, HEIGHT - 45))

    def run(self):
        while self.result is None:
            dt=self.clock.tick(FPS)
            self.handle_events()
            if self.result: break
            self.update(dt); self.render()
        return self.result or "menu"
