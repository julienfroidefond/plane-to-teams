# Plane to Teams Integration Project

## Project Overview

Ce projet crée une intégration entre Plane et Microsoft Teams, permettant d'envoyer des notifications quotidiennes des tickets les plus prioritaires dans un canal Teams.

## Development Steps

### 1. Project Setup [✓]

- [x] Initialize a new Python project
- [x] Create requirements.txt with necessary dependencies
- [x] Setup project structure
- [x] Create configuration management system
- [x] Setup logging

### 2. Plane API Integration [✓]

- [x] Create Plane API client class
- [x] Implement authentication
- [x] Implement issue fetching
- [x] Add error handling
- [x] Add rate limiting
- [x] Add data validation
- [x] Write tests for API integration

### 3. Data Transformation [✓]

- [x] Define data models for Plane issues
- [x] Create mapping between Plane and Teams message format
- [x] Implement data transformation logic
  - [x] Filter issues by state (En cours, A faire, Backlog)
  - [x] Sort by priority (urgent -> high -> medium -> low)
  - [x] Sort by state (En cours -> A faire -> Backlog)
  - [x] Limit to top 10 issues
  - [x] Format with priority colors
  - [x] Add state names in bold
  - [x] Make entire row clickable with issue URL
- [x] Add validation for transformed data
- [x] Write tests for data transformation

### 4. Microsoft Teams Integration [✓]

- [x] Create Teams webhook client
- [x] Implement message sending with Adaptive Cards
- [x] Add error handling and retries
- [x] Add rate limiting
- [x] Write tests for Teams integration

### 5. Synchronization Service [✓]

- [x] Create sync scheduler
  - [x] Utiliser APScheduler pour planifier les envois
  - [x] Configurer le job pour s'exécuter tous les jours à 8h
  - [x] Gérer le cas où le service démarre après 8h
- [x] Implement sync logic
  - [x] Créer une classe SyncService
  - [x] Stocker la date du dernier envoi dans .state.json
  - [x] Vérifier si un envoi a déjà été fait aujourd'hui
  - [x] Récupérer et formater les issues
  - [x] Envoyer la notification Teams
- [x] Add error recovery
  - [x] Gérer les erreurs de connexion à Plane
  - [x] Gérer les erreurs d'envoi Teams
  - [x] Implémenter une logique de retry avec backoff (max_retries)
  - [x] Logger les erreurs pour monitoring
- [x] Add state management
  - [x] Créer un fichier de state (.state.json)
  - [x] Stocker la date du dernier envoi réussi (last_sync)
  - [x] Stocker le statut et les erreurs (last_sync_status, error_count, last_error)
  - [x] Stocker les IDs des derniers tickets envoyés (last_issues)
- [x] Write tests for sync service
  - [x] Tests unitaires pour la logique de synchronisation
  - [x] Tests pour la gestion du state
  - [x] Tests pour la logique de retry
  - [x] Tests avec différentes heures de démarrage

### 6. Monitoring and Logging [✓]

- [x] Add detailed logging
  - [x] Configuration des logs avec rotation
  - [x] Logs au format JSON pour le fichier
  - [x] Logs formatés pour la console
- [x] Implement error tracking
  - [x] Suivi des erreurs dans le state
  - [x] Compteur d'erreurs avec reset
- [x] Add performance metrics
  - [x] Temps de réponse des APIs
  - [x] Nombre de tickets synchronisés
- [x] Create monitoring documentation
  - [x] Format des logs
  - [x] Structure du state
  - [x] Gestion des erreurs

## Technical Stack

- Language: Python 3.9+
- HTTP Client: aiohttp
- Testing: pytest, pytest-asyncio, freezegun
- Configuration: python-dotenv
- Scheduling: APScheduler
- Logging: Python logging, python-json-logger

## Message Format

### Teams Adaptive Card

- Version: 1.2
- Structure:
  - Title container with emoji and text
  - Issues container with columns:
    - Number (#1, #2, etc.)
    - Priority (color-coded: URGENT=red, HIGH=orange, MEDIUM=green, LOW=blue)
    - Issue name with state in bold
  - Each row is clickable and links to the issue in Plane

### Issue States

- En cours (daaf8056-e88d-40ba-b527-d58f3e518059)
- A faire (9ce312cc-0018-4864-9867-064939dda809)
- Backlog (318803e3-f0ce-4dbf-b0b4-beb1cfba9e81)

Only "En cours", "A faire", and "Backlog" states are included in Teams messages.

## Configuration Requirements

- Plane API Token
- Microsoft Teams Webhook URL
- Notification hour (default: 8:00 AM)
- Max retries (default: 3)
- State file location (.state.json)
- Log level and location

## State Management

Le fichier .state.json contient :

```json
{
  "last_sync": "2024-01-30T08:00:00+01:00",
  "last_sync_status": "success",
  "last_issues": ["id1", "id2", "..."],
  "error_count": 0,
  "last_error": null
}
```

## Notes

- Gestion asynchrone des appels API avec aiohttp
- Retry automatique en cas d'erreur avec compteur
- Logs détaillés pour le debugging
- Tests unitaires complets avec mocks
- Support des fuseaux horaires pour les notifications
