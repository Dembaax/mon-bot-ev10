import os
import discord
import asyncio
import aiohttp
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration
CHANNEL_ID = 123456789012345678  # Remplacez par l'ID de votre salon texte
KEYWORDS_EV10 = [
    "Écarlate et Violet", "Rivalités Destinées", "EV10",
    "Destinées", "EV10 français", "Rivalites Destinees"
]
TRIGGER_WORDS = ["booster", "display", "tripack", "etb", "coffret"]
TRUSTED_SITES = [
    "https://www.micromania.fr", "https://www.fnac.com",
    "https://www.king-jouet.com", "https://www.philibertnet.com", "https://www.smythstoys.com"
]
CHECK_URLS = [
    "https://www.pokeguardian.com/",
    "https://www.pokebeach.com/",
    "https://www.pokecardex.com/",
    "https://www.philibertnet.com/fr/recherche?controller=search&s=pokemon",
    "https://www.smythstoys.com/fr/fr-fr/recherche/?q=pokemon"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
sent_links = set()

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    check_ev10.start()

@tasks.loop(minutes=60)
async def check_ev10():
    channel = bot.get_channel(CHANNEL_ID)
    for url in CHECK_URLS:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text().lower()
                    if any(k.lower() in text for k in KEYWORDS_EV10) and any(w in text for w in TRIGGER_WORDS):
                        if url not in sent_links:
                            sent_links.add(url)
                            if any(site in url for site in TRUSTED_SITES):
                                await channel.send(f"❗ @here **Précommande EV10 détectée !**\n👉 {url}")
                                return
            except Exception as e:
                print(f"Erreur pendant la vérification de {url}: {e}")

    # Si rien sur EV10, partage autre actu
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.pokeguardian.com/", timeout=10) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            latest = soup.find("article")
            if latest:
                title = latest.find("h2").get_text(strip=True)
                link = latest.find("a")["href"]
                await channel.send(f"📰 **Autre actu Pokémon :** {title}\n🔗 {link}")

@bot.command()
async def ev10(ctx):
    await ctx.send("🔍 Recherche manuelle EV10 en cours...")
    await check_ev10()

bot.run(TOKEN)
