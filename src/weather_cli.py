"""
Command-line interface for fetching weather data from OpenWeatherMap.

This script allows users to get the current weather for a specified city
by providing the city name and optionally a country code. It requires an
OpenWeatherMap API key, which can be supplied via a command-line argument
or an environment variable.
"""

import argparse
import os
import requests
from datetime import datetime, timezone
import time
from functools import wraps


def get_api_key(args: argparse.Namespace) -> str:
    """
    Retrieves the OpenWeatherMap API key.

    Prioritizes the key provided via the '--apikey' argument, then checks
    the 'OPENWEATHERMAP_API_KEY' environment variable.

    Args:
        args: The parsed command-line arguments object.

    Returns:
        The API key as a string.

    Raises:
        ValueError: If the API key is not found in either the arguments
                    or the environment variable.
    """
    if args.apikey:
        return args.apikey
    else:
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        if not api_key:
            raise ValueError("API key must be provided either via --apikey argument or OPENWEATHERMAP_API_KEY environment variable")
        return api_key


def log_execution_time(func):
    """
    Decorator to measure and log the execution time of a function.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        print(f"Execution time for {func.__name__}: {elapsed_time:.3f} seconds")
        return result
    return wrapper


def get_coordinates(city: str, state_code: str, country_code: str, api_key: str) -> tuple[float, float]:
    """
    Fetches latitude and longitude for a location using the OpenWeatherMap Geocoding API.

    Args:
        city: The name of the city.
        state_code: The state code (e.g., CA for California).
        country_code: The 2-letter country code (e.g., US).
        api_key: The OpenWeatherMap API key.

    Returns:
        A tuple containing the latitude and longitude (lat, lon).

    Raises:
        ConnectionError: If a network error occurs during the API request.
        ValueError: If the API key is invalid (401), the location is not found,
                    or another API error occurs.
    """
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    location_query = f"{city},{state_code},{country_code}"
    params = {"q": location_query, "limit": 1, "appid": api_key}

    try:
        response = requests.get(base_url, params=params)
        # Check for specific HTTP errors first
        if response.status_code == 401:
             raise ValueError("Invalid API key provided.")
        # Raise for other bad status codes (4xx or 5xx)
        response.raise_for_status()

        data = response.json()

        if not data: # Empty list means location not found
            raise ValueError(f"Location '{location_query}' not found.")

        # Extract lat and lon from the first result
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        return lat, lon

    except requests.exceptions.HTTPError as e:
        # Handle non-401 HTTP errors that raise_for_status() catches
        raise ValueError(f"Geocoding API error or unexpected status code: {e} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error occurred during geocoding: {e}")
    except (KeyError, IndexError) as e:
        # Handle potential issues with the structure of the response JSON
        raise ValueError(f"Error parsing geocoding response: {e}")


@log_execution_time
def get_weather_data(latitude: float, longitude: float, api_key: str) -> dict:
    """
    Fetches weather data from the OpenWeatherMap API for given coordinates.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        api_key: The OpenWeatherMap API key.

    Returns:
        A dictionary containing the weather data JSON response.

    Raises:
        ConnectionError: If a network error occurs during the API request.
        ValueError: If the city is not found (404) or the API key is invalid (401).
        ValueError: If weather data is not found for the coordinates (404)
                    or the API key is invalid (401).
        RuntimeError: For other non-successful HTTP status codes from the API.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"}
    try:
        response = requests.get(base_url, params=params)
        # Raise HTTPError for bad responses (4xx or 5xx) first
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error occurred: {e}")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("Invalid API key provided.")
        elif response.status_code == 404:
            # Changed error message to be generic for coordinates
            raise ValueError("Weather data not found for the provided coordinates.")
        else:
            # Ensure the error message includes the response text for debugging
            raise RuntimeError(f"API error occurred: {e} - {response.text}")


def display_weather_data(data: dict) -> None:
    """
    Processes and displays the weather data in a user-friendly format.

    Args:
        data: A dictionary containing the weather data from the API response.
              Expected to conform to the OpenWeatherMap 'current weather' schema.
    """
    try:
        city = data["name"]
        country = data["sys"]["country"]
        description = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]  # Already in Celsius due to units=metric
        feels_like = data["main"]["feels_like"]  # Already in Celsius
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind_speed = data["wind"]["speed"]  # m/s
        timestamp = data["dt"]

        # Convert timestamp to readable local time
        local_time = datetime.fromtimestamp(timestamp, timezone.utc).astimezone()
        time_str = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")  # Format as desired

        print("-" * 40)
        print(f"Weather in {city}, {country} at {time_str}")
        print("-" * 40)
        print(f"Description: {description}")
        print(f"Temperature: {temp}°C")
        print(f"Feels like: {feels_like}°C")
        print(f"Humidity: {humidity}%")
        print(f"Pressure: {pressure} hPa")
        print(f"Wind Speed: {wind_speed} m/s")
        print("-" * 40)
    except KeyError as e:
        print(f"Error processing weather data: Missing key {e}")
    except Exception as e:  # Catch any other unexpected errors during display
        print(f"An unexpected error occurred during data processing: {e}")


def main() -> None:
    """
    Parses command-line arguments, fetches weather data, and displays it.

    Handles argument parsing, API key retrieval, calls the weather fetching
    function, and then calls the display function. Catches and prints errors
    that occur during the process.
    """
    parser = argparse.ArgumentParser(description="Get weather information for a specific location.")
    parser.add_argument("--city", required=True, help="The name of the city.")
    parser.add_argument("--state", required=True, help="The state code (e.g., CA for California).")
    parser.add_argument("--country", required=True, help="The 2-letter country code (e.g., US).")
    parser.add_argument(
        "--apikey", help="Your OpenWeatherMap API key (optional, can use OPENWEATHERMAP_API_KEY env var)."
    )

    args = parser.parse_args()

    # Use a more specific variable name than 'e' for exceptions

    try:
        api_key = get_api_key(args)
        location_string = f"{args.city}, {args.state}, {args.country}"
        # Fetch coordinates first
        print(f"Fetching coordinates for {location_string}...")
        lat, lon = get_coordinates(args.city, args.state, args.country, api_key)
        print(f"Coordinates found: Lat={lat}, Lon={lon}")

        # Fetch weather data using coordinates
        print(f"Fetching weather data for Lat={lat}, Lon={lon}...")
        weather_data = get_weather_data(lat, lon, api_key)
        display_weather_data(weather_data)

    # The existing exception handlers should catch errors from both functions
    except (ValueError, ConnectionError, RuntimeError) as error:
        print(f"Error: {error}")
    except Exception as unexpected_error: # Catch any other unexpected errors
        print(f"An unexpected error occurred: {unexpected_error}")


if __name__ == "__main__":
    main()
