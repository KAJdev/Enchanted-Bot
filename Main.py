# Imports
import Config
import discord
from discord.ext import commands, tasks
import logging
import random
import datetime
import importlib
import Utils

logging.basicConfig(level = logging.INFO, format="Enchanted [%(levelname)s] | %(message)s")

running_commands = 0


class UserInBlacklist(Exception):
    """Raised when a user is in the blacklist"""
    pass


async def get_prefix(bot, message):
    if Config.testing:
        return "b]"
    return commands.when_mentioned_or(Utils.fetch_prefix(message))(bot, message)

bot = commands.AutoShardedBot(command_prefix = get_prefix, case_insensitive = True)

bot.remove_command("help")

# Cogs
cogs = ["Eval", "Settings", "Profile", "Spells", "Matchmaking", "Chests", "Bosses", "Essentials", "Cosmetics", "Leaderboard", "Shop", "Inventory", "TopGG", "Clans", "Blacklist"]

# Starts all cogs
for cog in cogs:
    bot.load_extension("Cogs." + cog)

# Check to see if the user invoking the command is in the OWNERIDS Config
def owner(ctx):
    return int(ctx.author.id) in Config.OWNERIDS

# Restarts and reloads all cogs
@bot.command(aliases = ["retard"])
@commands.check(owner)
async def restart(ctx):
    """
    Restart the bot.
    """
    restarting = discord.Embed(
        title = "Restarting...",
        color = Config.MAINCOLOR
    )
    msg = await ctx.send(embed = restarting)
    for cog in cogs:
        bot.reload_extension("Cogs." + cog)
        restarting.add_field(name = f"{cog}", value = "✅ Restarted!")
        #await msg.edit(embed = restarting)
    importlib.reload(Utils)
    restarting.add_field(name="Utils module", value="Reloaded")
    importlib.reload(Config)
    restarting.add_field(name="Config", value="Reloaded")
    restarting.title = "Bot Restarted"
    await msg.edit(embed = restarting)
    logging.info(f"Bot has been restarted succesfully in {len(bot.guilds)} server(s) with {len(bot.users)} users by {ctx.author.name}#{ctx.author.discriminator} (ID - {ctx.author.id})!")
    await msg.delete(delay = 3)
    if ctx.guild != None:
        await ctx.message.delete(delay = 3)

@bot.before_invoke
async def before_commands(ctx):
    global running_commands
    running_commands += 1
    logging.info("Command " + ctx.command.name + " Started by " + ctx.author.name + " | " + str(running_commands) + " commands running")

@bot.after_invoke
async def after_commands(ctx):
    global running_commands
    running_commands -= 1
    logging.info("Command " + ctx.command.name + " Started by " + ctx.author.name + " Was completed alright." + " | " + str(running_commands) + " commands running")

# Command error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.UserInputError):
        embed = discord.Embed(
            title="Oh no.",
            description=f"Looks like you used that command wrong:\n```{error}```",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, UserInBlacklist):
        embed = discord.Embed(
            title="Oh no.",
            description=f"It looks like you have been blacklisted from using Enchanted. You can join the [Support Server](https://discord.gg/c8kRvzf) and appeal by opening a ticket.",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title = "Error",
            description = f"An error has occured while executing this command:\n```{error}```",
            color = Config.ERRORCOLOR
        )
        await ctx.send(embed = embed)
        raise error

@tasks.loop(seconds=30)
async def status_set():
    if Config.testing:
        statuses = ["new additions", "prayers from above", "for the next update", "new things", "out for you", "bug reports", "suggestions"]
    else:
        statuses = ["heavenly beings smile", "flutters of the night", "the sky twinkle", "trees bend",
                    "the faries dance", "leaves fall", "every star", "grass wave", "bees buzz", "startdust sprinkle",
                    "tadpoles play", "waterfalls"]
    if Config.testing:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))
    else:
        await bot.change_presence(activity = discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses) + " | ]help"))


@bot.check
async def check_blacklist(ctx):
    if Config.BLACKLIST.find_one({'user_id': ctx.author.id}) is not None:
        embed = discord.Embed(
            title="Oh no.",
            description=f"It looks like you have been blacklisted from using Enchanted. You can join the [Support Server](https://discord.gg/QeRbckh) and appeal by opening a ticket.",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
        raise UserInBlacklist
    else:
        return True


# On ready
@bot.event
async def on_ready():
    logging.info(f"Bot has started succesfully in {len(bot.guilds)} server(s) with {len(bot.users)} users")
    status_set.start()
    if not hasattr(bot, "uptime"):
        bot.uptime = datetime.datetime.utcnow()

# shard on_ready
@bot.event
async def on_shard_ready(shard_id):
    logging.info(f"Shard ID {shard_id} is online and connected to discord gateway")


# Starts bot
bot.run(Config.TOKEN)
