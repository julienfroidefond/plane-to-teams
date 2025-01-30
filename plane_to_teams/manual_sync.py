"""
Script pour exécuter manuellement la synchronisation entre Plane et Teams.
"""
import asyncio
import logging
from datetime import datetime

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging
from plane_to_teams.plane_client import PlaneClient
from plane_to_teams.teams_client import TeamsClient
from plane_to_teams.sync_service import SyncService

async def main():
    """Point d'entrée du script."""
    # Charger la configuration
    config = Config.from_env()
    
    # Valider la configuration
    error = config.validate()
    if error:
        print(f"Erreur de configuration: {error}")
        return
    
    # Configurer le logging
    logger = setup_logging(config)
    
    # Initialiser les clients
    plane_client = PlaneClient(config)
    teams_client = TeamsClient(config.teams_webhook_url)
    
    # Créer le service de synchronisation
    sync_service = SyncService(
        plane_client=plane_client,
        teams_client=teams_client,
        notification_hour=config.notification_hour,
        max_retries=config.max_retries
    )
    
    # Forcer la synchronisation
    logger.info("Démarrage de la synchronisation manuelle")
    await sync_service.sync(force=True)
    logger.info("Synchronisation terminée")

if __name__ == "__main__":
    asyncio.run(main()) 
