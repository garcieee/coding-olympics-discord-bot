import discord
import os
from discord.ext import commands
from Core import leaderboard
from Core import compile_members

from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

intents = compile_members.setup_member_intents()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

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


def Add(num, num2):
    return int(num) + int(num2)

@bot.command()
async def add(ctx, arg, arg2):
    await ctx.send(Add(arg, arg2))
    
@bot.command()
async def cache_members(ctx):
    await compile_members.cache_all_guilds_members(bot)
    info = compile_members.member_cache.get_cache_info()
    await ctx.send(f"Cached {info['member_count']} members. Last updated: {info['last_updated']}")

@bot.command()
async def member_lookup(ctx, member_id: int):
    details = compile_members.get_member_cache().get_member_details(member_id)
    if details:
        await ctx.send(f"🔍 {details['display_name']} (Roles: {', '.join(details['roles'])})")
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


# Get the Discord bot token from .env file. sorry person who made this is a windows user
load_dotenv(dotenv_path=os.path.abspath(".env"))

token = os.getenv("COMPILED_TOKEN")
print("Token loaded:", token)
bot.run(token)
