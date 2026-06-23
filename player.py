"""
player.py
Represents the human player taking the penalty: the on-screen kicker figure
and the random decision logic that determines the outcome of each shot.
"""

import random

import pygame

from settings import (
    PENALTY_SPOT,
    ZONE_NAMES,
    MIN_GOAL_POINTS,
    MAX_GOAL_POINTS,
    SKIN,
)

KIT_SHIRT = (40, 60, 160)
KIT_SHORTS = (235, 235, 235)


def decide_shot(keeper_direction):
    """
    Decide the outcome of a single penalty kick.

    Returns a tuple: (is_goal, ball_target_zone, points)
    - is_goal           : bool, whether the shot results in a goal
    - ball_target_zone  : "LEFT" | "CENTER" | "RIGHT" - where the ball visually goes
    - points            : int, points earned this shot (0 if saved)

    The outcome (GOAL or SAVE) is decided completely at random. The ball's
    target zone is then chosen so the animation always looks coherent:
    - On a SAVE, the ball travels straight at the keeper's diving position.
    - On a GOAL, the ball travels to a different zone than the keeper dove to.
    """
    is_goal = random.random() < 0.5

    if is_goal:
        other_zones = [z for z in ZONE_NAMES if z != keeper_direction]
        ball_zone = random.choice(other_zones) if other_zones else random.choice(ZONE_NAMES)
        points = random.randint(MIN_GOAL_POINTS, MAX_GOAL_POINTS)
    else:
        ball_zone = keeper_direction
        points = 0

    return is_goal, ball_zone, points


class Kicker:
    """A small stylized figure standing behind the ball before the shot."""

    def __init__(self):
        self.x = PENALTY_SPOT[0]
        self.y = PENALTY_SPOT[1] + 6
        self.kicking = False
        self.timer = 0.0
        self.duration = 0.35
        self.visible = True

    def start_kick(self, duration):
        self.kicking = True
        self.timer = 0.0
        self.duration = max(0.01, duration)

    def update(self, dt):
        if self.kicking:
            self.timer += dt
            if self.timer >= self.duration:
                self.kicking = False

    def draw(self, surface):
        if not self.visible:
            return

        t = min(1.0, self.timer / self.duration) if self.kicking else 0.0
        leg_swing = 18 * (1 - abs(t - 0.5) * 2) if self.kicking else 0

        base_x, base_y = self.x, self.y

        # Shadow
        shadow = pygame.Surface((50, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (base_x - 25, base_y + 34))

        # Standing leg
        pygame.draw.line(surface, KIT_SHORTS, (base_x - 6, base_y + 10), (base_x - 6, base_y + 36), 8)
        # Kicking leg, swings forward toward the ball
        pygame.draw.line(
            surface, KIT_SHORTS,
            (base_x + 6, base_y + 10),
            (base_x + 6 + leg_swing, base_y + 36 - leg_swing * 0.4),
            8,
        )

        # Torso
        pygame.draw.rect(surface, KIT_SHIRT, (base_x - 11, base_y - 22, 22, 32), border_radius=8)

        # Arms
        pygame.draw.line(surface, SKIN, (base_x - 11, base_y - 14), (base_x - 22, base_y - 2), 6)
        pygame.draw.line(surface, SKIN, (base_x + 11, base_y - 14), (base_x + 20, base_y - 4), 6)

        # Head
        pygame.draw.circle(surface, SKIN, (int(base_x), int(base_y - 30)), 10)