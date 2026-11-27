"""Offline tests for Weather CLI.

Every ``urlopen`` call is monkeypatched with canned Open-Meteo-shaped
payloads, so the suite never touches the network.
"""

import json
import urllib.error

import pytest

from weather import api as weather_api
from weather import cli, render


class FakeResponse:
    """Minimal stand-in for the object returned by urlopen()."""

    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        pass


@pytest.fixture
def sample_geocode_payload():
    return {
        "results": [
            {
                "name": "Tehran",
                "country": "Iran",
                "latitude": 35.6892,
                "longitude": 51.389,
            }
        ]
    }


@pytest.fixture
def sample_forecast_payload():
    return {
        "latitude": 35.6892,
        "longitude": 51.389,
        "temperature_unit": "celsius",
        "current": {
            "temperature_2m": 28.4,
            "relative_humidity_2m": 35,
            "wind_speed_10m": 12.3,
            "weather_code": 0,
        },
        "daily": {
            "time": ["2026-02-01", "2026-02-02", "2026-02-03"],
            "weather_code": [0, 2, 61],
            "temperature_2m_max": [29.5, 28.0, 30.2],
            "temperature_2m_min": [18.0, 17.5, 19.0],
            "precipitation_probability_max": [0, 10, 60],
        },
    }


@pytest.fixture
def fake_place():
    return {
        "name": "Tehran",
        "country": "Iran",
        "latitude": 35.6892,
        "longitude": 51.389,
    }


def test_geocode_parses_first_result(monkeypatch, sample_geocode_payload):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.headers)
        return FakeResponse(json.dumps(sample_geocode_payload).encode("utf-8"))

    monkeypatch.setattr(weather_api, "urlopen", fake_urlopen)

    place = weather_api.geocode("Tehran")

    assert place == {
        "name": "Tehran",
        "country": "Iran",
        "latitude": 35.6892,
        "longitude": 51.389,
    }
    assert "name=Tehran" in captured["url"]
    user_agent = " ".join(
        value
        for key, value in captured["headers"].items()
        if key.lower() == "user-agent"
    )
    assert user_agent.startswith("Mozilla/5.0")


def test_geocode_city_not_found(monkeypatch):
    monkeypatch.setattr(
        weather_api,
        "urlopen",
        lambda request, timeout=None: FakeResponse(b'{"results": []}'),
    )
    with pytest.raises(
        weather_api.WeatherError, match="city not found: Nowhereville"
    ):
        weather_api.geocode("Nowhereville")


def test_wmo_code_mapping():
    assert weather_api.describe_weather_code(0) == "Clear sky"
    assert weather_api.describe_weather_code(61) == "Slight rain"
    assert weather_api.describe_weather_code(95) == "Thunderstorm"


def test_unknown_wmo_code_falls_back():
    assert weather_api.describe_weather_code(42) == "Unknown"


def test_render_table_contains_city_current_and_date_rows(
    sample_forecast_payload,
):
    report = render.render_table(sample_forecast_payload, "Tehran, Iran")
    assert "Tehran, Iran" in report
    assert "CURRENT" in report
    assert "28.4" in report
    assert "2026-02-02" in report
    assert "Condition" in report


def test_render_json_is_valid_json_with_current(sample_forecast_payload):
    parsed = json.loads(render.render_json(sample_forecast_payload))
    assert "current" in parsed
    assert parsed["current"]["temperature_2m"] == 28.4


def test_cli_end_to_end(monkeypatch, capsys, fake_place, sample_forecast_payload):
    monkeypatch.setattr(weather_api, "geocode", lambda city: fake_place)
    monkeypatch.setattr(
        weather_api,
        "fetch_forecast",
        lambda lat, lon, days=3, unit="c": sample_forecast_payload,
    )

    exit_code = cli.main(["Tehran"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Tehran, Iran" in captured.out
    assert "28.4" in captured.out


def test_cli_json_output(monkeypatch, capsys, fake_place, sample_forecast_payload):
    monkeypatch.setattr(weather_api, "geocode", lambda city: fake_place)
    monkeypatch.setattr(
        weather_api,
        "fetch_forecast",
        lambda lat, lon, days=3, unit="c": sample_forecast_payload,
    )

    assert cli.main(["Tehran", "--json"]) == 0

    parsed = json.loads(capsys.readouterr().out)
    assert "current" in parsed


def test_cli_invalid_city_exits_1(monkeypatch, capsys):
    def failing_geocode(city):
        raise weather_api.WeatherError(f"city not found: {city}")

    monkeypatch.setattr(weather_api, "geocode", failing_geocode)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["Nowhereville"])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err
    assert "city not found" in captured.err


def test_cli_days_out_of_range_exits_2(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["Tehran", "--days", "9"])

    assert excinfo.value.code == 2
    assert "--days must be between 1 and 7" in capsys.readouterr().err


def test_fetch_forecast_url_building(monkeypatch, sample_forecast_payload):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        return FakeResponse(json.dumps(sample_forecast_payload).encode("utf-8"))

    monkeypatch.setattr(weather_api, "urlopen", fake_urlopen)

    weather_api.fetch_forecast(35.6892, 51.389, days=3)
    assert "forecast_days=3" in captured["url"]
    assert "temperature_unit" not in captured["url"]
    assert "current=temperature_2m" in captured["url"]
    assert "daily=weather_code" in captured["url"]

    weather_api.fetch_forecast(35.6892, 51.389, days=3, unit="f")
    assert "temperature_unit=fahrenheit" in captured["url"]


def test_network_error_wrapped_as_weather_error(monkeypatch):
    def failing_urlopen(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(weather_api, "urlopen", failing_urlopen)

    with pytest.raises(weather_api.WeatherError, match="network error"):
        weather_api.geocode("Tehran")


def test_fetch_forecast_rejects_unexpected_payload(monkeypatch):
    monkeypatch.setattr(
        weather_api,
        "urlopen",
        lambda request, timeout=None: FakeResponse(b'{"error": true}'),
    )
    with pytest.raises(weather_api.WeatherError, match="unexpected forecast"):
        weather_api.fetch_forecast(35.0, 51.0)
