import asyncio

import Config
import discord
from discord.ext import commands
import Utils


class Profile(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['player', 'p'])
    async def profile(self, ctx, member:discord.Member=None):
        if member is not None and Utils.get_account(member.id) is None:
            await ctx.send(embed=discord.Embed(title="User has no profile", description=member.name+" does not have a profile.", color = Config.MAINCOLOR))
            return
        if member is None:
            member = ctx.author
        msg, account = await Utils.get_account_lazy(self.bot, ctx, member.id)
        if account is None:
            return

        rank = Utils.get_rank_object(account['power'])
        prefix = Utils.fetch_prefix(ctx)

        if account["selected_embed_color"] is None:
            color = Config.MAINCOLOR
        else:
            color = int(account["selected_embed_color"]["value"], 0)
        embed=discord.Embed(title="Player Profile", color = color, description="Health: " + str(account['stats']['health']) + "\nStrength: " + str(account['stats']['strength']) + "\nDefense: " + str(account['stats']['defense']) + "\nEndurance: " + str(account['stats']['endurance']))
        embed.set_author(name=str(member.name), icon_url=str(member.avatar_url))
        if account["selected_embed_image"] is not None:
            embed.set_thumbnail(url=account["selected_embed_image"]["value"])
        if 'xp' not in account:
            account['xp'] = 0
        embed.set_footer(text=f"use {prefix}s to look at spells, {prefix}b to battle, {prefix}c to open chests, and {prefix}items to see items")
        embed.add_field(name="Class "+Config.EMOJI['book'], value=account['class'])
        embed.add_field(name="Crowns "+Config.EMOJI['crown'], value=str("{:,}".format(round(account['crowns']))))
        embed.add_field(name="Rubies "+Config.EMOJI['ruby'], value=str("{:,}".format(account['rubies'])))
        embed.add_field(name="Chests "+Config.EMOJI['chest'], value=str(account['chests']))
        embed.add_field(name="Keys "+Config.EMOJI['key'], value=str(account['keys']) + "/10")
        embed.add_field(name="Battles "+Config.EMOJI['battle'], value=str(account['battles']))
        embed.add_field(name="Coins "+Config.EMOJI['coin'], value=str("{:,}".format(account['coins'])))
        embed.add_field(name="Rank "+rank['emoji'], value=rank['name'])
        embed.add_field(name="Title "+Config.EMOJI['scroll'], value=str(account['selected_title']))


        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)
        #if needsTutorial == True:
        #    Tutorial.tutorial(self, ctx, member)

    @commands.command()
    async def rebirth(self, ctx):
        account = Utils.get_account(ctx.author.id)
        if account is None:
            await ctx.send(embed=discord.Embed(title="huh.", description="You don't appear to have played before... I cannot re-birth you.", color = Config.MAINCOLOR))
            return
        else:
            embed = discord.Embed(title="Please select your class to be re-birthed, or do nothing to cancel", description="use the emojis to choose",
                                  color=Config.MAINCOLOR)
            embed.set_footer(text="Message will be timeout in 30 seconds")
            for _class in Utils.get_all_classes():
                embed.add_field(name=_class['name'] + " " + _class['emote'], value=_class['desc'])
            msg = await ctx.send(embed=embed)
            for _class in Utils.get_all_classes():
                await msg.add_reaction(_class['emote'])

            def check(reaction, user):
                return user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and reaction.me and reaction.emoji in [
                    x['emote'] for x in Utils.get_all_classes()]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
                for _class in Utils.get_all_classes():
                    if _class['emote'] == str(reaction):
                        account['slots'] = [0, 1, None, None]
                        account['keys'] = 0
                        account['power'] = round(account['power'] * 0.8)
                        account['stats'] = _class['stats']
                        account['class'] = _class['name']
                        # account['grown'] = []
                        # account['seeds'] = []
                        # account['crops'] = [{'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}]
                        account['spells'] = [0, 1]
                        i = 0
                        double = False

                        for cosmetic in account['cosmetics']:
                            if cosmetic['type'] == 'title':
                                if cosmetic['value'] == " the " + _class['name']:
                                    double = True
                        if not double:
                            account['cosmetics'].append({'type': 'title', 'value': " the " + _class['name']})
                        account['selected_title'] = " the " + _class['name']
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': account})

                        rank = Utils.get_rank_object(account['power'])
                        prefix = Utils.fetch_prefix(ctx)

                        if account["selected_embed_color"] is None:
                            color = Config.MAINCOLOR
                        else:
                            color = int(account["selected_embed_color"]["value"], 0)
                        embed = discord.Embed(title="Welcome back to the world...", color=color,
                                              description="Health: " + str(
                                                  account['stats']['health']) + "\nStrength: " + str(
                                                  account['stats']['strength']) + "\nDefense: " + str(
                                                  account['stats']['defense']) + "\nEndurance: " + str(
                                                  account['stats']['endurance']))
                        embed.set_author(name=str(ctx.author.name), icon_url=str(ctx.author.avatar_url))
                        if account["selected_embed_image"] is not None:
                            embed.set_thumbnail(url=account["selected_embed_image"]["value"])
                        embed.set_footer(text=f"use {prefix}s to look at spells, {prefix}b to battle, {prefix}c to open chests, and {prefix}items to see items")
                        embed.add_field(name="Class "+Config.EMOJI['book'], value=account['class'])
                        embed.add_field(name="Crowns "+Config.EMOJI['crown'], value=str("{:,}".format(round(account['crowns']))))
                        embed.add_field(name="Rubies "+Config.EMOJI['ruby'], value=str("{:,}".format(account['rubies'])))
                        embed.add_field(name="Chests "+Config.EMOJI['chest'], value=str(account['chests']))
                        embed.add_field(name="Keys "+Config.EMOJI['key'], value=str(account['keys']) + "/10")
                        embed.add_field(name="Battles "+Config.EMOJI['battle'], value=str(account['battles']))
                        embed.add_field(name="Coins "+Config.EMOJI['coin'], value=str("{:,}".format(account['coins'])))
                        embed.add_field(name="Rank "+rank['emoji'], value=rank['name'])
                        embed.add_field(name="Title "+Config.EMOJI['scroll'], value=str(account['selected_title']))

                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        return

            except asyncio.TimeoutError:
                await ctx.message.delete()
                await msg.delete()
                return None, None


def setup(bot):
    bot.add_cog(Profile(bot))
