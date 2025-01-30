"""Tests for the Plane API client."""
import json
from unittest import TestCase, mock
from requests.exceptions import RequestException

from plane_to_teams.config import Config
from plane_to_teams.plane_client import PlaneClient, PlaneIssue


class TestPlaneClient(TestCase):
    """Test cases for PlaneClient class."""

    def setUp(self):
        """Set up test cases."""
        self.config = Config(
            plane_api_token='test_token',
            plane_base_url='http://test.url',
            plane_workspace='test_workspace',
            plane_project_id='test_project',
            teams_webhook_url='http://teams.webhook',
            notification_hour=8,
            max_retries=3,
            sync_interval=10,
            log_level='DEBUG',
            log_file='test.log'
        )
        self.client = PlaneClient(self.config)
        
        # Sample issue data
        self.sample_issue = {
            'id': 'test-id',
            'name': 'Test Issue',
            'description_html': '<p>Test description</p>',
            'priority': 'high',
            'state': 'in_progress',
            'created_at': '2024-01-29T12:00:00Z',
            'updated_at': '2024-01-29T13:00:00Z',
            'estimate_point': 3,
            'start_date': '2024-01-29',
            'target_date': '2024-02-29',
            'completed_at': None,
            'sequence_id': 1,
            'project': 'test_project',
            'labels': ['label1', 'label2'],
            'assignees': ['user1', 'user2']
        }

    def test_get_issues_url(self):
        """Test issues URL construction."""
        url = self.client._get_issues_url()
        expected_url = 'http://test.url/workspaces/test_workspace/projects/test_project/issues/'
        self.assertEqual(url, expected_url)

    @mock.patch('requests.Session.get')
    async def test_get_issues_success(self, mock_get):
        """Test successful issues retrieval."""
        # Setup mock
        mock_response = mock.MagicMock()
        mock_response.json.return_value = [
            {
                'id': '1',
                'name': 'Test Issue',
                'priority': 'high',
                'state': 'daaf8056-e88d-40ba-b527-d58f3e518059'
            }
        ]
        mock_get.return_value = mock_response

        # Get issues
        issues = await self.client.get_issues()

        # Verify
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].id, '1')
        self.assertEqual(issues[0].name, 'Test Issue')
        self.assertEqual(issues[0].priority, 'high')
        self.assertEqual(issues[0].state, 'daaf8056-e88d-40ba-b527-d58f3e518059')

    @mock.patch('requests.Session.get')
    async def test_get_issues_failure(self, mock_get):
        """Test issues retrieval failure."""
        # Setup mock to raise exception
        mock_get.side_effect = Exception("Network error")

        # Verify exception is raised
        with self.assertRaises(Exception):
            await self.client.get_issues()

    @mock.patch('requests.Session.get')
    async def test_get_issue_success(self, mock_get):
        """Test successful issue retrieval."""
        # Setup mock
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {
            'id': '1',
            'name': 'Test Issue',
            'priority': 'high',
            'state': 'daaf8056-e88d-40ba-b527-d58f3e518059'
        }
        mock_get.return_value = mock_response

        # Get issue
        issue = await self.client.get_issue('1')

        # Verify
        self.assertEqual(issue.id, '1')
        self.assertEqual(issue.name, 'Test Issue')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.state, 'daaf8056-e88d-40ba-b527-d58f3e518059')

    @mock.patch('requests.Session.get')
    async def test_get_issue_failure(self, mock_get):
        """Test issue retrieval failure."""
        # Setup mock to raise exception
        mock_get.side_effect = Exception("Network error")

        # Verify exception is raised
        with self.assertRaises(Exception):
            await self.client.get_issue('1')

    @mock.patch('requests.Session.get')
    async def test_get_issue_not_found(self, mock_get):
        """Test issue not found."""
        # Setup mock
        mock_response = mock.MagicMock()
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        # Get issue
        issue = await self.client.get_issue('1')

        # Verify
        self.assertIsNone(issue)

    def test_plane_issue_from_api_response(self):
        """Test PlaneIssue creation from API response."""
        api_response = {
            'id': '1',
            'name': 'Test Issue',
            'description_html': '<p>Test description</p>',
            'priority': 'high',
            'state': 'daaf8056-e88d-40ba-b527-d58f3e518059',
            'created_at': '2024-01-30T12:00:00Z',
            'updated_at': '2024-01-30T12:00:00Z',
            'estimate_point': 3,
            'start_date': '2024-01-30',
            'target_date': '2024-02-30',
            'completed_at': None,
            'sequence_id': 1,
            'project': 'test_project',
            'labels': [],
            'assignees': []
        }

        issue = PlaneIssue.from_api_response(api_response)
        
        self.assertEqual(issue.id, '1')
        self.assertEqual(issue.name, 'Test Issue')
        self.assertEqual(issue.description_html, '<p>Test description</p>')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.state, 'daaf8056-e88d-40ba-b527-d58f3e518059')
        self.assertEqual(issue.estimate_point, 3)
        self.assertEqual(issue.sequence_id, 1)
        self.assertEqual(issue.project_id, 'test_project')
        self.assertEqual(issue.labels, [])
        self.assertEqual(issue.assignees, [])