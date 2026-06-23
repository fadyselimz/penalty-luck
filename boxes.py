"""
boxes.py
Mystery-box grid that fills the goal mouth.
Each box hides a random point value revealed only when the ball hits it.
"""

import random
import pygame

from settings import (
    GOAL_CENTER_X, GOAL_TOP_Y, GOAL_WIDTH, GOAL_HEIGHT,
    BOX_COLS, BOX_ROWS, BOX_PAD, BOX_VALUE_TABLE,
    BOX_BROWN, BOX_BROWN_LIGHT, WHITE, GOLD,
)
from assets import get_font


def _weighted_value():
    pool, weights = zip(*BOX_VALUE_TABLE)
    return random.choices(pool, weights=weights, k=1)[0]


# Colour per tier
_TIER_COLOR = {
    500: (232, 176,  32),   # gold
    200: ( 78, 220, 120),   # green
    100: ( 66, 140, 226),   # blue
     50: (140, 100, 220),   # purple
     25: (200, 100,  60),   # orange
     10: (120, 130, 145),   # grey
}


class BoxGrid:
    def __init__(self):
        self.cols = BOX_COLS
        self.rows = BOX_ROWS
        self._values: list[int]   = [_weighted_value() for _ in range(self.cols * self.rows)]
        self._revealed: list[bool] = [False] * (self.cols * self.rows)
        self._hit_index: int       = -1

        bw, bh = self._box_size()
        self._font_q  = get_font(max(9, int(bh * 0.52)), bold=True)
        self._font_val= get_font(max(8, int(bh * 0.40)), bold=True)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def _box_size(self):
        bw = (GOAL_WIDTH  - BOX_PAD * (self.cols - 1)) / self.cols
        bh = (GOAL_HEIGHT - BOX_PAD * (self.rows - 1)) / self.rows
        return bw, bh

    def _box_rect(self, col, row):
        bw, bh = self._box_size()
        left = GOAL_CENTER_X - GOAL_WIDTH // 2
        x = left + col * (bw + BOX_PAD)
        y = GOAL_TOP_Y + row * (bh + BOX_PAD)
        return pygame.Rect(int(x), int(y), int(bw), int(bh))

    def index_at(self, pixel_x: int, pixel_y: int) -> int:
        """Return grid index for a pixel coordinate, or -1 if outside grid."""
        bw, bh = self._box_size()
        left = GOAL_CENTER_X - GOAL_WIDTH // 2
        col = int((pixel_x - left) / (bw + BOX_PAD))
        row = int((pixel_y - GOAL_TOP_Y) / (bh + BOX_PAD))
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return row * self.cols + col
        return -1

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def reveal(self, index: int):
        if 0 <= index < len(self._revealed):
            self._revealed[index] = True
            self._hit_index = index

    def value_at(self, index: int) -> int:
        if 0 <= index < len(self._values):
            return self._values[index]
        return 0

    def reset_hit(self):
        self._hit_index = -1

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        bw, bh = self._box_size()
        for row in range(self.rows):
            for col in range(self.cols):
                idx   = row * self.cols + col
                rect  = self._box_rect(col, row)
                rev   = self._revealed[idx]
                is_hit = idx == self._hit_index

                if rev:
                    self._draw_revealed(surface, rect, idx, is_hit)
                else:
                    self._draw_mystery(surface, rect)

    def _draw_mystery(self, surface, rect):
        # shadow
        shadow = pygame.Surface((rect.w + 3, rect.h + 3), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), (2, 2, rect.w, rect.h), border_radius=2)
        surface.blit(shadow, (rect.x - 1, rect.y - 1))

        # body
        pygame.draw.rect(surface, BOX_BROWN, rect, border_radius=2)
        # top highlight strip
        hi_rect = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, int(rect.h * 0.35))
        pygame.draw.rect(surface, BOX_BROWN_LIGHT, hi_rect, border_radius=2)
        # border
        pygame.draw.rect(surface, (80, 55, 30), rect, width=1, border_radius=2)

        # "?" text
        surf = self._font_q.render("?", True, (255, 255, 255, 180))
        surface.blit(surf, surf.get_rect(center=rect.center))

    def _draw_revealed(self, surface, rect, idx, is_hit):
        val   = self._values[idx]
        color = _TIER_COLOR.get(val, (100, 110, 125))
        if is_hit:
            bg = color
        else:
            bg = tuple(max(0, c - 80) for c in color)

        pygame.draw.rect(surface, bg, rect, border_radius=2)
        border = color if is_hit else tuple(min(255, c + 40) for c in bg)
        pygame.draw.rect(surface, border, rect, width=1 if not is_hit else 2, border_radius=2)

        text_color = WHITE if not is_hit else (20, 20, 20)
        surf = self._font_val.render(str(val), True, text_color)
        surface.blit(surf, surf.get_rect(center=rect.center))
