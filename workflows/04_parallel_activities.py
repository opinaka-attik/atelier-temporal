"""
Workflow 04 - Activities Paralleles et Child Workflows
Niveau : Intermediaire-Avance
Objectif : Executer des activities en parallele + orchestrer des sous-workflows
"""

import asyncio
from datetime import timedelta
from dataclasses import dataclass
from typing import List
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class CommandeItem:
    produit: str
    quantite: int
    prix: float


# --- ACTIVITIES ---
@activity.defn
async def verifier_stock(produit: str, quantite: int) -> bool:
    import asyncio
    await asyncio.sleep(0.5)  # Simule appel API stock
    print(f"[Activity] Stock {produit} x{quantite} : disponible")
    return True

@activity.defn
async def calculer_frais_livraison(adresse: str) -> float:
    import asyncio
    await asyncio.sleep(0.3)  # Simule appel API livraison
    print(f"[Activity] Frais livraison pour {adresse} : 5.99 EUR")
    return 5.99

@activity.defn
async def appliquer_reduction(total: float, code_promo: str) -> float:
    import asyncio
    await asyncio.sleep(0.2)  # Simule appel API promos
    reduction = 0.10 if code_promo == "PROMO10" else 0.0
    montant = total * (1 - reduction)
    print(f"[Activity] Reduction {code_promo} : -{reduction*100}% -> {montant:.2f} EUR")
    return montant

@activity.defn
async def traiter_paiement(montant: float, mode: str) -> str:
    print(f"[Activity] Paiement {montant:.2f} EUR via {mode} : OK")
    return f"PAIEMENT-{mode.upper()}-OK"

@activity.defn
async def envoyer_confirmation(email: str, commande_id: str) -> None:
    print(f"[Activity] Email confirmation envoye a {email} pour {commande_id}")


# --- CHILD WORKFLOW : traitement d'un item ---
@workflow.defn
class TraiterItemWorkflow:
    @workflow.run
    async def run(self, item: CommandeItem) -> dict:
        """Child workflow pour traiter un seul item."""
        dispo = await workflow.execute_activity(
            verifier_stock,
            args=[item.produit, item.quantite],
            start_to_close_timeout=timedelta(seconds=15),
        )
        return {"produit": item.produit, "dispo": dispo, "total": item.prix * item.quantite}


# --- WORKFLOW PRINCIPAL ---
@workflow.defn
class CommandeWorkflow:
    @workflow.run
    async def run(self, items: List[CommandeItem], adresse: str,
                  email: str, code_promo: str) -> dict:
        """Workflow commande : parallele + child workflows."""
        commande_id = f"CMD-{workflow.now().strftime('%Y%m%d%H%M%S')}"

        # PHASE 1 : Verifier tous les items EN PARALLELE (child workflows)
        child_handles = []
        for item in items:
            handle = await workflow.start_child_workflow(
                TraiterItemWorkflow.run,
                item,
                id=f"{commande_id}-item-{item.produit}",
                task_queue="parallel-task-queue",
            )
            child_handles.append(handle)

        # Attendre TOUS les child workflows en parallele
        resultats_items = await asyncio.gather(*[h for h in child_handles])
        total_produits = sum(r["total"] for r in resultats_items)

        # PHASE 2 : Calculs en parallele (frais + reduction)
        frais_task = workflow.execute_activity(
            calculer_frais_livraison,
            adresse,
            start_to_close_timeout=timedelta(seconds=10),
        )
        reduction_task = workflow.execute_activity(
            appliquer_reduction,
            args=[total_produits, code_promo],
            start_to_close_timeout=timedelta(seconds=10),
        )

        frais, total_reduit = await asyncio.gather(frais_task, reduction_task)
        total_final = total_reduit + frais

        # PHASE 3 : Paiement (sequentiel - depend du total)
        ref_paiement = await workflow.execute_activity(
            traiter_paiement,
            args=[total_final, "carte"],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # PHASE 4 : Confirmation (fire & forget)
        await workflow.execute_activity(
            envoyer_confirmation,
            args=[email, commande_id],
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "commande_id": commande_id,
            "total_final": total_final,
            "ref_paiement": ref_paiement,
            "items_traites": len(resultats_items),
        }


async def main():
    client = await Client.connect("localhost:7233")
    items = [
        CommandeItem("Laptop", 1, 999.99),
        CommandeItem("Souris", 2, 29.99),
        CommandeItem("Clavier", 1, 79.99),
    ]
    result = await client.execute_workflow(
        CommandeWorkflow.run,
        args=[items, "12 rue de la Paix, Paris", "client@example.com", "PROMO10"],
        id="commande-workflow-001",
        task_queue="parallel-task-queue",
    )
    print(f"Commande terminee : {result}")


if __name__ == "__main__":
    asyncio.run(main())
