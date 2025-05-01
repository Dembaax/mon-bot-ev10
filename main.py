# main.py
import os
import sys
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import discord
from discord.ext import commands

# --- 1) Chargement des vars ---
# Charge .env si présent (local)
load_dotenv()

# Récupère toutes les vars d’environnement (Railway, Heroku, etc.)
TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Vérifie et convertit l’ID du salon en int
if CHANNEL_ID is None:
    print("❌ ERREUR : la variable DISCORD_CHANNEL_ID n’est pas définie.")
    sys.exit(1)
try:
    CHANNEL_ID = int(CHANNEL_ID)
except ValueError:
    print("❌ ERREUR : DISCORD_CHANNEL_ID doit être un nombre entier.")
    sys.exit(1)

if TOKEN is None:
    print("❌ ERREUR : la variable TOKEN n’est pas définie.")
    sys.exit(1)

# --- 2) Setup du bot Discord ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3) Mots-clés par extension ---
EXTENSIONS = {
    "EV10": ["écarlate", "violet", "rivaux", "destinées"],
    "EV8.5": ["évolutions prismatiques", "super premium", "8.5"],
    "EV151": ["151", "classique", "première génération"],
}

# --- 4) Sites à scraper ---
SITES = {
    "Micromania": "https://www.micromania.fr/cartes-pokemon.html",
    "SmithToys": "https://www.smithtoys.fr/search?query=pokemon",
    "Philibert": "https://www.philibertnet.com/fr/20-pokemon",
    "Cultura": "https://www.cultura.com/carte-pokemon.html",
}

# --- 5) Fonction utilitaire de fetch & parse ---
async def fetch(session, url):
    async with session.get(url, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.text()

async def search_extension(ext_key: str, keywords: list[str], msg: discord.Message):
    """Scrape tous les sites et renvoie la liste des nouveautés pour une extension."""
    found = []
    async with aiohttp.ClientSession() as session:
        for i, (site_name, url) in enumerate(SITES.items(), 1):
            await msg.edit(content=f"🔍 Recherche {ext_key} sur **{site_name}** ({i}/{len(SITES)})…")
            try:
                html = await fetch(session, url)
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(" ", strip=True).lower()
                # cherche un des mots-clés
                if any(kw.lower() in text for kw in keywords):
                    found.append(f"{site_name}: **nouveauté {ext_key} détectée**")
                await asyncio.sleep(1)  # léger délai pour ne pas spammer
            except Exception as e:
                found.append(f"{site_name}: erreur ({e.__class__.__name__})")
    return found

async def do_search(ext_key: str, ctx: commands.Context):
    """Lance la recherche et envoie le résultat."""
    msg = await ctx.send(f"🔎 Recherche manuelle {ext_key} en cours…")
    results = await search_extension(ext_key, EXTENSIONS[ext_key], msg)
    if results:
        await msg.edit(content="\n".join(results))
    else:
        await msg.edit(content=f"✅ Aucune nouveauté {ext_key} trouvée.")

# --- 6) Commandes Discord ---
@bot.command(name="ev10")
async def ev10(ctx: commands.Context):
    await do_search("EV10", ctx)

@bot.command(name="ev8.5")
async def ev85(ctx: commands.Context):
    await do_search("EV8.5", ctx)

@bot.command(name="ev151")
async def ev151(ctx: commands.Context):
    await do_search("EV151", ctx)

# --- 7) Logging au démarrage ---
@bot.event
async def on_ready():
    print(f"✅ Connecté sous {bot.user} (ID salon = {CHANNEL_ID})")

# --- 8) Lancement du bot ---
bot.run(TOKEN)
