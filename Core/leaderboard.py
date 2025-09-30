"""
Leaderboard system for the Discord bot.
Tracks wins, ranks, and persists data in JSON.
Also can cache all human members from the server automatically.
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime
import discord

LEADERBOARD_FILE = "cache/leaderboard.json"


class Leaderboard:
    def __init__(self):
        self.scores: Dict[int, dict] = {}  # {user_id: {"display_name": str, "wins": int}}
        self.last_updated: Optional[str] = None
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
        """Increase a user's wins by 1 (or create if missing)."""
        self.ensure_member(user_id, display_name)
        self.scores[user_id]["wins"] += 1
        self.save_to_file()

    def subtract_win(self, user_id: int, display_name: str) -> None:
        """Decrease a user's wins by 1, but not below 0."""
        self.ensure_member(user_id, display_name)
        if self.scores[user_id]["wins"] > 0:
            self.scores[user_id]["wins"] -= 1
            self.save_to_file()

    def set_wins(self, user_id: int, display_name: str, wins: int) -> None:
        """Set exact wins for a user."""
        self.ensure_member(user_id, display_name)
        self.scores[user_id]["wins"] = max(0, wins)
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
    # caching all guild members
    # ----------------
    async def cache_guild_members(self, guild: discord.Guild) -> None:
        """Add all human members in a guild to the leaderboard."""
        count = 0
        for member in guild.members:
            if not member.bot:
                self.ensure_member(member.id, member.display_name)
                count += 1
        self.last_updated = datetime.now().isoformat()
        self.save_to_file()
        print(f"✅ Cached {count} members from {guild.name}")

    async def cache_all_guilds(self, bot) -> None:
        """Add all human members from all guilds to the leaderboard."""
        print("Starting leaderboard cache process...")
        self.scores.clear()
        for guild in bot.guilds:
            await self.cache_guild_members(guild)
        print(f"✅ Leaderboard caching complete! Total members: {len(self.scores)}")
        print("Last updated:", self.last_updated)

    # ----------------
    # persistence
    # ----------------
    def save_to_file(self):
        os.makedirs("cache", exist_ok=True)
        data = {
            "scores": self.scores,
            "last_updated": self.last_updated
        }
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_from_file(self):
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert keys back to int if stored as strings
                raw_scores = data.get("scores", {})
                self.scores = {int(k): v for k, v in raw_scores.items()}
                self.last_updated = data.get("last_updated")


# ----------------
# global instance
# ----------------
leaderboard = Leaderboard()