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

# Liste des genres disponibles
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
                migrated = False
                # Migration de l'ancienne structure (genre en str vers liste, ajout description)
                for film_name, film_info in data.items():
                    if isinstance(film_info, str): # Ancienne structure (juste le lien)
                        data[film_name] = {"lien": film_info, "genre": ["Non spécifié"], "description": "Aucune description."}
                        migrated = True
                    else:
                        if "genre" not in film_info: # Si le genre n'existe pas
                            film_info["genre"] = ["Non spécifié"]
                            migrated = True
                        elif isinstance(film_info["genre"], str): # Si le genre est une chaîne (ancien format multi-genre ou mono-genre)
                            genres_list = [g.strip() for g in film_info["genre"].split(',') if g.strip()]
                            film_info["genre"] = [g for g in genres_list if g in GENRES] or ["Non spécifié"]
                            migrated = True
                        
                        if "description" not in film_info: # Si la description n'existe pas
                            film_info["description"] = "Aucune description."
                            migrated = True
                if migrated:
                    save_films(data) # Sauvegarde après migration
                    print("Anciens films migrés vers la nouvelle structure (genre en liste et description).")
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

@tree.command(name="addmovie", description="Ajoute un film à la liste avec un ou plusieurs genres.")
@app_commands.describe(
    nom_film="Le nom du film à ajouter.",
    lien_film="Le lien du film (YouTube, etc.).",
    genres_str="Un ou plusieurs genres séparés par des virgules (ex: 'Action, Comédie').",
    description="Une courte description du film (optionnel)."
)
@app_commands.default_permissions(manage_guild=True)
async def addmovie_command(
    interaction: discord.Interaction,
    nom_film: str,
    lien_film: str,
    genres_str: str,
    description: str = "Aucune description."
):
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

    parsed_genres = []
    for g_raw in [s.strip() for s in genres_str.split(',')]:
        if g_raw:
            found_genre = next((item for item in GENRES if item.lower() == g_raw.lower()), None)
            if found_genre:
                parsed_genres.append(found_genre)
            else:
                await interaction.followup.send(f"Attention : Le genre '{g_raw}' n'est pas reconnu et ne sera pas ajouté.", ephemeral=True)
    
    if not parsed_genres:
        parsed_genres = ["Non spécifié"]

    films[nom_film] = {"lien": lien_film, "genre": parsed_genres, "description": description}
    save_films(films)

    embed = discord.Embed(
        title="Film ajouté !",
        description=f"Le film **{nom_film}** ({', '.join(parsed_genres)}) a bien été ajouté à la liste.",
        color=discord.Color.green()
    )
    embed.add_field(name="Lien", value=lien_film, inline=False)
    if description != "Aucune description.":
        embed.add_field(name="Description", value=description, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Autocomplétion pour /addmovie (paramètre 'genres_str') ---
@addmovie_command.autocomplete('genres_str')
async def addmovie_autocomplete_genres(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    parts = [s.strip() for s in current.split(',')]
    last_part = parts[-1] if parts else ""
    
    suggestions = []
    for g in GENRES:
        if last_part.lower() in g.lower():
            if len(parts) > 1:
                suggested_value = ", ".join(parts[:-1] + [g])
            else:
                suggested_value = g
            suggestions.append(app_commands.Choice(name=suggested_value, value=suggested_value))
    return suggestions[:25]


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


# --- Commande /movieinfo ---
@tree.command(name="movieinfo", description="Affiche les informations détaillées d'un film.")
@app_commands.describe(nom_film="Le nom du film dont vous voulez les informations.")
async def movieinfo_command(interaction: discord.Interaction, nom_film: str):
    """Commande pour afficher les informations d'un film."""
    films = load_films()
    film_data = None
    original_film_name = None

    for name, data in films.items():
        if name.lower() == nom_film.lower():
            film_data = data
            original_film_name = name
            break

    if film_data:
        lien = film_data.get("lien", "N/A")
        genres = film_data.get("genre", ["Non spécifié"])
        description = film_data.get("description", "Aucune description.")

        embed = discord.Embed(
            title=f"Informations sur : {original_film_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Genre(s)", value=", ".join(genres), inline=True)
        embed.add_field(name="Lien", value=f"[Cliquer ici]({lien})", inline=True)
        embed.add_field(name="Description", value=description, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="Film introuvable",
            description=f"Le film **{nom_film}** n'est pas dans la liste.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Autocomplétion pour /movieinfo (paramètre 'nom_film') ---
@movieinfo_command.autocomplete('nom_film')
async def movieinfo_autocomplete(
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
        lien = film_info.get("lien", "N/A")
        genres = film_info.get("genre", ["Non spécifié"])
        film_entries.append(f"**{nom}** ({', '.join(genres)}) : [Lien]({lien})")

    description = "\n".join(film_entries)

    embed = discord.Embed(
        title="Liste des films",
        description=description,
        color=discord.Color.blue()
    )
    if len(films) > 5:
        embed.set_footer(text=f"Total: {len(films)} films enregistrés.")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="statsmovies", description="Affiche les statistiques sur les films enregistrés.")
async def moviestats_command(interaction: discord.Interaction):
    """Commande pour afficher le nombre de films et leur répartition par genre."""
    films = load_films()
    total_films = len(films)

    if total_films == 0:
        embed = discord.Embed(
            title="Statistiques des films",
            description="Aucun film enregistré pour le moment.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    genre_counts = {}
    for film_name, film_info in films.items():
        film_genres = film_info.get("genre", ["Non spécifié"])
        if not isinstance(film_genres, list):
            film_genres = [film_genres]

        for genre in film_genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1

    sorted_genres = sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)

    stats_description = f"**Nombre total de films :** {total_films}\n\n**Films par genre :**\n"
    if sorted_genres:
        for genre, count in sorted_genres:
            stats_description += f"- {genre}: {count} film(s)\n"
    else:
        stats_description += "Aucun genre n'a pu être identifié."


    embed = discord.Embed(
        title="Statistiques de la collection de films",
        description=stats_description,
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="randommovie", description="Affiche un film aléatoire de la liste en fonction des genres.")
@app_commands.describe(
    genres="Un ou plusieurs genres séparés par des virgules (ex: 'Action, Comédie'). Laissez vide pour tous les genres."
)
async def randommovie_command(interaction: discord.Interaction, genres: str = None):
    """Commande pour afficher un film aléatoire, filtré par un ou plusieurs genres."""
    films = load_films()
    if not films:
        embed = discord.Embed(
            title="Liste de films vide",
            description="Impossible de choisir un film, la liste est vide.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    requested_genres = []
    if genres:
        for g_raw in [s.strip() for s in genres.split(',')]:
            if g_raw:
                found_genre = next((item for item in GENRES if item.lower() == g_raw.lower()), None)
                if found_genre:
                    requested_genres.append(found_genre)
                else:
                    await interaction.followup.send(f"Le genre '{g_raw}' n'est pas reconnu et sera ignoré.", ephemeral=True)

    if not requested_genres:
        selected_genre_display = "Tous les genres"
        filtered_films = films
    else:
        selected_genre_display = ", ".join(requested_genres)
        filtered_films = {}
        for nom, film_info in films.items():
            film_genres = film_info.get("genre", ["Non spécifié"])
            if not isinstance(film_genres, list):
                film_genres = [film_genres]

            # Vérifie si le film contient TOUS les genres demandés
            if all(g in film_genres for g in requested_genres):
                filtered_films[nom] = film_info

    if not filtered_films:
        embed = discord.Embed(
            title="Aucun film trouvé",
            description=f"Aucun film trouvé pour le(s) genre(s) : **{selected_genre_display}**.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    nom_film, film_info = random.choice(list(filtered_films.items()))
    lien_film = film_info.get("lien", "N/A")
    film_genres_display = ", ".join(film_info.get("genre", ["Non spécifié"]))
    film_description = film_info.get("description", "Aucune description.")

    embed = discord.Embed(
        title="Votre film aléatoire est :",
        description=f"**{nom_film}** ({film_genres_display})\n[Regarder le film]({lien_film})",
        color=discord.Color.purple()
    )
    if film_description != "Aucune description.":
        embed.add_field(name="Description", value=film_description, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- NOUVELLE COMMANDE : /editmovie ---
@tree.command(name="editmovie", description="Modifie un film existant.")
@app_commands.describe(
    nom_film="Le nom du film à modifier.",
    nouveau_nom="Le nouveau nom du film (optionnel).",
    nouveau_lien="Le nouveau lien du film (optionnel).",
    nouveaux_genres="Un ou plusieurs nouveaux genres séparés par des virgules (optionnel).",
    nouvelle_description="La nouvelle description du film (optionnel)."
)
@app_commands.default_permissions(manage_guild=True)
async def editmovie_command(
    interaction: discord.Interaction,
    nom_film: str,
    nouveau_nom: str = None,
    nouveau_lien: str = None,
    nouveaux_genres: str = None,
    nouvelle_description: str = None
):
    """Commande pour modifier un film."""
    films = load_films()
    original_film_name = None
    film_data = None

    # Trouver le film en ignorant la casse et garder le nom original
    for name, data in films.items():
        if name.lower() == nom_film.lower():
            film_data = data
            original_film_name = name
            break

    if not film_data:
        embed = discord.Embed(
            title="Film introuvable",
            description=f"Le film **{nom_film}** n'est pas dans la liste.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Préparer le message de confirmation
    changes_made = []
    new_film_name = original_film_name # Commencer avec le nom actuel
    updated_film_data = film_data.copy() # Créer une copie pour les modifications

    # 1. Modifier le nom du film
    if nouveau_nom and nouveau_nom.lower() != original_film_name.lower():
        # Vérifier si le nouveau nom existe déjà (sauf si c'est le même film)
        if nouveau_nom.lower() in {k.lower() for k in films.keys() if k.lower() != original_film_name.lower()}:
            embed = discord.Embed(
                title="Erreur de modification",
                description=f"Le nouveau nom **{nouveau_nom}** est déjà utilisé par un autre film.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        new_film_name = nouveau_nom
        changes_made.append(f"Nom : `{original_film_name}` -> `{new_film_name}`")
        # Supprimer l'ancienne entrée et ajouter la nouvelle plus tard
        del films[original_film_name]

    # 2. Modifier le lien
    if nouveau_lien and nouveau_lien != updated_film_data.get("lien"):
        updated_film_data["lien"] = nouveau_lien
        changes_made.append(f"Lien : `{film_data.get('lien', 'N/A')}` -> `{nouveau_lien}`")

    # 3. Modifier les genres
    if nouveaux_genres is not None: # Utiliser 'is not None' car une chaîne vide est valide si l'utilisateur veut supprimer les genres
        parsed_new_genres = []
        if nouveaux_genres: # Si l'utilisateur a fourni des genres
            for g_raw in [s.strip() for s in nouveaux_genres.split(',')]:
                if g_raw:
                    found_genre = next((item for item in GENRES if item.lower() == g_raw.lower()), None)
                    if found_genre:
                        parsed_new_genres.append(found_genre)
                    else:
                        await interaction.followup.send(f"Attention : Le genre '{g_raw}' n'est pas reconnu et ne sera pas ajouté.", ephemeral=True)
        
        # Si aucun genre valide n'a été fourni ou si la chaîne était vide, utilise "Non spécifié"
        if not parsed_new_genres:
            parsed_new_genres = ["Non spécifié"]

        # Comparer avec les genres existants pour voir s'il y a un changement réel
        if sorted(parsed_new_genres) != sorted(updated_film_data.get("genre", [])):
            changes_made.append(f"Genre(s) : `{', '.join(film_data.get('genre', ['Non spécifié']))}` -> `{', '.join(parsed_new_genres)}`")
            updated_film_data["genre"] = parsed_new_genres


    # 4. Modifier la description
    if nouvelle_description is not None and nouvelle_description != updated_film_data.get("description"):
        updated_film_data["description"] = nouvelle_description
        changes_made.append(f"Description : `{film_data.get('description', 'Aucune description.')}` -> `{nouvelle_description}`")
    
    if not changes_made:
        embed = discord.Embed(
            title="Aucune modification",
            description=f"Aucune modification n'a été spécifiée pour le film **{original_film_name}**.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Appliquer les modifications et sauvegarder
    films[new_film_name] = updated_film_data
    save_films(films)

    embed = discord.Embed(
        title="Film modifié !",
        description=f"Le film **{original_film_name}** a été mis à jour.",
        color=discord.Color.green()
    )
    for change in changes_made:
        embed.add_field(name="Modification", value=change, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Autocomplétion pour /editmovie (paramètre 'nom_film') ---
@editmovie_command.autocomplete('nom_film')
async def editmovie_autocomplete_film_name(
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

# --- Autocomplétion pour /editmovie (paramètre 'nouveaux_genres') ---
@editmovie_command.autocomplete('nouveaux_genres')
async def editmovie_autocomplete_genres(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    parts = [s.strip() for s in current.split(',')]
    last_part = parts[-1] if parts else ""
    
    suggestions = []
    for g in GENRES:
        if last_part.lower() in g.lower():
            if len(parts) > 1:
                suggested_value = ", ".join(parts[:-1] + [g])
            else:
                suggested_value = g
            suggestions.append(app_commands.Choice(name=suggested_value, value=suggested_value))
    return suggestions[:25]


# --- Démarrage du bot ---
if __name__ == "__main__":
    if not os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
    client.run(DISCORD_BOT_TOKEN)
