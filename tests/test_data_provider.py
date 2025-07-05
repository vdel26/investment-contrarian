import unittest
import json
import pandas as pd
import requests
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path to allow importing data_provider
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_provider import (
    fetch_and_process_fear_and_greed, 
    fetch_and_process_aaii_sentiment,
    fetch_and_process_ssi,
    get_fear_and_greed_data,
    get_aaii_sentiment_data,
    get_ssi_data
)

class TestDataProvider(unittest.TestCase):

    def setUp(self):
        """Set up test data."""
        sample_path = os.path.join(os.path.dirname(__file__), 'sample__fearandgreed.json')
        with open(sample_path, 'r') as f:
            self.fng_sample_data = json.load(f)
        
        self.aaii_sample_df = pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-05']),
            'Bullish': [0.205],
            'Neutral': [0.289],
            'Bearish': [0.506],
            'Total': [1.0],
            'Bullish 8-week Mov Avg': [0.25],
            'Bull-Bear Spread': [-0.301],
            'Bullish Average': [0.375],
            'Bullish Average +St. Dev.': [0.479],
            'Bullish Average - St. Dev.': [0.271],
            'S&P 500 Weekly High': [3878.46],
            'S&P 500 Weekly Low': [3820.14],
            'S&P 500 Weekly Close': [3852.36]
        })

    @patch('data_provider.fetch_fear_greed_data')
    @patch('data_provider.process_fear_greed_data')
    @patch('data_provider.cache_fear_greed_data')
    def test_fetch_and_process_fear_and_greed_success(self, mock_cache, mock_process, mock_fetch):
        """Tests successful fetching and processing of Fear & Greed data."""
        mock_fetch.return_value = {"score": 45, "rating": "Neutral"}
        mock_process.return_value = {"score": 45, "rating": "Neutral", "commentary": "Test"}
        mock_cache.return_value = True

        data = fetch_and_process_fear_and_greed()
        
        self.assertIsNotNone(data)
        self.assertEqual(data['score'], 45)
        mock_fetch.assert_called_once()
        mock_process.assert_called_once()
        mock_cache.assert_called_once()

    @patch('data_provider.fetch_fear_greed_data')
    def test_fetch_and_process_fear_and_greed_request_error(self, mock_fetch):
        """Tests the handling of a request exception for Fear & Greed data."""
        mock_fetch.side_effect = Exception("Network error")
        data = fetch_and_process_fear_and_greed()
        self.assertIsNone(data)

    @patch('data_provider.fetch_aaii_raw_data')
    @patch('data_provider.process_aaii_data')
    @patch('data_provider.cache_aaii_data')
    def test_fetch_and_process_aaii_sentiment_success(self, mock_cache, mock_process, mock_fetch):
        """Tests successful processing of AAII sentiment data."""
        mock_fetch.return_value = self.aaii_sample_df
        mock_process.return_value = {
            'report_date': '2023-01-05',
            'bullish': 20.5,
            'bearish': 50.6
        }
        mock_cache.return_value = True
        
        data = fetch_and_process_aaii_sentiment()
        
        self.assertIsNotNone(data)
        self.assertEqual(data['report_date'], '2023-01-05')
        self.assertEqual(data['bullish'], 20.5)
        self.assertEqual(data['bearish'], 50.6)
        mock_fetch.assert_called_once()
        mock_process.assert_called_once()
        mock_cache.assert_called_once()

    @patch('data_provider.fetch_aaii_raw_data')
    def test_fetch_and_process_aaii_sentiment_file_not_found(self, mock_fetch):
        """Tests the handling of a missing AAII sentiment file."""
        mock_fetch.return_value = None
        data = fetch_and_process_aaii_sentiment()
        self.assertIsNone(data)

    @patch('data_provider.get_fear_greed_cached_data')
    def test_get_fear_and_greed_data_success(self, mock_get_cached):
        """Tests successfully reading F&G data from cache."""
        mock_get_cached.return_value = {"score": 50, "rating": "Neutral"}
        data = get_fear_and_greed_data()
        self.assertEqual(data['score'], 50)
        mock_get_cached.assert_called_once()

    @patch('data_provider.get_fear_greed_cached_data')
    def test_get_fear_and_greed_data_not_found(self, mock_get_cached):
        """Tests handling of a missing F&G cache file."""
        mock_get_cached.return_value = {"error": "Fear & Greed data not available"}
        data = get_fear_and_greed_data()
        self.assertIn('error', data)

    @patch('data_provider.get_fear_greed_cached_data')
    def test_get_fear_and_greed_data_corrupt(self, mock_get_cached):
        """Tests handling of a corrupt F&G cache file."""
        mock_get_cached.return_value = {"error": "Fear & Greed data not available"}
        data = get_fear_and_greed_data()
        self.assertIn('error', data)

    @patch('data_provider.get_aaii_cached_data')
    def test_get_aaii_sentiment_data_success(self, mock_get_cached):
        """Tests successfully reading AAII data from cache."""
        mock_get_cached.return_value = {"bullish": 40.1}
        data = get_aaii_sentiment_data()
        self.assertEqual(data['bullish'], 40.1)
        mock_get_cached.assert_called_once()

    @patch('data_provider.get_aaii_cached_data')
    def test_get_aaii_sentiment_data_not_found(self, mock_get_cached):
        """Tests handling of a missing AAII cache file."""
        mock_get_cached.return_value = {"error": "AAII Sentiment data not available"}
        data = get_aaii_sentiment_data()
        self.assertIn('error', data)
        
    @patch('data_provider.get_ssi_cached_data')
    def test_get_ssi_data_success(self, mock_get_cached):
        """Tests successfully reading SSI data from cache."""
        mock_get_cached.return_value = [{"level": 85, "date": "2024-01"}]
        data = get_ssi_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['level'], 85)
        mock_get_cached.assert_called_once()
        
    @patch('data_provider.fetch_ssi_data')
    @patch('data_provider.process_ssi_data') 
    @patch('data_provider.cache_ssi_data')
    def test_fetch_and_process_ssi_success(self, mock_cache, mock_process, mock_fetch):
        """Tests successful fetching and processing of SSI data."""
        mock_fetch.return_value = [{"level": 85}]
        mock_process.return_value = [{"level": 85, "date": "2024-01"}]
        mock_cache.return_value = True
        
        data = fetch_and_process_ssi()
        
        self.assertIsNotNone(data)
        self.assertEqual(data[0]['level'], 85)
        mock_fetch.assert_called_once()
        mock_process.assert_called_once()
        mock_cache.assert_called_once()


if __name__ == '__main__':
    unittest.main() 