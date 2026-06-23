"""
goalkeeper.py
The goalkeeper: a procedurally drawn figure that dives left, stays center,
or dives right with a smooth eased animation. Drawn entirely from rects,
circles and lines (no images).
"""

import pygame

from settings import (
    GOAL_CENTER_X,
    GOAL_TOP_Y,
    GOAL_HEIGHT,
    ZONES,
    KEEPER_KIT,
    KEEPER_KIT_DARK,
    SKIN,
)


def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)


class Goalkeeper:
    def __init__(self):
        self.reset()

    def reset(self):
        self.home_x = GOAL_CENTER_X
        self.home_y = GOAL_TOP_Y + GOAL_HEIGHT - 35
        self.x = self.home_x
        self.y = self.home_y
        self.target_x = self.home_x
        self.lean = 0.0
        self.direction = "CENTER"
        self.progress = 1.0
        self.duration = 1.0
        self.diving = False

    def start_dive(self, direction, duration):
        self.direction = direction
        self.target_x = ZONES[direction]
        self.duration = max(0.01, duration)
        self.progress = 0.0
        self.diving = True

    def update(self, dt):
        if not self.diving:
            return

        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            self.diving = False

        t = ease_out_quad(self.progress)
        self.x = self.home_x + (self.target_x - self.home_x) * t

        if self.direction == "CENTER":
            self.lean = 0.0
            self.y = self.home_y
        else:
            sign = -1 if self.direction == "LEFT" else 1
            self.lean = sign * t
            self.y = self.home_y + 18 * t

    def draw(self, surface):
        lean_px = self.lean * 26
        body_w = 26 + abs(self.lean) * 22
        body_h = 46 - abs(self.lean) * 18

        # Ground shadow
        shadow = pygame.Surface((int(body_w * 1.6), 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), shadow.get_rect())
        surface.blit(shadow, (self.x - body_w * 0.8, self.y + body_h / 2))

        # Legs
        leg_color = KEEPER_KIT_DARK
        pygame.draw.rect(
            surface, leg_color,
            (self.x - body_w / 2 + lean_px * 0.2, self.y + body_h / 2 - 4, 10, 18),
            border_radius=4,
        )
        pygame.draw.rect(
            surface, leg_color,
            (self.x + body_w / 2 - 14 + lean_px * 0.2, self.y + body_h / 2 - 4, 10, 18),
            border_radius=4,
        )

        # Torso
        torso_rect = pygame.Rect(0, 0, int(body_w), int(body_h))
        torso_rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, KEEPER_KIT, torso_rect, border_radius=10)
        pygame.draw.rect(surface, KEEPER_KIT_DARK, torso_rect, width=2, border_radius=10)

        # Arms stretched outward in the dive direction
        arm_len = 28 + abs(self.lean) * 18
        arm_y = self.y - body_h * 0.15
        left_arm_end = (
            self.x - body_w / 2 - arm_len * (1 if self.lean <= 0 else 0.3),
            arm_y - self.lean * 20,
        )
        right_arm_end = (
            self.x + body_w / 2 + arm_len * (1 if self.lean >= 0 else 0.3),
            arm_y + self.lean * 20,
        )
        pygame.draw.line(surface, SKIN, (self.x - body_w / 2, arm_y), left_arm_end, 8)
        pygame.draw.line(surface, SKIN, (self.x + body_w / 2, arm_y), right_arm_end, 8)

        # Head
        head_pos = (int(self.x), int(self.y - body_h / 2 - 10))
        pygame.draw.circle(surface, SKIN, head_pos, 11)
        pygame.draw.circle(surface, (30, 30, 30), head_pos, 11, 1)

        # Gloves
        pygame.draw.circle(surface, (240, 240, 240), (int(left_arm_end[0]), int(left_arm_end[1])), 7)
        pygame.draw.circle(surface, (240, 240, 240), (int(right_arm_end[0]), int(right_arm_end[1])), 7)