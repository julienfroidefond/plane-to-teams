"""Tests for the sync service."""
import json
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import os

import pytest
from freezegun import freeze_time
from aiohttp import ClientError

from plane_to_teams.plane_client import PlaneIssue, PlaneState
from plane_to_teams.sync_service import SyncService

@pytest.fixture
def mock_plane_client():
    """Mock du client Plane."""
    client = AsyncMock()
    client.get_issues = AsyncMock(return_value=[])
    client.get_states = AsyncMock(return_value=[
        PlaneState(
            id="state1",
            name="En cours",
            color="#ff0000",
            sequence=1,
            group="started",
            default=False
        ),
        PlaneState(
            id="state2",
            name="A faire",
            color="#00ff00",
            sequence=2,
            group="unstarted",
            default=False
        ),
        PlaneState(
            id="state3",
            name="Backlog",
            color="#0000ff",
            sequence=3,
            group="backlog",
            default=False
        )
    ])
    client.close = AsyncMock()
    return client

@pytest.fixture
def mock_teams_client():
    """Mock du client Teams."""
    client = AsyncMock()
    client.send_message = AsyncMock()
    return client

@pytest.fixture
def temp_state_file(tmp_path):
    """Crée un fichier de state temporaire."""
    return tmp_path / ".state.json"

@pytest.fixture
def sync_service(mock_plane_client, mock_teams_client, temp_state_file):
    """Crée une instance du service de sync pour les tests."""
    return SyncService(
        plane_client=mock_plane_client,
        teams_client=mock_teams_client,
        notification_hour=8,
        max_retries=3
    )

def test_load_state_new_file(sync_service):
    """Test du chargement du state avec un nouveau fichier."""
    # On s'assure que le fichier n'existe pas
    if os.path.exists(sync_service.state_file):
        os.remove(sync_service.state_file)
    
    state = sync_service._load_state()
    assert state["last_sync"] is None
    assert state["last_sync_status"] == "success"
    assert state["last_issues"] == []
    assert state["error_count"] == 0
    assert state["last_error"] is None

def test_load_state_existing_file(sync_service, temp_state_file):
    """Test du chargement du state depuis un fichier existant."""
    test_state = {
        "last_sync": "2024-01-29T08:00:00+01:00",
        "last_sync_status": "success",
        "last_issues": ["1", "2"],
        "error_count": 0,
        "last_error": None
    }

    # On s'assure que le répertoire existe
    os.makedirs(os.path.dirname(temp_state_file), exist_ok=True)
    
    with open(temp_state_file, 'w') as f:
        json.dump(test_state, f)

    sync_service.state_file = temp_state_file
    state = sync_service._load_state()
    assert state == test_state

def test_save_state(sync_service, temp_state_file):
    """Test de la sauvegarde du state."""
    test_state = {
        "last_sync": "2024-01-29T08:00:00+01:00",
        "last_sync_status": "success",
        "last_issues": ["1", "2"],
        "error_count": 0,
        "last_error": None
    }
    sync_service.state = test_state
    sync_service.state_file = temp_state_file

    # On s'assure que le répertoire existe
    os.makedirs(os.path.dirname(temp_state_file), exist_ok=True)
    
    sync_service._save_state()

    with open(temp_state_file) as f:
        saved_state = json.load(f)
    assert saved_state == test_state

@pytest.mark.parametrize("current_time,last_sync,expected", [
    # Pas de dernier sync -> doit sync
    ("2024-01-29 08:00:00", None, True),
    
    # Dernier sync aujourd'hui avant 8h, maintenant 8h -> doit sync
    ("2024-01-29 08:00:00", "2024-01-29T07:00:00", True),
    
    # Dernier sync aujourd'hui après 8h -> ne doit pas sync
    ("2024-01-29 09:00:00", "2024-01-29T08:00:00", False),
    
    # Dernier sync hier avant 8h, maintenant avant 8h -> ne doit pas sync
    ("2024-01-29 07:00:00", "2024-01-28T07:00:00", False),
    
    # Dernier sync hier avant 8h, maintenant après 8h -> doit sync
    ("2024-01-29 08:00:00", "2024-01-28T07:00:00", True),
])
def test_should_sync(sync_service, current_time, last_sync, expected):
    """Test de la logique de décision de synchronisation."""
    sync_service.state["last_sync"] = last_sync
    
    with freeze_time(current_time):
        assert sync_service._should_sync() == expected

@pytest.mark.asyncio
async def test_sync_success(sync_service, mock_plane_client, mock_teams_client):
    """Test d'une synchronisation réussie."""
    # Setup mock issues
    mock_plane_client.get_issues.return_value = [
        PlaneIssue(
            id="1",
            name="Test Issue",
            description_html="<p>Test</p>",
            priority="urgent",
            state="state1",  # En cours
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            estimate_point=None,
            start_date=None,
            target_date=None,
            completed_at=None,
            sequence_id=1,
            project_id="test",
            labels=[],
            assignees=[]
        )
    ]
    
    # Force sync
    await sync_service.sync(force=True)
    
    # Verify
    assert mock_plane_client.get_states.called
    assert mock_plane_client.get_issues.called
    assert mock_teams_client.send_message.called
    assert mock_plane_client.close.called

@pytest.mark.asyncio
async def test_sync_failure_client_error(sync_service, mock_plane_client, mock_teams_client):
    """Test d'une synchronisation échouée à cause d'une erreur client."""
    # Setup mock to raise ClientError
    mock_plane_client.get_issues.side_effect = ClientError()
    
    # Force sync
    await sync_service.sync(force=True)
    
    # Verify
    assert mock_plane_client.get_states.called
    assert mock_plane_client.get_issues.called
    assert not mock_teams_client.send_message.called
    assert mock_plane_client.close.called

@pytest.mark.asyncio
async def test_sync_failure_value_error(sync_service, mock_plane_client, mock_teams_client):
    """Test d'une synchronisation échouée à cause d'une erreur de valeur."""
    # Setup mock to raise ValueError
    mock_plane_client.get_issues.side_effect = ValueError("Invalid data")
    
    # Force sync
    await sync_service.sync(force=True)
    
    # Verify
    assert mock_plane_client.get_states.called
    assert mock_plane_client.get_issues.called
    assert not mock_teams_client.send_message.called
    assert mock_plane_client.close.called

@pytest.mark.asyncio
async def test_sync_with_empty_states(sync_service, mock_plane_client, mock_teams_client):
    """Test d'une synchronisation avec une liste d'états vide."""
    # Setup mock to return empty states
    mock_plane_client.get_states.return_value = []

    # Force sync
    await sync_service.sync(force=True)

    # Verify
    mock_plane_client.get_states.assert_called_once()
    mock_plane_client.get_issues.assert_not_called()
    mock_teams_client.send_message.assert_not_called()
    mock_plane_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_sync_with_empty_issues(sync_service, mock_plane_client, mock_teams_client):
    """Test d'une synchronisation avec une liste d'issues vide."""
    # Setup mock to return empty issues
    mock_plane_client.get_issues.return_value = []
    
    # Force sync
    await sync_service.sync(force=True)
    
    # Verify
    assert mock_plane_client.get_states.called
    assert mock_plane_client.get_issues.called
    assert mock_teams_client.send_message.called  # Devrait quand même envoyer un message
    assert mock_plane_client.close.called

def test_start_scheduler(sync_service):
    """Test du démarrage du scheduler."""
    with patch('apscheduler.schedulers.asyncio.AsyncIOScheduler.add_job') as mock_add_job:
        sync_service.start()
        
        # Vérifier que le job quotidien a été ajouté
        mock_add_job.assert_called()
        
        # Si on doit sync immédiatement, vérifier qu'un second job a été ajouté
        if sync_service._should_sync():
            assert mock_add_job.call_count == 2 