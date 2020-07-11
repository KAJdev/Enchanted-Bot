# Imports
import pymongo
import discord

## MongoDB
# Cluster (Replace the <password> part of your uri with your password and remove the "<>")
myclient = pymongo.MongoClient(
    "URI")

# SWITCH BETWEEN TESTING AND NOT TESTING
testing = True

if testing:
    USERS = myclient["enchanted-testing"]['users']
else:
    USERS = myclient["enchanted-main"]['users']
CLANS = myclient["enchanted-main"]['clans']
CLAN_MESSAGES = myclient["enchanted-main"]['clan_messages']
SPELLS = myclient["enchanted-main"]['spells']
CLASSES = myclient["enchanted-main"]['classes']
PLANTS = myclient['enchanted-main']['plants']
ITEMS = myclient['enchanted-main']['items']
SERVERS = myclient['enchanted-main']['servers']
BLACKLIST = myclient['enchanted-main']['blacklist']
REPORTS = myclient['enchanted-main']['reports']
DROPPED_ITEMS = myclient['enchanted-main']['dropped_items']

RANK_LINKS = {5: {'name': "Unranked", 'link': "https://pngimage.net/wp-content/uploads/2019/05/circle-x-png-1.png",
                  'emoji': "<:unranked:677932715231936522>"},
              25: {'name': "Wood", 'link': "https://i.imgur.com/6rLnzo5.png",
                   'emoji': "<:wooden_rank:677932717781942285>"},
              75: {'name': "Silver", 'link': "https://i.imgur.com/INixUEF.png",
                   'emoji': "<:silver_rank:677932718109098004>"},
              150: {'name': "Gold", 'link': "https://i.imgur.com/3bOutcO.png",
                    'emoji': "<:gold_rank:677932717693730856>"},
              250: {'name': "Emerald", 'link': "https://i.imgur.com/TLpCgDB.png",
                    'emoji': "<:emerald_rank:677932717899251730>"},
              'max_rank': {'name': "Diamond", 'link': "https://i.imgur.com/WfCX8cu.png",
                           'emoji': "<:diamond_rank:677932716590759947>"}}

ACTIVE_CONTRACT = 0

## Main Discord bot settings
# Bot"s token (DO NOT SHARE WITH ANYONE ELSE!) (To find your token go to https://discordapp.com/developers/appli~cations/ > Your Wumpus-Bot Application > Bot (Turn the application into a bot if you haven"t already) > Token)
#
if testing:
    TOKEN = "TEST_BOT_TOKEN"  # TEST BOT TOKEN
else:
    TOKEN = "MAIN_BOT_TOKEN"  # main bot token

# Owner IDS (People who have access to restart the bot)
OWNERIDS = []

# Main Color (Replace the part after 0x with a hex code)
MAINCOLOR = discord.Colour(0xdb58dd)
TURNCOLOR = discord.Color.blue()
NOTTURN = discord.Color(0x000000)
DAMAGE = discord.Color.red()
OK = discord.Color.green()

CLAN_EMOTE_HOSTS = []

OPEN_QUEUES = True

# Error Color (Replace the part after the 0x with a hex code)
ERRORCOLOR = 0xED4337

TITLES = [' the Warrior', ' the Guard', ' the Bard', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII', ' IX',
          ' X', ' the Holy', ' the One', ' the Only', ' the Emperor', ' the King', ' the Queen', ' the Duke',
          ' the Duchess', ' the Knight', ' <:Crystal:672975609135366145>']

EMOJI = {'artifact': "<:artifact:708807345119035454>", 'up1': "<:1_up_arrow:707863240956444702>",
         'up2': "<:2_up_arrow:707863257804701739>", 'up3': "<:3_up_arrow:707863451350990890>",
         'down1': "<:1_down_arrow:707863720633827350>", 'down2': "<:2_down_arrow:707863721350922281>",
         'down3': "<:3_down_arrow:707863744654344293>", 'scroll': "<:scroll:676183918487142421>",
         'coin': "<:Coin:676181520062349322>", 'flame': "<:Mana2:675074552065163364>",
         'chest': "<:box:671574326364995595>", 'ruby': "<:ruby:676177832963211284>",
         'battle': "<:battle:670882198450339855>", 'power': "<:mana:670881187387932683>",
         'book': "<:book:670882689640955924>", 'key': "<:key:670880439199596545>", 'xp': "<:xp:707853397310701638>",
         'crown': "<:crowncoin:718518061573079082>", 'hp': "<:hp:723885353718644796>"}

GROWTH = {-1: "🥀", 0: "<:dirt:674075707772764160>", 1: "🌱", 2: "🌿", 3: "🌾", 4: "🌴"}

CONTRACTS = [{'1': {'xp': 10000, 'name': EMOJI['chest'] + " Chest", 'reward': 1, 'type': 'chest'},
              '2': {'xp': 30000, 'name': EMOJI['scroll'] + " '[FIRST CONTRACT]' Title", 'reward': ' [FIRST CONTRACT]',
                    'type': 'title'},
              '3': {'xp': 50000, 'name': EMOJI['chest'] + "x2 Chest", 'reward': 2, 'type': 'chest'},
              '4': {'xp': 80000, 'name': EMOJI['ruby'] + "x50 Rubies", 'reward': 50, 'type': 'ruby'},
              '5': {'xp': 100000, 'name': "<a:orb:710795781921177601> Orb Badge",
                    'reward': ' <a:orb:710795781921177601>', 'type': 'title'}}]

WIKI = [{'name': "Spells", 'pages': [
    {'title': "Damage Spells", 'content': "Damage spells do damage to your opponent. They consume mana when casted."}]},
        {'name': "Classes", 'pages': [{'title': "Arcane Class",
                                       'content': "The Arcane class is a powerful mage class that has lots of damage and steal spells."}]},
        {'name': "Bosses", 'pages': [{'title': "Regular Bosses",
                                      'content': "Regular bosses can be started at any time and played with up to 25 players."}]}]

print("Config loaded")
