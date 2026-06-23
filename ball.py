"""
ball.py
Ball with curved arc trajectory, spin, and perspective shrink.
"""

import math
import pygame
from settings import PENALTY_SPOT, PENALTY_BALL_RADIUS, GOAL_BALL_RADIUS


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

    def shoot(self, target_pos, duration, power=0.5):
        self.start_pos   = PENALTY_SPOT
        self.target_pos  = target_pos
        self.duration    = max(0.01, duration)
        self.progress    = 0.0
        self.moving      = True
        # Higher power = flatter arc; low power = more lofted
        self._arc_height = (1.0 - power) * 60

    def update(self, dt):
        if not self.moving:
            return
        self.progress += dt / self.duration
        self.rotation += dt * 680
        if self.progress >= 1.0:
            self.progress = 1.0
            self.moving   = False

        t  = ease_out_cubic(self.progress)
        sx, sy = self.start_pos
        tx, ty = self.target_pos
        self.x = sx + (tx - sx) * t
        # Arc: sin curve lifts ball in first half of flight
        arc    = math.sin(self.progress * math.pi) * self._arc_height
        self.y = sy + (ty - sy) * t - arc
        self.radius = PENALTY_BALL_RADIUS + (GOAL_BALL_RADIUS - PENALTY_BALL_RADIUS) * t

    @property
    def is_finished(self):
        return self.progress >= 1.0 and not self.moving

    def draw(self, surface):
        r = max(2, int(self.radius))
        ix, iy = int(self.x), int(self.y)

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
