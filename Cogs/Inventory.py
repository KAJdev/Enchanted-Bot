import asyncio
import logging
import random

import Config
import discord
from discord.ext import commands
import Utils


class Inventory(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.upgrading_users = []

    @commands.command()
    async def make_item(self, ctx, effect=None, emoji:str=None, cost:int=None, type:str=None, *, name:str=None):
        if ctx.author.id not in Config.OWNERIDS:
            return
        prefix = Utils.fetch_prefix(ctx)
        if None in [emoji, cost, type, name] or type not in ['chest', 'title', 'armor', 'weapon']:
            await ctx.send(f"You need to use this command like this: `{prefix}make_item <effect> <emoji> <cost> <type> <name>`. The ID will be generated automatically. Types are:\narmor, weapon, chest, title")
        else:
            Config.ITEMS.insert_one({'name': name, 'cost': cost, 'effect': effect, 'type': type, 'emoji': emoji})
            await ctx.send(embed=discord.Embed(color=Config.MAINCOLOR, title="Item created!"))

    @commands.command(aliases=['inv', 'inventory', 'item', 'i'])
    async def items(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        if len(account['inventory']) < 1:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Items",
                                  description="You have no items. Obtain Coins and purchase items from the store.")
        else:
            embed = discord.Embed(title="Items", description="", color=Config.MAINCOLOR)
            if account['armor'] is not None:
                embed.description += "**Armor:** " + account['armor']['emoji'] + " " + account['armor'][
                    'name'] + " | +`" + str(account['armor']['effect']) + "` defense\n"
            else:
                embed.description += "**Armor:** *empty...*\n"

            if account['weapon'] is not None:
                embed.description += "**Weapon:** " + account['weapon']['emoji'] + " " + account['weapon'][
                    'name'] + " | +`" + str(account['weapon']['effect']) + "` strength\n\n"
            else:
                embed.description += "**Weapon:** *empty...*\n\n"
            embed.description += "Bag space: " + str(len(account['inventory'])) + "/25 total items"
            i = 1
            for item in account['inventory']:
                if item['type'] in ['weapon', 'armor']:
                    type_string = "effect"
                    if item['type'] == "armor":
                        type_string = "armor"
                    elif item['type'] == "weapon":
                        type_string = "strength"
                    value_string = "**+`" + str(item['effect']) + "` " + type_string + "**"
                    value_string += "\n⌞ level `" + str(item['level']) + "/" + str(item['max']) + "` "
                    if item['level'] < item['max']:
                        value_string += "**`" + prefix + "upgrade " + str(i) + "`**"
                    value_string += "\n⌞ durability `" + str(item['current_durability']) + "/" + str(item['durability']) + "` "
                    embed.add_field(name=str(i) + " | " + item['emoji'] + " " + item['name'], value=value_string)
                elif item['type'] == "good":
                    embed.add_field(name=str(i) + " | " + item['emoji'] + " " + item['name'], value="Trade these goods with other players")
                else:
                    embed.add_field(name=str(i) + " | " + item['emoji'] + " " + item['name'], value="Item")
                i += 1
        embed.set_footer(text=f"Use {prefix}armor <name> or {prefix}weapon <name> to equip items.")
        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command()
    async def drop(self, ctx, *, index = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        try:
            index = int(index)
            index -= 1
        except:
            embed = discord.Embed(title="Wait a second",
                                  description="You must use an item number. Use a number from 1 to " + str(len(account['inventory'])) + ". See all your item numbers with `]items`",
                                  color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        if index is None:
            embed = discord.Embed(title="Wait a second",
                                      description="You cannot drop nothing. Use a number from 1 to " + str(len(account['inventory'])),
                                      color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        if index > len(account['inventory']) - 1 or index < 0:
            embed = discord.Embed(title="You don't have that item",
                                  description="You rummaged through your bag, but could not find the item you were looking for. (use number 1-"+str(len(account['inventory']))+")",
                                  color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        temp = Utils.get_account(ctx.author.id)
        i = temp['inventory'].pop(index)
        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'inventory': temp['inventory']}})
        embed = discord.Embed(title=i['emoji'] + " " + i['name'],
                              description="This item was dropped by " + ctx.author.name + "\nReact to pick it up.",
                              color=discord.Color.gold())
        embed.set_author(name="Dropped Item")
        if account['weapon'] is not None:
            if i['name'] == account['weapon']['name']:
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'weapon': None}})
        if account['armor'] is not None:
            if i['name'] == account['armor']['name']:
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'armor': None}})

        if msg is not None:
            await msg.edit(embed=embed)
        else:
            msg = await ctx.send(embed=embed)
        Config.DROPPED_ITEMS.insert_one(
            {'dropper': ctx.author.id, 'item': i, 'message': msg.id, 'channel': msg.channel.id,
             'guild': msg.guild.id})
        emoji = self.bot.get_emoji(707863240956444702)
        await msg.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        dropped_item = Config.DROPPED_ITEMS.find_one({'message': payload.message_id})
        if dropped_item is not None:
            account = Utils.get_account(payload.user_id)
            if account is not None:
                if len(account['inventory']) > 24:
                    message = await self.bot.get_channel(dropped_item['channel']).fetch_message(dropped_item['message'])
                    await message.channel.send("<@" + str(payload.user_id) + ">, You can't fit any more items in your bag!")
                    return
            else:
                message = await self.bot.get_channel(dropped_item['channel']).fetch_message(dropped_item['message'])
                await message.channel.send("<@" + str(payload.user_id) + ">, You can't pick up this item.")
                return
            Config.DROPPED_ITEMS.delete_one({'message': payload.message_id})
            message = await self.bot.get_channel(dropped_item['channel']).fetch_message(dropped_item['message'])
            embed = message.embeds[0]
            user = await self.bot.fetch_user(payload.user_id)
            embed.description = "Item has been picked up by " + user.name
            Config.USERS.update_one({'user_id': user.id}, {'$push': {'inventory': dropped_item['item']}})
            await message.edit(embed=embed)
            await message.clear_reactions()


    @commands.command()
    async def armor(self, ctx, *, name: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if name in [None, ""]:
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'armor': None}})
            if account['armor'] is not None:
                embed = discord.Embed(title="You took your " + account['armor']['name'] + " off",
                                      description="You feel less secure, but you can see the sun again.",
                                      color=Config.MAINCOLOR)
            else:
                embed = discord.Embed(title="You took off nothing",
                                      description="You took off nothing... What an odd action...",
                                      color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        if name.lower() not in [x['name'].lower() for x in account['inventory']]:
            embed = discord.Embed(title="You don't have that item",
                                  description="You rummaged through your bag, but could not find the item you were looking for.",
                                  color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        for i in account['inventory']:
            if name.lower() == i['name'].lower():

                # check if right item is of right type
                if i['type'] != "armor":
                    embed = discord.Embed(title="That looks odd...",
                                          description="You tried to put a non-descript item on and wear it as armor... but it didn't look good and wasn't practical so you took it off.",
                                          color=Config.MAINCOLOR)
                    if msg is not None:
                        await msg.edit(embed=embed)
                    else:
                        await ctx.send(embed=embed)
                    return
                if account['armor'] == i:
                    embed = discord.Embed(title="Don't you already have that on?",
                                          description="You took off your " + i['name'] + " and put it back on again.",
                                          color=Config.MAINCOLOR)
                    if msg is not None:
                        await msg.edit(embed=embed)
                    else:
                        await ctx.send(embed=embed)
                    return

                if account['armor'] is None:
                    embed = discord.Embed(title="You put on your " + i['name'],
                                          description="You are now ready for battle, with your " + i[
                                              'name'] + " on, you look valiant, and unbeatable.",
                                          color=Config.MAINCOLOR)
                else:
                    embed = discord.Embed(
                        title="You took off your " + account['armor']['name'] + " and put on your " + i['name'],
                        description="You are now ready for battle, with your " + i[
                            'name'] + " on, you look valiant, and unbeatable.",
                        color=Config.MAINCOLOR)
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'armor': i}})
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
        embed = discord.Embed(title="You don't have that item",
                              description="You rummaged through your bag, but could not find the item you were looking for.",
                              color=Config.MAINCOLOR)
        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)
        return

    @commands.command(aliases=['w', 'sword'])
    async def weapon(self, ctx, *, name: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if name in [None, ""]:
            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'weapon': None}})
            if account['weapon'] is not None:
                embed = discord.Embed(title="You put your " + account['weapon']['name'] + " Away",
                                      description="Your bag is now hefty, but your arms feel better not carrying that around.",
                                      color=Config.MAINCOLOR)
            else:
                embed = discord.Embed(title="You put nothing away",
                                      description="You dropped nothing into your bag...",
                                      color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        if name.lower() not in [x['name'].lower() for x in account['inventory']]:
            embed = discord.Embed(title="You don't have that item",
                                  description="You rummaged through your bag, but could not find the item you were looking for.",
                                  color=Config.MAINCOLOR)
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        for i in account['inventory']:
            if name.lower() == i['name'].lower():

                # check if right item is of right type
                if i['type'] != "weapon":
                    embed = discord.Embed(title="That looks odd...",
                                          description="You tried to swing around a non-descript item, but it didn't feel like it would be useful in battle so you put it back in your bag",
                                          color=Config.MAINCOLOR)
                    if msg is not None:
                        await msg.edit(embed=embed)
                    else:
                        await ctx.send(embed=embed)
                    return
                if account['weapon'] == i:
                    embed = discord.Embed(title="You already have that in your hand.",
                                          description="You stared at your " + i[
                                              'name'] + " in your hand, and grasped it firmly. Ready to fight.",
                                          color=Config.MAINCOLOR)
                    if msg is not None:
                        await msg.edit(embed=embed)
                    else:
                        await ctx.send(embed=embed)
                    return

                if account['weapon'] is None:
                    embed = discord.Embed(title="You dug your " + i['name'] + " out of your bag.",
                                          description="You are now ready for battle, holding your " + i[
                                              'name'] + " you feel like you can defeat anyone.",
                                          color=Config.MAINCOLOR)
                else:
                    embed = discord.Embed(
                        title="You put your " + account['weapon']['name'] + " back into your bag, and grabbed your " +
                              i['name'],
                        description="You are now ready for battle, holding your " + i[
                            'name'] + " you feel like you can defeat anyone.",
                        color=Config.MAINCOLOR)
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'weapon': i}})
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
        embed = discord.Embed(title="You don't have that item",
                              description="You rummaged through your bag, but could not find the item you were looking for.",
                              color=Config.MAINCOLOR)
        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)
        return

    async def do_upgrade_loop(self, ctx, selected_item, selected_index, account, msg):

        cost = Utils.calc_item_upgrade_cost(selected_item['level'], selected_item['cost_scale'])
        more_effect = round(selected_item['upgrade_amount'], 1)
        embed = discord.Embed(
            title="Upgrade `" + selected_item['name'] + "` to level `" + str(selected_item['level'] + 1) + "`?",
            description=
            "Your Rubies: `" + str(account['rubies']) + "`\n" +
            "Cost: `" + str(cost) + "` " + Config.EMOJI['ruby']
            + f"\nLevel: `{selected_item['level']}` → `{selected_item['level'] + 1}`"
            + f"\nEffect: `{selected_item['effect']}` → `{round(selected_item['effect'] + more_effect, 1)}`"
            + "\n\n*Click the reaction to upgrade\nwait to cancel*", color=Config.MAINCOLOR)
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✅")

        def check(reaction, user):
            return reaction.message.id == msg.id and user.id == ctx.author.id and reaction.me

        try:
            if account['rubies'] < cost:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have enough rubies to upgrade this item...",
                                      color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, selected_item, msg

            if selected_item['level'] >= selected_item['max'] and 'phantom' not in selected_item.keys():
                cost = Utils.calc_item_upgrade_cost(selected_item['level'], selected_item['cost_scale'])
                embed = discord.Embed(
                    title="Repair `" + selected_item['name'] + "` for `" + str(cost) + "` Rubies?",
                    description=
                    "Your Rubies: `" + str(account['rubies']) + "`\n" +
                    "Cost: `" + str(cost) + "` " + Config.EMOJI['ruby']
                    + f"\nDurability: `{selected_item['current_durability']}` → `{selected_item['durability']}`"
                    + "\n\n*Click the reaction to upgrade\nwait to cancel*", color=Config.MAINCOLOR)
                if msg is None:
                    msg = await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                await msg.add_reaction("✅")

                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                await reaction.remove(user)

                if random.randint(0, 3) == 0:
                    account['inventory'][selected_index]['durability'] += 5
                account['inventory'][selected_index]['current_durability'] = account['inventory'][selected_index]['durability']

                if account[selected_item['type']] is not None:
                    if account[selected_item['type']]['name'].lower() == selected_item['name'].lower():
                        account[selected_item['type']] = account['inventory'][selected_index]

                Config.USERS.update_one({'user_id': ctx.author.id}, {
                    '$set': {'inventory': account['inventory'], selected_item['type']: account[selected_item['type']]},
                    '$inc': {'rubies': -cost}})
                return False, cost, more_effect, 1, account['inventory'][selected_index], msg

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            await reaction.remove(user)

            account['inventory'][selected_index]['level'] += 1
            if random.randint(0, 3) == 0:
                account['inventory'][selected_index]['durability'] += 5
            account['inventory'][selected_index]['current_durability'] = account['inventory'][selected_index]['durability']
            account['inventory'][selected_index]['effect'] += more_effect
            account['inventory'][selected_index]['effect'] = round(account['inventory'][selected_index]['effect'], 1)
            account['rubies'] -= cost

            if selected_item['level'] >= selected_item['max'] and 'phantom' in selected_item.keys():
                if selected_item['tier'] == 'phantom':
                    embed = discord.Embed(title="Wait a second",
                                          description="A Phantom tier item cannot be upgraded anymore.",
                                          color=Config.MAINCOLOR)
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    await asyncio.sleep(3)
                    return False, 0, 0, 0, selected_item, msg
                account['inventory'][selected_index]['name'] = selected_item['phantom']['name']
                account['inventory'][selected_index]['emoji'] = selected_item['phantom']['emoji']
                account['inventory'][selected_index]['tier'] = "phantom"
                if account[selected_item['type']] is not None:
                    if account[selected_item['type']]['name'].lower() == selected_item['name'].lower():
                        account[selected_item['type']] = account['inventory'][selected_index]

                Config.USERS.update_one({'user_id': ctx.author.id}, {
                    '$set': {'inventory': account['inventory'], selected_item['type']: account[selected_item['type']]},
                    '$inc': {'rubies': -cost}})
                embed = discord.Embed(title="The spirits whisper...",
                                          description="the " + selected_item['name'] + " starts shaking, souls from the depths now encapsulated within the vessel. They will fight for ***you*** now... You pick up your **" + selected_item['phantom']['name'] + "** "+selected_item['phantom']['emoji']+". The item is reborn.",
                                          color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(10)
                return False, cost, more_effect, 1, account['inventory'][selected_index], msg

            if account[selected_item['type']] is not None:
                if account[selected_item['type']]['name'].lower() == selected_item['name'].lower():
                    account[selected_item['type']] = account['inventory'][selected_index]

            Config.USERS.update_one({'user_id': ctx.author.id}, {
                '$set': {'inventory': account['inventory'], selected_item['type']: account[selected_item['type']]},
                '$inc': {'rubies': -cost}})
            return True, cost, more_effect, 1, account['inventory'][selected_index], msg
        except asyncio.TimeoutError:
            return False, 0, 0, 0, selected_item, msg

    @commands.command(aliases=['u'])
    async def upgrade(self, ctx, item=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if ctx.author.id in self.upgrading_users:
            embed = discord.Embed(title="Wait a second",
                                  description="You are already upgrading. Please use that message, or wait until the timeout.",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if item is None:
            embed = discord.Embed(title="Wait a second",
                                  description="Please provide a name or index of the item you would like to upgrade",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            item = int(item)
        except:
            item = str(item)

        selected_item = None
        selected_index = None

        # User chose index instead of name
        if isinstance(item, int):
            if item > len(account['inventory']) or item < 1:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have that many items. Try a number from 1-" + str(
                                          len(account['inventory'])),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return

            selected_item = account['inventory'][item - 1].copy()
            selected_index = item - 1
            
            if selected_item['type'] not in ['armor', 'weapon']:
                embed = discord.Embed(title="Wait a second",
                                      description="You can only upgrade weapons and armor!",
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return

        # User chose name instead of index
        elif isinstance(item, str):
            pass

        if selected_index is not None and selected_item is not None:
            if ctx.author.id not in self.upgrading_users:
                self.upgrading_users.append(ctx.author.id)
            archived_item = selected_item.copy()
            do_continue = True
            total_cost = 0
            total_effect = 0
            total_levels = 0
            while do_continue:
                try:
                    do_continue, more_cost, more_levels, more_effect, selected_item, msg = await self.do_upgrade_loop(
                        ctx, selected_item, selected_index, account, msg)
                    total_cost += more_cost
                    total_effect += more_effect
                    total_levels += more_levels
                except:
                    pass
            try:
                if archived_item['level'] == selected_item['level']:
                    await msg.delete()
                    await ctx.message.delete()
                    return
                await msg.clear_reactions()
                embed = discord.Embed(
                    title="Upgraded `" + selected_item['name'] + "` from level `" + str(
                        archived_item['level']) + "` to `" + str(selected_item['level']) + "`",
                    description=
                    "Total Cost: `" + str(total_cost) + "` " + Config.EMOJI['ruby']
                    + f"\nLevel: `{archived_item['level']}` → `{selected_item['level']}`"
                    + f"\nEffect: `{archived_item['effect']}` → `{selected_item['effect']}`",
                    color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
            except:
                logging.error("Issue with upgrading. Error editing message.")
            finally:
                if ctx.author.id in self.upgrading_users:
                    self.upgrading_users.remove(ctx.author.id)


def setup(bot):
    bot.add_cog(Inventory(bot))
