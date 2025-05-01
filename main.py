# main.py

import os
import logging
import asyncio
from dotenv import load_dotenv
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import commands

# ─── CONFIG & LOGGING ────────────────────────────────────────────────
load_dotenv()

TOKEN              = os.getenv("TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

if not TOKEN or not DISCORD_CHANNEL_ID:
    raise RuntimeError("TOKEN ou DISCORD_CHANNEL_ID non défini dans .env")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ─── FONCTIONS DE SCRAPING ────────────────────────────────────────────

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as e:
        logger.warning(f"Erreur HTTP sur {url} : {e}")
        return None

async def check_pokecardex(keyword):
    url = "https://www.pokecardex.com/actualites/"
    async with aiohttp.ClientSession() as s:
        html = await fetch(s, url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("article a"):
        if keyword.lower() in a.get_text(strip=True).lower():
            return a["href"]
    return None

async def check_micromania(keyword):
    url = "https://www.micromania.fr/cartes-pokemon.html"
    async with aiohttp.ClientSession() as s:
        html = await fetch(s, url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select(".productListItem"):
        title = card.select_one(".productName").get_text(strip=True).lower()
        if keyword.lower() in title:
            return card.select_one("a")["href"]
    return None

async def check_kingjouet(keyword):
    url = "https://www.king-jouet.com/4187-jouets-pokemon"
    async with aiohttp.ClientSession() as s:
        html = await fetch(s, url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    for item in soup.select(".product-container"):
        title = item.select_one(".product-name").get_text(strip=True).lower()
        if keyword.lower() in title:
            return item.select_one("a")["href"]
    return None

async def check_philibert(keyword):
    url = "https://www.philibertnet.com/fr/144-jeux-pokemon/2"
    async with aiohttp.ClientSession() as s:
        html = await fetch(s, url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select(".product-miniature"):
        title = card.select_one(".product-title a").get_text(strip=True).lower()
        if keyword.lower() in title:
            return card.select_one(".product-title a")["href"]
    return None

# ─── NOUVELLE FONCTION pour Cultura ───────────────────────────────────
async def check_cultura(keyword):
    url = f"https://www.cultura.com/search/autocomplete?term={keyword}"
    logger.info(f"[Cultura] recherche '{keyword}'")
    async with aiohttp.ClientSession() as s:
        resp = await fetch(s, url)
    if not resp: 
        return None
    # Cultura renvoie JSON en auto-complete, on peut parser manuellement
    import json
    data = json.loads(resp)
    for entry in data.get("products", []):
        title = entry.get("name", "").lower()
        if keyword.lower() in title:
            return "https://www.cultura.com" + entry.get("url", "")
    return None

# ─── SmithToys ────────────────────────────────────────────────────────
async def check_smithtoy(keyword):
    url = "https://www.smithtoys.fr/collections/pokemon"
    logger.info(f"[SmithToys] recherche '{keyword}'")
    async with aiohttp.ClientSession() as s:
        html = await fetch(s, url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    for prod in soup.select(".product-card"):
        title = prod.select_one(".product-card__title").get_text(strip=True).lower()
        if keyword.lower() in title:
            return prod.select_one("a")["href"]
    return None


# ─── COMMANDE !ev10 ──────────────────────────────────────────────────
@bot.command(name="ev10")
async def cmd_ev10(ctx):
    sites = [
        ("Pokécardex", check_pokecardex),
        ("Micromania", check_micromania),
        ("King Jouet", check_kingjouet),
        ("Philibert", check_philibert),
        ("Cultura", check_cultura),   # ← ajouté
        ("SmithToys", check_smithtoy),
    ]
    keywords     = ["ev10", "écarlate et violet", "rivalités destinées"]
    keywords_alt = ["ev8.5", "prismatiques", "premium 8.5"]

    status_msg = await ctx.send("🔍 Lancement de la recherche EV10/EV8.5… (0/6)")

    # Recherche EV10
    for idx, (name, fnc) in enumerate(sites, 1):
        await status_msg.edit(content=f"🔍 EV10 sur **{name}** ({idx}/{len(sites)})…")
        for kw in keywords:
            link = await fnc(kw)
            if link:
                return await ctx.send(f"🚨 @here Précommande **EV10** sur {name} → {link}")

    # Recherche EV8.5
    for idx, (name, fnc) in enumerate(sites, 1):
        await status_msg.edit(content=f"🔍 EV8.5 sur **{name}** ({idx}/{len(sites)})…")
        for kw in keywords_alt:
            link = await fnc(kw)
            if link:
                return await ctx.send(f"ℹ️ Pas d’EV10, mais **EV8.5** sur {name} → {link}")

    await status_msg.edit(content="❌ Aucune précommande EV10/EV8.5 dispo pour l’instant.")


# ─── DÉMARRAGE ───────────────────────────────────────────────────────
@bot.event
async def on_ready():
    logger.info(f"✅ Connecté comme {bot.user} (ID={bot.user.id})")

if __name__ == "__main__":
    bot.run(TOKEN)
