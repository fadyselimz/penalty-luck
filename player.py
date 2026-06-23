"""
player.py
Kicker figure and shot-outcome logic.
Keeper is strong — even off-zone dives have reach; power matters a lot.
"""

import random
import pygame
from settings import PENALTY_SPOT, WHITE, ZONE_NAMES, SKIN

KIT_SHIRT  = (40,  60, 160)
KIT_SHORTS = (230, 230, 230)


def decide_shot(keeper_direction: str, power: float, aim_zone: str):
    """
    Realistic keeper: dives cover a wide area.
    - Same zone as keeper dive: almost always saved unless very high power + corners.
    - Adjacent zone: keeper has long arms — partial chance of save depending on power.
    - Opposite zone: goal, but low power might allow a diving save anyway.

    Returns (is_goal, ball_zone, points)
    """
    same_zone  = (keeper_direction == aim_zone)
    # Is the aim zone adjacent to keeper (one step away)?
    order = ["LEFT", "CENTER", "RIGHT"]
    k_idx = order.index(keeper_direction)
    a_idx = order.index(aim_zone)
    dist  = abs(k_idx - a_idx)   # 0=same, 1=adjacent, 2=opposite

    if dist == 0:
        # Keeper went exact same way — save unless very powerful and aimed corner
        # Only ~15 % chance of goal even at full power
        is_goal = power > 0.80 and random.random() < 0.15
    elif dist == 1:
        # Adjacent — keeper's reach can still get there at low power
        # power 0 → ~25 % goal, power 1 → ~60 % goal
        goal_chance = 0.25 + power * 0.35
        is_goal = random.random() < goal_chance
    else:
        # Opposite side — keeper fully committed wrong way
        # But low power weak shot might be reachable: power 0 → 65 %, power 1 → 95 %
        goal_chance = 0.65 + power * 0.30
        is_goal = random.random() < goal_chance

    ball_zone = aim_zone
    # Points = the box value (set by game.py from BoxGrid); return 1 as placeholder
    points = 1 if is_goal else 0
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
        t     = min(1.0, self.timer / self.duration) if self.kicking else 0.0
        swing = 22 * (1 - abs(t - 0.5) * 2) if self.kicking else 0
        bx, by = self.x, self.y

        # Shadow
        sh = pygame.Surface((54, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
        surface.blit(sh, (bx - 27, by + 34))

        # Standing leg
        pygame.draw.line(surface, KIT_SHORTS, (bx-6, by+10), (bx-6, by+38), 8)
        # Boot (standing)
        pygame.draw.ellipse(surface, (30,30,30), (int(bx-12), int(by+34), 14, 7))

        # Kicking leg
        pygame.draw.line(surface, KIT_SHORTS, (bx+6, by+10),
                         (int(bx+6+swing), int(by+38-swing*0.45)), 8)
        # Boot (kicking)
        pygame.draw.ellipse(surface, (30,30,30),
                            (int(bx+6+swing-4), int(by+38-swing*0.45-3), 14, 7))

        # Torso
        pygame.draw.rect(surface, KIT_SHIRT, (bx-12, by-24, 24, 34), border_radius=8)
        # Kit number "10"
        nf = pygame.font.Font(None, 14)
        ns = nf.render("10", True, WHITE)
        surface.blit(ns, ns.get_rect(center=(int(bx), int(by-10))))

        # Arms
        pygame.draw.line(surface, SKIN, (bx-12, by-14), (bx-24, by-2), 6)
        pygame.draw.line(surface, SKIN, (bx+12, by-14), (bx+22, by-4), 6)

        # Head
        pygame.draw.circle(surface, SKIN, (int(bx), int(by-32)), 11)
        pygame.draw.circle(surface, (160, 110, 70), (int(bx), int(by-32)), 11, 1)
        # Hair
        pygame.draw.arc(surface, (60, 40, 20),
                        (int(bx)-11, int(by)-43, 22, 14), 0, 3.14, 4)