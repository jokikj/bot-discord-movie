import discord
from discord import app_commands
from dotenv import load_dotenv
import json
import random
import os

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# --- Configuration et variables ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FILMS_FILE = 'films.json'

# Initialiser le client Discord avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialiser le client Discord et l'arborescence de commandes
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Status bot (Fusion des deux fonctions on_ready)
@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")
    try:
        # Synchronisation des commandes slash
        synced = await tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

    # --- Définition du statut du bot ---
    # Décommentez et choisissez l'activité que vous voulez.
    # Assurez-vous d'en choisir une seule et de commenter les autres.

    # Exemple 1: Joue à...
    # await client.change_presence(activity=discord.Game(name="Chercher des films"))

    # Exemple 2: En stream... (nécessite une URL valide)
    # await client.change_presence(activity=discord.Streaming(name="L'état du serveur", url="https://www.twitch.tv/votre_chaine"))

    # Exemple 3: Écoute...
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="les commandes"))

    # Exemple 4: Regarde...
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="les films en stock")) # J'ai mis cet exemple ici

    # Vous pouvez également combiner une activité avec un statut (online, idle, dnd, invisible)
    # Pour un statut "Ne pas déranger" (dnd) avec une activité:
    # await client.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Gérer le serveur"))

    print("Statut du bot défini.")


# --- Fonctions utilitaires pour la gestion des films ---
# ... (le reste de votre code reste inchangé) ...

def load_films():
    """Charge les données des films depuis le fichier JSON."""
    if os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_films(films_data):
    """Sauvegarde les données des films dans le fichier JSON."""
    with open(FILMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(films_data, f, indent=4)

# --- Commandes du bot (pas de changement ici) ---

@tree.command(name="addmovie", description="Ajoute un film à la liste.")
@app_commands.describe(
    nom_film="Le nom du film à ajouter.",
    lien_film="Le lien du film (YouTube, etc.)."
)
@app_commands.default_permissions(manage_guild=True)
async def addmovie_command(interaction: discord.Interaction, nom_film: str, lien_film: str):
    """Commande pour ajouter un film."""
    films = load_films()
    if nom_film.lower() in {k.lower() for k in films.keys()}:
        embed = discord.Embed(
            title="Film déjà existant",
            description=f"Le film **{nom_film}** est déjà dans la liste.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    films[nom_film] = lien_film
    save_films(films)

    embed = discord.Embed(
        title="Film ajouté !",
        description=f"Le film **{nom_film}** a bien été ajouté à la liste.",
        color=discord.Color.green()
    )
    embed.add_field(name="Lien", value=lien_film, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- Commande /removemovie ---
@tree.command(name="removemovie", description="Supprime un film de la liste.")
@app_commands.describe(nom_film="Le nom du film à supprimer.")
@app_commands.default_permissions(manage_guild=True)
async def removemovie_command(interaction: discord.Interaction, nom_film: str):
    """Commande pour supprimer un film."""
    films = load_films()
    found_film_name = None
    for k in films.keys():
        if k.lower() == nom_film.lower():
            found_film_name = k
            break

    if found_film_name:
        del films[found_film_name]
        save_films(films)
        embed = discord.Embed(
            title="Film supprimé !",
            description=f"Le film **{found_film_name}** a bien été supprimé de la liste.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="Film introuvable",
            description=f"Le film **{nom_film}** n'est pas dans la liste.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Autocomplétion pour /removemovie (paramètre 'nom_film') ---
@removemovie_command.autocomplete('nom_film')
async def removemovie_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    films = load_films()
    matching_films = [
        app_commands.Choice(name=film_name, value=film_name)
        for film_name in films.keys()
        if current.lower() in film_name.lower()
    ]
    return matching_films[:25]


@tree.command(name="listmovie", description="Affiche tous les films enregistrés.")
async def listmovie_command(interaction: discord.Interaction):
    """Commande pour afficher tous les films."""
    films = load_films()
    if not films:
        embed = discord.Embed(
            title="Liste de films vide",
            description="Il n'y a aucun film enregistré pour le moment.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    film_entries = []
    for nom, lien in films.items():
        film_entries.append(f"**{nom}** : [Lien]({lien})")

    description = "\n".join(film_entries)

    embed = discord.Embed(
        title="Liste des films",
        description=description,
        color=discord.Color.blue()
    )
    if len(films) > 5:
        embed.set_footer(text=f"Total: {len(films)} films enregistrés.")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="randommovie", description="Affiche un film aléatoire de la liste.")
async def randommovie_command(interaction: discord.Interaction):
    """Commande pour afficher un film aléatoire."""
    films = load_films()
    if not films:
        embed = discord.Embed(
            title="Liste de films vide",
            description="Impossible de choisir un film, la liste est vide.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    nom_film, lien_film = random.choice(list(films.items()))

    embed = discord.Embed(
        title="Votre film aléatoire est :",
        description=f"**{nom_film}**\n[Regarder le film]({lien_film})",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Démarrage du bot ---
if __name__ == "__main__":
    if not os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
    client.run(DISCORD_BOT_TOKEN)
