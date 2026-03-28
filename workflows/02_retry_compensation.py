"""
Workflow 02 - Retry et Compensation (Saga Pattern)
Niveau : Debutant-Intermediaire
Objectif : Gerer les echecs avec retry automatique et compensation Saga
"""

import asyncio
import random
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker


# --- ACTIVITIES ---
@activity.defn
async def debit_compte(montant: float, compte_id: str) -> str:
    """Debite un compte - peut echouer aleatoirement."""
    if random.random() < 0.3:  # 30% de chance d'echec
        raise Exception(f"Echec debit compte {compte_id} - service indisponible")
    print(f"[Activity] Debit de {montant}EUR sur compte {compte_id}")
    return f"debit_{compte_id}_ok"


@activity.defn
async def credit_compte(montant: float, compte_id: str) -> str:
    """Credits un compte."""
    print(f"[Activity] Credit de {montant}EUR sur compte {compte_id}")
    return f"credit_{compte_id}_ok"


@activity.defn
async def annuler_debit(montant: float, compte_id: str) -> str:
    """Compensation : annule le debit (Saga rollback)."""
    print(f"[Compensation] Annulation debit {montant}EUR compte {compte_id}")
    return f"annulation_{compte_id}_ok"


@activity.defn
async def notifier_echec(message: str) -> None:
    """Notifie en cas d'echec total."""
    print(f"[Notification] ECHEC VIREMENT : {message}")


# --- WORKFLOW SAGA ---
@workflow.defn
class VirementWorkflow:
    @workflow.run
    async def run(self, montant: float, compte_source: str, compte_dest: str) -> str:
        """Workflow de virement avec pattern Saga."""
        debit_effectue = False

        try:
            # Etape 1 : Debit avec retry automatique (3 tentatives)
            await workflow.execute_activity(
                debit_compte,
                args=[montant, compte_source],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0,
                ),
            )
            debit_effectue = True

            # Etape 2 : Credit (pas de retry - idempotent)
            await workflow.execute_activity(
                credit_compte,
                args=[montant, compte_dest],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )

            return f"Virement {montant}EUR de {compte_source} vers {compte_dest} : SUCCES"

        except Exception as e:
            # Compensation Saga : annuler le debit si credit echoue
            if debit_effectue:
                await workflow.execute_activity(
                    annuler_debit,
                    args=[montant, compte_source],
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(maximum_attempts=10),  # critique
                )
            await workflow.execute_activity(
                notifier_echec,
                str(e),
                start_to_close_timeout=timedelta(seconds=5),
            )
            raise


async def main():
    client = await Client.connect("localhost:7233")
    try:
        result = await client.execute_workflow(
            VirementWorkflow.run,
            args=[100.0, "COMPTE-001", "COMPTE-002"],
            id="virement-workflow-001",
            task_queue="retry-task-queue",
        )
        print(f"Resultat : {result}")
    except Exception as e:
        print(f"Workflow echoue apres compensation : {e}")


if __name__ == "__main__":
    asyncio.run(main())
