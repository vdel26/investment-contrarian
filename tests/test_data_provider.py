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
    get_fear_and_greed_data,
    get_aaii_sentiment_data,
    FNG_CACHE_PATH,
    AAII_CACHE_PATH
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

    @patch('data_provider.requests.get')
    def test_fetch_and_process_fear_and_greed_success(self, mock_get):
        """Tests successful fetching and processing of Fear & Greed data."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.fng_sample_data
        mock_get.return_value = mock_response

        data = fetch_and_process_fear_and_greed()
        
        self.assertIsNotNone(data)
        self.assertEqual(data['score'], self.fng_sample_data['fear_and_greed']['score'])
        self.assertEqual(len(data['components']), 7)
        
        momentum = next((c for c in data['components'] if c['name'] == 'Stock Price Momentum'), None)
        self.assertIsNotNone(momentum)
        self.assertEqual(momentum['rating'], 'fear')

    @patch('sys.stdout')
    @patch('data_provider.requests.get')
    def test_fetch_and_process_fear_and_greed_request_error(self, mock_get, mock_stdout):
        """Tests the handling of a request exception for Fear & Greed data."""
        mock_get.side_effect = requests.exceptions.RequestException
        data = fetch_and_process_fear_and_greed()
        self.assertIsNone(data)

    @patch('data_provider._fetch_latest_sentiment_from_ycharts', return_value=None)
    @patch('data_provider.pd.read_excel')
    @patch('builtins.open')
    def test_fetch_and_process_aaii_sentiment_success(self, mock_open, mock_read_excel, mock_ycharts):
        """Tests successful processing of AAII sentiment data from a local file."""
        mock_read_excel.return_value = self.aaii_sample_df
        
        data = fetch_and_process_aaii_sentiment()
        
        # Ensure the function attempted to read the Excel file
        mock_open.assert_any_call('sentiment.xls', 'rb')
        self.assertIsNotNone(data)
        self.assertEqual(data['report_date'], '2023-01-05')
        self.assertEqual(data['bullish'], 20.5)
        self.assertEqual(data['bearish'], 50.6)

    @patch('sys.stdout')
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_fetch_and_process_aaii_sentiment_file_not_found(self, mock_open, mock_stdout):
        """Tests the handling of a missing AAII sentiment file."""
        data = fetch_and_process_aaii_sentiment()
        self.assertIsNone(data)

    @patch('builtins.open')
    @patch('json.load')
    def test_get_fear_and_greed_data_success(self, mock_json_load, mock_open):
        """Tests successfully reading F&G data from cache."""
        mock_json_load.return_value = {"score": 50, "rating": "Neutral"}
        data = get_fear_and_greed_data()
        mock_open.assert_called_with(FNG_CACHE_PATH, 'r')
        self.assertEqual(data['score'], 50)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_fear_and_greed_data_not_found(self, mock_open):
        """Tests handling of a missing F&G cache file."""
        data = get_fear_and_greed_data()
        self.assertIn('error', data)

    @patch('json.load', side_effect=json.JSONDecodeError("err", "doc", 0))
    @patch('builtins.open')
    def test_get_fear_and_greed_data_corrupt(self, mock_open, mock_json_load):
        """Tests handling of a corrupt F&G cache file."""
        data = get_fear_and_greed_data()
        self.assertIn('error', data)

    @patch('builtins.open')
    @patch('json.load')
    def test_get_aaii_sentiment_data_success(self, mock_json_load, mock_open):
        """Tests successfully reading AAII data from cache."""
        mock_json_load.return_value = {"bullish": 40.1}
        data = get_aaii_sentiment_data()
        mock_open.assert_called_with(AAII_CACHE_PATH, 'r')
        self.assertEqual(data['bullish'], 40.1)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_aaii_sentiment_data_not_found(self, mock_open):
        """Tests handling of a missing AAII cache file."""
        data = get_aaii_sentiment_data()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main() 