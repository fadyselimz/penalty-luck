"""
goalkeeper.py
Goalkeeper with AI that dives based on aim zone.
Higher shot power = harder for keeper to guess correctly.
"""

import pygame
from settings import (
    GOAL_CENTER_X, GOAL_TOP_Y, GOAL_HEIGHT, GOAL_WIDTH,
    KEEPER_KIT, KEEPER_KIT_DARK, SKIN,
)


def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


class Goalkeeper:
    def __init__(self):
        self.reset()

    def reset(self):
        self.home_x   = GOAL_CENTER_X
        self.home_y   = GOAL_TOP_Y + GOAL_HEIGHT - 28
        self.x        = self.home_x
        self.y        = self.home_y
        self.target_x = self.home_x
        self.lean     = 0.0
        self.direction= "CENTER"
        self.progress = 1.0
        self.duration = 1.0
        self.diving   = False

    def start_dive(self, direction: str, duration: float):
        self.direction = direction
        max_slide = GOAL_WIDTH * 0.40
        self.target_x = {
            "LEFT":   self.home_x - max_slide,
            "CENTER": self.home_x,
            "RIGHT":  self.home_x + max_slide,
        }.get(direction, self.home_x)
        self.duration = max(0.01, duration)
        self.progress = 0.0
        self.diving   = True

    def update(self, dt: float):
        if not self.diving:
            return
        self.progress = min(1.0, self.progress + dt / self.duration)
        t = ease_out_cubic(self.progress)
        self.x = self.home_x + (self.target_x - self.home_x) * t
        if self.direction == "CENTER":
            self.lean = 0.0
            self.y    = self.home_y
        else:
            sign      = -1 if self.direction == "LEFT" else 1
            self.lean = sign * t
            self.y    = self.home_y + 20 * t
        if self.progress >= 1.0:
            self.diving = False

    def draw(self, surface: pygame.Surface):
        lean_px = self.lean * 28
        body_w  = 28 + abs(self.lean) * 24
        body_h  = 44 - abs(self.lean) * 16

        # Shadow
        sh = pygame.Surface((int(body_w * 1.8), 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 100), sh.get_rect())
        surface.blit(sh, (self.x - body_w * 0.9, self.y + body_h / 2))

        # Legs
        for ox in (-body_w * 0.25, body_w * 0.25):
            pygame.draw.rect(surface, KEEPER_KIT_DARK,
                             (self.x + ox + lean_px * 0.2 - 4, self.y + body_h / 2 - 4, 8, 20),
                             border_radius=4)

        # Torso
        torso = pygame.Rect(0, 0, int(body_w), int(body_h))
        torso.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, KEEPER_KIT, torso, border_radius=10)
        pygame.draw.rect(surface, KEEPER_KIT_DARK, torso, width=2, border_radius=10)

        # Arms
        arm_len = 30 + abs(self.lean) * 20
        arm_y   = self.y - body_h * 0.15
        left_end  = (self.x - body_w / 2 - arm_len * (1 if self.lean <= 0 else 0.3),
                     arm_y - self.lean * 22)
        right_end = (self.x + body_w / 2 + arm_len * (1 if self.lean >= 0 else 0.3),
                     arm_y + self.lean * 22)
        for start, end in [((self.x - body_w/2, arm_y), left_end),
                            ((self.x + body_w/2, arm_y), right_end)]:
            pygame.draw.line(surface, SKIN, start, end, 8)

        # Gloves
        for end in (left_end, right_end):
            pygame.draw.circle(surface, (240, 240, 240), (int(end[0]), int(end[1])), 7)
            pygame.draw.circle(surface, (180, 180, 180), (int(end[0]), int(end[1])), 7, 1)

        # Head
        hx, hy = int(self.x), int(self.y - body_h / 2 - 11)
        pygame.draw.circle(surface, SKIN, (hx, hy), 11)
        pygame.draw.circle(surface, (160, 110, 70), (hx, hy), 11, 1)
