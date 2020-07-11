import asyncio
import datetime
import random

import Config
import discord
from discord.ext import commands
import Utils


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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

    def get_day_of_year(self):
        return datetime.datetime.now().timetuple().tm_yday

    @commands.command(aliases=['market', 'npc', 'store'])
    async def shop(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        shop_string = "Howdy! You wanna spend yer coins here huh? Well, if you have enough, you can browse today's stock and pick out somthing you like eh?\n\n**Your Coins: %s %s**\n**Your Crowns: %s %s**\n\n" % (account['coins'], Config.EMOJI['coin'], account["crowns"], Config.EMOJI['crown'])
        random.seed(self.get_day_of_year())
        weapon_items = random.sample(Utils.get_all_weapons(), random.randint(4, 6))
        cosmetic_items = random.sample(Utils.get_all_cosmetics(), 3)
        #wood_item = random.sample(list(Config.ITEMS.find({'tier': "wood"})), 1)
        #items.insert(0, wood_item)
        prefix = Utils.fetch_prefix(ctx)

        midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=1)

        embed = discord.Embed(
            description=shop_string,
            color=Config.MAINCOLOR,
            timestamp=midnight
        )

        for item in weapon_items:
            if item['type'] in ['armor', 'weapon']:
                string = "Effect"
                if item['type'] == "armor":
                    string = "Defense"
                elif item['type'] == "weapon":
                    string = "Strength"
                # shop_string = shop_string + f"%s **%s**\n+`%s` %s | Max level: `%s`\n%s %s\n`{prefix}buy %s`\n\n" % (item['emoji'], item['name'], str(item['effect']), string, str(item['max']), self.commify(item['cost']), Config.EMOJI['coin'], item['name'])
                embed.add_field(name=item['emoji'] + " **" + item['name'] + "**", value=f"+`%s` %s\nMax: `lvl %s`\n%s %s\n`{prefix}buy %s`\n\n" % (str(item['effect']), string, str(item['max']), self.commify(item['cost']), Config.EMOJI['coin'], item['name']))
        embed.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", value="🔱 __Cosmetics:__", inline=False)
        for item in cosmetic_items:
            if item['type'] == "image":
                embed.add_field(name="**" + item['name'] + "**",value=f"[Image](%s)\n%s %s\n`{prefix}buy %s`\n\n" % (item["effect"],self.commify(item['cost']),Config.EMOJI['crown'], item['name']))
            elif item['type'] == "emote":
                embed.add_field(name="**" + item['effect'] + "**",value=f"%s %s\n`{prefix}buy %s`\n\n" % (self.commify(item['cost']),Config.EMOJI['crown'], item['name']))
            elif item['type'] == "color":
                embed.add_field(name="**" + item['name'] + "**",value=f"%s\n%s %s\n`{prefix}buy %s`\n\n" % (item["effect"],self.commify(item['cost']),Config.EMOJI['crown'], item['name']))
            else:
                embed.add_field(name=item['emoji'] + " **" + item['name'] + "**",value=f"%s %s\n`{prefix}buy %s`\n\n" % (self.commify(item['cost']),Config.EMOJI['crown'], item['name']))
                # shop_string = shop_string + f"%s **%s**\n%s %s\n`{prefix}buy %s`\n\n" % (
                # item['emoji'], item['name'], str(item['cost']), Config.EMOJI['coin'], item['name'])

        embed.set_footer(text="Items reset ")
        if msg is None:
            await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)


    @commands.command(aliases=['purchase', 'comprar'])
    async def buy(self, ctx, *, id:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        random.seed(self.get_day_of_year())
        item = random.sample(Utils.get_all_weapons(), random.randint(4, 6)) + random.sample(Utils.get_all_cosmetics(), 3)

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
        
        if item['type'] in ['title', 'color', 'image', 'emote']:
            if account['crowns'] >= item['cost']:
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$inc': {'crowns': -item['cost']}})
            else:
                await ctx.send(embed=discord.Embed(title="Not enough coins!", description="You don't have enough crowns to purchase this item!", color=Config.MAINCOLOR))
                return
            if {'type': item['type'], 'value': item['effect']} in account["cosmetics"]:
                await ctx.send(embed=discord.Embed(title="No duplicating!", description="You already have this item!", color=Config.MAINCOLOR))
                return
            await ctx.send(embed=discord.Embed(title="Here you go.", description="You purchased `" + item['name'] + f"`. You can view and use your title with `{prefix}cosmetics`", color=Config.MAINCOLOR))
        else:
            if account['coins'] >= item['cost']:
                if len(account['inventory']) > 24:
                    await ctx.send(embed=discord.Embed(title="Your bag is full!",
                                                    description="You don't have enough space in your bag for this item!",
                                                    color=Config.MAINCOLOR))
                    Config.USERS.update_one({'user_id': ctx.author.id}, {'$inc': {'coins': -item['cost']}})
            else:
                await ctx.send(embed=discord.Embed(title="Not enough coins!", description="You don't have enough coins to purchase this item!", color=Config.MAINCOLOR))
                return
            await ctx.send(embed=discord.Embed(title="Here you go.", description="You purchased `" + item['name'] + f"`. You can view and use your title with `{prefix}inventory`", color=Config.MAINCOLOR))

        
        if item['type'] in ["armor", "weapon"]:
            item['level'] = 1
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'inventory': item}})
        elif item['type'] == "chest":
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$inc': {'chests': item['effect']}})
        elif item['type'] == 'emote':
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': {'type': 'emote', 'value': item['effect']}}})
        elif item['type'] == 'title':
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': {'type': 'title', 'value': item['effect']}}})
        elif item['type'] == 'color':
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': {'type': 'color', 'name': item["name"], 'value': item['effect']}}})
        elif item['type'] == 'image':
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': {'type': 'image', 'name': item["name"], 'value': item['effect']}}})
        else:
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'inventory': item}})


def setup(bot):
    bot.add_cog(Shop(bot))
