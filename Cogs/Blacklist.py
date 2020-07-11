import math

import pymongo
import asyncio
import Config
import discord
import datetime
from discord.ext import commands, tasks
import logging
import Utils


class Blacklist(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blacklist_channel = None

    @commands.command()
    async def ban(self, ctx, user:discord.User=None, *, reason:str=None):
        if ctx.author.id in Config.OWNERIDS:
            if user is not None:
                if Config.BLACKLIST.find_one({'user_id': user.id}) is None:
                    Config.BLACKLIST.insert_one({'user_id': user.id, 'date': datetime.datetime.utcnow(), 'reason': reason})
                    embed = discord.Embed(title="Blacklist Update")
                    embed.add_field(name="User Added", value=user.mention)
                    if self.blacklist_channel is None:
                        self.blacklist_channel = self.bot.get_channel(715408045127106630)
                    await self.blacklist_channel.send(embed=embed)
                else:
                    await ctx.send("User already blacklisted")
                    return
            else:
                await ctx.send("please mention a user")
                return

    @commands.command()
    async def pardon(self, ctx, user:discord.User=None):
        if ctx.author.id in Config.OWNERIDS:
            if user is not None:
                if Config.BLACKLIST.find_one({'user_id': user.id}) is not None:
                    Config.BLACKLIST.delete_one({'user_id': user.id})
                    embed = discord.Embed(title="Blacklist Update")
                    embed.add_field(name="User Removed", value=user.mention)
                    if self.blacklist_channel is None:
                        self.blacklist_channel = self.bot.get_channel(715408045127106630)
                    await self.blacklist_channel.send(embed=embed)
                else:
                    await ctx.send("User not blacklisted")
                    return
            else:
                await ctx.send("please mention a user")
                return

    @commands.command()
    async def lookup(self, ctx, user: discord.User = None):
        if ctx.author.id in Config.OWNERIDS:
            reports = list(Config.REPORTS.find({'user_id': user.id}))
            unique = []
            for report in reports:
                if report['reporter'] not in [x['reporter'] for x in unique]:
                    unique.append(report)
            if user is not None:
                found = Config.BLACKLIST.find_one({'user_id': user.id})
                if found is not None:
                    embed = discord.Embed(title="Blacklisted User", description=user.mention)
                    embed.add_field(name="Reason", value=str(found['reason']))
                    if len(reports) > 0:
                        embed.add_field(name="reports", value="Total: %s\nUnique: %s" % (str(len(reports)), str(len(unique))))
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Blacklisted User", description="Not found")
                    if len(reports) > 0:
                        embed.add_field(name="reports", value="Total: %s\nUnique: %s" % (str(len(reports)), str(len(unique))))
                    await ctx.send(embed=embed)
                    return
            else:
                embed = discord.Embed(title="Blacklisted User", description="Not found")
                await ctx.send(embed=embed)
                return

    @commands.command()
    async def report(self, ctx, user:discord.User=None, *, reason:str=None):
        if user is None:
            await ctx.send("You must specify a user to report.")
        else:
            Config.REPORTS.insert_one({'user_id': user.id, 'reason': reason, 'date': datetime.datetime.utcnow(), 'reporter': ctx.author.id})
            await ctx.send("User has been reported.")

    @commands.command()
    async def dashboard(self, ctx):
        recent = list(Config.REPORTS.find({}).sort("date", pymongo.DESCENDING).limit(10))
        top_ = list(Config.REPORTS.find({}))
        top = []
        for report in top_:
            found = False
            for user in top:
                if user['user_id'] == report['user_id']:
                    user['reports'].append(report)
                    found = True
                    break
            if not found:
                top.append({'user_id': report['user_id'], 'reports': [report]})

        def top_sort(e):
            return len(e['reports'])

        top.sort(key=top_sort, reverse=True)

        embed = discord.Embed(title="Report Dashboard", color = Config.MAINCOLOR)
        recent_string = ""
        for report in recent:
            try:
                reported = await self.bot.fetch_user(report['user_id'])
                reported = reported.name
            except:
                reported = str(report['user_id'])

            try:
                author = await self.bot.fetch_user(report['reporter'])
                author = author.name
            except:
                author = str(report['reporter'])
            recent_string += "**%s** ```\n%s\n``` reported by %s\n\n" % (reported, report['reason'], author)
        embed.add_field(name="Recent Reports", value=recent_string)

        top_string = ""
        top_limit = 15
        for report in top:
            if top_limit < 1:
                break
            try:
                reported = await self.bot.fetch_user(report['user_id'])
                reported = reported.name
            except:
                reported = str(report['user_id'])
            top_string += "**%s** - %s reports\n" % (reported, str(len(report['reports'])))
            top_limit -= 1
        embed.add_field(name="Top Reported Users", value=top_string)
        await ctx.send(embed=embed)






def setup(bot):
    bot.add_cog(Blacklist(bot))
