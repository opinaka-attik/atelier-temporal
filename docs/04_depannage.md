# 04 - Dépannage Temporal

## Problèmes courants

### 1. Worker ne se connecte pas au serveur

**Erreur :**
```
grpc._channel._InactiveRpcError: StatusCode.UNAVAILABLE
failed to connect to all addresses
```

**Solutions :**
```bash
# Vérifier que Temporal tourne
docker compose ps
docker compose logs temporal

# Vérifier le port
nc -zv localhost 7233

# Attendre que PostgreSQL soit prêt (temporal démarre après)
docker compose logs postgres | tail -5
```

---

### 2. Workflow en statut "Failed"

**Dans l'UI :** Cliquer sur le workflow -> Event History -> chercher `ActivityTaskFailed`

**Causes fréquentes :**
- Activity lève une exception non gérée
- Timeout `start_to_close_timeout` dépassé
- Maximum retries épuisés

**Solutions :**
```python
# Augmenter le timeout
start_to_close_timeout=timedelta(minutes=5)  # au lieu de secondes

# Augmenter les retries
retry_policy=RetryPolicy(maximum_attempts=10)

# Exclure des erreurs du retry
retry_policy=RetryPolicy(
    non_retryable_error_types=["ValidationError", "BusinessError"]
)
```

---

### 3. Erreur de Déterminisme (NonDeterministicError)

**Erreur :**
```
temporalio.exceptions.NonDeterministicError:
history mismatch on replay
```

**Cause :** Le code du workflow a été modifié pendant qu'une instance est en cours.

**Solutions :**
```python
# 1. Utiliser workflow.patched() pour la migration
if workflow.patched("ma-nouvelle-feature"):
    # Nouveau code
else:
    # Ancien code

# 2. Terminer toutes les instances en cours avant de déployer
# Dans l'UI : terminer les workflows Running

# 3. Utiliser des IDs de workflow versioones
id="mon-workflow-v2-001"
```

---

### 4. Activity en timeout (HeartbeatTimeout)

**Erreur :**
```
ActivityTaskTimedOutError: heartbeat timeout
```

**Cause :** L'activity ne fait pas de heartbeat assez fréquemment.

**Solution :**
```python
@activity.defn
async def longue_operation(data: list) -> str:
    for i, item in enumerate(data):
        traiter(item)
        if i % 100 == 0:
            activity.heartbeat(f"Progres : {i}/{len(data)}")  # Obligatoire !

# Et configurer le heartbeat_timeout
await workflow.execute_activity(
    longue_operation, data,
    start_to_close_timeout=timedelta(hours=2),
    heartbeat_timeout=timedelta(seconds=30),  # <= doit matcher la freq heartbeat
)
```

---

### 5. Workflow Duplicate ID

**Erreur :**
```
WorkflowAlreadyStartedError: workflow already started
```

**Solutions :**
```python
# Option 1 : ID unique (timestamp, UUID)
import uuid
id=f"mon-workflow-{uuid.uuid4()}"

# Option 2 : Politique de conflit
from temporalio.client import WorkflowIDReusePolicy
await client.start_workflow(
    ...,
    id="mon-workflow-fixe",
    id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
)
```

---

### 6. Le Worker ne trouve pas les Workflows/Activities

**Erreur dans l'UI :** `Workflow type not found: MonWorkflow`

**Solutions :**
```python
# Vérifier que le worker enregistre bien les workflows et activities
async with Worker(
    client,
    task_queue="ma-queue",
    workflows=[MonWorkflow, AutreWorkflow],   # <- liste complète
    activities=[activity1, activity2],         # <- liste complète
):
    ...

# Vérifier que la task_queue correspond
# Client : task_queue="ma-queue"
# Worker : task_queue="ma-queue"  <- doit être identique !
```

---

## Commandes de diagnostic utiles

```bash
# Voir les logs du serveur Temporal
docker compose logs temporal -f

# Voir les logs du worker
docker compose logs temporal-worker -f

# Lister les workflows depuis la CLI (optionnel)
docker exec temporal tctl workflow list

# Réinitialiser complètement (tout effacer)
docker compose down -v && docker compose up -d
```

## FAQ

**Q : Puis-je utiliser `requests` dans un Workflow ?**
Non, uniquement dans les Activities. Le Workflow doit être pur.

**Q : Est-ce que Temporal remplace une base de données ?**
Non. Il stocke l'état des workflows (Event History), pas les données métier.

**Q : Différence entre Terminate et Cancel ?**
- `Terminate` : arrêt immédiat, brutal
- `Cancel` : arrêt propre, le workflow peut nettoyer ses ressources

**Q : Temporal est-il compatible avec FastAPI ?**
Oui, le client Temporal est async et s'intègre parfaitement avec FastAPI.
