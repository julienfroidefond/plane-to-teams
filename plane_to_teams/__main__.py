"""Script principal pour lancer le service de synchronisation."""
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

from plane_to_teams.config import Config
from plane_to_teams.plane_client import PlaneClient
from plane_to_teams.teams_client import TeamsClient
from plane_to_teams.sync_service import SyncService

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arrêter proprement le service."""
    logger.info(f"Signal reçu: {signum}")
    sys.exit(0)

async def main():
    """Point d'entrée principal."""
    try:
        # Charger la configuration
        config = Config.from_env()
        error = config.validate()
        if error:
            logger.error(f"Erreur de configuration: {error}")
            sys.exit(1)
        
        # Créer les clients
        plane_client = PlaneClient(config)
        teams_client = TeamsClient(config.teams_webhook_url)
        
        # Créer et démarrer le service
        state_file = os.getenv('STATE_FILE', '.state.json')
        notification_hour = int(os.getenv('NOTIFICATION_HOUR', '8'))
        max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        service = SyncService(
            plane_client=plane_client,
            teams_client=teams_client,
            state_file=state_file,
            notification_hour=notification_hour,
            max_retries=max_retries
        )
        
        # Configurer les gestionnaires de signaux
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Démarrer le service
        logger.info("Démarrage du service...")
        service.start()
        
        # Maintenir le processus en vie
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du service: {e}")
        sys.exit(1)
    finally:
        if 'service' in locals():
            service.stop()

if __name__ == "__main__":
    asyncio.run(main()) 