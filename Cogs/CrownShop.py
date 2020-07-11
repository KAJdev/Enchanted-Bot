import asyncio
import datetime
import random

import Config
import discord
from discord.ext import commands
import Utils


class CrownShop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_day_of_year(self):
        return datetime.datetime.now().timetuple().tm_yday

    def commify(self, n):
        if n is None: return None
        n = str(n)
        if '.' in n:
            dollars, cents = n.split('.')
        else:
            dollars, cents = n, None

        r = []
        for i, c in enumerate(str(dollars)[::-1]):
            if i and (not (i % 3)):
                r.insert(0, ',')
            r.insert(0, c)
        out = ''.join(r)
        if cents:
            out += '.' + cents
        return out

    @commands.command(aliases=['market', 'npc', 'store'])
    async def crownshop(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        shop_string = "**Your Crowns: %s %s**\n\n" % (account['crowns'], Config.EMOJI['crown'])
        random.seed(self.get_day_of_year())
        items = random.sample(list(Config.CROWNSHOP.find({})), random.randint(4, 6))
        prefix = Utils.fetch_prefix(ctx)

        midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=1)

        embed = discord.Embed(
            description=shop_string,
            color=Config.MAINCOLOR,
            timestamp=midnight
        )

        for item in items:
            embed.add_field(name=item['emoji'] + " **" + item['name'] + "**",value=f"%s %s\n`{prefix}cbuy %s`\n%s\n\n" % (self.commify(item['cost']),Config.EMOJI['crown'], item['name'], item['description']))

        embed.set_footer(text="New shop ")
        if msg is None:
            await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)

    @commands.command(aliases=['cb'])
    async def cbuy(self, ctx, *, id:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        random.seed(self.get_day_of_year())
        items = random.sample(list(Config.CROWNSHOP.find({})), random.randint(4, 6))

        if id is None:
            await ctx.send(embed=discord.Embed(title="<a:lg:670720658166251559> I can't seem to find that item", description="Please specify the item that you would like to buy..", color=Config.MAINCOLOR))
            return

        item = None
        for i in items:
            if i['name'].lower() == id.lower():
                item = i
        if item is None:
            await ctx.send(embed=discord.Embed(title="<a:lg:670720658166251559> I can't seem to find that item", description="That item isn't on sale today.", color=Config.MAINCOLOR))
            return

        if account['crowns'] >= item['cost']:
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$inc': {'crowns': -item['cost']}})
            #if item['type'] == "chest":
            #    Config.USERS.update_one({'user_id': ctx.author.id}, {'$inc': {'chests': item['effect']}})
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': item}})
            await ctx.send(embed=discord.Embed(title="Pleasure.", description="You purchased `" + item['name'] + f"`. You can use your cosmetics with `{prefix}cosmetics`", color=Config.MAINCOLOR))
            return
        else:
            await ctx.send(embed=discord.Embed(title="Not enough crowns!", description="You don't have enough crowns to purchase this item! Get more crowns with `]crowns`", color=Config.MAINCOLOR))
            return


def setup(bot):
    bot.add_cog(CrownShop(bot))
