"""Tests for the Teams message formatter."""
from datetime import datetime
import unittest

from plane_to_teams.plane_client import PlaneIssue
from plane_to_teams.teams_formatter import TeamsMessage, format_issues, STATE_ORDER

class TestTeamsFormatter(unittest.TestCase):
    """Test cases for Teams formatter."""

    def setUp(self):
        """Set up test cases."""
        self.sample_issues = [
            PlaneIssue(
                id="1",
                name="Urgent Issue",
                description_html="<p>Test</p>",
                priority="urgent",
                state="daaf8056-e88d-40ba-b527-d58f3e518059",  # En cours
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
                state="9ce312cc-0018-4864-9867-064939dda809",  # A faire
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
                state="318803e3-f0ce-4dbf-b0b4-beb1cfba9e81",  # Backlog
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
                name="Archived Issue",
                description_html="<p>Test</p>",
                priority="urgent",
                state="ad3ab555-13e9-4ef5-901d-a64813915722",  # Archivé
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
        message = format_issues(self.sample_issues)
        
        self.assertIsInstance(message, TeamsMessage)
        self.assertEqual(len(message.items), 3)  # Only issues with states in STATE_ORDER
        
        # Check first item (urgent + en cours)
        priority, name, state, url = message.items[0]
        self.assertEqual(priority, "URGENT")
        self.assertEqual(name, "Urgent Issue")
        self.assertEqual(state, "daaf8056-e88d-40ba-b527-d58f3e518059")
        self.assertTrue(url.startswith("https://plane.julienfroidefond.com"))
        
        # Check sorting (urgent en cours, then high a faire, then medium backlog)
        states = [item[2] for item in message.items]
        self.assertEqual(
            states,
            [
                "daaf8056-e88d-40ba-b527-d58f3e518059",  # En cours
                "9ce312cc-0018-4864-9867-064939dda809",  # A faire
                "318803e3-f0ce-4dbf-b0b4-beb1cfba9e81",  # Backlog
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
                ("URGENT", "Test Issue", "daaf8056-e88d-40ba-b527-d58f3e518059", "https://test.com/1")
            ]
        )
        
        message_dict = message.to_dict()
        
        self.assertEqual(message_dict["type"], "message")
        self.assertEqual(len(message_dict["attachments"]), 1)
        self.assertEqual(
            message_dict["attachments"][0]["contentType"],
            "application/vnd.microsoft.card.adaptive"
        )
        
        content = message_dict["attachments"][0]["content"]
        self.assertEqual(content["type"], "AdaptiveCard")
        self.assertEqual(content["version"], "1.2")
        
        # Check container structure
        body = content["body"]
        self.assertEqual(len(body), 2)
        self.assertEqual(body[0]["type"], "Container")
        self.assertEqual(body[1]["type"], "Container")
        
        # Check title
        title_container = body[0]
        title_block = title_container["items"][0]
        self.assertEqual(title_block["text"], "🎯 Test Title")
        self.assertEqual(title_block["weight"], "bolder")
        
        # Check issue item
        items_container = body[1]
        column_set = items_container["items"][0]
        self.assertEqual(column_set["type"], "ColumnSet")
        
        # Check columns
        columns = column_set["columns"]
        self.assertEqual(len(columns), 3)
        
        # Check priority column
        priority_column = columns[1]
        priority_text = priority_column["items"][0]["text"]
        self.assertEqual(priority_text, "[URGENT]")
        
        # Check issue column with state
        issue_column = columns[2]
        issue_text = issue_column["items"][0]["text"]
        self.assertEqual(issue_text, "Test Issue (**En cours**)")
        
        # Check URL action
        self.assertEqual(column_set["selectAction"]["type"], "Action.OpenUrl")
        self.assertEqual(column_set["selectAction"]["url"], "https://test.com/1") 