"""Tests for the Teams webhook client."""
import unittest
from unittest.mock import MagicMock, patch

import requests
from requests.exceptions import RequestException

from plane_to_teams.teams_client import TeamsClient
from plane_to_teams.teams_formatter import TeamsMessage

class TestTeamsClient(unittest.TestCase):
    """Test cases for TeamsClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.webhook_url = "https://teams.webhook.url"
        self.client = TeamsClient(self.webhook_url)
        self.message = TeamsMessage(
            title="Test Message",
            items=[
                ("high", "Item 1", "daaf8056-e88d-40ba-b527-d58f3e518059", "http://test.url/1"),
                ("medium", "Item 2", "9ce312cc-0018-4864-9867-064939dda809", "http://test.url/2")
            ]
        )
        
    @patch('requests.Session.post')
    async def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Send message
        result = await self.client.send_message(self.message)
        
        # Verify
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            self.webhook_url,
            json=self.message.to_dict(),
            timeout=10
        )
        
    @patch('requests.Session.post')
    async def test_send_message_failure(self, mock_post):
        """Test message sending failure."""
        # Setup mock to raise exception
        mock_post.side_effect = RequestException("Network error")
        
        # Verify exception is raised
        with self.assertRaises(RequestException):
            await self.client.send_message(self.message)
            
    def test_message_format(self):
        """Test message formatting."""
        message_dict = self.message.to_dict()
        
        # Verify message structure
        self.assertEqual(message_dict["type"], "message")
        self.assertEqual(len(message_dict["attachments"]), 1)
        
        # Verify card content
        card = message_dict["attachments"][0]
        self.assertEqual(card["contentType"], "application/vnd.microsoft.card.adaptive")
        
        # Verify card body
        body = card["content"]["body"]
        self.assertEqual(len(body), 2)
        
        # Verify title
        title_block = body[0]["items"][0]
        self.assertEqual(title_block["type"], "TextBlock")
        self.assertEqual(title_block["text"], "🎯 Test Message")
        
        # Verify items
        items_container = body[1]
        self.assertEqual(items_container["type"], "Container")
        items = items_container["items"]
        self.assertEqual(len(items), 2)
        
        # Verify first item
        first_item = items[0]
        self.assertEqual(first_item["type"], "ColumnSet")
        self.assertEqual(len(first_item["columns"]), 3)
        self.assertEqual(first_item["columns"][1]["items"][0]["text"], "[high]")
        self.assertEqual(first_item["columns"][2]["items"][0]["text"], "Item 1 (**En cours**)")
        self.assertEqual(first_item["selectAction"]["url"], "http://test.url/1") 