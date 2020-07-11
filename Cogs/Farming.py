import random
import Config
import discord
import datetime
from discord.ext import commands, tasks
import logging
import Utils


class Farming(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.grow.start()

    def cog_unload(self):
        self.grow.cancel()
        logging.info("Shutdown growth system")

    @commands.command(aliases=['food', 'crops', 'grow', 'farm'])
    async def berries(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        embed = discord.Embed(title=ctx.author.name + "'s Farm", color = Config.MAINCOLOR)
        all_crops = Utils.get_all_crops()
        embed.set_footer(text="type ]plant 1-6 <crop> to plant a seed")
        for crop in account['crops']:
            if crop['growth'] == -1:
                embed.add_field(name=Config.GROWTH[crop['growth']], value="Dead Crop")
            elif crop['growth'] == 0:
                embed.add_field(name=Config.GROWTH[crop['growth']], value="Empty Field")
            else:
                try:
                    embed.add_field(name=Config.GROWTH[crop['growth']], value=all_crops[crop['type']]['name'])
                except:
                    embed.add_field(name="!", value="Null crop")

        if len(account['seeds']) > 0:
            embed.description = "**Seed Pouch**\n\n"
            for crop in account['seeds']:
                embed.description += "> " + str(crop['amount']) + " " + all_crops[crop['id']]['emoji'] + " " + all_crops[crop['id']]['name'] + "\n"
        else:
            embed.description = "*Your seed pouch is empty, try opening some chests*\n"

        if len(account['grown']) > 0:
            revised_grown = []
            for berry in account['grown']:
                did_add = False
                for _ in revised_grown:
                    if _['id'] == berry:
                        _['amount'] += 1
                        did_add = True
                if not did_add:
                    revised_grown.append({'id': berry, 'amount': 1})
            embed.description += "\n**Berry Stockpile**\n\n"
            for crop in revised_grown:
                embed.description += "> " + str(crop['amount']) + " " + all_crops[crop['id']]['berry'] + " " + all_crops[crop['id']]['name'] + "\n"


        if msg is None:
            await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)

    @commands.command()
    async def plant(self, ctx, field:int=1, *, plant:str=""):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if field > 6 or field < 1:
            embed=discord.Embed(title="Hmmmm...", description="You don't appear to have that field. Try using the numbers 1-6.", color = Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        if account['crops'][field - 1]['growth'] not in [0, -1]:
            embed=discord.Embed(title="Hmmmm...", description="That field already has something growing in it.", color = Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        plant_obj = Utils.get_plant_by_name(plant)
        if plant_obj is None:
            embed = discord.Embed(title="Hmmmm...", description="I haven't heard of that crop...", color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        to_delete = None
        did_plant = False
        for seed in account['seeds']:
            if seed['id'] == plant_obj['id']:
                seed['amount'] -= 1
                did_plant = True
                account['crops'][field - 1] = {'type': plant_obj['id'], 'growth': 1, 'timestamp': datetime.datetime.utcnow()}
                if seed['amount'] < 1:
                    to_delete = seed
        if to_delete is not None:
            account['seeds'].remove(to_delete)

        if did_plant:
            Config.USERS.update_one({'user_id': ctx.author.id},
                                    {'$set': {'crops': account['crops'], 'seeds': account['seeds']}})
            embed = discord.Embed(title=plant_obj['name'] + " was planted",
                                  description="You have successfully planted a " + plant_obj[
                                      'name'] + " on your farm! Check back often to see how it's doing!",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
        else:
            embed = discord.Embed(title="Hmmmm...", description="You don't seem to have that crop! Try opening some chests to get the seed.",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @commands.command()
    async def harvest(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        harvested = []
        for _ in range(6):
            if account['crops'][_]['growth'] > 3:
                account['grown'].append(account['crops'][_]['type'])
                harvested.append(account['crops'][_]['type'])
                account['crops'][_] = {'type': 0, 'growth': 0}
        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'crops': account['crops'], 'grown': account['grown']}})
        all_crops = Utils.get_all_crops()
        embed=discord.Embed(title="Harvest", description="", color=Config.MAINCOLOR)
        embed.description += "*You harvested:*\n\n"
        if len(harvested) > 0:
            for harvest in harvested:
                embed.description += all_crops[harvest]['berry'] + " " + all_crops[harvest]['name'] + "\n"
        else:
            embed.description = "*You couldn't harvest anything because nothing was ripe...*"
        if msg is None:
            await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)


    @tasks.loop(minutes=20)
    async def grow(self):
        logging.info("Starting growth routine")
        all_crops = Utils.get_all_crops()
        for user in Config.USERS.find({}):
            for plant in user['crops']:
                if plant['growth'] < 4 and plant['growth'] not in [-1, 0]:
                    delta = datetime.datetime.utcnow() - plant['timestamp']
                    if (delta.total_seconds() / 60) >= all_crops[plant['type']]['growth']:
                        if random.randint(0, 5) == 0:
                            plant['growth'] = -1
                            logging.info("GROWTH ROUTINE | Killed plant")
                        else:
                            plant['growth'] += 1
                            plant['timestamp'] = datetime.datetime.utcnow()
                            logging.info("GROWTH ROUTINE | Incremented crop growth")
            Config.USERS.update_one({'user_id': user['user_id']}, {'$set': {'crops': user['crops']}})
        logging.info("Completed Growth routine")




def setup(bot):
    bot.add_cog(Farming(bot))
