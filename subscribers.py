"""
Subscriber management module for email notifications.
Handles subscriber storage, validation, and management using JSON file storage.
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUBSCRIBERS_FILE = "subscribers.json"
SUBSCRIBERS_DIR = "data"
SUBSCRIBERS_PATH = os.path.join(SUBSCRIBERS_DIR, SUBSCRIBERS_FILE)

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _ensure_data_directory():
    """Ensure the data directory exists."""
    os.makedirs(SUBSCRIBERS_DIR, exist_ok=True)


def _load_subscribers() -> Dict[str, Any]:
    """
    Load subscribers from JSON file.
    
    Returns:
        Dict containing subscribers data with metadata
    """
    _ensure_data_directory()
    
    if not os.path.exists(SUBSCRIBERS_PATH):
        # Create initial structure
        initial_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "subscribers": []
        }
        _save_subscribers(initial_data)
        return initial_data
    
    try:
        with open(SUBSCRIBERS_PATH, 'r') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading subscribers file: {e}")
        # Return empty structure on error
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "subscribers": []
        }


def _save_subscribers(data: Dict[str, Any]) -> bool:
    """
    Save subscribers data to JSON file.
    
    Args:
        data: Subscribers data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        _ensure_data_directory()
        data["updated_at"] = datetime.now().isoformat()
        
        with open(SUBSCRIBERS_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Subscribers data saved successfully. Total: {len(data['subscribers'])}")
        return True
        
    except IOError as e:
        logger.error(f"Error saving subscribers file: {e}")
        return False


def validate_email(email: str) -> Dict[str, Any]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Dict with validation result and message
    """
    if not email or not isinstance(email, str):
        return {"valid": False, "message": "Email address is required"}
    
    email = email.strip().lower()
    
    if not email:
        return {"valid": False, "message": "Email address cannot be empty"}
    
    if len(email) > 254:  # RFC 5321 limit
        return {"valid": False, "message": "Email address is too long"}
    
    if not EMAIL_REGEX.match(email):
        return {"valid": False, "message": "Invalid email address format"}
    
    return {"valid": True, "message": "Email is valid", "email": email}


def add_subscriber(email: str) -> Dict[str, Any]:
    """
    Add a new subscriber to the list.
    
    Args:
        email: Email address to add
        
    Returns:
        Dict with success status and message
    """
    # Validate email
    validation = validate_email(email)
    if not validation["valid"]:
        return {"success": False, "message": validation["message"]}
    
    email = validation["email"]
    
    # Load existing subscribers
    data = _load_subscribers()
    
    # Check if email already exists
    existing_emails = [sub["email"] for sub in data["subscribers"]]
    if email in existing_emails:
        return {"success": False, "message": "Email address is already subscribed"}
    
    # Add new subscriber
    subscriber = {
        "email": email,
        "subscribed_at": datetime.now().isoformat(),
        "active": True,
        "subscription_source": "web_dashboard"
    }
    
    data["subscribers"].append(subscriber)
    
    # Save updated data
    if _save_subscribers(data):
        logger.info(f"New subscriber added: {email}")
        return {
            "success": True, 
            "message": "Successfully subscribed to daily alerts",
            "email": email
        }
    else:
        return {"success": False, "message": "Failed to save subscription"}


def remove_subscriber(email: str) -> Dict[str, Any]:
    """
    Remove a subscriber from the list.
    
    Args:
        email: Email address to remove
        
    Returns:
        Dict with success status and message
    """
    # Validate email format
    validation = validate_email(email)
    if not validation["valid"]:
        return {"success": False, "message": validation["message"]}
    
    email = validation["email"]
    
    # Load existing subscribers
    data = _load_subscribers()
    
    # Find and remove subscriber
    original_count = len(data["subscribers"])
    data["subscribers"] = [sub for sub in data["subscribers"] if sub["email"] != email]
    
    if len(data["subscribers"]) == original_count:
        return {"success": False, "message": "Email address not found in subscribers"}
    
    # Save updated data
    if _save_subscribers(data):
        logger.info(f"Subscriber removed: {email}")
        return {
            "success": True, 
            "message": "Successfully unsubscribed from daily alerts",
            "email": email
        }
    else:
        return {"success": False, "message": "Failed to save unsubscription"}


def get_all_subscribers() -> List[str]:
    """
    Get list of all active subscriber email addresses.
    
    Returns:
        List of email addresses
    """
    data = _load_subscribers()
    active_subscribers = [
        sub["email"] for sub in data["subscribers"] 
        if sub.get("active", True)
    ]
    return active_subscribers


def get_subscriber_stats() -> Dict[str, Any]:
    """
    Get statistics about subscribers.
    
    Returns:
        Dict with subscriber statistics
    """
    data = _load_subscribers()
    
    total_subscribers = len(data["subscribers"])
    active_subscribers = len([sub for sub in data["subscribers"] if sub.get("active", True)])
    
    # Get subscription dates for analysis
    subscription_dates = [sub["subscribed_at"] for sub in data["subscribers"]]
    
    stats = {
        "total_subscribers": total_subscribers,
        "active_subscribers": active_subscribers,
        "inactive_subscribers": total_subscribers - active_subscribers,
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "latest_subscription": max(subscription_dates) if subscription_dates else None
    }
    
    return stats


def backup_subscribers() -> Dict[str, Any]:
    """
    Create a backup of subscriber data.
    
    Returns:
        Dict with backup status and filename
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"subscribers_backup_{timestamp}.json"
        backup_path = os.path.join(SUBSCRIBERS_DIR, backup_filename)
        
        data = _load_subscribers()
        
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Subscriber backup created: {backup_filename}")
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_file": backup_filename
        }
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return {"success": False, "message": f"Failed to create backup: {str(e)}"}


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Subscriber Management CLI")
        print("Usage:")
        print("  python subscribers.py add <email>")
        print("  python subscribers.py remove <email>")
        print("  python subscribers.py list")
        print("  python subscribers.py stats")
        print("  python subscribers.py backup")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "add" and len(sys.argv) == 3:
        email = sys.argv[2]
        result = add_subscriber(email)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
    elif command == "remove" and len(sys.argv) == 3:
        email = sys.argv[2]
        result = remove_subscriber(email)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
    elif command == "list":
        subscribers = get_all_subscribers()
        print(f"Active subscribers ({len(subscribers)}):")
        for email in subscribers:
            print(f"  - {email}")
            
    elif command == "stats":
        stats = get_subscriber_stats()
        print("Subscriber Statistics:")
        print(f"  Total: {stats['total_subscribers']}")
        print(f"  Active: {stats['active_subscribers']}")
        print(f"  Inactive: {stats['inactive_subscribers']}")
        print(f"  Last updated: {stats['updated_at']}")
        
    elif command == "backup":
        result = backup_subscribers()
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
    else:
        print("❌ Invalid command or arguments")
        sys.exit(1)