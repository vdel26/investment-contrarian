"""
Tests for the AAII indicator module.
"""

import unittest
import json
import pandas as pd
from unittest.mock import patch, mock_open
from indicators.aaii import get_cached_data, cache_data, fetch_data, process_data


class TestAAIIIndicator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_aaii_data = {
            "report_date": "2024-01-15",
            "bullish": 35.2,
            "neutral": 28.5,
            "bearish": 36.3,
            "bullish_avg": 38.0,
            "bearish_avg": 30.5
        }
        
        # Create sample DataFrame for testing
        self.sample_df = pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01', '2024-01-08', '2024-01-15']),
            'Bullish': [0.35, 0.36, 0.352],
            'Neutral': [0.30, 0.29, 0.285],
            'Bearish': [0.35, 0.35, 0.363]
        })
    
    def test_get_cached_data_success(self):
        """Test successful cache read."""
        mock_file_content = json.dumps(self.sample_aaii_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = get_cached_data()
            self.assertEqual(result, self.sample_aaii_data)
    
    def test_get_cached_data_file_not_found(self):
        """Test cache read when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = get_cached_data()
            self.assertIn("error", result)
            self.assertIn("AAII Sentiment data not available", result["error"])
    
    def test_cache_data_success(self):
        """Test successful cache write."""
        with patch('builtins.open', mock_open()) as mock_file:
            result = cache_data(self.sample_aaii_data)
            self.assertTrue(result)
            mock_file.assert_called_once()
    
    def test_cache_data_error(self):
        """Test cache write error handling."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = cache_data(self.sample_aaii_data)
            self.assertFalse(result)
    
    @patch('indicators.aaii.pd.read_excel')
    @patch('builtins.open')
    def test_fetch_data_success(self, mock_open_file, mock_read_excel):
        """Test successful data fetch."""
        mock_read_excel.return_value = self.sample_df
        mock_open_file.return_value.__enter__.return_value = "mock_file"
        
        with patch('indicators.aaii._fetch_latest_sentiment_from_ycharts', return_value=None):
            result = fetch_data()
            
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 3)
            self.assertIn('Date', result.columns)
            self.assertIn('Bullish', result.columns)
    
    @patch('builtins.open')
    def test_fetch_data_file_not_found(self, mock_open_file):
        """Test fetch data when Excel file doesn't exist."""
        mock_open_file.side_effect = FileNotFoundError("File not found")
        
        result = fetch_data()
        self.assertIsNone(result)
    
    def test_process_data_success(self):
        """Test successful data processing."""
        with patch('indicators.aaii.generate_aaii_commentary', return_value="Test commentary"):
            result = process_data(self.sample_df)
            
            self.assertIsNotNone(result)
            self.assertIn("report_date", result)
            self.assertIn("bullish", result)
            self.assertIn("bearish", result)
            self.assertIn("commentary", result)
            self.assertEqual(result["commentary"], "Test commentary")
    
    def test_process_data_with_none(self):
        """Test process data with None input."""
        result = process_data(None)
        self.assertIsNone(result)
    
    def test_process_data_with_empty_df(self):
        """Test process data with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = process_data(empty_df)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()