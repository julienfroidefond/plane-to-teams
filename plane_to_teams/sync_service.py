"""
Service de synchronisation entre Plane et Teams.
Gère l'envoi quotidien des notifications à 8h.
"""
import asyncio
import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from plane_to_teams.plane_client import PlaneClient, PlaneIssue
from plane_to_teams.teams_client import TeamsClient
from plane_to_teams.teams_formatter import format_issues

logger = logging.getLogger(__name__)

class SyncService:
    """Service de synchronisation entre Plane et Teams."""
    
    def __init__(
        self,
        plane_client: PlaneClient,
        teams_client: TeamsClient,
        state_file: str = ".state.json",
        notification_hour: int = 8,
        max_retries: int = 3
    ):
        """Initialize the sync service.
        
        Args:
            plane_client: Client pour l'API Plane
            teams_client: Client pour l'API Teams
            state_file: Chemin vers le fichier de state
            notification_hour: Heure d'envoi de la notification (default: 8)
            max_retries: Nombre maximum de tentatives en cas d'erreur
        """
        self.plane_client = plane_client
        self.teams_client = teams_client
        self.state_file = Path(state_file)
        self.notification_hour = time(notification_hour)
        self.max_retries = max_retries
        self.scheduler = AsyncIOScheduler()
        
        # Charger ou créer le state
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Charge le state depuis le fichier ou crée un nouveau state.
        
        Returns:
            Dict: Le state chargé ou un nouveau state
        """
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur lors du chargement du state: {e}")
        
        # State par défaut
        return {
            "last_sync": None,
            "last_sync_status": "success",
            "last_issues": [],
            "error_count": 0,
            "last_error": None
        }
    
    def _save_state(self):
        """Sauvegarde le state dans le fichier."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du state: {e}")
    
    def _should_sync(self) -> bool:
        """Vérifie si une synchronisation doit être effectuée.
        
        Returns:
            bool: True si une sync est nécessaire
        """
        now = datetime.now()
        
        # Si pas de dernier sync, on doit synchro
        if not self.state["last_sync"]:
            return True
            
        # Convertir last_sync en datetime
        last_sync = datetime.fromisoformat(self.state["last_sync"])
        
        # Si on est un jour différent et qu'il est après l'heure de notification
        if last_sync.date() < now.date() and now.time() >= self.notification_hour:
            return True
            
        # Si on est le même jour, avant l'heure de notification, et que le dernier sync était avant l'heure de notification
        if (last_sync.date() == now.date() and 
            now.time() >= self.notification_hour and 
            last_sync.time() < self.notification_hour):
            return True
            
        return False
    
    def _update_state(self, success: bool, error: Optional[str] = None, issues: Optional[List[PlaneIssue]] = None):
        """Met à jour le state après une tentative de sync.
        
        Args:
            success: Si la sync a réussi
            error: Message d'erreur éventuel
            issues: Liste des issues synchronisées
        """
        self.state["last_sync"] = datetime.now().isoformat()
        self.state["last_sync_status"] = "success" if success else "error"
        
        if success:
            self.state["error_count"] = 0
            self.state["last_error"] = None
            if issues:
                self.state["last_issues"] = [issue.id for issue in issues]
        else:
            # N'incrémenter le compteur que si on n'a pas atteint le max
            if self.state["error_count"] < self.max_retries:
                self.state["error_count"] += 1
            self.state["last_error"] = error
            
        self._save_state()
    
    async def sync(self, force: bool = False):
        """Synchronise les issues de Plane vers Teams."""
        try:
            logging.info("Début de la synchronisation")

            # Récupération des states
            states = await self.plane_client.get_states()
            logging.info("Récupération des states terminée")

            # Si pas d'états, on arrête là
            if not states:
                logging.info("Pas d'états à synchroniser")
                return

            # Récupération des issues
            issues = await self.plane_client.get_issues()
            logging.info("Récupération des issues terminée")
            
            # Formater le message
            message = format_issues(issues, states)
            logging.info("Formatage du message terminé")
            
            # Envoyer à Teams
            await self.teams_client.send_message(message)
            logging.info("Envoi du message Teams terminé")
            
            # Mettre à jour le state
            self._update_state(True, issues=issues)
            
            logging.info("Synchronisation terminée avec succès")
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Erreur lors de la synchronisation: {error_msg}")
            self._update_state(False, error=error_msg)
        finally:
            # Fermer la session du client Plane
            await self.plane_client.close()
    
    def start(self):
        """Démarre le service de synchronisation."""
        # Ajouter le job de sync quotidien
        self.scheduler.add_job(
            self.sync,
            CronTrigger(hour=self.notification_hour.hour, minute=0),
            id='daily_sync'
        )
        
        # Si on démarre après l'heure de notif et qu'on n'a pas encore sync aujourd'hui
        if self._should_sync():
            logging.info("Démarrage après l'heure de notification, tentative de sync immédiate")
            self.scheduler.add_job(self.sync, 'date')
        
        self.scheduler.start()
        logging.info("Service de synchronisation démarré")
    
    def stop(self):
        """Arrête le service de synchronisation."""
        self.scheduler.shutdown()
        logging.info("Service de synchronisation arrêté") 