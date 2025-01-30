"""Tests for the logger module."""
import logging
import os
from unittest import TestCase, mock

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging


class TestLogger(TestCase):
    """Test cases for logger setup."""

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

    def tearDown(self):
        """Clean up after tests."""
        # Remove test log file if it exists
        if os.path.exists(self.config.log_file):
            os.remove(self.config.log_file)
        
        # Reset root logger
        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.setLevel(logging.WARNING)

    def test_setup_logging(self):
        """Test logging setup."""
        setup_logging(self.config)
        
        root_logger = logging.getLogger()
        
        # Check log level
        self.assertEqual(root_logger.level, logging.DEBUG)
        
        # Check handlers
        self.assertEqual(len(root_logger.handlers), 2)
        
        # Check handler types
        handlers = root_logger.handlers
        handler_types = [type(h) for h in handlers]
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.handlers.RotatingFileHandler, handler_types)
        
        # Test logging
        test_message = "Test log message"
        logging.info(test_message)
        
        # Verify file logging
        with open(self.config.log_file, 'r') as f:
            log_content = f.read()
            self.assertIn(test_message, log_content)

    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid log level."""
        self.config.log_level = 'INVALID'
        
        with self.assertRaises(ValueError):
            setup_logging(self.config)

    def test_setup_logging_file_creation(self):
        """Test log file creation."""
        setup_logging(self.config)
        
        self.assertTrue(os.path.exists(self.config.log_file))
        self.assertTrue(os.path.isfile(self.config.log_file)) 