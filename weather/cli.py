"""Command-line interface for Weather CLI.

The flow is: geocode the city, fetch the forecast, render the report.
The API layer is reached through the module attribute ``weather_api``
(``from . import api as weather_api``) so tests can monkeypatch
``weather_api.geocode`` / ``weather_api.fetch_forecast`` without any
network access.
"""

from __future__ import annotations

import argparse
import sys

from . import api as weather_api
from .render import render_json, render_table


def _bounded_days(value: str) -> int:
    """argparse type: an integer between 1 and 7 (forecast window)."""
    try:
        days = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid int value: {value!r}"
        ) from None
    if not 1 <= days <= 7:
        raise argparse.ArgumentTypeError("--days must be between 1 and 7")
    return days


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather",
        description=(
            "Fetch current weather and a short forecast from the free "
            "Open-Meteo API (no API key needed)."
        ),
    )
    parser.add_argument(
        "city", help="City name to look up, for example: Tehran"
    )
    parser.add_argument(
        "--days",
        type=_bounded_days,
        default=3,
        metavar="N",
        help="Forecast length in days, 1-7 (default: 3)",
    )
    parser.add_argument(
        "--unit",
        choices=("c", "f"),
        default="c",
        help="Temperature unit: c for Celsius (default) or f for Fahrenheit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the raw API payload as JSON instead of the ASCII table",
    )
    return parser


def main(argv=None) -> int:
    """Entry point; returns 0 on success and exits with status 1 on errors."""
    args = build_parser().parse_args(argv)
    try:
        place = weather_api.geocode(args.city)
        label = place["name"]
        if place.get("country"):
            label = f"{label}, {place['country']}"
        data = weather_api.fetch_forecast(
            place["latitude"],
            place["longitude"],
            days=args.days,
            unit=args.unit,
        )
    except weather_api.WeatherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(render_json(data))
    else:
        print(render_table(data, label))
    return 0
