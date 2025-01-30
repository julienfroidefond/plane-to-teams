"""Tests for the configuration module."""
import os
from unittest import TestCase, mock

from plane_to_teams.config import Config


class TestConfig(TestCase):
    """Test cases for Config class."""

    def setUp(self):
        """Set up test cases."""
        self.env_vars = {
            'PLANE_API_TOKEN': 'test_token',
            'PLANE_BASE_URL': 'http://test.url',
            'PLANE_WORKSPACE': 'test_workspace',
            'PLANE_PROJECT_ID': 'test_project',
            'TEAMS_WEBHOOK_URL': 'http://teams.webhook',
            'SYNC_INTERVAL': '10',
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': 'test.log'
        }

    def test_config_from_env(self):
        """Test configuration loading from environment variables."""
        with mock.patch.dict(os.environ, self.env_vars):
            config = Config.from_env()
            
            self.assertEqual(config.plane_api_token, 'test_token')
            self.assertEqual(config.plane_base_url, 'http://test.url')
            self.assertEqual(config.plane_workspace, 'test_workspace')
            self.assertEqual(config.plane_project_id, 'test_project')
            self.assertEqual(config.teams_webhook_url, 'http://teams.webhook')
            self.assertEqual(config.sync_interval, 10)
            self.assertEqual(config.log_level, 'DEBUG')
            self.assertEqual(config.log_file, 'test.log')

    def test_config_validation_success(self):
        """Test configuration validation with valid data."""
        with mock.patch.dict(os.environ, self.env_vars):
            config = Config.from_env()
            self.assertIsNone(config.validate())

    def test_config_validation_missing_required(self):
        """Test configuration validation with missing required fields."""
        # Test each required field
        required_fields = [
            'PLANE_API_TOKEN',
            'PLANE_BASE_URL',
            'PLANE_WORKSPACE',
            'PLANE_PROJECT_ID',
            'TEAMS_WEBHOOK_URL'
        ]

        for field in required_fields:
            env_vars = self.env_vars.copy()
            env_vars[field] = ''
            
            with mock.patch.dict(os.environ, env_vars):
                config = Config.from_env()
                error = config.validate()
                self.assertIsNotNone(error)
                self.assertIn(field.replace('_', ' ').title(), error)

    def test_config_validation_invalid_sync_interval(self):
        """Test configuration validation with invalid sync interval."""
        env_vars = self.env_vars.copy()
        env_vars['SYNC_INTERVAL'] = '0'

        with mock.patch.dict(os.environ, env_vars):
            config = Config.from_env()
            error = config.validate()
            self.assertEqual(error, "Sync Interval must be greater than 0") 
