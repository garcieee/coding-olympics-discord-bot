import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

# correct Core imports (case-sensitive)
from Core.leaderboard import leaderboard
from Core.ticketing import setup_ticketing, CloseTicketView
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

    # If the Ticketing cog doesn't provide its own cleanup task, start the fallback cleanup loop.
    cog = bot.get_cog("Ticketing")
    if not (cog and hasattr(cog, "cleanup_task") and getattr(cog, "cleanup_task").is_running()):
        if not _ticket_cleanup_loop.is_running():
            _ticket_cleanup_loop.start()


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
        value="`//toggle_ticketing` - Toggle ticketing on/off\n`//ticket` - Open a ticket (users)",
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
# Ticket command (robust replacement)
# --------------------
@bot.command(name="ticket")
async def ticket_cmd(ctx):
    """
    Robust ticket command:
    - If Ticketing cog exists and is disabled -> send embedded "ticketing is off".
    - If bot lacks Manage Channels permission -> send embedded missing-perms message.
    - Otherwise create a private channel visible to author + admin roles, record expiry (2 days).
    """
    guild = ctx.guild
    if guild is None:
        await ctx.send(embed=discord.Embed(
            description="❌ This command can only be used inside a server.",
            color=discord.Color.red()
        ))
        return

    # Try to use Ticketing cog if present
    cog = bot.get_cog("Ticketing")

    # If cog exists and ticketing is disabled, tell the user with an embed
    if cog and not getattr(cog, "enabled", False):
        await ctx.send(embed=discord.Embed(
            title="🎫 Ticketing Disabled",
            description="Ticketing is currently **disabled**. If you believe this is an error, please contact a server admin.",
            color=discord.Color.red()
        ))
        return

    # If no cog, check a fallback flag on bot if present
    if (not cog) and hasattr(bot, "_ticketing_enabled") and not getattr(bot, "_ticketing_enabled"):
        await ctx.send(embed=discord.Embed(
            title="🎫 Ticketing Disabled",
            description="Ticketing is currently **disabled**. If you believe this is an error, please contact a server admin.",
            color=discord.Color.red()
        ))
        return

    # Check bot permissions in the guild
    me = guild.me or guild.get_member(bot.user.id)
    if not me:
        await ctx.send(embed=discord.Embed(
            description="❌ Could not determine bot permissions in this server.",
            color=discord.Color.red()
        ))
        return

    missing = []
    if not me.guild_permissions.manage_channels:
        missing.append("Manage Channels")
    if not me.guild_permissions.send_messages:
        missing.append("Send Messages")
    if not me.guild_permissions.view_channel:
        missing.append("View Channels")

    if missing:
        await ctx.send(embed=discord.Embed(
            title="⚠️ Missing Permissions",
            description=(
                "I need the following permission(s) to create ticket channels:\n\n"
                f"**{', '.join(missing)}**\n\n"
                "Ask a server admin to grant these to the bot (or give the bot a role with those perms)."
            ),
            color=discord.Color.orange()
        ))
        return

    # Determine the active tickets store (cog.store or bot fallback)
    def get_active_store():
        if cog and hasattr(cog, "active_tickets"):
            return cog.active_tickets
        if not hasattr(bot, "_ticket_active"):
            bot._ticket_active = {}
        return bot._ticket_active

    active_store = get_active_store()

    # Prevent duplicate open ticket
    if ctx.author.id in active_store:
        ticket_data = active_store[ctx.author.id]
        channel = bot.get_channel(ticket_data["channel_id"])
        channel_mention = channel.mention if channel else "your existing ticket"
        await ctx.send(embed=discord.Embed(
            title="⚠️ Ticket Already Open",
            description=f"You already have an open ticket: {channel_mention}\n\nPlease use that channel or wait until it is closed.",
            color=discord.Color.orange()
        ))
        return

    # Find or create 'Tickets' category
    try:
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            # creating a category requires Manage Channels
            category = await guild.create_category("Tickets")
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            title="❌ Permission Denied",
            description="I don't have permission to create categories/channels. Please grant me `Manage Channels`.",
            color=discord.Color.red()
        ))
        return
    except Exception as e:
        await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"Failed to create/find ticket category: `{e}`",
            color=discord.Color.red()
        ))
        return

    # Build overwrites: hide @everyone, allow author, bot, and roles with Administrator
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    for role in guild.roles:
        if role.permissions.administrator:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # Create the ticket channel
    try:
        channel_name = f"ticket-{ctx.author.name}".lower()[:90]
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            title="❌ Permission Denied",
            description="I don't have permission to create channels. Please grant me `Manage Channels`.",
            color=discord.Color.red()
        ))
        return
    except Exception as e:
        await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"Failed to create ticket channel: `{e}`",
            color=discord.Color.red()
        ))
        return

    # Record the ticket with 2-day expiry
    expires = datetime.utcnow() + timedelta(days=2)
    active_store[ctx.author.id] = {"channel_id": channel.id, "expires": expires}

    # ✅ Add button view
    view = CloseTicketView(active_store, channel.id, ctx.author.id)
    bot.add_view(view)  # persistent after restart

    # Send welcome embed in the new channel and confirm to user
    await channel.send(embed=discord.Embed(
        title="🎟️ New Ticket",
        description=(
            f"{ctx.author.mention}, this channel is private. Submit your answer here.\n\n"
            "A server admin and you can see this channel.\n"
            "It will be deleted in 2 days or you can close it manually below."
        ),
        color=discord.Color.blue()
    ), view=view)

    await ctx.send(embed=discord.Embed(
        description=f"✅ Ticket created: {channel.mention}",
        color=discord.Color.green()
    ))


# --------------------
# Ticket cleanup loop (fallback)
# --------------------
@tasks.loop(minutes=10)
async def _ticket_cleanup_loop():
    # check cog store first, fallback to bot._ticket_active
    cog = bot.get_cog("Ticketing")
    store = cog.active_tickets if (cog and hasattr(cog, "active_tickets")) else getattr(bot, "_ticket_active", {})
    now = datetime.utcnow()
    expired = [uid for uid, data in list(store.items()) if data.get("expires") and data["expires"] <= now]
    for uid in expired:
        data = store.pop(uid, None)
        if data:
            ch = bot.get_channel(data.get("channel_id"))
            if ch:
                try:
                    await ch.delete(reason="Ticket expired (2 days)")
                except Exception:
                    pass


@_ticket_cleanup_loop.before_loop
async def _before_ticket_cleanup():
    await bot.wait_until_ready()


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