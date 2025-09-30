import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# local imports
from Core.leaderboard import leaderboard  # global instance
from Core import compile_members

# --------------------
# setup
# --------------------
intents = compile_members.setup_member_intents()
bot = commands.Bot(command_prefix="$", intents=intents)

# remove default help so we can define our own
bot.remove_command("help")

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
# leaderboard commands
# --------------------
@bot.command()
async def cache_leaderboard(ctx):
    await leaderboard.cache_all_guilds(bot)
    await ctx.send(embed=discord.Embed(
        title="✅ Leaderboard Cached",
        description=f"Total members: {len(leaderboard.scores)}",
        color=discord.Color.green()
    ))

@bot.command(name="leaderboard")
async def leaderboard_command(ctx, top_n: int = 10):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)

    leaders = leaderboard.get_leaderboard(top_n)
    if not leaders:
        await ctx.send(embed=discord.Embed(
            title="🏆 Leaderboard",
            description="Leaderboard is empty.",
            color=discord.Color.red()
        ))
        return

    desc = ""
    for idx, m in enumerate(leaders, start=1):
        desc += f"{idx}. {m['display_name']} — {m['wins']} wins\n"

    embed = discord.Embed(
        title="🏆 Leaderboard 🏆",
        description=desc,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def myrank(ctx):
    leaderboard.ensure_member(ctx.author.id, ctx.author.display_name)
    stats = leaderboard.get_member_stats(ctx.author.id)
    rank = leaderboard.get_rank(ctx.author.id)

    embed = discord.Embed(
        title="📊 My Rank",
        description=f"{stats['display_name']} — {stats['wins']} wins (Rank #{rank})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def lookup(ctx, member: discord.Member):
    leaderboard.ensure_member(member.id, member.display_name)
    stats = leaderboard.get_member_stats(member.id)
    rank = leaderboard.get_rank(member.id)

    embed = discord.Embed(
        title="🔍 Lookup",
        description=f"{stats['display_name']} — {stats['wins']} wins (Rank #{rank})",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.command()
async def addwin(ctx, member: discord.Member = None):
    member = member or ctx.author
    leaderboard.add_win(member.id, member.display_name)
    embed = discord.Embed(
        title="✅ Win Added",
        description=f"Added a win to {member.display_name}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# --------------------
# other commands
# --------------------
@bot.command()
async def test(ctx, arg):
    await ctx.send(embed=discord.Embed(
        title="Test Command",
        description=arg,
        color=discord.Color.orange()
    ))

def add_numbers(num1, num2):
    return int(num1) + int(num2)

@bot.command()
async def add(ctx, arg, arg2):
    result = add_numbers(arg, arg2)
    await ctx.send(embed=discord.Embed(
        title="➕ Add",
        description=f"{arg} + {arg2} = {result}",
        color=discord.Color.orange()
    ))

@bot.command()
async def cache_members(ctx):
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.get_member_cache().get_cache_info()
    embed = discord.Embed(
        title="✅ Members Cached",
        description=f"Cached {info['member_count']} members.\nLast updated: {info['last_updated']}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        embed = discord.Embed(
            title="🔍 Member Lookup",
            description=f"{details['display_name']} (Roles: {', '.join(details['roles']) if details['roles'] else 'None'})",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="❌ Member Lookup",
            description="Member not found.",
            color=discord.Color.red()
        )
    await ctx.send(embed=embed)

@bot.command()
async def search_member(ctx, *, query: str):
    results = compile_members.get_member_cache().search_members(query)
    if results:
        names = ", ".join([r['display_name'] for r in results])
        embed = discord.Embed(
            title="🔍 Search Results",
            description=f"Found: {names}",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="🔍 Search Results",
            description="No members found.",
            color=discord.Color.red()
        )
    await ctx.send(embed=embed)

# --------------------
# custom help command
# --------------------
@bot.command(name="help")
async def help_command(ctx):
    prefix = ctx.prefix
    embed = discord.Embed(
        title="📖 Help Menu",
        description="Here are all available commands:",
        color=discord.Color.teal()
    )

    embed.add_field(name="Leaderboard", value=f"`{prefix}cache_leaderboard`, `{prefix}leaderboard`, `{prefix}myrank`, `{prefix}lookup @member`, `{prefix}addwin [@member]`", inline=False)
    embed.add_field(name="Members", value=f"`{prefix}cache_members`, `{prefix}member_lookup <id>`, `{prefix}search_member <query>`", inline=False)
    embed.add_field(name="Misc", value=f"`{prefix}test <arg>`, `{prefix}add <num1> <num2>`", inline=False)

    await ctx.send(embed=embed)

# --------------------
# run bot
# --------------------
load_dotenv(dotenv_path=os.path.abspath(".env"))
token = os.getenv("COMPILED_TOKEN")

if not token:
    raise ValueError("❌ No COMPILED_TOKEN found in .env file")

print("✅ Token loaded")
bot.run(token)