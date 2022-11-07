from math import floor, log10

from discord import (ApplicationContext, ButtonStyle, Embed, Option,
                     OptionChoice, SlashCommandGroup, User)
from discord.ext import commands
from discord.ui import View, button

from main import db, embedColor, load

br='\n'
blank=''
positive='+'
millnames = ['',' Thousand',' Million',' Billion',' Trillion']
bSpace=' \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b \u200b'
LIMITE=15

class MyListView(View):
    def __init__(self, ctx, embeds, index):
        super().__init__(timeout=10)
        self.ctx = ctx
        self.embeds = embeds
        self.index = index

    @button(emoji="<:coinleft:1002959962810617940>")
    async def left_button_callback(self, button, interaction):
        self.index -= 1
        self.index = self.index % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index])

    @button(emoji="<:coinright:1002959964534476820>")
    async def right_button_callback(self, button, interaction):
        self.index += 1
        self.index = self.index % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index])

    async def on_timeout(self):
        self.disable_all_items()
        await self.interaction.edit_original_message(view=self)

class MyOperationView(View):
    def __init__(self, ctx, embed, inWallet, total, amount, symbol, string, userCollection, findUser, pop=False):
        super().__init__(timeout=5)
        self.ctx = ctx
        self.embed = embed
        self.inWallet = inWallet
        self.total = total
        self.amount = amount
        self.symbol = symbol
        self.string = string
        self.userCollection = userCollection
        self.findUser = findUser
        self.pop = pop

    @button(label="Yes", style=ButtonStyle.success)
    async def left_button_callback(self, button, interaction):
        self.disable_all_items()
        self.embed = Embed(
            title=f"💸 Operation successful! ✅",
            description=self.string,
            color=embedColor
        )
        self.embed.set_footer(text=f"✅ Data Saved")
        if not self.inWallet:
            self.userCollection.update_one({"_id": self.ctx.author.id}, {
                "$set": {f"wallet.{self.symbol}": self.total},
                "$inc": {"balance": self.amount}
            })
        else:
            if not self.pop:
                self.userCollection.update_one({"_id": self.ctx.author.id}, {"$inc": {
                    f"wallet.{self.symbol}": self.total,
                    "balance": self.amount
                }})
            else:
                self.userCollection.update_one({"_id": self.ctx.author.id}, {
                    "$unset": {f"wallet.{self.symbol}": ""},
                    "$inc": {"balance": self.amount}
                })
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(label="No", style=ButtonStyle.danger)
    async def right_button_callback(self, button, interaction):
        self.embed.set_footer(text=f"❌ Operation declined")
        self.disable_all_items()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def on_timeout(self):
        self.disable_all_items()
        if (self.embed.footer.text != Embed.Empty):
            await self.interaction.edit(view=self)
        else:
            self.embed.set_footer(text=f"❌ Operation expired")
            await self.interaction.edit(embed=self.embed, view=self)

    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

with open('./json/chips.json', 'r') as rh:
    arcadeChips = load(rh)

def arcadeEmbed(pageNum=0, inline=False):
    pageNum = pageNum % (len(list(arcadeChips))-1)
    arcadeTitle = list(arcadeChips)[3]
    arcadeDescription = arcadeChips[arcadeTitle]
    pageTitle = list(arcadeChips)[pageNum]
    string=""
    for key, val in arcadeChips[pageTitle].items():
        string += f"{key}: {val}\n"
    embed = Embed(color=embedColor, title=arcadeTitle, description=arcadeDescription)
    embed.add_field(
        name=pageTitle,
        value=string,
        inline=False
    )
    embed.set_footer(
        text=f"Page {pageNum + 1}/{len(list(arcadeChips))-1}"
    )
    return embed

class MyArcadeView(View):
    def __init__(self, ctx, index=0):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.index = index

    @button(emoji="<:coinleft:1002959962810617940>")
    async def left_button_callback(self, button, interaction):
        self.index -= 1
        await interaction.response.edit_message(embed=arcadeEmbed(pageNum=self.index))

    @button(emoji="<:coinright:1002959964534476820>")
    async def right_button_callback(self, button, interaction):
        self.index += 1
        await interaction.response.edit_message(embed=arcadeEmbed(pageNum=self.index))

    async def on_timeout(self):
        self.disable_all_items()
        await self.interaction.edit_original_message(view=self)

    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

class Crypto(commands.Cog):

    def __init__(self, beppo):

        self.beppo = beppo

    @commands.Cog.listener()
    async def on_ready(self):
        print("Crypto Loaded & Ready!")

    crypto = SlashCommandGroup("crypto", "Crypto economy commands.")

    @crypto.command(name="beppowallet", description="Shows user's beppo wallet", usage="/beppowallet (user optional)")
    async def beppowallet(
            self,
            ctx: ApplicationContext,
            user: Option(User, description="Wallet from the user that you choose (Optional)", default=None)
    ):
        if user==None:
            user = ctx.author
        id = user.id
        name = user.name

        userCollection = db['users']
        serverCollection = db['servers']

        findUser = userCollection.find_one({"_id": user.id})
        findServer = serverCollection.find_one({"_id": ctx.guild.id})

        if findUser == None:
            raise IndexError(f"{name}'s Beppo Wallet not found...")

        if findUser['perswage'] > findServer['wage']:
            wage = findUser['perswage']
        else:
            wage = findServer['wage']

        embed = Embed(
            title=f"💰 {name}'s Beppo Wallet",
            description=f"BPPC: ``${findUser['balance']:.2f}``\n"
                        f"BPPC p/msg: ``${wage}``",
            color=embedColor
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text="/help_crypto for more info")
        await ctx.respond(embed=embed)

    @crypto.command(name="wallet", description="Shows user's crypto wallet", usage="/cryptowallet (user optional) (symbol optional)")
    async def wallet(
            self,
            ctx: ApplicationContext,
            user: Option(User, discription="Wallet from the user you choose (Optional)", default=None),
            symbol: Option(str, discription="Symbol of the crypto you choose (Optional)", default=None)
    ):
        if user == None:
            user = ctx.author

        userCollection = db['users']
        imageCollection = db['images']
        currencyCollection = db['currencies']

        findUser = userCollection.find_one({"_id": user.id})
        findCurrencies = currencyCollection.find({})

        totalprice=0
        string=""
        if symbol == None:
            for item in findUser['wallet']:
                for coin in findCurrencies:
                    if coin['symbol'] == item:
                        totalprice += findUser['wallet'][f'{item}'] * coin['price']
                        break
                string += f"**{item}** :coin:``{findUser['wallet'][f'{item}']:.0f}*``\n"
            stringTitle = f"Use /cryptol symbol if you want the\nespecific info about a currency\n\n***Total price of crypto wallet***:\n``${totalprice:.0f}* BPPCs``\n\n"
            embed = Embed(
                title=f"💵 {user.name}'s Crypto Wallet",
                description=stringTitle+string if string!="" else "\u200b\n- Buy crypto with /buy",
                color=embedColor
            )
            embed.set_thumbnail(url=user.avatar.url)
            embed.set_footer(text="*Approximately") if string!="" else ""
        else:
            symbol = symbol.upper()
            found = False
            for item in findUser['wallet']:
                if item == symbol:
                    found = True
                    break
            if not found:
                raise IndexError("Crypto not found...")
            for coin in findCurrencies:
                if coin['symbol'] == symbol:
                    findImage = imageCollection.find_one({"_id": coin['symbol']})
                    currency = coin['currency']
                    id = coin['_id']
                    name = coin[f"{coin['symbol']}"]
                    symbol = coin['symbol']
                    rank = coin['rank']
                    price = findUser['wallet'][f'{symbol}'] * coin['price']
                    volume24h = coin['volume24h']
                    volumec24h = coin['volumec24h']
                    mktcap = coin['mktcap']
                    pc1h = coin['priceChanges']['1h']
                    pc24h = coin['priceChanges']['24h']
                    pc7d = coin['priceChanges']['7d']
                    pc30d = coin['priceChanges']['30d']
                    pc60d = coin['priceChanges']['60d']
                    pc90d = coin['priceChanges']['90d']
                    seemore = findUser['seemore']['intervals']
                    priceformated = f'{price:.2f}'

                    embed = Embed(
                        title=f"#{rank} {name} ({symbol} : ${currency})",
                        description=f"**Total Price\***: ``${'{:.10f}'.format(price) if price < 1 else priceformated}``\n"
                                    f"**Exactly Amount Owned**: \n``{findUser['wallet'][f'{symbol}']}``\n"
                                    f"**PChange**: *1h:* `{positive if pc1h >= 0 else blank}{pc1h:.2f}%` *24h:* `{positive if pc24h >= 0 else blank}{pc24h:.2f}%` {(f'{br}{bSpace}*7d:* ``{positive if pc7d >= 0 else blank}{pc7d:.2f}%`` *30d:* ``{positive if pc30d >= 0 else blank}{pc30d:.2f}%``{br}') if seemore else br}"
                                    f"**Vol.**: ``${millify(volume24h)}`` ``{positive if volumec24h >= 0 else blank}{volumec24h:.2f}%``\n"
                                    f"**MarketCap**: ``${millify(mktcap)}``\n",
                        color=embedColor
                    )
                    embed.set_footer(text="*Quantity you have X How much it cost")
                    embed.set_image(url=f"{findImage[f'{symbol}']}")
        await ctx.respond(embed=embed)

    @crypto.command(name="list", description="Shows the cryptocurrency list", usage="/cryptol")
    async def list(
            self,
            ctx: ApplicationContext,
            images: Option(
                int,
                description="Show images? (Default = No)",
                choices=[
                    OptionChoice(name="Yes", value=1),
                ],
                default=0
            ),
            page: Option(int, description="May help with pagination on list with images", name="rank", default=1),
    ):
        userCollection = db['users']
        imageCollection = db['images']
        currencyCollection = db['currencies']

        findUser = userCollection.find_one({"_id": ctx.author.id})
        findImages = imageCollection.find({})
        temp = []
        for coin in findImages:
            temp.append(
                {
                    "_id": coin['_id'],
                    coin['_id']: coin[f"{coin['_id']}"]
                }
            )
        findImages = temp
        findCurrencies = currencyCollection.find().sort("rank", 1)
        if images!=0:
            embeds = self.imageList(findCurrencies, findUser, findImages)
        else:
            size = currencyCollection.count_documents({})
            findCurrency = currencyCollection.find_one({'rank': 1})
            image = imageCollection.find_one({"_id": f"{findCurrency['symbol']}"})
            embeds = self.normalList(findCurrencies, findUser, image[f"{findCurrency['symbol']}"], size)
        try:
            view = MyListView(ctx, embeds, page - 1)
            view.interaction = await ctx.respond(embed=embeds[page - 1], view=view)
        except Exception:
            view = MyListView(ctx, embeds, 0)
            view.interaction = await ctx.respond(embed=embeds[0], view=view)

    @crypto.command(name="buy", description="Action to buy a cryptocurrency", usage="/buycrypto symbol amount")
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def buy(
            self,
            ctx: ApplicationContext,
            sbl: Option(str, description="Symbol of the crypto you want to buy", name="symbol", required=True),
            amount: Option(float, description="Amount of crypto you want to buy", name="amount", min_value=100, max_value=999, required=True)
    ):
        await ctx.defer()
        userCollection = db['users']
        currencyCollection = db['currencies']
        findUser = userCollection.find_one({"_id": ctx.author.id})
        findCurrencies = currencyCollection.find({})

        amount = round(amount, 2)

        if amount > findUser['balance']:
            raise IndexError("Insufficient amount in bank...")

        found = False
        sbl = sbl.upper()
        for coin in findCurrencies:
            if coin['symbol'] == sbl:
                price = coin['price']
                name = coin[f"{coin['symbol']}"]
                found = True
                break

        if not found:
            raise IndexError("Crypto not found...")
        try:
            findUser['wallet'][f'{sbl}']
            inWallet = True
        except KeyError:
            inWallet = False

        total = amount/price

        embedConfimation = Embed(
            title=f"{ctx.author.name}, are you sure?",
            description=f"Are you sure you want to buy **{round(total, 2) if total > 0.0156 else total:.2f}\*** ***{sbl}s*** for ``${amount}``?",
            color=embedColor
        )
        success=f"**{total}** ***{sbl}s*** added to your wallet!"
        view = MyOperationView(ctx, embedConfimation, inWallet, total, -amount, sbl, success, userCollection, findUser)
        view.interaction = await ctx.respond(embed=embedConfimation, view=view)

    @crypto.command(name="sell", description="Action to sell a cryptocurrency", usage="/sellcrypto symbol amount or all")
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def sell(
            self,
            ctx: ApplicationContext,
            sbl: Option(str, description="Symbol of the crypto you want to sell", name="symbol", required=True),
            amount: Option(float, description="Amount of crypto you want to sell (to sell all leave blank)", min_value=0.01, max_value=999999, name="amount", required=True, default=0)
    ):
        await ctx.defer()
        userCollection = db['users']
        currencyCollection = db['currencies']
        findUser = userCollection.find_one({"_id": ctx.author.id})
        findCurrencies = currencyCollection.find({})
        sbl = sbl.upper()

        try:
            if amount > findUser['wallet'][f'{sbl}'] or amount==0:
                amount = findUser['wallet'][f'{sbl}']
            inWallet = True
        except KeyError:
            inWallet = False

        if not inWallet:
            raise IndexError("Crypto not found in your wallet...")

        success=False
        pop=False
        for coin in findCurrencies:
            if coin['symbol'] == sbl:
                subtract = findUser['wallet'][f'{sbl}'] - amount
                if subtract==0:
                    pop = True
                total =  coin['price'] * amount

                success=True
                break
        if not success:
            raise IndexError("Crypto not in database smh...")
        embedConfimation = Embed(
            title=f"{ctx.author.name}, are you sure?",
            description=f"Are you sure you want to sell **{amount}** ***{sbl}s*** for ``${round(total, 4) if total > 0.0156 else total:.2f}*``?",
            color=embedColor
        )
        success = f"**{amount}** ***{sbl}s*** sold from your wallet!"
        view = MyOperationView(ctx, embedConfimation, inWallet, -amount, total, sbl, success, userCollection, findUser, pop)
        view.interaction = await ctx.respond(embed=embedConfimation, view=view)

    arcade = SlashCommandGroup("arcade", "Boosts for crypto gambling.")

    @arcade.command(name="chips", description="Buy you arcade chips and get ahead of the others NOW!")
    async def chips(self, ctx: ApplicationContext):
        view = MyArcadeView(ctx)
        view.interaction = await ctx.respond(embed=arcadeEmbed(),view=view)

    # @arcade.command(name="buy", description="Buy you arcade chips and get power ups, NOW!")
    # async def chips(self, ctx: ApplicationContext):

    #METHODS SECTION

    def normalList(self, findCurrencies, findUser, image, size):
        string = "Type /crypto symbol if you want the\nespecific info about a currency\n\n"
        string += ""
        stringCurrentPage = []
        embeds = []
        i=0
        for coin in findCurrencies:
            symbol = coin['symbol']
            name = coin[f"{coin['symbol']}"]
            rank = coin['rank']
            price = coin['price']
            pctg = findUser['seemore']['percentages']['timestamp']
            percentage = coin['priceChanges'][f"{stringstampsint(pctg)}"]
            priceformated = f"{price:.0f}"
            string += f"**#{rank}** {'- ' + name if findUser['seemore']['names'] else ''} " \
                      f"**{symbol}** {'``$' + ('{:.6f}'.format(price) if price < 1 else priceformated) + '``' if findUser['seemore']['prices'] else ''} " \
                      f"{('``' + positive + '{:.4f}'.format(percentage) + '%``' if float(percentage) >= 0 else '``' + '{:.4f}'.format(percentage) + '%``') if findUser['seemore']['percentages']['enabled'] else ''} \n"
            i += 1
            if i % 15 == 0:
                stringCurrentPage.append(string)
                string = ""
                embed = Embed(
                    title="Cryptocurrencies List",
                    description=stringCurrentPage[int((i / 15) - 1)],
                    color=embedColor
                )
                embed.set_thumbnail(url=image)
                embed.set_footer(
                    text=f"Page {int(i/ 15)}/{round(size / 15.0, 0):.0f}")
                embeds.append(embed)

        return embeds

    def imageList(self, findCurrencies, findUser, findImages):
        embeds = []
        for coin in findCurrencies:
            currency = coin['currency']
            id = coin['_id']
            name = coin[f"{coin['symbol']}"]
            symbol = coin['symbol']
            rank = coin['rank']
            price = coin['price']
            volume24h = coin['volume24h']
            volumec24h = coin['volumec24h']
            mktcap = coin['mktcap']
            pc1h = coin['priceChanges']['1h']
            pc24h = coin['priceChanges']['24h']
            pc7d = coin['priceChanges']['7d']
            pc30d = coin['priceChanges']['30d']
            pc60d = coin['priceChanges']['60d']
            pc90d = coin['priceChanges']['90d']
            seemore = findUser['seemore']['intervals']
            priceformated = f'{price:.2f}'
            embed = Embed(
                title=f"#{rank} {name} ({symbol} : ${currency})",
                description=f"**Price**: ``${'{:.10f}'.format(price) if price < 1 else priceformated}``\n"
                            f"**PChange**: *1h:* `{positive if pc1h >= 0 else blank}{pc1h:.2f}%` *24h:* `{positive if pc24h >= 0 else blank}{pc24h:.2f}%` {(f'{br}{bSpace}*7d:* ``{positive if pc7d >= 0 else blank}{pc7d:.2f}%`` *30d:* ``{positive if pc30d >= 0 else blank}{pc30d:.2f}%``{br}{bSpace}*60d:* ``{positive if pc60d >= 0 else blank}{pc60d:.0f}%`` *90d:* ``{positive if pc90d >= 0 else blank}{pc90d:.0f}%``{br}') if seemore else br}"
                            f"**Vol.**: ``${millify(volume24h)}`` ``{positive if volumec24h >= 0 else blank}{volumec24h:.2f}%``\n"
                            f"**MarketCap**: ``${millify(mktcap)}``\n",
                color=embedColor
            )
            embed.set_footer(text="/help_crypto for help with meanings")
            for image in findImages:
                if image['_id'] == symbol:
                    link = f"{image[symbol]}"
            embed.set_image(url=link)
            embeds.append(embed)
        return embeds

def millify(n):
    n = float(n)
    millidx = max(0, min(len(millnames) - 1,
                         int(floor(0 if n == 0 else log10(abs(n)) / 3))))
    return '{:.0f}{}'.format(n / 10 ** (3 * millidx), millnames[millidx])

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

def setup(beppo):
    beppo.add_cog(Crypto(beppo))
