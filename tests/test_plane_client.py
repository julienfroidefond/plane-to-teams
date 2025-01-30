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
        expected_url = 'http://test.url/workspaces/test_workspace/projects/test_project/issues/'
        self.assertEqual(self.client._get_issues_url(), expected_url)

    def test_get_issues_success(self):
        """Test successful issues fetch."""
        with mock.patch('requests.Session.get') as mock_get:
            mock_get.return_value.json.return_value = {'results': [self.sample_issue]}
            mock_get.return_value.status_code = 200
            
            issues = self.client.get_issues()
            
            self.assertEqual(len(issues), 1)
            issue = issues[0]
            self.assertIsInstance(issue, PlaneIssue)
            self.assertEqual(issue.id, 'test-id')
            self.assertEqual(issue.name, 'Test Issue')
            self.assertEqual(issue.priority, 'high')
            self.assertEqual(issue.labels, ['label1', 'label2'])
            self.assertEqual(issue.assignees, ['user1', 'user2'])

    def test_get_issues_failure(self):
        """Test failed issues fetch."""
        with mock.patch('requests.Session.get') as mock_get:
            mock_get.side_effect = RequestException('API Error')
            
            with self.assertRaises(RequestException):
                self.client.get_issues()

    def test_get_issue_success(self):
        """Test successful single issue fetch."""
        with mock.patch('requests.Session.get') as mock_get:
            mock_get.return_value.json.return_value = self.sample_issue
            mock_get.return_value.status_code = 200
            
            issue = self.client.get_issue('test-id')
            
            self.assertIsInstance(issue, PlaneIssue)
            self.assertEqual(issue.id, 'test-id')
            self.assertEqual(issue.name, 'Test Issue')
            self.assertEqual(issue.labels, ['label1', 'label2'])
            self.assertEqual(issue.assignees, ['user1', 'user2'])

    def test_get_issue_not_found(self):
        """Test issue not found."""
        with mock.patch('requests.Session.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            issue = self.client.get_issue('non-existent')
            self.assertIsNone(issue)

    def test_get_issue_failure(self):
        """Test failed single issue fetch."""
        with mock.patch('requests.Session.get') as mock_get:
            mock_get.side_effect = RequestException('API Error')
            
            with self.assertRaises(RequestException):
                self.client.get_issue('test-id')

    def test_plane_issue_from_api_response(self):
        """Test PlaneIssue creation from API response."""
        issue = PlaneIssue.from_api_response(self.sample_issue)
        
        self.assertEqual(issue.id, 'test-id')
        self.assertEqual(issue.name, 'Test Issue')
        self.assertEqual(issue.description_html, '<p>Test description</p>')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.state, 'in_progress')
        self.assertEqual(issue.estimate_point, 3)
        self.assertEqual(issue.sequence_id, 1)
        self.assertEqual(issue.project_id, 'test_project')
        self.assertEqual(issue.labels, ['label1', 'label2'])
        self.assertEqual(issue.assignees, ['user1', 'user2'])