# NMC API Notes

## Endpoints

- `GET https://www.nmc.cn/rest/province`
  - Return province list with `code` and `name`.
- `GET https://www.nmc.cn/rest/province/{province_code}`
  - Return city/station list in a province.
  - Key fields: `code` (station code), `province`, `city`, `url`.
- `GET https://www.nmc.cn/rest/weather?stationid={station_code}`
  - Return real-time and forecast weather payload.
  - Main fields:
    - `data.real`: current weather, wind, alerts.
    - `data.predict.detail[]`: daily forecast entries.

## Forecast Fields Used

- `detail[].date`: forecast date.
- `detail[].day.weather.temperature`: daytime temperature (C).
- `detail[].night.weather.temperature`: nighttime temperature (C).
- `detail[].day.weather.info` / `detail[].night.weather.info`: weather description.
- `detail[].day.wind.direct` / `detail[].day.wind.power`: daytime wind.
- `detail[].night.wind.direct` / `detail[].night.wind.power`: nighttime wind.
- `detail[].precipitation`: precipitation hint/value from source.

## Error Handling Guidance

- If city is ambiguous, ask for province (for example: `朝阳` can map to multiple locations).
- If endpoint is unavailable, retry once and then return a concise failure message.
- If user provides station code, skip city resolution and query directly.
