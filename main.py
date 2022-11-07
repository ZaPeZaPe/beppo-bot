import os
from json import load

import dotenv
from discord import (ApplicationContext, Embed, Intents, Option, OptionChoice,
                     User)
from discord.ext import commands
from discord.ui import View, button
from pymongo import MongoClient

intents=Intents.default();intents.members=True;intents.message_content=True
beppo=commands.Bot(command_prefix='$$$', intents=intents);beppo.remove_command('help')
dotenv.load_dotenv();dbpass=os.getenv("dbpass");apikey=os.getenv("API_KEY")
cluster = MongoClient(f"mongodb+srv://bppbot:{dbpass}@cluster0.wqcjs.mongodb.net/Beppo?retryWrites=true&w=majority")
db = cluster["Beppo"]
embedColor = 0x9859C8

with open('json/help.json', 'r') as rh:
    helpGuide = load(rh)

class MyHelpView(View):
    def __init__(self, ctx, index=0):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.index = index

    @button(emoji="<:coinleft:1002959962810617940>")
    async def left_button_callback(self, button, interaction):
        self.index -= 1
        await interaction.response.edit_message(embed=createHelpEmbed(pageNum=self.index))

    @button(emoji="<:coinright:1002959964534476820>")
    async def right_button_callback(self, button, interaction):
        self.index += 1
        await interaction.response.edit_message(embed=createHelpEmbed(pageNum=self.index))

    async def on_timeout(self):
        self.disable_all_items()
        await self.interaction.edit_original_message(view=self)

def createHelpEmbed(pageNum=0, inline=False):
    pageNum = pageNum % len(list(helpGuide))
    pageTitle = list(helpGuide)[pageNum]
    string=""
    for key, val in helpGuide[pageTitle].items():
        string += f"{key}: {val}.\n"
    embed = Embed(color=embedColor, title=pageTitle, description=string)
    embed.set_footer(
        text=f"Page {pageNum + 1}/{len(list(helpGuide))}"
    )
    return embed

for f in os.listdir("./cogs"):
	if f.endswith(".py") and not f.endswith("Cooldown.py"):
		beppo.load_extension("cogs." + f[:-3], store=False)

# for slash_commands checks=[commands.is_owner().predicate]
@beppo.slash_command(name="help", description="Shows the command list")
async def help(ctx):
    view = MyHelpView(ctx)
    view.interaction = await ctx.respond(embed=createHelpEmbed(),view=view, ephemeral=True)

@beppo.slash_command(name="help_crypto", description="Provides information about a the data given in /crypto symbol", usage="/infocrypto")
async def help_crypto(ctx):
    await infoCryptoCommand(ctx)

@beppo.slash_command(name="level", description="Shows the level of the user", usage="/level (user optional)")
async def level(
        ctx,
        user: Option(User, description="User (Optional)", default=None)
):
    await levelCommand(ctx, user)

@beppo.slash_command(name="ping", description="Shows bot latency", usage="/ping")
async def ping(ctx):
    await pingCommand(ctx)

@beppo.slash_command(name="serverinfo", description="Shows the server information", usage="/serverinfo (id optional)")
async def serverinfo(
        ctx: ApplicationContext,
        serverid: Option(str, description="Id of the server (Optional)", default=None)
):
    if serverid!=None:
        serverid = int(serverid)
    else:
        serverid = ctx.guild.id
    await serverInfoCommand(ctx, serverid)

seemore = beppo.create_group("seemore", "Commands to enable/disable some info in crypto exibition.")

@seemore.command(name="intervals", description="Shows more time intervals in /crypto symbol")
async def intervals(ctx):
    await seeMoreIntervals(ctx)

@seemore.command(name="names", description="Shows the currencies names")
async def names(ctx):
    await seeMoreNames(ctx)

@seemore.command(name="prices", description="Shows the currencies prices")
async def prices(ctx):
    await seeMorePrices(ctx)

@seemore.command(name="percentages", description="Shows the currencies percentages, to disable you must use this command while enabled.")
async def percentages(
        ctx,
        timestamp:
            Option(
                int,
                description="Timestamp (Default = 1h)",
                choices=[
                    OptionChoice(name="1h", value=1),
                    OptionChoice(name="24h", value=24),
                    OptionChoice(name="7d", value=7),
                    OptionChoice(name="30d", value=30),
                    OptionChoice(name="60d", value=60),
                    OptionChoice(name="90d", value=90),
                ],
                default=1
            )
):
    await seeMorePercentages(ctx, timestamp)

#METHODS SECTION

async def infoCryptoCommand(ctx):
    embed = Embed(
        title="**Criptocurrency Info**",
        description=f"__**Beppo Wallet Command**__:\nBPPC = Beppo Coin\nBPPC P/MSG = Beppo Coins per message (with an interval of 1 minute between every message)\n\n"
                    f"__**Price Section**__:\nThe current price of the cryptocurrency.\n\n"
                    f"__**PChange (Price change) Section**__:\nThe percentage of change between the interval given (1hr, 24hr, 7d\*, 30d\*, 60d\*, 90d\*).\n\n"
                    f"__**Vol. (Volume) Section**__:\nA measure of how much of a cryptocurrency was traded in the last 24 hours.\n\n"
                    f"__**MarketCap (Market Capitalization) Section**__:\nThe total market value of a cryptocurrency's circulating supply.\nIt is analogous to the free-float capitalization in the stock market.\nMarket Cap = Current Price x Circulating Supply.\n",
        color=embedColor
    )
    embed.set_footer(text="*If used the command /seemoreintervals")
    await ctx.respond(embed=embed, ephemeral=True)

async def levelCommand(ctx, user):
    if user==None:
        user = ctx.author

    userCollection = db['users']
    findUser = userCollection.find_one({"_id": user.id})

    if findUser == None:
        raise IndexError("User not found...")

    level = findUser['level']

    embed = Embed(
        title=f"✨ {user.display_name} is level {level}! ✨",
        color=embedColor
    )
    await ctx.respond(embed=embed)

async def pingCommand(ctx):
    embed = Embed(
        title="🏓 Pong",
        description=f"**{round(beppo.latency * 1000)}ms**",
        color=embedColor
    )
    await ctx.respond(embed=embed, ephemeral=True)

async def serverInfoCommand(ctx, server):
    if server!=ctx.guild.id:
        server = beppo.get_guild(server)
    else:
        server = ctx.guild

    serverCollection = db['servers']

    try :
        findServer = serverCollection.find_one({"_id": server.id})
    except Exception:
        raise IndexError("Invalid ID...")

    if findServer == None:
        raise IndexError("I'm not in that guild...")

    name = server.name
    description = server.description
    icon = server.icon
    memberCount = server.member_count
    owner = str(server.owner)
    id = server.id
    wage = findServer['wage']
    embed = Embed(
        title=name,
        color=embedColor
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=False)
    embed.add_field(name="Member Count", value=memberCount, inline=False)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Server $BPPC p/msg", value="``$"+str(wage)+"``", inline=True)
    embed.set_footer(text=f"Nivel do servidor: {findServer['level']}")
    await ctx.respond(embed=embed)

async def seeMoreIntervals(ctx):
    userCollection = db['users']
    user = userCollection.find_one({"_id": ctx.author.id})

    if user['seemore']['intervals']:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.intervals": False}})
        await ctx.respond("See more intervals *disabled*", ephemeral=True)
    else:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.intervals": True}})
        await ctx.respond("See more intervals *enabled*", ephemeral=True)

async def seeMoreNames(ctx):
    userCollection = db['users']
    user = userCollection.find_one({"_id": ctx.author.id})

    if user['seemore']['seenames']:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.names": False}})
        await ctx.respond("See names *disabled*", ephemeral=True)
    else:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.names": True}})
        await ctx.respond("See names *disabled*", ephemeral=True)

async def seeMorePrices(ctx):
    userCollection = db['users']
    user = userCollection.find_one({"_id": ctx.author.id})

    if user['seemore']['prices']:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.prices": False}})
        await ctx.respond("See prices *disabled*", ephemeral=True)
    else:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.prices": True}})
        await ctx.respond("See prices *enabled*", ephemeral=True)

async def seeMorePercentages(ctx, timestamp):
    userCollection = db['users']
    user = userCollection.find_one({"_id": ctx.author.id})

    if user['seemore']['percentages']['enabled']:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.percentages.enabled": False}})
        await ctx.respond("See percentages *disabled*", ephemeral=True)
    else:
        userCollection.update_one({"_id": user['_id']}, {"$set": {"seemore.percentages": {'enabled':True, 'timestamp':timestamp}}})
        await ctx.respond(f"See {stringstampsint(timestamp)} percentages *enabled*", ephemeral=True)

def stringstampsint(tempo):
    options = {
        1: "1h",
        24: "24h",
        7: "7d",
        30: "30d",
        60: "60d",
        90: "90d"
    }
    return options.get(tempo)

beppo.run(os.getenv("TOKEN"))