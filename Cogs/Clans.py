import random
import statistics

import pymongo
import asyncio
import Config
import discord
import datetime
from discord.ext import commands, tasks
import logging
import Utils


class Clans(commands.Cog):

    def __init__(self, bot):
        self.upgrading_users = []
        self.waiting_users = []
        self.dungeons = 0
        self.active_channels = []
        self.battling_users = []
        self.bot = bot
        #self.clan_minter.start()
        #self.clan_grinder.start()
        #self.clan_miner.start()
        #self.clan_power_update.start()
        # self.clan_loop.start()
        # self.clan_loop_index = 0

    def cog_unload(self):
        self.clan_loop.cancel()
        logging.info("Shutdown clan rewards system")


    @tasks.loop(hours=1)
    async def clan_power_update(self):
        logging.info("Starting Clan Power Update loop")
        for clan in Config.CLANS.find({}):
            all_members = Config.USERS.find({'user_id': {'$in': clan['members']}})
            clan['power'] = 0
            for member in all_members:
                clan['power'] += member['power']
            Config.CLANS.update_one({'name': clan['name']}, {'$set': clan})
        logging.info("Completed clan Power Update loop.")

    @tasks.loop(hours=1)
    async def clan_minter(self):
        logging.info("Starting Clan Mint loop")
        for clan in Config.CLANS.find({}):
            clan['coin_storage'] += clan['coin_mint']
            if clan['coin_storage'] > clan['coin_storage_max']:
                clan['coin_storage'] = clan['coin_storage_max']
            Config.CLANS.update_one({'name': clan['name']}, {'$set': clan})
        logging.info("Completed clan Mint loop.")

    @tasks.loop(minutes=12)
    async def clan_loop(self):
        logging.info("Starting Clan loop")
        for clan in Config.CLANS.find({}):
            clan['xp_storage'] += clan['xp_grinder']
            if clan['xp_storage'] > clan['xp_storage_max']:
                clan['xp_storage'] = clan['xp_storage_max']

            if self.clan_loop_index % 5 == 0:
                clan['coin_storage'] += clan['coin_mint']
                if clan['coin_storage'] > clan['coin_storage_max']:
                    clan['coin_storage'] = clan['coin_storage_max']

                all_members = Config.USERS.find({'user_id': {'$in': clan['members']}})
                clan['power'] = 0
                for member in all_members:
                    clan['power'] += member['power']

            if self.clan_loop_index % 10 == 0:
                clan['ruby_storage'] += clan['ruby_miner']
                if clan['ruby_storage'] > clan['ruby_storage_max']:
                    clan['ruby_storage'] = clan['ruby_storage_max']

            Config.CLANS.update_one({'name': clan['name']}, {'$set': clan})
        logging.info("Completed clan loop.")
        self.clan_loop_index += 1

    @tasks.loop(hours=2)
    async def clan_miner(self):
        logging.info("Starting Clan Miner loop")
        for clan in Config.CLANS.find({}):
            clan['ruby_storage'] += clan['ruby_miner']
            if clan['ruby_storage'] > clan['ruby_storage_max']:
                clan['ruby_storage'] = clan['ruby_storage_max']
            Config.CLANS.update_one({'name': clan['name']}, {'$set': clan})
        logging.info("Completed clan Miner loop.")

    async def make_clan_embed(self, ctx, clan):
        clan_members = ""
        owner_name = "Nobody?"
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        i = 0
        for member in all_clan_members:
            i += 1
            try:
                discord_member = await self.bot.fetch_user(member['user_id'])
            except:
                continue
            if 'member_artifacts' not in clan.keys():
                clan['member_artifacts'] = {}
            if str(member['user_id']) not in clan['member_artifacts'].keys():
                artifact = ""
            else:
                artifact = "| **%s**%s" % (str(clan['member_artifacts'][str(member['user_id'])]), Config.EMOJI['artifact'])
            
            if member['user_id'] == clan['owner']:
                clan_members += "\n%s | %s %s %s | 🌟" % (i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
                owner_name = discord_member.name
            elif member['user_id'] in clan['admins']:
                clan_members += "\n%s | %s %s %s | ⭐" % (i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
            else:
                clan_members += "\n%s | - %s %s %s" % (
                i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
        clan_info = "Name: " + clan['name'] + "\nPower: " + str(clan['power']) + "\nOwner: " + owner_name + "\nIcon: " + \
                    clan['emoji'] + "\nArtifacts: " + str(clan['artifacts']) + " " + Config.EMOJI['artifact'] + "\n\n**Members (" + str(clan['member_count']) + "/20):**\n" + clan_members
        embed = discord.Embed(title=clan['name'],
                              description=clan_info, color=Config.MAINCOLOR)
        # embed.set_author(name="Clan", icon_url=str(self.bot.get_emoji(clan['emoji_id']).url))
        # embed.set_thumbnail(url=str(self.bot.get_emoji(clan['emoji_id']).url))
        embed.add_field(name="Base", value="Ruby Miner: +`" + str(clan['ruby_miner'] / 2) + "` " + Config.EMOJI[
            'ruby'] + "/hour\nCoin Mint: +`" + str(clan['coin_mint']) + "` " + Config.EMOJI[
                                               'coin'] + "/hour\nXP Grinder: +`" + str(clan['xp_grinder'] * 5) + "` " +
                                           Config.EMOJI['xp'] + "/hour")
        embed.add_field(name="Storage", value="Ruby Storage: `" + str(clan['ruby_storage']) + "/" + str(
            clan['ruby_storage_max']) + "` " + Config.EMOJI['ruby'] + "\nCoin Storage: `" + str(
            clan['coin_storage']) + "/" + str(clan['coin_storage_max']) + "` " + Config.EMOJI[
                                                  'coin'] + "\nXP Storage: `" + str(clan['xp_storage']) + "/" + str(
            clan['xp_storage_max']) + "` " + Config.EMOJI['xp'])
        #embed.add_field(name="Members (" + str(clan['member_count']) + "/20):", value=clan_members, inline=False)
        if 'motd' in clan.keys():
            if clan['motd']:
                embed.add_field(name="Clan Message", value=clan['motd'], inline=False)
        # embed.add_field(name="Commands", value=f"`{prefix}clan claim`\n`{prefix}clan edit <attribute> <value>`\n`{prefix}clan leave`\n`{prefix}clan upgrade`")
        await ctx.send(embed=embed)
 
    @commands.group(aliases=['clans', 'group', 'groups'])
    async def clan(self, ctx):
        if ctx.invoked_subcommand is None:
            msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
            if account is None:
                return

            clan = Utils.get_user_clan(ctx.author.id)
            prefix = Utils.fetch_prefix(ctx)
            if clan is None:
                recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}}).limit(5))
                clan_string = ""
                for rec_clan in recommended:
                    clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']), prefix, rec_clan['name'])
                embed = discord.Embed(title="Clan", color=Config.MAINCOLOR, description="Clans are groups of players that band together in order to fight dungeons, get larger rewards, and share resources.\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
                await ctx.send(embed=embed)
            else:
                await self.make_clan_embed(ctx, clan)

    @clan.command()
    async def info(self, ctx, *, name: str = None):
        if name is not None:
            clan = Config.CLANS.find_one({'name': name})
            if clan is None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="That clan does not exist. Sorry about that.")
                await ctx.send(embed=embed)
                return
            else:
                await self.make_clan_embed(ctx, clan)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You need to specify a clan name in order to see info!")
            await ctx.send(embed=embed)


    @clan.command()
    async def top(self, ctx):
        prefix = Utils.fetch_prefix(ctx)
        top = list(Config.CLANS.find({}).sort("power", pymongo.DESCENDING).limit(5))
        clan_string = ""
        for rec_clan in top:
            if len(rec_clan['members']) < 20 and rec_clan['open']:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']), prefix,
                rec_clan['name'])
            else:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']))
        embed = discord.Embed(title="Top Clans", color=Config.MAINCOLOR,
                              description="**Top 5 Clans based on Power:**\n\n" + clan_string)
        await ctx.send(embed=embed)

    @clan.command()
    async def promote(self, ctx, choice : int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return
        
        if ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are not a clan leader!")
            await ctx.send(embed=embed)
        elif member["user_id"] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't promote yourself, nice try though")
            await ctx.send(embed=embed)
        elif member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                   description="That's the owner, silly")
            await ctx.send(embed=embed)
        else:
            discord_member = await self.bot.fetch_user(member["user_id"])
            p = Utils.fetch_prefix(ctx)
            if member["user_id"] in clan['admins']:
                if ctx.author.id != clan['owner']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="That user is already an admin. You cannot promote them any futher.")
                    await ctx.send(embed=embed)
                    return
                embed = discord.Embed(title="Change Clan Ownership?", color=Config.MAINCOLOR,
                                      description=discord_member.name + f" is already a clan admin. React with `✔` to this message to transfer ownership, or `✖` to cancel.")
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("✔")
                await msg.add_reaction("✖")

                def check(reaction, user):
                    return reaction.message.id == msg.id and user.id == ctx.author.id

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
                    if str(reaction) == "✖":
                        embed = discord.Embed(title="Canceled", color=Config.MAINCOLOR,
                                              description=discord_member.name + f" is still a clan admin. Ownership has not changed")
                        await msg.edit(embed=embed)
                        return
                    Config.CLANS.update_one({'name': clan['name']}, {'$set': {'owner': member["user_id"]}})
                    if member["user_id"] not in clan['admins']:
                        Config.CLANS.update_one({'name': clan['name']}, {'$push': {'admins': member["user_id"]}})

                    embed = discord.Embed(title="Ownership changed", color=Config.MAINCOLOR,
                                          description=discord_member.name + f" is now the owner of **{clan['name']}** {clan['emoji']}")
                    await msg.edit(embed=embed)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title="Canceled", color=Config.MAINCOLOR,
                                          description=discord_member.name + f" is still a clan admin. Ownership has not changed")
                    await msg.edit(embed=embed)
                    return
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$push': {'admins': member["user_id"]}})
                embed = discord.Embed(title="Welcome aboard!", color=Config.MAINCOLOR,
                                      description=discord_member.name + " is now a clan admin. They can edit the clan, and manage members.")
                await ctx.send(embed=embed)
            

    @clan.command()
    async def demote(self, ctx, choice : int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return
        
        if member["user_id"] not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are not a clan leader!")
            await ctx.send(embed=embed)
        elif member["user_id"] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You cannot demote yourself!")
            await ctx.send(embed=embed)
        elif member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                   description="You cannot demote the clan owner!")
            await ctx.send(embed=embed)
        else:
            discord_member = await self.bot.fetch_user(member["user_id"])
            p = Utils.fetch_prefix(ctx)
            if member["user_id"] not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description=member.name + f" is not a clan admin. Use `{p}clan promote {discord_member.name}` to promote them.")
                await ctx.send(embed=embed)
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$pull': {'admins': member["user_id"]}})
                embed = discord.Embed(title="C ya later!", color=Config.MAINCOLOR,
                                      description=discord_member.name + " is no longer a clan admin. They cannot edit the clan or manage members anymore.")
                await ctx.send(embed=embed)

    @clan.command()
    async def create(self, ctx, *, name):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            if Config.CLANS.find_one({'name': name}) is not None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="A clan already exists with that name! try using something else.")
                await ctx.send(embed=embed)
            elif len(name) > 30:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="That's too long! A clan name must be 30 characters or less.")
                await ctx.send(embed=embed)
            else:
                Config.CLANS.insert_one(
                    {'name': name, 'emoji': "<:helmet:675820506284556306>", 'emoji_id': 675820506284556306,
                     'members': [ctx.author.id], 'member_artifacts': {}, 'member_count': 1, 'artifacts': 0, 'owner': ctx.author.id, 'admins': [ctx.author.id],
                     'power': account['power'], 'open': True, 'color': str(Config.MAINCOLOR), 'ruby_miner': 1, 'coin_mint': 1, 'xp_grinder': 1, 'key_factory': 1,
                     'ruby_storage': 0, 'ruby_storage_max': 10, 'coin_storage': 0, 'coin_storage_max': 100, 'xp_storage': 0, 'xp_storage_max': 1000, 'key_storage': 0, 'key_storage_max': 30})

                embed = discord.Embed(title="Clan created", color=Config.MAINCOLOR,
                                      description=f"You can view your clan with the `{prefix}clan` command. Edit your clan with the `{prefix}clan edit` command. Good luck!")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are already in a clan!")
            await ctx.send(embed=embed)

    async def do_upgrade_loop(self, ctx, clan, msg, part):
        cost = Utils.calc_clan_upgrade_cost(clan[part.lower()])
        more_output = 1
        embed = discord.Embed(
            title="Upgrade `" + part.title().replace("_", " ") + "` to `" + str((clan[part] + 1) /2) + "`/hour?",
            description=
            "Clan Artifacts: `" + str(clan['artifacts']) + "`\n" +
            "Cost: `" + str(cost) + "` " + Config.EMOJI['artifact']
            + f"\nUpgrades: `{clan[part]}` → `{clan[part] + 1}`"
            + f"\nOutput: `{clan[part] / 2}` → `{round((clan[part] + more_output) / 2, 1)}`"
            + "\n\n*Click the reaction to upgrade\nwait to cancel*", color=Config.MAINCOLOR)
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✅")

        def check(reaction, user):
            return reaction.message.id == msg.id and user.id == ctx.author.id and reaction.me

        try:
            if clan['artifacts'] < cost:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have enough artifacts to upgrade this item...",
                                      color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, clan, msg

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            await reaction.remove(user)
            clan = Utils.get_user_clan(ctx.author.id)
            if clan['artifacts'] < cost:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have enough artifacts to upgrade this item...",
                                      color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, clan, msg

            clan[part] += 1
            clan['artifacts'] -= cost

            Config.CLANS.update_one({'name': clan['name']}, {'$inc': {'artifacts': -cost, part: 1}})
            clan = Utils.get_user_clan(ctx.author.id)
            return True, cost, more_output, 1, clan, msg
        except asyncio.TimeoutError:
            return False, 0, 0, 0, clan, msg

    @clan.command()
    async def message(self, ctx, *, content: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan admin!")
            elif content is None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You must provide a message!")
            elif len(content) > 100:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="Your message must be under 100 characters in length.")
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'motd': content}})
                embed = discord.Embed(title="Message Set!", color=Config.MAINCOLOR,
                                      description="Your message has been set!\n```\n"+content+"\n```")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

    @clan.command()
    async def upgrade(self, ctx, part:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan leader!")
                await ctx.send(embed=embed)
            else:
                if part is None:
                    part = ""
                if part.lower() not in ['miner', 'grinder', 'mint']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description=f"You must provide a part of your base to upgrade. Some available parts:\n\n`{prefix}clan upgrade mint` "+Config.EMOJI['coin']+f"\n `{prefix}clan upgrade miner` "+Config.EMOJI['ruby']+f"\n `{prefix}clan upgrade grinder` "+Config.EMOJI['xp'])
                    await ctx.send(embed=embed)
                else:
                    if part.lower() == "miner":
                        part = "ruby_miner"
                    elif part.lower() == "grinder":
                        part = "xp_grinder"
                    elif part.lower() == "mint":
                        part = "coin_mint"
                    if ctx.author.id not in self.upgrading_users:
                        self.upgrading_users.append(ctx.author.id)
                    archived_clan = clan.copy()
                    do_continue = True
                    total_cost = 0
                    total_output = 0
                    total_upgrades = 0
                    while do_continue:
                        do_continue, more_cost, more_upgrades, more_output, clan, msg = await self.do_upgrade_loop(
                            ctx, clan, msg, part)
                        total_cost += more_cost
                        total_output += more_output
                        total_upgrades += more_upgrades
                    try:
                        if archived_clan[part] == clan[part]:
                            await msg.delete()
                            await ctx.message.delete()
                            return
                        await msg.clear_reactions()
                        embed = discord.Embed(
                            title="Upgraded `" + part.title().replace("_", " ") + "` from `" + str(
                                archived_clan[part]/2) + "`/hour to `" + str(clan[part]/2) + "`/hour",
                            description=
                            "Total Cost: `" + str(total_cost) + "` " + Config.EMOJI['artifact']
                            + f"\nUpgrades: `{archived_clan[part]}` → `{clan[part]}`"
                            + f"\nOutput: `{archived_clan[part]/2}` → `{clan[part]/2}`",
                            color=Config.MAINCOLOR)
                        await msg.edit(embed=embed)
                    except:
                        logging.error("Issue with upgrading. Error editing message.")
                    finally:
                        if ctx.author.id in self.upgrading_users:
                            self.upgrading_users.remove(ctx.author.id)


    @clan.command(name="help")
    async def _help(self, ctx):
        prefix = Utils.fetch_prefix(ctx)
        embed=discord.Embed(title="Clan Command Help", color=Config.MAINCOLOR, description=f"`{prefix}clan` - show info about your clan\n`{prefix}clan join <name>` - join a clan\n`{prefix}clan leave` - leave your current clan\n`{prefix}clan create <name>` - create a clan\n`{prefix}clan disband` - disband a clan that you own\n`{prefix}clan claim` - claim the resources in the clan's storage\n`{prefix}clan edit <attribue> <value>` - edit a clan that you own\n`{prefix}clan upgrade <part>` - upgrade a part of your clan base\n`{prefix}clan kick <member>` - kick a member from your clan\n`{prefix}clan promote <member>` - promote a member to admin status\n`{prefix}clan demote <member>` - demote a member from admin status")
        await ctx.send(embed=embed)


    @clan.command()
    async def join(self, ctx, *, name: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            if name is None:
                prefix = Utils.fetch_prefix(ctx)
                recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
                clan_string = ""
                for rec_clan in recommended:
                    clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']), prefix,
                    rec_clan['name'])
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You must specify a clan to join!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
                await ctx.send(embed=embed)
            else:
                joining_clan = Config.CLANS.find_one({'name': name})
                if joining_clan is None:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR, description="That clan does not exist. Sorry about that.")
                    await ctx.send(embed=embed)
                elif not joining_clan['open']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="This clan is not accepting new members.")
                    await ctx.send(embed=embed)
                elif len(joining_clan['members']) >= 20:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="This clan is full!")
                    await ctx.send(embed=embed)
                else:
                    Config.CLANS.update_one({'name': name}, {'$set': {'member_count': len(joining_clan['members']) + 1, 'power': joining_clan['power'] + account['power']}, '$push': {'members': ctx.author.id}})
                    embed = discord.Embed(title="Welcome to the clan!", color=Config.MAINCOLOR, description="You have successfully joined **%s** %s" % (joining_clan['name'], joining_clan['emoji']))
                    await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"You are already in a clan. If you would like to join a new one, please use `{prefix}clan leave` first.")
            await ctx.send(embed=embed)
            
    @clan.command()
    async def claim(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            result = Config.USERS.update_many({'user_id': {'$in': clan['members']}}, {'$inc': {'coins': clan['coin_storage'], 'rubies': clan['ruby_storage'], 'xp': clan['xp_storage']}})
            logging.info("Claimed for " + str(result.modified_count) + " users.")
            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'coin_storage': 0, 'ruby_storage': 0, 'xp_storage': 0}})
            embed = discord.Embed(title="Resources Claimed", color=Config.MAINCOLOR, 
                                  description="You have claimed resources from your clan base for everyone:\n\n+`" + str(clan['ruby_storage']) + "` " + Config.EMOJI['ruby'] + "\n+`" + str(clan['xp_storage']) + "` " + Config.EMOJI['xp'] + "\n+`" + str(clan['coin_storage']) + "` " + Config.EMOJI['coin'])
            await ctx.send(embed=embed)

    @clan.command()
    async def leave(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        elif clan['owner'] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"You can't leave your own clan! If you would like to disband it, use `{prefix}clan disband`")
            await ctx.send(embed=embed)
        else:
            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                      'power': clan['power'] - account['power']},
                                                             '$pull': {'members': ctx.author.id}})
            embed = discord.Embed(title="Sad to see you go!", color=Config.MAINCOLOR,
                                  description="You have successfully left **%s** %s" % (clan['name'], clan['emoji']))
            await ctx.send(embed=embed)

    @clan.command()
    async def kick(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return
        if clan['owner'] != ctx.author.id and ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You don't have the permissions to kick somebody from the clan!")
            return await ctx.send(embed=embed)
        choice -= 1
        if member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't kick the owner of a clan!")
            await ctx.send(embed=embed)
        elif member["user_id"]in clan['admins'] and ctx.author.id != clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't kick a fellow clan admin!")
            await ctx.send(embed=embed)
        else:
            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                      'power': clan['power'] - member['power']},
                                                             '$pull': {'members': member["user_id"]}})
            discord_member = await self.bot.fetch_user(member["user_id"])
            embed = discord.Embed(title="There must be a reason...", color=Config.MAINCOLOR,
                                  description="You have successfully kicked %s from **%s** %s" % (discord_member.name, clan['name'], clan['emoji']))
            await ctx.send(embed=embed)

    @clan.command()
    async def disband(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/20`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    prefix,
                    rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        elif clan['owner'] != ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"Yopu cannot disband a clan you don't own. use `{prefix}clan leave` to leave it instead.")
            await ctx.send(embed=embed)
        else:
            Config.CLANS.delete_one({'name': clan['name']})
            embed = discord.Embed(title="There were many adventures!", color=Config.MAINCOLOR,
                                  description="You have successfully disbanded **%s** %s" % (
                                      clan['name'], clan['emoji']))
            await ctx.send(embed=embed)
            if clan['emoji_id'] != 675820506284556306:
                old_emoji = self.bot.get_emoji(clan['emoji_id'])
                await old_emoji.delete()

    @clan.command()
    async def edit(self, ctx, attribute:str=None, *, value = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan leader!")
                await ctx.send(embed=embed)
            else:
                if attribute is None:
                    attribute = "None"
                if attribute.lower() not in ['name', 'icon', 'invite']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="That's not a valid clan attribute you can change, sorry about that. Here are the things you can edit:\n`name`, `icon`, `invite`")
                    await ctx.send(embed=embed)
                else:
                    if attribute.lower() == "name":
                        if value is None:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="You can't change your clan name to nothing! Please specify a name.")
                            await ctx.send(embed=embed)
                        elif Config.CLANS.find_one({'name': value}) is not None:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="A clan already exists with that name! try using something else.")
                            await ctx.send(embed=embed)
                        elif len(value) > 30:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="That's too long! A clan name must be 30 characters or less.")
                            await ctx.send(embed=embed)
                        else:
                            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'name': value}})
                            embed = discord.Embed(title="Nice name!", color=Config.MAINCOLOR,
                                                  description="You clan is now called: **%s** %s" % (value, clan['emoji']))
                            await ctx.send(embed=embed)
                    elif attribute.lower() == "icon":
                        if len(ctx.message.attachments) < 1:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="Please upload an image or gif with the message to change the icon. (put the command in the caption)")
                            await ctx.send(embed=embed)
                        else:
                            for host in Config.CLAN_EMOTE_HOSTS:
                                guild_obj = self.bot.get_guild(host)
                                if guild_obj is None:
                                    continue
                                elif len(guild_obj.emojis) >= guild_obj.emoji_limit:
                                    continue
                                else:
                                    with open(f"temp/{ctx.message.attachments[0].filename}", 'wb+') as fp:
                                        await ctx.message.attachments[0].save(fp)
                                    with open(f"temp/{ctx.message.attachments[0].filename}", 'rb') as new_image:
                                        try:
                                            emoji = await guild_obj.create_custom_emoji(name="Clan_Icon_" + str(len(guild_obj.emojis)), image=new_image.read(), reason=ctx.author.name + " updating icon for clan " + clan['name'])
                                        except Exception as e:
                                            logging.error(str(e))
                                            continue
                                    emoji_string = ""
                                    if emoji.animated:
                                        emoji_string = "<a:" + str(emoji.name) + ":" + str(emoji.id) + ">"
                                    else:
                                        emoji_string = "<:" + str(emoji.name) + ":" + str(emoji.id) + ">"
                                    Config.CLANS.update_one({'name': clan['name']}, {'$set': {'emoji': emoji_string, 'emoji_id': emoji.id}})
                                    if clan['emoji_id'] != 675820506284556306:
                                        old_emoji = self.bot.get_emoji(clan['emoji_id'])
                                        await old_emoji.delete()
                                    embed = discord.Embed(title="Icon Changed", color=Config.MAINCOLOR,
                                                          description="Your clan's icon has changed to " + emoji_string)
                                    await ctx.send(embed=embed)
                                    return
                            embed = discord.Embed(title="Uh oh..", color=Config.MAINCOLOR,
                                                  description="We could not change your clan icon at this time. We are sorry about this.")
                            await ctx.send(embed=embed)
                    elif attribute.lower() == "invite":
                        if value is None:
                            value = ""
                        if value.lower() not in ['open', 'closed']:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="Please specify whether you want your clan to be `open` or `closed`.")
                            await ctx.send(embed=embed)
                        else:
                            if value.lower() == "open":
                                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'open': True}})
                                embed = discord.Embed(title="Clan invite status updated", color=Config.MAINCOLOR,
                                                      description="Your clan is now open and people can join!")
                                await ctx.send(embed=embed)
                            elif value.lower() == "closed":
                                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'open': False}})
                                embed = discord.Embed(title="Clan invite status updated", color=Config.MAINCOLOR,
                                                      description="Your clan is closed. Nobody can join.")
                                await ctx.send(embed=embed)
                            else:
                                embed = discord.Embed(title="oh dear", color=Config.MAINCOLOR,
                                                      description="something has gone very, very wrong.")
                                await ctx.send(embed=embed)


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
            _['health'] = round(_['health'], 1)
            _['mana'] = round(_['mana'], 1)

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


    async def construct_embeds(self, match, turn, floor, message, monster):
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
            embed.title = "Dungeon fight against " + monster['name'] + " | Floor " + str(floor)
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
            embed.title = "Dungeon fight against " + monster['name'] + " | Floor " + str(floor)
            footer_string = ""
            for effect in monster['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text=monster['name'] + " gains 8 mana at the beginning of their turn." + footer_string)
            await message.edit(embed=embed)

    async def construct_embeds_with_message(self, message, monster, turn, floor, match, text):
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
            embed.title = "Dungeon fight against " + monster['name'] + " | Floor " + str(floor)
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
            embed.title = "Dungeon fight against " + monster['name'] + " | Floor " + str(floor)
            weapon_additive_string = ""
            if 'weapon' in monster.keys():
                weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in monster.keys():
                armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            embed.description += "\n\n**" + monster['name'] + "**\nHealth: " + str(monster['health']) + "/" + str(monster['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(monster['mana']) + "/" + str(monster['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(monster['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(monster['stats']['defense']) + armor_additive_string
            embed.set_footer(text=monster['name'] + " is casting a spell.")
            await message.edit(embed=embed)

    async def dungeon_thread(self, match, message, monster, floor, clan):
        match_cache = match.copy()
        if len(match) < 1:
            Config.CLANS.update_one({'name': clan['name']}, {'$inc': {'artifacts': floor - 1}})
            embed = discord.Embed(color=Config.MAINCOLOR, description="**" + monster[
                'name'] + " Has bested the group...**\n\nYou made it past " + str(
                floor - 1) + " floors and collected " + Config.EMOJI['artifact'] + " `" + str(
                floor - 1) + "` Artifacts.")
            await message.edit(embed=embed)
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.dungeons -= 1
            return match, floor - 1, False, message
        logging.info("Dungeon thread started: Current threads: " + str(self.dungeons))
        await message.clear_reactions()
        monster['health'] = monster['stats']['health']
        monster['mana'] = monster['stats']['endurance']
        await message.delete()
        embed = discord.Embed(title="You enter floor "+str(floor)+"...", color=Config.MAINCOLOR,
                              description="[jump](" + message.jump_url + ")")
        message = await message.channel.send(", ".join(x['user'].mention for x in match), embed=embed)
        #await one_message.delete(delay=10)
        monster['effects'] = []
        for user in match:
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

        for player in match:
            broken_items = Utils.decrease_durability(player['account']['user_id'])
            if len(broken_items) > 0:
                embed = discord.Embed(title="Broken Tools", description=player['user'].mention + "! Your " + " and ".join([x['name'] for x in broken_items]) + " broke!", color=Config.MAINCOLOR)
                await message.channel.send(content=player['user'].mention, embed=embed)

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

            await self.construct_embeds(match, turn, floor, message, monster)

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
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[victim]['account']['stats']['defense']) + "` blocked)")

                    elif spell['type'] == "HEAL":
                        monster['health'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" gains `" + str(spell['damage']) + "` health.")

                    elif spell['type'] == "MANA":
                        monster['mana'] += spell['damage']
                        monster['health'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" transforms `" + str(spell['damage']) + "` health into mana.")

                    elif spell['type'] == "DRAIN":
                        monster['mana'] += spell['damage']
                        match[victim]['mana'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" stole `" + str(spell['damage']) + "` mana from "+match[victim]['user'].name+" using `" + str(spell['cost']) + "` health.")

                    elif spell['type'] == "PEN":
                        monster['stats']['strength'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" boosted their Strength from `" + str(monster['stats']['strength'] - spell['damage']) + "` to `"+str(monster['stats']['strength'])+"`")

                    elif spell['type'] == "ARMOR":
                        monster['stats']['defense'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" boosted their Defense from `" + str(monster['stats']['defense'] - spell['damage']) + "` to `"+str(monster['stats']['defense'])+"`")

                    elif spell['type'] == "POISON":
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': round(((spell['damage'] + monster['stats']['strength']) * spell['scalling']) / match[victim]['account']['stats']['defense'], 1)}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == "BLIND":
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': round((spell['damage'] + monster['stats']['strength']) * spell['scalling'] / match[victim]['account']['stats']['defense'], 1)}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + monster['stats']['strength']) * spell['scalling']) - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        monster['health'] += calculated_damage
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. "+monster['name']+" stole `" + str(spell['damage']) + "` health from "+match[victim]['user'].name)

                    elif spell['type'] == "IMPAIR":
                        before_stat = match[victim]['account']['stats']['defense']
                        match[victim]['account']['stats']['defense'] -= spell['damage']
                        if match[victim]['account']['stats']['defense'] < 1:
                            match[victim]['account']['stats']['defense'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. " + match[victim]['user'].name + "'s defense falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['defense']) + "`.")

                    elif spell['type'] == "WEAKEN":
                        before_stat = match[victim]['account']['stats']['strength']
                        match[victim]['account']['stats']['strength'] -= spell['damage']
                        if match[victim]['account']['stats']['strength'] < 1:
                            match[victim]['account']['stats']['strength'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, monster['name'] + " casted **" + spell['name'] + "**. " + match[victim]['user'].name + "'s strength falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['strength']) + "`.")

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
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(monster['stats']['defense']) + "` blocked)")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "HEAL":
                        match[turn]['health'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" gains `" + str(spell['damage']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "STUN":
                        calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        monster['health'] -= calculated_damage
                        monster['health'] = round(monster['health'], 1)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(monster['stats']['defense']) + "` blocked) the stun failed...")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "MANA":
                        match[turn]['mana'] += spell['damage']
                        match[turn]['health'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" transforms `" + str(spell['damage']) + "` health into mana.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "DRAIN":
                        match[turn]['mana'] += spell['damage']
                        monster['mana'] -= spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" stole `" + str(spell['damage']) + "` mana from "+monster['name']+" using `" + str(spell['cost']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "PEN":
                        match[turn]['account']['stats']['strength'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" boosted their Strength from `" + str(match[turn]['account']['stats']['strength'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['strength'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "ARMOR":
                        match[turn]['account']['stats']['defense'] += spell['damage']
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" boosted their Defense from `" + str(match[turn]['account']['stats']['defense'] - spell['damage']) + "` to `"+str(match[turn]['account']['stats']['defense'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "POISON":
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / monster['stats']['defense'], 1)}
                        monster['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "BLIND":
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': round((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling'] / monster['stats']['defense'], 1)}
                        monster['effects'].append(effect)
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+monster['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + match[turn]['account']['stats']['strength']) * spell['scalling']) - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[turn]['health'] += calculated_damage
                        monster['health'] -= calculated_damage
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. "+match[turn]['user'].name+" stole `" + str(spell['damage']) + "` health from "+monster['name'])
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "IMPAIR":
                        before_stat = monster['stats']['defense']
                        monster['stats']['defense'] -= spell['damage']
                        if monster['stats']['defense'] < 1:
                            monster['stats']['defense'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. " + monster['name'] + "'s defense falls from `" + str(before_stat) + "` to `" + str(monster['stats']['defense']) + "`.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "WEAKEN":
                        before_stat = monster['stats']['strength']
                        monster['stats']['strength'] -= spell['damage']
                        if monster['stats']['strength'] < 1:
                            monster['stats']['strength'] = 1
                        turn, match, monster = self.clean_up_match(turn, match, monster)
                        await self.construct_embeds_with_message(message, monster, turn, floor, match, match[turn]['user'].name + " casted **" + spell['name'] + "**. " + monster['name'] + "'s strength falls from `" + str(before_stat) + "` to `" + str(monster['stats']['strength']) + "`.")
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
                                          description="Your quest is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + message.jump_url + ")")
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

        if monster['health'] > 0 and monster['mana'] > 0:
            Config.CLANS.update_one({'name': clan['name']}, {'$inc': {'artifacts': floor - 1}})
            temp_clan = Config.CLANS.find_one({'name': clan['name']})
            if temp_clan is not None:
                if 'member_artifacts' not in temp_clan.keys():
                    temp_clan['member_artifacts'] = {}
                for guy in match_cache:
                    if str(guy['user'].id) not in temp_clan['member_artifacts'].keys():
                        temp_clan['member_artifacts'][str(guy['user'].id)] = 1
                    else:
                        temp_clan['member_artifacts'][str(guy['user'].id)] += 1
            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_artifacts': temp_clan['member_artifacts']}})

            embed = discord.Embed(color = Config.MAINCOLOR, description="**"+monster['name']+" Has bested the group...**\n\nYou made it past " + str(floor - 1) + " floors and collected "+Config.EMOJI['artifact']+" `" + str(floor - 1) + "` Artifacts.")
            await message.edit(embed=embed)
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.dungeons -= 1
            return match, floor - 1, False, message
        else:
            if not monster['titan']:
                coins_amount = random.randint(5, (len(match_cache) * 2) + 5)
            else:
                coins_amount = random.randint(5, (len(match_cache) * 3) + 5)
            mystring = "+`" + str(coins_amount) + "` " + Config.EMOJI['coin']
            for user in match_cache:
                user['account'] = Utils.get_account(user['user'].id)
                Config.USERS.update_one({'user_id': user['user'].id}, {'$inc': {'coins': coins_amount}})
            if monster['health'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has been killed!**\n\nEveryone gets:\n\n" + mystring + "\nCurrent Artifacts Collected: " + str(floor) + " "+Config.EMOJI['artifact']+"\nNext Floor: " + str(floor + 1))
            elif monster['mana'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has fainted!**\n\nEveryone gets:\n\n" + mystring + "\nCurrent Artifacts Collected: " + str(floor) + " "+Config.EMOJI['artifact']+"\nNext Floor: " + str(floor + 1))
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster['name'] + " has been destroyed completely!**\n\nEveryone gets:\n\n" + mystring + "\nCurrent Artifacts Collected: " + str(floor) + " "+Config.EMOJI['artifact']+"\nNext Floor: " + str(floor + 1))
            await message.edit(embed=embed)
            await asyncio.sleep(15)
            return match, floor + 1, True, message

    @commands.command()
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def dungeon(self, ctx):
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
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon", description="You are already in a dungeon. Please finish that quest first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.waiting_users:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon", description="You are already entering a dungeon. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.channel.id in self.active_channels:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon", description="This channel is already exploring a dungeon. Please finish that quest first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon",
                                  description="You are not part of a clan. Dungeons are meant to get Artifacts for clans. Go create or join a clan to be able to explore dungeons!")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        self.waiting_users.append(ctx.author.id)
        self.active_channels.append(ctx.channel.id)


        embed=discord.Embed(color=Config.MAINCOLOR, title=ctx.author.name + " Is entering a Dungeon for the **`" + str(clan['name']) + "`** clan<a:dots:715134569355018284>", description="The quest will begin in 1 minute. React to join.", timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
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
                    await msg.edit(embed=discord.Embed(title="Dungeon Quest canceled", color = Config.MAINCOLOR, description=ctx.author.name + " has disbanded the quest..."))
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
                    error_msg = await ctx.send(embed=discord.Embed(title="You don't have an account", color = Config.MAINCOLOR, description="Type `]profile` to choose a class and react again to join the party!"))
                    await error_msg.delete(delay=20)
                    continue
                elif user.id in self.waiting_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already entering", color = Config.MAINCOLOR, description="You are already entering a dungeon!"))
                    await error_msg.delete(delay=20)
                    await reaction.remove(user)
                    continue
                elif user.id in self.battling_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already exploring", color = Config.MAINCOLOR, description="You are already exploring a dungeon!"))
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
        self.dungeons += 1
        do_continue = True
        floors = 1
        match_copy = match.copy()

        for i in range(len(match)):
            self.battling_users.append(match[i]['user'].id)

        while do_continue:
            monster_class = random.choice(list(Config.CLASSES.find({})))
            spells = list(Config.SPELLS.find({'class': monster_class['name'], 'type': {'$nin': ['STUN']}}).limit(6))
            if floors > 5:
                monster = {'name': Utils.make_monster_name_titan(), 'titan': True, 'spells': spells, 'armor': {'name': "Titan's Breastplate", 'effect': random.randint(3, 10), 'emoji': "<:helmet:675820506284556306>"}, 'weapon': {'name': "Aged Sword", 'effect': random.randint(3, 10), 'emoji': "<:battle:670882198450339855>"}, 'stats': {'health': random.randint(200, 200), 'strength': random.randint(3, 10), 'defense': random.randint(4, 8), 'endurance': random.randint(200, 300)}}
            else:
                strength = statistics.mean(x['account']['stats']['defense'] for x in match_copy) + random.randint(-1, 1)
                defense = statistics.mean(x['account']['stats']['strength'] for x in match_copy) + random.randint(-1, 1)
                if strength < 3:
                    strength = 3
                if defense < 3:
                    defense = 3
                monster = {'name': Utils.make_monster_name(), 'titan': False, 'spells': spells, 'stats': {'health': random.randint(100, 200), 'strength': strength, 'defense': defense, 'endurance': random.randint(90, 150)}}
            for user in match:
                # if user["account"]["armor"] is not None:
                #     if user["account"]["armor"]["effect"] >= 10:
                #         monster['stats']['strength'] += 3
                #     else:
                #         monster['stats']['strength'] += 1
                # else:
                #     monster['stats']['strength'] += 1
                # if user["account"]["weapon"] is not None:
                #     if user["account"]["weapon"]["effect"] >= 10:
                #         monster['stats']['health'] += 50
                #     else:
                #         monster['stats']['health'] += 10
                # else:
                #     monster['stats']['health'] += 10
                # if user["account"]["class"] == "Arcane":
                #     monster['stats']['endurance'] += 50
                # else:
                #     monster['stats']['endurance'] += 10
                # monster['stats']['defense'] += 0.2
                if user["account"]["user_id"] in self.waiting_users:
                    self.waiting_users.remove(user["account"]["user_id"])

            if 'weapon' in monster.keys():
                monster['stats']['strength'] += monster['weapon']['effect']
            if 'armor' in monster.keys():
                monster['stats']['defense'] += monster['armor']['effect']

            for i in range(len(match)):
                if match[i]['account']['armor'] is not None:
                    match[i]['account']['stats']['defense'] += match[i]['account']['armor']['effect']
                if match[i]['account']['weapon'] is not None:
                    match[i]['account']['stats']['strength'] += match[i]['account']['weapon']['effect']

            monster['stats']['strength'] = round(monster['stats']['strength'])
            monster['stats']['defense'] = round(monster['stats']['defense'])
            monster['stats']['health'] = round(monster['stats']['health'])
            try:
                match, floors, do_continue, msg = await self.dungeon_thread(match, msg, monster, floors, clan)
            except Exception as e:
                for user in match_copy:
                    if user['user'].id in self.battling_users:
                        self.battling_users.remove(user['user'].id)
                if msg.channel.id in self.active_channels:
                    self.active_channels.remove(msg.channel.id)
                self.dungeons -= 1
                raise e
                return
        for user in match_copy:
            if user['user'].id in self.battling_users:
                self.battling_users.remove(user['user'].id)
        if msg.channel.id in self.active_channels:
            self.active_channels.remove(msg.channel.id)
        self.dungeons -= 1

    @dungeon.error
    async def dungeon_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..", description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"), color = Config.ERRORCOLOR)


def setup(bot):
    bot.add_cog(Clans(bot))
