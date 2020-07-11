import Config
import discord
from discord.ext import commands
import Utils

class Spells(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def make_spell(self, ctx, class_name:str=None, effect:int=None, scaling:int=None, emoji:str=None, cost:int=None, type:str=None, *, name:str=None):
        if ctx.author.id not in Config.OWNERIDS:
            return
        prefix = Utils.fetch_prefix(ctx)
        if None in [class_name, scaling, emoji, cost, type, name] or type not in ['DAMAGE', 'STUN', 'MANA', 'STEAL', 'ARMOR', 'PEN', 'POISON', 'HEAL'] or class_name not in ['Paladin', 'Druid', 'Arcane']:
            await ctx.send(f"You need to use this command like this: `{prefix}make_spell <class> <effect> <scailing> <emoji> <cost> <type> <name>`. The ID will be generated automatically. Types are:\nDAMAGE, STUN, HEAL, MANA, PEN, ARMOR, POISON, STEAL\nClasses are: Paladin, Druid, Arcane")
        else:
            top_id = 0
            id = Config.SPELLS.count_documents({'class': class_name})
            spell = {'name': name, 'class': class_name, 'id': id, 'damage': effect, 'scalling': scaling, 'emoji': emoji, 'cost': cost, 'type': type}
            Config.SPELLS.insert_one(spell)
            await ctx.send(embed=discord.Embed(color = Config.MAINCOLOR, title="Spell created for class " + class_name + " ID: " + str(id), description = "> " + spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost] [ "+str(spell['scalling'])+" scaling]"))


    @commands.command(aliases=['enchants', 's', 'spell'])
    async def spells(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        user_spells = Utils.get_users_spells(account)


        if len(user_spells) < 1:
            embed=discord.Embed(color = Config.MAINCOLOR, title="Spells", description="You have no spells. This is an issue. A very big one. Please contact support so you can tell us how we messed up. :)")
        else:
            spell_string = ""
            equipped_string = ""
            for spell in account['slots']:
                if spell is None:
                    equipped_string += "\n> *Nothing is written on this page...*"
                    continue
                for _ in user_spells:
                    if spell == _['id']:
                        spell = _
                if spell is not None:
                    equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost]"
            total = 0
            amount_of_slots = 0
            for spell in user_spells:
                if spell['id'] in account['slots']:
                    total += spell['cost']
                    amount_of_slots += 1
            for spell in user_spells:
                spell_string += "\n"+spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost] [ "+str(spell['scalling'])+" scaling]"
                #embed.add_field(name=spell['name'] + " " + spell['emoji'], value="**Cost:** " + str(spell['cost']) + "\n**Damage:** " + str(spell['damage']) + "\n**Scalling:** " + str(spell['scalling']))
            prefix = Utils.fetch_prefix(ctx)
            embed=discord.Embed(color = Config.MAINCOLOR, title="Spells", description="**Spellbook** (Average Spell Cost: "+ str(total / amount_of_slots) + ")\nThe spells you take with you on your travels."+equipped_string+"\n\n**Library**\na list of all spells you have learned.\n" + spell_string)
            embed.set_footer(text=f"Use {prefix}equip <slot> <spell> to equip a spell.")
        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command(aliases=['e'])
    async def equip(self, ctx, slot:int=1, *, name:str=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if slot > 4:
            embed=discord.Embed(color=Config.ERRORCOLOR, description="Spell slot must be between 1 and 4.")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        elif name.lower() not in [x['name'].lower() for x in Utils.get_users_spells(account)] and name.lower() != "none":
            embed=discord.Embed(color=Config.ERRORCOLOR, description="You do not know that spell...")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            slot -= 1
            if name.lower() == 'none':
                spell = Utils.get_spell(account['class'], Utils.equip_spell(ctx.author.id, None, slot))
                if account['slots'][slot] is None:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="You wrote nothing on a blank page...")
                else:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(spell['name'])+"' has been erased from your spellbook")
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            spell = Utils.get_spell_by_name(account['class'], name)
            if spell['id'] in account['slots']:
                embed=discord.Embed(color=Config.ERRORCOLOR, description="This spell is already written in your spellbook on page " + str(account['slots'].index(spell['id']) + 1))
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            Utils.equip_spell(ctx.author.id, spell['id'], slot)
            if account['slots'][slot] is not None:
                embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(Utils.get_spell(account['class'], account['slots'][slot])['name'])+"' has been replaced with '"+str(spell['name'])+"' in your spellbook")
            else:
                embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(spell['name'])+"' has been written on page "+str(slot + 1)+" of your spellbook")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Spells(bot))
