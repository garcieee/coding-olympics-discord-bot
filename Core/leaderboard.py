"""
Leaderboard system for the Discord bot.
Tracks wins, ranks, and persists data in JSON.
"""

import json
import os
from typing import Dict, Optional, List

LEADERBOARD_FILE = "cache/leaderboard.json"


class Leaderboard:
    def __init__(self):
        self.scores: Dict[int, dict] = {}  # {user_id: {"display_name": str, "wins": int}}
        self.load_from_file()

    # ----------------
    # core operations
    # ----------------
    def ensure_member(self, user_id: int, display_name: str) -> None:
        """Make sure a member exists in the leaderboard with 0 wins."""
        if user_id not in self.scores:
            self.scores[user_id] = {"display_name": display_name, "wins": 0}
            self.save_to_file()

    def add_win(self, user_id: int, display_name: str) -> None:
        """Increase a user’s wins by 1 (or create if missing)."""
        self.ensure_member(user_id, display_name)
        self.scores[user_id]["wins"] += 1
        self.save_to_file()

    def set_wins(self, user_id: int, display_name: str, wins: int) -> None:
        """Set exact wins for a user."""
        self.ensure_member(user_id, display_name)
        self.scores[user_id]["wins"] = wins
        self.save_to_file()

    def get_member_stats(self, user_id: int) -> Optional[dict]:
        """Return stats for a member."""
        return self.scores.get(user_id)

    def get_leaderboard(self, top_n: int = 10) -> List[dict]:
        """Return the top N members sorted by wins."""
        return sorted(
            self.scores.values(),
            key=lambda x: x["wins"],
            reverse=True
        )[:top_n]

    def get_rank(self, user_id: int) -> Optional[int]:
        """Return the rank of a user (1 = highest wins)."""
        sorted_scores = sorted(
            self.scores.items(),
            key=lambda x: x[1]["wins"],
            reverse=True
        )
        for idx, (uid, _) in enumerate(sorted_scores, start=1):
            if uid == user_id:
                return idx
        return None

    # ----------------
    # persistence
    # ----------------
    def save_to_file(self):
        os.makedirs("cache", exist_ok=True)
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(self.scores, f, indent=4, ensure_ascii=False)

    def load_from_file(self):
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert keys back to int
                self.scores = {int(k): v for k, v in data.items()}


# Global leaderboard instance
leaderboard = Leaderboard()


# ----------------
# helper functions
# ----------------
def ensure_member(user_id: int, display_name: str):
    leaderboard.ensure_member(user_id, display_name)


def add_win(user_id: int, display_name: str):
    leaderboard.add_win(user_id, display_name)


def set_wins(user_id: int, display_name: str, wins: int):
    leaderboard.set_wins(user_id, display_name, wins)


def get_member_stats(user_id: int) -> Optional[dict]:
    return leaderboard.get_member_stats(user_id)


def get_leaderboard(top_n: int = 10) -> List[dict]:
    return leaderboard.get_leaderboard(top_n)


def get_rank(user_id: int) -> Optional[int]:
    return leaderboard.get_rank(user_id)