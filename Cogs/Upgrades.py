import asyncio
import Config
import discord
from discord.ext import commands
import Utils


class Upgrades(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def restart_upgrade(self, msg, ctx, stat, account):
        account = Utils.get_account(ctx.author.id)
        if stat is None:
            mystring = "Health: " + str(account['stats']['health']) + " | +1 for " + str(Utils.calc_health_upgrade_cost(account['stats']['health'])) + " "+Config.EMOJI['ruby']
            mystring += "\nStrength: " + str(account['stats']['strength']) + " | +1 for " + str(Utils.calc_strength_upgrade_cost(account['stats']['strength'])) + " "+Config.EMOJI['ruby']
            mystring += "\nDefense: " + str(account['stats']['defense']) + " | +1 for " + str(Utils.calc_defense_upgrade_cost(account['stats']['defense'])) + " "+Config.EMOJI['ruby']
            mystring += "\nEndurance: " + str(account['stats']['endurance']) + " | +1 for " + str(Utils.calc_endurance_upgrade_cost(account['stats']['endurance'])) + " "+Config.EMOJI['ruby']
            embed = discord.Embed(color = Config.MAINCOLOR, title="Upgrade stats", description="You have " + str(account['rubies']) + " "+Config.EMOJI['ruby']+"\n\n" + mystring)
            await msg.edit(embed=embed)

            def check(reaction, user):
                return user.id == ctx.author.id and reaction.message.id == msg.id and reaction.me

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
                await reaction.remove(user)

                if str(reaction) == "🇭":
                    if account['rubies'] >= Utils.calc_health_upgrade_cost(account['stats']['health']):

                        account['rubies'] -= Utils.calc_health_upgrade_cost(account['stats']['health'])
                        account['stats']['health'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Health stat from `" + str(account['stats']['health'] - 1) + "` to `" + str(account['stats']['health']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇸":
                    if account['rubies'] >= Utils.calc_strength_upgrade_cost(account['stats']['strength']):

                        account['rubies'] -= Utils.calc_strength_upgrade_cost(account['stats']['strength'])
                        account['stats']['strength'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Strength stat from `" + str(account['stats']['strength'] - 1) + "` to `" + str(account['stats']['strength']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇩":
                    if account['rubies'] >= Utils.calc_defense_upgrade_cost(account['stats']['defense']):

                        account['rubies'] -= Utils.calc_defense_upgrade_cost(account['stats']['defense'])
                        account['stats']['defense'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Defense stat from `" + str(account['stats']['defense'] - 1) + "` to `" + str(account['stats']['defense']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇪":
                    if account['rubies'] >= Utils.calc_endurance_upgrade_cost(account['stats']['endurance']):

                        account['rubies'] -= Utils.calc_endurance_upgrade_cost(account['stats']['endurance'])
                        account['stats']['endurance'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Endurance stat from `" + str(account['stats']['endurance'] - 1) + "` to `" + str(account['stats']['endurance']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)

            except asyncio.TimeoutError:
                await ctx.message.delete()
                await msg.delete()

    @commands.command(aliases=['u'])
    async def upgrade(self, ctx, stat:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        if stat is None:
            mystring = "Health: " + str(account['stats']['health']) + " | +1 for " + str(Utils.calc_health_upgrade_cost(account['stats']['health'])) + " "+Config.EMOJI['ruby']
            mystring += "\nStrength: " + str(account['stats']['strength']) + " | +1 for " + str(Utils.calc_strength_upgrade_cost(account['stats']['strength'])) + " "+Config.EMOJI['ruby']
            mystring += "\nDefense: " + str(account['stats']['defense']) + " | +1 for " + str(Utils.calc_defense_upgrade_cost(account['stats']['defense'])) + " "+Config.EMOJI['ruby']
            mystring += "\nEndurance: " + str(account['stats']['endurance']) + " | +1 for " + str(Utils.calc_endurance_upgrade_cost(account['stats']['endurance'])) + " "+Config.EMOJI['ruby']
            embed = discord.Embed(color = Config.MAINCOLOR, title="Upgrade stats", description="You have " + str(account['rubies']) + " "+Config.EMOJI['ruby']+"\n\n" + mystring)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                msg = await ctx.send(embed=embed)

            await msg.add_reaction("🇭")
            await msg.add_reaction("🇸")
            await msg.add_reaction("🇩")
            await msg.add_reaction("🇪")

            def check(reaction, user):
                return user.id == ctx.author.id and reaction.message.id == msg.id and reaction.me

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
                await reaction.remove(user)

                if str(reaction) == "🇭":
                    if account['rubies'] >= Utils.calc_health_upgrade_cost(account['stats']['health']):

                        account['rubies'] -= Utils.calc_health_upgrade_cost(account['stats']['health'])
                        account['stats']['health'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Health stat from `" + str(account['stats']['health'] - 1) + "` to `" + str(account['stats']['health']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇸":
                    if account['rubies'] >= Utils.calc_strength_upgrade_cost(account['stats']['strength']):

                        account['rubies'] -= Utils.calc_strength_upgrade_cost(account['stats']['strength'])
                        account['stats']['strength'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Strength stat from `" + str(account['stats']['strength'] - 1) + "` to `" + str(account['stats']['strength']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇩":
                    if account['rubies'] >= Utils.calc_defense_upgrade_cost(account['stats']['defense']):

                        account['rubies'] -= Utils.calc_defense_upgrade_cost(account['stats']['defense'])
                        account['stats']['defense'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Defense stat from `" + str(account['stats']['defense'] - 1) + "` to `" + str(account['stats']['defense']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                elif str(reaction) == "🇪":
                    if account['rubies'] >= Utils.calc_endurance_upgrade_cost(account['stats']['endurance']):

                        account['rubies'] -= Utils.calc_endurance_upgrade_cost(account['stats']['endurance'])
                        account['stats']['endurance'] += 1
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'stats': account['stats'], 'rubies': account['rubies']}})
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Upgraded Endurance stat from `" + str(account['stats']['endurance'] - 1) + "` to `" + str(account['stats']['endurance']) + "`.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)
                    else:
                        await msg.edit(embed=discord.Embed(title="Upgrade stats", description="Cannot afford upgrade.", color = Config.MAINCOLOR))
                        await asyncio.sleep(3)
                        await self.restart_upgrade(msg, ctx, stat, account)

            except asyncio.TimeoutError:
                await ctx.message.delete()
                await msg.delete()


def setup(bot):
    bot.add_cog(Upgrades(bot))
