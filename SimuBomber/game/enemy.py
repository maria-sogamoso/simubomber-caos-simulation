"""
Enemy types for SimuBomber: Caos — uses movement.py for all collision.
  Enemy     — L1 Zombie: pure LCG random-walk, never chases, never flees.
  ImpEnemy  — L2 Imp:    fast, chases, flees explosions, erratic.
  FireEnemy — L3 Dragon: 2 lives, chases, transforms on first hit (Flam form).
"""
from __future__ import annotations
import math, time, sys, os
import pygame
from config import (TILE_SIZE,
                    ENEMY1_SPEED, ENEMY1_MOVE_INTERVAL,
                    ENEMY2_SPEED, ENEMY2_MOVE_INTERVAL,
                    ENEMY3_SPEED, ENEMY3_MOVE_INTERVAL)
from assets_loader import get_enemy_frames

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
try:
    from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
    _HAS_LCG = True
except ImportError:
    _HAS_LCG = False

DIRS = ((1,0),(-1,0),(0,1),(0,-1))

def _make_lcg(obj):
    seed = (int(time.time()*1_000_000) + id(obj)) % (2**32-1) or 1
    if _HAS_LCG: return GeneradorCongruenciaLineal(seed)
    import random as _r
    class _F:
        def siguiente_Ri_Congruencia_Lineal(self,pasos=1): return [_r.random() for _ in range(pasos)]
    return _F()

def _ri(lcg): return lcg.siguiente_Ri_Congruencia_Lineal(pasos=1)[0]


class Enemy:
    """Level-1 Zombie — PURE random-walk via LCG. Zero aggression."""
    KEEP_DIR = 0.60

    def __init__(self, x, y, bounds, enemy_id="enemy1",
                 speed=ENEMY1_SPEED, move_interval=ENEMY1_MOVE_INTERVAL):
        self.rect   = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.speed  = speed; self.bounds = bounds.copy()
        self.enemy_id = enemy_id; self.alive = True
        self.move_interval = move_interval
        self.base_move_interval = move_interval
        self.direction = (1, 0); self.frame_counter = 0
        self.lcg = _make_lcg(self)
        # Never chases/flees
        self.chase_threshold = 0; self.flee_threshold = 0
        self.base_chase_th   = 0; self.bias_strength   = 0.0
        self.state = "wander"
        self._idle = get_enemy_frames(enemy_id, "idle")
        self._run  = get_enemy_frames(enemy_id, "run")
        self._at=0; self._fi=0; self._asp=200; self._mov=False; self._flip=False
        self._fb = (220, 100, 80)

    # desired velocity for movement.py
    def desired_delta(self):
        return (self.direction[0]*self.speed, self.direction[1]*self.speed)

    def apply_chaos(self, chaos, difficulty=1.0):
        self.move_interval = max(6, int(self.base_move_interval - chaos*0.4))
        # Difficulty scales enemy speed (positive feedback loop)
        self.speed = max(1, int(ENEMY1_SPEED * (1.0 + 0.06 * (difficulty - 1.0))))

    def _choose_dir(self):
        valid = [d for d in DIRS]   # all dirs — wall collision is handled by movement.py
        keep = self.direction in valid and _ri(self.lcg) < self.KEEP_DIR
        if keep: return
        cands = [d for d in valid if d != self.direction] or valid
        self.direction = cands[int(_ri(self.lcg)*len(cands))]

    def update(self, player=None, bomb_system=None, dt=16):
        self.frame_counter += 1
        if self.frame_counter % self.move_interval == 1:
            self._choose_dir()
        dx, dy = self.desired_delta()
        self._mov = bool(dx or dy)
        if dx < 0: self._flip = True
        elif dx > 0: self._flip = False
        self._at += dt
        if self._at >= self._asp:
            self._at = 0
            frames = self._run if self._mov else self._idle
            if frames: self._fi = (self._fi+1) % len(frames)

    def draw(self, screen):
        import config
        frames = self._run if self._mov else self._idle
        if frames:
            surf = frames[self._fi % len(frames)]
            sw,sh = surf.get_size()
            sc = min(TILE_SIZE/sw, TILE_SIZE/sh)
            nw,nh = int(sw*sc), int(sh*sc)
            s = pygame.transform.scale(surf,(nw,nh))
            if self._flip: s = pygame.transform.flip(s,True,False)
            screen.blit(s,(self.rect.x+(TILE_SIZE-nw)//2,
                           self.rect.y+(TILE_SIZE-nh)//2 + config.VISUAL_Y))
        else:
            pygame.draw.rect(screen, self._fb, self.rect)
        if config.SHOW_HITBOXES:
            from game.movement import hitbox_of
            pygame.draw.rect(screen,(255,0,0),hitbox_of(self.rect),1)
            pygame.draw.rect(screen,(255,140,0),self.rect,1)


class ImpEnemy(Enemy):
    """Level-2 Imp — fast, chases player, flees explosions."""
    KEEP_DIR = 0.25

    def __init__(self, x, y, bounds):
        super().__init__(x, y, bounds, "enemy2", ENEMY2_SPEED, ENEMY2_MOVE_INTERVAL)
        self.chase_threshold = 280; self.base_chase_th = 280
        self.flee_threshold  = 90;  self.bias_strength  = 0.3
        self._asp = 110; self._fb = (160, 50, 220)

    def apply_chaos(self, chaos, difficulty=1.0):
        self.move_interval   = max(4, int(self.base_move_interval - chaos*0.7))
        self.chase_threshold = self.base_chase_th + chaos*12 + difficulty*8
        self.bias_strength   = min(0.92, chaos/10.0 + 0.3 + 0.02 * difficulty)
        # Difficulty scales imp speed and aggression
        self.speed = max(1, int(ENEMY2_SPEED * (1.0 + 0.08 * (difficulty - 1.0))))

    def _perceive(self, player, bomb_system):
        self.dist_p = self.dist_t = float("inf")
        self.pos_p  = self.pos_t  = None
        if player:
            px,py = player.rect.centerx, player.rect.centery
            self.pos_p = (px,py)
            self.dist_p = math.hypot(px-self.rect.centerx, py-self.rect.centery)
        if bomb_system:
            for b in bomb_system.bombs:
                if getattr(b,"is_exploding",False):
                    areas = b.get_explosion_rects_clamped(bomb_system.map_rect, bomb_system.game_map)
                    for a in areas:
                        d = math.hypot(a.centerx-self.rect.centerx, a.centery-self.rect.centery)
                        if d < self.dist_t: self.dist_t=d; self.pos_t=(a.centerx,a.centery)
                else:
                    d = math.hypot(b.rect.centerx-self.rect.centerx, b.rect.centery-self.rect.centery)
                    if d < self.dist_t: self.dist_t=d; self.pos_t=(b.rect.centerx,b.rect.centery)

    def _best_dir(self, target, flee):
        best,bs = DIRS[0],None
        for dd in DIRS:
            nx = self.rect.centerx+dd[0]*self.speed
            ny = self.rect.centery+dd[1]*self.speed
            sc = math.hypot(target[0]-nx,target[1]-ny)
            if bs is None or (flee and sc>bs) or (not flee and sc<bs):
                best,bs=dd,sc
        return best

    def update(self, player=None, bomb_system=None, dt=16):
        self.frame_counter += 1
        self._perceive(player, bomb_system)
        if self.pos_t and self.dist_t < self.flee_threshold:
            state = "flee"
        elif self.pos_p and self.dist_p < self.chase_threshold:
            state = "chase"
        else:
            state = "wander"

        if self.frame_counter % self.move_interval == 1:
            self._choose_dir()
            if state=="chase" and self.pos_p and _ri(self.lcg)<self.bias_strength:
                self.direction = self._best_dir(self.pos_p, flee=False)
            elif state=="flee" and self.pos_t and _ri(self.lcg)<self.bias_strength:
                self.direction = self._best_dir(self.pos_t, flee=True)

        dx,dy = self.desired_delta()
        self._mov = bool(dx or dy)
        if dx<0: self._flip=True
        elif dx>0: self._flip=False
        self._at += dt
        if self._at >= self._asp:
            self._at=0
            frames = self._run if self._mov else self._idle
            if frames: self._fi=(self._fi+1)%len(frames)


class FireEnemy(ImpEnemy):
    """Level-3 Dragon — 2 lives; transforms to Flam form after first hit."""
    def __init__(self, x, y, bounds):
        super().__init__(x, y, bounds)
        self.enemy_id        = "enemy3_normal"
        self.speed           = ENEMY3_SPEED
        self.base_move_interval = ENEMY3_MOVE_INTERVAL
        self.move_interval      = ENEMY3_MOVE_INTERVAL
        self.chase_threshold = 200; self.base_chase_th = 200
        self._asp = 160
        self.lives = 2; self.on_fire = False
        self._idle = get_enemy_frames("enemy3_normal","idle")
        self._run  = get_enemy_frames("enemy3_normal","run")
        self._fire_idle = get_enemy_frames("enemy3_fire","idle")
        self._fire_run  = get_enemy_frames("enemy3_fire","run")
        self._fb    = (220,80,40)
        self._glow  = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
        self._glow.fill((255,80,0,55))

    def hit(self):
        self.lives -= 1
        if self.lives <= 0: self.alive=False; return True
        self.on_fire = True; self.speed = ENEMY3_SPEED+2; self._fb=(255,160,30); return False

    def draw(self, screen):
        import config
        frames = (self._fire_run if self._mov else self._fire_idle) if self.on_fire \
                 else (self._run if self._mov else self._idle)
        if frames:
            surf = frames[self._fi%len(frames)]
            sw,sh = surf.get_size()
            sc = min(TILE_SIZE/sw, TILE_SIZE/sh)
            nw,nh = int(sw*sc),int(sh*sc)
            s = pygame.transform.scale(surf,(nw,nh))
            if self._flip: s=pygame.transform.flip(s,True,False)
            screen.blit(s,(self.rect.x+(TILE_SIZE-nw)//2,
                           self.rect.y+(TILE_SIZE-nh)//2 + config.VISUAL_Y))
            if self.on_fire: screen.blit(self._glow,self.rect.topleft)
        else:
            pygame.draw.rect(screen,self._fb,self.rect)
        if config.SHOW_HITBOXES:
            from game.movement import hitbox_of
            pygame.draw.rect(screen,(255,0,0),hitbox_of(self.rect),1)
            pygame.draw.rect(screen,(255,140,0),self.rect,1)
