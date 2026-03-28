# 02 - Concepts Clés de Temporal

## Architecture globale

```
[Client] --soumet--> [Temporal Server] <--poll-- [Worker]
                          |
                    [PostgreSQL]
                  (Event History)
```

## 1. Workflow

Un **Workflow** est une fonction qui orchestre des Activities. Il est :
- **Durable** : survit aux redemarrages du serveur et du worker
- **Déterministe** : pour le replay, pas d'I/O direct, pas de `datetime.now()`
- **Long-running** : peut durer des secondes... ou des années

```python
@workflow.defn
class MonWorkflow:
    @workflow.run
    async def run(self, input: str) -> str:
        # Orchestration uniquement - pas d'I/O direct
        result = await workflow.execute_activity(ma_function, input, ...)
        return result
```

**Règles d'or :**
- Ne pas utiliser `time.sleep()` -> utiliser `await asyncio.sleep()` ou `workflow.sleep()`
- Ne pas appeler des APIs directement -> déléguer aux Activities
- Utiliser `workflow.now()` et non `datetime.now()`

## 2. Activity

Une **Activity** est une tâche unitaire avec effets de bord (I/O, BDD, API...).
- Peut être réessayée automatiquement
- Supporte le **Heartbeat** pour les longues opérations
- Isolée du Workflow (pas de ré-exécution lors du replay)

```python
@activity.defn
async def ma_function(data: str) -> str:
    activity.heartbeat("En cours...")
    result = requests.get(f"https://api.example.com/{data}")
    return result.json()
```

## 3. Worker

Le **Worker** exécute les Workflows et Activities. Il :
- Poll une Task Queue spécifique
- Rejoue l'Event History pour restituer l'état du workflow
- Est stateless (l'état est dans Temporal)

```python
async with Worker(client, task_queue="ma-queue",
                  workflows=[MonWorkflow], activities=[ma_function]):
    await asyncio.Future()
```

## 4. Task Queue

Une **Task Queue** est un canal de communication entre clients et workers.
- Un workflow et son worker doivent partager la même task queue
- Permet la scalabilité (plusieurs workers sur la même queue)
- Permet l'isolation (dev vs prod)

## 5. Signal

Un **Signal** envoie un message à un workflow en cours d'exécution.
- Unidirectionnel (pas de réponse)
- Utilisé pour les décisions humaines, événements externes

```python
@workflow.signal
async def mon_signal(self, valeur: str) -> None:
    self._etat = valeur
```

## 6. Query

Une **Query** lit l'état d'un workflow sans le modifier.
- Synchrone (retourne immédiatement)
- Ne peut pas modifier l'état

```python
@workflow.query
def get_statut(self) -> str:
    return self._statut
```

## 7. Retry Policy

Contrôle les tentatives de retry automatique :

```python
RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,       # 1s, 2s, 4s, 8s...
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=10,
    non_retryable_error_types=["BusinessError"],
)
```

## 8. Durabilité vs Camunda

| Aspect | Camunda (Zeebe) | Temporal |
|--------|-----------------|----------|
| Persistance | BPMN XML + state en BDD | Event Sourcing (append-only log) |
| Replay | Non (reprise depuis checkpoint) | Oui (déterministe, complet) |
| Définition | BPMN graphique | Code (Python, Go, Java, TS) |
| Long-running | Oui | Oui |
| Human Task | User Task natif | Signal + wait_condition |
| Versioning | Process version | Workflow.patched() |
