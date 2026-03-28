"""
Workflow 05 - Pipeline ETL avec Cron et Heartbeat
Niveau : Avance
Objectif : Pipeline ETL recurrent, traitement par batch, heartbeat pour longues taches
Comparaison Camunda : equivalent au Timer Start Event + Service Tasks en BPMN
"""

import asyncio
from datetime import timedelta
from dataclasses import dataclass, field
from typing import List, Optional
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy


@dataclass
class ETLConfig:
    source: str
    destination: str
    batch_size: int = 1000
    filtre: Optional[str] = None


@dataclass
class ETLResult:
    lignes_extraites: int
    lignes_transformees: int
    lignes_chargees: int
    erreurs: int
    duree_secondes: float


# --- ACTIVITIES ETL ---
@activity.defn
async def extraire_donnees(config: ETLConfig) -> List[dict]:
    """Extract : lit les donnees depuis la source par batch."""
    # Heartbeat pour les longues operations (evite timeout)
    activity.heartbeat(f"Extraction depuis {config.source}...")

    # Simule extraction depuis une API/BDD
    donnees = []
    for i in range(config.batch_size):
        donnees.append({
            "id": i,
            "valeur": f"data_{i}",
            "source": config.source,
            "actif": i % 10 != 0  # 10% inactifs
        })
        # Heartbeat regulier pour les gros volumes
        if i % 100 == 0:
            activity.heartbeat(f"Extraction : {i}/{config.batch_size} lignes")

    print(f"[Extract] {len(donnees)} lignes extraites de {config.source}")
    return donnees


@activity.defn
async def transformer_donnees(donnees: List[dict], filtre: Optional[str]) -> List[dict]:
    """Transform : nettoie, filtre et enrichit les donnees."""
    activity.heartbeat("Transformation en cours...")

    transformees = []
    for d in donnees:
        # Filtre
        if not d.get("actif", True):
            continue
        # Transformation
        transformee = {
            "id": d["id"],
            "valeur_upper": d["valeur"].upper(),
            "source": d["source"],
            "traite": True,
        }
        if filtre and filtre not in d["valeur"]:
            continue
        transformees.append(transformee)
        if len(transformees) % 100 == 0:
            activity.heartbeat(f"Transformation : {len(transformees)} lignes")

    print(f"[Transform] {len(transformees)} lignes apres transformation")
    return transformees


@activity.defn
async def charger_donnees(donnees: List[dict], destination: str) -> int:
    """Load : charge les donnees dans la destination."""
    activity.heartbeat(f"Chargement vers {destination}...")

    # Simule insertion en BDD par mini-batchs
    total_charge = 0
    mini_batch_size = 100
    for i in range(0, len(donnees), mini_batch_size):
        mini_batch = donnees[i:i + mini_batch_size]
        total_charge += len(mini_batch)
        activity.heartbeat(f"Charge : {total_charge}/{len(donnees)}")

    print(f"[Load] {total_charge} lignes chargees dans {destination}")
    return total_charge


@activity.defn
async def envoyer_rapport(resultat: ETLResult, destinataires: List[str]) -> None:
    """Envoie un rapport de synthese."""
    taux_erreur = resultat.erreurs / max(resultat.lignes_extraites, 1) * 100
    print(f"[Rapport] ETL termine en {resultat.duree_secondes:.1f}s")
    print(f"  Extrait: {resultat.lignes_extraites}")
    print(f"  Transforme: {resultat.lignes_transformees}")
    print(f"  Charge: {resultat.lignes_chargees}")
    print(f"  Taux erreur: {taux_erreur:.1f}%")
    print(f"  Rapport envoye a : {', '.join(destinataires)}")


# --- WORKFLOW ETL CRON ---
@workflow.defn
class ETLCronWorkflow:
    @workflow.run
    async def run(self, config: ETLConfig, destinataires: List[str]) -> ETLResult:
        """
        Workflow ETL complet avec mesure de duree.
        Quand planifie avec cron_schedule, il se re-execute automatiquement.
        """
        debut = workflow.now()
        erreurs = 0

        # EXTRACT
        donnees_brutes = await workflow.execute_activity(
            extraire_donnees,
            config,
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30),  # Detecte si l'activity freeze
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # TRANSFORM
        try:
            donnees_transformees = await workflow.execute_activity(
                transformer_donnees,
                args=[donnees_brutes, config.filtre],
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        except Exception as e:
            workflow.logger.error(f"Erreur transformation : {e}")
            donnees_transformees = []
            erreurs += len(donnees_brutes)

        # LOAD
        lignes_chargees = await workflow.execute_activity(
            charger_donnees,
            args=[donnees_transformees, config.destination],
            start_to_close_timeout=timedelta(minutes=15),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )

        fin = workflow.now()
        duree = (fin - debut).total_seconds()

        resultat = ETLResult(
            lignes_extraites=len(donnees_brutes),
            lignes_transformees=len(donnees_transformees),
            lignes_chargees=lignes_chargees,
            erreurs=erreurs,
            duree_secondes=duree,
        )

        # Rapport final
        await workflow.execute_activity(
            envoyer_rapport,
            args=[resultat, destinataires],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return resultat


async def planifier_etl_cron():
    """Planifie le workflow ETL pour s'executer chaque nuit a minuit."""
    client = await Client.connect("localhost:7233")

    config = ETLConfig(
        source="postgresql://prod-db/commandes",
        destination="postgresql://dw/faits_commandes",
        batch_size=5000,
        filtre=None,
    )

    # Le cron_schedule relance automatiquement le workflow - comme Camunda Timer
    handle = await client.start_workflow(
        ETLCronWorkflow.run,
        args=[config, ["data-team@company.com", "ops@company.com"]],
        id="etl-nightly-pipeline",
        task_queue="etl-task-queue",
        cron_schedule="0 0 * * *",  # Chaque nuit a minuit
    )

    print(f"ETL Cron planifie. ID: {handle.id}")
    print("Consultez http://localhost:8080 pour suivre les executions")


if __name__ == "__main__":
    asyncio.run(planifier_etl_cron())
