"""
goalkeeper.py
Realistic-looking goalkeeper — larger, more detailed, strong diver.
Keeper AI guesses correctly ~70% of the time regardless of power.
"""

import math
import pygame
from settings import (
    GOAL_CENTER_X, GOAL_TOP_Y, GOAL_HEIGHT, GOAL_WIDTH,
    KEEPER_KIT, KEEPER_KIT_DARK, SKIN,
)

WHITE = (255, 255, 255)


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


class Goalkeeper:
    def __init__(self):
        self.reset()

    def reset(self):
        self.home_x    = GOAL_CENTER_X
        self.home_y    = GOAL_TOP_Y + GOAL_HEIGHT - 32
        self.x         = self.home_x
        self.y         = self.home_y
        self.target_x  = self.home_x
        self.lean      = 0.0
        self.direction = "CENTER"
        self.progress  = 1.0
        self.duration  = 1.0
        self.diving    = False

    def start_dive(self, direction: str, duration: float):
        self.direction = direction
        # Keeper reaches all the way to the post — very wide coverage
        max_slide = GOAL_WIDTH * 0.46
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
            self.y    = self.home_y + 22 * t
        if self.progress >= 1.0:
            self.diving = False

    def draw(self, surface: pygame.Surface):
        lean    = self.lean
        body_w  = 34 + abs(lean) * 28   # keeper stretches wide when diving
        body_h  = 52 - abs(lean) * 18
        lean_px = lean * 32

        cx, cy = int(self.x), int(self.y)

        # ---- Ground shadow ----
        sh = pygame.Surface((int(body_w * 2.0), 16), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 110), sh.get_rect())
        surface.blit(sh, (cx - int(body_w), cy + int(body_h // 2) + 2))

        # ---- Legs ----
        leg_color = (30, 30, 30)      # black shorts
        sock_col  = WHITE
        boot_col  = (20, 20, 20)

        for side in (-1, 1):
            lx = cx + side * int(body_w * 0.22) + int(lean_px * 0.3)
            ly = cy + int(body_h // 2) - 4
            # Short (thigh)
            pygame.draw.rect(surface, leg_color, (lx - 5, ly, 10, 20), border_radius=3)
            # Sock
            pygame.draw.rect(surface, sock_col,  (lx - 4, ly + 18, 8, 14), border_radius=2)
            # Boot
            pygame.draw.ellipse(surface, boot_col,
                                (lx - 7, ly + 28, 16, 8))

        # ---- Torso / jersey ----
        torso = pygame.Rect(0, 0, int(body_w), int(body_h))
        torso.center = (cx + int(lean_px * 0.3), cy)
        pygame.draw.rect(surface, KEEPER_KIT, torso, border_radius=12)
        # Jersey stripe
        stripe_rect = pygame.Rect(torso.x + torso.w // 3, torso.y + 4,
                                  torso.w // 3, torso.h - 8)
        pygame.draw.rect(surface, KEEPER_KIT_DARK, stripe_rect, border_radius=4)
        pygame.draw.rect(surface, KEEPER_KIT_DARK, torso, width=2, border_radius=12)

        # ---- Arms ----
        # Keeper stretches arms way out in dive direction
        arm_base_len = 36 + abs(lean) * 26
        arm_y_base   = cy - int(body_h * 0.18)

        def arm_end(side_sign, is_dive_side):
            length = arm_base_len * (1.4 if is_dive_side else 0.5)
            ex = cx + int(body_w // 2) * side_sign + int(lean_px * 0.3) + int(length * side_sign)
            ey = arm_y_base + int(lean * 26 * side_sign * -1)
            return (ex, ey)

        if lean < -0.1:      # diving LEFT
            l_end = arm_end(-1, True)
            r_end = arm_end( 1, False)
        elif lean > 0.1:     # diving RIGHT
            l_end = arm_end(-1, False)
            r_end = arm_end( 1, True)
        else:                # standing
            l_end = (cx - int(body_w // 2) - 28, arm_y_base)
            r_end = (cx + int(body_w // 2) + 28, arm_y_base)

        for sx, sy, ex, ey in [
            (cx - int(body_w // 2) + int(lean_px * 0.3), arm_y_base, *l_end),
            (cx + int(body_w // 2) + int(lean_px * 0.3), arm_y_base, *r_end),
        ]:
            pygame.draw.line(surface, SKIN, (sx, sy), (ex, ey), 9)

        # Gloves — big and bright yellow
        for ex, ey in (l_end, r_end):
            pygame.draw.circle(surface, (230, 210, 40), (ex, ey), 9)
            pygame.draw.circle(surface, (180, 160, 10), (ex, ey), 9, 2)
            # finger lines
            for i in range(3):
                ang = math.radians(150 + i * 30 + (lean * 30))
                pygame.draw.line(surface, (140, 120, 5),
                                 (ex, ey),
                                 (ex + int(math.cos(ang)*7), ey + int(math.sin(ang)*7)), 1)

        # ---- Head ----
        hx = cx + int(lean_px * 0.25)
        hy = cy - int(body_h // 2) - 13
        # Neck
        pygame.draw.rect(surface, SKIN, (hx - 5, hy + 8, 10, 10))
        # Head
        pygame.draw.circle(surface, SKIN, (hx, hy), 13)
        pygame.draw.circle(surface, (150, 100, 60), (hx, hy), 13, 1)
        # Keeper gloves cap
        pygame.draw.arc(surface, KEEPER_KIT_DARK,
                        (hx - 13, hy - 13, 26, 14), 0, math.pi, 5)
        # Eyes
        for ex_off in (-4, 4):
            pygame.draw.circle(surface, (30, 30, 30), (hx + ex_off, hy - 1), 2)