import math

import pymongo
import asyncio
import Config
import discord
import datetime
from discord.ext import commands, tasks
import logging
import Utils


class Essentials(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='discord')
    async def discord_link(self, ctx):
        embed = discord.Embed(description="[**Click here to join the community!**](https://discord.gg/c8kRvzf)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/ccXi2xb.png")
        await ctx.send(embed=embed)

    @commands.command(name='vote', aliases=['daily', 'weekly'])
    async def vote_link(self, ctx):
        # embed=discord.Embed(description="[**Click here to vote for the bot**](https://top.gg/bot/697879596040716455)", color = Config.MAINCOLOR)
        embed=discord.Embed(description="[**Click here to vote for the bot!**](https://top.gg/bot/697879596040716455/vote)\nyou can vote every 12 hours.", color = Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/ccXi2xb.png")
        await ctx.send(embed=embed)

    @commands.command(aliases=['h', 'commands'])
    async def help(self, ctx):
        embed=discord.Embed(title="Help", description="`]battle` - start a battle with another player\n`]clan` - view and join clans\n`]dungeon` - start a dungeon battle\n`]profile` - view your profile and statistics\n`]upgrade` - upgrade your items\n`]chests` - view and open your chests\n`]spells` - view and equip your spells for battle\n`]boss` - start a bossfight and battle a boss with your friends\n`]discord` - join the community!\n`]twitter` - Follow our twitter for updates!\n`]invite` - invite the bot!\n`]vote` - gain some neat rewards!\n`]rebirth` - reset your character and choose a new class\n`]shop` - view today's NPC shop.\n`]items` - view and equip weapons and armor.", color = Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def twitter(self, ctx):
        embed = discord.Embed(description="[**Here's our twitter page!**](https://twitter.com/EnchantedGG)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/ccXi2xb.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        embed = discord.Embed(description="[**Add the bot to your server!**](https://discordapp.com/api/oauth2/authorize?client_id=697879596040716455&permissions=67464272&scope=bot)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/ccXi2xb.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def wiki(self, ctx, topic : str = None, page : int = None):
        if topic is None:
            embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki", description="Welcome to the enchanted wiki command. Here might be some useful things to check out.\n\n`]tutorial`\n`]help`\n`]wiki <topic> <page>`\n\nHere are the current topics in the wiki:\n\n`" + "`, ".join(x['name'] for x in Config.WIKI) + "`.")
            await ctx.send(embed=embed)
        else:
            pass

    @commands.command()
    async def toggle_q(self, ctx):
        if ctx.author.id in Config.OWNERIDS:
            Config.OPEN_QUEUES = not Config.OPEN_QUEUES
            await ctx.send("Queuing is now set to: " + str(Config.OPEN_QUEUES))

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx):
        """Returns an embed containing some basic statistics."""
        
        prefix = Utils.fetch_prefix(ctx)

        embed = discord.Embed(
            title="Stats for Enchanted",
            color=Config.MAINCOLOR,
            description=f"**Name**: Enchanted\n"
            + f"**Prefix**: {prefix}\n"
            + f"**Ping**: {round(self.bot.latency * 1000)} ms\n"
            + f"**Uptime**: {self.get_uptime()}\n"
            + f"**Server Count**: {len(self.bot.guilds)} ({self.bot.shard_count} shards)\n"
            + f"**Saved Accounts**: {Config.USERS.count_documents({})}\n"
            + f"**Discord**: <https://discord.gg/72RFQpU>",
        )

        await ctx.send(embed=embed)

    def get_uptime(self):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime

        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if days:
            fmt = f"{days} days, {hours} hours, {minutes} minutes and {seconds} seconds"
        elif hours:
            fmt = f"{hours} hours, {minutes} minutes and {seconds} seconds"
        elif minutes:
            fmt = f"{minutes} minutes and {seconds} seconds"
        else:
            fmt = f"{seconds} seconds"

        return fmt

    @commands.command()
    async def change_user(self, ctx, user: discord.Member = None, mongo_string : str = None):
        if ctx.author.id in Config.OWNERIDS:
            eval("Config.USERS.update_one({'user_id': user.id}, %s)" % mongo_string)

    @commands.command()
    async def change_clan(self, ctx, name: str = None, mongo_string: str = None):
        if ctx.author.id in Config.OWNERIDS:
            eval("Config.CLANS.update_one({'name': name}, %s)" % mongo_string)







def setup(bot):
    bot.add_cog(Essentials(bot))
