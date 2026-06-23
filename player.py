"""
player.py
Kicker figure and shot-outcome logic.
Power level now influences keeper save probability.
"""

import random
import pygame
from settings import PENALTY_SPOT, ZONE_NAMES, SKIN

KIT_SHIRT  = (40,  60, 160)
KIT_SHORTS = (230, 230, 230)


def decide_shot(keeper_direction: str, power: float, aim_zone: str):
    """
    Determine shot outcome from the player's aim zone, keeper direction, and power.

    - If keeper dives to the same zone: save unless power is high AND shot is
      in a corner column (hard to reach).
    - If keeper dives to a different zone: goal.
    - Returns (is_goal, ball_zone, points)
    """
    from settings import BOX_VALUE_TABLE
    weights = [w for _, w in BOX_VALUE_TABLE]
    values  = [v for v, _ in BOX_VALUE_TABLE]

    same_zone = (keeper_direction == aim_zone)

    if same_zone:
        # High power can still beat the keeper if aimed well
        save_threshold = 0.72 - power * 0.30   # e.g. power=1 → threshold=0.42
        is_goal = (power > save_threshold) and random.random() < 0.45
    else:
        is_goal = True

    ball_zone = aim_zone
    points    = random.choices(values, weights=weights, k=1)[0] if is_goal else 0
    return is_goal, ball_zone, points


class Kicker:
    def __init__(self):
        self.x        = PENALTY_SPOT[0]
        self.y        = PENALTY_SPOT[1] + 6
        self.kicking  = False
        self.timer    = 0.0
        self.duration = 0.30

    def start_kick(self, duration):
        self.kicking  = True
        self.timer    = 0.0
        self.duration = max(0.01, duration)

    def update(self, dt):
        if self.kicking:
            self.timer += dt
            if self.timer >= self.duration:
                self.kicking = False

    def draw(self, surface):
        t = min(1.0, self.timer / self.duration) if self.kicking else 0.0
        swing = 22 * (1 - abs(t - 0.5) * 2) if self.kicking else 0
        bx, by = self.x, self.y

        # Shadow
        sh = pygame.Surface((54, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
        surface.blit(sh, (bx - 27, by + 34))

        # Legs
        pygame.draw.line(surface, KIT_SHORTS, (bx-6, by+10), (bx-6, by+38), 8)
        pygame.draw.line(surface, KIT_SHORTS, (bx+6, by+10),
                         (int(bx+6+swing), int(by+38-swing*0.45)), 8)

        # Torso
        pygame.draw.rect(surface, KIT_SHIRT, (bx-12, by-24, 24, 34), border_radius=8)

        # Arms
        pygame.draw.line(surface, SKIN, (bx-12, by-14), (bx-24, by-2), 6)
        pygame.draw.line(surface, SKIN, (bx+12, by-14), (bx+22, by-4), 6)

        # Head
        pygame.draw.circle(surface, SKIN, (int(bx), int(by-32)), 11)
        pygame.draw.circle(surface, (160, 110, 70), (int(bx), int(by-32)), 11, 1)
