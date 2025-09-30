import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta


class Ticketing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = False
        self.active_tickets = {}  # {user_id: {"channel_id": int, "expires": datetime}}

    # --------------------
    # lifecycle
    # --------------------
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.cleanup_task.is_running():
            self.cleanup_task.start()

    def cog_unload(self):
        if self.cleanup_task.is_running():
            self.cleanup_task.cancel()

    # --------------------
    # commands
    # --------------------
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_ticketing(self, ctx):
        """Enable or disable the ticketing system."""
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        await ctx.send(embed=discord.Embed(
            title="🎫 Ticketing System",
            description=f"Ticketing is now **{status}**",
            color=discord.Color.green() if self.enabled else discord.Color.red()
        ))

    @commands.command()
    async def ticket(self, ctx):
        """Create a ticket if ticketing is enabled."""
        if not self.enabled:
            await ctx.send("❌ Ticketing is currently disabled.")
            return

        if ctx.author.id in self.active_tickets:
            await ctx.send("❌ You already have an active ticket.")
            return

        guild = ctx.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            category=category,
            overwrites=overwrites
        )

        self.active_tickets[ctx.author.id] = {
            "channel_id": channel.id,
            "expires": datetime.now() + timedelta(days=2)
        }

        await channel.send(
            embed=discord.Embed(
                title="🎟️ New Ticket",
                description=f"{ctx.author.mention}, please submit your answer here.",
                color=discord.Color.blue()
            )
        )
        await ctx.send(f"✅ Ticket created: {channel.mention}")

    # --------------------
    # cleanup
    # --------------------
    @tasks.loop(minutes=1)
    async def cleanup_task(self):
        now = datetime.now()
        expired = [uid for uid, data in self.active_tickets.items() if data["expires"] < now]
        for uid in expired:
            data = self.active_tickets.pop(uid)
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                await channel.delete()

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


def setup_ticketing(bot):
    bot.add_cog(Ticketing(bot))