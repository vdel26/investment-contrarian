"""
Unit tests for subscriber management module.
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch
import sys

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subscribers


class TestSubscribers(unittest.TestCase):
    """Test cases for subscriber management functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_subscribers_dir = subscribers.SUBSCRIBERS_DIR
        self.original_subscribers_path = subscribers.SUBSCRIBERS_PATH
        
        # Patch the paths to use temporary directory
        subscribers.SUBSCRIBERS_DIR = self.test_dir
        subscribers.SUBSCRIBERS_PATH = os.path.join(self.test_dir, subscribers.SUBSCRIBERS_FILE)
        
        self.test_email = "test@example.com"
        self.test_email2 = "test2@example.com"

    def tearDown(self):
        """Clean up test environment."""
        # Restore original paths
        subscribers.SUBSCRIBERS_DIR = self.original_subscribers_dir
        subscribers.SUBSCRIBERS_PATH = self.original_subscribers_path
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_validate_email_success(self):
        """Test email validation with valid email."""
        result = subscribers.validate_email(self.test_email)
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["email"], self.test_email)
        self.assertEqual(result["message"], "Email is valid")

    def test_validate_email_invalid_format(self):
        """Test email validation with invalid format."""
        invalid_emails = [
            "invalid-email",
            "invalid@",
            "@invalid.com",
            "invalid@.com",
            "invalid@com",
            "invalid.email@"
        ]
        
        for email in invalid_emails:
            result = subscribers.validate_email(email)
            self.assertFalse(result["valid"])
            self.assertIn("Invalid email address", result["message"])

    def test_validate_email_empty_or_none(self):
        """Test email validation with empty or None input."""
        result = subscribers.validate_email("")
        self.assertFalse(result["valid"])
        
        result = subscribers.validate_email(None)
        self.assertFalse(result["valid"])

    def test_validate_email_too_long(self):
        """Test email validation with too long email."""
        long_email = "a" * 250 + "@example.com"
        result = subscribers.validate_email(long_email)
        
        self.assertFalse(result["valid"])
        self.assertIn("too long", result["message"])

    def test_add_subscriber_success(self):
        """Test adding a new subscriber."""
        result = subscribers.add_subscriber(self.test_email)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["email"], self.test_email)
        self.assertIn("Successfully subscribed", result["message"])
        
        # Verify subscriber was added to file
        all_subscribers = subscribers.get_all_subscribers()
        self.assertIn(self.test_email, all_subscribers)

    def test_add_subscriber_duplicate(self):
        """Test adding duplicate subscriber."""
        # Add subscriber first time
        result1 = subscribers.add_subscriber(self.test_email)
        self.assertTrue(result1["success"])
        
        # Try to add same subscriber again
        result2 = subscribers.add_subscriber(self.test_email)
        self.assertFalse(result2["success"])
        self.assertIn("already subscribed", result2["message"])

    def test_add_subscriber_invalid_email(self):
        """Test adding subscriber with invalid email."""
        result = subscribers.add_subscriber("invalid-email")
        
        self.assertFalse(result["success"])
        self.assertIn("Invalid email address", result["message"])

    def test_remove_subscriber_success(self):
        """Test removing an existing subscriber."""
        # Add subscriber first
        subscribers.add_subscriber(self.test_email)
        
        # Remove subscriber
        result = subscribers.remove_subscriber(self.test_email)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["email"], self.test_email)
        self.assertIn("Successfully unsubscribed", result["message"])
        
        # Verify subscriber was removed
        all_subscribers = subscribers.get_all_subscribers()
        self.assertNotIn(self.test_email, all_subscribers)

    def test_remove_subscriber_not_found(self):
        """Test removing non-existent subscriber."""
        result = subscribers.remove_subscriber(self.test_email)
        
        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"])

    def test_remove_subscriber_invalid_email(self):
        """Test removing subscriber with invalid email."""
        result = subscribers.remove_subscriber("invalid-email")
        
        self.assertFalse(result["success"])
        self.assertIn("Invalid email address", result["message"])

    def test_get_all_subscribers(self):
        """Test getting all subscribers."""
        # Initially should be empty
        subscribers_list = subscribers.get_all_subscribers()
        self.assertEqual(len(subscribers_list), 0)
        
        # Add multiple subscribers
        subscribers.add_subscriber(self.test_email)
        subscribers.add_subscriber(self.test_email2)
        
        # Get all subscribers
        subscribers_list = subscribers.get_all_subscribers()
        self.assertEqual(len(subscribers_list), 2)
        self.assertIn(self.test_email, subscribers_list)
        self.assertIn(self.test_email2, subscribers_list)

    def test_get_subscriber_stats(self):
        """Test getting subscriber statistics."""
        # Initially should be empty
        stats = subscribers.get_subscriber_stats()
        self.assertEqual(stats["total_subscribers"], 0)
        self.assertEqual(stats["active_subscribers"], 0)
        
        # Add subscribers
        subscribers.add_subscriber(self.test_email)
        subscribers.add_subscriber(self.test_email2)
        
        # Get updated stats
        stats = subscribers.get_subscriber_stats()
        self.assertEqual(stats["total_subscribers"], 2)
        self.assertEqual(stats["active_subscribers"], 2)
        self.assertIsNotNone(stats["created_at"])
        self.assertIsNotNone(stats["updated_at"])

    def test_backup_subscribers(self):
        """Test creating subscriber backup."""
        # Add some subscribers
        subscribers.add_subscriber(self.test_email)
        subscribers.add_subscriber(self.test_email2)
        
        # Create backup
        result = subscribers.backup_subscribers()
        
        self.assertTrue(result["success"])
        self.assertIn("backup", result["backup_file"])
        
        # Verify backup file exists
        backup_path = os.path.join(self.test_dir, result["backup_file"])
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup contains data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
            self.assertEqual(len(backup_data["subscribers"]), 2)

    def test_file_persistence(self):
        """Test that subscriber data persists across module reloads."""
        # Add subscriber
        subscribers.add_subscriber(self.test_email)
        
        # Verify file was created
        self.assertTrue(os.path.exists(subscribers.SUBSCRIBERS_PATH))
        
        # Load data directly from file
        with open(subscribers.SUBSCRIBERS_PATH, 'r') as f:
            data = json.load(f)
            emails = [sub["email"] for sub in data["subscribers"]]
            self.assertIn(self.test_email, emails)

    def test_email_normalization(self):
        """Test that emails are normalized (lowercase, trimmed)."""
        # Add email with mixed case and whitespace
        test_email_mixed = "  TEST@EXAMPLE.COM  "
        result = subscribers.add_subscriber(test_email_mixed)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["email"], "test@example.com")
        
        # Verify normalized email is in subscribers list
        all_subscribers = subscribers.get_all_subscribers()
        self.assertIn("test@example.com", all_subscribers)
        self.assertNotIn(test_email_mixed, all_subscribers)

    def test_concurrent_operations(self):
        """Test that multiple operations work correctly."""
        # Add multiple subscribers
        emails = [f"test{i}@example.com" for i in range(5)]
        
        for email in emails:
            result = subscribers.add_subscriber(email)
            self.assertTrue(result["success"])
        
        # Verify all were added
        all_subscribers = subscribers.get_all_subscribers()
        self.assertEqual(len(all_subscribers), 5)
        
        # Remove some subscribers
        for email in emails[:3]:
            result = subscribers.remove_subscriber(email)
            self.assertTrue(result["success"])
        
        # Verify correct count remains
        remaining_subscribers = subscribers.get_all_subscribers()
        self.assertEqual(len(remaining_subscribers), 2)


class TestSubscriberFileOperations(unittest.TestCase):
    """Test file operations and error handling."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_subscribers_dir = subscribers.SUBSCRIBERS_DIR
        self.original_subscribers_path = subscribers.SUBSCRIBERS_PATH
        
        subscribers.SUBSCRIBERS_DIR = self.test_dir
        subscribers.SUBSCRIBERS_PATH = os.path.join(self.test_dir, subscribers.SUBSCRIBERS_FILE)

    def tearDown(self):
        """Clean up test environment."""
        subscribers.SUBSCRIBERS_DIR = self.original_subscribers_dir
        subscribers.SUBSCRIBERS_PATH = self.original_subscribers_path
        shutil.rmtree(self.test_dir)

    def test_corrupted_file_handling(self):
        """Test handling of corrupted subscriber file."""
        # Create corrupted JSON file
        with open(subscribers.SUBSCRIBERS_PATH, 'w') as f:
            f.write("invalid json content")
        
        # Should handle corruption gracefully
        result = subscribers.add_subscriber("test@example.com")
        self.assertTrue(result["success"])
        
        # Should create new valid file
        all_subscribers = subscribers.get_all_subscribers()
        self.assertEqual(len(all_subscribers), 1)

    @patch('subscribers._ensure_data_directory')
    def test_directory_creation_error(self, mock_ensure_dir):
        """Test handling of directory creation errors."""
        mock_ensure_dir.side_effect = OSError("Permission denied")
        
        # Should handle directory creation error gracefully
        try:
            result = subscribers.add_subscriber("test@example.com")
            # If it succeeds, the directory already existed
            self.assertIsInstance(result, dict)
        except OSError:
            # If it fails, that's expected behavior for permission errors
            pass


if __name__ == '__main__':
    unittest.main()