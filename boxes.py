"""
boxes.py
Mystery-box grid – values are 10 to 200.
"""

import random
import pygame

from settings import (
    GOAL_CENTER_X, GOAL_TOP_Y, GOAL_WIDTH, GOAL_HEIGHT,
    BOX_COLS, BOX_ROWS, BOX_PAD, BOX_VALUE_TABLE,
    BOX_BROWN, BOX_BROWN_LIGHT, WHITE,
)
from assets import get_font


def _weighted_value():
    pool, weights = zip(*BOX_VALUE_TABLE)
    return random.choices(pool, weights=weights, k=1)[0]


def _tier_color(value: int):
    if value >= 180:
        return (232, 176,  32)   # gold
    if value >= 150:
        return (140, 100, 220)   # purple
    if value >= 120:
        return (200, 100,  50)   # orange
    if value >= 90:
        return ( 60, 160,  80)   # green
    if value >= 60:
        return ( 66, 130, 210)   # blue
    if value >= 30:
        return (110, 120, 135)   # grey
    return ( 80,  88, 100)       # dark


class BoxGrid:
    def __init__(self):
        self.cols = BOX_COLS
        self.rows = BOX_ROWS
        self._values:   list[int]  = [_weighted_value() for _ in range(self.cols * self.rows)]
        self._revealed: list[bool] = [False] * (self.cols * self.rows)
        self._hit_index: int       = -1
        n = len(self._values)
        self._falling = [False] * n
        self._fall_offsets = [0.0] * n
        self._fall_vy = [0.0] * n
        self._fall_target = [None] * n

        bw, bh = self._box_size()
        self._font_q   = get_font(max(9, int(bh * 0.54)), bold=True)
        self._font_val = get_font(max(9, int(bh * 0.56)), bold=True)

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
        bw, bh = self._box_size()
        left = GOAL_CENTER_X - GOAL_WIDTH // 2
        col = int((pixel_x - left) / (bw + BOX_PAD))
        row = int((pixel_y - GOAL_TOP_Y) / (bh + BOX_PAD))
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return row * self.cols + col
        return -1

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

    def start_fall(self, index: int, target_floor_y: int):
        """Begin falling animation for a revealed box toward target floor y (bottom coordinate).
        `target_floor_y` is the desired pixel y for the bottom of the box when it lands.
        """
        n = len(self._values)
        if not (0 <= index < n):
            return
        self._revealed[index] = True
        self._hit_index = index
        self._falling[index] = True
        self._fall_offsets[index] = 0.0
        self._fall_vy[index] = 0.0
        self._fall_target[index] = target_floor_y

    def shuffle_and_hide(self):
        """New random values and hide every box for the next shot."""
        n = len(self._values)
        self._values = [_weighted_value() for _ in range(n)]
        self._revealed = [False] * n
        self._hit_index = -1
        self._falling = [False] * n
        self._fall_offsets = [0.0] * n
        self._fall_vy = [0.0] * n
        self._fall_target = [None] * n

    def reveal_all(self):
        n = len(self._values)
        self._revealed = [True] * n

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        for row in range(self.rows):
            for col in range(self.cols):
                idx    = row * self.cols + col
                rect   = self._box_rect(col, row)
                is_hit = (idx == self._hit_index)
                if self._revealed[idx]:
                    # apply vertical offset if falling
                    yo = int(self._fall_offsets[idx]) if self._falling[idx] or self._fall_offsets[idx] != 0 else 0
                    if yo != 0:
                        rect_draw = rect.move(0, yo)
                    else:
                        rect_draw = rect
                    self._draw_revealed(surface, rect_draw, idx, is_hit)
                else:
                    self._draw_mystery(surface, rect)

    def update(self, dt: float):
        """Update any falling boxes (simple gravity simulation)."""
        n = len(self._values)
        gravity = 1600.0
        for idx in range(n):
            if not self._falling[idx]:
                continue
            # integrate velocity/position
            self._fall_vy[idx] += gravity * dt
            self._fall_offsets[idx] += self._fall_vy[idx] * dt
            # compute current bottom y
            col = idx % self.cols
            row = idx // self.cols
            rect = self._box_rect(col, row)
            current_bottom = rect.bottom + self._fall_offsets[idx]
            target_bottom = self._fall_target[idx] or (rect.bottom + 9999)
            if current_bottom >= target_bottom:
                # land
                self._fall_offsets[idx] = target_bottom - rect.bottom
                self._falling[idx] = False

    def any_falling(self) -> bool:
        return any(self._falling)

    def _draw_mystery(self, surface, rect):
        # drop shadow
        sh = pygame.Surface((rect.w + 3, rect.h + 3), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 90), (2, 2, rect.w, rect.h), border_radius=2)
        surface.blit(sh, (rect.x - 1, rect.y - 1))

        # cardboard body
        pygame.draw.rect(surface, BOX_BROWN, rect, border_radius=2)
        # top highlight
        hi = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, int(rect.h * 0.32))
        pygame.draw.rect(surface, BOX_BROWN_LIGHT, hi, border_radius=2)
        # subtle crease lines for realism
        mid_x = rect.x + rect.w // 2
        pygame.draw.line(surface, (100, 68, 40), (mid_x, rect.y + 2), (mid_x, rect.bottom - 2), 1)
        # border
        pygame.draw.rect(surface, (88, 60, 34), rect, width=1, border_radius=2)

        # "?" white text
        s = self._font_q.render("?", True, (255, 255, 255))
        surface.blit(s, s.get_rect(center=rect.center))

    def _draw_revealed(self, surface, rect, idx, is_hit):
        val   = self._values[idx]
        color = _tier_color(val)
        bg    = color if is_hit else tuple(max(0, c - 90) for c in color)

        pygame.draw.rect(surface, bg, rect, border_radius=2)
        border = color if is_hit else tuple(min(255, c + 30) for c in bg)
        pygame.draw.rect(surface, border, rect, width=2 if is_hit else 1, border_radius=2)

        tc = (15, 15, 15) if is_hit else WHITE
        s  = self._font_val.render(str(val), True, tc)
        surface.blit(s, s.get_rect(center=rect.center))