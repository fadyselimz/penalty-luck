"""
settings.py
Global constants and configuration values for the Penalty Shootout game.
Centralising these values here keeps every other module easy to tune.
"""

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WIDTH = 1000
HEIGHT = 700
FPS = 60
TITLE = "Penalty Shootout - Pro Edition"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
OFF_WHITE = (235, 238, 240)

DARK_GREEN = (18, 92, 48)
MID_GREEN = (26, 122, 62)
LIGHT_GREEN = (34, 148, 76)
STRIPE_DARK = (22, 108, 56)
STRIPE_LIGHT = (28, 130, 66)

SKY_TOP = (8, 14, 28)
SKY_BOTTOM = (32, 52, 84)

GOLD = (255, 198, 60)
GOLD_DARK = (200, 150, 30)
RED = (214, 64, 64)
RED_DARK = (160, 40, 40)
BLUE = (66, 140, 226)
BLUE_DARK = (40, 95, 170)
GRAY = (150, 156, 164)
DARK_GRAY = (45, 49, 58)
PANEL = (18, 22, 30)

KEEPER_KIT = (250, 180, 30)
KEEPER_KIT_DARK = (200, 140, 10)
SKIN = (235, 190, 150)

# ---------------------------------------------------------------------------
# Field geometry
# ---------------------------------------------------------------------------
FIELD_TOP_Y = 130
FIELD_BOTTOM_Y = HEIGHT - 40

GOAL_CENTER_X = WIDTH // 2
GOAL_WIDTH = 320
GOAL_HEIGHT = 150
GOAL_TOP_Y = FIELD_TOP_Y - 10
GOAL_POST_THICK = 8

PENALTY_SPOT = (WIDTH // 2, FIELD_BOTTOM_Y - 60)
PENALTY_BALL_RADIUS = 16
GOAL_BALL_RADIUS = 7

LEFT_ZONE_X = GOAL_CENTER_X - 105
CENTER_ZONE_X = GOAL_CENTER_X
RIGHT_ZONE_X = GOAL_CENTER_X + 105
ZONES = {"LEFT": LEFT_ZONE_X, "CENTER": CENTER_ZONE_X, "RIGHT": RIGHT_ZONE_X}
ZONE_NAMES = ["LEFT", "CENTER", "RIGHT"]

# ---------------------------------------------------------------------------
# Timings (seconds)
# ---------------------------------------------------------------------------
WINDUP_TIME = 0.35
SHOT_TIME = 0.95

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
MIN_GOAL_POINTS = 50
MAX_GOAL_POINTS = 150

# ---------------------------------------------------------------------------
# Save file
# ---------------------------------------------------------------------------
SAVE_FILE = "data.json"

# ---------------------------------------------------------------------------
# Fonts (tried in this order, falls back to pygame default if none exist)
# ---------------------------------------------------------------------------
FONT_CANDIDATES = ["Verdana", "Arial", "Segoe UI", "Calibri", "Tahoma"]