"""
Email content generation module for daily market sentiment alerts.
Reads cached data and generates formatted email content using templates.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from data_provider import get_fear_and_greed_data, get_aaii_sentiment_data, get_ssi_data, get_overall_analysis_data

# Configuration
from config import EMAIL_TEMPLATES_DIR, DASHBOARD_URL, UNSUBSCRIBE_URL

# Template paths
HTML_TEMPLATE_PATH = EMAIL_TEMPLATES_DIR / "daily_alert.html"
TEXT_TEMPLATE_PATH = EMAIL_TEMPLATES_DIR / "daily_alert.txt"


def load_template(template_path) -> str:
    """
    Load email template from file.
    
    Args:
        template_path: Path to template file (str or Path object)
        
    Returns:
        Template content as string
    """
    try:
        with open(str(template_path), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_path}")
    except Exception as e:
        raise Exception(f"Error loading template: {str(e)}")


def get_recommendation_class(recommendation: str) -> str:
    """Get CSS class for recommendation styling."""
    return recommendation.lower().replace(' ', '')


def get_fng_class(score: float) -> str:
    """Get CSS class for Fear & Greed score."""
    if score < 25:
        return "fear-extreme"
    elif score < 45:
        return "fear"
    elif score < 55:
        return "neutral"
    elif score < 75:
        return "greed"
    else:
        return "greed-extreme"


def get_aaii_class(spread: float) -> str:
    """Get CSS class for AAII spread."""
    if spread < -20:
        return "bearish"
    elif spread < -10:
        return "fear"
    elif spread < 10:
        return "neutral"
    elif spread < 20:
        return "greed"
    else:
        return "bullish"


def get_ssi_class(level: float) -> str:
    """Get CSS class for SSI level."""
    if level < 50:
        return "bearish"
    elif level < 55:
        return "neutral"
    elif level < 60:
        return "bullish"
    else:
        return "extreme-bullish"


def format_ssi_history(ssi_data: list, limit: int = 4) -> Tuple[str, str]:
    """
    Format SSI history for both HTML and text templates.
    
    Args:
        ssi_data: List of SSI data points
        limit: Number of recent months to include
        
    Returns:
        Tuple of (html_formatted, text_formatted)
    """
    if not ssi_data:
        return "No historical data available", "No historical data available"
    
    # Get recent data points
    recent_data = ssi_data[-limit:] if len(ssi_data) > limit else ssi_data
    recent_data.reverse()  # Most recent first
    
    # HTML format
    html_rows = []
    for data_point in recent_data:
        level = float(data_point.get('level', 0))
        date = data_point.get('date', 'Unknown')
        css_class = get_ssi_class(level)
        
        html_rows.append(f'''
            <div class="ssi-row">
                <div class="ssi-month">{date}</div>
                <div class="ssi-value {css_class}">{level:.1f}%</div>
            </div>
        ''')
    
    html_formatted = ''.join(html_rows)
    
    # Text format
    text_rows = []
    for data_point in recent_data:
        level = float(data_point.get('level', 0))
        date = data_point.get('date', 'Unknown')
        text_rows.append(f"{date}: {level:.1f}%")
    
    text_formatted = '\n'.join(text_rows)
    
    return html_formatted, text_formatted


def generate_template_variables() -> Dict[str, Any]:
    """
    Generate template variables from cached market data.
    
    Returns:
        Dictionary of template variables
    """
    # Load cached data
    fng_data = get_fear_and_greed_data()
    aaii_data = get_aaii_sentiment_data()
    ssi_data = get_ssi_data()
    overall_data = get_overall_analysis_data()
    
    # Check for errors in data
    if "error" in fng_data:
        raise Exception(f"Fear & Greed data error: {fng_data['error']}")
    if "error" in aaii_data:
        raise Exception(f"AAII data error: {aaii_data['error']}")
    
    # Process Fear & Greed data
    fng_score = fng_data.get('score', 0)
    fng_rating = fng_data.get('rating', 'Unknown')
    
    # Shorter description for email
    if fng_score < 25:
        fng_description = "Extreme fear - potential buying opportunity."
    elif fng_score < 45:
        fng_description = "Fear dominates - contrarian signal."
    elif fng_score < 55:
        fng_description = "Balanced sentiment."
    elif fng_score < 75:
        fng_description = "Greed building - caution advised."
    else:
        fng_description = "Extreme greed - potential selling opportunity."
    
    fng_1d_ago = fng_data.get('previous_close', 0)
    fng_1w_ago = fng_data.get('previous_1_week', 0)
    
    # Process AAII data
    aaii_bullish = aaii_data.get('bullish', 0)
    aaii_bearish = aaii_data.get('bearish', 0)
    aaii_spread = aaii_bullish - aaii_bearish
    
    # Get AAII historical data
    aaii_historical = aaii_data.get('historical', {})
    aaii_1w_ago = aaii_historical.get('1w_ago', {}).get('spread', 0)
    aaii_1m_ago = aaii_historical.get('1m_ago', {}).get('spread', 0)
    
    if aaii_spread > 15:
        aaii_description = "Excessive bullishness - sell signal."
    elif aaii_spread < -15:
        aaii_description = "Excessive bearishness - buy signal."
    else:
        aaii_description = "Balanced sentiment."
    
    # Process SSI data
    ssi_latest_value = 0
    ssi_latest_month = "Unknown"
    ssi_sentiment = "Unknown"
    ssi_description = "SSI data not available."
    ssi_history_html = ""
    ssi_history_text = ""
    
    if ssi_data and isinstance(ssi_data, list) and len(ssi_data) > 0:
        latest_ssi = ssi_data[-1]
        ssi_latest_value = float(latest_ssi.get('level', 0))
        ssi_latest_month = latest_ssi.get('date', 'Unknown')
        
        if ssi_latest_value < 50:
            ssi_sentiment = "Bearish"
            ssi_description = "Sell-side analysts pessimistic - contrarian buy."
        elif ssi_latest_value < 55:
            ssi_sentiment = "Neutral"
            ssi_description = "Balanced analyst sentiment."
        elif ssi_latest_value < 60:
            ssi_sentiment = "Bullish"
            ssi_description = "Analysts optimistic - caution advised."
        else:
            ssi_sentiment = "Extreme Bullish"
            ssi_description = "Extreme optimism - contrarian sell signal."
        
        ssi_history_html, ssi_history_text = format_ssi_history(ssi_data)
    
    # Process overall recommendation
    recommendation = overall_data.get('recommendation', 'HOLD')
    commentary = overall_data.get('commentary', 'No commentary available.')
    
    # Generate timestamp
    now = datetime.now()
    date_str = now.strftime("%m.%d.%y")  # Format: 8.3.25
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S ET")
    
    # Build template variables
    variables = {
        # Header
        'date': date_str,
        'timestamp': timestamp,
        
        # Recommendation
        'recommendation': recommendation,
        'recommendation_class': get_recommendation_class(recommendation),
        'commentary': commentary,
        
        # Fear & Greed
        'fng_score': round(fng_score),
        'fng_rating': fng_rating,
        'fng_class': get_fng_class(fng_score),
        'fng_description': fng_description,
        'fng_1d_ago': round(fng_1d_ago),
        'fng_1w_ago': round(fng_1w_ago),
        
        # AAII
        'aaii_bullish': f"{aaii_bullish:.1f}",
        'aaii_bearish': f"{aaii_bearish:.1f}",
        'aaii_spread': f"{aaii_spread:+.1f}",
        'aaii_class': get_aaii_class(aaii_spread),
        'aaii_description': aaii_description,
        'aaii_1w_ago': f"{aaii_1w_ago:+.1f}",
        'aaii_1m_ago': f"{aaii_1m_ago:+.1f}",
        
        # SSI
        'ssi_latest_value': f"{ssi_latest_value:.1f}",
        'ssi_latest_month': ssi_latest_month,
        'ssi_sentiment': ssi_sentiment,
        'ssi_class': get_ssi_class(ssi_latest_value),
        'ssi_description': ssi_description,
        'ssi_history': ssi_history_html,
        'ssi_history_text': ssi_history_text,
        
        # Footer
        'dashboard_url': DASHBOARD_URL,
        'unsubscribe_url': UNSUBSCRIBE_URL,
    }
    
    return variables


def render_template(template_content: str, variables: Dict[str, Any]) -> str:
    """
    Render template with variables using simple string substitution.
    
    Args:
        template_content: Template content string
        variables: Dictionary of template variables
        
    Returns:
        Rendered template content
    """
    rendered = template_content
    
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value))
    
    return rendered


def generate_email_content() -> Dict[str, str]:
    """
    Generate complete email content (HTML and text versions).
    
    Returns:
        Dictionary with 'html' and 'text' keys containing email content
    """
    try:
        # Load templates
        html_template = load_template(HTML_TEMPLATE_PATH)
        text_template = load_template(TEXT_TEMPLATE_PATH)
        
        # Generate variables
        variables = generate_template_variables()
        
        # Render templates
        html_content = render_template(html_template, variables)
        text_content = render_template(text_template, variables)
        
        return {
            'html': html_content,
            'text': text_content,
            'subject': f"Daily Market Sentiment Report {variables['date']} - {variables['recommendation']} Signal",
            'variables': variables
        }
        
    except Exception as e:
        raise Exception(f"Error generating email content: {str(e)}")


def generate_preview_email() -> str:
    """
    Generate a preview email for testing purposes.
    
    Returns:
        HTML email content for preview
    """
    try:
        content = generate_email_content()
        return content['html']
    except Exception as e:
        return f"<h1>Error generating preview</h1><p>{str(e)}</p>"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        # Generate preview and save to file
        try:
            content = generate_email_content()
            
            # Save HTML preview
            with open("email_preview.html", "w", encoding="utf-8") as f:
                f.write(content['html'])
            
            # Save text preview
            with open("email_preview.txt", "w", encoding="utf-8") as f:
                f.write(content['text'])
            
            print("✅ Email preview generated successfully!")
            print("   HTML: email_preview.html")
            print("   Text: email_preview.txt")
            print(f"   Subject: {content['subject']}")
            
        except Exception as e:
            print(f"❌ Error generating preview: {e}")
            sys.exit(1)
    
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test email generation and send test email
        try:
            from email_service import send_email
            
            content = generate_email_content()
            
            if len(sys.argv) > 2:
                test_email = sys.argv[2]
                result = send_email(
                    test_email,
                    content['subject'],
                    content['html'],
                    content['text']
                )
                
                if result['success']:
                    print(f"✅ Test email sent successfully to {test_email}")
                    print(f"   Subject: {content['subject']}")
                    print(f"   Message ID: {result.get('message_id', 'N/A')}")
                else:
                    print(f"❌ Failed to send test email: {result.get('error', 'Unknown error')}")
                    sys.exit(1)
            else:
                print("❌ Please provide email address for testing")
                print("   Usage: python email_content_generator.py test your@email.com")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error sending test email: {e}")
            sys.exit(1)
    
    else:
        print("Email Content Generator")
        print("Usage:")
        print("  python email_content_generator.py preview")
        print("  python email_content_generator.py test <email@example.com>")
        sys.exit(1)