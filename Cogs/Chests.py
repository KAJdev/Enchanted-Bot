import asyncio
import Config
import discord
from discord.ext import commands
import logging
import Utils
import random

class Chests(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def restart_open_menu(self, ctx, msg):
        account = Utils.get_account(ctx.author.id)
        if account['chests'] < 1:
            embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
            embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
            embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
            await msg.edit(embed=embed)
            await msg.delete(delay=30)
            return
        else:
            mystring = str(account['chests']) + " Chests."

        embed = discord.Embed(colour=Config.MAINCOLOR, description=mystring+"\n\n**React below to open a chest**")
        embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
        embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
        await msg.edit(embed=embed)

        #await msg.add_reaction(self.bot.get_emoji(670881966861844490))

        def check(reaction, user):
            if user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and isinstance(reaction.emoji, discord.Emoji):
                return reaction.emoji.id == 671574326364995595
            else:
                return False
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout = 30.0, check=check)
            #await reaction.message.clear_reactions()
            await reaction.remove(user)
            await self.open_crate(account, ctx, msg, embed)

        except asyncio.TimeoutError:
            try:
                await msg.delete()
                await ctx.message.delete()
            except:
                logging.info("Error deleting message of user. Don't have the permission or message does not exist.")

    async def open_crate(self, account, ctx, msg, embed):
        account = Utils.get_account(ctx.author.id)
        if account['chests'] < 1:
            embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
            embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
            embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=30)
            return


        spell = Utils.win_spell(account)
        all_titles = Config.TITLES.copy()
        new_title = random.choice(all_titles)
        i = len(all_titles) + 5
        while new_title in account['titles']:
            i -= 1
            new_title = random.choice(all_titles)
            if i < 0:
                new_title = None
                break
        account['chests'] -= 1
        if account['chests'] < 1:
            account['chests'] = 0
        if spell is not None and random.randint(0, 5) == 0:
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'spells': spell['id']}, '$set': {'chests': account['chests']}})
            end_embed=discord.Embed(title='Chest', color = Config.MAINCOLOR, description = "You opened a chest and got:\n\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Damage] [ "+str(spell['cost'])+" Cost] [ "+str(spell['scalling'])+" scaling]")
        elif False:
            seed = Utils.win_seed()
            account_ = Utils.get_account(ctx.author.id)
            did_add = False
            for user_seed in account_['seeds']:
                if user_seed['id'] == seed['id']:
                    did_add = True
                    user_seed['amount'] += 1
            if not did_add:
                account_['seeds'].append({'id': seed['id'], 'amount': 1})
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'seeds': account_['seeds'], 'chests': account['chests']}})
            end_embed=discord.Embed(title='Chest', color = Config.MAINCOLOR, description = "You opened a chest and got:\n\n> 1 "+seed['emoji']+" "+seed['name']+" Seed.")
        elif random.randint(0, 6) == 0 and new_title is not None:
            Config.USERS.update_one({'user_id': ctx.author.id},
                                    {'$push': {'titles': new_title}, '$set': {'chests': account['chests']}})
            end_embed = discord.Embed(title='Chest', color=Config.MAINCOLOR,
                                      description="You opened a chest and got:\n\n> `" + new_title + "` Title")
        elif random.randint(0, 1) == 0:
            coins = random.randint(10, 20)
            Config.USERS.update_one({'user_id': ctx.author.id},
                                    {'$set': {'chests': account['chests']}, '$inc': {'coins': coins}})
            end_embed = discord.Embed(title='Chest', color=Config.MAINCOLOR,
                                      description="You opened a chest and got:\n\n> " + str(coins) + " " +
                                                  Config.EMOJI['coin'])
        else:
            rubies = random.randint(20, 40)
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'chests': account['chests']}, '$inc': {'rubies': rubies}})
            end_embed=discord.Embed(title='Chest', color = Config.MAINCOLOR, description = "You opened a chest and got:\n\n> " + str(rubies) + " "+ Config.EMOJI['ruby'])

        end_embed.set_footer(text='Going to menu in 5 seconds')

        slot_embed = discord.Embed(title='Chest', color=Config.MAINCOLOR)
        slot_embed.set_image(url="https://i.pinimg.com/originals/20/c0/27/20c0271883ddbbeda8aaa106b9c57066.gif")
        await msg.edit(embed=slot_embed)
        await asyncio.sleep(2)

        await msg.edit(embed=end_embed)

        await asyncio.sleep(5)

        await self.restart_open_menu(ctx, msg)

    @commands.command(aliases=['crates', 'c', 'o', 'chests', 'chest'])
    async def open(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if account['chests'] < 1:
            embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
            embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
            embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=30)
            return
        else:
            mystring = str(account['chests']) + " Chests."

        embed = discord.Embed(colour=Config.MAINCOLOR, description=mystring+"\n\n**React below to open a chest**")
        embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
        embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)

        await msg.add_reaction(self.bot.get_emoji(671574326364995595))

        def check(reaction, user):
            if user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and isinstance(reaction.emoji, discord.Emoji):
                return reaction.emoji.id == 671574326364995595
            else:
                return False
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout = 30.0, check=check)
            #await reaction.message.clear_reactions()
            await reaction.remove(user)
            await self.open_crate(account, ctx, msg, embed)

        except asyncio.TimeoutError:
            try:
                await msg.delete()
                await ctx.message.delete()
            except:
                logging.info("Error deleteing message of user. Don't have permission or message does not exist.")

def setup(bot):
    bot.add_cog(Chests(bot))
