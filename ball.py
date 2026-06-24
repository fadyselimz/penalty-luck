"""
ball.py
Ball with curved arc trajectory, spin, and perspective shrink.
"""

import math
import pygame
from settings import PENALTY_SPOT, PENALTY_BALL_RADIUS, GOAL_BALL_RADIUS, FIELD_BOTTOM_Y

GROUND_Y = FIELD_BOTTOM_Y - 18
GRAVITY  = 620.0


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y   = PENALTY_SPOT
        self.start_pos   = PENALTY_SPOT
        self.target_pos  = PENALTY_SPOT
        self.radius      = PENALTY_BALL_RADIUS
        self.progress    = 1.0
        self.duration    = 1.0
        self.moving      = False
        self.rotation    = 0.0
        self._arc_height = 0.0   # mid-flight rise (pixels)
        self.caught      = False
        self.rebounding  = False
        self.vx          = 0.0
        self.vy          = 0.0
        self._vx         = 0.0
        self._vy         = 0.0

    def shoot(self, target_pos, duration, power=0.5):
        self.start_pos   = PENALTY_SPOT
        self.target_pos  = target_pos
        self.duration    = max(0.01, duration)
        self.progress    = 0.0
        self.moving      = True
        self.caught      = False
        self.rebounding  = False
        self.vx = self.vy = self._vx = self._vy = 0.0
        # Higher power = flatter arc; low power = more lofted
        self._arc_height = (1.0 - power) * 60

    def catch_at(self, x, y):
        self.x          = x
        self.y          = y
        self.radius     = GOAL_BALL_RADIUS
        self.moving     = False
        self.rebounding = False
        self.caught     = True
        self.vx = self.vy = 0.0

    def start_rebound(self, nx, ny, px=None, py=None):
        """Deflect off the keeper's body — realistic parry away from goal."""
        if px is not None:
            self.x = px + nx * self.radius
            self.y = py + ny * self.radius

        speed = max(math.hypot(self._vx, self._vy), 240.0)
        dot = self._vx * nx + self._vy * ny
        if dot < 0:
            self.vx = self._vx - 2.0 * dot * nx
            self.vy = self._vy - 2.0 * dot * ny
        else:
            self.vx = nx * speed
            self.vy = ny * speed

        self.vx *= 0.62
        self.vy *= 0.62
        if self.vy > -60:
            self.vy -= 90

        self.moving     = False
        self.rebounding = True
        self.caught     = False

    def update(self, dt):
        if self.caught:
            return
        if self.rebounding:
            self._update_rebound(dt)
            return
        if not self.moving:
            return

        prev_x, prev_y = self.x, self.y
        self.progress += dt / self.duration
        self.rotation += dt * 680
        if self.progress >= 1.0:
            self.progress = 1.0
            self.moving   = False

        t  = ease_out_cubic(self.progress)
        sx, sy = self.start_pos
        tx, ty = self.target_pos
        self.x = sx + (tx - sx) * t
        arc    = math.sin(self.progress * math.pi) * self._arc_height
        self.y = sy + (ty - sy) * t - arc
        self.radius = PENALTY_BALL_RADIUS + (GOAL_BALL_RADIUS - PENALTY_BALL_RADIUS) * t

        if dt > 0:
            self._vx = (self.x - prev_x) / dt
            self._vy = (self.y - prev_y) / dt

    def _update_rebound(self, dt):
        self.rotation += dt * 420
        self.vy += GRAVITY * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt

        floor = GROUND_Y - self.radius
        if self.y >= floor:
            self.y  = floor
            if abs(self.vy) > 35:
                self.vy *= -0.38
                self.vx *= 0.72
            else:
                self.vy = 0.0
                self.vx *= 0.82

        self._vx, self._vy = self.vx, self.vy

    @property
    def is_settled(self):
        if not self.rebounding:
            return False
        on_ground = self.y >= GROUND_Y - self.radius - 2
        slow = abs(self.vx) < 18 and abs(self.vy) < 18
        return on_ground and slow

    @property
    def is_finished(self):
        return self.progress >= 1.0 and not self.moving

    def draw(self, surface):
        r = max(2, int(self.radius))
        ix, iy = int(self.x), int(self.y)

        if not self.caught and not self.rebounding:
            # Ground shadow (follows x; stays on ground)
            sw = max(6, int(r * 1.7))
            sh = max(3, int(r * 0.5))
            shadow = pygame.Surface((sw * 2, sh * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, sw * 2, sh * 2))
            surface.blit(shadow, (ix - sw, iy + r - sh + 4))

        # Ball body
        pygame.draw.circle(surface, (238, 238, 238), (ix, iy), r)
        pygame.draw.circle(surface, (40,  40,  40),  (ix, iy), r, 1)

        # Pentagon panels
        for i in range(5):
            angle = math.radians(self.rotation + i * 72)
            px = ix + math.cos(angle) * r * 0.44
            py = iy + math.sin(angle) * r * 0.44
            pr = max(1, int(r * 0.22))
            pygame.draw.circle(surface, (30, 30, 30), (int(px), int(py)), pr)

        # Gloss highlight
        pygame.draw.circle(surface, (255, 255, 255),
                           (ix - int(r * 0.34), iy - int(r * 0.34)),
                           max(1, int(r * 0.28)))
