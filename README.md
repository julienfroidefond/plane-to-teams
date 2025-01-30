# Plane to Teams Integration

Ce service permet d'envoyer des notifications quotidiennes dans Microsoft Teams contenant les tickets Plane les plus prioritaires. Les tickets sont filtrés par état (En cours, A faire, Backlog) et triés par priorité.

## Prérequis

- Python 3.9+
- Un webhook Microsoft Teams
- Un token d'API Plane
- pip (gestionnaire de paquets Python)

## Installation

1. Cloner le repository :

```bash
git clone <repository-url>
cd plane-toapi
```

2. Créer un environnement virtuel et l'activer :

```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/macOS
# ou
.\venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

1. Copier le fichier d'exemple de configuration :

```bash
cp .env.example .env
```

2. Éditer le fichier `.env` avec vos informations :

```env
# Plane API Configuration
PLANE_API_TOKEN=your_plane_api_token_here
PLANE_BASE_URL=https://plane.example.com/api/v1
PLANE_WORKSPACE=your_workspace_id
PLANE_PROJECT_ID=your_project_id

# Microsoft Teams Configuration
TEAMS_WEBHOOK_URL=your_teams_webhook_url_here

# Service Configuration
NOTIFICATION_HOUR=8  # Heure d'envoi quotidien (format 24h)
MAX_RETRIES=3       # Nombre maximum de tentatives en cas d'erreur
STATE_FILE=.state.json  # Fichier de stockage de l'état

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=plane_to_teams.log
```

## Utilisation

### Démarrer le service

```bash
python -m plane_to_teams
```

Le service va :

- Démarrer un scheduler qui s'exécute tous les jours à l'heure configurée (par défaut 8h)
- Si le service démarre après l'heure configurée et qu'aucune notification n'a été envoyée aujourd'hui, une synchronisation immédiate sera effectuée
- Les états de synchronisation sont stockés dans `.state.json`

### Synchronisation manuelle

Pour forcer une synchronisation sans attendre l'heure planifiée, vous pouvez utiliser le script de synchronisation manuelle :

```bash
python -m plane_to_teams.manual_sync
```

Ce script va :

- Charger la configuration depuis le fichier `.env`
- Initialiser les clients Plane et Teams
- Forcer une synchronisation immédiate, indépendamment de l'heure
- Les résultats seront visibles dans les logs et dans Teams

### État du Service

Le fichier `.state.json` contient :

```json
{
  "last_sync": "2024-01-30T08:00:00+01:00",
  "last_sync_status": "success",
  "last_issues": ["id1", "id2", "..."],
  "error_count": 0,
  "last_error": null
}
```

### Logs

Les logs sont écrits dans la sortie standard et dans le fichier `plane_to_teams.log`. Ils incluent :

- Les démarrages/arrêts du service
- Les tentatives de synchronisation
- Les erreurs éventuelles
- Les états des tickets synchronisés

## Tests

Pour lancer les tests :

```bash
python -m pytest
```

Pour lancer les tests avec la couverture :

```bash
python -m pytest --cov=plane_to_teams
```

## Structure du Projet

```
plane-toapi/
├── plane_to_teams/
│   ├── __init__.py
│   ├── __main__.py          # Point d'entrée du service
│   ├── config.py            # Gestion de la configuration
│   ├── plane_client.py      # Client API Plane
│   ├── teams_client.py      # Client webhook Teams
│   ├── teams_formatter.py   # Formatage des messages Teams
│   └── sync_service.py      # Service de synchronisation
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_plane_client.py
│   ├── test_teams_client.py
│   ├── test_teams_formatter.py
│   └── test_sync_service.py
├── .env.example
├── .gitignore
├── README.md
├── devbook.md
└── requirements.txt
```

## Format des Messages

Les messages envoyés à Teams utilisent des Adaptive Cards et incluent :

- Un titre avec emoji
- La liste des tickets triés par priorité
- Les états en gras
- Des liens cliquables vers les tickets
- Un code couleur par priorité :
  - URGENT = rouge
  - HIGH = orange
  - MEDIUM = vert
  - LOW = bleu

## Gestion des Erreurs

Le service inclut :

- Un système de retry configurable (MAX_RETRIES)
- Un compteur d'erreurs qui se réinitialise après un succès
- Des logs détaillés des erreurs
- Un état persistant entre les redémarrages

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## License

[MIT](LICENSE)
