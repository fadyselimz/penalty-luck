"""
save.py
Handles loading and saving persistent player statistics to data.json.

Stored stats:
- total_score   : cumulative score earned across all goals ever scored
- games_played  : total number of penalties taken
- goals_scored  : total number of successful goals
"""

import json
import os

from settings import SAVE_FILE

DEFAULT_DATA = {
    "total_score": 0,
    "games_played": 0,
    "goals_scored": 0,
}


def load_data():
    """Load saved stats from disk, returning sane defaults if missing/corrupt."""
    if not os.path.exists(SAVE_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        merged = DEFAULT_DATA.copy()
        for key in DEFAULT_DATA:
            value = data.get(key, DEFAULT_DATA[key])
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                value = DEFAULT_DATA[key]
            merged[key] = value
        return merged
    except (json.JSONDecodeError, OSError, ValueError, AttributeError):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()


def save_data(data):
    """Persist stats to disk as JSON. Fails silently if disk is unavailable."""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except OSError:
        pass