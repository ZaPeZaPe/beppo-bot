from datetime import datetime
from json import dump, load

from discord import Embed
from discord.ext import commands

from main import db, embedColor


class Owner(commands.Cog):

    def __init__(self, beppo):
        self.beppo = beppo

    @commands.Cog.listener()
    async def on_ready(self):
        print("Owner Commands Loaded & Ready!")

    @commands.command(name="wage", description="owner", usage="$$$wage id amount")
    @commands.is_owner()
    async def wage(self, ctx, *, args:str):
        async with ctx.typing():
            await self.wageCommand(ctx, args)

    @commands.command(name="embed", description="owner", usage="$$$embed")
    @commands.is_owner()
    async def embed(self, ctx, *, args=None):
        async with ctx.typing():
            await self.embedCommand(ctx)

    @commands.command(name="reload", description="owner", usage="$$$reload extension")
    @commands.is_owner()
    async def reload(self, ctx, extension):
        async with ctx.typing():
            self.beppo.reload_extension(f"cogs.{extension}")
            await ctx.reply("Done!", mention_author=False)

    @commands.command(name="unload", description="owner", usage="$$$unload extension")
    @commands.is_owner()
    async def unload(self, ctx, extension):
        async with ctx.typing():
            self.beppo.unload_extension(f"cogs.{extension}")
            await ctx.reply("Done!", mention_author=False)

    @commands.command(name="hello", description="owner", usage="$$$hello")
    @commands.is_owner()
    async def hello(self, ctx):
        async with ctx.typing():
            await ctx.reply("test", mention_author=False)

    @commands.command(name="addxp", description="owner", usage="$$$addxp id xp")
    @commands.is_owner()
    async def addxp(self, ctx, id: int, xp: int):
        userCollection = db['users']
        await self.addCommand(ctx, userCollection, id, xp, 'experience')

    @commands.command(name="addbal", description="owner", usage="$$$addbal id amount")
    @commands.is_owner()
    async def addbal(self, ctx, id: int, amount: float):
        userCollection = db['users']
        await self.addCommand(ctx, userCollection, id, amount, 'balance')

    @commands.command(name="setimage", description="owner", usage="$$$setimage symbol link.jpg")
    @commands.is_owner()
    async def setimage(self, ctx, symbol: str, link: str):
        async with ctx.typing():
            imageCollection = db['images']
            currencyCollection = db['currencies']
            await self.update_image(imageCollection, ctx, symbol, link, currencyCollection)

    @commands.command(name="refreshimages", description="owner", usage="$$$refreshimages")
    @commands.is_owner()
    async def refreshimages(self, ctx):
        async with ctx.typing():
            with open('data/images.json', 'r') as f:
                images = load(f)
            imageCollection = db['images']
            currencyCollection = db['currencies']
            await self.update_images(images, imageCollection, currencyCollection)
            await ctx.message.add_reaction("✅")

    #METHODS SECTION

    async def wageCommand(self, ctx, args):
        args = args.split()
        if len(args) > 1:
            elementid = args[0]
            for am in args[1]:
                if not am.isnumeric():
                    await ctx.reply("Invalid amount input", mention_author=False)
                    return
            amount = int(args[1])
        else:
            elementid = None
            for am in args[0]:
                if not am.isnumeric():
                    await ctx.reply("Invalid amount input", mention_author=False)
                    return
            amount = int(args[0])

        if elementid != None:
            id = ""
            if not elementid.isalpha():
                for s in elementid:
                    if s.isnumeric():
                        id += s
                    else:
                        id += ""
        else:
            id = str(ctx.author.id)

        userCollection = db['users']
        serverCollection = db['servers']
        element = userCollection.find_one({"_id": int(id)})
        server = False

        if element == None:
            element = serverCollection.find_one({"_id": int(id)})
            if element == None:
                await ctx.reply("Server or Member id not found...", mention_author=False)
                return
            server = True

        if not server:
            userCollection.update_one({"_id": int(id)}, {"$set": {"perswage": amount}})
            await ctx.reply(f"The wage of the user has been set to ${amount}")
        else:
            serverCollection.update_one({"_id": int(id)}, {"$set": {"wage": amount}})
            await ctx.reply(f"The wage of the server has been set to ${amount}")

    async def embedCommand(self, ctx):
        embed = Embed(
            title="title",
            description="description",
            color=embedColor,
            url="https://monkeytype.com",
            timestamp=datetime.now()
        )
        embed.set_footer(text="footer")
        embed.set_thumbnail(url="https://imgur.com/c2Dfniq.jpg")
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=False
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=False
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.add_field(
            name="field name",
            value="field value",
            inline=True
        )
        embed.set_image(url="https://imgur.com/c2Dfniq.jpg")
        await ctx.reply(embed=embed, mention_author=False)

    async def addCommand(self, ctx, userCollection, id, amount, target):
        findUser = userCollection.find_one({"_id": id})
        if findUser != None:
            if not amount:
                userCollection.update_one({"_id": id}, {"$set": {target: 0}})
            else:
                userCollection.update_one({"_id": id}, {"$inc": {target: amount}})
        else:
            await ctx.reply("User not found...", delete_after=5, mention_author=False)
            return
        await ctx.message.add_reaction('✅')

    async def update_images(self, images, imageCollection, currencyCollection):
        stringNotOk = "Were added: "
        findCurrencies = currencyCollection.find({})
        for coin in findCurrencies:
            if coin['symbol'] not in images:
                imageCollection.insert_one({
                    "_id" : coin['symbol'],
                    f"{coin['symbol']}" : "https://imgur.com/jCypPaT.gif"
                })
                stringNotOk += f"{coin['symbol']} "
                images[coin['symbol']] = {}
        with open('data/images.json', 'w') as u:
            dump(images, u)
        print(stringNotOk)

    async def update_image(self, imageCollection, ctx, symbol, link, currencyCollection):
        found=False
        symbol = symbol.upper()
        findCurrencies = currencyCollection.find({})
        for coin in findCurrencies:
            if findCurrencies['symbol'] == symbol:
                imageCollection.update_one({"_id": findCurrencies['symbol']}, {"$set": {f"{symbol}": str(link)}})
                found=True
        if not found:
            await ctx.message.add_reaction("❌")
        else:
            await ctx.message.add_reaction("✅")

def setup(beppo):
    beppo.add_cog(Owner(beppo))