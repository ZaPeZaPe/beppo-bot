from datetime import datetime, time, timedelta
from discord.ext import tasks
from json import loads
from logging import error
from main import db, embedColor, apikey, commands, ApplicationContext, Embed
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from traceback import format_exc

exp = 5

timeList = []
for h in range(0, 23):
    timeList.append(time(hour=h))

minuteList = []
for h in range(0, 23):
    s=0
    for m in range(0, 590, 45):
        s=(m%10)*6
        m=int(m/10)
        minuteList.append(time(hour=h, minute=m, second=s))
        # print(f"{h}:{m}:{s}")

class Events(commands.Cog):

    def __init__(self, beppo):
        self.beppo = beppo
        self.refreshCurrencies.start()
        self.update_users.start()

    @tasks.loop(time=timeList)
    async def update_users(self):
        userCollection = db['users']
        userCollection.update_many({}, {"$set": {"pickaxes": 8}})

    @commands.Cog.listener()
    async def on_ready(self):
        print("Events Loaded & Ready!")

    @commands.Cog.listener()
    async def on_message(self, message):

        if str(message.channel.type) == "private":
            return
        if message.author == self.beppo.user:
            return
        if message.author.bot:
            return

        userCollection = db['users']
        serverCollection = db['servers']

        user = userCollection.find_one({"_id": message.author.id})
        server = serverCollection.find_one({"_id": message.guild.id})

        userfound = True if user != None else False
        serverfound = True if server != None else False

        try:
            if not userfound:
                user = await self.update_user_data(userCollection, message.author)
            if not serverfound:
                server = await self.update_server_data(serverCollection, message.guild)

            uWage = user['perswage']
            sWage = server['wage']

            if uWage > sWage:
                wage = uWage
            else:
                wage = sWage

            await self.add_server_experience(serverCollection, server, exp)
            await self.add_moneyxpcd(userCollection, user, wage)

        except Exception as e:
            error(format_exc())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        userCollection = db['users']
        userfound = True if userCollection.find_one({"_id": member.id}) != None else False
        if not userfound:
            await self.update_user_data(userCollection, member)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: ApplicationContext, error):
        if isinstance(error, commands.CommandError):
            print(str(error) + " " +str(error.__cause__))
            await ctx.message.add_reaction('❌')
        if isinstance(error, commands.CheckFailure):
            print(str(error) + " " +str(error.__cause__))
            await ctx.message.add_reaction('🚫')
        if isinstance(error, KeyError):
            print(str(error) + " " +str(error.__cause__))
            await ctx.message.add_reaction('❓')

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, error):
        embed = Embed(
            title=f"❌ Uh... Something went wrong...",
            description=f"{error}",
            color=embedColor
        )
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Try later in *{timedelta(seconds=error.retry_after).seconds}* second(s)...", ephemeral=True)
            return
        if isinstance(error, KeyError):
            embed = Embed(
                title=f"❌ Uh... Data Base error",
                description=f"{error}",
                color=embedColor
            )
        try:
            if isinstance(error.__dict__['original'], KeyError):
                embed = Embed(
                    title=f"❌ Uh... Data Base error",
                    description=f"Coulnd't find id {error.__cause__}",
                    color=embedColor
                )
            if isinstance(error.__dict__['original'], IndexError):
                embed = Embed(
                    title=f"❌ {error.__cause__}",
                    color=embedColor
                )
        except Exception:
            pass
        await ctx.respond(embed=embed, ephemeral=True)

    #METHODS SECTION

    @tasks.loop(time=minuteList)
    async def refreshCurrencies(self):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        # test url 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        # TODO FAZER O USD,BRL : não dá por conta de plano gratis...
        parameters = {
            'start': '1',
            'limit': '50',
            'convert': 'USD'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': apikey,
        }

        session = Session()
        session.headers.update(headers)
        
        currencyCollection = db['currencies']
        
        try:
            response = session.get(url, params=parameters)
            data = loads(response.text)
            i = 0
            while i < len(data['data']):
                currency = "USD"
                id = listGet("id", data, i)
                name = listGet("name", data, i)
                symbol = listGet("symbol", data, i)
                rank = listGet("rank", data, i)
                priceUSD = listGet("priceUSD", data, i)
                # priceBRL = listGet("priceBRL", data, i)
                volume24h = listGet("volume24h", data, i)
                volumec24h = listGet("volumec24h", data, i)
                pc1h = listGet("pc1h", data, i)
                pc24h = listGet("pc24h", data, i)
                pc7d = listGet("pc7d", data, i)
                pc30d = listGet("pc30d", data, i)
                pc60d = listGet("pc60d", data, i)
                pc90d = listGet("pc90d", data, i)
                mktcap = listGet("mktcap", data, i)
                i+=1
                findCurrency = currencyCollection.find_one({"symbol": symbol})
                if findCurrency != None:
                    currencyCollection.update_one({"symbol": symbol}, {"$set": {
                        "rank": rank,
                        # "priceBRL": priceBRL,
                        "price": priceUSD,
                        "volume24h": volume24h,
                        "volumec24h": volumec24h,
                        "mktcap": mktcap,
                        "priceChanges": {
                            "1h": pc1h,
                            "24h": pc24h,
                            "7d": pc7d,
                            "30d": pc30d,
                            "60d": pc60d,
                            "90d": pc90d
                        }
                    }})
                else:
                    currencyCollection.insert_one({
                        "_id": id,
                        "currency": "USD",
                        f"{symbol}": f"{name}",
                        "symbol": f"{symbol}",
                        "rank": rank,
                        "price": priceUSD,
                        "volume24h": volume24h,
                        "volumec24h": volumec24h,
                        "mktcap": mktcap,
                        "priceChanges": {
                            "1h" : pc1h,
                            "24h": pc24h,
                            "7d": pc7d,
                            "30d": pc30d,
                            "60d": pc60d,
                            "90d": pc90d
                        }
                    })
            print(f"Refreshed")
        
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)

    async def update_user_data(self, userCollection, user):
        userCollection.insert_one({
            "_id": user.id,
            "experience": 0,
            "level": 1,
            "balance": 10,
            "perswage": 5,
            "pickaxes": 20,
            "wallet": {},
            "banned": False,
            "lvlcd": datetime.now().strftime("%Y, %m, %d, %H, %M, %S"),
            "daily": datetime.now().strftime("%Y, %m, %d, %H, %M, %S"),
            "seemore": {
                'intervals': False,
                'names': False,
                'prices': True,
                'percentages': {'enabled':True, 'timestamp': 1}
            }
        })
        return userCollection.find_one({"_id": user.id})

    async def update_server_data(self, serverCollection, server):
        serverCollection.insert_one({
            "_id": server.id,
            "experience": 0,
            "level": 1,
            "wage": 5,
            "lvlcd": datetime.now().strftime("%Y, %m, %d, %H, %M, %S")
        })
        return serverCollection.find_one({"_id": server.id})

    async def add_server_experience(self, serverCollection, server, exp):
        if datetime.strptime(server['lvlcd'], '%Y, %m, %d, %H, %M, %S') <= datetime.now():
            serverCollection.update_one({"_id": server["_id"]}, {
                "$inc": {"experience": exp},
                "$set": {"lvlcd": (datetime.now() + timedelta(minutes=1)).strftime("%Y, %m, %d, %H, %M, %S")}
            })
            await self.level_up(serverCollection, server)

    async def add_moneyxpcd(self, userCollection, user, wage):
        if datetime.strptime(user['lvlcd'], '%Y, %m, %d, %H, %M, %S') <= datetime.now():
            userCollection.update_one({"_id": user['_id']}, {
                "$inc": {
                    "experience": exp,
                    "balance": wage
                },
                "$set": {
                    "lvlcd": (datetime.now() + timedelta(minutes=1)).strftime("%Y, %m, %d, %H, %M, %S")
                }
            })
            await self.level_up(userCollection, user)

    async def level_up(self, elements, element):
        res = elements.find_one({"_id": element['_id']})
        experience = res['experience']
        level_start = res['level']
        level_end = int(experience ** (1 / 4))

        if level_start < level_end:
            elements.update_one({"_id": element['_id']}, {"$inc": {"level": level_end}})

def listGet(want, list, i):
    options = {
        "id": list['data'][i]['id'],
        "name": list['data'][i]['name'],
        "symbol": list['data'][i]['symbol'],
        "rank": list['data'][i]['cmc_rank'],
        "priceUSD": list['data'][i]['quote']['USD']['price'],
        # "priceBRL": list['data'][i]['quote']['BRL']['price'],
        "volume24h": list['data'][i]['quote']['USD']['volume_24h'],
        "volumec24h": list['data'][i]['quote']['USD']['volume_change_24h'],
        "pc1h": list['data'][i]['quote']['USD']['percent_change_1h'],
        "pc24h": list['data'][i]['quote']['USD']['percent_change_24h'],
        "pc7d": list['data'][i]['quote']['USD']['percent_change_7d'],
        "pc30d": list['data'][i]['quote']['USD']['percent_change_30d'],
        "pc60d": list['data'][i]['quote']['USD']['percent_change_60d'],
        "pc90d": list['data'][i]['quote']['USD']['percent_change_90d'],
        "mktcap": list['data'][i]['quote']['USD']['market_cap'],
        "data": list['data']
    }
    return options.get(want)

def setup(beppo):
    beppo.add_cog(Events(beppo))