# 01 - Découverte de l'Interface Temporal

## Accès

URL : **http://localhost:8080**

## Vue principale : Namespaces

Temporal organise tout en **Namespaces** (isolation logique, comme des tenants).
Par défaut, le namespace `default` est utilisé pour tous les exemples.

## Section Workflows

### Liste des workflows

Affiche tous les workflows exécutés avec leur statut :

| Statut | Signification |
|--------|---------------|
| **Running** | En cours d'exécution |
| **Completed** | Terminé avec succès |
| **Failed** | Échoué (tous les retries épuisés) |
| **TimedOut** | Dépassement du timeout global |
| **Terminated** | Arrêté manuellement |
| **Canceled** | Annulé proprement |

### Détail d'un workflow

Cliquer sur un workflow pour voir :

- **Summary** : ID, type, statut, durée, Task Queue
- **Event History** : chaque étape du workflow (durable replay log)
- **Stack Trace** : état courant du workflow (debug en temps réel)
- **Queries** : exécuter des queries directement depuis l'UI
- **Signal** : envoyer un signal depuis l'UI

## Event History - Le cœur de Temporal

L'**Event History** est le journal immuable de chaque action :

```
WorkflowExecutionStarted
  ActivityTaskScheduled (say_hello)
  ActivityTaskStarted
  ActivityTaskCompleted -> "Bonjour Monde !"
WorkflowExecutionCompleted
```

C'est ce log qui permet la **durabilité** : si le serveur redémarre, le workflow
repart exactement où il en était en rejouant l'history.

## Section Workers

Affiche les workers actifs connectés par Task Queue :
- Quels workflows ils peuvent exécuter
- Quelles activities ils supportent
- Leur statut de santé

## Section Schedules

Gestion des workflows planifiés (cron) :
- Voir les prochaines exécutions
- Mettre en pause / reprendre
- Modifier le cron schedule

## Section Task Queues

Les **Task Queues** sont des files logiques qui connectent :
`Client (soumet) -> Task Queue -> Worker (consomme)`

Chaque workflow et activity est assigné à une task queue spécifique.

## Comparaison avec Camunda

| Camunda | Temporal |
|---------|----------|
| Cockpit | Temporal UI |
| Process Instance | Workflow Execution |
| Token Flow | Event History |
| Job / Service Task | Activity |
| Timer | cron_schedule ou wait_condition |
| Signal Event | Signal |
| User Task | Signal + wait_condition |
| Incident | Failed + retry |
| Tenant | Namespace |
