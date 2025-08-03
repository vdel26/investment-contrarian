"""
Email service module using Resend API for sending notifications.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import resend

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration from environment variables
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@yourdomain.com")
FROM_NAME = os.getenv("FROM_NAME", "Market Sentiment Terminal")

# Initialize Resend client
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info("Resend API key configured successfully")
else:
    logger.warning("RESEND_API_KEY not found in environment variables")


def send_email(to: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an email using Resend API.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        html_content: HTML version of the email
        text_content: Plain text version of the email (optional)
    
    Returns:
        Dict containing success status and message/error details
    """
    if not RESEND_API_KEY:
        error_msg = "Resend API key not configured"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    try:
        # Prepare email parameters
        email_params = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to],
            "subject": subject,
            "html": html_content,
        }
        
        # Add text content if provided
        if text_content:
            email_params["text"] = text_content
        
        # Send email via Resend
        response = resend.Emails.send(email_params)
        
        logger.info(f"Email sent successfully to {to}. Message ID: {response.get('id', 'N/A')}")
        return {
            "success": True,
            "message_id": response.get("id"),
            "recipient": to
        }
        
    except Exception as e:
        error_msg = f"Failed to send email to {to}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


def send_test_email(to: str) -> Dict[str, Any]:
    """
    Send a test email to verify email service is working.
    
    Args:
        to: Recipient email address
    
    Returns:
        Dict containing success status and message/error details
    """
    subject = "Test Email - Market Sentiment Terminal"
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Email</title>
        <style>
            body {
                font-family: 'Courier New', monospace;
                background-color: #0a0a0a;
                color: #e4e4e4;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #111;
                border: 1px solid #333;
                padding: 20px;
            }
            .header {
                background-color: #111;
                color: #ff8c00;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                margin-bottom: 20px;
            }
            .content {
                padding: 0 15px;
            }
            .success {
                color: #4ADE80;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MARKET SENTIMENT TERMINAL</h1>
                <p>Email Service Test</p>
            </div>
            <div class="content">
                <p class="success">✓ Email service is working correctly!</p>
                <p>This is a test email to verify that the Resend integration is functioning properly.</p>
                <p>If you received this email, the email service is ready to send daily market sentiment alerts.</p>
                <hr style="border: 1px solid #333; margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated test message from the Market Sentiment Terminal.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = """
    MARKET SENTIMENT TERMINAL - Email Service Test
    
    ✓ Email service is working correctly!
    
    This is a test email to verify that the Resend integration is functioning properly.
    If you received this email, the email service is ready to send daily market sentiment alerts.
    
    ---
    This is an automated test message from the Market Sentiment Terminal.
    """
    
    return send_email(to, subject, html_content, text_content)


def validate_email_config() -> Dict[str, Any]:
    """
    Validate email service configuration.
    
    Returns:
        Dict containing configuration status and any issues
    """
    issues = []
    
    if not RESEND_API_KEY:
        issues.append("RESEND_API_KEY not set in environment variables")
    
    if not FROM_EMAIL or FROM_EMAIL == "alerts@yourdomain.com":
        issues.append("FROM_EMAIL not properly configured")
    
    config_status = {
        "configured": len(issues) == 0,
        "issues": issues,
        "settings": {
            "from_email": FROM_EMAIL,
            "from_name": FROM_NAME,
            "api_key_set": bool(RESEND_API_KEY)
        }
    }
    
    return config_status


if __name__ == "__main__":
    # CLI usage for testing
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python email_service.py <test_email@example.com>")
        sys.exit(1)
    
    test_email = sys.argv[1]
    
    # Validate configuration
    config = validate_email_config()
    if not config["configured"]:
        print("❌ Email service configuration issues:")
        for issue in config["issues"]:
            print(f"  - {issue}")
        sys.exit(1)
    
    print("✅ Email service configuration valid")
    print(f"📧 Sending test email to {test_email}...")
    
    # Send test email
    result = send_test_email(test_email)
    
    if result["success"]:
        print(f"✅ Test email sent successfully!")
        print(f"   Message ID: {result.get('message_id', 'N/A')}")
    else:
        print(f"❌ Failed to send test email:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)