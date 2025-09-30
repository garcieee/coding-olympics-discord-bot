import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# local imports
from Core.leaderboard import leaderboard
from Core import compile_members
from Core.ticketing import setup_ticketing

# --------------------
# setup
# --------------------
intents = compile_members.setup_member_intents()
bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)  # disable default help

already_ready = False

# --------------------
# events
# --------------------
@bot.event
async def on_ready():
    global already_ready
    if already_ready:
        return
    already_ready = True

    compile_members.load_cache_from_file()
    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")


# --------------------
# leaderboard commands
# --------------------
@bot.command()
async def cache_leaderboard(ctx):
    await leaderboard.cache_all_guilds(bot)
    embed = discord.Embed(
        title="📥 Leaderboard Cached",
        description=f"✅ Total members: **{len(leaderboard.scores)}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="leaderboard")
async def leaderboard_command(ctx, top_n: int = 10):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    leaders = leaderboard.get_leaderboard(top_n)
    if not leaders:
        await ctx.send(embed=discord.Embed(
            description="Leaderboard is empty.",
            color=discord.Color.red()
        ))
        return

    embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
    for idx, m in enumerate(leaders, start=1):
        embed.add_field(
            name=f"{idx}. {m['display_name']}",
            value=f"{m['wins']} wins",
            inline=False
        )
    await ctx.send(embed=embed)


@bot.command()
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


@bot.command()
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


@bot.command()
async def addwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.add_win(member.id, member.display_name)
    embed = discord.Embed(
        description=f"✅ Added a win to **{member.display_name}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command()
async def subwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.ensure_member(member.id, member.display_name)
    if leaderboard.scores[member.id]["wins"] > 0:
        leaderboard.scores[member.id]["wins"] -= 1
        leaderboard.save_to_file()
        msg = f"➖ Subtracted a win from **{member.display_name}**"
        color = discord.Color.orange()
    else:
        msg = f"⚠️ {member.display_name} already has 0 wins."
        color = discord.Color.red()

    await ctx.send(embed=discord.Embed(description=msg, color=color))


# --------------------
# member cache commands
# --------------------
@bot.command()
async def cache_members(ctx):
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.get_member_cache().get_cache_info()
    embed = discord.Embed(
        title="📥 Members Cached",
        description=f"✅ Cached **{info['member_count']}** members\n"
                    f"Last updated: {info['last_updated']}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command()
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        roles = details.get("roles", [])
        embed = discord.Embed(
            title=f"🔍 {details['display_name']}",
            description=f"Roles: {', '.join(roles) if roles else 'None'}",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(description="❌ Member not found.", color=discord.Color.red())
    await ctx.send(embed=embed)


@bot.command()
async def search_member(ctx, *, query: str):
    results = compile_members.get_member_cache().search_members(query)
    if results:
        names = ", ".join([r['display_name'] for r in results])
        embed = discord.Embed(description=f"Found: {names}", color=discord.Color.green())
    else:
        embed = discord.Embed(description="No members found.", color=discord.Color.red())
    await ctx.send(embed=embed)


# --------------------
# help command
# --------------------
@bot.command(name="helpme")
async def helpme(ctx):
    embed = discord.Embed(title="📖 Bot Commands", color=discord.Color.teal())

    embed.add_field(
        name="🎫 Ticketing",
        value="`$toggle_ticketing` — Enable/disable ticketing (admin)\n"
              "`$ticket` — Create a new ticket",
        inline=False
    )

    embed.add_field(
        name="🏆 Leaderboard",
        value="`$leaderboard [N]` — Show top N leaderboard\n"
              "`$myrank` — Show your rank\n"
              "`$lookup @member` — Look up another member\n"
              "`$addwin [@member]` — Add a win\n"
              "`$subwin [@member]` — Subtract a win\n"
              "`$cache_leaderboard` — Cache all guild members",
        inline=False
    )

    embed.add_field(
        name="👥 Members",
        value="`$cache_members` — Cache all members\n"
              "`$member_lookup <id>` — Lookup member by ID\n"
              "`$search_member <query>` — Search member by name",
        inline=False
    )

    await ctx.send(embed=embed)


# --------------------
# run bot
# --------------------
load_dotenv(dotenv_path=os.path.abspath(".env"))
token = os.getenv("COMPILED_TOKEN")

if not token:
    raise ValueError("❌ No COMPILED_TOKEN found in .env file")

setup_ticketing(bot)

print("✅ Token loaded")
bot.run(token)