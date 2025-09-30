# main.py
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# correct Core imports (case-sensitive)
from Core.leaderboard import leaderboard
from Core.ticketing import setup_ticketing
from Core import compile_members

# --------------------
# setup
# --------------------
load_dotenv(dotenv_path=os.path.abspath(".env"))
intents = compile_members.setup_member_intents()
bot = commands.Bot(command_prefix="//", intents=intents, help_command=None)  # disable default help

# --------------------
# start ticketing cog (adds cog to bot)
# --------------------
setup_ticketing(bot)

# --------------------
# events
# --------------------
@bot.event
async def on_ready():
    # load cached members on startup
    compile_members.load_cache_from_file()
    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")


# --------------------
# HELP (member-only embed)
# --------------------
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 Help (Members)",
        description="Commands you can use:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🏆 Leaderboard",
        value=(
            "`//leaderboard` - Show the top leaderboard\n"
            "`//myrank` - Show your rank & wins\n"
            "`//lookup @member` - Look up another member’s stats"
        ),
        inline=False
    )

    embed.add_field(
        name="👥 Members (view/search)",
        value=(
            "`//member_lookup <id>` - Lookup a member by ID\n"
            "`//search_member <query>` - Search for members"
        ),
        inline=False
    )

    embed.add_field(
        name="🎟️ Ticketing",
        value="`//ticket` - Open a ticket (if enabled)",
        inline=False
    )

    await ctx.send(embed=embed)


# --------------------
# HELP (admin-only embed)
# --------------------
@commands.has_permissions(administrator=True)
@bot.command(name="help_admin")
async def help_admin_command(ctx):
    embed = discord.Embed(
        title="📖 Help (Admins)",
        description="Admin commands:",
        color=discord.Color.dark_blue()
    )

    embed.add_field(
        name="🏆 Leaderboard (admin)",
        value=(
            "`//cache_leaderboard` - Cache all guild members into the leaderboard\n"
            "`//addwin [@member]` - Add a win (admin only)\n"
            "`//subwin [@member]` - Subtract a win (admin only)"
        ),
        inline=False
    )

    embed.add_field(
        name="👥 Members (admin)",
        value=(
            "`//cache_members` - Cache all members (admin only)\n"
            "`//member_lookup <id>` - Lookup a member by ID\n"
            "`//search_member <query>` - Search for members"
        ),
        inline=False
    )

    embed.add_field(
        name="🎟️ Ticketing (admin)",
        value="`//toggle_ticketing` - Toggle ticketing on/off\n`#ticket` - Open a ticket (users)",
        inline=False
    )

    await ctx.send(embed=embed)


# --------------------
# Leaderboard commands (embed outputs)
# --------------------
@bot.command(name="leaderboard")
async def leaderboard_command(ctx, top_n: int = 10):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    leaders = leaderboard.get_leaderboard(top_n)
    if not leaders:
        await ctx.send(embed=discord.Embed(description="Leaderboard is empty.", color=discord.Color.red()))
        return

    embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
    for idx, m in enumerate(leaders, start=1):
        embed.add_field(name=f"{idx}. {m['display_name']}", value=f"{m['wins']} wins", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="myrank")
async def myrank(ctx):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    stats = leaderboard.get_member_stats(ctx.author.id)
    rank = leaderboard.get_rank(ctx.author.id)
    embed = discord.Embed(
        title="📊 My Rank",
        description=f"{stats['display_name']} — **{stats['wins']} wins** (Rank #{rank})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


@bot.command(name="lookup")
async def lookup(ctx, member: discord.Member):
    leaderboard.ensure_member(member.id, member.display_name)
    stats = leaderboard.get_member_stats(member.id)
    rank = leaderboard.get_rank(member.id)
    embed = discord.Embed(
        title=f"🔍 Stats for {stats['display_name']}",
        description=f"Wins: **{stats['wins']}**\nRank: **#{rank}**",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)


# --------------------
# Admin-only leaderboard changes (admin permission)
# --------------------
@commands.has_permissions(administrator=True)
@bot.command(name="addwin")
async def addwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.add_win(member.id, member.display_name)
    await ctx.send(embed=discord.Embed(
        description=f"✅ Added a win to **{member.display_name}**",
        color=discord.Color.green()
    ))


@commands.has_permissions(administrator=True)
@bot.command(name="subwin")
async def subwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.ensure_member(member.id, member.display_name)
    if leaderboard.get_member_stats(member.id)["wins"] > 0:
        leaderboard.subtract_win(member.id, member.display_name)
        await ctx.send(embed=discord.Embed(
            description=f"➖ Subtracted a win from **{member.display_name}**",
            color=discord.Color.orange()
        ))
    else:
        await ctx.send(embed=discord.Embed(
            description="❌ Wins cannot go below 0.",
            color=discord.Color.red()
        ))


# --------------------
# Cache commands
# --------------------
@commands.has_permissions(administrator=True)
@bot.command(name="cache_members")
async def cache_members(ctx):
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.get_member_cache().get_cache_info()
    await ctx.send(embed=discord.Embed(
        title="📥 Members Cached",
        description=f"✅ Cached **{info['member_count']}** members\nLast updated: {info['last_updated']}",
        color=discord.Color.green()
    ))


@commands.has_permissions(administrator=True)
@bot.command(name="cache_leaderboard")
async def cache_leaderboard_cmd(ctx):
    await leaderboard.cache_all_guilds(bot)
    await ctx.send(embed=discord.Embed(
        description="✅ Cached all guild members into leaderboard.",
        color=discord.Color.green()
    ))


# --------------------
# Member lookup / search
# --------------------
@bot.command(name="member_lookup")
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        roles = details.get("roles", [])
        await ctx.send(embed=discord.Embed(
            title=f"🔍 {details['display_name']}",
            description=f"Roles: {', '.join(roles) if roles else 'None'}",
            color=discord.Color.blue()
        ))
    else:
        await ctx.send(embed=discord.Embed(description="❌ Member not found.", color=discord.Color.red()))


@bot.command(name="search_member")
async def search_member(ctx, *, query: str):
    results = compile_members.get_member_cache().search_members(query)
    if results:
        names = ", ".join([r['display_name'] for r in results])
        await ctx.send(embed=discord.Embed(description=f"Found: {names}", color=discord.Color.green()))
    else:
        await ctx.send(embed=discord.Embed(description="No members found.", color=discord.Color.red()))


# --------------------
# Run bot
# --------------------
if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"))
    token = os.getenv("COMPILED_TOKEN") or os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("❌ No token found in .env (COMPILED_TOKEN or DISCORD_TOKEN).")
    print("✅ Token loaded")
    bot.run(token)