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
bot = commands.Bot(command_prefix="$", intents=intents)

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
# load ticketing
# --------------------
setup_ticketing(bot)

# --------------------
# leaderboard commands
# --------------------
@bot.command()
async def cache_leaderboard(ctx):
    await leaderboard.cache_all_guilds(bot)
    await ctx.send(f"✅ Leaderboard cached! Total members: {len(leaderboard.scores)}")

@bot.command(name="leaderboard")
async def leaderboard_command(ctx, top_n: int = 10):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    leaders = leaderboard.get_leaderboard(top_n)
    if not leaders:
        await ctx.send("Leaderboard is empty.")
        return

    embed = discord.Embed(title="🏆 Leaderboard 🏆", color=discord.Color.gold())
    for idx, m in enumerate(leaders, start=1):
        embed.add_field(name=f"{idx}. {m['display_name']}", value=f"{m['wins']} wins", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def myrank(ctx):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    stats = leaderboard.get_member_stats(ctx.author.id)
    rank = leaderboard.get_rank(ctx.author.id)
    await ctx.send(embed=discord.Embed(
        title="📊 My Rank",
        description=f"{stats['display_name']} — {stats['wins']} wins (Rank #{rank})",
        color=discord.Color.blue()
    ))

@bot.command()
async def lookup(ctx, member: discord.Member):
    leaderboard.ensure_member(member.id, member.display_name)
    stats = leaderboard.get_member_stats(member.id)
    rank = leaderboard.get_rank(member.id)
    await ctx.send(embed=discord.Embed(
        title="🔍 Lookup",
        description=f"{stats['display_name']} — {stats['wins']} wins (Rank #{rank})",
        color=discord.Color.green()
    ))

@bot.command()
async def addwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.add_win(member.id, member.display_name)
    await ctx.send(f"✅ Added a win to {member.display_name}")

@bot.command()
async def subwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.ensure_member(member.id, member.display_name)
    stats = leaderboard.get_member_stats(member.id)
    if stats["wins"] > 0:
        stats["wins"] -= 1
        leaderboard.save_to_file()
        await ctx.send(f"➖ Subtracted a win from {member.display_name}")
    else:
        await ctx.send("❌ Wins cannot go below 0.")

# --------------------
# member cache commands
# --------------------
@bot.command()
async def cache_members(ctx):
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.get_member_cache().get_cache_info()
    await ctx.send(f"✅ Cached {info['member_count']} members. Last updated: {info['last_updated']}")

@bot.command()
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        await ctx.send(f"🔍 {details['display_name']} (Roles: {', '.join(details['roles'])})")
    else:
        await ctx.send("❌ Member not found.")

@bot.command()
async def search_member(ctx, *, query: str):
    results = compile_members.get_member_cache().search_members(query)
    if results:
        names = ", ".join([r['display_name'] for r in results])
        await ctx.send(f"Found: {names}")
    else:
        await ctx.send("No members found.")

# --------------------
# run bot
# --------------------
load_dotenv(dotenv_path=os.path.abspath(".env"))
token = os.getenv("COMPILED_TOKEN")
if not token:
    raise ValueError("❌ No COMPILED_TOKEN found in .env file")

print("✅ Token loaded")
bot.run(token)