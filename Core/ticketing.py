"""
Ticketing Cog.
- Admins can toggle ticketing on/off.
- Users can create a private ticket channel with $ticket.
- Ticket channels auto-delete after 2 days.
All bot responses in this cog are embeds.
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from Core import compile_members


class Ticketing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = False
        self.active_tickets = {}  # user_id -> {channel_id, expires}
        # don't start loop here; start on_ready

    # start cleanup when bot ready
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.cleanup_task.is_running():
            self.cleanup_task.start()

    def cog_unload(self):
        if self.cleanup_task.is_running():
            self.cleanup_task.cancel()

    # ----------------
    # admin toggle
    # ----------------
    @commands.command(name="toggle_ticketing")
    @commands.has_permissions(administrator=True)
    async def toggle_ticketing(self, ctx):
        self.enabled = not self.enabled
        status = "enabled ✅" if self.enabled else "disabled ❌"
        embed = discord.Embed(
            title="🎫 Ticketing System",
            description=f"Ticketing has been **{status}**",
            color=discord.Color.green() if self.enabled else discord.Color.red()
        )
        await ctx.send(embed=embed)

    # ----------------
    # user creates ticket
    # ----------------
    @commands.command(name="ticket")
    async def ticket(self, ctx):
        if not self.enabled:
            await ctx.send(embed=discord.Embed(
                description="❌ Ticketing is currently disabled.",
                color=discord.Color.red()
            ))
            return

        if ctx.author.id in self.active_tickets:
            await ctx.send(embed=discord.Embed(
                description="⚠️ You already have an open ticket.",
                color=discord.Color.orange()
            ))
            return

        guild = ctx.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        # allow server admins (roles with administrator) to view
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            category=category,
            overwrites=overwrites
        )

        expires = datetime.utcnow() + timedelta(days=2)
        self.active_tickets[ctx.author.id] = {"channel_id": channel.id, "expires": expires}

        await channel.send(embed=discord.Embed(
            title="🎟️ New Ticket",
            description=f"{ctx.author.mention}, this channel is private. Submit your answer here. It will be deleted in 2 days.",
            color=discord.Color.blue()
        ))
        await ctx.send(embed=discord.Embed(
            description=f"✅ Ticket created: {channel.mention}",
            color=discord.Color.green()
        ))

    # ----------------
    # cleanup loop
    # ----------------
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        now = datetime.utcnow()
        to_remove = []
        for uid, data in list(self.active_tickets.items()):
            if data["expires"] <= now:
                ch = self.bot.get_channel(data["channel_id"])
                if ch:
                    try:
                        await ch.delete(reason="Ticket expired (2 days)")
                    except Exception:
                        pass
                to_remove.append(uid)

        for uid in to_remove:
            self.active_tickets.pop(uid, None)

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


# helper to install cog easily from main
def setup_ticketing(bot):
    bot.add_cog(Ticketing(bot))