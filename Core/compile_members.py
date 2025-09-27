"""
Simple member caching system - stores only member names and roles.
"""

import discord
from typing import Dict, List

class MemberCache:
    """Simple member cache storing only names and roles."""
    
    def __init__(self):
        self.members: Dict[int, dict] = {}  # {member_id: {'name': str, 'roles': [str]}}
        
    def add_member(self, member: discord.Member) -> None:
        """Add a member to the cache."""
        self.members[member.id] = {
            'name': member.name,
            'roles': [role.name for role in member.roles]
        }
        
    def get_member_name(self, member_id: int) -> str:
        """Get member name by ID."""
        return self.members.get(member_id, {}).get('name', 'Unknown')
        
    def get_member_roles(self, member_id: int) -> List[str]:
        """Get member roles by ID."""
        return self.members.get(member_id, {}).get('roles', [])
        
    def get_member_count(self) -> int:
        """Get total number of cached members."""
        return len(self.members)
        
    def get_members_by_role(self, role_name: str) -> List[dict]:
        """Get all members with a specific role."""
        results = []
        for member_id, data in self.members.items():
            if role_name in data['roles']:
                results.append({
                    'id': member_id,
                    'name': data['name']
                })
        return results
        
    def clear_cache(self) -> None:
        """Clear all cached members."""
        self.members.clear()

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
    return intents

async def cache_all_guilds_members(bot) -> None:
    """Cache members from all guilds the bot is in."""
    print("Caching members...")
    member_cache.clear_cache()
    
    for guild in bot.guilds:
        for member in guild.members:
            member_cache.add_member(member)
        
    print(f"Cached {member_cache.get_member_count()} members!")
