"""Tests for the logger module."""
import os
import unittest
from unittest import mock

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging


class TestLogger(unittest.TestCase):
    """Test cases for logger module."""

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

    def test_setup_logging(self):
        """Test logging setup."""
        logger = setup_logging(self.config)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, 10)  # DEBUG level
        self.assertEqual(len(logger.handlers), 2)  # File and console handlers
        os.remove(self.config.log_file)

    def test_setup_logging_file_creation(self):
        """Test log file creation."""
        setup_logging(self.config)
        self.assertTrue(os.path.exists(self.config.log_file))
        os.remove(self.config.log_file)

    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid log level."""
        self.config.log_level = 'INVALID'
        with self.assertRaises(ValueError) as cm:
            setup_logging(self.config)
        self.assertEqual(str(cm.exception), "Invalid log level: INVALID") 