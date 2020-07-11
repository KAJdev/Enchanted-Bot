import asyncio

import discord
from discord.ext import commands

import Utils
import Config

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, prefix=None):
        """Changes the prefix"""

        if prefix is None:
            prefix = Utils.fetch_prefix(ctx)

            embed = discord.Embed(
                title="Prefix",
                description=f"Current prefix: `{prefix}`",
                color=Config.MAINCOLOR,
            )

            return await ctx.send(embed=embed)

        if len(prefix) > 5:
            embed = discord.Embed(
                title="Prefix",
                description="The prefix can't be longer than 5 characters.",
                color=Config.MAINCOLOR,
            )

            return await ctx.send(embed=embed)

        struct = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        if struct is None:
            Utils.insert_guild(ctx)

        Config.SERVERS.update_one(
            {"guild_id": ctx.guild.id}, {"$set": {"prefix": prefix}}
        )

        embed = discord.Embed(
            title="Prefix",
            description=f"The bot will now use `{prefix}` as prefix.",
            color=Config.MAINCOLOR,
        )

        return await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx):
        """BlackList.Pro amirite"""

        server = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        if server is None:
            Utils.insert_guild(ctx)
            server = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        blacklist = server["channel_blacklist"]

        mentions = [f"<#{c}>" for c in blacklist]

        embed = discord.Embed(title="Blacklist", color=Config.MAINCOLOR)

        embed.add_field(
            name="Current Blacklisted Channels", value=", ".join(mentions) if mentions else "None"
        )

        await ctx.send(embed=embed)

    @blacklist.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def add(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """Add a channel to the blacklist"""

        if not channels:
            return await ctx.send("I couldn't find any channels in your command.")

        server = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        if server is None:
            Utils.insert_guild(ctx)
            server = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        already_blacklisted = server["channel_blacklist"]

        merge = [c.id for c in channels if c.id not in already_blacklisted]
        new_blacklist = already_blacklisted + merge

        mentions = [f"<#{c}>" for c in new_blacklist]

        Config.SERVERS.find_one_and_update(
            {"guild_id": ctx.guild.id}, {"$set": {"channel_blacklist": new_blacklist}}
        )

        embed = discord.Embed(
            title="Blacklist",
            description=f"Successfully added to the blacklist!",
            color=Config.MAINCOLOR,
        )

        embed.add_field(name="Current Blacklisted Channels", value=", ".join(mentions))

        await ctx.send(embed=embed)

    @blacklist.command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """Remove a channel from the blacklist"""

        if not channels:
            return await ctx.send("I couldn't find any channels in your command.")

        server = Config.SERVERS.find_one({"guild_id": ctx.guild.id})

        if server is None:
            return await ctx.send("This server doesn't have a blacklist.")

        already_blacklisted = server["channel_blacklist"]

        blacklist = already_blacklisted.copy()

        [blacklist.remove(c.id) for c in channels if c.id in already_blacklisted]

        mentions = [f"<#{c}>" for c in blacklist]

        Config.SERVERS.find_one_and_update(
            {"guild_id": ctx.guild.id}, {"$set": {"channel_blacklist": blacklist}}
        )

        embed = discord.Embed(
            title="Blacklist",
            description=f"Successfully removed from the blacklist!",
            color=Config.MAINCOLOR,
        )
        if len(mentions) != 0:
            embed.add_field(name="Current Blacklisted Channels", value=", ".join(mentions))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Settings(bot))
