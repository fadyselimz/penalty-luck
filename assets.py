"""
assets.py
Procedurally generated sound effects and reusable drawing helpers.

No external image or audio files are used anywhere in this project -
every sound is synthesised at runtime with simple waveform math, and every
visual is drawn with pygame primitives (rects, circles, lines, gradients).
"""

import math
import random
from array import array

import pygame

from settings import FONT_CANDIDATES

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_font_cache = {}


def get_font(size, bold=False):
    """Return a cached SysFont, trying a list of nice-looking fonts first."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]

    font = None
    for name in FONT_CANDIDATES:
        try:
            candidate = pygame.font.SysFont(name, size, bold=bold)
            if candidate is not None:
                font = candidate
                break
        except Exception:
            continue

    if font is None:
        font = pygame.font.Font(None, size)

    _font_cache[key] = font
    return font


# ---------------------------------------------------------------------------
# Sound generation (pure pygame + python stdlib, no numpy required)
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100


def _envelope(samples, attack=0.05, release=0.25):
    """Apply a simple linear fade in/out to avoid harsh clicking sounds."""
    n = len(samples)
    if n == 0:
        return samples
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    for i in range(min(a, n)):
        samples[i] = int(samples[i] * (i / a))
    for i in range(min(r, n)):
        idx = n - 1 - i
        samples[idx] = int(samples[idx] * (i / r))
    return samples


def _tone(freq, duration, volume=0.5, kind="sine", sample_rate=SAMPLE_RATE):
    """Generate a short tone as an array of signed 16-bit samples."""
    n = max(1, int(sample_rate * duration))
    buf = array("h", [0] * n)
    amp = int(32767 * volume)
    for i in range(n):
        t = i / sample_rate
        if kind == "sine":
            value = math.sin(2 * math.pi * freq * t)
        elif kind == "square":
            value = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif kind == "noise":
            value = random.uniform(-1, 1)
        else:
            value = math.sin(2 * math.pi * freq * t)
        buf[i] = int(amp * value)
    return _envelope(buf)


def _concat(*chunks):
    out = array("h")
    for chunk in chunks:
        out.extend(chunk)
    return out


def _silence(duration, sample_rate=SAMPLE_RATE):
    return array("h", [0] * int(sample_rate * duration))


def _make_sound(samples):
    return pygame.mixer.Sound(buffer=samples.tobytes())


class SoundManager:
    """Generates and plays simple placeholder sound effects on the fly."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self._build_sounds()
            self.enabled = True
        except Exception:
            # No audio device available (e.g. some servers/CI) - fail silently.
            self.enabled = False

    def _build_sounds(self):
        kick = _tone(180, 0.10, 0.6, "square")
        self.sounds["kick"] = _make_sound(kick)

        save_thud = _concat(
            _tone(95, 0.18, 0.7, "sine"),
            _tone(70, 0.14, 0.5, "sine"),
        )
        self.sounds["save"] = _make_sound(save_thud)

        goal_notes = [523, 659, 784, 1046]
        chunks = []
        for note in goal_notes:
            chunks.append(_tone(note, 0.12, 0.5, "sine"))
            chunks.append(_silence(0.02))
        self.sounds["goal"] = _make_sound(_concat(*chunks))

        click = _tone(720, 0.05, 0.3, "square")
        self.sounds["click"] = _make_sound(click)

    def play(self, name):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Drawing helpers (gradients, shadows, rounded panels, glow effects)
# ---------------------------------------------------------------------------

def vertical_gradient(width, height, top_color, bottom_color):
    """Return a Surface filled with a smooth vertical gradient."""
    height = max(1, height)
    surf = pygame.Surface((width, height)).convert()
    for y in range(height):
        ratio = y / max(1, height - 1)
        r = top_color[0] + (bottom_color[0] - top_color[0]) * ratio
        g = top_color[1] + (bottom_color[1] - top_color[1]) * ratio
        b = top_color[2] + (bottom_color[2] - top_color[2]) * ratio
        pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (width, y))
    return surf


def striped_field(width, height, color_dark, color_light, stripe_count=10):
    """Return a Surface with horizontal mowing stripes for a football pitch."""
    height = max(1, height)
    surf = pygame.Surface((width, height)).convert()
    stripe_h = max(1, height // stripe_count)
    i = 0
    y = 0
    while y < height:
        color = color_light if i % 2 == 0 else color_dark
        pygame.draw.rect(surf, color, (0, y, width, stripe_h))
        y += stripe_h
        i += 1
    return surf


def draw_panel(surface, rect, color=(18, 22, 30), alpha=190, radius=18,
                border_color=None, border_width=2):
    """Draw a rounded, translucent UI panel with a soft drop shadow."""
    shadow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
    pygame.draw.rect(
        shadow, (0, 0, 0, 90), (8, 10, rect.width, rect.height), border_radius=radius
    )
    surface.blit(shadow, (rect.x - 8, rect.y - 6))

    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, alpha), (0, 0, rect.width, rect.height), border_radius=radius)
    if border_color:
        pygame.draw.rect(
            panel, border_color, (0, 0, rect.width, rect.height),
            width=border_width, border_radius=radius
        )
    surface.blit(panel, rect.topleft)


def draw_glow_circle(surface, center, radius, color, layers=18, max_alpha=70):
    """Draw a soft ambient glow that fades smoothly from the center outward."""
    size = max(2, radius * 2)
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    for i in range(layers, 0, -1):
        t = i / layers
        r = max(1, int(radius * t))
        alpha = int(max_alpha * (1 - t) ** 2)
        if alpha <= 0:
            continue
        pygame.draw.circle(glow, (*color, alpha), (cx, cy), r)
    surface.blit(glow, (center[0] - size // 2, center[1] - size // 2))


def text_with_shadow(surface, font, text, color, pos, center=False,
                      shadow_color=(0, 0, 0), shadow_offset=(2, 2)):
    """Render text with a subtle drop shadow for readability and style."""
    shadow_surf = font.render(text, True, shadow_color)
    main_surf = font.render(text, True, color)
    if center:
        rect = main_surf.get_rect(center=pos)
    else:
        rect = main_surf.get_rect(topleft=pos)
    shadow_rect = rect.copy()
    shadow_rect.x += shadow_offset[0]
    shadow_rect.y += shadow_offset[1]
    surface.blit(shadow_surf, shadow_rect)
    surface.blit(main_surf, rect)
    return rect