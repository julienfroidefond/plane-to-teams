"""Tests for the sync service."""
import json
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time

from plane_to_teams.sync_service import SyncService

@pytest.fixture
def mock_plane_client():
    """Mock du client Plane."""
    client = AsyncMock()
    client.get_issues = AsyncMock(return_value=[])
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
        state_file=temp_state_file,
        notification_hour=8
    )

def test_load_state_new_file(sync_service):
    """Test du chargement du state avec un nouveau fichier."""
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
    
    with open(temp_state_file, 'w') as f:
        json.dump(test_state, f)
    
    state = sync_service._load_state()
    assert state == test_state

def test_save_state(sync_service, temp_state_file):
    """Test de la sauvegarde du state."""
    sync_service.state = {
        "last_sync": "2024-01-29T08:00:00+01:00",
        "last_sync_status": "success",
        "last_issues": ["1", "2"],
        "error_count": 0,
        "last_error": None
    }
    
    sync_service._save_state()
    
    with open(temp_state_file) as f:
        saved_state = json.load(f)
    
    assert saved_state == sync_service.state

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
    # Simuler qu'on doit sync
    sync_service._should_sync = MagicMock(return_value=True)
    
    await sync_service.sync()
    
    # Vérifier que les appels ont été faits
    mock_plane_client.get_issues.assert_called_once()
    mock_teams_client.send_message.assert_called_once()
    
    # Vérifier le state
    assert sync_service.state["last_sync_status"] == "success"
    assert sync_service.state["error_count"] == 0
    assert sync_service.state["last_error"] is None

@pytest.mark.asyncio
async def test_sync_error(sync_service, mock_plane_client):
    """Test d'une synchronisation avec erreur."""
    # Simuler qu'on doit sync
    sync_service._should_sync = MagicMock(return_value=True)
    
    # Simuler une erreur
    mock_plane_client.get_issues.side_effect = Exception("Test error")
    
    await sync_service.sync()
    
    # Vérifier le state
    assert sync_service.state["last_sync_status"] == "error"
    assert sync_service.state["error_count"] == 1
    assert sync_service.state["last_error"] == "Test error"

@pytest.mark.asyncio
async def test_sync_max_retries(sync_service, mock_plane_client):
    """Test du nombre maximum de tentatives."""
    # Simuler qu'on doit sync
    sync_service._should_sync = MagicMock(return_value=True)
    
    # Simuler une erreur
    mock_plane_client.get_issues.side_effect = Exception("Test error")
    
    # Faire plus que le nombre max de tentatives
    for _ in range(sync_service.max_retries + 1):
        await sync_service.sync()
    
    # Vérifier que le compteur d'erreurs est au max
    assert sync_service.state["error_count"] == sync_service.max_retries
    
def test_start_scheduler(sync_service):
    """Test du démarrage du scheduler."""
    with patch('apscheduler.schedulers.asyncio.AsyncIOScheduler.add_job') as mock_add_job:
        sync_service.start()
        
        # Vérifier que le job quotidien a été ajouté
        mock_add_job.assert_called()
        
        # Si on doit sync immédiatement, vérifier qu'un second job a été ajouté
        if sync_service._should_sync():
            assert mock_add_job.call_count == 2 