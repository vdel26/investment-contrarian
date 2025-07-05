"""
Tests for the Fear & Greed indicator module.
"""

import unittest
import json
import os
from unittest.mock import patch, mock_open
from indicators.fear_greed import get_cached_data, cache_data, fetch_data, process_data


class TestFearGreedIndicator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_fng_data = {
            "score": 45,
            "rating": "Neutral",
            "timestamp": "2024-01-15",
            "components": [
                {"name": "Stock Price Momentum", "score": 50, "rating": "Neutral"}
            ]
        }
    
    def test_get_cached_data_success(self):
        """Test successful cache read."""
        mock_file_content = json.dumps(self.sample_fng_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = get_cached_data()
            self.assertEqual(result, self.sample_fng_data)
    
    def test_get_cached_data_file_not_found(self):
        """Test cache read when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = get_cached_data()
            self.assertIn("error", result)
            self.assertIn("Fear & Greed data not available", result["error"])
    
    def test_cache_data_success(self):
        """Test successful cache write."""
        with patch('builtins.open', mock_open()) as mock_file:
            result = cache_data(self.sample_fng_data)
            self.assertTrue(result)
            mock_file.assert_called_once()
    
    def test_cache_data_error(self):
        """Test cache write error handling."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = cache_data(self.sample_fng_data)
            self.assertFalse(result)
    
    @patch('indicators.fear_greed.requests.get')
    def test_fetch_data_success(self, mock_get):
        """Test successful data fetch."""
        mock_response_data = {
            "fear_and_greed": {
                "score": 45,
                "rating": "Neutral",
                "timestamp": "2024-01-15"
            },
            "market_momentum_sp500": {
                "score": 50,
                "rating": "Neutral",
                "value": "100"
            }
        }
        
        mock_response = unittest.mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_data()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 45)
        self.assertEqual(result["rating"], "Neutral")
        # Commentary is not added by fetch_data, but by process_data
        self.assertIsNone(result["commentary"])
    
    @patch('indicators.fear_greed.requests.get')
    def test_fetch_data_network_error(self, mock_get):
        """Test fetch data with network error."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_data()
        self.assertIsNone(result)
    
    def test_process_data_success(self):
        """Test successful data processing."""
        raw_data = {
            "score": 45,
            "rating": "Neutral"
        }
        
        with patch('indicators.fear_greed.generate_fng_commentary', return_value="Test commentary"):
            result = process_data(raw_data)
            
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 45)
            self.assertEqual(result["commentary"], "Test commentary")
    
    def test_process_data_with_none(self):
        """Test process data with None input."""
        result = process_data(None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()