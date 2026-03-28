"""
Workflow 01 - Hello Temporal
Niveau : Debutant
Objectif : Premier workflow Temporal - comprendre la structure de base
"""

import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker


# --- ACTIVITY ---
# Une activity est une tache unitaire (appel API, BDD, email...)
@activity.defn
async def say_hello(name: str) -> str:
    """Activity simple : retourne un message de bienvenue."""
    print(f"[Activity] Traitement de la salutation pour : {name}")
    return f"Bonjour {name} ! Bienvenue dans Temporal."


# --- WORKFLOW ---
# Un workflow orchestre les activities avec retry, timeout, durabilite
@workflow.defn
class HelloWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        """Workflow principal : appelle l'activity say_hello."""
        result = await workflow.execute_activity(
            say_hello,
            name,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return result


# --- WORKER ---
async def run_worker():
    """Lance le worker qui ecoute la task queue."""
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="hello-task-queue",
        workflows=[HelloWorkflow],
        activities=[say_hello],
    ):
        print("[Worker] En attente de workflows...")
        await asyncio.Future()  # attend indefiniment


# --- CLIENT (demarrage du workflow) ---
async def run_client():
    """Client qui soumet un workflow a Temporal."""
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        HelloWorkflow.run,
        "Monde",
        id="hello-workflow-001",
        task_queue="hello-task-queue",
    )
    print(f"[Client] Resultat : {result}")


if __name__ == "__main__":
    # Pour lancer le worker : python 01_hello_temporal.py worker
    # Pour lancer le client : python 01_hello_temporal.py client
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        asyncio.run(run_worker())
    else:
        asyncio.run(run_client())
