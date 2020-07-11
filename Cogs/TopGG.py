import datetime
import random

import dbl
import discord
from discord.ext import commands, tasks
import logging

import Config
import Utils


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = 'DBL_TOKEN'
        self.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path='/dblpath',
                                   webhook_auth="AUTH_SECRET", webhook_port=3001)
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count"""
        logger.info('Attempting to post server count')
        try:
            await self.dblpy.post_guild_count()
            logger.info('Posted server count ({})'.format(self.dblpy.guild_count()))
        except Exception as e:
            logger.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        data['user'] = int(data['user'])
        account = Utils.get_account(data['user'])
        print(data)
        decide_reward = random.randint(1, 3)
        if decide_reward == 1:
            chest_amount = 1
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`1` Chest",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if data['isWeekend']:
                chest_amount = 2
                embed = discord.Embed(title="Vote Redeemed",
                                      description="Thanks for voting. You have redeemed:\n\n`2` Chests",
                                      color=Config.MAINCOLOR,
                                      timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'chests': chest_amount}})
        elif decide_reward == 2:
            amount = random.randint(20, 50)
            if data['isWeekend']:
                amount *= 2
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`"+str(amount)+"` Rubies",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if data['isWeekend']:
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'rubies': amount}})
        elif decide_reward == 3:
            amount = random.randint(20, 70)
            if data['isWeekend']:
                amount *= 2
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`"+str(amount)+"` Coins",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if data['isWeekend']:
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'coins': amount}})
        try:
            user = await self.bot.fetch_user(int(data['user']))
            await user.send(embed=embed)
        except Exception as e:
            logging.error(
                'Error occured in voting. Could not find user, or could not DM user. Ignore this as it is not a big deal. But kinda is idk. Its just not the best outcome.')
        logger.info('Received a (' + data['type'] + ') action from : ' + str(data['user']))

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        logger.info('Received a (' + data['type'] + ') action from : ' + str(data['user']))


def setup(bot):
    global logger
    logger = logging.getLogger('bot')
    bot.add_cog(TopGG(bot))
