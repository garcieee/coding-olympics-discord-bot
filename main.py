import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# local imports
from Core import leaderboard
from Core import compile_members

# --------------------
# setup
# --------------------
intents = compile_members.setup_member_intents()

# Use a unique prefix to avoid conflicts with other bots like Carl-bot
bot = commands.Bot(command_prefix="?", intents=intents)

# prevent double on_ready
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

    # load cache from JSON if available
    compile_members.load_cache_from_file()

    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")


# --------------------
# trial/test commands
# --------------------
@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)


def add_numbers(num1, num2):
    return int(num1) + int(num2)


@bot.command()
async def add(ctx, arg, arg2):
    await ctx.send(add_numbers(arg, arg2))


@bot.command()
async def cache_members(ctx):
    """Cache all members from all guilds."""
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.get_member_cache().get_cache_info()
    await ctx.send(
        f"✅ Cached {info['member_count']} members. "
        f"Last updated: {info['last_updated']}"
    )


# --------------------
# leaderboard commands
# --------------------
@bot.command()
async def leaderboard(ctx, top_n: int = 10):
    """Show the top N leaderboard (default 10)."""
    leaders = leaderboard.get_leaderboard(top_n)
    if not leaders:
        await ctx.send("Leaderboard is empty.")
        return

    msg = "**🏆 Leaderboard 🏆**\n"
    for idx, m in enumerate(leaders, start=1):
        msg += f"{idx}. {m['display_name']} — {m['wins']} wins\n"
    await ctx.send(msg)


@bot.command()
async def myrank(ctx):
    """Show your rank & wins."""
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    stats = leaderboard.get_member_stats(ctx.author.id)
    rank = leaderboard.get_rank(ctx.author.id)

    await ctx.send(
        f"📊 {stats['display_name']} — {stats['wins']} wins (Rank #{rank})"
    )


@bot.command()
async def lookup(ctx, member: discord.Member):
    """Look up another member’s stats."""
    leaderboard.ensure_member(member.id, member.display_name)
    stats = leaderboard.get_member_stats(member.id)
    rank = leaderboard.get_rank(member.id)

    await ctx.send(
        f"🔍 {stats['display_name']} — {stats['wins']} wins (Rank #{rank})"
    )


@bot.command()
async def member_lookup(ctx, *, query: str):
    """Look up member info from the cache (roles, etc.)."""
    cache = compile_members.get_member_cache()

    if query.isdigit():
        details = cache.get_member_details(int(query))
    else:
        results = cache.search_members(query)
        details = results[0] if results else None

    if details:
        roles = details.get("roles", [])
        await ctx.send(
            f"🔍 {details['display_name']} "
            f"(Roles: {', '.join(roles) if roles else 'None'})"
        )
    else:
        await ctx.send("❌ Member not found.")


# --------------------
# run bot
# --------------------
load_dotenv(dotenv_path=os.path.abspath(".env"))
token = os.getenv("COMPILED_TOKEN")

if not token:
    raise ValueError("❌ No COMPILED_TOKEN found in .env file")

print("✅ Token loaded")
bot.run(token)