import asyncio

import Config
import discord
from discord.ext import commands
import Utils


class Contract(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['season', 'xp'])
    async def contract(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if 'claimed_contract' not in account.keys():
            account['claimed_contract'] = {}

        if str(Config.ACTIVE_CONTRACT) not in account['claimed_contract'].keys():
            account['claimed_contract'][str(Config.ACTIVE_CONTRACT)] = 0

        current_tier, current_tier_number = Utils.get_contract_tier(account['xp'])
        print(current_tier)
        print(current_tier_number)

        bar_string = list("╠═══════════════════════╬═════════════════════════╣")

        if int(current_tier_number) >= len(Config.CONTRACTS[Config.ACTIVE_CONTRACT]):
            index = 50
        elif int(current_tier_number) > 1:
            index = (account['xp'] - Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 1)]['xp']) / (Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['xp'] - Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 1)]['xp'])
        else:
            index = account['xp'] / Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)]['xp']
        if round(index * 100) > (len(bar_string) - 1):
            index = (len(bar_string) - 1) / 100
        if round(index * 100) <= 0:
            index = 0
        bar_string[round(index * 100)] = "="

        embed = discord.Embed(title="Contract 00" + str(Config.ACTIVE_CONTRACT + 1), color=Config.MAINCOLOR, description="Current Tier: "+str(int(current_tier_number) - 1)+"\nXP until next tier: "+str("{:,}".format(current_tier['xp'] - account['xp']))+"\n```fix\n"""+"".join(bar_string)+"```")

        if int(current_tier_number) >= len(Config.CONTRACTS[Config.ACTIVE_CONTRACT].keys()):
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 2)]['name'],
                            value="`" + str("{:,}".format(
                                Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 2)][
                                    'xp'])) + " XP`\n✅ CLAIMED!")
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)]['name'],
                            value="`" + str("{:,}".format(
                                Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)][
                                    'xp'])) + " XP`\n✅ CLAIMED!")
            if account['xp'] > Config.CONTRACTS[Config.ACTIVE_CONTRACT][len(Config.CONTRACTS[Config.ACTIVE_CONTRACT])]:
                embed.add_field(name=current_tier['name'], value="`" + str("{:,}".format(current_tier['xp'])) + "`\n✅ CLAIMED!")
            else:
                embed.add_field(name=current_tier['name'], value="`" + str("{:,}".format(current_tier['xp'])) + "`\n" + str("{:,}".format(current_tier['xp'] - account['xp'])) + " XP to go")
        elif int(current_tier_number) > 1:
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 1)]['name'], value="`"+str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) - 1)]['xp']))+" XP`\n✅ CLAIMED!")
            embed.add_field(name=current_tier['name'], value="`"+str("{:,}".format(current_tier['xp']))+"`\n"+str("{:,}".format(current_tier['xp'] - account['xp']))+" XP to go")
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['name'],
                            value="`"+str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['xp']))+" XP`\n"+str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['xp'] - account['xp']))+" XP to go")
        else:
            embed.add_field(name=current_tier['name'], value="`" + str("{:,}".format(current_tier['xp'])) + "`\n" + str(
                "{:,}".format(current_tier['xp'] - account['xp'])) + " XP to go")
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['name'],
                            value="`" + str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['xp'])) + " XP`\n" + str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 1)]['xp'] - account['xp'])) + " XP to go")
            embed.add_field(name=Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)]['name'],
                            value="`" + str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)]['xp'])) + " XP`\n" + str("{:,}".format(Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(int(current_tier_number) + 2)]['xp'] - account['xp'])) + " XP to go")

        await ctx.channel.send(embed=embed)




def setup(bot):
    bot.add_cog(Contract(bot))
