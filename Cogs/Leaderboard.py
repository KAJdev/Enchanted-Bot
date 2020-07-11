import pymongo
import asyncio
import Config
import discord
import datetime
from discord.ext import commands, tasks
import math
import logging
import Utils


class Leaderboard(commands.Cog):

    async def add_reactions(self, page, msg, field, total):
        dic = {'power': 670881187387932683, 'rubies': 676177832963211284,
               'battles': 670882198450339855, 'coins': 676181520062349322, 'xp': 707853397310701638}
        del dic[field]
        if page > 1:
            await msg.add_reaction("⬅️")
        if total > page:
            await msg.add_reaction("➡️")
        for not_field in dic.values():
            emoji = self.bot.get_emoji(not_field)
            await msg.add_reaction(emoji)

    def skiplimit(self, page_size, page_num, field):
        """returns a set of documents belonging to page number `page_num`
        where size of each page is `page_size`.
        """
        # Calculate number of documents to skip
        skips = page_size * (page_num - 1)

        # Skip and limit
        cursor = Config.USERS.find({}).sort([(field, pymongo.DESCENDING)]).skip(skips).limit(page_size)

        # Return documents
        return [x for x in cursor]

    def __init__(self, bot):
        self.bot = bot

    async def restart_leaderboard(self, page, field, msg, total, ctx):
        if total < page:
            page = total
        docs = self.skiplimit(10, page, field)
        embed = discord.Embed(title="Leaderboard", description="", color=Config.MAINCOLOR)
        embed.set_footer(text="Page " + str(page) + " of " + str(total))
        index = 0
        emoji = {'power': "<:mana:670881187387932683>", 'rubies': "<:ruby:676177832963211284>",
                 'battles': "<:battle:670882198450339855>", 'coins': "<:Coin:676181520062349322>", 'xp': "<:xp:707853397310701638>"}
        for doc in docs:
            index += 1
            try:
                user = await self.bot.fetch_user(doc['user_id'])
            except:
                print("wtf")

            embed.description += str(index) + " | " + str(doc[field]) + emoji[field] + " **" + user.name + "** \n"
        await msg.edit(embed=embed)
        routine = self.bot.loop.create_task(self.add_reactions(page, msg, field, total))
        def check(reaction, user):
            return reaction.me and reaction.message.id == msg.id and user.id != self.bot.user.id
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            dic = {'power': 670881187387932683, 'rubies': 676177832963211284,
                   'battles': 670882198450339855, 'coins': 676181520062349322, 'xp': 707853397310701638}
            if str(reaction) == "➡️":
                page += 1
            elif str(reaction) == "⬅️":
                page -= 1
            else:
                for key, value in dic.items():
                    if reaction.emoji.id == value:
                        field = key
            routine.cancel()
            await msg.clear_reactions()
            await self.restart_leaderboard(page, field, msg, total, ctx)
        except asyncio.TimeoutError:
            routine.cancel()
            await msg.delete()
            await ctx.message.delete()

    @commands.command(aliases=['top'])
    async def leaderboard(self, ctx, page: int = 1):
        total = math.ceil(Config.USERS.count_documents({}) / 10)
        if total < page:
            page = total
        field = "power"
        docs = self.skiplimit(10, page, field)
        embed = discord.Embed(title="Leaderboard", description="", color=Config.MAINCOLOR)
        embed.set_footer(text="Page " + str(page) + " of " + str(total))
        index = 0
        emoji = {'power': "<:mana:670881187387932683>", 'rubies': "<:ruby:676177832963211284>", 'battles': "<:battle:670882198450339855>", 'coins': "<:Coin:676181520062349322>"}
        for doc in docs:
            index += 1
            try:
                user = await self.bot.fetch_user(doc['user_id'])
            except:
                print("wtf")

            embed.description += str(index) + " | "+str(doc[field])+emoji[field]+" **" + user.name + "** \n"
        msg = await ctx.send(embed=embed)
        routine = self.bot.loop.create_task(self.add_reactions(page, msg, field, total))
        def check(reaction, user):
            return reaction.me and reaction.message.id == msg.id and user.id != self.bot.user.id
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            dic = {'power': 670881187387932683, 'rubies': 676177832963211284,
                   'battles': 670882198450339855, 'coins': 676181520062349322, 'xp': 707853397310701638}
            if str(reaction) == "➡️":
                page += 1
            elif str(reaction) == "⬅️":
                page -= 1
            else:
                for key, value in dic.items():
                    if reaction.emoji.id == value:
                        field = key
            routine.cancel()
            await msg.clear_reactions()
            await self.restart_leaderboard(page, field, msg, total, ctx)
        except asyncio.TimeoutError:
            routine.cancel()
            await msg.delete()
            await ctx.message.delete()



def setup(bot):
    bot.add_cog(Leaderboard(bot))
