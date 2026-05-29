"""
Main game loop — 3 levels, pause, transition, tile-snap movement,
exact bomb placement, returns to menu on game over / victory.
Integrates system dynamics and comprehensive metrics from feature-UI branch.
"""
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


def _find_free(gm, pref_c, pref_r):
    for dc in range(-4, 5):
        for dr in range(-4, 5):
            c, r = pref_c+dc, pref_r+dr
            if 0<=c<gm.cols and 0<=r<gm.rows and gm.tile_at(r,c)==0:
                return (gm.rect.left+c*TILE_SIZE, gm.rect.top+r*TILE_SIZE)
    return None
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


def _find_free(gm, pref_c, pref_r):
    for dc in range(-4, 5):
        for dr in range(-4, 5):
            c, r = pref_c+dc, pref_r+dr
            if 0<=c<gm.cols and 0<=r<gm.rows and gm.tile_at(r,c)==0:
                return (gm.rect.left+c*TILE_SIZE, gm.rect.top+r*TILE_SIZE)
    return None


class GameLoop:
    ST_PLAYING    = "playing"
    ST_PAUSED     = "paused"
    ST_TRANSITION = "transition"
    ST_GAME_OVER  = "game_over"
    ST_VICTORY    = "victory"
    TRANSITION_MS = 1800
    PAUSE_OPTS    = ["Continuar", "Reiniciar nivel", "Salir al menú"]

    # Per-level story
    STORY = {
        1: {"title": "El Bosque Maldito",
            "lines": ("Los demonios han invadido Lumeria.",
                      "El bosque encantado ha sido corrompido.",
                      "Elimina a los monstruos que lo habitan.")},
        2: {"title": "El Cementerio Oscuro",
            "lines": ("El bosque está limpio, pero el mal persiste.",
                      "Sombras rápidas acechan entre las lápidas.",
                      "No dejes que te atrapen en este lugar oscuro.")},
        3: {"title": "La Mazmorra del Dragón",
            "lines": ("El Dragón del Caos guarda el portal final.",
                      "Tiene dos vidas — transforma en llamas al primer golpe.",
                      "Derrótalo para sellar el portal para siempre.")},
    }

    def __init__(self, screen, char_id="char1"):
        self.screen = screen; self.clock = pygame.time.Clock()
        self.char_id = char_id; self.current_level = 1
        self._load_level(1)
        self.state = self.ST_PLAYING; self._state_timer = 0
        self._pause_sel = 0; self._trans_cap = None; self.result = None
        self._pf = pygame.font.SysFont("Arial",32,bold=True)
        self._sf = pygame.font.SysFont("Arial",22)
        self._hf = pygame.font.SysFont("Arial",16)
        # Track which bomb IDs have already hit which enemy IDs (prevents multi-hit)
        self._bomb_hit_log: dict[int, set[int]] = {}  # bomb_id -> set of enemy ids
        # System dynamics engine
        self.dynamics = SistemaDinamicoRuntime()

    def _load_level(self, level):
        self.game_map       = Map(level)
        mr                  = self.game_map.rect
        sx, sy              = _find_free(self.game_map,1,1) or (mr.left+TILE_SIZE,mr.top+TILE_SIZE)
        self.player         = Player(sx, sy, mr, self.char_id)
        self.bomb_system    = BombSystem(mr, self.game_map)
    ST_PLAYING    = "playing"
    ST_PAUSED     = "paused"
    ST_TRANSITION = "transition"
    ST_GAME_OVER  = "game_over"
    ST_VICTORY    = "victory"
    TRANSITION_MS = 1800
    PAUSE_OPTS    = ["Continuar", "Reiniciar nivel", "Salir al menú"]

    # Per-level story
    STORY = {
        1: {"title": "El Bosque Maldito",
            "lines": ("Los demonios han invadido Lumeria.",
                      "El bosque encantado ha sido corrompido.",
                      "Elimina a los monstruos que lo habitan.")},
        2: {"title": "El Cementerio Oscuro",
            "lines": ("El bosque está limpio, pero el mal persiste.",
                      "Sombras rápidas acechan entre las lápidas.",
                      "No dejes que te atrapen en este lugar oscuro.")},
        3: {"title": "La Mazmorra del Dragón",
            "lines": ("El Dragón del Caos guarda el portal final.",
                      "Tiene dos vidas — transforma en llamas al primer golpe.",
                      "Derrótalo para sellar el portal para siempre.")},
    }

    def __init__(self, screen, char_id="char1"):
        self.screen = screen; self.clock = pygame.time.Clock()
        self.char_id = char_id; self.current_level = 1
        self._load_level(1)
        self.state = self.ST_PLAYING; self._state_timer = 0
        self._pause_sel = 0; self._trans_cap = None; self.result = None
        self._pf = pygame.font.SysFont("Arial",32,bold=True)
        self._sf = pygame.font.SysFont("Arial",22)
        self._hf = pygame.font.SysFont("Arial",16)
        # Track which bomb IDs have already hit which enemy IDs (prevents multi-hit)
        self._bomb_hit_log: dict[int, set[int]] = {}  # bomb_id -> set of enemy ids
        # System dynamics engine
        self.dynamics = SistemaDinamicoRuntime()

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
                elif self.state==self.ST_GAME_OVER:
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_KP_ENTER): self.result="menu"
                elif self.state==self.ST_VICTORY:
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_ESCAPE,pygame.K_KP_ENTER): self.result="menu"

    def _play_key(self, key):
        if key in (pygame.K_ESCAPE,pygame.K_p):
            self.state=self.ST_PAUSED; self._pause_sel=0; play("select.wav",0.4)
        elif key==pygame.K_SPACE:
            self.bomb_system.try_place_bomb(pygame.time.get_ticks(), self.player.bomb_tile_pos())
        self.metrics        = MetricsSystem(mr)
        self.enemies        = self._spawn_enemies(level, mr)
        self.chaos          = 0.0
        self._bomb_hit_log  = {}

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
        if self.state != self.ST_PLAYING:
            self._state_timer += dt
            if self.state==self.ST_TRANSITION and self._state_timer>=self.TRANSITION_MS:
                self._advance_level()
            return

        # Player movement
        dx, dy = self.player.desired_delta()
        move_and_collide(self.player, dx, dy, self.game_map, self.bomb_system)
        self.player.update(dx, dy, dt)

        # Bombs
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
        if self.state != self.ST_PLAYING:
            self._state_timer += dt
            if self.state==self.ST_TRANSITION and self._state_timer>=self.TRANSITION_MS:
                self._advance_level()
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
        self.state=self.ST_TRANSITION; self._state_timer=0
        self._trans_cap=self.screen.copy(); play("level_clear.wav",0.75)

    def _advance_level(self):
        if self.current_level<TOTAL_LEVELS:
            self.current_level+=1; self._load_level(self.current_level)
            self.state=self.ST_PLAYING; self._state_timer=0
        else:
            self.state=self.ST_VICTORY; self._state_timer=0
        self.metrics.sample_frame(now,dt,self.enemies,nb,ne)
        self.metrics.sample_dynamics(now, self.dynamics.observe())
        self.metrics.sample_bomb_queue(now, self.bomb_system.observe_queue())

        if self.player.lives<=0:
            self.state=self.ST_GAME_OVER; self._state_timer=0; play("game_over.wav",0.7)
        elif not self.enemies:
            self._begin_transition()

    def _begin_transition(self):
        self.state=self.ST_TRANSITION; self._state_timer=0
        self._trans_cap=self.screen.copy(); play("level_clear.wav",0.75)

    def _advance_level(self):
        if self.current_level<TOTAL_LEVELS:
            self.current_level+=1; self._load_level(self.current_level)
            self.state=self.ST_PLAYING; self._state_timer=0
        else:
            self.state=self.ST_VICTORY; self._state_timer=0

    def render(self):
    def render(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.game_map.draw(self.screen)
        self.powerup_system.draw(self.screen)
        self.bomb_system.draw(self.screen)
        for en in self.enemies: en.draw(self.screen)
        self.player.draw(self.screen)
        draw_hud(self.screen, self.player, self.current_level, self.bomb_system)

        if   self.state==self.ST_PAUSED:     self._draw_pause()
        elif self.state==self.ST_TRANSITION: self._draw_transition()
        elif self.state==self.ST_GAME_OVER:  self._draw_game_over()
        elif self.state==self.ST_VICTORY:    self._draw_victory()
        self.bomb_system.draw(self.screen)
        for en in self.enemies: en.draw(self.screen)
        self.player.draw(self.screen)
        draw_hud(self.screen, self.player, self.current_level, self.bomb_system)

        if   self.state==self.ST_PAUSED:     self._draw_pause()
        elif self.state==self.ST_TRANSITION: self._draw_transition()
        elif self.state==self.ST_GAME_OVER:  self._draw_game_over()
        elif self.state==self.ST_VICTORY:    self._draw_victory()
        pygame.display.flip()

    def _draw_pause(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,155))
        self.screen.blit(ov,(0,0))
        pw,ph=400,310; px,py=WIDTH//2-pw//2,HEIGHT//2-ph//2
        panel=pygame.Surface((pw,ph),pygame.SRCALPHA); panel.fill((18,18,35,235))
        self.screen.blit(panel,(px,py)); pygame.draw.rect(self.screen,(90,110,200),(px,py,pw,ph),2)
        t=self._pf.render("PAUSA",True,(220,220,80))
        self.screen.blit(t,(WIDTH//2-t.get_width()//2,py+18))
        # Story hint
        story=self.STORY.get(self.current_level,{})
        if story:
            sl=self._hf.render(f"Nivel {self.current_level}: {story['title']}",True,(180,180,220))
            self.screen.blit(sl,(WIDTH//2-sl.get_width()//2,py+60))
        for i,opt in enumerate(self.PAUSE_OPTS):
            sel=(i==self._pause_sel); c=(255,220,60) if sel else (175,175,195)
            s=self._sf.render(("▶ " if sel else "  ")+opt,True,c)
            self.screen.blit(s,(WIDTH//2-s.get_width()//2,py+100+i*54))
        h=self._hf.render("↑↓ navegar • ENTER confirmar • ESC/P reanudar",True,(110,110,135))
        self.screen.blit(h,(WIDTH//2-h.get_width()//2,py+ph-26))

    def _draw_transition(self):
        if self._trans_cap: self.screen.blit(self._trans_cap,(0,0))
        prog=min(1.0,self._state_timer/self.TRANSITION_MS)
        tints={1:(50,160,50),2:(50,90,50),3:(50,30,110)}
        tint=tints.get(self.current_level,(70,70,70))
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((*tint,int(prog*215)))
        self.screen.blit(ov,(0,0))
        if prog>0.2:
            alpha=int((prog-0.2)/0.8*255)
            story=self.STORY.get(self.current_level,{})
            f48=pygame.font.SysFont("Arial",48,bold=True)
            s=f48.render(f"¡Nivel {self.current_level} Completado!",True,(255,255,110)); s.set_alpha(alpha)
            self.screen.blit(s,(WIDTH//2-s.get_width()//2,HEIGHT//2-80))
            if self.current_level<TOTAL_LEVELS:
                next_s=self.STORY.get(self.current_level+1,{})
                if next_s:
                    f22=pygame.font.SysFont("Arial",24,bold=True)
                    ns=f22.render(f"Siguiente: {next_s['title']}",True,(220,220,80)); ns.set_alpha(alpha)
                    self.screen.blit(ns,(WIDTH//2-ns.get_width()//2,HEIGHT//2))
                    f18=pygame.font.SysFont("Arial",18,italic=True)
                    for i,line in enumerate(next_s.get('lines',())[:1]):
                        nl=f18.render(line,True,(200,200,200)); nl.set_alpha(alpha)
                        self.screen.blit(nl,(WIDTH//2-nl.get_width()//2,HEIGHT//2+36))

    def _draw_game_over(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,170))
        self.screen.blit(ov,(0,0)); draw_message(self.screen,"GAME OVER",(255,60,60))
        hint=self._sf.render("ENTER / ESPACIO — Volver al menú",True,(200,200,200))
        self.screen.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT//2+65))
        f18=pygame.font.SysFont("Arial",18,italic=True)
        sl=f18.render("El héroe ha caído… pero la esperanza no muere.",True,(180,140,140))
        self.screen.blit(sl,(WIDTH//2-sl.get_width()//2,HEIGHT//2+100))

    def _draw_victory(self):
        # Transition: black overlay fades in over time
        progress = min(1.0, self._state_timer / 1500)  # 1.5s fade
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, int(255 * progress)))
        self.screen.blit(ov, (0, 0))

        if progress < 0.3:
            return  # wait for background to darken

        # Text alpha fades in after background
        text_alpha = min(255, int(255 * (progress - 0.3) / 0.4))

        fb = pygame.font.SysFont("Arial", 36, bold=True)
        fm = pygame.font.SysFont("Arial", 23)
        fs = pygame.font.SysFont("Arial", 17, italic=True)

        lines = [
            (fb, "¡El Dragón del Caos ha sido derrotado!", (100, 255, 120)),
            (fm, "Pero la oscuridad no cesa…", (200, 200, 200)),
            (fm, "Todo lo que hizo nuestro héroe fue en vano.", (200, 200, 200)),
            (fm, "El mundo aún está repleto de demonios,", (200, 200, 200)),
            (fm, "pero aún hay una última esperanza…", (200, 200, 200)),
        ]

        y = 50  # start from top
        for font, text, color in lines:
            s = font.render(text, True, color)
            s.set_alpha(text_alpha)
            self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, y))
            y += font.get_height() + 10

        # Image fades in after text
        img_alpha = min(255, int(255 * (progress - 0.6) / 0.4))
        if img_alpha > 0:
            try:
                from assets_loader import get_sprite
                sarita = get_sprite("sarita.png")
                if sarita:
                    sw, sh = sarita.get_size()
                    max_w = WIDTH - 120
                    max_h = HEIGHT - y - 70
                    scale = min(max_w / sw, max_h / sh, 1.0)
                    nw, nh = int(sw * scale), int(sh * scale)
                    scaled = pygame.transform.smoothscale(sarita, (nw, nh))
                    scaled.set_alpha(img_alpha)
                    self.screen.blit(scaled, (WIDTH // 2 - nw // 2, y + 10))
            except Exception:
                pass

        # Hint at bottom
        hint = fs.render("ENTER / ESC — Volver al menú", True, (150, 150, 150))
        hint.set_alpha(text_alpha)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 38))

    def run(self):
        while self.result is None:
            dt=self.clock.tick(FPS)
            self.handle_events()
            if self.result: break
            self.update(dt); self.render()
        return self.result or "menu"
            if self.result: break
            self.update(dt); self.render()
        return self.result or "menu"
