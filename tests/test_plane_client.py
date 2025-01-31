"""Tests for the Plane API client."""
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError

from plane_to_teams.config import Config
from plane_to_teams.plane_client import PlaneClient, PlaneIssue, PlaneState


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        plane_api_token="test_token",
        plane_base_url="https://test.plane.so/api/v1",
        plane_workspace="test_workspace",
        plane_project_id="test_project",
        teams_webhook_url="https://test.teams.webhook"
    )


@pytest.fixture
def client(config):
    """Create a test client."""
    return PlaneClient(config)


@pytest.fixture
def sample_issue_data():
    """Create sample issue data."""
    return {
        "id": "test_id",
        "name": "Test Issue",
        "description_html": "<p>Test</p>",
        "priority": "urgent",
        "state": "state1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "estimate_point": None,
        "start_date": None,
        "target_date": None,
        "completed_at": None,
        "sequence_id": 1,
        "project": "test_project",
        "labels": [],
        "assignees": []
    }


@pytest.fixture
def sample_state_data():
    """Create sample state data."""
    return {
        "id": "state1",
        "name": "En cours",
        "color": "#ff0000",
        "sequence": 1,
        "group": "started",
        "default": False
    }


@pytest.mark.asyncio
async def test_get_states_success(client, sample_state_data):
    """Test successful states retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": [sample_state_data]})

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        states = await client.get_states()

        assert len(states) == 1
        state = states[0]
        assert isinstance(state, PlaneState)
        assert state.id == sample_state_data["id"]
        assert state.name == sample_state_data["name"]
        assert state.color == sample_state_data["color"]
        assert state.sequence == sample_state_data["sequence"]
        assert state.group == sample_state_data["group"]
        assert state.default == sample_state_data["default"]


@pytest.mark.asyncio
async def test_get_states_failure(client):
    """Test states retrieval failure."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.json = AsyncMock(side_effect=ClientError())

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(ClientError):
            await client.get_states()


@pytest.mark.asyncio
async def test_get_states_not_found(client):
    """Test states not found."""
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not Found")
    mock_response.json = AsyncMock(side_effect=ClientError())

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(ClientError):
            await client.get_states()


@pytest.mark.asyncio
async def test_get_issues_success(client, sample_issue_data):
    """Test successful issues retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": [sample_issue_data]})

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        issues = await client.get_issues()

        assert len(issues) == 1
        issue = issues[0]
        assert isinstance(issue, PlaneIssue)
        assert issue.id == sample_issue_data["id"]
        assert issue.name == sample_issue_data["name"]
        assert issue.priority == sample_issue_data["priority"]
        assert issue.state == sample_issue_data["state"]


@pytest.mark.asyncio
async def test_get_issues_failure(client):
    """Test issues retrieval failure."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.json = AsyncMock(side_effect=ClientError())

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(ClientError):
            await client.get_issues()


@pytest.mark.asyncio
async def test_get_issues_not_found(client):
    """Test issues not found."""
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not Found")
    mock_response.json = AsyncMock(side_effect=ClientError())

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(ClientError):
            await client.get_issues()


@pytest.mark.asyncio
async def test_get_issue_success(client, sample_issue_data):
    """Test successful issue retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=sample_issue_data)

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        issue = await client.get_issue("test_id")

        assert isinstance(issue, PlaneIssue)
        assert issue.id == sample_issue_data["id"]
        assert issue.name == sample_issue_data["name"]
        assert issue.priority == sample_issue_data["priority"]
        assert issue.state == sample_issue_data["state"]


@pytest.mark.asyncio
async def test_get_states_invalid_response(client):
    """Test states retrieval with invalid response format."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"invalid": "format"})

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(ValueError, match="Invalid API response format"):
            await client.get_states()


@pytest.mark.asyncio
async def test_get_states_invalid_state_data(client):
    """Test states retrieval with invalid state data."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": [{"invalid": "state"}]})

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        states = await client.get_states()
        assert len(states) == 0  # Le state invalide est ignoré