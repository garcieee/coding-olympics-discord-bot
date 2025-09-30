"""
Member compilation and caching system for the Discord bot.
Handles member intents, caching, and member management with JSON persistence.
"""

import discord
import json
import os
from typing import Dict, Optional, List
from datetime import datetime

CACHE_FILE = "cache/members.json"

# hardcoded admin IDs
ADMIN_IDS = {123456789012345678}  # <-- Replace with Joseph's actual Discord ID


class MemberCache:
    """Handles member caching and management for the Discord bot."""

    def __init__(self):
        self.members_dict: Dict[int, str] = {}
        self.member_details: Dict[int, dict] = {}
        self.last_updated: Optional[str] = None

    def add_member(self, member: discord.Member) -> None:
        roles = [role.name for role in member.roles if role.name != "@everyone"]

        # force admin role if member ID matches ADMIN_IDS
        if member.id in ADMIN_IDS and "Admin" not in roles:
            roles.append("Admin")

        self.members_dict[member.id] = member.name
        self.member_details[member.id] = {
            'id': member.id,
            'name': member.name,
            'display_name': member.display_name,
            'discriminator': member.discriminator,
            'nick': member.nick,
            'joined_at': str(member.joined_at) if member.joined_at else None,
            'created_at': str(member.created_at),
            'roles': roles,
            'is_bot': member.bot,
            'status': str(member.status) if hasattr(member, 'status') else 'unknown'
        }

    def remove_member(self, member_id: int) -> None:
        self.members_dict.pop(member_id, None)
        self.member_details.pop(member_id, None)

    def update_member(self, member: discord.Member) -> None:
        self.add_member(member)

    def get_member_name(self, member_id: int) -> Optional[str]:
        return self.members_dict.get(member_id)

    def get_member_details(self, member_id: int) -> Optional[dict]:
        return self.member_details.get(member_id)

    def get_all_members(self) -> Dict[int, str]:
        return self.members_dict.copy()

    def get_member_count(self) -> int:
        return len(self.members_dict)

    def search_members(self, query: str) -> List[dict]:
        results = []
        query_lower = query.lower()
        for details in self.member_details.values():
            if (query_lower in details['name'].lower()
                or query_lower in details['display_name'].lower()
                or (details['nick'] and query_lower in details['nick'].lower())):
                results.append(details)
        return results

    def get_members_by_role(self, role_name: str) -> List[dict]:
        return [
            details for details in self.member_details.values()
            if role_name in details['roles']
        ]

    def clear_cache(self) -> None:
        self.members_dict.clear()
        self.member_details.clear()
        self.last_updated = None

    def update_timestamp(self) -> None:
        self.last_updated = datetime.now().isoformat()

    def get_cache_info(self) -> dict:
        return {
            'member_count': self.get_member_count(),
            'last_updated': self.last_updated,
            'cache_size_mb': len(str(self.member_details)) / (1024 * 1024)
        }

    # ----------------
    # persistence
    # ----------------
    def save_cache_to_file(self):
        os.makedirs("cache", exist_ok=True)
        data = {
            "members_dict": self.members_dict,
            "member_details": self.member_details,
            "last_updated": self.last_updated
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_cache_from_file(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.members_dict = {int(k): v for k, v in data["members_dict"].items()}
                self.member_details = {int(k): v for k, v in data["member_details"].items()}
                self.last_updated = data.get("last_updated")


# Global instance
member_cache = MemberCache()


def get_member_cache() -> MemberCache:
    return member_cache


def setup_member_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    return intents


async def cache_guild_members(guild: discord.Guild) -> None:
    print(f"Caching members from {guild.name}...")
    for member in guild.members:
        member_cache.add_member(member)
    member_cache.update_timestamp()
    member_cache.save_cache_to_file()
    print(f"✅ Cached {member_cache.get_member_count()} members from {guild.name}")


async def cache_all_guilds_members(bot) -> None:
    print("Starting member cache process...")
    member_cache.clear_cache()
    for guild in bot.guilds:
        await cache_guild_members(guild)
    print(f"✅ Member caching complete! Total: {member_cache.get_member_count()}")
    print("Cache info:", member_cache.get_cache_info())


def load_cache_from_file():
    member_cache.load_cache_from_file()


def is_admin(user_id: int) -> bool:
    details = member_cache.get_member_details(user_id)
    if not details:
        return False
    return "Admin" in details.get("roles", [])