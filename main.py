import discord
from discord.ext import commands
from core.leaderboard import leaderboard
from core.ticketing import setup_ticketing

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

# ----------------------
# Custom Help Command
# ----------------------
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 Help Menu",
        description="List of available commands:",
        color=discord.Color.blue()
    )

    # Leaderboard
    embed.add_field(
        name="🏆 Leaderboard",
        value=(
            "`$leaderboard` - Show the top leaderboard\n"
            "`$myrank` - Show your rank & wins\n"
            "`$lookup @member` - Look up another member’s stats"
        ),
        inline=False
    )

    # Members
    embed.add_field(
        name="👥 Members",
        value=(
            "`$cache_members` - Cache all members\n"
            "`$member_lookup <id>` - Lookup a member by ID\n"
            "`$search_member <query>` - Search for members"
        ),
        inline=False
    )

    # Ticketing
    embed.add_field(
        name="🎟️ Ticketing",
        value="`$ticket` - Open a ticket (if enabled)",
        inline=False
    )

    # Admin
    embed.add_field(
        name="🛠️ Admin",
        value=(
            "`$cache_leaderboard` - Cache all members into leaderboard\n"
            "`$toggle_ticketing` - Enable/Disable ticketing\n"
            "`$addwin [@member]` - Add a win\n"
            "`$subwin [@member]` - Subtract a win"
        ),
        inline=False
    )

    await ctx.send(embed=embed)


# ----------------------
# Leaderboard Commands
# ----------------------
@bot.command()
async def leaderboard_cmd(ctx):
    top = leaderboard.get_leaderboard()
    embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
    for i, entry in enumerate(top, start=1):
        embed.add_field(
            name=f"{i}. {entry['display_name']}",
            value=f"Wins: {entry['wins']}",
            inline=False
        )
    await ctx.send(embed=embed)


@bot.command()
async def myrank(ctx):
    stats = leaderboard.get_member_stats(ctx.author.id)
    if not stats:
        await ctx.send(embed=discord.Embed(
            description="❌ You are not on the leaderboard yet!",
            color=discord.Color.red()
        ))
        return
    rank = leaderboard.get_rank(ctx.author.id)
    embed = discord.Embed(
        title="📊 Your Rank",
        description=f"Rank: **{rank}**\nWins: **{stats['wins']}**",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


@bot.command()
async def lookup(ctx, member: discord.Member):
    stats = leaderboard.get_member_stats(member.id)
    if not stats:
        await ctx.send(embed=discord.Embed(
            description="❌ Member not found on the leaderboard.",
            color=discord.Color.red()
        ))
        return
    rank = leaderboard.get_rank(member.id)
    embed = discord.Embed(
        title=f"📊 Stats for {member.display_name}",
        description=f"Rank: **{rank}**\nWins: **{stats['wins']}**",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


# ----------------------
# Admin Leaderboard Commands
# ----------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def addwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.add_win(member.id, member.display_name)
    await ctx.send(embed=discord.Embed(
        description=f"✅ Added a win to **{member.display_name}**",
        color=discord.Color.green()
    ))


@commands.has_permissions(administrator=True)
@bot.command()
async def subwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    stats = leaderboard.get_member_stats(member.id)
    if stats and stats["wins"] > 0:
        leaderboard.set_wins(member.id, member.display_name, stats["wins"] - 1)
        await ctx.send(embed=discord.Embed(
            description=f"➖ Subtracted a win from **{member.display_name}**",
            color=discord.Color.orange()
        ))
    else:
        await ctx.send(embed=discord.Embed(
            description="❌ Cannot subtract, no wins recorded.",
            color=discord.Color.red()
        ))


# ----------------------
# Cache Members
# ----------------------
@bot.command()
async def cache_members(ctx):
    await leaderboard.cache_guild_members(ctx.guild)
    await ctx.send(embed=discord.Embed(
        description=f"✅ Cached all members from **{ctx.guild.name}**",
        color=discord.Color.green()
    ))


@commands.has_permissions(administrator=True)
@bot.command()
async def cache_leaderboard(ctx):
    await leaderboard.cache_all_guilds(bot)
    await ctx.send(embed=discord.Embed(
        description="✅ Cached all guilds into leaderboard.",
        color=discord.Color.green()
    ))


# ----------------------
# Load Ticketing Cog
# ----------------------
setup_ticketing(bot)


# ----------------------
# Events
# ----------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")


# ----------------------
# Run Bot
# ----------------------
if __name__ == "__main__":
    import os
    TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_TOKEN_HERE"
    bot.run(TOKEN)