"""
Bomb system.

Key fixes:
- Explosion rays stop at the FIRST entity hit in each direction (not just walls).
- Bomb blocking uses hitbox_of() so it matches the movement system.
- Breakable tiles are destroyed only if they are the FIRST obstacle in that ray.
"""
from __future__ import annotations
import pygame
from config import (BOMB_SIZE, BOMB_FUSE_MS, EXPLOSION_DURATION_MS,
                    EXPLOSION_RANGE, TILE_SIZE, MAX_ACTIVE_BOMBS, BOMB_COOLDOWN_MS)
from assets_loader import get_sprite
from game.movement import hitbox_of


class Bomb:
    BLOCKING_DELAY = 600   # ms after placement before it blocks movement

    def __init__(self, x, y):
        self.rect         = pygame.Rect(x, y, BOMB_SIZE, BOMB_SIZE)
        self.elapsed      = 0
        self.is_exploding = False
        self.range        = EXPLOSION_RANGE
        self.spawn_time   = pygame.time.get_ticks()
        self._surf        = get_sprite("bomb.png")

    def update(self, dt):
        self.elapsed += dt
        if not self.is_exploding and self.elapsed >= BOMB_FUSE_MS:
            self.is_exploding = True

    def is_active(self):        return not self.is_exploding
    def is_exploding_now(self): return self.is_exploding and (self.elapsed-BOMB_FUSE_MS) < EXPLOSION_DURATION_MS
    def should_remove(self):    return self.is_exploding and (self.elapsed-BOMB_FUSE_MS) >= EXPLOSION_DURATION_MS
    def is_blocking(self, now): return (now - self.spawn_time) >= self.BLOCKING_DELAY

    def get_explosion_rays(self, map_rect, game_map=None):
        """
        Returns a dict: {direction: [list of tile rects in that ray]}.
        Each ray stops at the first wall (fixed = not included, breakable = included).
        Centre tile is in "center" key.
        """
        rays = {"center": [self.rect.copy()]}
        for (ddx, ddy), key in [((1,0),"right"),((-1,0),"left"),((0,1),"down"),((0,-1),"up")]:
            ray = []
            for step in range(1, self.range+1):
                nx = self.rect.x + ddx*step*TILE_SIZE
                ny = self.rect.y + ddy*step*TILE_SIZE
                cand = pygame.Rect(nx, ny, TILE_SIZE, TILE_SIZE)
                if not map_rect.contains(cand): break
                if game_map:
                    r, c = game_map.pixel_to_tile(nx, ny)
                    tv   = game_map.tile_at(r, c)
                    if tv == 1: break           # fixed wall — stop, don't include
                    if tv == 2:
                        ray.append(cand); break # breakable — include, then stop
                ray.append(cand)
            rays[key] = ray
        return rays

    def get_explosion_rects_clamped(self, map_rect, game_map=None):
        """Flat list of all explosion rects (used for drawing)."""
        rays = self.get_explosion_rays(map_rect, game_map)
        result = list(rays["center"])
        for k in ("right","left","down","up"):
            result.extend(rays[k])
        return result

    def draw(self, screen):
        if self.is_exploding: return
        frac = self.elapsed / BOMB_FUSE_MS
        if frac > 0.70:
            pulse = 1.0 + 0.15 * abs(pygame.time.get_ticks()%200-100)/100
            pw = int(BOMB_SIZE*pulse); ph = int(BOMB_SIZE*pulse)
            ox = self.rect.x-(pw-BOMB_SIZE)//2; oy = self.rect.y-(ph-BOMB_SIZE)//2
            if self._surf: screen.blit(pygame.transform.scale(self._surf,(pw,ph)),(ox,oy))
            else:          pygame.draw.ellipse(screen,(30,30,30),(ox,oy,pw,ph))
        else:
            if self._surf: screen.blit(pygame.transform.scale(self._surf,(BOMB_SIZE,BOMB_SIZE)),self.rect.topleft)
            else:          pygame.draw.ellipse(screen,(30,30,30),self.rect)


class BombSystem:
    def __init__(self, map_rect, game_map=None):
        self.bombs: list[Bomb] = []
        self.last_place_time   = 0
        self.map_rect = map_rect
        self.game_map = game_map

    def set_map(self, gm): self.game_map = gm

    def try_place_bomb(self, now, tile_pos):
        if now - self.last_place_time < BOMB_COOLDOWN_MS: return False
        if sum(1 for b in self.bombs if b.is_active()) >= MAX_ACTIVE_BOMBS: return False
        bx, by = tile_pos
        if self.game_map:
            r,c = self.game_map.pixel_to_tile(bx,by)
            if self.game_map.tile_at(r,c) != 0: return False
        for b in self.bombs:
            if b.rect.x==bx and b.rect.y==by: return False
        self.bombs.append(Bomb(bx,by))
        self.last_place_time = now
        try:
            from game.sounds import play; play("bomb_place.wav",0.55)
        except Exception: pass
        return True

    def update(self, dt):
        for b in self.bombs:
            was = b.is_exploding
            b.update(dt)
            if b.is_exploding and not was:
                # Destroy breakable tiles (one per ray direction)
                if self.game_map:
                    for rect in b.get_explosion_rects_clamped(self.map_rect, self.game_map):
                        r,c = self.game_map.pixel_to_tile(rect.x, rect.y)
                        self.game_map.break_tile(r,c)
                try:
                    from game.sounds import play; play("explosion.wav",0.8)
                except Exception: pass
        self.bombs = [b for b in self.bombs if not b.should_remove()]

    def _hits_rect(self, target_rect: pygame.Rect, entity_rects: list[pygame.Rect]) -> bool:
        """
        Check if target_rect is in any explosion, respecting ray-blocking:
        if another entity is closer in the same ray direction, target is shielded.
        """
        for b in self.bombs:
            if not b.is_exploding_now(): continue
            target_hb = hitbox_of(target_rect)
            rays = b.get_explosion_rays(self.map_rect, self.game_map)
            # Check centre
            if rays["center"][0].colliderect(target_hb): return True
            for key in ("right","left","down","up"):
                for i, tile_rect in enumerate(rays[key]):
                    if tile_rect.colliderect(target_hb):
                        # Check if any other entity is at an earlier step in this ray
                        blocked = False
                        for other in entity_rects:
                            if other == target_rect: continue
                            for j, earlier in enumerate(rays[key]):
                                if j >= i: break
                                if earlier.colliderect(hitbox_of(other)):
                                    blocked = True; break
                            if blocked: break
                        if not blocked: return True
        return False

    def get_player_explosion_damage(self, player_rect):
        """Returns damage amount if player is in explosion, else 0."""
        for b in self.bombs:
            if not b.is_exploding_now(): continue
            for rect in b.get_explosion_rects_clamped(self.map_rect, self.game_map):
                if rect.colliderect(player_rect): return 0.5
        return 0.0

    def check_enemy_hit(self, enemy_rect, all_enemy_rects=None):
        """True if enemy is hit by explosion, not shielded by another entity."""
        others = all_enemy_rects or [enemy_rect]
        return self._hits_rect(enemy_rect, others)

    def draw(self, screen):
        tick = pygame.time.get_ticks()
        for b in self.bombs:
            if b.is_exploding:
                rects = b.get_explosion_rects_clamped(self.map_rect, self.game_map)
                flicker = (tick//60)%2==0
                for i, r in enumerate(rects):
                    s = pygame.Surface((r.width,r.height),pygame.SRCALPHA)
                    if i==0: s.fill((255,200,50,220 if flicker else 170))
                    else:    s.fill((255,110,25,185 if flicker else 140))
                    screen.blit(s,(r.x,r.y))
                    pygame.draw.rect(screen,(255,240,80),r,1)
            else:
                b.draw(screen)

    def check_enemy_hit_single(self, bomb, enemy_rect: pygame.Rect,
                                all_enemy_rects: list) -> bool:
        """Check if ONE specific bomb hits ONE specific enemy (ray-aware).
        Uses hitbox_of(enemy_rect) for the target check — only the inner box counts.
        """
        if not bomb.is_exploding_now():
            return False
        target_hb = hitbox_of(enemy_rect)
        rays = bomb.get_explosion_rays(self.map_rect, self.game_map)
        # Centre
        if rays["center"][0].colliderect(target_hb):
            return True
        for key in ("right","left","down","up"):
            for i, tile_rect in enumerate(rays[key]):
                if tile_rect.colliderect(target_hb):
                    # Check if shielded by another entity closer in the ray
                    blocked = False
                    for other in all_enemy_rects:
                        if other is enemy_rect or other == enemy_rect:
                            continue
                        for j, earlier in enumerate(rays[key]):
                            if j >= i: break
                            if earlier.colliderect(hitbox_of(other)):
                                blocked = True; break
                        if blocked: break
                    if not blocked:
                        return True
        return False
