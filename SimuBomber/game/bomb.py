"""
Bomb system with M/M/1 queue model for bomb placement requests.

The bomb placement uses a FIFO queue to model a queuing system:
- Arrivals: player bomb requests
- Service: bomb placement (subject to cooldown + capacity)
- Metrics: arrival count, service count, rejection count, wait times

Also includes ray-based explosions, cached rays, and centered hitboxes.
"""
from __future__ import annotations
import pygame
from config import (BOMB_SIZE, BOMB_FUSE_MS, EXPLOSION_DURATION_MS,
                    EXPLOSION_RANGE, TILE_SIZE, MAX_ACTIVE_BOMBS, BOMB_COOLDOWN_MS)
from assets_loader import get_sprite
from game.movement import hitbox_of
from collections import deque


class Bomb:
    BLOCKING_DELAY = 600

    def __init__(self, x, y):
        self.rect         = pygame.Rect(x, y, BOMB_SIZE, BOMB_SIZE)
        self.elapsed      = 0
        self.is_exploding = False
        self.range        = EXPLOSION_RANGE
        self.spawn_time   = pygame.time.get_ticks()
        self._surf        = get_sprite("bomb.png")
        self._cached_rays = None

    def update(self, dt):
        self.elapsed += dt
        if not self.is_exploding and self.elapsed >= BOMB_FUSE_MS:
            self.is_exploding = True

    def cache_explosion_rays(self, map_rect, game_map=None):
        self._cached_rays = self._compute_rays(map_rect, game_map)

    def is_active(self):        return not self.is_exploding
    def is_exploding_now(self): return self.is_exploding and (self.elapsed-BOMB_FUSE_MS) < EXPLOSION_DURATION_MS
    def should_remove(self):    return self.is_exploding and (self.elapsed-BOMB_FUSE_MS) >= EXPLOSION_DURATION_MS
    def is_blocking(self, now): return (now - self.spawn_time) >= self.BLOCKING_DELAY

    def _compute_rays(self, map_rect, game_map=None):
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
                    if tv == 1: break
                    if tv == 2:
                        ray.append(cand); break
                ray.append(cand)
            rays[key] = ray
        return rays

    def get_explosion_rays(self, map_rect, game_map=None):
        if self._cached_rays is not None:
            return self._cached_rays
        return self._compute_rays(map_rect, game_map)

    def get_explosion_rects_clamped(self, map_rect, game_map=None):
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
    """Bomb system with M/M/1 queue model for placement requests.

    The queue is observational: bomb requests enter a FIFO queue and are
    processed immediately (service = cooldown + capacity check). The queue
    telemetry tracks arrivals, services, rejections, and wait times for
    simulation validation.
    """

    def __init__(self, map_rect, game_map=None):
        self.bombs: list[Bomb] = []
        self.last_place_time   = 0
        self.map_rect = map_rect
        self.game_map = game_map
        # ── Queue (M/M/1 observational model) ──
        self._request_queue: deque[dict] = deque()
        self._queue_event_log: deque[dict] = deque(maxlen=5000)
        self._queue_sequence = 0
        self._queue_arrivals = 0
        self._queue_served = 0
        self._queue_rejected = 0
        self._queue_rejected_cooldown = 0
        self._queue_rejected_capacity = 0
        self._queue_total_wait_ms = 0
        self._queue_max_depth = 0

    def set_map(self, gm): self.game_map = gm

    # ── Queue API ──────────────────────────────────────────────────────────

    def request_place_bomb(self, current_time: int, position: tuple[int, int]) -> bool:
        """Record a bomb request in the internal queue and process it immediately.

        The queue models an M/M/1 system: arrivals (player requests) enter a FIFO,
        service occurs instantly (subject to cooldown + capacity constraints), and
        metrics are collected for simulation validation.
        """
        self._queue_sequence += 1
        request = {
            "request_id": self._queue_sequence,
            "request_time": current_time,
            "position": position,
        }
        self._request_queue.append(request)
        self._queue_arrivals += 1
        self._queue_max_depth = max(self._queue_max_depth, len(self._request_queue))
        self._queue_event_log.append({
            "tick_ms": current_time,
            "event": "arrival",
            "request_id": request["request_id"],
            "queue_depth": len(self._request_queue),
        })
        return self._service_internal_queue(current_time)

    def _service_internal_queue(self, current_time: int) -> bool:
        """Process all pending requests in the queue (immediate service)."""
        serviced_any = False
        while self._request_queue:
            request = self._request_queue.popleft()
            placed, reason = self._try_place_bomb(current_time, request["position"])
            wait_ms = max(0, current_time - request["request_time"])
            self._queue_event_log.append({
                "tick_ms": current_time,
                "event": "service" if placed else "rejection",
                "request_id": request["request_id"],
                "wait_ms": wait_ms,
                "reason": reason,
                "queue_depth": len(self._request_queue),
            })
            if placed:
                self._queue_served += 1
                self._queue_total_wait_ms += wait_ms
                serviced_any = True
            else:
                self._queue_rejected += 1
                if reason == "cooldown":
                    self._queue_rejected_cooldown += 1
                elif reason == "capacity":
                    self._queue_rejected_capacity += 1
        return serviced_any

    def observe_queue(self) -> dict:
        """Return an internal snapshot of bomb request-queue telemetry."""
        avg_wait = (self._queue_total_wait_ms / self._queue_served) if self._queue_served else 0.0
        return {
            "arrivals": self._queue_arrivals,
            "served": self._queue_served,
            "rejected": self._queue_rejected,
            "rejected_cooldown": self._queue_rejected_cooldown,
            "rejected_capacity": self._queue_rejected_capacity,
            "current_depth": len(self._request_queue),
            "max_depth": self._queue_max_depth,
            "avg_wait_ms": avg_wait,
            "event_count": len(self._queue_event_log),
        }

    # ── Bomb placement (internal) ──────────────────────────────────────────

    def _try_place_bomb(self, current_time: int, position: tuple[int, int]) -> tuple[bool, str]:
        """Attempt to place a bomb; returns (placed, reason)."""
        bx, by = position
        if current_time - self.last_place_time < BOMB_COOLDOWN_MS:
            return False, "cooldown"
        if sum(1 for b in self.bombs if b.is_active()) >= MAX_ACTIVE_BOMBS:
            return False, "capacity"
        if self.game_map:
            r, c = self.game_map.pixel_to_tile(bx, by)
            if self.game_map.tile_at(r, c) != 0:
                return False, "wall"
        for b in self.bombs:
            if b.rect.x == bx and b.rect.y == by:
                return False, "occupied"
        self.bombs.append(Bomb(bx, by))
        self.last_place_time = current_time
        try:
            from game.sounds import play; play("bomb_place.wav", 0.55)
        except Exception: pass
        return True, "placed"

    def try_place_bomb(self, now, tile_pos):
        """Backward-compatible: place bomb through the queue."""
        return self.request_place_bomb(now, tile_pos)

    # ── Update ─────────────────────────────────────────────────────────────

    def update(self, dt):
        for b in self.bombs:
            was = b.is_exploding
            b.update(dt)
            if b.is_exploding and not was:
                if self.game_map:
                    b.cache_explosion_rays(self.map_rect, self.game_map)
                    for rect in b.get_explosion_rects_clamped(self.map_rect, self.game_map):
                        r, c = self.game_map.pixel_to_tile(rect.x, rect.y)
                        self.game_map.break_tile(r, c)
                try:
                    from game.sounds import play; play("explosion.wav", 0.8)
                except Exception: pass
        self.bombs = [b for b in self.bombs if not b.should_remove()]

    # ── Collision ──────────────────────────────────────────────────────────

    def _hits_rect(self, target_rect: pygame.Rect, entity_rects: list[pygame.Rect]) -> bool:
        for b in self.bombs:
            if not b.is_exploding_now(): continue
            target_hb = hitbox_of(target_rect)
            rays = b.get_explosion_rays(self.map_rect, self.game_map)
            exp_hb = hitbox_of(rays["center"][0])
            if exp_hb.colliderect(target_hb): return True
            for key in ("right","left","down","up"):
                for i, tile_rect in enumerate(rays[key]):
                    exp_hb = hitbox_of(tile_rect)
                    if exp_hb.colliderect(target_hb):
                        blocked = False
                        for other in entity_rects:
                            if other == target_rect: continue
                            for j, earlier in enumerate(rays[key]):
                                if j >= i: break
                                if hitbox_of(earlier).colliderect(hitbox_of(other)):
                                    blocked = True; break
                            if blocked: break
                        if not blocked: return True
        return False

    def get_player_explosion_damage(self, player_rect):
        for b in self.bombs:
            if not b.is_exploding_now(): continue
            player_hb = hitbox_of(player_rect)
            for rect in b.get_explosion_rects_clamped(self.map_rect, self.game_map):
                if hitbox_of(rect).colliderect(player_hb): return 0.5
        return 0.0

    def check_enemy_hit(self, enemy_rect, all_enemy_rects=None):
        others = all_enemy_rects or [enemy_rect]
        return self._hits_rect(enemy_rect, others)

    def check_enemy_hit_single(self, bomb, enemy_rect: pygame.Rect,
                                all_enemy_rects: list) -> bool:
        if not bomb.is_exploding_now(): return False
        target_hb = hitbox_of(enemy_rect)
        rays = bomb.get_explosion_rays(self.map_rect, self.game_map)
        if hitbox_of(rays["center"][0]).colliderect(target_hb): return True
        for key in ("right","left","down","up"):
            for i, tile_rect in enumerate(rays[key]):
                exp_hb = hitbox_of(tile_rect)
                if exp_hb.colliderect(target_hb):
                    blocked = False
                    for other in all_enemy_rects:
                        if other is enemy_rect or other == enemy_rect: continue
                        for j, earlier in enumerate(rays[key]):
                            if j >= i: break
                            if hitbox_of(earlier).colliderect(hitbox_of(other)):
                                blocked = True; break
                        if blocked: break
                    if not blocked: return True
        return False

    # ── Draw ───────────────────────────────────────────────────────────────

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
