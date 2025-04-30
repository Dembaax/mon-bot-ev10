import os
import discord
import aiohttp
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

WEBHOOK_SITES = {
    "Micromania": "https://www.micromania.fr/cartes-pokemon.html",
    "Fnac": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0%211&Search=ev10+pokemon",
    "KingJouet": "https://www.king-jouet.com/recherche?text=ev10",
    "Philibert": "https://www.philibertnet.com/fr/recherche?controller=search&search_query=ev10",
    "SmithToys": "https://www.smythstoys.com/fr/fr-fr/search/?q=ev10"
}

KEYWORDS = ["Écarlate", "Violet", "Rivalités Destinées", "booster", "display", "tripack", "ETB"]
TRIGGER_WORDS = ["précommande", "ajouter au panier", "disponible", "précommander"]

seen_urls = set()

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user.name}")
    check_ev10.start()

@tasks.loop(minutes=10)
async def check_ev10():
    async with aiohttp.ClientSession() as session:
        for name, url in WEBHOOK_SITES.items():
            try:
                async with session.get(url, timeout=15) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    if any(keyword.lower() in soup.text.lower() for keyword in KEYWORDS):
                        if any(trigger.lower() in soup.text.lower() for trigger in TRIGGER_WORDS):
                            if url not in seen_urls:
                                seen_urls.add(url)
                                channel = bot.get_channel(CHANNEL_ID)
                                if channel:
                                    await channel.send(f"🛒 **Précommande détectée chez {name} !**\n{url}")
            except Exception as e:
                print(f"[ERREUR] {name}: {e}")

@bot.command()
async def ev10(ctx):
    await ctx.send("🔍 Recherche manuelle lancée...")
    await check_ev10()

bot.run(TOKEN)
