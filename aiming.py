"""
aiming.py
Handles the two-phase aiming mechanic:
  Phase 1 – free crosshair movement over the goal mouth
  Phase 2 – hold SPACE / left-click to charge a power bar; release to shoot

The crosshair wobbles slightly to make precision challenging.
"""

import math
import random
import pygame
from settings import (
    GOAL_CENTER_X, GOAL_TOP_Y, GOAL_WIDTH, GOAL_HEIGHT,
    WHITE, GOLD, RED,
)
from assets import get_font


class AimingSystem:
    MAX_CHARGE_TIME = 1.4   # seconds to fill bar fully
    WOBBLE_AMOUNT   = 18    # max pixel wobble radius at zero power

    def __init__(self):
        self.active     = False   # aiming mode on
        self.charging   = False   # holding down for power
        self.charge     = 0.0    # 0..1
        self.aim_x      = GOAL_CENTER_X
        self.aim_y      = GOAL_TOP_Y + GOAL_HEIGHT // 2
        self._wobble_x  = 0.0
        self._wobble_y  = 0.0
        self._wobble_t  = 0.0
        self._hint_font = get_font(17)
        self._bar_font  = get_font(14, bold=True)

    # ------------------------------------------------------------------
    def start(self):
        self.active   = True
        self.charging = False
        self.charge   = 0.0

    def stop(self):
        self.active   = False
        self.charging = False
        self.charge   = 0.0

    # ------------------------------------------------------------------
    def handle_event(self, event):
        """Returns True when the player releases a charged shot."""
        if not self.active:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.aim_x = event.pos[0]
            self.aim_y = event.pos[1]

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            trigger = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                      (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
            if trigger and self._in_goal(self.aim_x, self.aim_y):
                self.charging = True

        if event.type in (pygame.MOUSEBUTTONUP, pygame.KEYUP):
            release = (event.type == pygame.MOUSEBUTTONUP and event.button == 1) or \
                      (event.type == pygame.KEYUP and event.key == pygame.K_SPACE)
            if release and self.charging and self.charge > 0.08:
                self.charging = False
                return True          # signal: fire the shot

        return False

    def _in_goal(self, x, y):
        left  = GOAL_CENTER_X - GOAL_WIDTH  // 2
        right = GOAL_CENTER_X + GOAL_WIDTH  // 2
        return left <= x <= right and GOAL_TOP_Y <= y <= GOAL_TOP_Y + GOAL_HEIGHT

    # ------------------------------------------------------------------
    def update(self, dt):
        if not self.active:
            return

        # Wobble (harder to aim in center; diminishes with charge)
        self._wobble_t += dt * 4.5
        wobble_scale = self.WOBBLE_AMOUNT * (1.0 - self.charge * 0.6)
        self._wobble_x = math.sin(self._wobble_t * 1.3) * wobble_scale
        self._wobble_y = math.cos(self._wobble_t * 1.7) * wobble_scale * 0.6

        if self.charging:
            self.charge = min(1.0, self.charge + dt / self.MAX_CHARGE_TIME)

    def effective_aim(self):
        """Return the wobble-adjusted target position."""
        return (
            int(self.aim_x + self._wobble_x),
            int(self.aim_y + self._wobble_y),
        )

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return

        ex, ey = self.effective_aim()
        in_goal = self._in_goal(self.aim_x, self.aim_y)

        # -- Crosshair --
        r_outer = 22
        r_inner = 4
        cross_len = 10
        alpha = 220 if in_goal else 110
        color = (255, 80, 80) if self.charging else WHITE

        cross_surf = pygame.Surface((r_outer*2+cross_len*2+4,
                                     r_outer*2+cross_len*2+4), pygame.SRCALPHA)
        cx = cy = r_outer + cross_len + 2

        pygame.draw.circle(cross_surf, (*color, alpha), (cx, cy), r_outer, 2)
        pygame.draw.circle(cross_surf, (*color, alpha), (cx, cy), r_inner)
        for dx_, dy_ in [(0,-1),(0,1),(-1,0),(1,0)]:
            pygame.draw.line(cross_surf, (*color, alpha),
                             (cx + dx_*(r_outer+2),  cy + dy_*(r_outer+2)),
                             (cx + dx_*(r_outer+cross_len), cy + dy_*(r_outer+cross_len)), 2)

        surface.blit(cross_surf, (ex - cx, ey - cy))

        # -- Hint text --
        if not self.charging and not in_goal:
            hint = self._hint_font.render("Move mouse over goal to aim", True, (200, 210, 230))
            surface.blit(hint, hint.get_rect(center=(GOAL_CENTER_X, GOAL_TOP_Y + GOAL_HEIGHT + 30)))

        if in_goal and not self.charging:
            hint = self._hint_font.render("Hold SPACE or click to charge · Release to shoot", True, (220, 230, 255))
            surface.blit(hint, hint.get_rect(center=(GOAL_CENTER_X, GOAL_TOP_Y + GOAL_HEIGHT + 30)))

        # -- Power bar --
        if self.charging or self.charge > 0:
            bar_w = 260
            bar_h = 16
            bx = GOAL_CENTER_X - bar_w // 2
            by = GOAL_TOP_Y + GOAL_HEIGHT + 18

            # Background
            pygame.draw.rect(surface, (30, 35, 45), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=8)
            pygame.draw.rect(surface, (50, 58, 72), (bx, by, bar_w, bar_h), border_radius=6)

            # Fill gradient: green → gold → red
            fill_w = int(bar_w * self.charge)
            if fill_w > 0:
                t = self.charge
                if t < 0.5:
                    r2 = int(78 + (232-78)*t*2);  g2 = int(220 + (176-220)*t*2); b2 = int(120 + (32-120)*t*2)
                else:
                    r2 = int(232 + (220-232)*(t-0.5)*2); g2 = int(176 + (60-176)*(t-0.5)*2); b2 = int(32 + (60-32)*(t-0.5)*2)
                pygame.draw.rect(surface, (r2, g2, b2), (bx, by, fill_w, bar_h), border_radius=6)

            pygame.draw.rect(surface, (80, 90, 110), (bx, by, bar_w, bar_h), width=1, border_radius=6)

            label = self._bar_font.render("POWER", True, (180, 190, 210))
            surface.blit(label, label.get_rect(midright=(bx - 8, by + bar_h // 2)))
