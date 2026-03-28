# 00 - Installation et Configuration

## Prérequis

- Docker Desktop >= 24.0 (ou Docker Engine + Docker Compose V2)
- Python >= 3.10
- 4 Go RAM minimum
- Ports libres : **7233** (Temporal), **8080** (UI), **5432** (PostgreSQL)

## Lancement de la stack

```bash
# 1. Cloner le dépôt
git clone https://github.com/opinaka-attik/atelier-temporal.git
cd atelier-temporal

# 2. Lancer tous les services
cd docker
docker compose up -d

# 3. Vérifier que tout tourne
docker compose ps
```

### Services démarrés

| Service | Port | Role |
|---------|------|------|
| temporal | 7233 | Serveur gRPC principal |
| temporal-ui | 8080 | Interface web |
| postgres | 5432 | Base de données du serveur |
| temporal-worker | - | Executes les workflows Python |

## Accès à l'interface

Ouvrir : **http://localhost:8080**

Aucune authentification requise en mode développement.

## Installation du SDK Python

```bash
# Depuis la racine du projet
pip install temporalio

# Ou avec un environnement virtuel (recommandé)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install temporalio
```

## Test de connexion

```bash
# Vérifier que le serveur Temporal répond
python -c "
import asyncio
from temporalio.client import Client
async def test():
    client = await Client.connect('localhost:7233')
    print('Connexion OK :', client.identity)
asyncio.run(test())
"
```

## Lancer un workflow de test

```bash
# Dans un terminal : lancer le worker
python workflows/01_hello_temporal.py worker

# Dans un autre terminal : lancer le client
python workflows/01_hello_temporal.py client

# Observer le résultat dans l'UI : http://localhost:8080
```

## Arrêt et nettoyage

```bash
cd docker

# Arrêter
docker compose down

# Arrêter et supprimer les volumes (reset complet)
docker compose down -v
```

## Dépannage rapide

| Problème | Solution |
|---------|----------|
| Port 7233 déjà utilisé | `lsof -i :7233` puis kill le processus |
| Temporal ne démarre pas | Attendre que PostgreSQL soit healthy d'abord |
| Worker ne se connecte pas | Vérifier que Temporal écoute sur `localhost:7233` |
| Erreur SDK Python | `pip install --upgrade temporalio` |
