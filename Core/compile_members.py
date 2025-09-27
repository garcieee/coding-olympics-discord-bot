"""
Member compilation and caching system for the Discord bot.
Handles member intents, caching, and member management.
"""

import discord
from typing import Dict, Optional, List
from datetime import datetime

class MemberCache:
    """Handles member caching and management for the Discord bot."""
    
    def __init__(self):
        self.members_dict: Dict[int, str] = {}
        self.member_details: Dict[int, dict] = {}
        self.last_updated: Optional[datetime] = None
        
    def add_member(self, member: discord.Member) -> None:
        """Add a member to the cache."""
        self.members_dict[member.id] = member.name
        self.member_details[member.id] = {
            'name': member.name,
            'display_name': member.display_name,
            'discriminator': member.discriminator,
            'nick': member.nick,
            'joined_at': member.joined_at,
            'created_at': member.created_at,
            'roles': [role.name for role in member.roles],
            'is_bot': member.bot,
            'status': str(member.status) if hasattr(member, 'status') else 'unknown'
        }
        
    def remove_member(self, member_id: int) -> None:
        """Remove a member from the cache."""
        self.members_dict.pop(member_id, None)
        self.member_details.pop(member_id, None)
        
    def update_member(self, member: discord.Member) -> None:
        """Update member information in the cache."""
        self.add_member(member)
        
    def get_member_name(self, member_id: int) -> Optional[str]:
        """Get member name by ID."""
        return self.members_dict.get(member_id)
        
    def get_member_details(self, member_id: int) -> Optional[dict]:
        """Get detailed member information by ID."""
        return self.member_details.get(member_id)
        
    def get_all_members(self) -> Dict[int, str]:
        """Get all cached members."""
        return self.members_dict.copy()
        
    def get_member_count(self) -> int:
        """Get total number of cached members."""
        return len(self.members_dict)
        
    def search_members(self, query: str) -> List[dict]:
        """Search members by name (case-insensitive)."""
        results = []
        query_lower = query.lower()
        
        for member_id, details in self.member_details.items():
            if (query_lower in details['name'].lower() or 
                query_lower in details['display_name'].lower() or
                (details['nick'] and query_lower in details['nick'].lower())):
                results.append({
                    'id': member_id,
                    'name': details['name'],
                    'display_name': details['display_name'],
                    'nick': details['nick']
                })
                
        return results
        
    def get_members_by_role(self, role_name: str) -> List[dict]:
        """Get all members with a specific role."""
        results = []
        
        for member_id, details in self.member_details.items():
            if role_name in details['roles']:
                results.append({
                    'id': member_id,
                    'name': details['name'],
                    'display_name': details['display_name'],
                    'nick': details['nick']
                })
                
        return results
        
    def clear_cache(self) -> None:
        """Clear all cached members."""
        self.members_dict.clear()
        self.member_details.clear()
        self.last_updated = None
        
    def update_timestamp(self) -> None:
        """Update the last updated timestamp."""
        self.last_updated = datetime.now()
        
    def get_cache_info(self) -> dict:
        """Get information about the cache."""
        return {
            'member_count': self.get_member_count(),
            'last_updated': self.last_updated,
            'cache_size_mb': len(str(self.member_details)) / (1024 * 1024)  # Rough estimate
        }

# Global member cache instance
member_cache = MemberCache()

def get_member_cache() -> MemberCache:
    """Get the global member cache instance."""
    return member_cache

def setup_member_intents() -> discord.Intents:
    """Set up Discord intents with member access."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True  # Required for accessing member list
    intents.presences = True  # Optional: for member status info
    return intents

async def cache_guild_members(guild: discord.Guild) -> None:
    """Cache all members from a guild."""
    print(f"Caching members from {guild.name}...")
    
    for member in guild.members:
        member_cache.add_member(member)
        
    member_cache.update_timestamp()
    print(f"Cached {member_cache.get_member_count()} members from {guild.name}")

async def cache_all_guilds_members(bot) -> None:
    """Cache members from all guilds the bot is in."""
    print("Starting member cache process...")
    member_cache.clear_cache()
    
    for guild in bot.guilds:
        await cache_guild_members(guild)
        
    print(f"Member caching complete! Total members cached: {member_cache.get_member_count()}")
    print("Cache info:", member_cache.get_cache_info())
