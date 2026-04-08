# Gas Finder ⛽

Une application Web complète de comparaison de prix de carburants en France en temps réel.

## Fonctionnalités
- 📍 **Géolocalisation** : Recherche par adresse avec autocomplétion Google Places.
- ⛽ **Prix en Temps Réel** : Données récupérées directement depuis le flux officiel de `data.gouv.fr`.
- 📊 **Classement par Prix** : Les 5 stations les plus proches, triées par prix pour le carburant sélectionné.
- 🏢 **Identification des Enseignes** : Utilisation de l'API Google Places pour afficher les noms réels des marques (Total, Shell, BP, etc.).
- 📜 **Historique de Recherche** : Accès rapide aux 5 dernières adresses consultées.
- 🐳 **Docker Ready** : Lancement simplifié via Docker Compose.

## Installation Locale

1. **Cloner le projet**
2. **Ajouter votre clé API Google** dans un fichier `.env` :
   ```env
   GOOGLE_MAPS_API_KEY=VOTRE_CLE_API
   ```
3. **Lancer avec Docker** :
   ```bash
   docker compose up --build
   ```
   *Ou classiquement : `pip install -r requirements.txt` puis `python -m app.main`.*

4. **Accès** : [http://localhost:8000](http://localhost:8000)

## Tech Stack
- **Backend** : FastAPI (Python)
- **Frontend** : JavaScript Vanille, HTML5, CSS3
- **APIs** : Google Maps JS API, Google Places, Google Geocoding, data.gouv.fr
