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
    "match_active": False,
    "match_finished": False,
    "team_names": [],
    "team_scores": [],
    "team_goals": [],
    "team_shots_taken": [],
    "team_double_chips": [],
    "team_offside_chips": [],
    "team_current": 0,
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
        for key, default_value in DEFAULT_DATA.items():
            value = data.get(key, default_value)
            if isinstance(default_value, int):
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    value = default_value
            elif isinstance(default_value, list):
                if not isinstance(value, list):
                    value = default_value
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