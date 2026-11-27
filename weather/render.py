"""ASCII rendering helpers for Weather CLI reports."""

from __future__ import annotations

import json

from .api import describe_weather_code


def _unit_label(data: dict) -> str:
    unit = str(data.get("temperature_unit", "celsius")).lower()
    return "F" if unit.startswith("f") else "C"


def render_table(data: dict, city_label: str) -> str:
    """Build a clean ASCII weather report for the given API payload."""
    current = data.get("current", {})
    daily = data.get("daily", {})
    unit = _unit_label(data)

    lines = [f"Weather report: {city_label}", "", "CURRENT"]
    lines.append(f"  Temperature: {current.get('temperature_2m')} {unit}")
    lines.append(f"  Wind speed:  {current.get('wind_speed_10m')} km/h")
    lines.append(f"  Humidity:    {current.get('relative_humidity_2m')}%")
    lines.append(
        f"  Condition:   {describe_weather_code(current.get('weather_code'))}"
    )
    lines.append("")

    dates = daily.get("time", [])
    maxima = daily.get("temperature_2m_max", [])
    minima = daily.get("temperature_2m_min", [])
    codes = daily.get("weather_code", [])
    rain = daily.get("precipitation_probability_max", [])

    rows = []
    for index, date in enumerate(dates):
        condition = (
            describe_weather_code(codes[index])
            if index < len(codes)
            else "Unknown"
        )
        if index < len(rain) and rain[index] is not None:
            condition = f"{condition} ({rain[index]}% rain)"
        if index < len(minima) and index < len(maxima):
            minmax = f"{minima[index]} - {maxima[index]} {unit}"
        else:
            minmax = "-"
        rows.append((str(date), minmax, condition))

    header = ("Date", "Min-Max", "Condition")
    widths = []
    for column in range(3):
        candidates = [len(header[column])] + [len(row[column]) for row in rows]
        widths.append(max(candidates))

    lines.append(f"FORECAST ({len(dates)} day(s))")
    lines.append(
        f"{header[0]:<{widths[0]}}  {header[1]:<{widths[1]}}  {header[2]}"
    )
    lines.append(f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}")
    for row in rows:
        lines.append(f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}")

    return "\n".join(lines)


def render_json(data: dict) -> str:
    """Serialize the raw API payload as pretty-printed JSON."""
    return json.dumps(data, indent=2)
