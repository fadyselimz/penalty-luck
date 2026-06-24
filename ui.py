"""
ui.py
Reusable UI widgets: rounded buttons with hover/press states, a confetti
particle system for goal celebrations, and the scoreboard panel.
"""

import random

import pygame

from assets import get_font, draw_panel, text_with_shadow
from settings import WHITE, GOLD, BLUE, GRAY, DARK_GRAY, RED


class Button:
    def __init__(self, rect, text, base_color=BLUE, hover_color=None,
                 text_color=WHITE, font_size=26, radius=14):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color or self._lighten(base_color, 30)
        self.text_color = text_color
        self.font = get_font(font_size, bold=True)
        self.radius = radius
        self.hovered = False
        self.enabled = True

    @staticmethod
    def _lighten(color, amount):
        return tuple(min(255, c + amount) for c in color)

    @staticmethod
    def _darken(color, amount):
        return tuple(max(0, c - amount) for c in color)

    def update(self, mouse_pos):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.base_color
        if not self.enabled:
            color = DARK_GRAY

        # Soft drop shadow
        shadow = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow, (0, 0, 0, 110), (5, 6, self.rect.width, self.rect.height),
            border_radius=self.radius,
        )
        surface.blit(shadow, (self.rect.x - 5, self.rect.y - 2))

        # Main button body
        pygame.draw.rect(surface, color, self.rect, border_radius=self.radius)

        # Glassy top highlight strip
        try:
            highlight = pygame.Surface((self.rect.width, self.rect.height // 2), pygame.SRCALPHA)
            pygame.draw.rect(
                highlight, (255, 255, 255, 35), highlight.get_rect(),
                border_top_left_radius=self.radius, border_top_right_radius=self.radius,
            )
            surface.blit(highlight, self.rect.topleft)
        except TypeError:
            # Older pygame versions without per-corner radius support.
            pass

        border_color = self._darken(color, 60)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=self.radius)

        text_color = self.text_color if self.enabled else GRAY
        text_with_shadow(surface, self.font, self.text, text_color, self.rect.center, center=True)


class TextInput:
    def __init__(self, rect, placeholder="", max_len=14, font_size=22):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.max_len = max_len
        self.active = False
        self.font = get_font(font_size)
        self.radius = 10

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return self.active
        if not self.active or event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return True
        if event.key in (pygame.K_RETURN, pygame.K_TAB):
            self.active = False
            return True
        ch = event.unicode
        if ch and ch.isprintable() and len(self.text) < self.max_len:
            self.text += ch
            return True
        return False

    def draw(self, surface):
        bg = (28, 36, 52) if self.active else (20, 26, 38)
        border = GOLD if self.active else (70, 80, 100)
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.radius)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=self.radius)

        shown = self.text if self.text else self.placeholder
        color = WHITE if self.text else GRAY
        surf = self.font.render(shown, True, color)
        clip = self.rect.inflate(-16, -8)
        surface.set_clip(clip)
        surface.blit(surf, (self.rect.x + 12, self.rect.centery - surf.get_height() // 2))
        surface.set_clip(None)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "size", "color", "life", "max_life", "shape")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-160, 160)
        self.vy = random.uniform(-260, -80)
        self.size = random.randint(4, 8)
        self.color = random.choice([GOLD, BLUE, RED, WHITE, (90, 220, 120)])
        self.max_life = random.uniform(0.9, 1.6)
        self.life = self.max_life
        self.shape = random.choice(["rect", "circle"])

    def update(self, dt):
        self.vy += 420 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color = (*self.color, alpha)
        if self.shape == "rect":
            pygame.draw.rect(s, color, (0, 0, self.size * 2, self.size * 2), border_radius=2)
        else:
            pygame.draw.circle(s, color, (self.size, self.size), self.size)
        surface.blit(s, (self.x, self.y))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, count=70):
        self.particles.extend(Particle(x, y) for _ in range(count))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()


def draw_scoreboard(surface, rect, stats, title="CAREER STATS"):
    """Draw a translucent stats panel showing total score, games and goals."""
    draw_panel(surface, rect, radius=16)

    title_font = get_font(18, bold=True)
    label_font = get_font(15)
    value_font = get_font(26, bold=True)

    text_with_shadow(surface, title_font, title, GOLD, (rect.x + 18, rect.y + 14))

    games = stats.get("games_played", 0)
    goals = stats.get("goals_scored", 0)
    accuracy = f"{(goals / games * 100):.0f}%" if games > 0 else "0%"

    entries = [
        ("TOTAL SCORE", str(stats.get("total_score", 0))),
        ("GAMES PLAYED", str(games)),
        ("GOALS SCORED", str(goals)),
        ("ACCURACY", accuracy),
    ]

    col_w = rect.width // 2
    start_y = rect.y + 46
    for i, (label, value) in enumerate(entries):
        col = i % 2
        row = i // 2
        x = rect.x + 18 + col * col_w
        y = start_y + row * 56
        surface.blit(label_font.render(label, True, GRAY), (x, y))
        text_with_shadow(surface, value_font, value, WHITE, (x, y + 18))