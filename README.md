# Weather CLI — zero-dependency Python weather app

A polished command-line weather report powered by the free Open-Meteo API. No API key, no third-party packages.

![CI](https://github.com/pixel24-0/weather-cli/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)
![Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)

## Features

- Current conditions: temperature, wind speed, humidity and condition
- Daily forecast for 1-7 days with min/max temperatures and rain probability
- City geocoding by name (no coordinates needed)
- Clean ASCII table output or raw JSON via `--json`
- Celsius or Fahrenheit (`--unit c | f`)
- Zero third-party runtime dependencies: standard library only
- No API key required: Open-Meteo is free and open

## Install

```bash
pip install -e .
```

Or run it from the repository root without installing:

```bash
python -m weather Tehran
```

## Usage

```bash
weather Tehran --days 5 --unit c
weather Berlin --unit f
weather "New York" --days 7 --json
```

## Sample output

```text
$ weather Tehran --days 3
Weather report: Tehran, Iran

CURRENT
  Temperature: 28.4 C
  Wind speed:  12.3 km/h
  Humidity:    35%
  Condition:   Clear sky

FORECAST (3 day(s))
  Date        Min-Max         Condition
  ----------  --------------  ---------------------------
  2026-02-01  18.0 - 29.5 C   Clear sky (0% rain)
  2026-02-02  17.5 - 28.0 C   Partly cloudy (10% rain)
  2026-02-03  19.0 - 30.2 C   Slight rain (60% rain)
```

## Options

| Option   | Values        | Default | Description                            |
|----------|---------------|---------|----------------------------------------|
| `city`   | any city name | -       | City to look up (positional argument)  |
| `--days` | 1-7           | 3       | Forecast length in days                |
| `--unit` | `c` or `f`    | `c`     | Temperature unit (Celsius/Fahrenheit)  |
| `--json` | flag          | off     | Print the raw API payload as JSON      |

## How it works

1. **Geocoding** — the city name is resolved with the free Open-Meteo
   geocoding endpoint (`https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1`).
   The first match provides latitude/longitude and the country.
2. **Forecast** — current conditions and daily arrays are fetched from
   `https://api.open-meteo.com/v1/forecast` with `current=...`, `daily=...`,
   `forecast_days=N` and `timezone=auto`; `temperature_unit=fahrenheit` is
   added when `--unit f` is used.
3. **Rendering** — WMO weather codes are mapped to plain-English phrases and
   the report is formatted with plain `str` formatting (table) or
   `json.dumps` (JSON).

Both endpoints are keyless. Requests use a 10 second timeout and a
browser-like User-Agent, and every network or parse failure is converted
into a friendly `error: ...` message on stderr with exit code 1.

## Testing

```bash
pip install pytest
pip install -e .
pytest -q
```

The test suite is fully offline: every `urlopen` call is monkeypatched with
canned Open-Meteo-shaped payloads, so CI never touches the network.

## Project structure

```text
weather-cli/
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions: pytest on Python 3.11 / 3.12
├── tests/
│   └── test_cli.py         # Offline unit + end-to-end CLI tests
├── weather/
│   ├── __init__.py
│   ├── __main__.py         # python -m weather entry point
│   ├── api.py              # Open-Meteo client + WMO code mapping
│   ├── cli.py              # argparse flow: geocode -> fetch -> render
│   └── render.py           # ASCII table + JSON rendering
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

## Roadmap

- Optional response cache (per city, TTL-based) to avoid repeat calls
- A small config file for default units, days and language
- Hourly forecast view

## License

MIT — Farbod. See [LICENSE](LICENSE).

## مستندات فارسی

- **معرفی:** Weather CLI یک ابزار خط فرمان برای نمایش آب‌وهوای فعلی و پیش‌بینی چند روز آینده است که از سرویس رایگان و بدون کلید Open-Meteo استفاده می‌کند.
- **امکانات:** هیچ وابستگی خارجی ندارد، نام شهر را به مختصات تبدیل می‌کند و دما، باد، رطوبت و پیش‌بینی تا ۷ روز را با خروجی جدول یا JSON نمایش می‌دهد.
- **اجرا:** پس از نصب با `pip install -e .` کافی است دستوری مانند `weather Tehran --days 3` را اجرا کنید؛ اجرای `python -m weather Tehran` هم بدون نصب کار می‌کند.
- **گزینه‌ها:** `--days` برای تعداد روزها، `--unit f` برای فارنهایت و `--json` برای خروجی JSON استفاده می‌شود.
- **تست:** تست‌ها کاملاً بدون اینترنت اجرا می‌شوند و همه درخواست‌های شبکه با داده‌های نمونه جایگزین شده‌اند؛ اجرای آن‌ها با دستور `pytest -q` انجام می‌شود.
- **مجوز:** این پروژه تحت مجوز MIT منتشر شده و متعلق به Farbod است.
