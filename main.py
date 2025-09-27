import discord
import os
from discord.ext import commands
from Core import leaderboard
intents = discord.Intents.default()
intents.message_content = True

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


bot.run(os.getenv("COMPILED_TOKEN"))
