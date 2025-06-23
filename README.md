# Bot de Gestion de Films Discord

Ce bot Discord permet aux utilisateurs de gérer une liste de films, y compris l'ajout, la suppression, la modification, la recherche d'informations, la liste complète ou par genre, et la sélection aléatoire de films. Il utilise les commandes slash de Discord pour une meilleure intégration.

## Fonctionnalités

* **`/add`**: Ajoute un nouveau film à la liste.
    * `nom_film`: Le nom du film.
    * `lien_film` (optionnel): Un lien vers le film (ex: YouTube, bande-annonce).
    * `genres_str` (optionnel): Un ou plusieurs genres séparés par des virgules (ex: "Action, Comédie"). L'autocomplétion est disponible.
    * `description` (optionnel): Une courte description du film.
* **`/remove`**: Supprime un film existant de la liste. L'autocomplétion du nom du film est disponible.
* **`/info`**: Affiche les informations détaillées d'un film spécifique (nom, lien, genres, description). L'autocomplétion du nom du film est disponible.
* **`/list`**: Affiche la liste de tous les films enregistrés, ou filtre par genre.
    * `genre` (optionnel): Filtre les films par un genre spécifique. L'autocomplétion est disponible.
* **`/stats`**: Affiche des statistiques sur la collection de films, incluant le nombre total de films et leur répartition par genre.
* **`/random`**: Sélectionne et affiche un film aléatoire de la liste, avec une option pour filtrer par un ou plusieurs genres. L'autocomplétion des genres est disponible.
* **`/edit`**: Modifie les informations d'un film existant. L'autocomplétion du nom du film et des genres est disponible.
    * `film_a_modifier`: Le nom du film à modifier.
    * `nom` (optionnel): Le nouveau nom du film.
    * `lien` (optionnel): Le nouveau lien du film.
    * `genres` (optionnel): Un ou plusieurs nouveaux genres séparés par des virgules.
    * `description` (optionnel): La nouvelle description du film.

## Prérequis

* Python 3.8 ou supérieur (le script utilise `python3.13` dans les exemples, assurez-vous que cette version est installée ou adaptez la commande).
* Un compte Discord et un serveur Discord où vous avez les permissions de gérer les bots.
* Une application de bot Discord créée dans le [Portail des Développeurs Discord](https://discord.com/developers/applications).

## Installation et Mise en Place

Suivez ces étapes pour configurer et exécuter le bot sur votre machine.

1.  **Clonez le dépôt :**
    ```bash
    git clone https://github.com/jokikj/bot-discord-movie.git
    cd bot-discord-movie
    ```

2.  **Créez un environnement virtuel (recommandé) :**
    Un environnement virtuel isole les dépendances de votre projet du reste de votre système.
    ```bash
    python3 -m venv myenv
    ```

3.  **Activez l'environnement virtuel :**
    * Sur macOS/Linux :
        ```bash
        source myenv/bin/activate
        ```
    * Sur Windows (Command Prompt) :
        ```bash
        myenv\Scripts\activate.bat
        ```
    * Sur Windows (PowerShell) :
        ```powershell
        .\myenv\Scripts\Activate.ps1
        ```

4.  **Installez les dépendances Python :**
    Une fois l'environnement virtuel activé, installez les bibliothèques nécessaires :
    ```bash
    pip install discord.py python-dotenv
    ```

5.  **Créez un fichier `.env` :**
    À la racine de votre projet (là où se trouve votre script Python, par exemple `bot.py`), créez un fichier nommé `.env`. Ce fichier contiendra votre token de bot Discord.
    ```
    DISCORD_BOT_TOKEN=VOTRE_TOKEN_DE_BOT_ICI
    ```
    Remplacez `VOTRE_TOKEN_DE_BOT_ICI` par le token de votre bot que vous trouverez dans le [Portail des Développeurs Discord](https://discord.com/developers/applications) sous votre application de bot (Onglet `Bot` -> `Token` -> `Copy`).

6.  **Activez les Intents privilégiés dans Discord Developer Portal :**
    Dans le [Portail des Développeurs Discord](https://discord.com/developers/applications), sélectionnez votre application de bot.
    Allez dans l'onglet **Bot** sur le côté gauche.
    Sous "Privileged Gateway Intents", activez les options suivantes :
    * `PRESENCE INTENT` (nécessaire pour le statut `idle`)
    * `MESSAGE CONTENT INTENT`
    * `SERVER MEMBERS INTENT` (nécessaire pour certaines fonctionnalités futures ou la gestion avancée des membres si vous l'ajoutez)

7.  **Invitez le bot sur votre serveur Discord :**
    Dans le [Portail des Développeurs Discord](https://discord.com/developers/applications), allez dans l'onglet **OAuth2** -> **URL Generator**.
    * Cochez `bot` et `applications.commands` sous "SCOPES".
    * Sous "BOT PERMISSIONS", cochez les permissions nécessaires (par exemple, `Send Messages`, `Read Message History`, `Manage Guild` pour les commandes d'administration).
    * Copiez l'URL générée et collez-la dans votre navigateur pour inviter le bot sur votre serveur.

## Exécution du bot

Une fois toutes les étapes d'installation terminées, et avec votre environnement virtuel activé :

```bash
python3.13 bot.py
