"""Test Teams client."""
import json
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp

from plane_to_teams.teams_client import TeamsClient, TeamsMessage


class TestTeamsClient(unittest.TestCase):
    """Test Teams client."""

    def setUp(self):
        """Set up test environment."""
        self.webhook_url = "https://test.com/webhook"
        self.client = TeamsClient(self.webhook_url)
        self.message = TeamsMessage(
            title="Test Title",
            items=[
                ("URGENT", "Test Issue", "daaf8056-e88d-40ba-b527-d58f3e518059", "https://test.com/1")
            ]
        )

    @patch("aiohttp.ClientSession.post")
    async def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response

        await self.client.send_message(self.message)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.webhook_url)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    @patch("aiohttp.ClientSession.post")
    async def test_send_message_failure(self, mock_post):
        """Test failed message sending."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        mock_post.return_value.__aenter__.return_value = mock_response

        with self.assertRaises(aiohttp.ClientError):
            await self.client.send_message(self.message)

    def test_message_format(self):
        """Test message formatting."""
        message_dict = self.message.to_dict()

        # Verify message structure
        self.assertEqual(message_dict["@type"], "MessageCard")
        self.assertEqual(message_dict["@context"], "http://schema.org/extensions")
        self.assertEqual(message_dict["title"], "🎯 Test Title")
        self.assertEqual(len(message_dict["sections"]), 1)
        self.assertEqual(len(message_dict["sections"][0]["facts"]), 1)
        self.assertTrue(message_dict["sections"][0]["markdown"]) 