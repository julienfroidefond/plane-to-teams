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
class PlaneState:
    """Represents a Plane state."""
    id: str
    name: str
    color: str
    sequence: int
    group: str
    default: bool

    @classmethod
    def from_api_response(cls, data: Dict) -> 'PlaneState':
        """Create a PlaneState instance from API response data.
        
        Args:
            data: Raw state data from the API with the following fields:
                - name (str): Name of the state
                - color (str): String code of the color
                - sequence (int): Auto generated sequence of the state for ordering
                - group (str): Group to which the state belongs (backlog, unstarted, started, completed, cancelled)
                - default (bool): Is it the default state
                - id (str): State ID
        """
        try:
            return cls(
                id=str(data['id']),  # Ensure id is string
                name=str(data['name']),  # Name is required
                color=str(data.get('color', '#000000')),  # Color is required but provide default
                sequence=int(data.get('sequence', 0)),  # Sequence for ordering
                group=str(data.get('group', 'backlog')),  # Group is required but provide default
                default=bool(data.get('default', False))  # Default state flag
            )
        except (KeyError, ValueError, TypeError) as e:
            logging.error(f"Error parsing state data: {e}")
            logging.error(f"Raw state data: {json.dumps(data, indent=2)}")
            raise ValueError(f"Invalid state data: {e}")


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
        self.session = None
        logging.info("PlaneClient initialized with base URL: %s", config.plane_base_url)

    async def _ensure_session(self):
        """Ensure we have an active session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None

    def _get_issues_url(self) -> str:
        """Get the URL for issues endpoint."""
        url = f"{self.config.plane_base_url}/workspaces/{self.config.plane_workspace}/projects/{self.config.plane_project_id}/issues/"
        logging.debug("Issues URL: %s", url)
        return url

    def _get_states_url(self) -> str:
        """Get the URL for states endpoint."""
        url = f"{self.config.plane_base_url}/workspaces/{self.config.plane_workspace}/projects/{self.config.plane_project_id}/states/"
        logging.debug("States URL: %s", url)
        return url

    async def get_states(self) -> List[PlaneState]:
        """
        Fetch all states from Plane.

        Returns:
            List[PlaneState]: List of states

        Raises:
            ClientError: If the API request fails
            ValueError: If the response data is invalid
        """
        try:
            logging.info("Fetching states from Plane API...")
            url = self._get_states_url()
            logging.debug("Using URL: %s", url)
            
            session = await self._ensure_session()
            logging.debug("Session created with headers: %s", self.headers)
            
            async with session.get(url) as response:
                logging.debug("Response status: %s", response.status)
                if response.status >= 400:
                    error_text = await response.text()
                    logging.error("API error: %s - %s", response.status, error_text)
                    response.raise_for_status()
                
                response_data = await response.json()
                logging.debug("Response data: %s", json.dumps(response_data, indent=2))
                
                # L'API retourne un objet avec un champ 'results'
                if not isinstance(response_data, dict) or 'results' not in response_data:
                    logging.error("Invalid API response format. Expected dict with 'results', got: %s", type(response_data))
                    raise ValueError("Invalid API response format")
                
                states_data = response_data['results']
                logging.info("Received %d states from API", len(states_data))
                
                states = []
                for state_data in states_data:
                    try:
                        logging.debug("Processing state data: %s", json.dumps(state_data, indent=2))
                        state = PlaneState.from_api_response(state_data)
                        logging.info("State: '%s' (Group: %s, Sequence: %d)", 
                                   state.name, 
                                   state.group,
                                   state.sequence)
                        states.append(state)
                    except ValueError as e:
                        logging.error("Failed to parse state data: %s", str(e))
                        # Continue avec le prochain état
                        continue
                
                # Trier les états par sequence
                states.sort(key=lambda x: x.sequence)
                logging.debug("Returning %d sorted states", len(states))
                return states
        
        except ClientError as e:
            logging.error("Failed to fetch states from Plane: %s", str(e))
            raise
        except Exception as e:
            logging.error("Error processing states data: %s", str(e))
            logging.error("Traceback:", exc_info=True)
            raise

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
            session = await self._ensure_session()
            
            async with session.get(url) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logging.error("API error: %s - %s", response.status, error_text)
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
            session = await self._ensure_session()
            
            async with session.get(url) as response:
                if response.status == 404:
                    logging.warning("Issue %s not found", issue_id)
                    return None
                
                if response.status >= 400:
                    error_text = await response.text()
                    logging.error("API error: %s - %s", response.status, error_text)
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