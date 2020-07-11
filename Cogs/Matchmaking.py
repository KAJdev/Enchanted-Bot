import asyncio
import functools

import Config
import discord
import datetime
from discord.ext import commands, tasks
import logging
import Utils
import random


def match_check(match):
    # make sure health and mana are not above max value
    for _ in range(2):
        if match[_]['health'] > match[_]['account']['stats']['health']:
            match[_]['health'] = match[_]['account']['stats']['health']
        if match[_]['mana'] > match[_]['account']['stats']['endurance']:
            match[_]['mana'] = match[_]['account']['stats']['endurance']

        # make sure strength stats are where they should be
        strength_min = 0
        if match[_]['account']['weapon'] is not None:
            strength_min = match[_]['account']['weapon']['effect']
        if match[_]['account']['stats']['strength'] < strength_min:
            match[_]['account']['stats']['strength'] = strength_min
        else:
            match[_]['account']['stats']['strength'] = round(match[_]['account']['stats']['strength'], 1)

        # make sure armor stats are where they should be
        armor_min = 0
        if match[_]['account']['armor'] is not None:
            armor_min = match[_]['account']['armor']['effect']
        if match[_]['account']['stats']['defense'] < armor_min:
            match[_]['account']['stats']['defense'] = armor_min
        else:
            match[_]['account']['stats']['defense'] = round(match[_]['account']['stats']['defense'], 1)

    return match


class Matchmaking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.battles = 0
        self.battling_users = []
        self.chats = []
        self.matchmaking.start()
        self.ticket_garbage.start()

    def cog_unload(self):
        logging.info("Shutting down matchmaking system")
        self.matchmaking.cancel()
        logging.info("Shutting down queue cleaning system")
        self.ticket_garbage.cancel()

    async def construct_embeds(self, match, turn):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        for _ in range(2):
            field_description = ""
            field_description = "╔ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            for chat in self.chats:
                found = False
                if match[0]['account']['user_id'] in chat[0]["ids"]:
                    for c in chat[1:]:
                        field_description += f"│ **{c['user']}**: {c['msg']}\n"
                        found = True
            if not found:
                field_description += "│ *No chat logs*\n"
            field_description += "╚ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            if turn == _:
                embed = discord.Embed(color = Config.TURNCOLOR, description="It's your turn. React with a number to use a spell. Or react with 💤 to pass")
            else:
                embed = discord.Embed(color = Config.NOTTURN, description="It is " + match[int(not bool(_))]['ctx'].author.name + "'s turn, Please wait for them to cast a spell.")
            equipped_string = ""
            for spell in match[_]['account']['slots']:
                if spell is None:
                    equipped_string += "\n> *Nothing is written on this page...*"
                    continue
                for x in Utils.get_users_spells(match[_]['account']):
                    if spell == x['id']:
                        spell = x
                if spell is not None:
                    equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost]"
            embed.description += "\n\n**Spellbook**:" + equipped_string
            for __ in range(2):
                weapon_additive_string = ""
                if match[__]['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(match[__]['account']['weapon']['effect'])+ match[__]['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if match[__]['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(match[__]['account']['armor']['effect']) + \
                                             match[__]['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(match[__]['account']['power']) + match[__]['ctx'].author.name + match[__]['account']['selected_title'], value="Health: " + str(match[__]['health']) + "/" + str(match[__]['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match[__]['mana']) + "/" + str(match[__]['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match[__]['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(match[__]['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Battle against " + match[int(not bool(_))]['ctx'].author.name + match[int(not bool(_))]['account']['selected_title']
            footer_string = ""
            for effect in match[_]['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)
            embed.add_field(name="💬 **Chat**", value=field_description, inline=False)
            await match[_]['message'].edit(embed=embed)

    async def construct_embeds_with_message(self, turn, match, message):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        for _ in range(2):
            field_description = "╔ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            for chat in self.chats:
                found = False
                if match[0]['account']['user_id'] in chat[0]["ids"]:
                    for c in chat[1:]:
                        field_description += f"│ **{c['user']}**: {c['msg']}\n"
                        found = True
            if not found:
                field_description += "│ *No chat logs*\n"
            field_description += "╚ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            if turn == _:
                embed = discord.Embed(color = Config.OK, description=message)
            else:
                embed = discord.Embed(color = Config.DAMAGE, description=message)
            equipped_string = ""
            for spell in match[_]['account']['slots']:
                if spell is None:
                    equipped_string += "\n> *Nothing is written on this page...*"
                    continue
                for x in Utils.get_users_spells(match[_]['account']):
                    if spell == x['id']:
                        spell = x
                if spell is not None:
                    equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost]"
            embed.description += "\n\n**Spellbook**:" + equipped_string
            for __ in range(2):
                weapon_additive_string = ""
                if match[__]['account']['weapon'] is not None:
                    weapon_additive_string = " [+"+str(match[__]['account']['weapon']['effect'])+ match[__]['account']['weapon']['emoji'] +"]"
                armor_additive_string = ""
                if match[__]['account']['armor'] is not None:
                    armor_additive_string = " [+" + str(match[__]['account']['armor']['effect']) + \
                                             match[__]['account']['armor']['emoji'] + "]"
                embed.add_field(name=Utils.get_rank_emoji(match[__]['account']['power']) + match[__]['ctx'].author.name + match[__]['account']['selected_title'], value="Health: " + str(match[__]['health']) + "/" + str(match[__]['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match[__]['mana']) + "/" + str(match[__]['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match[__]['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(match[__]['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Battle against " + match[int(not bool(_))]['ctx'].author.name + match[int(not bool(_))]['account']['selected_title']
            footer_string = ""
            for effect in match[_]['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)
            embed.add_field(name="💬 **Chat**", value=field_description, inline=False)
            await match[_]['message'].edit(embed=embed)

    async def battle_thread(self, match):
        try:
            logging.info("Battle thread started: Current threads: " + str(self.battles))
            self.battling_users.append(match[0]['ctx'].author.id)
            self.battling_users.append(match[1]['ctx'].author.id)
            turn = random.randint(0, 1)
            total_turns = 1

            draw = False
            match[0]['health'] = match[0]['account']['stats']['health']
            embed = discord.Embed(title="Match Started", color = Config.MAINCOLOR, description= "[jump]("+match[0]['message'].jump_url+")")
            one_message = await match[0]['ctx'].send(match[0]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)
            embed = discord.Embed(title="Match Started", color=Config.MAINCOLOR,
                                  description="[jump](" + match[1]['message'].jump_url + ")")
            one_message = await match[1]['ctx'].send(match[1]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)
            match[1]['health'] = match[1]['account']['stats']['health']
            match[0]['mana'] = match[0]['account']['stats']['endurance']
            match[1]['mana'] = match[1]['account']['stats']['endurance']
            match[0]['effects'] = []
            match[1]['effects'] = []
            match[0]['afk'] = 0
            match[1]['afk'] = 0

            for _ in range(2):
                if match[_]['account']['armor'] is not None:
                    match[_]['account']['stats']['defense'] += match[_]['account']['armor']['effect']
                if match[_]['account']['weapon'] is not None:
                    match[_]['account']['stats']['strength'] += match[_]['account']['weapon']['effect']

                if match[_]['account']['slots'][0] is not None:
                    await match[_]['message'].add_reaction("1️⃣")
                if match[_]['account']['slots'][1] is not None:
                    await match[_]['message'].add_reaction("2️⃣")
                if match[_]['account']['slots'][2] is not None:
                    await match[_]['message'].add_reaction("3️⃣")
                if match[_]['account']['slots'][3] is not None:
                    await match[_]['message'].add_reaction("4️⃣")
                await match[_]['message'].add_reaction("💤")
            while match[0]['health'] > 0 and match[1]['health'] > 0 and match[0]['mana'] > 0 and match[1]['mana'] > 0:

                if match[turn]['afk'] > 2:
                    match[turn]['health'] = 0
                    match[turn]['mana'] = 0
                    continue

                # calculate effects for beginning of round
                for _ in range(2):
                    effects_remove = []
                    for effect in match[_]['effects']:
                        match[_][effect['type']] -= effect['amount']
                        match[_][effect['type']] = round(match[_][effect['type']], 1)
                        effect['turns'] -= 1
                        if effect['turns'] < 1:
                            effects_remove.append(effect)
                    for effect in effects_remove:
                        match[_]['effects'].remove(effect)


                # add mana to player
                match[turn]['mana'] += 3

                match = match_check(match)

                for _ in range(2):
                    if match[_]['health'] <= 0 or match[_]['mana'] <= 0:
                        break

                total_turns += 1

                await self.construct_embeds(match, turn)
                try:
                    reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '💤': 4}
                    def check(payload):
                        if payload.user_id == match[turn]['ctx'].author.id and payload.message_id == match[turn]['message'].id:
                            if str(payload.emoji) in reaction_dict.keys():
                                if reaction_dict[str(payload.emoji)] < 4:
                                    return match[turn]['account']['slots'][reaction_dict[str(payload.emoji)]] is not None
                                else:
                                    return True
                        return False

                    temp_msg = await match[turn]['ctx'].channel.fetch_message(match[turn]['message'].id)
                    reaction = None
                    for temp_reaction in temp_msg.reactions:
                        users = await temp_reaction.users().flatten()
                        if match[turn]['ctx'].author.id in [x.id for x in users] and temp_reaction.me:
                            can_continue = True
                            reaction = temp_reaction
                            try:
                                await temp_reaction.remove(match[turn]['ctx'].author)
                            except:
                                logging.error("Cannot remove emoji (not a big deal)")
                    if reaction is None:
                        payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                        reaction = payload.emoji
                        try:
                            await match[turn]['message'].remove_reaction(payload.emoji, match[turn]['ctx'].author)
                        except:
                            logging.error("Cannot remove emoji (not big deal)")
                    if str(reaction) == "💤":
                        turn = int(not bool(turn))
                        continue
                    else:
                        spell = Utils.get_spell(match[turn]['account']['class'], match[turn]['account']['slots'][reaction_dict[str(reaction)]])
                        if spell['type'] not in ["MANA", "DRAIN"]:
                            match[turn]['mana'] -= spell['cost']
                        elif spell['type'] == "DRAIN":
                            match[turn]['health'] -= spell['cost']

                        # spell types
                        if spell['type'] == "DAMAGE":
                            calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - match[int(not bool(turn))]['account']['stats']['defense'], 1)
                            if calculated_damage < 0:
                                calculated_damage = 0
                            match[int(not bool(turn))]['health'] -= calculated_damage
                            match[int(not bool(turn))]['health'] = round(match[int(not bool(turn))]['health'], 1)
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[int(not bool(turn))]['ctx'].author.name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[int(not bool(turn))]['account']['stats']['defense']) + "` blocked)")
                            turn = int(not bool(turn))

                        elif spell['type'] == "HEAL":
                            match[turn]['health'] += spell['damage']
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" gains `" + str(spell['damage']) + "` health.")
                            turn = int(not bool(turn))

                        elif spell['type'] == "STUN":
                            calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - match[int(not bool(turn))]['account']['stats']['defense'], 1)
                            if calculated_damage < 0:
                                calculated_damage = 0
                            match[int(not bool(turn))]['health'] -= calculated_damage
                            match[int(not bool(turn))]['health'] = round(match[int(not bool(turn))]['health'], 1)
                            match = match_check(match)
                            chance = random.randint(0, 1)
                            if chance == 1:
                                await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[int(not bool(turn))]['ctx'].author.name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[int(not bool(turn))]['account']['stats']['defense']) + "` blocked) and is stunned. (loses next turn)")
                            elif chance == 0:
                                await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[int(not bool(turn))]['ctx'].author.name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[int(not bool(turn))]['account']['stats']['defense']) + "` blocked) the stun failed...")
                                turn = int(not bool(turn))

                        elif spell['type'] == "MANA":
                            match[turn]['mana'] += spell['damage']
                            match[turn]['health'] -= spell['damage']
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" transforms `" + str(spell['damage']) + "` health into mana.")
                            turn = int(not bool(turn))

                        elif spell['type'] == "DRAIN":
                            match[turn]['mana'] += spell['damage']
                            match[int(not bool(turn))]['mana'] -= spell['damage']
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" stole `" + str(spell['damage']) + "` mana from "+match[int(not bool(turn))]['ctx'].author.name+" using `" + str(spell['cost']) + "` health.")
                            turn = int(not bool(turn))

                        elif spell['type'] == "PEN":
                            match[turn]['account']['stats']['strength'] += spell['damage']
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" boosted their Strength from `" + str(match[turn]['account']['stats']['strength'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['strength'])+"`")
                            turn = int(not bool(turn))

                        elif spell['type'] == "ARMOR":
                            match[turn]['account']['stats']['defense'] += spell['damage']
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" boosted their Defense from `" + str(match[turn]['account']['stats']['defense'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['defense'])+"`")
                            turn = int(not bool(turn))

                        elif spell['type'] == "POISON":
                            effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / match[int(not bool(turn))]['account']['stats']['defense'], 1)}
                            match[int(not bool(turn))]['effects'].append(effect)
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[int(not bool(turn))]['ctx'].author.name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                            turn = int(not bool(turn))

                        elif spell['type'] == "BLIND":
                            effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / match[int(not bool(turn))]['account']['stats']['defense'], 1)}
                            match[int(not bool(turn))]['effects'].append(effect)
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[int(not bool(turn))]['ctx'].author.name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                            turn = int(not bool(turn))

                        elif spell['type'] == 'STEAL':
                            calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - match[int(not bool(turn))]['account']['stats']['defense'], 1)
                            if calculated_damage < 0:
                                calculated_damage = 0
                            match[int(not bool(turn))]['health'] -= calculated_damage
                            match[turn]['health'] += calculated_damage
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. "+match[turn]['ctx'].author.name+" stole `" + str(spell['damage']) + "` health from "+match[int(not bool(turn))]['ctx'].author.name)
                            turn = int(not bool(turn))

                        elif spell['type'] == "IMPAIR":
                            before_stat = match[int(not bool(turn))]['account']['stats']['defense']
                            match[int(not bool(turn))]['account']['stats']['defense'] -= spell['damage']
                            if match[int(not bool(turn))]['account']['stats']['defense'] < 1:
                                match[int(not bool(turn))]['account']['stats']['defense'] = 1
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. " + match[int(not bool(turn))]['ctx'].author.name + "'s defense falls from `" + str(before_stat) + "` to `" + str(match[int(not bool(turn))]['account']['stats']['defense']) + "`.")
                            turn = int(not bool(turn))

                        elif spell['type'] == "WEAKEN":
                            before_stat = match[int(not bool(turn))]['account']['stats']['strength']
                            match[int(not bool(turn))]['account']['stats']['strength'] -= spell['damage']
                            if match[int(not bool(turn))]['account']['stats']['strength'] < 1:
                                match[int(not bool(turn))]['account']['stats']['strength'] = 1
                            match = match_check(match)
                            await self.construct_embeds_with_message(turn, match, match[turn]['ctx'].author.name + " casted **" + spell['name'] + "**. " + match[int(not bool(turn))]['ctx'].author.name + "'s strength falls from `" + str(before_stat) + "` to `" + str(match[int(not bool(turn))]['account']['stats']['strength']) + "`.")
                            turn = int(not bool(turn))

                        await asyncio.sleep(5)
                        continue
                except Exception as e:
                    if isinstance(e, asyncio.TimeoutError):
                        embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                              description="Your battle is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + match[turn]['message'].jump_url + ")")
                        timeout_msg = await match[turn]['ctx'].send(match[turn]['ctx'].author.mention, embed=embed)
                        await timeout_msg.delete(delay=20)
                        match[turn]['afk'] += 1
                        turn = int(not bool(turn))
                        continue
                    elif isinstance(e, discord.errors.NotFound):
                        draw = True
                        break
            person_lost = False
            for _ in range(2):
                try:
                    await match[_]['message'].clear_reactions()
                except:
                    logging.error("Cannot remove emoji (not a big deal)")

                if draw:
                    embed = discord.Embed(color = Config.MAINCOLOR, description="**DRAW**")
                elif match[_]['mana'] > 0 and match[_]['health'] > 0 or person_lost:
                    amount = random.randint(1, 3)
                    money = random.randint(5, 15)
                    coins = random.randint(12, 20)
                    power = random.randint(7, 9)
                    upgrade_emoji = Config.EMOJI['up1']
                    if power == 8:
                        upgrade_emoji = Config.EMOJI['up2']
                    elif power == 9:
                        upgrade_emoji = Config.EMOJI['up3']

                    xp = round(round(total_turns / 2, 1) * 100)
                    rankstring = Utils.get_rank_emoji(match[_]['account']['power'] + power) + " " + upgrade_emoji + "\n\n"
                    mystring = rankstring + "+`" + str(amount) + "` <:key:670880439199596545>\n+`" + str(money) + "` " + Config.EMOJI['ruby']+"\n+`" + str(coins) + "` " + Config.EMOJI['coin'] + "\n+`" + str("{:,}".format(xp)) + "` " + Config.EMOJI['xp']
                    match[_]['account']['keys'] += amount
                    if match[_]['account']['keys'] > 9:
                        match[_]['account']['keys'] -= 10
                        match[_]['account']['chests'] += 1
                        mystring += "\n+`1` " + Config.EMOJI['chest']
                    if 'xp' not in match[_]['account']:
                        match[_]['account']['xp'] = 0
                    Config.USERS.update_one({'user_id': match[_]['ctx'].author.id}, {'$inc': {'rubies': money, 'power': power, "coins": coins}, '$set': {'chests': match[_]['account']['chests'], 'keys': match[_]['account']['keys'], 'xp': match[_]['account']['xp'] + xp}})

                    embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! You have won!**\n\n" + mystring)
                else:
                    person_lost = True
                    power = random.randint(5, 7)
                    upgrade_emoji = Config.EMOJI['down1']
                    if power == 6:
                        upgrade_emoji = Config.EMOJI['down2']
                    elif power == 7:
                        upgrade_emoji = Config.EMOJI['down3']
                    money = random.randint(3, 9)
                    coins = random.randint(4, 10)
                    xp = round(round(total_turns / 2, 1) * 100)
                    match[_]['account']['power'] -= power
                    if match[_]['account']['power'] < 2:
                        match[_]['account']['power'] = 1
                        power = 0
                    rankstring = Utils.get_rank_emoji(match[_]['account']['power']) + " " + upgrade_emoji + "\n\n"
                    if 'xp' not in match[_]['account']:
                        match[_]['account']['xp'] = 0
                    Config.USERS.update_one({'user_id': match[_]['ctx'].author.id}, {'$inc': {'rubies': money, "coins": coins}, '$set': {'power': match[_]['account']['power'], 'xp': match[_]['account']['xp'] + xp}})
                    embed = discord.Embed(color = Config.MAINCOLOR, description="**You lost...**\n\n" + rankstring + "+`" + str(money) + "` " + Config.EMOJI['ruby'] + "\n+`" + str(coins) + "` " + Config.EMOJI['coin'] + "\n+`" + str("{:,}".format(xp)) + "` " + Config.EMOJI['xp'])
                for __ in range(2):
                    embed.add_field(name=Utils.get_rank_emoji(match[__]['account']['power']) + match[__]['ctx'].author.name + match[__]['account']['selected_title'], value="Health: " + str(match[__]['health']) + Config.EMOJI['hp'] + "\nMana: " + str(match[__]['mana']) + Config.EMOJI['flame'])
                embed.title = "Battle against " + match[int(not bool(_))]['ctx'].author.name + match[int(not bool(_))]['account']['selected_title']
                try:
                    await match[_]['message'].edit(embed=embed)
                except:
                    logging.error("While cleaning up match message is not found. ignorning.")
                logging.info("Cleaning up a battle")
                Config.USERS.update_many({'user_id': {'$in': [match[0]['ctx'].author.id, match[1]['ctx'].author.id]}}, {'$inc': {'battles': 1}})
                if match[0]['ctx'].author.id in self.battling_users:
                    self.battling_users.remove(match[0]['ctx'].author.id)
                if match[1]['ctx'].author.id in self.battling_users:
                    self.battling_users.remove(match[1]['ctx'].author.id)
                broken_items = Utils.decrease_durability(match[_]['account']['user_id'])
                if len(broken_items) > 0:
                    embed = discord.Embed(title="Broken Tools",
                                          description=match[_]['ctx'].author.mention + "! Your " + " and ".join(
                                              [x['name'] for x in broken_items]) + " broke!",
                                          color=Config.MAINCOLOR)
                    await match[_]['ctx'].send(content=match[_]['ctx'].author.mention, embed=embed)
        except:
            logging.error("Battle has errored! It has been disbanded and players were unqueued.")
            embed = discord.Embed(color=Config.MAINCOLOR, title="Battle has ended", description="The battle has ended.")
            for _ in match:
                try:
                    await _['message'].edit(embed=embed)
                except:
                    pass
        finally:
            self.battles -= 1
            if match[0]['ctx'].author.id in self.battling_users:
                self.battling_users.remove(match[0]['ctx'].author.id)
            if match[1]['ctx'].author.id in self.battling_users:
                self.battling_users.remove(match[1]['ctx'].author.id)



    @commands.command()
    async def clear_q(self, ctx):
        if ctx.author.id not in Config.OWNERIDS:
            await ctx.send("You do not have permission to do this")
        else:
            Utils.matchmaking = []
            await ctx.send("All tickets in matchmaking Queue have been cleared.")

    @commands.command(aliases=['b'])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def battle(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under maintenance.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.battling_users:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error entering Queue", description="You are already battling someone. Please finish that battle first.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        prefix = Utils.fetch_prefix(ctx)
        embed=discord.Embed(color=Config.MAINCOLOR, title="Looking for match... <a:lg:670720658166251559>", description="You are in queue. Once you find a match you will begin battling.", timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=10))
        embed.set_footer(text=f'type {prefix}cancel to stop searching | timeout at ')
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)

        for ticket in Utils.matchmaking:
            if ticket['account']['user_id'] == ctx.author.id:
                await ticket['message'].edit(embed=discord.Embed(title="Entered Queue somewhere else", description="You have started looking for a match in a different location.", color = Config.MAINCOLOR))
                ticket['ctx'] = ctx
                ticket['message'] = msg
                return

        Utils.send_ticket({'power': account['power'], 'ctx': ctx, 'account': account, 'message': msg, 'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)})

    @commands.command()
    async def cancel(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        remove_ticket = None
        for ticket in Utils.matchmaking:
            if ticket['account']['user_id'] == ctx.author.id:
                await ticket['message'].edit(embed=discord.Embed(title="Canceled Matchmaking", description="Matchmaking has been canceled.", color = Config.MAINCOLOR))
                await ticket['message'].delete(delay=10)
                await ticket['ctx'].message.delete(delay=10)
                remove_ticket = ticket
        if remove_ticket is not None:
            Utils.matchmaking.remove(remove_ticket)

            embed=discord.Embed(color=Config.MAINCOLOR, title="Matchmaking Canceled", description="You have exited the battle queue.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=10)
            await ctx.message.delete(delay=10)
        else:
            embed=discord.Embed(color=Config.MAINCOLOR, title="You look confused.", description="You are not actively looking for a battle. Use ]battle to start looking for one.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=10)
            await ctx.message.delete(delay=10)

    @battle.error
    async def battle_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..", description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"), color=Config.ERRORCOLOR)

    async def after_battle(self, task, match):
        logging.info("Callback for after match has been called.")
        try:
            task.result()
        except:
            logging.error("Battle has errored! It has been disbanded and players were unqueued.")
            embed = discord.Embed(color = Config.MAINCOLOR, title="Battle has ended", description="The battle has ended.")
            for _ in match:
                await _['message'].edit(embed=embed)
        finally:
            self.battles -= 1
            if match[0]['ctx'].author.id in self.battling_users:
                self.battling_users.remove(match[0]['ctx'].author.id)
            if match[1]['ctx'].author.id in self.battling_users:
                self.battling_users.remove(match[1]['ctx'].author.id)
            loop = 0
            for chat in self.chats:
                if match[0]['ctx'].author.id in chat[0]["ids"]:
                    self.chats.remove(self.chats[loop])
                loop += 1

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def chat(self, ctx, *, choice:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(title="Emotes", description="", color = Config.MAINCOLOR)
            i = 0
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    i += 1
                    embed.description += "> " + str(i) + " | **" + cosmetic["value"] + "**\n"
            embed.set_footer(text=f"Get more emotes from the shop | use {prefix}chat <index> to chat in battle")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        try:
            emotes = []
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    emotes.append(cosmetic)
            choice = int(choice)
            if choice > len(emotes) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(len(emotes)) + " Emotes. Try using a number 1-" + str(len(emotes)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                loop = 0
                for chat in self.chats:
                    if ctx.author.id in chat[0]["ids"]:
                        if len(chat) > 5:
                            self.chats[loop].remove(self.chats[loop][1])
                        self.chats[loop].append({'user': str(ctx.author.name), 'msg': emotes[choice]['value']}) 
                        embed = discord.Embed(description=f"Chat sent!\n**{str(ctx.author.name)}**: {emotes[choice]['value']}", color=Config.MAINCOLOR)
                        if msg is None:
                            message = await ctx.send(embed=embed)
                            await asyncio.sleep(5)
                            await message.delete()
                            await ctx.message.delete()
                        else:
                            await msg.edit(embed=embed)
                        return
                    loop += 1
                embed = discord.Embed(title="Whoops..", description=f"You can only use this command when you're battling!", color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...", description="Thats not a emote index. Try using a number 1-" + str(len(emotes)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @tasks.loop(seconds=10)
    async def matchmaking(self):
        if len(Utils.matchmaking) > 1:
            logging.info("Starting matching")
            matched = Utils.match_tickets()
            for match in matched:
                logging.info("Found match")
                await match[0]['message'].edit(embed=discord.Embed(color = Config.MAINCOLOR, title="Match found!", description="Battling " + match[1]['ctx'].author.name))
                await match[1]['message'].edit(embed=discord.Embed(color = Config.MAINCOLOR, title="Match found!", description="Battling " + match[0]['ctx'].author.name))
                self.battles += 1
                match[0]['message']
                id1 = match[0]['ctx'].author.id
                id2 = match[1]['ctx'].author.id
                self.chats = [[{"ids": [id1, id2]}]]
                battle = self.bot.loop.create_task(self.battle_thread(match))
                #battle.add_done_callback(functools.partial(self.after_battle, match=match))

            logging.info("Matching completed.")


    @tasks.loop(seconds=30)
    async def ticket_garbage(self):
        if len(Utils.matchmaking) > 0:
            logging.info("Started queue cleaning")
            to_delete = []
            for ticket in Utils.matchmaking:
                if ticket['expire'] < datetime.datetime.utcnow():
                    to_delete.append(ticket)
            for ticket in to_delete:
                await ticket['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Matchmaking Canceled", description="timout has been reached. Please type `]battle` to join the queue again."))
                Utils.matchmaking.remove(ticket)
                logging.info("Cleaned ticket from queue.")
            logging.info("Queue cleaning completed.")


def setup(bot):
    bot.add_cog(Matchmaking(bot))
