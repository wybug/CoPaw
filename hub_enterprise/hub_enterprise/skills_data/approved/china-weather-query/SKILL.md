---
name: china-weather-query
description: Query and scrape China weather forecast information from the National Meteorological Center (NMC) APIs by city or station code. Use when a user asks for China weather, forecasts for a specific city/district, weather comparison across cities, or structured weather output (JSON/text) for downstream processing.
---

# China Weather Query

## Quick Start

Run the bundled script to query current weather + multi-day forecast:

```bash
python scripts/query_weather.py --city 北京
```

Return JSON for programmatic consumption:

```bash
python scripts/query_weather.py --city 上海 --days 5 --format json
```

Disambiguate duplicate city names by province:

```bash
python scripts/query_weather.py --city 朝阳 --province 北京市
```

Query directly by station code:

```bash
python scripts/query_weather.py --station Wqsps
```

## Workflow

1. Parse user input to identify `city`, optional `province`, and required day range.
2. Resolve city to a station code using `scripts/query_weather.py`.
3. Fetch forecast data from NMC endpoint and return concise weather summary.
4. If city is ambiguous, ask user to specify province or list top candidates.
5. If the user asks for machine-readable output, use `--format json`.

## Output Contract

- Include city/province, publish time, real-time weather, and forecast days.
- Keep default response concise (3-day forecast unless user asks otherwise).
- Keep temperatures in Celsius and winds in original Chinese direction/power.
- If lookup fails, return a clear error with suggested next action.

## Resources

- `scripts/query_weather.py`: Query utility for city/station weather lookups.
- `references/api.md`: NMC endpoint map and response field notes.
