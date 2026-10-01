from datetime import datetime, timedelta

import requests

HTTP_SESSION = requests.Session()
GEOCODE_CACHE = {}


def geocode_city(city_name):
    if city_name in GEOCODE_CACHE:
        latitude, longitude = GEOCODE_CACHE[city_name]
        return latitude, longitude, None

    try:
        response = HTTP_SESSION.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name, "count": 1},
            timeout=10,
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        if not results:
            return None, None, f"Could not resolve location: {city_name}"

        result = results[0]
        coordinates = (result["latitude"], result["longitude"])
        if len(GEOCODE_CACHE) >= 128:
            GEOCODE_CACHE.pop(next(iter(GEOCODE_CACHE)))
        GEOCODE_CACHE[city_name] = coordinates
        return *coordinates, None

    except requests.RequestException as error:
        return None, None, f"Geocoding API error: {error}"


def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "forecast_days": 3,
        "current": "temperature_2m,wind_speed_10m,precipitation,uv_index",
        "hourly": (
            "temperature_2m,wind_speed_10m,precipitation,"
            "precipitation_probability,uv_index"
        ),
    }

    try:
        response = HTTP_SESSION.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})
        hourly = data.get("hourly", {})

        required_fields = [
            "time",
            "temperature_2m",
            "wind_speed_10m",
            "precipitation",
            "uv_index",
        ]

        if any(current.get(field) is None for field in required_fields):
            return None, "Weather API returned incomplete current-weather data."

        hourly_times = hourly.get("time", [])
        probabilities = hourly.get("precipitation_probability", [])

        try:
            current_index = hourly_times.index(current["time"])
        except ValueError:
            current_index = 0

        if current_index >= len(probabilities):
            return None, "Weather API returned no rain-probability data."

        weather = {
            "current_time": current["time"],
            "temperature": current["temperature_2m"],
            "wind_speed": current["wind_speed_10m"],
            "precipitation": current["precipitation"],
            "precipitation_probability": probabilities[current_index],
            "uv_index": current["uv_index"],
            "hourly_time": hourly_times,
            "hourly_temperature": hourly.get("temperature_2m", []),
            "hourly_wind_speed": hourly.get("wind_speed_10m", []),
            "hourly_precipitation": hourly.get("precipitation", []),
            "hourly_precipitation_probability": probabilities,
            "hourly_uv_index": hourly.get("uv_index", []),
        }

        return weather, None

    except requests.RequestException as error:
        return None, f"Weather API error: {error}"


def get_weather_for_period(weather, time_period, target_hour=None):
    """
    Uses the exact hourly forecast if the user asks for a time such as 12 PM.
    Otherwise uses current weather, or the highest values in the relevant period.
    """

    period = (time_period or "now").lower()

    if period == "now" and target_hour is None:
        return {
            "temperature": weather["temperature"],
            "wind_speed": weather["wind_speed"],
            "precipitation": weather["precipitation"],
            "precipitation_probability": weather["precipitation_probability"],
            "uv_index": weather["uv_index"],
        }, None

    current_date = datetime.fromisoformat(weather["current_time"]).date()
    target_date = current_date + timedelta(days=1) if period == "tomorrow" else current_date

    if target_hour is not None:
        for index, value in enumerate(weather["hourly_time"]):
            timestamp = datetime.fromisoformat(value)

            if timestamp.date() == target_date and timestamp.hour == target_hour:
                return {
                    "temperature": weather["hourly_temperature"][index],
                    "wind_speed": weather["hourly_wind_speed"][index],
                    "precipitation": weather["hourly_precipitation"][index],
                    "precipitation_probability": weather[
                        "hourly_precipitation_probability"
                    ][index],
                    "uv_index": weather["hourly_uv_index"][index],
                }, None

        return None, "No hourly forecast is available for the requested time."

    time_ranges = {
        "morning": (6, 12),
        "afternoon": (12, 17),
        "evening": (17, 21),
        "night": (21, 24),
    }

    start_hour, end_hour = time_ranges.get(period, (0, 24))
    indices = []

    for index, value in enumerate(weather["hourly_time"]):
        timestamp = datetime.fromisoformat(value)

        if (
            timestamp.date() == target_date
            and start_hour <= timestamp.hour < end_hour
        ):
            indices.append(index)

    if not indices:
        return None, "No hourly forecast is available for the requested period."

    def maximum(values):
        selected = [
            values[index]
            for index in indices
            if index < len(values) and values[index] is not None
        ]
        return max(selected) if selected else None

    return {
        "temperature": maximum(weather["hourly_temperature"]),
        "wind_speed": maximum(weather["hourly_wind_speed"]),
        "precipitation": maximum(weather["hourly_precipitation"]),
        "precipitation_probability": maximum(
            weather["hourly_precipitation_probability"]
        ),
        "uv_index": maximum(weather["hourly_uv_index"]),
    }, None