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

# Liste des genres disponibles (MAJ : Ajout de "Western")
GENRES = [
    "Action", "Animation", "Aventure", "Comédie", "Crime", "Documentaire",
    "Drame", "Familial", "Fantastique", "Guerre", "Histoire", "Horreur",
    "Mystère", "Romance", "Science-fiction", "Thriller", "Western" 
]

# Initialiser le client Discord avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialiser le client Discord et l'arborescence de commandes
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# --- Fonctions d'autocomplétion ---

async def add_autocomplete_genres(
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

async def remove_autocomplete_film_name(
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

async def info_autocomplete_film_name(
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

async def random_autocomplete_genres(
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

async def list_autocomplete_genres(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    suggestions = []
    for g in GENRES:
        if current.lower() in g.lower():
            suggestions.append(app_commands.Choice(name=g, value=g))
    return suggestions[:25]

async def edit_autocomplete_film_name(
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

async def edit_autocomplete_genres(
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


# --- Status bot ---
@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")
    try:
        synced = await tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

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
                for film_name, film_info in data.items():
                    if isinstance(film_info, str): 
                        data[film_name] = {"lien": film_info, "genre": ["Non spécifié"], "description": "Aucune description."}
                        migrated = True
                    else:
                        if "genre" not in film_info: 
                            film_info["genre"] = ["Non spécifié"]
                            migrated = True
                        elif isinstance(film_info["genre"], str):
                            genres_list = [g.strip() for g in film_info["genre"].split(',') if g.strip()]
                            film_info["genre"] = [g for g in genres_list if g in GENRES] or ["Non spécifié"]
                            migrated = True
                        
                        if "description" not in film_info: 
                            film_info["description"] = "Aucune description."
                            migrated = True
                if migrated:
                    save_films(data) 
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

@tree.command(name="add", description="Ajoute un film à la liste avec un ou plusieurs genres.")
@app_commands.describe(
    nom_film="Le nom du film à ajouter.",
    lien_film="Le lien du film (YouTube, etc.) (optionnel).",
    genres_str="Un ou plusieurs genres séparés par des virgules (ex: 'Action, Comédie') (optionnel).",
    description="Une courte description du film (optionnel)."
)
@app_commands.autocomplete(genres_str=add_autocomplete_genres)
@app_commands.default_permissions(manage_guild=True)
async def add_command(
    interaction: discord.Interaction,
    nom_film: str,
    lien_film: str = "N/A", 
    genres_str: str = "", 
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
    if genres_str:
        for g_raw in [s.strip() for s in genres_str.split(',')]:
            if g_raw:
                found_genre = next((item for item in GENRES if item.lower() == g_raw.lower()), None)
                if found_genre:
                    parsed_genres.append(found_genre)
                else:
                    # Utilisez followup.send pour les messages additionnels APRES la première réponse
                    # Nous ne pouvons pas envoyer de followup ici avant la réponse initiale.
                    # Pour gérer les genres non reconnus, nous les ignorerons silencieusement ou avertirons plus tard.
                    pass # Nous allons ignorer les genres non reconnus ici pour éviter l'erreur
    
    if not parsed_genres:
        parsed_genres = ["Non spécifié"]

    films[nom_film] = {"lien": lien_film, "genre": parsed_genres, "description": description}
    save_films(films)

    embed = discord.Embed(
        title="Film ajouté !",
        description=f"Le film **{nom_film}** ({', '.join(parsed_genres)}) a bien été ajouté à la liste.",
        color=discord.Color.green()
    )
    if lien_film != "N/A":
        embed.add_field(name="Lien", value=lien_film, inline=False)
    if description != "Aucune description.":
        embed.add_field(name="Description", value=description, inline=False)
    
    # La seule réponse initiale
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="remove", description="Supprime un film de la liste.")
@app_commands.describe(nom_film="Le nom du film à supprimer.")
@app_commands.autocomplete(nom_film=remove_autocomplete_film_name)
@app_commands.default_permissions(manage_guild=True)
async def remove_command(interaction: discord.Interaction, nom_film: str):
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


@tree.command(name="info", description="Affiche les informations détaillées d'un film.")
@app_commands.describe(nom_film="Le nom du film dont vous voulez les informations.")
@app_commands.autocomplete(nom_film=info_autocomplete_film_name)
async def info_command(interaction: discord.Interaction, nom_film: str):
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
        if lien != "N/A":
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


@tree.command(name="list", description="Affiche tous les films enregistrés ou filtre par genre.")
@app_commands.describe(
    genre="Filtrez les films par un genre spécifique. Laissez vide pour afficher tous les films."
)
@app_commands.autocomplete(genre=list_autocomplete_genres)
async def list_command(interaction: discord.Interaction, genre: str = None):
    """Commande pour afficher tous les films ou filtrer par genre."""
    films = load_films()
    
    # Prépare l'embed de réponse en fonction des conditions
    embed = None
    
    if not films:
        embed = discord.Embed(
            title="Liste de films vide",
            description="Il n'y a aucun film enregistré pour le moment.",
            color=discord.Color.blue()
        )
    elif genre:
        found_genre = next((g for g in GENRES if g.lower() == genre.lower()), None)
        if not found_genre:
            embed = discord.Embed(
                title="Genre inconnu",
                description=f"Le genre **{genre}** n'est pas reconnu. Veuillez choisir parmi les suggestions.",
                color=discord.Color.orange()
            )
        else:
            display_genre = found_genre
            film_entries = []
            filtered_films_count = 0
            for nom, film_info in films.items():
                film_genres = film_info.get("genre", ["Non spécifié"])
                if not isinstance(film_genres, list):
                    film_genres = [film_genres]

                if display_genre in film_genres:
                    lien = film_info.get("lien", "N/A")
                    genres_display = ", ".join(film_genres)
                    if lien != "N/A":
                        film_entries.append(f"**{nom}** ({genres_display}) : [Lien]({lien})")
                    else:
                        film_entries.append(f"**{nom}** ({genres_display})")
                    filtered_films_count += 1
            
            if not film_entries:
                embed = discord.Embed(
                    title="Aucun film trouvé",
                    description=f"Aucun film trouvé pour le genre : **{display_genre}**.",
                    color=discord.Color.orange()
                )
            else:
                title_description = f"Liste des films pour le genre : {display_genre}"
                footer_text = f"Total: {filtered_films_count} film(s) dans ce genre."
                description_content = "\n".join(film_entries)

                embed = discord.Embed(
                    title=title_description,
                    description=description_content,
                    color=discord.Color.blue()
                )
                if filtered_films_count > 5: 
                    embed.set_footer(text=footer_text)

    else: # Aucun genre n'est fourni, affiche tous les films
        film_entries = []
        for nom, film_info in films.items():
            lien = film_info.get("lien", "N/A")
            genres_display = ", ".join(film_info.get("genre", ["Non spécifié"]))
            if lien != "N/A":
                film_entries.append(f"**{nom}** ({genres_display}) : [Lien]({lien})")
            else:
                film_entries.append(f"**{nom}** ({genres_display})")
        
        filtered_films_count = len(films)
        title_description = "Liste de tous les films"
        footer_text = f"Total: {filtered_films_count} films enregistrés."
        description_content = "\n".join(film_entries)

        embed = discord.Embed(
            title=title_description,
            description=description_content,
            color=discord.Color.blue()
        )
        if filtered_films_count > 5: 
            embed.set_footer(text=footer_text)
    
    # Envoie la seule et unique réponse
    if embed: # S'assure qu'un embed a bien été créé
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else: # Au cas où aucun embed n'aurait été créé pour une raison inattendue
        await interaction.response.send_message("Une erreur inattendue est survenue.", ephemeral=True)


@tree.command(name="stats", description="Affiche les statistiques sur les films enregistrés.")
async def stats_command(interaction: discord.Interaction):
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


@tree.command(name="random", description="Affiche un film aléatoire de la liste en fonction des genres.")
@app_commands.describe(
    genres="Un ou plusieurs genres séparés par des virgules (ex: 'Action, Comédie'). Laissez vide pour tous les genres."
)
@app_commands.autocomplete(genres=random_autocomplete_genres)
async def random_command(interaction: discord.Interaction, genres: str = None):
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
                    # Ici, si vous voulez un avertissement, il faudrait d'abord defer la réponse
                    # ou inclure l'avertissement dans le message final.
                    pass 

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

            # ATTENTION : Cette ligne filtre les films qui ont *tous* les genres demandés.
            # Si vous voulez un film qui a *au moins un* des genres demandés,
            # remplacez 'all' par 'any': 'if any(g in film_genres for g in requested_genres):'
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
        description=f"**{nom_film}** ({film_genres_display})",
        color=discord.Color.purple()
    )
    if lien_film != "N/A":
        embed.add_field(name="Lien", value=f"[Regarder le film]({lien_film})", inline=False)
    if film_description != "Aucune description.":
        embed.add_field(name="Description", value=film_description, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="edit", description="Modifie un film existant.")
@app_commands.describe(
    nom_film="Le nom du film à modifier.",
    nouveau_nom="Le nouveau nom du film (optionnel).",
    nouveau_lien="Le nouveau lien du film (optionnel).",
    nouveaux_genres="Un ou plusieurs nouveaux genres séparés par des virgules (optionnel).",
    nouvelle_description="La nouvelle description du film (optionnel)."
)
@app_commands.autocomplete(nom_film=edit_autocomplete_film_name)
@app_commands.autocomplete(nouveaux_genres=edit_autocomplete_genres)
@app_commands.default_permissions(manage_guild=True)
async def edit_command(
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

    changes_made = []
    new_film_name = original_film_name
    updated_film_data = film_data.copy()

    if nouveau_nom and nouveau_nom.lower() != original_film_name.lower():
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
        del films[original_film_name]

    if nouveau_lien is not None and nouveau_lien != updated_film_data.get("lien"):
        updated_film_data["lien"] = nouveau_lien
        changes_made.append(f"Lien : `{film_data.get('lien', 'N/A')}` -> `{nouveau_lien}`")

    if nouveaux_genres is not None:
        parsed_new_genres = []
        if nouveaux_genres:
            for g_raw in [s.strip() for s in nouveaux_genres.split(',')]:
                if g_raw:
                    found_genre = next((item for item in GENRES if item.lower() == g_raw.lower()), None)
                    if found_genre:
                        parsed_new_genres.append(found_genre)
                    else:
                        # Comme pour /add, on gère les messages d'avertissement séparément
                        pass
        
        if not parsed_new_genres:
            parsed_new_genres = ["Non spécifié"]

        if sorted(parsed_new_genres) != sorted(updated_film_data.get("genre", [])):
            changes_made.append(f"Genre(s) : `{', '.join(film_data.get('genre', ['Non spécifié']))}` -> `{', '.join(parsed_new_genres)}`")
            updated_film_data["genre"] = parsed_new_genres

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


# --- Démarrage du bot ---
if __name__ == "__main__":
    if not os.path.exists(FILMS_FILE):
        with open(FILMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
    client.run(DISCORD_BOT_TOKEN)
