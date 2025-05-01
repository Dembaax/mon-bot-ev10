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

# Récupère TOUTES les vars d’environnement (Railway, Heroku…)
TOKEN = os.getenv("TOKEN")
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
    "EV10":  ["écarlate", "violet", "rivaux", "destinées"],
    "EV8.5": ["évolutions prismatiques", "super premium", "8.5"],
    "EV151": ["151", "classique", "première génération"],
}

# --- 4) Sites à scraper ---
SITES = {
    "Micromania": "https://www.micromania.fr/cartes-pokemon.html",
    "SmithToys":  "https://www.smithtoys.fr/collections/pokemon",
    "Philibert":  "https://www.philibertnet.com/fr/20-pokemon",
    "Cultura":    "https://www.cultura.com/carte-pokemon.html",
}

async def fetch(session, url):
    async with session.get(url, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.text()

async def search_extension(ext_key, keywords, progress_msg):
    found = []
    total = len(SITES)
    done = 0

    async with aiohttp.ClientSession() as sess:
        for site, url in SITES.items():
            done += 1
            bar = f"[{'█'*done}{'─'*(total-done)}] {done}/{total}"
            await progress_msg.edit(content=f"🔍 **{ext_key}** → {site} {bar}")

            html = await fetch(sess, url)
            text = BeautifulSoup(html, "html.parser").get_text().lower()

            if any(kw.lower() in text for kw in keywords):
                a = BeautifulSoup(html, "html.parser").find(
                    "a",
                    href=True,
                    text=lambda t: t and ("précommande" in t.lower() or ext_key.lower() in t.lower())
                )
                link = a["href"] if a else url
                found.append(f"• **{site}** ➔ {link}")

    return found

async def do_search(ext_key, ctx):
    msg = await ctx.send(f"🔎 Lancement de **{ext_key}**…")
    results = await search_extension(ext_key, EXTENSIONS[ext_key], msg)

    if results:
        summary = f"✅ **Précommande {ext_key} trouvée !**\n" + "\n".join(results)
    else:
        summary = f"❌ Aucune précommande pour **{ext_key}**."
    await msg.edit(content=summary)

# --- 5) Commandes utilisateur ---
@bot.command(name="ev10")
async def ev10(ctx):
    await do_search("EV10", ctx)

@bot.command(name="ev8_5")
async def ev8_5(ctx):
    await do_search("EV8.5", ctx)

@bot.command(name="ev151")
async def ev151(ctx):
    await do_search("EV151", ctx)

@bot.event
async def on_ready():
    print(f"✅ Connecté sous {bot.user}")
    await bot.change_presence(activity=discord.Game("!ev10 | !ev8_5 | !ev151"))

if __name__ == "__main__":
    bot.run(TOKEN)
