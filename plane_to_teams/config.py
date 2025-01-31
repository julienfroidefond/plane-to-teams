"""
Configuration management for the application.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

@dataclass
class Config:
    """Application configuration."""
    plane_api_token: str
    plane_base_url: str
    plane_workspace: str
    plane_project_id: str
    teams_webhook_url: str
    notification_hour: int = field(default=8)
    max_retries: int = field(default=3)
    log_level: str = field(default="INFO")
    log_file: str = field(default="plane_to_teams.log")
    sync_interval: int = field(default=10)

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        load_dotenv()

        return cls(
            plane_api_token=os.getenv('PLANE_API_TOKEN', ''),
            plane_base_url=os.getenv('PLANE_BASE_URL', ''),
            plane_workspace=os.getenv('PLANE_WORKSPACE', ''),
            plane_project_id=os.getenv('PLANE_PROJECT_ID', ''),
            teams_webhook_url=os.getenv('TEAMS_WEBHOOK_URL', ''),
            notification_hour=int(os.getenv('NOTIFICATION_HOUR', '8')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'plane_to_teams.log'),
            sync_interval=int(os.getenv('SYNC_INTERVAL', '10'))
        )

    def validate(self) -> Optional[str]:
        """
        Validate the configuration.
        
        Returns:
            Optional[str]: Error message if validation fails, None otherwise.
        """
        # Check required fields
        required_fields = {
            'PLANE_API_TOKEN': self.plane_api_token,
            'PLANE_BASE_URL': self.plane_base_url,
            'PLANE_WORKSPACE': self.plane_workspace,
            'PLANE_PROJECT_ID': self.plane_project_id,
            'TEAMS_WEBHOOK_URL': self.teams_webhook_url
        }

        for env_var, value in required_fields.items():
            if not value:
                field_name = env_var.replace('_', ' ').title()
                return f"{field_name} is required"

        # Check notification hour
        if not (0 <= self.notification_hour <= 23):
            return "Notification Hour must be between 0 and 23"

        # Check max retries
        if self.max_retries < 1:
            return "Max Retries must be greater than 0"

        # Check sync interval
        if self.sync_interval < 1:
            return "Sync Interval must be greater than 0"

        return None 