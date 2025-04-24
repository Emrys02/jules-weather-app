"""
Unit tests for the weather_cli script.

This module contains tests for argument parsing, API key handling,
API data fetching (using mocks), data display formatting, and utility
functions like the execution time logger.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
from io import StringIO
import time
from datetime import datetime, timezone
import inspect
import requests  # Import requests for exception types

# --- Setup sys.path to allow importing src module ---
# Find the current directory of this file (tests/)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# Find the parent directory (project root)
parentdir = os.path.dirname(currentdir)
# Find the src directory
srcdir = os.path.join(parentdir, "src")
# Add src directory to the start of sys.path
if srcdir not in sys.path:
    sys.path.insert(0, srcdir)

# Now import the module components we want to test
from weather_cli import (
    main,
    get_api_key,
    get_coordinates, # Added import
    get_weather_data,
    display_weather_data,
    log_execution_time,
)

# Sample data for mocking API responses (formatted like black)
SAMPLE_WEATHER_DATA = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [
        {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
    ],
    "base": "stations",
    "main": {
        "temp": 15.0,
        "feels_like": 14.5,
        "temp_min": 13.0,
        "temp_max": 17.0,
        "pressure": 1012,
        "humidity": 60,
    },
    "visibility": 10000,
    "wind": {"speed": 3.6, "deg": 80},
    "clouds": {"all": 0},
    "dt": 1678886400,  # Represents 2023-03-15 12:00:00 UTC
    "sys": {
        "type": 1,
        "id": 1414,
        "country": "GB",
        "sunrise": 1678859400,
        "sunset": 1678902600,
    },
    "timezone": 0,  # Offset in seconds from UTC
    "id": 2643743,
    "name": "London",
    "cod": 200,
}


class TestWeatherCLI(unittest.TestCase):
    """Test suite for the weather CLI application."""

    # --- Tests for argument parsing and API key retrieval ---

    # Note: The duplicate test_main_basic_args seems like an artifact. Removing one.
    @patch('argparse.ArgumentParser.parse_args')
    @patch('weather_cli.get_api_key')
    @patch('weather_cli.get_coordinates') # Added patch
    @patch('weather_cli.get_weather_data')
    @patch('weather_cli.display_weather_data')
    def test_main_integration(self, mock_display, mock_get_weather, mock_get_coords, mock_get_key, mock_parse_args):
        """Test main function integrates components including coordinate lookup."""
        # Updated mock args to include state
        mock_parse_args.return_value = MagicMock(
            city='TestCity', state='TS', country='TC', apikey='testkey'
        )
        mock_get_key.return_value = 'testkey'
        # Set return value for the mocked get_coordinates
        mock_get_coords.return_value = (51.5, -0.1) # Sample coordinates
        mock_get_weather.return_value = SAMPLE_WEATHER_DATA

        main()

        # Verify that the main components are called correctly
        mock_parse_args.assert_called_once()
        mock_get_key.assert_called_once_with(mock_parse_args.return_value)
        # Verify get_coordinates is called with city, state, country, key
        mock_get_coords.assert_called_once_with('TestCity', 'TS', 'TC', 'testkey')
        # Verify get_weather_data is called with lat, lon, key
        mock_get_weather.assert_called_once_with(51.5, -0.1, 'testkey')
        mock_display.assert_called_once_with(SAMPLE_WEATHER_DATA)

    # Add a test for main handling errors from get_coordinates
    @patch('argparse.ArgumentParser.parse_args')
    @patch('weather_cli.get_api_key')
    @patch('weather_cli.get_coordinates')
    @patch('builtins.print') # To capture error output
    def test_main_handles_get_coordinates_error(self, mock_print, mock_get_coords, mock_get_key, mock_parse_args):
        """Test main function handles errors raised by get_coordinates."""
        mock_parse_args.return_value = MagicMock(city='BadCity', state='BS', country='BC', apikey='key')
        mock_get_key.return_value = 'key'
        # Simulate get_coordinates raising a ValueError (e.g., location not found)
        mock_get_coords.side_effect = ValueError("Location 'BadCity,BS,BC' not found.")

        main()

        mock_get_coords.assert_called_once_with('BadCity', 'BS', 'BC', 'key')
        # Verify the error message is printed
        self.assertTrue(any("Error: Location 'BadCity,BS,BC' not found." in str(call_args) for call_args in mock_print.call_args_list))


    def test_get_api_key_from_arg(self):
        """Test get_api_key retrieves key from command line arguments."""
        args = MagicMock(apikey="arg_key")
        self.assertEqual(get_api_key(args), "arg_key")

    @patch.dict(os.environ, {"OPENWEATHERMAP_API_KEY": "env_key"}, clear=True)
    def test_get_api_key_from_env(self):
        """Test get_api_key retrieves key from environment variable when arg is absent."""
        args = MagicMock(apikey=None)
        self.assertEqual(get_api_key(args), "env_key")

    @patch.dict(os.environ, {}, clear=True)  # Ensure env var is not set
    def test_get_api_key_no_key_raises_error(self):
        """Test get_api_key raises ValueError when no key is found in args or env."""
        args = MagicMock(apikey=None)
        with self.assertRaisesRegex(
            ValueError, "API key must be provided"
        ):
            get_api_key(args)

    # --- Tests for get_coordinates (Geocoding API interaction) ---

    @patch("requests.get")
    def test_get_coordinates_success(self, mock_get):
        """Test get_coordinates handles a successful Geocoding API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate Geocoding API response structure
        mock_response.json.return_value = [{"lat": 51.5074, "lon": -0.1278, "name": "London", "country": "GB"}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        lat, lon = get_coordinates("London", "ENG", "GB", "fakekey")
        self.assertEqual((lat, lon), (51.5074, -0.1278))
        mock_get.assert_called_once_with(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": "London,ENG,GB", "limit": 1, "appid": "fakekey"},
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.get")
    def test_get_coordinates_location_not_found(self, mock_get):
        """Test get_coordinates handles an empty response (location not found)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [] # Empty list signifies not found
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "Location 'Nowhere,NV,US' not found"):
            get_coordinates("Nowhere", "NV", "US", "fakekey")

    @patch("requests.get")
    def test_get_coordinates_invalid_api_key(self, mock_get):
        """Test get_coordinates handles a 401 Invalid API Key error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        # Simulate requests.raise_for_status() behavior for 401 (although we check status directly)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "Invalid API key provided"):
            get_coordinates("London", "ENG", "GB", "invalidkey")

    @patch("requests.get")
    def test_get_coordinates_network_error(self, mock_get):
        """Test get_coordinates handles a requests.RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Network issue")

        with self.assertRaisesRegex(
            ConnectionError, "Network error occurred during geocoding: Network issue"
        ):
            get_coordinates("London", "ENG", "GB", "fakekey")

    @patch("requests.get")
    def test_get_coordinates_other_http_error(self, mock_get):
        """Test get_coordinates handles other HTTP errors (e.g., 500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(
            ValueError, "Geocoding API error or unexpected status code: .*Server Error"
        ):
            get_coordinates("London", "ENG", "GB", "fakekey")

    @patch("requests.get")
    def test_get_coordinates_json_parsing_error(self, mock_get):
        """Test get_coordinates handles errors parsing the JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Malformed JSON or unexpected structure
        mock_response.json.return_value = [{"latitude": 51.5}] # Missing 'lon' or 'lat'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "Error parsing geocoding response:"):
            get_coordinates("London", "ENG", "GB", "fakekey")


    # --- Tests for get_weather_data (API interaction) ---

    @patch("requests.get")
    def test_get_weather_data_success(self, mock_get):
        """Test get_weather_data handles a successful API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_WEATHER_DATA
        mock_response.raise_for_status = MagicMock()  # Mock this method
        mock_get.return_value = mock_response

        # Call with latitude and longitude
        data = get_weather_data(51.5085, -0.1257, "fakekey")
        self.assertEqual(data, SAMPLE_WEATHER_DATA)
        # Verify the correct API call parameters using lat/lon
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": 51.5085, "lon": -0.1257, "appid": "fakekey", "units": "metric"},
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.get")
    def test_get_weather_data_not_found_for_coords(self, mock_get):
        """Test get_weather_data handles a 404 for coordinates not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        # Simulate requests.raise_for_status() behavior for 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        # Changed regex to match the new error message
        with self.assertRaisesRegex(ValueError, "Weather data not found for the provided coordinates"):
            get_weather_data(99.99, -99.99, "fakekey") # Use dummy coordinates

    @patch("requests.get")
    def test_get_weather_data_invalid_api_key(self, mock_get):
        """Test get_weather_data handles a 401 Invalid API Key error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "Invalid API key provided"):
            get_weather_data(51.5, -0.1, "invalidkey") # Use dummy coordinates

    @patch("requests.get")
    def test_get_weather_data_network_error(self, mock_get):
        """Test get_weather_data handles a requests.RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Network issue")

        with self.assertRaisesRegex(
            ConnectionError, "Network error occurred: Network issue"
        ):
            get_weather_data(51.5, -0.1, "fakekey") # Use dummy coordinates

    @patch("requests.get")
    def test_get_weather_data_other_http_error(self, mock_get):
        """Test get_weather_data handles other HTTP errors (e.g., 500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(
            RuntimeError, "API error occurred: .*Internal Server Error"
        ):
            get_weather_data(51.5, -0.1, "fakekey") # Use dummy coordinates

    # --- Tests for display_weather_data (Output formatting) ---

    @patch("builtins.print")
    def test_display_weather_data_success(self, mock_print):
        """Test display_weather_data formats and prints expected output."""
        display_weather_data(SAMPLE_WEATHER_DATA)

        # Consolidate mock print calls into a single string for easier checking
        output = "\n".join(
            [str(call_args[0][0]) for call_args in mock_print.call_args_list]
        )

        # Check for key pieces of information in the output
        self.assertIn("Weather in London, GB", output)
        # Check timestamp - exact format depends on local timezone during test run
        # We check for the date part which should be consistent.
        self.assertIn("2023-03-15", output)  # Check date part
        # self.assertIn("12:00:00", output) # Time part depends on timezone
        self.assertIn("Description: Clear sky", output)
        self.assertIn("Temperature: 15.0°C", output)
        self.assertIn("Feels like: 14.5°C", output)
        self.assertIn("Humidity: 60%", output)
        self.assertIn("Pressure: 1012 hPa", output)
        self.assertIn("Wind Speed: 3.6 m/s", output)
        self.assertIn("-" * 40, output)  # Check for separator lines

    @patch("builtins.print")
    def test_display_weather_data_missing_key(self, mock_print):
        """Test display_weather_data handles missing keys in API data gracefully."""
        incomplete_data = {"name": "TestCity"}  # Missing most keys
        display_weather_data(incomplete_data)
        output = "\n".join(
            [str(call_args[0][0]) for call_args in mock_print.call_args_list]
        )
        # Check that an error message mentioning the missing key is printed
        self.assertIn("Error processing weather data: Missing key 'sys'", output)

    # --- Tests for log_execution_time decorator ---

    @patch("builtins.print")
    @patch("time.monotonic")
    def test_log_execution_time_decorator(self, mock_monotonic, mock_print):
        """Test the log_execution_time decorator calculates and logs time."""
        mock_monotonic.side_effect = [100.0, 102.5]  # Start time, End time

        @log_execution_time
        def dummy_function():
            """A dummy function to test the decorator."""
            return "done"

        result = dummy_function()

        self.assertEqual(result, "done")  # Ensure original function still works

        # Verify that the execution time was printed correctly
        log_message = "Execution time for dummy_function: 2.500 seconds"
        found_log = any(
            log_message in str(call_args[0][0])
            for call_args in mock_print.call_args_list
        )
        self.assertTrue(found_log, f"Log message '{log_message}' not found in print output.")


if __name__ == "__main__":
    # Allows running tests directly from the command line
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
