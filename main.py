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
intents = discord.Intents.default()
intents.message_content = True
intents = compile_members.setup_member_intents()

bot = commands.Bot(command_prefix="!", intents=intents)

# simple flag to prevent double on_ready execution
already_ready = False


# --------------------
# events
# --------------------
@bot.event
async def on_ready():
    global already_ready
    if already_ready:
        return  # stop if on_ready fired twice
    already_ready = True

    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")


# --------------------
# commands
# --------------------
@bot.command()
async def leaderboard(ctx):
    await ctx.send("Noper")


@bot.command()
async def myrank(ctx):
    await ctx.send("Ah! no ranks yet") 


@bot.command()
async def lookup(ctx):
    await ctx.send("Who're you tryna look up?")


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
    # make sure cache only runs once per command call
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.member_cache.get_cache_info()
    await ctx.send(
        f"Cached {info['member_count']} members. "
        f"Last updated: {info['last_updated']}"
    )


@bot.command()
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        await ctx.send(
            f"🔍 {details['display_name']} "
            f"(Roles: {', '.join(details['roles'])})"
        )
    else:
        await ctx.send("Member not found in cache.")


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