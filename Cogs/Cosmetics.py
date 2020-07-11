import asyncio

import Config
import discord
from discord.ext import commands
import Utils
from Paginator import EmbedPaginatorSession
import paypalrestsdk
from paypalrestsdk import Payment
from paypalrestsdk import Order
import flask

paypalrestsdk.configure({
    'mode': 'sandbox',  # sandbox or live
    'client_id': 'CLIENT_ID',
    'client_secret': 'CLIENT_SECRET'})


class Cosmetics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cosmetic', 'titles', 't', 'colors'])
    async def cosmetics(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if account['selected_embed_image'] is not None:
            image = account['selected_embed_image']["name"]
        else:
            image = None
        prefix = Utils.fetch_prefix(ctx)
        titles = discord.Embed(title="Titles", description="", color=Config.MAINCOLOR)
        titles.description += "**Selected Title:** " + str(account['selected_title']) + "\n\n"
        emotes = discord.Embed(title="Emotes", description="", color=Config.MAINCOLOR)
        images = discord.Embed(title="Embed Images", description="", color=Config.MAINCOLOR)
        images.description += "**Selected Profile Image:** " + str(image) + "\n\n"
        colors = discord.Embed(title="Embed Colors", description="", color=Config.MAINCOLOR)
        colors.description += "**Selected Profile Color:** " + str(account['selected_embed_color']["name"]) + "\n\n"

        titles.set_footer(text=f"Get more cosmetics from {prefix}shop")
        emotes.set_footer(text=f"Get more cosmetics from {prefix}shop")
        images.set_footer(text=f"Get more cosmetics from {prefix}shop")
        colors.set_footer(text=f"Get more cosmetics from {prefix}shop")

        titles.set_author(name="Your Cosmetics", icon_url=str(ctx.author.avatar_url))
        emotes.set_author(name="Your Cosmetics", icon_url=str(ctx.author.avatar_url))
        images.set_author(name="Your Cosmetics", icon_url=str(ctx.author.avatar_url))
        colors.set_author(name="Your Cosmetics", icon_url=str(ctx.author.avatar_url))

        tit = 0
        emo = 0
        col = 0
        img = 0
        for cosmetic in account['cosmetics']:
            if cosmetic['type'] == "title":
                tit += 1
                titles.description += "> " + str(tit) + f" | `{cosmetic['value']}` \n"
            elif cosmetic['type'] == "emote":
                emo += 1
                emotes.description += "> " + str(emo) + f" | {cosmetic['value']} \n"
            if cosmetic['type'] == "image":
                img += 1
                images.description += "> " + str(img) + f" | `{cosmetic['name']}` \n"
            if cosmetic['type'] == "color":
                col += 1
                colors.description += "> " + str(col) + f" | `{str(cosmetic['name'])}` \n"

        titles.description += f"\n\n*use {prefix}select title <index> to select a title to use*"
        emotes.description += f"\n\n*use {prefix}chat <index> to chat during battle*"
        images.description += f"\n\n*use {prefix}select image <index> to select a embed image to use*"
        colors.description += f"\n\n*use {prefix}select color <index> to select a embed color to use*"

        if msg is None:
            paginator = EmbedPaginatorSession(ctx, titles, emotes, images, colors)
            await paginator.run()
        else:
            await msg.edit(embed=titles)

    @commands.group()
    async def select(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(title="Select", color=Config.MAINCOLOR,
                                  description=f"Branches:\n `{prefix}select title (number of title you want to select)`\n`{prefix}select image (number of embed image you want to select)`\n`{prefix}select color (number of embed color you want to select)`")
            await ctx.send(embed=embed)

    @select.command()
    async def title(self, ctx, choice: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            titles = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'title':
                    titles.append(cosmetic)
            if choice > len(titles) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                    len(titles)) + " Titles. Try using a number 1-" + str(len(titles)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_title'] = titles[choice]['value']
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'selected_title': account['selected_title']}})
            embed = discord.Embed(title="Title Selected",
                                  description="You have changed your title to **" + account['selected_title'] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...",
                                  description="Thats not a title index. Try using a number 1-" + str(len(titles)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @select.command()
    async def image(self, ctx, choice: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            images = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'image':
                    images.append(cosmetic)
            if choice > len(images) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                    len(images)) + " Images. Try using a number 1-" + str(len(images)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_embed_image'] = {'name': str(images[choice]['name']),
                                                   'value': str(images[choice]['value'])}
            Config.USERS.update_one({'user_id': ctx.author.id},
                                    {'$set': {'selected_embed_image': account['selected_embed_image']}})
            embed = discord.Embed(title="Image Selected", description="You have changed your Embed Image to **" +
                                                                      account['selected_embed_image']["name"] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...",
                                  description="Thats not a image index. Try using a number 1-" + str(len(images)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @select.command()
    async def color(self, ctx, choice: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            embed = discord.Embed(title="Hmmmm...", description="Please type a number.", color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            choice = int(choice)
            colors = []
            for cosmetic in account['cosmetics']:
                if cosmetic['type'] == 'color':
                    colors.append(cosmetic)
            if choice > len(colors) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                    len(colors)) + " Colors. Try using a number 1-" + str(len(colors)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                account['selected_embed_color'] = {'name': str(colors[choice]['name']),
                                                   'value': str(colors[choice]['value'])}
            Config.USERS.update_one({'user_id': ctx.author.id},
                                    {'$set': {'selected_embed_color': account['selected_embed_color']}})
            embed = discord.Embed(title="Color Selected", description="You have changed your Embed Color to **" +
                                                                      account['selected_embed_color']["name"] + "**",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...",
                                  description="Thats not a color index. Try using a number 1-" + str(len(colors)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @commands.command(aliases=['crown', 'donate'])
    async def crowns(self, ctx):
        embed = discord.Embed(title="Crowns",
                              description="\n\nPlease type the number by the amount you want\n```md\n1. <$1.00> 100 Crowns\n2. <$2.00> 210 Crowns (10 bonus)\n3. <$5.00> 600 Crowns (100 bonus)\n4. <$10.00> 1,300 Crowns (300 bonus)\n```",
                              color=Config.MAINCOLOR)
        og_message = await ctx.send(embed=embed)

        def check(msg):
            return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id and msg.content.lower() in [
                '1', '2', '3', '4']

        try:

            # Paypal integration wasn't completed, as KAJ7#0001 was removed from the team before they could finish
            # the feature. And so that's why this is a mess.

            msg = await self.bot.wait_for('message', timeout=200, check=check)
            choice_to_payment = {'1':
                Payment({
                    "intent": "order",

                    # Set payment method
                    "payer": {
                        "payment_method": "paypal"
                    },

                    # Set redirect urls
                    "redirect_urls": {
                        "return_url": "http://localhost:3000/process",
                        "cancel_url": "http://localhost:3000/cancel"
                    },

                    # Set transaction object
                    "transactions": [{
                        "amount": {
                            "total": "1.00",
                            "currency": "USD",
                            "details": {
                                "subtotal": "1.00",
                                "tax": "0.00"
                            }
                        },
                        "description": "Crowns for usage on Enchanted Cosmetics.",
                        "invoice_number": "23423522324234234",
                        "payment_options": {
                            "allowed_payment_method": "INSTANT_FUNDING_SOURCE"
                        },
                        "item_list": {
                            "items": [{
                                "name": "Crown",
                                "quantity": "100",
                                "price": "0.01",
                                "tax": "0.00",
                                "sku": "1",
                                "currency": "USD"
                            }]
                        }
                    }]
                })
            }

            # Create payment
            if choice_to_payment[msg.content.lower()].create():
                # Extract redirect url
                for link in choice_to_payment[msg.content.lower()].links:
                    if link.method == "REDIRECT":
                        # Capture redirect url
                        redirect_url = str(link.href)
                        await ctx.send(embed=discord.Embed(title="Complete Purchase", color=Config.MAINCOLOR,
                                                           description="To complete this purchase, please click this link:\n\n> " + redirect_url))
                        return
            else:
                await ctx.send(embed=discord.Embed(title="Failed to create order", color=Config.ERRORCOLOR,
                                                   description="Please try again later"))
                return


        except asyncio.TimeoutError:
            await og_message.delete()
            return


def setup(bot):
    bot.add_cog(Cosmetics(bot))
