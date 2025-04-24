# Weather CLI Tool

A command-line tool to fetch and display current weather information for a specified location (city, state/region, country) using the OpenWeatherMap API.

## Features

*   Performs geocoding to find latitude/longitude based on city, state code, and country code.
*   Fetches current weather data (temperature, description, humidity, etc.) for the found coordinates.
*   Requires specifying city, state code (e.g., 'CA' for California, 'England' for UK region), and 2-letter country code (e.g., 'US', 'GB').
*   Retrieves API key from command-line argument or environment variable (`OPENWEATHERMAP_API_KEY`).
*   Displays weather information in a user-friendly format.
*   Logs the execution time of API calls.

## Requirements

*   Python 3.13+
*   An API key from [OpenWeatherMap](https://openweathermap.org/appid)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd <repository-directory> # Replace <repository-directory> with the cloned directory name
    ```

2.  **Install dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
    Then install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Key:**
    You need an OpenWeatherMap API key. You can either:
    *   Set the `OPENWEATHERMAP_API_KEY` environment variable:
        ```bash
        export OPENWEATHERMAP_API_KEY='your_api_key'
        ```
        (On Windows, use `set OPENWEATHERMAP_API_KEY=your_api_key` in Command Prompt or `$env:OPENWEATHERMAP_API_KEY='your_api_key'` in PowerShell)
    *   Or provide the key directly using the `--apikey` flag when running the script (see Usage below).

## Usage

Run the script from the project's root directory using `python src/weather_cli.py`.

**Basic Usage (API key set as environment variable):**

Requires `--city`, `--state`, and `--country`.

```bash
# Example for London, England, UK
python src/weather_cli.py --city London --state England --country GB

# Example for San Francisco, California, US
python src/weather_cli.py --city "San Francisco" --state CA --country US
```

**Provide API Key via Argument:**

Also requires `--city`, `--state`, and `--country`.

```bash
python src/weather_cli.py --city Paris --state IDF --country FR --apikey 'your_actual_api_key'
```
*(Note: 'IDF' is for Île-de-France region)*

**Example Output:**

```
Fetching coordinates for London, England, GB...
Coordinates found: Lat=51.5073, Lon=-0.1277
Fetching weather data for Lat=51.5073, Lon=-0.1277...
Execution time for get_weather_data: 0.456 seconds
----------------------------------------
Weather in London, GB at 2023-10-27 10:30:00 BST
----------------------------------------
Description: Scattered clouds
Temperature: 14.5°C
Feels like: 13.8°C
Humidity: 75%
Pressure: 1010 hPa
Wind Speed: 4.1 m/s
----------------------------------------
```
*(Note: Output details like coordinates, time, and weather conditions will vary.)*

## Running Tests

To run the unit tests, navigate to the project's root directory and run:

```bash
python -m unittest discover tests
```

This command will discover and execute all tests located in the `tests` directory.
