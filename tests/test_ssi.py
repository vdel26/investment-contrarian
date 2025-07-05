"""
Tests for the SSI indicator module.
"""

import unittest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from indicators.ssi import get_cached_data, cache_data, fetch_data, process_data


class TestSSIIndicator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_ssi_data = [
            {
                "level": 85,
                "date": "2024-01",
                "url": "https://example.com",
                "confidence": "high",
                "context": "Test context"
            }
        ]
        
        self.sample_cache_data = {
            "monthly_data": {
                "2024-01": {
                    "level": 85,
                    "date": "2024-01",
                    "url": "https://example.com",
                    "confidence": "high",
                    "context": "Test context"
                }
            },
            "last_updated": "2024-01-15T10:00:00"
        }
    
    def test_get_cached_data_success(self):
        """Test successful cache read."""
        mock_file_content = json.dumps(self.sample_cache_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = get_cached_data()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["level"], 85)
    
    def test_get_cached_data_file_not_found(self):
        """Test cache read when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = get_cached_data()
            self.assertIn("error", result)
            self.assertIn("SSI data not available", result["error"])
    
    def test_cache_data_success(self):
        """Test successful cache write."""
        with patch('indicators.ssi.SSICache') as mock_cache_class:
            mock_cache = MagicMock()
            mock_cache_class.return_value = mock_cache
            
            result = cache_data(self.sample_ssi_data)
            self.assertTrue(result)
            mock_cache.update_cache.assert_called_once()
            mock_cache.save_cache.assert_called_once()
    
    def test_cache_data_error(self):
        """Test cache write error handling."""
        with patch('indicators.ssi.SSICache', side_effect=Exception("Cache error")):
            result = cache_data(self.sample_ssi_data)
            self.assertFalse(result)
    
    @patch.dict(os.environ, {'SERPAPI_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'})
    @patch('indicators.ssi.SSISearcher')
    @patch('indicators.ssi.InvestingScraper')
    @patch('indicators.ssi.SSIExtractor')
    @patch('indicators.ssi.SSICache')
    def test_fetch_data_success(self, mock_cache_class, mock_extractor_class, 
                               mock_scraper_class, mock_searcher_class):
        """Test successful data fetch."""
        # Mock cache
        mock_cache = MagicMock()
        mock_cache.get_missing_months.return_value = ["January 2024"]
        mock_cache.get_cached_data.return_value = self.sample_ssi_data
        mock_cache_class.return_value = mock_cache
        
        # Mock searcher
        mock_searcher = MagicMock()
        mock_searcher.search_investing_ssi_articles.return_value = [{"title": "Test article"}]
        mock_searcher_class.return_value = mock_searcher
        
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.scrape_articles.return_value = [{"content": "Test content"}]
        mock_scraper_class.return_value = mock_scraper
        
        # Mock extractor
        mock_extractor = MagicMock()
        mock_extractor.extract_ssi_values.return_value = ([{"month": "January 2024", "level": 85}], 1, [])
        mock_extractor_class.return_value = mock_extractor
        
        with patch('indicators.ssi.generate_target_months', return_value=["January 2024"]):
            result = fetch_data()
            
            self.assertIsNotNone(result)
            self.assertEqual(result, self.sample_ssi_data)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_fetch_data_missing_env_vars(self):
        """Test fetch data with missing environment variables."""
        result = fetch_data()
        self.assertIsNone(result)
    
    def test_process_data_success(self):
        """Test successful data processing."""
        result = process_data(self.sample_ssi_data)
        self.assertEqual(result, self.sample_ssi_data)
    
    def test_process_data_with_none(self):
        """Test process data with None input."""
        result = process_data(None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()