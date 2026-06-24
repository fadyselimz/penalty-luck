"""
teams.py
Turn-based team match: setup, rotation, and scoring.
Play continues until the user ends the game.
"""

from settings import GOLD

MIN_TEAMS = 2
MAX_TEAMS = 6

TEAM_COLORS = [
    (66, 140, 226),
    (220, 60, 60),
    (78, 220, 120),
    GOLD,
    (180, 80, 180),
    (200, 120, 40),
]


class TeamMatch:
    def __init__(self):
        self.reset()

    def reset(self):
        self.names: list[str] = []
        self.scores: list[int] = []
        self.goals: list[int] = []
        self.shots_taken: list[int] = []
        self.current = 0
        self.active = False
        self.finished = False
        self.double_chips: list[int] = []
        self.offside_chips: list[int] = []

    def configure(self, names: list[str]):
        self.names = [
            (n.strip() or f"Team {i + 1}")[:14]
            for i, n in enumerate(names)
        ]
        n = len(self.names)
        self.scores = [0] * n
        self.goals = [0] * n
        self.shots_taken = [0] * n
        self.current = 0
        self.active = True
        self.finished = False
        # Give each team 2 double chips and 1 offside chip by default
        self.double_chips = [2] * n
        self.offside_chips = [1] * n

    @property
    def team_count(self) -> int:
        return len(self.names)

    def color_for(self, index: int):
        return TEAM_COLORS[index % len(TEAM_COLORS)]

    def current_name(self) -> str:
        return self.names[self.current]

    def current_color(self):
        return self.color_for(self.current)

    def shot_label(self, index: int | None = None) -> str:
        i = self.current if index is None else index
        return f"Penalty #{self.shots_taken[i] + 1}"

    def record_shot(self, is_goal: bool, points: int):
        i = self.current
        if is_goal:
            self.scores[i] += points
            self.goals[i] += 1
        self.shots_taken[i] += 1

    def advance_turn(self):
        if self.finished:
            return
        self.current = (self.current + 1) % self.team_count

    def end_match(self):
        self.finished = True

    def is_over(self) -> bool:
        return self.finished

    def winners(self) -> list[int]:
        if not self.finished:
            return []
        best_score = max(self.scores)
        return [i for i, s in enumerate(self.scores) if s == best_score]
