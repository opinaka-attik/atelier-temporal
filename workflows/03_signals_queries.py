"""
Workflow 03 - Signals et Queries
Niveau : Intermediaire
Objectif : Interagir avec un workflow en cours d'execution (approbation humaine)
"""

import asyncio
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class DemandeConge:
    employe: str
    jours: int
    motif: str


# --- ACTIVITIES ---
@activity.defn
async def notifier_manager(employe: str, jours: int) -> None:
    print(f"[Activity] Notification manager : {employe} demande {jours} jours")

@activity.defn
async def envoyer_reponse(employe: str, approuve: bool, commentaire: str) -> None:
    statut = "APPROUVE" if approuve else "REFUSE"
    print(f"[Activity] Reponse a {employe} : {statut} - {commentaire}")

@activity.defn
async def mettre_a_jour_rh(employe: str, jours: int, approuve: bool) -> str:
    if approuve:
        print(f"[Activity] RH : Conge de {jours}j enregistre pour {employe}")
        return "enregistre"
    return "refuse"


# --- WORKFLOW ---
@workflow.defn
class ApprouverCongeWorkflow:
    def __init__(self):
        self._decision: Optional[tuple[bool, str]] = None  # (approuve, commentaire)
        self._statut = "en_attente"

    # SIGNAL : recu depuis l'exterieur pour faire avancer le workflow
    @workflow.signal
    async def soumettre_decision(self, approuve: bool, commentaire: str) -> None:
        """Signal envoye par le manager pour approuver/refuser."""
        self._decision = (approuve, commentaire)
        self._statut = "approuve" if approuve else "refuse"
        print(f"[Signal] Decision recue : {self._statut} - {commentaire}")

    # QUERY : consulter l'etat du workflow sans le modifier
    @workflow.query
    def get_statut(self) -> str:
        """Query pour consulter l'etat actuel."""
        return self._statut

    @workflow.run
    async def run(self, demande: DemandeConge) -> str:
        # Etape 1 : Notifier le manager
        await workflow.execute_activity(
            notifier_manager,
            args=[demande.employe, demande.jours],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Etape 2 : Attendre la decision du manager (jusqu'a 7 jours !)
        # C'est la magie de Temporal : le workflow survit aux redemarrages
        await workflow.wait_condition(
            lambda: self._decision is not None,
            timeout=timedelta(days=7),
        )

        if self._decision is None:
            # Timeout : refus automatique
            await workflow.execute_activity(
                envoyer_reponse,
                args=[demande.employe, False, "Timeout - aucune reponse du manager"],
                start_to_close_timeout=timedelta(seconds=10),
            )
            return "TIMEOUT - refuse automatiquement"

        approuve, commentaire = self._decision

        # Etape 3 : Envoyer reponse + mettre a jour RH
        await workflow.execute_activity(
            envoyer_reponse,
            args=[demande.employe, approuve, commentaire],
            start_to_close_timeout=timedelta(seconds=10),
        )
        await workflow.execute_activity(
            mettre_a_jour_rh,
            args=[demande.employe, demande.jours, approuve],
            start_to_close_timeout=timedelta(seconds=10),
        )

        return f"Conge {demande.employe} : {'APPROUVE' if approuve else 'REFUSE'}"


async def demo_signal_query():
    """Demo : soumettre un workflow et l'interagir avec signal/query."""
    client = await Client.connect("localhost:7233")

    demande = DemandeConge(employe="Alice", jours=5, motif="Vacances")

    # Lancer le workflow de facon non-bloquante
    handle = await client.start_workflow(
        ApprouverCongeWorkflow.run,
        demande,
        id="conge-alice-001",
        task_queue="signals-task-queue",
    )

    # Interroger l'etat (QUERY)
    statut = await handle.query(ApprouverCongeWorkflow.get_statut)
    print(f"Statut actuel : {statut}")

    # Approuver via SIGNAL
    await handle.signal(ApprouverCongeWorkflow.soumettre_decision, True, "Bon courage !")

    # Attendre le resultat
    result = await handle.result()
    print(f"Resultat final : {result}")


if __name__ == "__main__":
    asyncio.run(demo_signal_query())
