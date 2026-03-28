# Atelier Temporal

> Orchestration de workflows durables — concurrent moderne à Camunda

## Description

Cet atelier pratique vous permet de découvrir **Temporal**, une plateforme d'orchestration de workflows durables codés en Python (ou Go, Java, TypeScript). Contrairement à Camunda qui utilise BPMN graphique, Temporal définit les workflows **en code pur**, avec durabilité, retry automatique et support natif des longues tâches.

## Pourquoi Temporal vs Camunda ?

| Aspect | Camunda | Temporal |
|--------|---------|----------|
| Définition | BPMN XML / graphique | Code Python/Go/Java/TS |
| Durabilité | Checkpoints BDD | Event Sourcing complet |
| Replay | Non | Oui (déterministe) |
| Human Tasks | User Task natif | Signal + wait_condition |
| Long-running | Oui | Oui (années) |
| Langage | Java / Spring | Python, Go, Java, TS |
| Cloud-native | Zeebe | Temporal Cloud / self-hosted |

## Prérequis

- Docker & Docker Compose installés
- Python >= 3.10 + `pip install temporalio`
- 4 Go de RAM minimum
- Ports 7233 (gRPC) et 8080 (UI) disponibles

## Structure du projet

```
atelier-temporal/
├── docker/
│   └── docker-compose.yml      # Temporal + PostgreSQL + UI
├── workflows/
│   ├── 01_hello_temporal.py    # Premier workflow : structure de base
│   ├── 02_retry_compensation.py # Retry + Pattern Saga
│   ├── 03_signals_queries.py   # Human-in-the-loop : Signal + Query
│   ├── 04_parallel_activities.py # Parallélisme + Child Workflows
│   └── 05_etl_cron_pipeline.py  # Pipeline ETL avec Cron + Heartbeat
├── docs/
│   ├── 00_installation.md
│   ├── 01_interface.md
│   ├── 02_concepts_cles.md
│   ├── 03_guide_patterns.md
│   └── 04_depannage.md
└── README.md
```

## Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/opinaka-attik/atelier-temporal.git
cd atelier-temporal

# 2. Lancer la stack (Temporal + PostgreSQL + UI)
cd docker
docker compose up -d

# 3. Accéder à l'interface
# http://localhost:8080

# 4. Installer le SDK Python
pip install temporalio

# 5. Lancer le premier workflow
python workflows/01_hello_temporal.py worker  # terminal 1
python workflows/01_hello_temporal.py client  # terminal 2
```

## Workflows inclus

| # | Workflow | Pattern | Niveau |
|---|----------|---------|--------|
| 01 | Hello Temporal | Séquentiel | Débutant |
| 02 | Retry & Compensation | Saga | Débutant+ |
| 03 | Signals & Queries | Human-in-loop | Intermédiaire |
| 04 | Activities Parallèles | Fan-out/Fan-in + Child WF | Intermédiaire+ |
| 05 | Pipeline ETL Cron | Cron + Heartbeat + ETL | Avancé |

## Documentation

| Fichier | Contenu |
|---------|----------|
| [00_installation.md](docs/00_installation.md) | Installation, démarrage, test |
| [01_interface.md](docs/01_interface.md) | Navigation dans Temporal UI |
| [02_concepts_cles.md](docs/02_concepts_cles.md) | Workflow, Activity, Signal, Query, RetryPolicy |
| [03_guide_patterns.md](docs/03_guide_patterns.md) | 7 patterns essentiels avec code |
| [04_depannage.md](docs/04_depannage.md) | Résolution des erreurs courantes |

## Concepts clés

- **Workflow** : orchestrateur durable et déterministe (pas d'I/O direct)
- **Activity** : tâche unitaire avec effets de bord (appel API, BDD, email)
- **Worker** : process qui exécute les workflows et activities
- **Task Queue** : canal entre client et worker
- **Signal** : message envoyé à un workflow en cours
- **Query** : lecture de l'état sans modification
- **Heartbeat** : signal de vie pour les longues activities
- **Event History** : journal immuable = source de durabilité

## Technologies

- Temporal 1.24.2 (auto-setup)
- Temporal UI 2.28.0
- PostgreSQL 13 (backend Temporal)
- Python SDK : `temporalio`
- Docker Compose

## Auteur

opinaka-attik — Atelier pédagogique open-source
