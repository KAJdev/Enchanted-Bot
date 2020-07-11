import math

import Config
import datetime
import random
import discord
import asyncio
import re

try:
    print("Matchmaking Queue already instantiated: " + str(matchmaking))
except NameError:
    matchmaking = []


def get_class(name):
    return Config.CLASSES.find_one({'name': name})

def fetch_prefix(guild):
    return Config.SERVERS.find_one({'guild_id': guild})

def fetch_prefix(ctx):
    server = Config.SERVERS.find_one({'guild_id': ctx.guild.id})
    if server is not None:
        return server['prefix']
    else:
        return "]"

def insert_guild(ctx):
    Config.SERVERS.insert_one({'guild_id': ctx.guild.id, 'prefix': "]", 'channel_blacklist': []})

def get_all_classes():
    return list(Config.CLASSES.find({}))


def make_monster_name():
    first = ['Gar', 'Hel', 'Bar', 'Or', 'Fre', 'Cra', 'Ju', 'Pre', 'Lue', 'Meu', 'Ve', 'Ki', 'Fr', 'Xse', "Har", 'Fai', 'Ig', 'Tel', 'Ral', 'Gr', 'H']
    second = ['mold', 'gamlo', 'crem', 'ulk', 'opref', 'hold', 'joint', 'opold', 'ulf', 'rep', 'teft', 'dolt', 'fop', '', '', ',', ' Ulk', 'O', 'S']
    last = [' The Second', ' II', ' The Powerful', ' The Almighty', ' The Fourth', ' I', ' The Arrogant', ' The Troll', ' The Warrior', ' The Guard', ' Underwhelm', ' The Sorcerer', ' The King', ' The Queen', ' The Bard', ' The Traveler', ' The Scarred', ' The Lost Man', ' The Lonely', ' The Spider', ' The Giant Spider', ' The Elf', ' The Magician', ' The Trickster']
    return random.choice(first) + random.choice(second) + random.choice(last)


async def get_account_lazy(bot, ctx, id):
    account = Config.USERS.find_one({'user_id': id})
    if account is None:
        embed = discord.Embed(title="Please select your class to begin!", description = "use the emojis to choose", color = Config.MAINCOLOR)
        embed.set_footer(text="Message will be deleted in 30 seconds")
        for _class in get_all_classes():
            embed.add_field(name=_class['name'] + " " + _class['emote'], value=_class['desc'])
        msg = await ctx.send(embed=embed)
        for _class in get_all_classes():
            await msg.add_reaction(_class['emote'])

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and reaction.me and reaction.emoji in [x['emote'] for x in get_all_classes()]

        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30.0)
            for _class in get_all_classes():
                if _class['emote'] == str(reaction):
                    account = create_account(ctx.author.id, _class['name'])
                    await msg.clear_reactions()
                    return msg, account
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await msg.delete()
            return None, None
    else:
        return None, account


def get_account(id):
    return Config.USERS.find_one({'user_id': id})


def create_account(user, _class):
    account = get_account(user)
    class_obj = get_class(_class)
    if account is None:
        account = {'user_id': user, 'rubies': 0, 'crowns': 0, 'claimed_contract': {}, 'coins': 0, 'xp': 0, 'inventory': [], 'weapon': None, 'armor': None, 'class': _class, 'cosmetics': [{'type': 'color', 'name': 'Basic color', 'value': "0xdb58dd"}, {'type': 'title', 'value': " the " + _class}, {'type': 'emote', 'value': "Wow!"}, {'type': 'emote', 'value': "Good Game!"}, {'type': 'emote', 'value': '<:smi:729075126532046868>'}], 'selected_title': " The " + _class, 'selected_embed_color': {'name': "Basic color", 'value': "0xdb58dd"}, 'selected_embed_image': None, 'keys': 0, 'grown': [], 'crops': [{'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}], 'stats': class_obj['stats'], 'seeds': [{'id': 0, 'amount': 1}], 'battles': 0, 'power': 2, 'chests': 0, 'spells': [0, 1], 'slots': [0, 1, None, None], 'registered': datetime.datetime.utcnow()}
        Config.USERS.insert_one(account)
        return account
    else:
        return account


def get_rank_name(power):
    return get_rank_object(power)['name']


def get_rank_link(power):
    return get_rank_object(power)['link']


def get_rank_emoji(power):
    return get_rank_object(power)['emoji'] + " "


def get_rank_object(power):
    rank = Config.RANK_LINKS['max_rank']
    for key, value in Config.RANK_LINKS.items():
        try:
            if power < key:
                rank = value
                break
            else:
                continue
        except:
            break
    return rank


def decrease_durability(userid):
    account = get_account(userid)
    broken_items = []
    if account['armor'] is not None:
        for item in account['inventory']:
            if item['name'] == account['armor']['name']:
                if 'durability' in item.keys():
                    item['current_durability'] = item['durability']
                else:
                    dura = 25
                    if item['tier'] == "bronze":
                        dura = 100
                    elif item['tier'] == "iron":
                        dura = 500
                    elif item['tier'] == "emerald":
                        dura = 1000
                    elif item['tier'] in ["enchanted", "phantom"]:
                        dura = 5000
                    item['durability'] = dura
                    item['current_durability'] = dura
                item['current_durability'] -= 1
                try:
                    account['armor']['current_durability'] -= 1
                except:
                    print("ignore this")
                if item['current_durability'] < 1:
                    account['armor'] = None
                    broken_items.append(item)
                break
    if account['weapon'] is not None:
        for item in account['inventory']:
            if item['name'] == account['weapon']['name']:
                if 'current_durability' not in item.keys():
                    if 'durability' in item.keys():
                        item['current_durability'] = item['durability']
                    else:
                        dura = 25
                        if item['tier'] == "bronze":
                            dura = 100
                        elif item['tier'] == "iron":
                            dura = 500
                        elif item['tier'] == "emerald":
                            dura = 1000
                        elif item['tier'] in ["enchanted", "phantom"]:
                            dura = 5000
                        item['durability'] = dura
                        item['current_durability'] = dura
                item['current_durability'] -= 1
                try:
                    account['weapon']['current_durability'] -= 1
                except:
                    print("ignore this")
                if item['current_durability'] < 1:
                    account['weapon'] = None
                    broken_items.append(item)
                break
    Config.USERS.update_one({'user_id': userid}, {'$set': {'inventory': account['inventory']}})
    if len(broken_items) > 0:
        Config.USERS.update_one({'user_id': userid}, {'$pull': {'inventory': {'$in': broken_items}}, '$set': {'armor': account['armor'], 'weapon': account['weapon']}})
    return broken_items




def get_contract_tier(xp):
    tier = Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(len(Config.CONTRACTS[Config.ACTIVE_CONTRACT]))]
    final_key = str(len(Config.CONTRACTS[Config.ACTIVE_CONTRACT]))
    for key, value in Config.CONTRACTS[Config.ACTIVE_CONTRACT].items():
        try:
            if xp < value['xp']:
                tier = value
                final_key = key
                break
            else:
                continue
        except:
            break
    return tier, final_key


def get_plant(id):
    return Config.PLANTS.find_one({'id': id})


## UPGRADE FORMULAS
def calc_strength_upgrade_cost(strength):
    return math.floor(40 * 1.15 ** math.floor(strength))


def calc_defense_upgrade_cost(defense):
    return math.floor(40 * 1.15 ** math.floor(defense))


def calc_health_upgrade_cost(health):
    return math.floor(20 * 1.1 ** (health/10))


def calc_item_upgrade_cost(effect, scale=1.1):
    return math.floor(15 * 1.25 ** effect)


def calc_clan_upgrade_cost(amount):
    return math.floor(10 * 1.05 ** amount)


def calc_endurance_upgrade_cost(endurance):
    return math.floor(1.03 ** math.floor(endurance))


def change_crate_amount(user, amount):
    Config.USERS.update_one({'user_id': user}, {'$inc': {'chests': amount}})


def change_money_amount(user, amount):
    Config.USERS.update_one({'user_id': user}, {'$inc': {'rubies': amount}})


def get_spell(_class, id):
    return Config.SPELLS.find_one({'class': _class, 'id': id})


def get_spell_by_name(_class, name):
    return Config.SPELLS.find_one({'class': _class, 'name': re.compile('^' + re.escape(name) + '$', re.IGNORECASE)})


def get_all_crops():
    crop_dict = {}
    for crop in Config.PLANTS.find({}):
        crop_dict[crop['id']] = crop
    return crop_dict


def get_plant_by_name(name):
    return Config.PLANTS.find_one({'name': re.compile('^' + re.escape(name) + '$', re.IGNORECASE)})


def get_users_spells(account):
    return list(Config.SPELLS.find({'class': account['class'], 'id': {'$in': account['spells']}}))


def check_user_has_spell(user, id):
    return id in get_account(user)['spells']


def equip_spell(user, id, slot):
    account = get_account(user)
    last_slot = account['slots'][slot]
    account['slots'][slot] = id
    Config.USERS.update_one({'user_id': user}, {'$set': account})
    return last_slot


def get_not_owned_spells(account):
    return Config.SPELLS.count_documents({'class': account['class'], 'id': {'$nin': account['spells']}})


def win_spell(account):
    spells = list(Config.SPELLS.find({'class': account['class'], 'id': {'$nin': account['spells']}}))
    if len(spells) < 1:
        return None
    else:
        return random.choice(spells)


def win_seed():
    seeds = get_all_crops()
    return random.choice(list(seeds.values()))


def send_ticket(ticket):
    if ticket in matchmaking:
        return False
    matchmaking.append(ticket)
    return True


def match_tickets():
    matched = []
    canceled = []
    for ticket in matchmaking:
        if ticket not in canceled:
            if ticket['expire'] < datetime.datetime.utcnow():
                canceled.append(ticket)
                continue
            for secondary_ticket in matchmaking:
                if secondary_ticket not in canceled and ticket != secondary_ticket:
                    if abs(ticket['power'] - secondary_ticket['power']) <= 40:
                        matched.append((ticket, secondary_ticket))
                        canceled.append(ticket)
                        canceled.append(secondary_ticket)
    for ticket in canceled:
        if ticket in matchmaking:
            matchmaking.remove(ticket)
    return matched


print("Utilities loaded")


def get_user_clan(id):
    return Config.CLANS.find_one({'members': id})


def get_all_items():
    return list(Config.ITEMS.find({}))

def get_all_weapons():
    items = []
    for item in Config.ITEMS.find({}):
        if item["type"] in ["weapon", "armor"]:
            items.append(item)
    return items

def get_all_cosmetics():
    items = []
    for item in Config.ITEMS.find({}):
        if item["type"] in ["title", "emote", "color", "image"]:
            items.append(item)
    return items


def make_monster_name_titan():
    first = ['Rel', 'Raid', 'Ur', 'Pal', 'Su']
    second = ['per', 'foul', 'es', 'idin', 'ipidimus']
    return random.choice(first) + random.choice(second) + " The TITAN"
