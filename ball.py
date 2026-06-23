"""
ball.py
The football itself: drawn procedurally and animated from the penalty spot
to the goal line using an eased trajectory with a simulated 3D shrink (depth).
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
        self.x, self.y = PENALTY_SPOT
        self.start_pos = PENALTY_SPOT
        self.target_pos = PENALTY_SPOT
        self.radius = PENALTY_BALL_RADIUS
        self.progress = 1.0
        self.duration = 1.0
        self.moving = False
        self.rotation = 0.0

    def shoot(self, target_pos, duration):
        self.start_pos = PENALTY_SPOT
        self.target_pos = target_pos
        self.duration = max(0.01, duration)
        self.progress = 0.0
        self.moving = True

    def update(self, dt):
        if not self.moving:
            return

        self.progress += dt / self.duration
        self.rotation += dt * 720

        if self.progress >= 1.0:
            self.progress = 1.0
            self.moving = False

        t = ease_out_cubic(self.progress)
        sx, sy = self.start_pos
        tx, ty = self.target_pos
        self.x = sx + (tx - sx) * t
        self.y = sy + (ty - sy) * t
        self.radius = PENALTY_BALL_RADIUS + (GOAL_BALL_RADIUS - PENALTY_BALL_RADIUS) * t

    @property
    def is_finished(self):
        return self.progress >= 1.0 and not self.moving

    def draw(self, surface):
        radius = max(2, int(self.radius))

        # Ground shadow - helps sell the depth/perspective illusion.
        shadow_w = max(6, int(radius * 1.6))
        shadow_h = max(3, int(radius * 0.55))
        shadow = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, shadow_w * 2, shadow_h * 2))
        surface.blit(shadow, (self.x - shadow_w, self.y + radius * 0.6 - shadow_h))

        # Ball body
        pygame.draw.circle(surface, (235, 235, 235), (int(self.x), int(self.y)), radius)
        pygame.draw.circle(surface, (40, 40, 40), (int(self.x), int(self.y)), radius, 1)

        # Rotating pentagon pattern for a classic football look
        for i in range(5):
            angle = math.radians(self.rotation + i * 72)
            px = self.x + math.cos(angle) * radius * 0.45
            py = self.y + math.sin(angle) * radius * 0.45
            r = max(1, int(radius * 0.22))
            pygame.draw.circle(surface, (35, 35, 35), (int(px), int(py)), r)

        # Glossy highlight for a 3D feel
        hl_pos = (int(self.x - radius * 0.35), int(self.y - radius * 0.35))
        pygame.draw.circle(surface, (255, 255, 255), hl_pos, max(1, int(radius * 0.3)))