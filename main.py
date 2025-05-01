import os
import discord
import aiohttp
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ─── Chargement des variables d’environnement ──────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# ─── Configuration des mots-clés ──────────────────────────────────────────
KEYWORDS_EV10 = ["écarlate et violet", "rivalités destinées", "ev10"]
KEYWORDS_EV85 = ["evolutions prismatiques", "évolutions prismatiques", "ev8.5"]
TRIGGER_WORDS = ["précommande", "disponible", "ajouter au panier", "acheter"]

# ─── Sites à surveiller ───────────────────────────────────────────────────
VENDORS = {
    "Micromania": "https://www.micromania.fr/cartes-pokemon.html",
    "Fnac":      "https://www.fnac.com/SearchResult/ResultList.aspx?Search=ev10+pokemon",
    "KingJouet": "https://www.king-jouet.com/recherche?text=ev10",
    "Philibert": "https://www.philibertnet.com/fr/recherche?controller=search&search_query=ev10",
    "SmithToys": "https://www.smythstoys.com/fr/fr-fr/recherche/?q=ev10"
}

# ─── Initialisation du bot ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

history_file = "sent_links.txt"
if os.path.exists(history_file):
    with open(history_file, "r") as f:
        seen_links = set(f.read().splitlines())
else:
    seen_links = set()

# ─── Au démarrage ──────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    # statut personnalisé
    await bot.change_presence(activity=discord.Game(name="🕵️ Surveille EV10/EV8.5"))
    print(f"✅ Connecté en tant que {bot.user}")
    check_preorders.start()

# ─── Tâche planifiée toutes les 15 minutes ────────────────────────────────
@tasks.loop(minutes=15)
async def check_preorders():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Salon non trouvé :", CHANNEL_ID)
        return

    async with aiohttp.ClientSession() as session:
        found_ev10 = []
        found_ev85 = []

        for name, url in VENDORS.items():
            try:
                async with session.get(url, timeout=10) as resp:
                    html = await resp.text()
                    text = html.lower()

                    # EV10 ?
                    if any(k in text for k in KEYWORDS_EV10) and any(w in text for w in TRIGGER_WORDS):
                        if url not in seen_links:
                            found_ev10.append((name, url))
                            seen_links.add(url)

                    # EV8.5 ?
                    if any(k in text for k in KEYWORDS_EV85) and any(w in text for w in TRIGGER_WORDS):
                        if url not in seen_links:
                            found_ev85.append((name, url))
                            seen_links.add(url)

            except Exception as e:
                print(f"[ERREUR] {name}: {e}")
                continue

    # Envoi des alertes
    for name, link in found_ev10:
        await channel.send(f"🚨 @here **Précommande EV10 détectée chez {name} !**\n{link}")
    for name, link in found_ev85:
        await channel.send(f"ℹ️ **Précommande EV8.5 détectée chez {name}** (fallback)\n{link}")

    # Sauvegarde de l’historique
    if found_ev10 or found_ev85:
        with open(history_file, "w") as f:
            f.write("\n".join(seen_links))

# ─── Commande manuelle !ev10 ───────────────────────────────────────────────
@bot.command()
async def ev10(ctx):
    """Force la recherche EV10/EV8.5"""
    await ctx.send("🔍 Recherche manuelle EV10/EV8.5 en cours...")
    await check_preorders()

# ─── Lancement du bot ─────────────────────────────────────────────────────
bot.run(TOKEN)
