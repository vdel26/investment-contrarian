import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import pandas as pd

# Add project root to path to allow importing data_provider
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import data_provider

class TestYChartsScraper(unittest.TestCase):
    """Tests for the _fetch_latest_sentiment_from_ycharts helper."""

    @patch('data_provider.requests.get')
    def test_scraper_parses_inline_pattern(self, mock_get):
        """Ensure the inline 'for Wk of' pattern is parsed correctly for all three series."""
        # HTML fragments for three pages with different values
        html_map = {
            'https://ycharts.com/indicators/us_investor_sentiment_bullish': "36.67% for Wk of Jun 12 2025",
            'https://ycharts.com/indicators/us_investor_sentiment_bearish': "33.59% for Wk of Jun 12 2025",
            'https://ycharts.com/indicators/us_investor_sentiment_neutral': "29.74% for Wk of Jun 12 2025",
        }

        def _make_response(url, *args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.text = html_map[url]
            return resp

        mock_get.side_effect = _make_response

        result = data_provider._fetch_latest_sentiment_from_ycharts()
        self.assertIsNotNone(result)
        self.assertEqual(result['date'].strftime('%Y-%m-%d'), '2025-06-12')
        self.assertAlmostEqual(result['bullish'], 36.67)
        self.assertAlmostEqual(result['bearish'], 33.59)
        self.assertAlmostEqual(result['neutral'], 29.74)
        # Values should roughly sum to 100 (allow rounding)
        self.assertAlmostEqual(result['bullish'] + result['bearish'] + result['neutral'], 100.0, places=1)


class TestAAIIMerge(unittest.TestCase):
    """Tests the merging of latest YCharts data into the AAII dataframe."""

    @patch('data_provider._fetch_latest_sentiment_from_ycharts')
    @patch('data_provider.pd.read_excel')
    @patch('builtins.open')
    def test_append_new_week(self, mock_open_file, mock_read_excel, mock_fetch_latest):
        """If YCharts week is newer, it should be appended and become the report_date."""
        # Prepare a historical DataFrame ending on 2025-06-05
        df_hist = pd.DataFrame({
            'Date': pd.to_datetime(['2025-06-05']),
            'Bullish': [0.30],
            'Neutral': [0.25],
            'Bearish': [0.45],
        })
        mock_read_excel.return_value = df_hist

        # Latest YCharts row one week later
        mock_fetch_latest.return_value = {
            'date': pd.Timestamp('2025-06-12').date(),
            'bullish': 36.67,
            'neutral': 29.74,
            'bearish': 33.59,
        }

        # mock the open call used to read the Excel binary
        mock_open_file.return_value = BytesIO(b'dummy')

        result = data_provider.fetch_and_process_aaii_sentiment()
        self.assertIsNotNone(result)
        # Should reflect the new YCharts date
        self.assertEqual(result['report_date'], '2025-06-12')
        # Numbers should be rounded to 1 decimal according to implementation
        self.assertAlmostEqual(result['bullish'], 36.7, places=1)

    @patch('data_provider._fetch_latest_sentiment_from_ycharts')
    @patch('data_provider.pd.read_excel')
    @patch('builtins.open')
    def test_no_append_when_not_newer(self, mock_open_file, mock_read_excel, mock_fetch_latest):
        """If YCharts week is not newer, the dataframe should remain unchanged."""
        df_hist = pd.DataFrame({
            'Date': pd.to_datetime(['2025-06-12']),
            'Bullish': [0.36],
            'Neutral': [0.30],
            'Bearish': [0.34],
        })
        mock_read_excel.return_value = df_hist
        mock_fetch_latest.return_value = {
            'date': pd.Timestamp('2025-06-12').date(),
            'bullish': 36.67,
            'neutral': 29.74,
            'bearish': 33.59,
        }
        mock_open_file.return_value = BytesIO(b'dummy')

        result = data_provider.fetch_and_process_aaii_sentiment()
        self.assertEqual(result['report_date'], '2025-06-12')
        # Because we did not append, bullish should equal 36.0 (from df_hist *100)
        self.assertAlmostEqual(result['bullish'], 36.0, places=1)


if __name__ == '__main__':
    unittest.main() 