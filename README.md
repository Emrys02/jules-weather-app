# Weather CLI Tool

A simple command-line tool to fetch and display current weather information for a specified city using the OpenWeatherMap API.

## Features

*   Fetches current weather data (temperature, description, humidity, etc.).
*   Supports specifying city and optional country code.
*   Retrieves API key from command-line argument or environment variable.
*   Displays weather information in a user-friendly format.
*   Logs the execution time of the API call.

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

```bash
python src/weather_cli.py --city London
```

**Specify City and Country:**

```bash
python src/weather_cli.py --city London --country GB
```

**Provide API Key via Argument:**

```bash
python src/weather_cli.py --city Paris --apikey 'your_actual_api_key'
```

**Example Output:**

```
Fetching weather for London, GB...
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
*(Note: Output details like time and weather conditions will vary.)*

## Running Tests

To run the unit tests, navigate to the project's root directory and run:

```bash
python -m unittest discover tests
```

This command will discover and execute all tests located in the `tests` directory.
