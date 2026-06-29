"""
settings.py
Global constants and configuration values for Penalty Luck.
"""

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WIDTH  = 1000
HEIGHT = 700
FPS    = 60
TITLE  = "Penalty Luck"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
WHITE       = (255, 255, 255)
BLACK       = (10,  10,  10)
OFF_WHITE   = (235, 238, 240)

DARK_GREEN  = (18,  92,  48)
MID_GREEN   = (26, 122,  62)
STRIPE_DARK = (20, 100,  44)
STRIPE_LIGHT= (24, 118,  54)

# Realistic daytime sky
SKY_TOP     = (82, 130, 190)
SKY_BOTTOM  = (148, 190, 230)

GOLD        = (232, 176,  32)
GOLD_DARK   = (180, 130,  20)
RED         = (220,  60,  60)
GREEN_GOAL  = ( 78, 220, 120)
BLUE        = ( 66, 140, 226)
GRAY        = (140, 150, 164)
DARK_GRAY   = ( 40,  44,  54)
PANEL       = ( 14,  18,  28)

# Keeper – bright lime green for visibility
KEEPER_KIT      = ( 80, 200,  80)
KEEPER_KIT_DARK = ( 50, 150,  50)
SKIN            = (210, 162, 108)

# Box colors
BOX_BROWN       = (139,  99,  64)
BOX_BROWN_LIGHT = (168, 128,  88)

# ---------------------------------------------------------------------------
# Field geometry
# ---------------------------------------------------------------------------
FIELD_TOP_Y    = 140
FIELD_BOTTOM_Y = HEIGHT - 30

GOAL_CENTER_X  = WIDTH  // 2
GOAL_WIDTH     = 380
GOAL_HEIGHT    = 185
GOAL_TOP_Y     = FIELD_TOP_Y - 20
GOAL_POST_THICK= 9

PENALTY_SPOT        = (WIDTH // 2, FIELD_BOTTOM_Y - 50)
PENALTY_BALL_RADIUS = 15
GOAL_BALL_RADIUS    = 6

# Mystery box grid inside goal
BOX_COLS = 11
BOX_ROWS =  8
BOX_PAD  =  2

# Aim zones
LEFT_ZONE_X   = GOAL_CENTER_X - 120
CENTER_ZONE_X = GOAL_CENTER_X
RIGHT_ZONE_X  = GOAL_CENTER_X + 120
ZONES      = {"LEFT": LEFT_ZONE_X, "CENTER": CENTER_ZONE_X, "RIGHT": RIGHT_ZONE_X}
ZONE_NAMES = ["LEFT", "CENTER", "RIGHT"]

# ---------------------------------------------------------------------------
# Timings (seconds)
# ---------------------------------------------------------------------------
WINDUP_TIME = 0.30
SHOT_TIME   = 0.75

# ---------------------------------------------------------------------------
# Box point values 10-100 (value: relative_weight)
# 10 is common, 100 is rare
# ---------------------------------------------------------------------------
BOX_VALUE_TABLE = [
    (10,  20),
    (20,  18),
    (30,  17),
    (40,  16),
    (50,  15),
    (60,  14),
    (70,  13),
    (80,  12),
    (90,  11),
    (100, 10),
]

# ---------------------------------------------------------------------------
# Save file
# ---------------------------------------------------------------------------
SAVE_FILE = "data.json"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_CANDIDATES = ["Verdana", "Arial", "Segoe UI", "Calibri", "Tahoma"]