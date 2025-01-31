"""Tests for the Teams message formatter."""
from datetime import datetime
import unittest

from plane_to_teams.config import Config
from plane_to_teams.plane_client import PlaneIssue, PlaneState
from plane_to_teams.teams_formatter import TeamsMessage, format_issues


class TestTeamsFormatter(unittest.TestCase):
    """Test cases for Teams formatter."""

    def setUp(self):
        """Set up test cases."""
        self.config = Config(
            plane_api_token="test_token",
            plane_base_url="http://test.url",
            plane_workspace="test_workspace",
            plane_project_id="test_project",
            teams_webhook_url="http://teams.webhook"
        )
        
        self.sample_states = [
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
            ),
            PlaneState(
                id="state4",
                name="Terminé",
                color="#000000",
                sequence=4,
                group="completed",
                default=False
            )
        ]
        
        self.sample_issues = [
            PlaneIssue(
                id="1",
                name="Urgent Issue",
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
            ),
            PlaneIssue(
                id="2",
                name="High Priority Issue",
                description_html="<p>Test</p>",
                priority="high",
                state="state2",  # A faire
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                estimate_point=None,
                start_date=None,
                target_date=None,
                completed_at=None,
                sequence_id=2,
                project_id="test",
                labels=[],
                assignees=[]
            ),
            PlaneIssue(
                id="3",
                name="Backlog Issue",
                description_html="<p>Test</p>",
                priority="medium",  # Changed from urgent to medium
                state="state3",  # Backlog
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                estimate_point=None,
                start_date=None,
                target_date=None,
                completed_at=datetime.now().isoformat(),
                sequence_id=3,
                project_id="test",
                labels=[],
                assignees=[]
            ),
            PlaneIssue(
                id="4",
                name="Completed Issue",
                description_html="<p>Test</p>",
                priority="urgent",
                state="state4",  # Terminé
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                estimate_point=None,
                start_date=None,
                target_date=None,
                completed_at=datetime.now().isoformat(),
                sequence_id=4,
                project_id="test",
                labels=[],
                assignees=[]
            )
        ]

    def test_format_issues(self):
        """Test formatting issues into Teams message."""
        message = format_issues(self.sample_issues, self.sample_states, self.config)
        
        self.assertIsInstance(message, TeamsMessage)
        self.assertEqual(len(message.items), 3)  # Only issues with states in allowed groups
        
        # Check first item (urgent + en cours)
        priority, name, state, url = message.items[0]
        self.assertEqual(priority, "URGENT")
        self.assertEqual(name, "Urgent Issue")
        self.assertEqual(state, "En cours")
        self.assertTrue(url.startswith("https://plane.julienfroidefond.com"))
        self.assertIn(self.config.plane_workspace, url)
        self.assertIn(self.config.plane_project_id, url)
        
        # Check sorting (urgent en cours, then high a faire, then medium backlog)
        states = [item[2] for item in message.items]
        self.assertEqual(
            states,
            [
                "En cours",  # state1
                "A faire",   # state2
                "Backlog"    # state3
            ]
        )
        
        # Check priorities are correctly sorted
        priorities = [item[0] for item in message.items]
        self.assertEqual(
            priorities,
            ["URGENT", "HIGH", "MEDIUM"]
        )

    def test_teams_message_to_dict(self):
        """Test Teams message conversion to dict."""
        message = TeamsMessage(
            title="Test Title",
            items=[
                ("URGENT", "Test Issue", "En cours", "https://test.com/1")
            ]
        )

        message_dict = message.to_dict()

        # Verify message structure
        self.assertEqual(message_dict["@type"], "MessageCard")
        self.assertEqual(message_dict["@context"], "http://schema.org/extensions")
        self.assertEqual(message_dict["title"], "🎯 Test Title")
        self.assertEqual(len(message_dict["sections"]), 1)
        self.assertEqual(len(message_dict["sections"][0]["facts"]), 1)
        self.assertTrue(message_dict["sections"][0]["markdown"]) 