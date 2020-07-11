import asyncio
import statistics

import Config
import math
import discord
import datetime
from discord.ext import commands
import logging
import Utils
import random


class Bosses(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.battling_users = []
        self.waiting_users = []
        self.active_channels = []
        self.bosses = 0

    def get_numbers(self, number_string):
        final_string = ""
        for character in number_string:
            try:
                int(character)
                final_string += character
            except:
                continue
        return int(final_string)

    async def drops(self, message):
        type = random.choice(['ruby', 'coin', 'xp', 'chest'])
        if type == 'ruby':
            amount = random.randint(1, 3)
            embed = discord.Embed(color=Config.MAINCOLOR, title="Rubies",
                                  description="There are " + str(amount) + " " + Config.EMOJI[
                                      'ruby'] + " on the ground. React first to pick them up!")
            ruby = self.bot.get_emoji(676177832963211284)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(ruby)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'rubies': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Rubies picked up by " + user.name,
                                               description=user.name + " has picked up the " + str(amount) + " " +
                                                           Config.EMOJI['ruby'] + " rubies"))
        elif type == 'coin':
            amount = random.randint(5, 10)
            embed = discord.Embed(color=Config.MAINCOLOR, title="Coins",
                                  description="There are " + str(amount) + " " + Config.EMOJI[
                                      'coin'] + " on the ground. React first to pick them up!")
            emoji = self.bot.get_emoji(676181520062349322)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'coins': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Coins picked up by " + user.name,
                                               description=user.name + " has picked up the " + str(amount) + " " +
                                                           Config.EMOJI['coin'] + " coins"))
        elif type == 'xp':
            amount = random.randint(20, 50)
            embed = discord.Embed(color=Config.MAINCOLOR, title="XP",
                                  description="There is " + str(amount) + " " + Config.EMOJI[
                                      'xp'] + " on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(707853397310701638)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'xp': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="XP picked up by " + user.name,
                                               description=user.name + " has picked up " + str(amount) + " " +
                                                           Config.EMOJI['xp'] + " XP"))
        elif type == 'chest':
            amount = 1
            embed = discord.Embed(color=Config.MAINCOLOR, title="Chest", description="There is a " + Config.EMOJI[
                'chest'] + " on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(671574326364995595)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'chests': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Chest picked up by " + user.name,
                                               description=user.name + " has picked up the " + Config.EMOJI[
                                                   'chest'] + " Chest"))
        elif type == 'item':
            item = random.choice(list(Config.ITEMS.find({'cost': {'$lt': 6000}})))
            item['level'] = 1
            embed = discord.Embed(color=Config.MAINCOLOR, title="Item",
                                  description="There is a " + item['emoji'] + " **" + item[
                                      'name'] + "** on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(self.get_numbers(item['emoji']))
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            did_pickup = False
            await msg.add_reaction(emoji)

            while not did_pickup:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return

                user_account = Utils.get_account(user.id)
                if user_account is not None:
                    for i in user_account['inventory']:
                        if i['name'] == item['name']:
                            await reaction.remove(user)
                            a_msg = await message.channel.send(user.mention + " You cannot collect an item you already have!")
                            await a_msg.delete(delay=20)
                            continue

                Config.USERS.update_one({'user_id': user.id}, {'$push': {'inventory': item}})

                await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR,
                                                   title=item['emoji'] + " " + item['name'] + " picked up by " + user.name,
                                                   description=user.name + " has picked up the " + item['emoji'] + " **" +
                                                               item['name'] + "**"))
                return

    @commands.Cog.listener()
    async def on_message(self, message):
        #logging.info(f"<{message.author.name}> {message.content}")
        if random.randint(0, 200) == 0:
            await self.drops(message)

    @commands.command()
    async def force_drop(self, ctx):
        await self.drops(ctx.message)

    def change_turn(self, turn, max):
        turn += 1
        if turn > max:
            turn = 0
        return turn

    def clean_up_match(self, turn, match, monster):
        # make sure health and mana are not above max value
        for _ in match:
            if _['health'] > _['account']['stats']['health']:
                _['health'] = _['account']['stats']['health']
            if _['mana'] > _['account']['stats']['endurance']:
                _['mana'] = _['account']['stats']['endurance']

            # make sure strength stats are where they should be
            strength_min  = 0
            if _['account']['weapon'] is not None:
                strength_min = _['account']['weapon']['effect']
            if _['account']['stats']['strength'] < strength_min:
                _['account']['stats']['strength'] = strength_min
            else:
                _['account']['stats']['strength'] = round(_['account']['stats']['strength'], 1)

            # make sure armor stats are where they should be
            armor_min = 0
            if _['account']['armor'] is not None:
                armor_min = _['account']['armor']['effect']
            if _['account']['stats']['defense'] < armor_min:
                _['account']['stats']['defense'] = armor_min
            else:
                _['account']['stats']['defense'] = round(_['account']['stats']['defense'], 1)

        # make sure monster values are in check as well
        if monster['health'] > monster['stats']['health']:
            monster['health'] = monster['stats']['health']
        if monster['mana'] > monster['stats']['endurance']:
            monster['mana'] = monster['stats']['endurance']

        # make sure strength stats are where they should be FOR MONSTER
        strength_min = 0
        if 'weapon' in monster.keys():
            strength_min = monster['weapon']['effect']
        if monster['stats']['strength'] < strength_min:
            monster['stats']['strength'] = strength_min
        else:
            monster['stats']['strength'] = round(monster['stats']['strength'], 1)

        # make sure armor stats are where they should be FOR MONSTER
        armor_min = 0
        if 'armor' in monster.keys():
            armor_min = monster['armor']['effect']
        if monster['stats']['defense'] < armor_min:
            monster['stats']['defense'] = armor_min
        else:
            monster['stats']['strength'] = round(monster['stats']['strength'], 1)

        return turn, match, monster


    async def construct_embeds(self, match, turn, message, monster):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        if turn != len(match):
            embed = discord.Embed(color = Config.MAINCOLOR, description="it is " + match[turn]['user'].name + "'s turn.")
            equipped_string = ""
            for spell in match[turn]['account']['slots']:
                if spell is None:
                    equipped_string += "\n> *Nothing is written on this page...*"
                    continue
                for x in Utils.get_users_spells(match[turn]['account']):
                    if spell == x['id']:
                        spell = x
                if spell is not None:
                    equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost]"
            embed.description += "\n\n**"+match[turn]['user'].name+"'s Spellbook**:" + equipped_string
            weapon_additive_string = ""
            if 'weapon' in monster.keys():
                weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in monster.keys():
                armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            embed.description += "\n\n**" + monster['name'] + "**\nHealth: " + str(monster['health']) + "/" + str(monster['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(monster['mana']) + "/" + str(monster['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(monster['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(monster['stats']['defense']) + armor_additive_string
            for user in match:
                weapon_additive_string = ""
                if user['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(user['account']['weapon']['effect'])+ user['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if user['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(user['account']['armor']['effect']) + user['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value="Health: " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength'])+ weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Boss fight against " + monster['name']
            footer_string = ""
            for effect in match[turn]['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text=match[turn]['user'].name + " gains 3 mana at the beginning of their turn." + footer_string)
            await message.edit(embed=embed)
        else:
            embed = discord.Embed(color = Config.NOTTURN, description="it is " + monster['name'] + "'s turn.")
            equipped_string = ""
            for spell in monster['spells']:
                equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost]"
            embed.description += "\n\n**"+monster['name']+"'s Spellbook**:" + equipped_string
            weapon_additive_string = ""
            if 'weapon' in monster.keys():
                weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in monster.keys():
                armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            embed.description += "\n\n**" + monster['name'] + "**\nHealth: " + str(monster['health']) + "/" + str(monster['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(monster['mana']) + "/" + str(monster['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(monster['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(monster['stats']['defense']) + armor_additive_string
            for user in match:
                weapon_additive_string = ""
                if user['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(user['account']['weapon']['effect'])+ user['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if user['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(user['account']['armor']['effect']) + \
                                             user['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value="Health: " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Boss fight against " + monster['name']
            footer_string = ""
            for effect in monster['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text=monster['name'] + " gains 8 mana at the beginning of their turn." + footer_string)
            await message.edit(embed=embed)

    async def construct_embeds_with_message(self, message, monster, turn, match, text):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        if turn != len(match):
            embed = discord.Embed(color = Config.OK, description=text)
            for user in match:
                weapon_additive_string = ""
                if user['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(user['account']['weapon']['effect'])+ user['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if user['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(user['account']['armor']['effect']) + \
                                             user['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value="Health: " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Boss fight against " + monster['name']
            weapon_additive_string = ""
            if 'weapon' in monster.keys():
                weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in monster.keys():
                armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            embed.description += "\n\n**" + monster['name'] + "**\nHealth: " + str(monster['health']) + "/" + str(monster['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(monster['mana']) + "/" + str(monster['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(monster['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(monster['stats']['defense']) + armor_additive_string
            embed.set_footer(text=match[turn]['user'].name + " is casting a spell.")
            await message.edit(embed=embed)
        else:
            embed = discord.Embed(color = Config.DAMAGE, description=text)
            for user in match:
                weapon_additive_string = ""
                if user['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(user['account']['weapon']['effect'])+ user['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if user['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(user['account']['armor']['effect']) + user['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value="Health: " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Boss fight against " + monster['name']
            weapon_additive_string = ""
            if 'weapon' in monster.keys():
                weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in monster.keys():
                armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            embed.description += "\n\n**" + monster['name'] + "**\nHealth: " + str(monster['health']) + "/" + str(monster['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(monster['mana']) + "/" + str(monster['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(monster['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(monster['stats']['defense']) + armor_additive_string
            embed.set_footer(text=monster['name'] + " is casting a spell.")
            await message.edit(embed=embed)

    async def boss_thread(self, match, message, monster):
        logging.info("Boss thread started: Current threads: " + str(self.bosses))
        match_cache = match.copy()
        await message.clear_reactions()
        monster['health'] = monster['stats']['health']
        monster['mana'] = monster['stats']['endurance']
        embed = discord.Embed(title="Boss found", color=Config.MAINCOLOR,
                              description="[jump](" + message.jump_url + ")")
        one_message = await message.channel.send(", ".join(x['user'].mention for x in match), embed=embed)
        await one_message.delete(delay=10)
        monster['effects'] = []
        for user in match:
            self.battling_users.append(user['user'].id)
            user['health'] = user['account']['stats']['health']
            user['mana'] = user['account']['stats']['endurance']
            user['effects'] = []
            user['afk'] = 0
        turn = random.randint(0, len(match) - 1)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("💤")
        await message.add_reaction("🏳️")
        while len(match) > 0 and monster['health'] > 0 and monster['mana'] > 0:
            restart = False
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    match.remove(user)
                    turn -= 1
                    restart = True
            if turn < 0:
                turn = 0
            if restart:
                continue


            # calculate effects for beginning of round
            for _ in match:
                effects_remove = []
                for effect in _['effects']:
                    _[effect['type']] -= effect['amount']
                    _[effect['type']] = round(_[effect['type']], 1)
                    effect['turns'] -= 1
                    if effect['turns'] < 1:
                        effects_remove.append(effect)
                for effect in effects_remove:
                    _['effects'].remove(effect)

            # restart if needed after effects applied
            restart = False
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    if turn >= match.index(user):
                        turn -= 1
                    match.remove(user)
                    restart = True
            if restart:
                continue

            # effects for monster
            effects_remove = []
            for effect in monster['effects']:
                monster[effect['type']] -= effect['amount']
                monster[effect['type']] = round(monster[effect['type']], 1)
                effect['turns'] -= 1
                if effect['turns'] < 1:
                    effects_remove.append(effect)
            for effect in effects_remove:
                monster['effects'].remove(effect)

            if turn != len(match):
                match[turn]['mana'] += 3
            else:
                monster['mana'] += 8

            # make sure health and mana are not above max value
            for _ in match:
                if _['health'] > _['account']['stats']['health']:
                    _['health'] = _['account']['stats']['health']
                if _['mana'] > _['account']['stats']['endurance']:
                    _['mana'] = _['account']['stats']['endurance']

            # make sure monster values are in check as well
            if monster['health'] > monster['stats']['health']:
                monster['health'] = monster['stats']['health']
            if monster['mana'] > monster['stats']['endurance']:
                monster['mana'] = monster['stats']['endurance']

            if monster['health'] <= 0 or monster['mana'] <= 0:
                break

            await self.construct_embeds(match, turn, message, monster)

            # check if monster's turn
            if turn == len(match):

                # simulate monster thinking lol
                await asyncio.sleep(3)


                if monster['mana'] < 25:
                    turn = self.change_turn(turn, len(match))
                    continue
                else:
                    spell = random.choice(monster['spells'])
                    victim = random.randint(0, len(match) - 1)

                    if spell['type'] not in ["MANA", "DRAIN"]:
                        monster['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        monster['health'] -= spell['cost']

                    # spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round(((spell['damage'] + monster['stats']['strength']) * spell['scalling']) - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[victim]['account']['stats']['defense']) + "` blocked)")

                    elif spell['type'] == "HEAL":
                        monster['health'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" gains `" + str(spell['damage']) + "` health.")

                    elif spell['type'] == "MANA":
                        monster['mana'] += spell['damage']
                        monster['health'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" transforms `" + str(spell['damage']) + "` health into mana.")

                    elif spell['type'] == "DRAIN":
                        monster['mana'] += spell['damage']
                        match[victim]['mana'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" stole `" + str(spell['damage']) + "` mana from "+match[victim]['user'].name+" using `" + str(spell['cost']) + "` health.")

                    elif spell['type'] == "PEN":
                        monster['stats']['strength'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" boosted their Strength from `" + str(monster['stats']['strength'] - spell['damage']) + "` to `"+str(monster['stats']['strength'])+"`")

                    elif spell['type'] == "ARMOR":
                        monster['stats']['defense'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" boosted their Defense from `" + str(monster['stats']['defense'] - spell['damage']) + "` to `"+str(monster['stats']['defense'])+"`")

                    elif spell['type'] == "POISON":
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': round(((spell['damage'] + monster['stats']['strength']) * spell['scalling']) / match[victim]['account']['stats']['defense'], 1)}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == "BLIND":
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': round((spell['damage'] + monster['stats']['strength']) * spell['scalling'] / match[victim]['account']['stats']['defense'], 1)}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + monster['stats']['strength']) * spell['scalling']) - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        monster['health'] += calculated_damage
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" stole `" + str(spell['damage']) + "` health from "+match[victim]['user'].name)

                    elif spell['type'] == "IMPAIR":
                        before_stat = match[victim]['account']['stats']['defense']
                        match[victim]['account']['stats']['defense'] -= spell['damage']
                        if match[victim]['account']['stats']['defense'] < 1:
                            match[victim]['account']['stats']['defense'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. " + match[victim]['user'].name + "'s defense falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['defense']) + "`.")

                    elif spell['type'] == "WEAKEN":
                        before_stat = match[victim]['account']['stats']['strength']
                        match[victim]['account']['stats']['strength'] -= spell['damage']
                        if match[victim]['account']['stats']['strength'] < 1:
                            match[victim]['account']['stats']['strength'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, monster['name'] + " casted **" + spell['name'] + "**. " + match[victim]['user'].name + "'s strength falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['strength']) + "`.")

                    await asyncio.sleep(5)
                    turn = self.change_turn(turn, len(match))
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue

            try:
                reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3}
                def check(payload):
                    if payload.user_id == match[turn]['user'].id and payload.message_id == message.id:
                        if str(payload.emoji) in reaction_dict.keys():
                            return match[turn]['account']['slots'][reaction_dict[str(payload.emoji)]] is not None
                        else:
                            return True
                    else:
                        return False

                temp_msg = await message.channel.fetch_message(message.id)
                reaction = None
                for temp_reaction in temp_msg.reactions:
                    users = await temp_reaction.users().flatten()
                    if match[turn]['user'].id in [x.id for x in users] and temp_reaction.me:
                        reaction = temp_reaction
                        try:
                            await temp_reaction.remove(match[turn]['user'])
                        except:
                            logging.error("Cannot remove emoji (not big deal)")
                if reaction is None:
                    payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                    reaction = payload.emoji

                    try:
                        await message.remove_reaction(payload.emoji, match[turn]['user'])
                    except:
                        logging.error("Cannot remove emoji (not big deal)")

                if str(reaction) == "💤":
                    turn = self.change_turn(turn, len(match))
                    continue
                elif str(reaction) == "🏳️":
                    match[turn]['health'] = 0
                    match[turn]['mena'] = 0
                    turn = self.change_turn(turn, len(match))
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue
                else:
                    spell = Utils.get_spell(match[turn]['account']['class'], match[turn]['account']['slots'][reaction_dict[str(reaction)]])
                    if spell['type'] not in ["MANA", "DRAIN"]:
                        match[turn]['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        match[turn]['health'] -= spell['cost']

                    # spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        monster['health'] -= calculated_damage
                        monster['health'] = round(monster['health'], 1)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(monster['stats']['defense']) + "` blocked)")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "HEAL":
                        match[turn]['health'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" gains `" + str(spell['damage']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "STUN":
                        calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        monster['health'] -= calculated_damage
                        monster['health'] = round(monster['health'], 1)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(monster['stats']['defense']) + "` blocked) the stun failed...")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "MANA":
                        match[turn]['mana'] += spell['damage']
                        match[turn]['health'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" transforms `" + str(spell['damage']) + "` health into mana.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "DRAIN":
                        match[turn]['mana'] += spell['damage']
                        monster['mana'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" stole `" + str(spell['damage']) + "` mana from "+monster['name']+" using `" + str(spell['cost']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "PEN":
                        match[turn]['account']['stats']['strength'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" boosted their Strength from `" + str(match[turn]['account']['stats']['strength'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['strength'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "ARMOR":
                        match[turn]['account']['stats']['defense'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" boosted their Defense from `" + str(match[turn]['account']['stats']['defense'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['defense'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "POISON":
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / monster['stats']['defense'], 1)}
                        monster['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "BLIND":
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / monster['stats']['defense'], 1)}
                        monster['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[turn]['health'] += calculated_damage
                        monster['health'] -= calculated_damage
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" stole `" + str(spell['damage']) + "` health from "+monster['name'])
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "IMPAIR":
                        before_stat = monster['stats']['defense']
                        monster['stats']['defense'] -= spell['damage']
                        if monster['stats']['defense'] < 1:
                            monster['stats']['defense'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. " + monster['name'] + "'s defense falls from `" + str(before_stat) + "` to `" + str(monster['stats']['defense']) + "`.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "WEAKEN":
                        before_stat = monster['stats']['strength']
                        monster['stats']['strength'] -= spell['damage']
                        if monster['stats']['strength'] < 1:
                            monster['stats']['strength'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. " + monster['name'] + "'s strength falls from `" + str(before_stat) + "` to `" + str(monster['stats']['strength']) + "`.")
                        turn = self.change_turn(turn, len(match))

                    await asyncio.sleep(5)
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and turn != len(match):
                    embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                          description="Your battle is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + message.jump_url + ")")
                    timeout_msg = await message.channel.send(match[turn]['user'].mention, embed=embed)
                    await timeout_msg.delete(delay=20)
                    match[turn]['afk'] += 1
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    turn = self.change_turn(turn, len(match))
                    continue
                elif isinstance(e, discord.errors.NotFound):
                    return
                else:
                    match[turn]['mana'] -= 3
        try:
            await message.clear_reactions()
        except:
            logging.error("Cannot remove emoji (not big deal)")

        for player in match_cache:
            broken_items = Utils.decrease_durability(player['account']['user_id'])
            if len(broken_items) > 0:
                embed = discord.Embed(title="Broken Tools", description=player['user'].mention + "! Your " + " and ".join([x['name'] for x in broken_items]) + " broke!", color=Config.MAINCOLOR)
                await message.channel.send(content=player['user'].mention, embed=embed)


        if monster['health'] > 0 and monster['mana'] > 0:
            embed = discord.Embed(color = Config.MAINCOLOR, description="**"+monster['name']+" Has bested the group...**")
            await message.edit(embed=embed)
        else:
            if not monster['titan']:
                amount = random.randint(math.floor(0.3 * len(match_cache)) * 2 + 3, math.floor(0.3 * len(match_cache)) * 2 + 6)
                coins_amount = random.randint(len(match_cache) * 3, (len(match_cache) * 4) + 1)
            else:
                amount = random.randint(math.floor(0.5 * len(match_cache)) * 2 + 5, math.floor(0.5 * len(match_cache)) * 2 + 9)
                coins_amount = random.randint(len(match_cache) * 4, (len(match_cache) * 5) + 1)
            mystring = str(amount) + " "+ Config.EMOJI['key'] + "\n+" + str(coins_amount) + " " + Config.EMOJI['coin']
            for user in match_cache:
                user['account'] = Utils.get_account(user['user'].id)
                user['account']['keys'] += amount
                while user['account']['keys'] > 9:
                    user['account']['keys'] -= 10
                    user['account']['chests'] += 1
                Config.USERS.update_one({'user_id': user['user'].id}, {'$set': {'chests': user['account']['chests'], 'keys': user['account']['keys']}, '$inc': {'coins': coins_amount}})
            if monster['health'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has been killed!**\n\nEveryone gets:\n\n+" + mystring)
            elif monster['mana'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has fainted!**\n\nEveryone gets:\n\n+" + mystring)
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster['name'] + " has been destroyed completely!**\n\nEveryone gets:\n\n+ " + mystring)
            await message.edit(embed=embed)
        for user in match_cache:
            if user['user'].id in self.battling_users:
                self.battling_users.remove(user['user'].id)
        if message.channel.id in self.active_channels:
            self.active_channels.remove(message.channel.id)
        self.bosses -= 1

    @commands.command()
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def boss(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under Maintenance.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.battling_users:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Finding Boss", description="You are already battling a boss. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.waiting_users:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Finding Boss", description="You are already searching for a boss. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.channel.id in self.active_channels:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Finding Boss", description="This channel is already battling a boss. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        self.waiting_users.append(ctx.author.id)
        self.active_channels.append(ctx.channel.id)

        embed=discord.Embed(color=Config.MAINCOLOR, title=ctx.author.name + " Is searching for a boss<a:dots:715134569355018284>", description="The battle will begin in 1 minute. React to join.", timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
        embed.set_footer(text='React with the ✔️ to join | starting at ')
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✔️")
        await msg.add_reaction("❌")
        await msg.add_reaction("⏩")

        countdown = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
        def check(reaction, user):
            return user.id != self.bot.user.id and reaction.message.id == msg.id

        while datetime.datetime.utcnow() < countdown:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
                if str(reaction) == "⏩" and user.id == ctx.author.id:
                    break
                elif str(reaction) == "❌" and user.id == ctx.author.id:
                    await msg.clear_reactions()
                    await msg.edit(embed=discord.Embed(title="Boss Search canceled", color = Config.MAINCOLOR, description=ctx.author.name + " has disbanded the search..."))
                    users = await reaction.users().flatten()
                    if ctx.channel.id in self.active_channels:
                        self.active_channels.remove(ctx.channel.id)
                    for u in users:
                        if u.id in self.waiting_users:
                            self.waiting_users.remove(u.id)
                    if ctx.author.id in self.waiting_users:
                        self.waiting_users.remove(ctx.author.id)
                    return
                elif Utils.get_account(user.id) is None:
                    await reaction.remove(user)
                    error_msg = await ctx.send(embed=discord.Embed(title="You don't have an account", color = Config.MAINCOLOR, description="Type `]profile` to choose a class and react again to join the battle!"))
                    await error_msg.delete(delay=20)
                    continue
                elif user.id in self.waiting_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already searching", color = Config.MAINCOLOR, description="You are already searching for a boss"))
                    await error_msg.delete(delay=20)
                    await reaction.remove(user)
                    continue
                elif user.id in self.battling_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already battling", color = Config.MAINCOLOR, description="You are already battling a boss"))
                    await error_msg.delete(delay=20)
                    await reaction.remove(user)
                    continue
                elif reaction.message != msg.id or not reaction.me:
                    continue
                self.waiting_users.append(user.id)
            except asyncio.TimeoutError:
                continue

        temp_msg = await ctx.channel.fetch_message(msg.id)
        users = []
        for temp_reaction in temp_msg.reactions:
            if str(temp_reaction) == "✔️":
                users = await temp_reaction.users().flatten()
        if ctx.author.id not in [x.id for x in users]:
            users.append(ctx.author)

        match = []
        for user in users:
            if user.id != self.bot.user.id:
                match.append({'user': user, 'account': Utils.get_account(user.id)})
        monster_class = random.choice(list(Config.CLASSES.find({})))
        spells = list(Config.SPELLS.find({'class': monster_class['name'], 'type': {'$nin': ['STUN']}}).limit(6))

        for i in range(len(match)):
            if match[i]['account']['armor'] is not None:
                match[i]['account']['stats']['defense'] += match[i]['account']['armor']['effect']
            if match[i]['account']['weapon'] is not None:
                match[i]['account']['stats']['strength'] += match[i]['account']['weapon']['effect']

        if random.randint(0, 7) == 0:
            monster = {'name': Utils.make_monster_name_titan(), 'titan': True, 'spells': spells, 'armor': {'name': "Titan's Breastplate", 'effect': random.randint(3, 9), 'emoji': "<:helmet:675820506284556306>"}, 'weapon': {'name': "Aged Sword", 'effect': random.randint(3, 9), 'emoji': "<:battle:670882198450339855>"}, 'stats': {'health': random.randint(200, 300), 'strength': random.randint(10, 20), 'defense': random.randint(7, 10), 'endurance': random.randint(200, 300)}}
        else:
            monster = {'name': Utils.make_monster_name(), 'titan': False, 'spells': spells, 'stats': {'health': random.randint(50, 150), 'strength': statistics.mean(x['account']['stats']['defense'] for x in match) * 0.5 + 2, 'defense': statistics.mean(x['account']['stats']['strength'] for x in match) * 0.5 + 2, 'endurance': random.randint(90, 150)}}
        for user in match:
            monster['stats']['health'] += 10
            monster['stats']['endurance'] += 10
            if user["account"]["user_id"] in self.waiting_users:
                self.waiting_users.remove(user["account"]["user_id"])

        if 'weapon' in monster.keys():
            monster['stats']['strength'] += monster['weapon']['effect']
        if 'armor' in monster.keys():
            monster['stats']['defense'] += monster['armor']['effect']

        monster['stats']['strength'] = round(monster['stats']['strength'])
        monster['stats']['defense'] = round(monster['stats']['defense'])
        monster['stats']['health'] = round(monster['stats']['health'])
        self.bosses += 1
        match_copy = match.copy()
        try:
            await self.boss_thread(match, msg, monster)
        except Exception as e:
            for user in match_copy:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if ctx.channel.id in self.active_channels:
                self.active_channels.remove(ctx.channel.id)
            self.bosses -= 1
            raise e

    @boss.error
    async def boss_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..", description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"), color = Config.ERRORCOLOR)

def setup(bot):
    bot.add_cog(Bosses(bot))
