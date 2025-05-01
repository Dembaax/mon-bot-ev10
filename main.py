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

# ─── Mots-clés et sites ────────────────────────────────────────────────────
KEYWORDS_EV10 = ["écarlate et violet", "rivalités destinées", "ev10"]
KEYWORDS_EV85 = ["évolutions prismatiques", "ev8.5"]
TRIGGER_WORDS   = ["précommande", "disponible", "ajouter au panier", "acheter"]
VENDORS = {
    "Micromania": "https://www.micromania.fr/cartes-pokemon.html",
    "Fnac":      "https://www.fnac.com/SearchResult/ResultList.aspx?Search=ev10+pokemon",
    "KingJouet": "https://www.king-jouet.com/recherche?text=ev10",
    "Philibert": "https://www.philibertnet.com/fr/recherche?controller=search&search_query=ev10",
    "SmithToys": "https://www.smythstoys.com/fr/fr-fr/recherche/?q=ev10"
}

# ─── Historique pour ne pas renvoyer 2× la même alerte ────────────────────
HISTORY = "sent_links.txt"
if os.path.exists(HISTORY):
    with open(HISTORY, "r") as f:
        seen = set(f.read().splitlines())
else:
    seen = set()

# ─── Configuration du bot ──────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="🕵️ Surveille EV10/EV8.5"))
    print(f"✅ Connecté comme {bot.user}")
    check_preorders.start()

# ─── Fonction unique de recherche ──────────────────────────────────────────
async def perform_search():
    """Retourne deux listes : [(nom, url), …] pour EV10 et EV8.5 trouvés."""
    found10 = []
    found85 = []

    async with aiohttp.ClientSession() as session:
        for name, url in VENDORS.items():
            try:
                async with session.get(url, timeout=10) as r:
                    html = await r.text()
                    text = html.lower()
                    # EV10 ?
                    if any(k in text for k in KEYWORDS_EV10) and any(w in text for w in TRIGGER_WORDS):
                        if url not in seen:
                            found10.append((name, url))
                            seen.add(url)
                    # EV8.5 ?
                    if any(k in text for k in KEYWORDS_EV85) and any(w in text for w in TRIGGER_WORDS):
                        if url not in seen:
                            found85.append((name, url))
                            seen.add(url)
            except Exception as e:
                print(f"[ERREUR] {name}: {e}")
    # on met à jour le fichier d’historique
    if found10 or found85:
        with open(HISTORY, "w") as f:
            f.write("\n".join(seen))
    return found10, found85

# ─── Tâche automatique toutes les 15 minutes ───────────────────────────────
@tasks.loop(minutes=15)
async def check_preorders():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Salon introuvable :", CHANNEL_ID)
        return

    ev10_list, ev85_list = await perform_search()

    for name, link in ev10_list:
        await channel.send(f"🚨 @here Précommande **EV10** détectée chez **{name}** !\n{link}")
    for name, link in ev85_list:
        await channel.send(f"ℹ️ Précommande **EV8.5** (fallback) détectée chez **{name}**\n{link}")

# ─── Commande manuelle !ev10 avec indicateur “typing…” ────────────────────
@bot.command(name="ev10")
async def cmd_ev10(ctx):
    """Force la recherche EV10/EV8.5 et affiche un indicateur."""
    async with ctx.typing():
        ev10_list, ev85_list = await perform_search()

    if not ev10_list and not ev85_list:
        return await ctx.send("✅ Aucune préco EV10/EV8.5 trouvée pour l’instant.")
    # on renvoie EV10 en priorité
    for name, link in ev10_list:
        await ctx.send(f"🚨 @here Précommande **EV10** détectée chez **{name}** !\n{link}")
    # puis EV8.5
    for name, link in ev85_list:
        await ctx.send(f"ℹ️ Précommande **EV8.5** (fallback) détectée chez **{name}**\n{link}")

# ─── Démarrage du bot ─────────────────────────────────────────────────────
bot.run(TOKEN)
