"""
Microsoft Teams webhook client for sending messages.
"""
import json
import logging
from typing import Dict, Optional

import aiohttp
from aiohttp import ClientError

from plane_to_teams.teams_formatter import TeamsMessage

logger = logging.getLogger(__name__)

class TeamsClient:
    """Client for sending messages to Microsoft Teams via webhook."""

    def __init__(self, webhook_url: str, timeout: int = 10):
        """Initialize Teams client.
        
        Args:
            webhook_url: The webhook URL for the Teams channel
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def send_message(self, message: TeamsMessage) -> bool:
        """Send a message to Teams.
        
        Args:
            message: The TeamsMessage to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
            
        Raises:
            ClientError: If there is an error sending the message
        """
        try:
            logger.info("Sending message to Teams")
            logger.debug("Message content: %s", message.to_dict())
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.webhook_url, json=message.to_dict()) as response:
                    response.raise_for_status()
                    
                    logger.info("Successfully sent message to Teams")
                    return True
            
        except ClientError as e:
            logger.error("Failed to send message to Teams: %s", str(e))
            raise 