"""
Plane API client implementation.
"""
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp
from aiohttp import ClientError

from plane_to_teams.config import Config


@dataclass
class PlaneIssue:
    """Represents a Plane issue."""
    id: str
    name: str
    description_html: Optional[str]
    priority: str
    state: str
    created_at: str
    updated_at: str
    estimate_point: Optional[int]
    start_date: Optional[str]
    target_date: Optional[str]
    completed_at: Optional[str]
    sequence_id: int
    project_id: str
    labels: List[str]
    assignees: List[str]

    @classmethod
    def from_api_response(cls, data: Dict) -> 'PlaneIssue':
        """Create a PlaneIssue instance from API response data."""
        logging.debug("Creating PlaneIssue from data: %s", json.dumps(data, indent=2))
        
        # Debug logs for labels and assignees
        logging.debug("Labels data: %s", json.dumps(data.get('labels', []), indent=2))
        logging.debug("Assignees data: %s", json.dumps(data.get('assignees', []), indent=2))
        
        return cls(
            id=data['id'],
            name=data['name'],
            description_html=data.get('description_html'),
            priority=data.get('priority', 'none'),
            state=data['state'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            estimate_point=data.get('estimate_point'),
            start_date=data.get('start_date'),
            target_date=data.get('target_date'),
            completed_at=data.get('completed_at'),
            sequence_id=data['sequence_id'],
            project_id=data['project'],
            labels=data.get('labels', []),
            assignees=data.get('assignees', [])
        )


class PlaneClient:
    """Client for interacting with the Plane API."""

    def __init__(self, config: Config):
        """Initialize the Plane API client."""
        self.config = config
        self.headers = {
            'X-API-Key': config.plane_api_token,
            'Content-Type': 'application/json',
        }
        logging.info("PlaneClient initialized with base URL: %s", config.plane_base_url)

    def _get_issues_url(self) -> str:
        """Get the URL for issues endpoint."""
        url = f"{self.config.plane_base_url}/workspaces/{self.config.plane_workspace}/projects/{self.config.plane_project_id}/issues/"
        logging.debug("Issues URL: %s", url)
        return url

    async def get_issues(self) -> List[PlaneIssue]:
        """
        Fetch all issues from Plane.

        Returns:
            List[PlaneIssue]: List of issues

        Raises:
            ClientError: If the API request fails
        """
        try:
            logging.info("Fetching issues from Plane API...")
            url = self._get_issues_url()
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    
                    if isinstance(response_data, dict):
                        issues_data = response_data.get('results', [])
                    else:
                        issues_data = response_data
                    
                    logging.info("Received %d issues from API", len(issues_data))
                    
                    issues = []
                    for issue_data in issues_data:
                        try:
                            issue = PlaneIssue.from_api_response(issue_data)
                            logging.info("Issue #%d: '%s' (Priority: %s, State: %s)", 
                                       issue.sequence_id, 
                                       issue.name, 
                                       issue.priority,
                                       issue.state)
                            issues.append(issue)
                        except Exception as e:
                            logging.error("Failed to parse issue data: %s", str(e))
                            logging.error("Raw issue data: %s", json.dumps(issue_data, indent=2))
                    
                    return issues
            
        except ClientError as e:
            logging.error("Failed to fetch issues from Plane: %s", str(e))
            raise
        except Exception as e:
            logging.error("Error processing issues data: %s", str(e))
            raise

    async def get_issue(self, issue_id: str) -> Optional[PlaneIssue]:
        """
        Fetch a specific issue from Plane.

        Args:
            issue_id: The ID of the issue to fetch

        Returns:
            Optional[PlaneIssue]: The issue if found, None otherwise

        Raises:
            ClientError: If the API request fails
        """
        try:
            logging.info("Fetching issue %s...", issue_id)
            url = f"{self._get_issues_url()}{issue_id}/"
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 404:
                        logging.warning("Issue %s not found", issue_id)
                        return None
                        
                    response.raise_for_status()
                    issue_data = await response.json()
                    
                    issue = PlaneIssue.from_api_response(issue_data)
                    logging.debug("Successfully fetched issue #%d: '%s'", 
                                issue.sequence_id, 
                                issue.name)
                    return issue
            
        except ClientError as e:
            logging.error("Failed to fetch issue %s: %s", issue_id, str(e))
            raise 