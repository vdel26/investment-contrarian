"""
Unit tests for email service module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import email_service


class TestEmailService(unittest.TestCase):
    """Test cases for email service functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_email = "test@example.com"
        self.test_subject = "Test Subject"
        self.test_html = "<h1>Test HTML</h1>"
        self.test_text = "Test Text"

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.resend.Emails.send')
    def test_send_email_success(self, mock_send):
        """Test successful email sending."""
        # Mock successful response
        mock_send.return_value = {"id": "msg_123456"}
        
        result = email_service.send_email(
            self.test_email, 
            self.test_subject, 
            self.test_html, 
            self.test_text
        )
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_123456")
        self.assertEqual(result["recipient"], self.test_email)
        
        # Verify the API was called correctly
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["to"], [self.test_email])
        self.assertEqual(call_args["subject"], self.test_subject)
        self.assertEqual(call_args["html"], self.test_html)
        self.assertEqual(call_args["text"], self.test_text)

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.resend.Emails.send')
    def test_send_email_without_text(self, mock_send):
        """Test email sending without text content."""
        mock_send.return_value = {"id": "msg_123456"}
        
        result = email_service.send_email(
            self.test_email, 
            self.test_subject, 
            self.test_html
        )
        
        self.assertTrue(result["success"])
        
        # Verify text content was not included
        call_args = mock_send.call_args[0][0]
        self.assertNotIn("text", call_args)

    @patch('email_service.RESEND_API_KEY', None)
    def test_send_email_no_api_key(self):
        """Test email sending without API key."""
        result = email_service.send_email(
            self.test_email, 
            self.test_subject, 
            self.test_html
        )
        
        self.assertFalse(result["success"])
        self.assertIn("API key not configured", result["error"])

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.resend.Emails.send')
    def test_send_email_api_error(self, mock_send):
        """Test email sending with API error."""
        mock_send.side_effect = Exception("API Error")
        
        result = email_service.send_email(
            self.test_email, 
            self.test_subject, 
            self.test_html
        )
        
        self.assertFalse(result["success"])
        self.assertIn("API Error", result["error"])

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.resend.Emails.send')
    def test_send_test_email(self, mock_send):
        """Test sending test email."""
        mock_send.return_value = {"id": "msg_test123"}
        
        result = email_service.send_test_email(self.test_email)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_test123")
        
        # Verify the API was called with test email content
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["to"], [self.test_email])
        self.assertIn("Test Email", call_args["subject"])
        self.assertIn("Email service is working", call_args["html"])
        self.assertIn("Email service is working", call_args["text"])

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.FROM_EMAIL', 'test@example.com')
    def test_validate_email_config_success(self):
        """Test email configuration validation with valid config."""
        result = email_service.validate_email_config()
        
        self.assertTrue(result["configured"])
        self.assertEqual(len(result["issues"]), 0)
        self.assertEqual(result["settings"]["from_email"], "test@example.com")
        self.assertTrue(result["settings"]["api_key_set"])

    @patch('email_service.RESEND_API_KEY', None)
    @patch('email_service.FROM_EMAIL', 'alerts@yourdomain.com')
    def test_validate_email_config_missing_values(self):
        """Test email configuration validation with missing values."""
        result = email_service.validate_email_config()
        
        self.assertFalse(result["configured"])
        self.assertEqual(len(result["issues"]), 2)
        self.assertIn("RESEND_API_KEY not set", result["issues"][0])
        self.assertIn("FROM_EMAIL not properly configured", result["issues"][1])

    @patch('email_service.RESEND_API_KEY', 'test_api_key')
    @patch('email_service.FROM_EMAIL', 'valid@example.com')
    def test_validate_email_config_partial_missing(self):
        """Test email configuration validation with some missing values."""
        result = email_service.validate_email_config()
        
        self.assertTrue(result["configured"])
        self.assertEqual(len(result["issues"]), 0)


class TestEmailServiceIntegration(unittest.TestCase):
    """Integration tests for email service (require actual API key)."""

    def setUp(self):
        """Set up integration test environment."""
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL")
        
    def test_config_validation_with_env_vars(self):
        """Test configuration validation with actual environment variables."""
        if not self.api_key:
            self.skipTest("RESEND_API_KEY not set - skipping integration test")
        
        result = email_service.validate_email_config()
        
        if self.from_email and self.from_email != "alerts@yourdomain.com":
            self.assertTrue(result["configured"])
        else:
            self.assertFalse(result["configured"])
            self.assertIn("FROM_EMAIL not properly configured", result["issues"])


if __name__ == '__main__':
    unittest.main()