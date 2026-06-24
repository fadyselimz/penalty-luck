"""
aiming.py
Crosshair aiming over the perspective goal mouth.
"""

import math
import pygame
from settings import WHITE, GOLD, RED, WIDTH
from assets import get_font


class AimingSystem:
    MAX_CHARGE_TIME = 1.4
    WOBBLE_AMOUNT   = 14

    def __init__(self, scene):
        self.scene = scene
        self.active     = False
        self.charging   = False
        self.charge     = 0.0
        cx, cy = scene.goal_to_screen(0.5, 0.5)
        self.aim_x      = cx
        self.aim_y      = cy
        self._wobble_x  = 0.0
        self._wobble_y  = 0.0
        self._wobble_t  = 0.0
        self._hint_font = get_font(16)
        self._bar_font  = get_font(14, bold=True)

    def start(self):
        self.active   = True
        self.charging = False
        self.charge   = 0.0
        cx, cy = self.scene.goal_to_screen(0.5, 0.5)
        self.aim_x, self.aim_y = cx, cy

    def stop(self):
        self.active   = False
        self.charging = False
        self.charge   = 0.0

    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.aim_x = event.pos[0]
            self.aim_y = event.pos[1]

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            trigger = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                      (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
            # Allow charging (and shooting) anywhere; shots outside the goal will be treated as misses.
            if trigger:
                self.charging = True

        if event.type in (pygame.MOUSEBUTTONUP, pygame.KEYUP):
            release = (event.type == pygame.MOUSEBUTTONUP and event.button == 1) or \
                      (event.type == pygame.KEYUP and event.key == pygame.K_SPACE)
            if release and self.charging and self.charge > 0.08:
                self.charging = False
                return True

        return False

    def _in_goal(self, x, y):
        return self.scene.point_in_goal(x, y)

    def update(self, dt):
        if not self.active:
            return
        self._wobble_t += dt * 4.5
        wobble_scale = self.WOBBLE_AMOUNT * (1.0 - self.charge * 0.6)
        self._wobble_x = math.sin(self._wobble_t * 1.3) * wobble_scale
        self._wobble_y = math.cos(self._wobble_t * 1.7) * wobble_scale * 0.6
        if self.charging:
            self.charge = min(1.0, self.charge + dt / self.MAX_CHARGE_TIME)

    def effective_aim(self):
        return (
            int(self.aim_x + self._wobble_x),
            int(self.aim_y + self._wobble_y),
        )

    def draw(self, surface):
        if not self.active:
            return

        ex, ey = self.effective_aim()
        in_goal = self._in_goal(self.aim_x, self.aim_y)
        color = (255, 90, 90) if self.charging else (255, 255, 255)
        alpha = 230 if in_goal else 100

        cross_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        cx, cy = 30, 30
        pygame.draw.circle(cross_surf, (*color, alpha), (cx, cy), 16, 2)
        pygame.draw.circle(cross_surf, (*color, alpha), (cx, cy), 3)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            pygame.draw.line(cross_surf, (*color, alpha),
                             (cx + dx * 18, cy + dy * 18),
                             (cx + dx * 28, cy + dy * 28), 2)
        surface.blit(cross_surf, (ex - 30, ey - 30))

        if self.charging or self.charge > 0:
            bar_w, bar_h = 220, 12
            bx = WIDTH // 2 - bar_w // 2
            by = self.scene.grass_floor_y - 36
            pygame.draw.rect(surface, (20, 28, 38, 180), (bx - 3, by - 3, bar_w + 6, bar_h + 6), border_radius=8)
            pygame.draw.rect(surface, (40, 48, 58), (bx, by, bar_w, bar_h), border_radius=6)
            fill_w = int(bar_w * self.charge)
            if fill_w > 0:
                t = self.charge
                if t < 0.5:
                    fc = (int(78 + (232 - 78) * t * 2), int(220 + (176 - 220) * t * 2), int(120 + (32 - 120) * t * 2))
                else:
                    fc = (int(232 + (220 - 232) * (t - 0.5) * 2), int(176 + (60 - 176) * (t - 0.5) * 2), int(32 + (60 - 32) * (t - 0.5) * 2))
                pygame.draw.rect(surface, fc, (bx, by, fill_w, bar_h), border_radius=6)
            label = self._bar_font.render("POWER", True, (200, 210, 225))
            surface.blit(label, label.get_rect(midright=(bx - 6, by + bar_h // 2)))
