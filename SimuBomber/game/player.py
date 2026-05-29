"""Player — exact-tile bomb placement, uses movement.py for collision."""
from __future__ import annotations
import pygame
from config import CHARACTER_STATS, DEFAULT_CHARACTER, TILE_SIZE, MAP_COLS, MAP_ROWS
from assets_loader import get_char_frames


class Player:
    def __init__(self, x, y, map_rect, char_id=DEFAULT_CHARACTER):
        st = CHARACTER_STATS.get(char_id, CHARACTER_STATS[DEFAULT_CHARACTER])
        self.char_id    = char_id
        self.max_lives  = float(st["max_lives"])
        self.lives      = self.max_lives
        self.base_speed = st["speed"]
        self.speed      = st["speed"]
        self.rect       = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.map_rect   = map_rect.copy()
        self.bounds     = map_rect            # alias used elsewhere

        self.invulnerable  = False
        self.inv_time      = 1400
        self.last_hit_time = 0
        self.speed_boost_active   = False
        self.speed_boost_end_time = 0

        self._idle = get_char_frames(char_id, "idle")
        self._run  = get_char_frames(char_id, "run")
        self._at   = 0; self._fi = 0; self._asp = 135
        self._mov  = False; self._flip = False
        self._step_t = 0

    # desired movement delta (consumed by game_loop via movement.py)
    def desired_delta(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += self.speed
        return dx, dy

    def bomb_tile_pos(self):
        col = max(0, min(MAP_COLS-1, (self.rect.centerx - self.map_rect.left) // TILE_SIZE))
        row = max(0, min(MAP_ROWS-1, (self.rect.centery - self.map_rect.top)  // TILE_SIZE))
        return (self.map_rect.left + col*TILE_SIZE,
                self.map_rect.top  + row*TILE_SIZE)

    def update(self, dx, dy, dt=16):
        now = pygame.time.get_ticks()
        if self.speed_boost_active and now >= self.speed_boost_end_time:
            self.speed = self.base_speed; self.speed_boost_active = False
        if self.invulnerable and now - self.last_hit_time >= self.inv_time:
            self.invulnerable = False
        self._mov = bool(dx or dy)
        if dx < 0: self._flip = True
        elif dx > 0: self._flip = False
        self._at += dt
        if self._at >= self._asp:
            self._at = 0
            frames = self._run if self._mov else self._idle
            if frames: self._fi = (self._fi+1) % len(frames)
        if self._mov:
            self._step_t += dt
            if self._step_t > 280:
                self._step_t = 0
                try:
                    from game.sounds import play; play("step.wav", 0.2)
                except Exception: pass

    def take_damage(self, dmg, now):
        if self.invulnerable: return
        self.lives = max(0.0, self.lives - float(dmg))
        self.invulnerable = True; self.last_hit_time = now
        try:
            from game.sounds import play; play("hit.wav", 0.6)
        except Exception: pass

    def draw(self, screen):
        import config
        if self.invulnerable and pygame.time.get_ticks() % 200 < 100: return
        frames = self._run if self._mov else self._idle
        if frames:
            surf = frames[self._fi % len(frames)]
            sw, sh = surf.get_size()
            sc = min(TILE_SIZE/sw, TILE_SIZE/sh)
            nw, nh = int(sw*sc), int(sh*sc)
            s = pygame.transform.scale(surf, (nw, nh))
            if self._flip: s = pygame.transform.flip(s, True, False)
            screen.blit(s, (self.rect.x+(TILE_SIZE-nw)//2,
                            self.rect.y+(TILE_SIZE-nh)//2 + config.VISUAL_Y))
        else:
            pygame.draw.rect(screen, (80,190,255), self.rect)
        if config.SHOW_HITBOXES:
            from game.movement import hitbox_of
            pygame.draw.rect(screen, (0,255,0), hitbox_of(self.rect), 1)
            pygame.draw.rect(screen, (0,100,255), self.rect, 1)
