# 03 - Guide des Patterns Temporal

## Pattern 1 : Séquentiel (Pipeline)

Exécuter des activities l'une après l'autre :

```python
@workflow.run
async def run(self, data: str) -> str:
    step1 = await workflow.execute_activity(extract, data, ...)
    step2 = await workflow.execute_activity(transform, step1, ...)
    step3 = await workflow.execute_activity(load, step2, ...)
    return step3
```
**Cas d'usage** : ETL, pipeline de traitement, onboarding utilisateur.

---

## Pattern 2 : Parallèle (Fan-out / Fan-in)

Exécuter plusieurs activities simultanément :

```python
@workflow.run
async def run(self, items: list) -> list:
    tasks = [
        workflow.execute_activity(traiter_item, item, ...)
        for item in items
    ]
    resultats = await asyncio.gather(*tasks)
    return resultats
```
**Cas d'usage** : Vérifications parallèles, enrichissement multi-sources.

---

## Pattern 3 : Saga (Compensation)

Annuler des actions déjà effectuées en cas d'échec :

```python
effectue = []
try:
    await workflow.execute_activity(etape_1, ...)
    effectue.append("etape_1")
    await workflow.execute_activity(etape_2, ...)
    effectue.append("etape_2")
except Exception:
    for etape in reversed(effectue):
        await workflow.execute_activity(f"annuler_{etape}", ...)
    raise
```
**Cas d'usage** : Transactions distribuées, réservation de ressources.

---

## Pattern 4 : Human-in-the-Loop

Attendre une décision humaine (peut durer des jours) :

```python
@workflow.signal
async def approuver(self, decision: bool) -> None:
    self._decision = decision

@workflow.run
async def run(self, demande: str) -> str:
    await workflow.execute_activity(notifier_approbateur, demande, ...)
    await workflow.wait_condition(
        lambda: self._decision is not None,
        timeout=timedelta(days=7)
    )
    return "approuve" if self._decision else "refuse"
```
**Cas d'usage** : Approbation de factures, validation KYC, contrôle qualité.

---

## Pattern 5 : Cron / Workflow Recurrent

Relancer automatiquement un workflow à intervalles réguliers :

```python
await client.start_workflow(
    MonWorkflow.run,
    args=[config],
    id="mon-workflow-cron",
    task_queue="ma-queue",
    cron_schedule="0 */6 * * *",  # Toutes les 6h
)
```
**Cas d'usage** : Rapports périodiques, synchronisations, ETL nocturnales.

---

## Pattern 6 : Child Workflow

Orchestrer des sous-workflows indépendants :

```python
handles = []
for item in items:
    h = await workflow.start_child_workflow(
        SousWorkflow.run, item,
        id=f"sous-{item.id}",
        task_queue="ma-queue"
    )
    handles.append(h)
resultats = await asyncio.gather(*handles)
```
**Cas d'usage** : Traitement par lot, isloation des erreurs, workflows modulaires.

---

## Pattern 7 : Versioning (Migration)

Mettre à jour un workflow sans casser les exécutions en cours :

```python
@workflow.run
async def run(self, data: str) -> str:
    if workflow.patched("nouvelle-logique-v2"):
        # Nouveau code pour les nouvelles instances
        result = await workflow.execute_activity(nouvelle_activity, ...)
    else:
        # Ancien code pour les instances en cours
        result = await workflow.execute_activity(ancienne_activity, ...)
    return result
```
**Cas d'usage** : Déploiements continus, migrations progressives.

---

## Résumé des patterns

| Pattern | Workflow | Cas d'usage |
|---------|----------|-------------|
| Séquentiel | 01, 05 | ETL, pipelines |
| Parallèle | 04 | Enrichissement, checks |
| Saga | 02 | Transactions distribuées |
| Human-in-Loop | 03 | Approbations |
| Cron | 05 | Tâches récurrentes |
| Child Workflow | 04 | Traitement par lot |
| Versioning | - | Migration progressive |
