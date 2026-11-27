"""Open-Meteo API client for Weather CLI.

Two calls are needed to build a report:

1. ``geocode()`` resolves a city name to coordinates via the free
   Open-Meteo geocoding endpoint.
2. ``fetch_forecast()`` downloads current conditions and daily forecast
   arrays from the free forecast endpoint.

Both endpoints are keyless. Everything uses the standard library
(``urllib.request``) so the package has zero third-party runtime
dependencies. Any network or parsing problem is surfaced as a
``WeatherError`` carrying a friendly message.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional
from urllib.request import urlopen

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
    "?name={city}&count=1&language=en&format=json"
)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT_SECONDS = 10

# Browser-like User-Agent: some corporate proxies reject requests without one.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) weather-cli/1.0.0"
)

#: WMO weather interpretation codes mapped to short human phrases.
WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherError(Exception):
    """Raised for any problem while fetching or decoding weather data."""


def describe_weather_code(code: Optional[int]) -> str:
    """Return a human phrase for a WMO weather code (Unknown if unmapped)."""
    return WMO_DESCRIPTIONS.get(code, "Unknown")


def _http_get_json(url: str) -> dict:
    """GET ``url`` (with a browser-like User-Agent) and parse the JSON body."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise WeatherError(
            f"network error while contacting Open-Meteo: {reason}"
        ) from exc
    except TimeoutError as exc:
        raise WeatherError(
            "network error while contacting Open-Meteo: request timed out"
        ) from exc
    try:
        raw = response.read()
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WeatherError(
            "could not decode the response from Open-Meteo"
        ) from exc


def geocode(city: str) -> dict:
    """Resolve a city name to ``{name, country, latitude, longitude}``.

    Raises:
        WeatherError: when the city cannot be found or the request fails.
    """
    if not city or not city.strip():
        raise WeatherError(f"city not found: {city}")
    url = GEOCODING_URL.format(city=urllib.parse.quote(city.strip()))
    payload = _http_get_json(url)
    results = payload.get("results") or []
    if not results:
        raise WeatherError(f"city not found: {city}")
    first = results[0]
    try:
        return {
            "name": first["name"],
            "country": first.get("country", ""),
            "latitude": first["latitude"],
            "longitude": first["longitude"],
        }
    except KeyError as exc:
        raise WeatherError(
            f"unexpected geocoding response for city: {city}"
        ) from exc


def fetch_forecast(
    latitude: float,
    longitude: float,
    days: int = 3,
    unit: str = "c",
) -> dict:
    """Fetch current conditions plus daily forecast arrays for a coordinate.

    ``unit`` is ``"c"`` for Celsius (default) or ``"f"`` for Fahrenheit;
    the latter adds ``temperature_unit=fahrenheit`` to the request.

    Raises:
        WeatherError: when the response is unusable or the request fails.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "forecast_days": days,
        "timezone": "auto",
    }
    if unit == "f":
        params["temperature_unit"] = "fahrenheit"
    url = f"{FORECAST_URL}?{urllib.parse.urlencode(params)}"
    payload = _http_get_json(url)
    if "current" not in payload or "daily" not in payload:
        raise WeatherError("unexpected forecast response from Open-Meteo")
    return payload
