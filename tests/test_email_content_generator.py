"""
Unit tests for email content generation module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import email_content_generator


class TestEmailContentGenerator(unittest.TestCase):
    """Test cases for email content generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.sample_fng_data = {
            "score": 35,
            "rating": "Fear"
        }
        
        self.sample_aaii_data = {
            "bullish": 25.5,
            "bearish": 45.2,
            "neutral": 29.3
        }
        
        self.sample_ssi_data = [
            {"level": 55.7, "date": "October 2024"},
            {"level": 48.3, "date": "November 2024"},
            {"level": 52.5, "date": "December 2024"}
        ]
        
        self.sample_overall_data = {
            "recommendation": "BUY",
            "commentary": "Extreme bearishness suggests potential market bottom."
        }

    def test_get_recommendation_class(self):
        """Test recommendation CSS class generation."""
        self.assertEqual(email_content_generator.get_recommendation_class("BUY"), "buy")
        self.assertEqual(email_content_generator.get_recommendation_class("SELL"), "sell")
        self.assertEqual(email_content_generator.get_recommendation_class("HOLD"), "hold")
        self.assertEqual(email_content_generator.get_recommendation_class("STRONG BUY"), "strongbuy")

    def test_get_fng_class(self):
        """Test Fear & Greed CSS class generation."""
        self.assertEqual(email_content_generator.get_fng_class(10), "fear-extreme")
        self.assertEqual(email_content_generator.get_fng_class(35), "fear")
        self.assertEqual(email_content_generator.get_fng_class(50), "neutral")
        self.assertEqual(email_content_generator.get_fng_class(65), "greed")
        self.assertEqual(email_content_generator.get_fng_class(85), "greed-extreme")

    def test_get_aaii_class(self):
        """Test AAII spread CSS class generation."""
        self.assertEqual(email_content_generator.get_aaii_class(-25), "bearish")
        self.assertEqual(email_content_generator.get_aaii_class(-15), "fear")
        self.assertEqual(email_content_generator.get_aaii_class(0), "neutral")
        self.assertEqual(email_content_generator.get_aaii_class(15), "greed")
        self.assertEqual(email_content_generator.get_aaii_class(25), "bullish")

    def test_get_ssi_class(self):
        """Test SSI level CSS class generation."""
        self.assertEqual(email_content_generator.get_ssi_class(45), "bearish")
        self.assertEqual(email_content_generator.get_ssi_class(52), "neutral")
        self.assertEqual(email_content_generator.get_ssi_class(57), "bullish")
        self.assertEqual(email_content_generator.get_ssi_class(65), "extreme-bullish")

    def test_format_ssi_history(self):
        """Test SSI history formatting."""
        html, text = email_content_generator.format_ssi_history(self.sample_ssi_data, 3)
        
        # Check HTML format
        self.assertIn("December 2024", html)
        self.assertIn("52.5%", html)
        self.assertIn("ssi-row", html)
        
        # Check text format
        self.assertIn("December 2024: 52.5%", text)
        self.assertIn("November 2024: 48.3%", text)

    def test_format_ssi_history_empty(self):
        """Test SSI history formatting with empty data."""
        html, text = email_content_generator.format_ssi_history([])
        
        self.assertEqual(html, "No historical data available")
        self.assertEqual(text, "No historical data available")

    def test_render_template(self):
        """Test template rendering with variables."""
        template = "Hello {{name}}, your score is {{score}}!"
        variables = {"name": "John", "score": 85}
        
        result = email_content_generator.render_template(template, variables)
        
        self.assertEqual(result, "Hello John, your score is 85!")

    def test_render_template_missing_variable(self):
        """Test template rendering with missing variables."""
        template = "Hello {{name}}, your score is {{score}}!"
        variables = {"name": "John"}
        
        result = email_content_generator.render_template(template, variables)
        
        # Should leave unreplaced variables as-is
        self.assertEqual(result, "Hello John, your score is {{score}}!")

    @patch('email_content_generator.get_fear_and_greed_data')
    @patch('email_content_generator.get_aaii_sentiment_data')
    @patch('email_content_generator.get_ssi_data')
    @patch('email_content_generator.get_overall_analysis_data')
    def test_generate_template_variables(self, mock_overall, mock_ssi, mock_aaii, mock_fng):
        """Test template variables generation."""
        # Mock data
        mock_fng.return_value = self.sample_fng_data
        mock_aaii.return_value = self.sample_aaii_data
        mock_ssi.return_value = self.sample_ssi_data
        mock_overall.return_value = self.sample_overall_data
        
        variables = email_content_generator.generate_template_variables()
        
        # Check basic variables
        self.assertEqual(variables['recommendation'], 'BUY')
        self.assertEqual(variables['fng_score'], 35)
        self.assertEqual(variables['fng_rating'], 'Fear')
        self.assertEqual(variables['aaii_bullish'], '25.5')
        self.assertEqual(variables['aaii_bearish'], '45.2')
        
        # Check calculated values
        self.assertEqual(variables['aaii_spread'], '-19.7')  # 25.5 - 45.2
        self.assertEqual(variables['ssi_latest_value'], '52.5')
        self.assertEqual(variables['ssi_latest_month'], 'December 2024')
        
        # Check CSS classes
        self.assertEqual(variables['recommendation_class'], 'buy')
        self.assertEqual(variables['fng_class'], 'fear')
        self.assertEqual(variables['aaii_class'], 'fear')
        self.assertEqual(variables['ssi_class'], 'neutral')
        
        # Check required fields exist
        self.assertIn('date', variables)
        self.assertIn('timestamp', variables)
        self.assertIn('commentary', variables)
        self.assertIn('dashboard_url', variables)
        self.assertIn('unsubscribe_url', variables)

    @patch('email_content_generator.get_fear_and_greed_data')
    def test_generate_template_variables_with_error(self, mock_fng):
        """Test template variables generation with data error."""
        mock_fng.return_value = {"error": "Failed to load data"}
        
        with self.assertRaises(Exception) as context:
            email_content_generator.generate_template_variables()
        
        self.assertIn("Fear & Greed data error", str(context.exception))

    @patch('email_content_generator.load_template')
    @patch('email_content_generator.generate_template_variables')
    def test_generate_email_content(self, mock_variables, mock_template):
        """Test complete email content generation."""
        # Mock template loading
        mock_template.side_effect = [
            "<html>Hello {{name}}</html>",  # HTML template
            "Hello {{name}}"  # Text template
        ]
        
        # Mock variables
        mock_variables.return_value = {
            'name': 'John',
            'recommendation': 'BUY'
        }
        
        result = email_content_generator.generate_email_content()
        
        # Check return structure
        self.assertIn('html', result)
        self.assertIn('text', result)
        self.assertIn('subject', result)
        self.assertIn('variables', result)
        
        # Check content
        self.assertEqual(result['html'], '<html>Hello John</html>')
        self.assertEqual(result['text'], 'Hello John')
        self.assertIn('BUY', result['subject'])

    @patch('email_content_generator.load_template')
    def test_generate_email_content_template_error(self, mock_template):
        """Test email content generation with template error."""
        mock_template.side_effect = FileNotFoundError("Template not found")
        
        with self.assertRaises(Exception) as context:
            email_content_generator.generate_email_content()
        
        self.assertIn("Error generating email content", str(context.exception))

    def test_load_template_success(self):
        """Test successful template loading."""
        # Create a temporary template file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            f.write("<html>Test Template</html>")
            temp_path = f.name
        
        try:
            content = email_content_generator.load_template(temp_path)
            self.assertEqual(content, "<html>Test Template</html>")
        finally:
            os.unlink(temp_path)

    def test_load_template_not_found(self):
        """Test template loading with missing file."""
        with self.assertRaises(FileNotFoundError):
            email_content_generator.load_template("nonexistent_template.html")

    @patch('email_content_generator.generate_email_content')
    def test_generate_preview_email(self, mock_generate):
        """Test email preview generation."""
        mock_generate.return_value = {
            'html': '<html>Preview</html>',
            'text': 'Preview',
            'subject': 'Test Subject'
        }
        
        result = email_content_generator.generate_preview_email()
        
        self.assertEqual(result, '<html>Preview</html>')

    @patch('email_content_generator.generate_email_content')
    def test_generate_preview_email_error(self, mock_generate):
        """Test email preview generation with error."""
        mock_generate.side_effect = Exception("Test error")
        
        result = email_content_generator.generate_preview_email()
        
        self.assertIn("Error generating preview", result)
        self.assertIn("Test error", result)


class TestEmailContentIntegration(unittest.TestCase):
    """Integration tests for email content generation."""

    def test_aaii_spread_calculation(self):
        """Test AAII spread calculation and classification."""
        # Test bearish scenario
        bearish_data = {"bullish": 20.0, "bearish": 45.0, "neutral": 35.0}
        
        with patch('email_content_generator.get_aaii_sentiment_data', return_value=bearish_data), \
             patch('email_content_generator.get_fear_and_greed_data', return_value={"score": 50, "rating": "Neutral"}), \
             patch('email_content_generator.get_ssi_data', return_value=[]), \
             patch('email_content_generator.get_overall_analysis_data', return_value={"recommendation": "HOLD", "commentary": "Test"}):
            
            variables = email_content_generator.generate_template_variables()
            
            # Should be -25.0 (20.0 - 45.0)
            self.assertEqual(variables['aaii_spread'], '-25.0')
            self.assertEqual(variables['aaii_class'], 'bearish')
            self.assertIn("bearishness", variables['aaii_description'])

    def test_ssi_sentiment_classification(self):
        """Test SSI sentiment classification."""
        test_cases = [
            (45.0, "Bearish", "bearish"),
            (52.0, "Neutral", "neutral"),
            (57.0, "Bullish", "bullish"),
            (65.0, "Extreme Bullish", "extreme-bullish")
        ]
        
        for level, expected_sentiment, expected_class in test_cases:
            ssi_data = [{"level": level, "date": "Test Month"}]
            
            with patch('email_content_generator.get_ssi_data', return_value=ssi_data), \
                 patch('email_content_generator.get_fear_and_greed_data', return_value={"score": 50, "rating": "Neutral"}), \
                 patch('email_content_generator.get_aaii_sentiment_data', return_value={"bullish": 33, "bearish": 33, "neutral": 34}), \
                 patch('email_content_generator.get_overall_analysis_data', return_value={"recommendation": "HOLD", "commentary": "Test"}):
                
                variables = email_content_generator.generate_template_variables()
                
                self.assertEqual(variables['ssi_sentiment'], expected_sentiment)
                self.assertEqual(variables['ssi_class'], expected_class)
                self.assertEqual(variables['ssi_latest_value'], f"{level:.1f}")


if __name__ == '__main__':
    unittest.main()