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

# Liste des genres disponibles (basée sur votre image, sans Western)
GENRES = [
    "Action", "Animation", "Aventure", "Comédie", "Crime", "Documentaire",
    "Drame", "Familial", "Fantastique", "Guerre", "Histoire", "Horreur",
    "Mystère", "Romance", "Science-fiction", "Thriller"
]

# Initialiser le client Discord avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialiser le client Discord et l'arborescence de commandes
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Status bot
@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")
    try:
        synced = await tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

    # Définition du statut du bot
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="les films en stock"))
    print("Statut du bot défini.")

# --- Fonctions utilitaires pour la gestion des films ---

def load_films():
    """Charge les données des films depuis le fichier JSON."""
    if os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Migration de l'ancienne structure si nécessaire
                migrated = False
                for film_name, film_info in data.items():
                    if isinstance(film_info, str): # Si c'est l'ancienne structure (juste le lien)
                        data[film_name] = {"lien": film_info, "genre": "Non spécifié"}
                        migrated = True
                if migrated:
                    save_films(data) # Sauvegarde après migration
                    print("Anciens films migrés vers la nouvelle structure.")
                return data
            except json.JSONDecodeError:
                print(f"Erreur de lecture du fichier {FILMS_FILE}. Il est peut-être vide ou corrompu.")
                return {}
    return {}

def save_films(films_data):
    """Sauvegarde les données des films dans le fichier JSON."""
    with open(FILMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(films_data, f, indent=4)

# --- Commandes du bot ---

@tree.command(name="addmovie", description="Ajoute un film à la liste.")
@app_commands.describe(
    nom_film="Le nom du film à ajouter.",
    lien_film="Le lien du film (YouTube, etc.).",
    genre="Le genre du film."
)
@app_commands.choices(genre=[app_commands.Choice(name=g, value=g) for g in GENRES])
@app_commands.default_permissions(manage_guild=True)
async def addmovie_command(interaction: discord.Interaction, nom_film: str, lien_film: str, genre: app_commands.Choice[str]):
    """Commande pour ajouter un film."""
    films = load_films()
    # Vérifie si le film existe déjà (insensible à la casse)
    if nom_film.lower() in {k.lower() for k in films.keys()}:
        embed = discord.Embed(
            title="Film déjà existant",
            description=f"Le film **{nom_film}** est déjà dans la liste.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Sauvegarde le film avec son lien et son genre
    films[nom_film] = {"lien": lien_film, "genre": genre.value}
    save_films(films)

    embed = discord.Embed(
        title="Film ajouté !",
        description=f"Le film **{nom_film}** ({genre.value}) a bien été ajouté à la liste.",
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
    for nom, film_info in films.items():
        # Accède au lien via film_info['lien'] et au genre via film_info['genre']
        lien = film_info.get("lien", "N/A") # Utilise .get pour la rétrocompatibilité
        genre = film_info.get("genre", "Non spécifié")
        film_entries.append(f"**{nom}** ({genre}) : [Lien]({lien})")

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
@app_commands.describe(
    genre="Le genre de film à choisir aléatoirement (laissez vide pour tous les genres)."
)
@app_commands.choices(genre=[app_commands.Choice(name="Tous les genres", value="all")] + [app_commands.Choice(name=g, value=g) for g in GENRES])
async def randommovie_command(interaction: discord.Interaction, genre: app_commands.Choice[str] = None):
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

    filtered_films = {}
    selected_genre_name = "Tous les genres"

    if genre and genre.value != "all":
        selected_genre_name = genre.value
        # Filtre les films par le genre sélectionné
        for nom, film_info in films.items():
            if film_info.get("genre") == genre.value:
                filtered_films[nom] = film_info
    else:
        # Si aucun genre n'est spécifié ou si "all" est choisi, utilise tous les films
        filtered_films = films

    if not filtered_films:
        embed = discord.Embed(
            title="Aucun film trouvé",
            description=f"Aucun film trouvé pour le genre **{selected_genre_name}**.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Choisit un film aléatoirement parmi les films filtrés
    nom_film, film_info = random.choice(list(filtered_films.items()))
    lien_film = film_info.get("lien", "N/A")
    film_genre = film_info.get("genre", "Non spécifié")


    embed = discord.Embed(
        title="Votre film aléatoire est :",
        description=f"**{nom_film}** ({film_genre})\n[Regarder le film]({lien_film})",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Démarrage du bot ---
if __name__ == "__main__":
    if not os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
    client.run(DISCORD_BOT_TOKEN)
