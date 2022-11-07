from datetime import datetime, timedelta
from main import db, embedColor, button, View, commands, Embed, ApplicationContext
from random import randint

MAX_NUMBER=20000
RECIEVE_COIN=99

class MyClaimView(View):
    def __init__(self, coin, amount, userCollection, findImage=None):
        super().__init__(timeout=45)
        self.coin = coin
        self.amount = amount
        self.userCollection = userCollection
        self.findImage = findImage
        self.claimed = False

    @button(emoji="🪙")
    async def claim_callback(self, button, interaction):
        self.claimed = True
        self.disable_all_items()
        self.userCollection.update_one({"_id": interaction.user.id}, {
            "$inc": {f"wallet.{self.coin}" if self.coin != "balance" else "balance": self.amount}
        })
        embed = Embed(
            title=f"🪙 You claimed a {self.coin}, lucky!" if self.coin != "balance" else "🪙 You claimed a BPPC!",
            color=0xD189FF
        )
        embed.set_image(url=f"{self.findImage[self.coin]}" if self.coin != "balance" else "https://imgur.com/168T4n9.jpg")
        embed.set_footer(text=f"{interaction.user.name} redeemed {f'{self.amount}' if self.coin != 'balance' else f'${self.amount}'} {self.coin if self.coin != 'balance' else 'BPPC'}s", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        self.disable_all_items()
        await self.interaction.edit(view=self)

    async def interaction_check(self, interaction) -> bool:
        if self.claimed:
            return False
        else:
            return True

class Gambling(commands.Cog):

    def __init__(self, beppo):

        self.beppo = beppo

    @commands.Cog.listener()
    async def on_ready(self):
        print("Gambling Loaded & Ready!")

    @commands.slash_command(name="mine", description="Money & Crypto RNG", usage="/mine")
    async def mine(self, ctx: ApplicationContext):
        await ctx.defer()
        userCollection = db['users']
        imageCollection = db['images']
        currencyCollection = db['currencies']
        findUser = userCollection.find_one({"_id": ctx.author.id})
        if findUser['pickaxes'] != 0:
            var = rng(currencyCollection)
            if isinstance(var, str):
                var = var.split()
                findImage = imageCollection.find_one({f"_id": f"{var[1]}"})
                view = MyClaimView(var[1], int(var[0]), userCollection, findImage)

            elif var==69:
                findImage = imageCollection.find_one({f"_id": f"BTC"})
                inWallet = False
                view = MyClaimView("BTC", 50, userCollection, findImage)

            elif var == 0:
                embed = Embed(
                    title="😓 No incomes for now...",
                    description=f"At least you got cobblestones 😅",
                    color=embedColor
                )
                embed.set_image(url="https://imgur.com/B2bYJKe.gif")
                userCollection.update_one({"_id": ctx.author.id}, {"$inc": {"pickaxes": -1}})
                if findUser['pickaxes'] == 3:
                    embed.set_footer(text="⚠️You have 2 pickaxes left ⚠️")
                await ctx.respond(embed=embed)
                return

            else:
                var = round(var, 2)
                view = MyClaimView("balance", var, userCollection)

            embed = Embed(
                title="🪙 You mined something!",
                description="Click in the button to redeem!",
                color=embedColor
            )
            embed.set_image(url="https://imgur.com/sc0GrsX.gif")
            if findUser['pickaxes'] == 3:
                embed.set_footer(text="⚠️You have 2 pickaxes left ⚠️")
            userCollection.update_one({"_id": ctx.author.id}, {"$inc": {"pickaxes": -1}})
            view.interaction = await ctx.respond(embed=embed, view=view)
        else:
            await ctx.respond("You got no pickaxes left...")

    @commands.slash_command(name="daily", description="Claim your daily BPPCs $50 to $600 per day", usage="/daily")
    async def daily(self, ctx: ApplicationContext):
        await ctx.defer()
        userCollection = db['users']
        findUser = userCollection.find_one({"_id": ctx.author.id})
        horas = datetime.strptime(findUser['daily'], '%Y, %m, %d, %H, %M, %S')
        if horas <= datetime.now():
            var = randint(50, 600)
            embed = Embed(
                title="💸 Daily claimed!",
                color=embedColor
            )
            embed.set_image(url="https://imgur.com/NU96qub.gif")
            embed.set_footer(text=f"{ctx.author.name} claimed ${var} BPPCs!", icon_url=f"{ctx.author.avatar.url}")
            userCollection.update_one({"_id": ctx.author.id}, {
                "$inc": {"balance": var},
                "$set": {"daily": (datetime.now() + timedelta(days=1)).strftime("%Y, %m, %d, %H, %M, %S")}
            })
            await ctx.respond(embed=embed)
        else:
            horas = horas - datetime.now()
            horas = str(horas).split(':')
            minutos = horas[1]
            segundos = horas[2].split('.')
            segundos = segundos[0]
            horas = horas[0]
            await ctx.respond(f"The cooldown expires in **{(horas if int(horas) > 9 else '0'+horas) + ':'}{minutos + ':'}{segundos}**")

    #METHODS SECTION

def rng(currencyCollection):
    lenght = currencyCollection.count_documents({})
    x = randint(1, 70000)
    if x >= MAX_NUMBER:
        return 0
    if x < MAX_NUMBER and x > RECIEVE_COIN:
        return ((MAX_NUMBER - x)*0.01)/3
    if x == 1:
        return 69
    else:
        crypto = randint(1, lenght)
        findCurrency = currencyCollection.find_one({"rank":crypto})
        price = findCurrency['price']
        symbol = findCurrency['symbol']
        prize=(f"{(randint(5000, 20000)/price):.0f} {symbol}")
        return prize


def setup(beppo):
    beppo.add_cog(Gambling(beppo))
