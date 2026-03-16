#!/usr/bin/env python3
"""Query China weather forecasts from NMC by city/province or station code."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://www.nmc.cn/rest"
HEADERS = {"User-Agent": "Mozilla/5.0 (Codex China Weather Query Skill)"}
CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".station_cache.json")


def fetch_json(url: str) -> Any:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_name(value: str) -> str:
    text = value.strip().lower()
    text = text.replace(" ", "")
    for token in ("省", "市", "自治区", "特别行政区", "地区", "盟", "州"):
        text = text.replace(token, "")
    return text


def load_stations() -> List[Dict[str, str]]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            ts = payload.get("timestamp", 0)
            if time.time() - ts < CACHE_TTL_SECONDS and isinstance(
                payload.get("stations"), list
            ):
                return payload["stations"]
        except Exception:
            pass

    provinces = fetch_json(f"{BASE_URL}/province")
    stations: List[Dict[str, str]] = []
    for prov in provinces:
        prov_code = prov["code"]
        cities = fetch_json(f"{BASE_URL}/province/{prov_code}")
        for city in cities:
            stations.append(
                {
                    "station_code": city["code"],
                    "province": city["province"],
                    "city": city["city"],
                    "url": city.get("url", ""),
                }
            )
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "stations": stations}, f, ensure_ascii=False)
    except Exception:
        pass
    return stations


def match_station(
    stations: List[Dict[str, str]], city: str, province: Optional[str]
) -> Dict[str, str]:
    city_norm = normalize_name(city)
    province_norm = normalize_name(province) if province else None

    candidates: List[Dict[str, str]] = []
    for s in stations:
        s_city_norm = normalize_name(s["city"])
        s_prov_norm = normalize_name(s["province"])
        if province_norm and province_norm not in s_prov_norm:
            continue
        if s_city_norm == city_norm:
            candidates.append(s)

    if not candidates:
        for s in stations:
            s_city_norm = normalize_name(s["city"])
            s_prov_norm = normalize_name(s["province"])
            if province_norm and province_norm not in s_prov_norm:
                continue
            if city_norm in s_city_norm or s_city_norm in city_norm:
                candidates.append(s)

    if not candidates:
        raise ValueError(f"未找到城市: {city}")

    if len(candidates) == 1:
        return candidates[0]

    exact_prov = [c for c in candidates if province and province in c["province"]]
    if len(exact_prov) == 1:
        return exact_prov[0]

    sample = ", ".join(f"{c['province']}-{c['city']}" for c in candidates[:8])
    raise ValueError(f"城市重名，请指定省份。候选: {sample}")


def safe_get(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def build_result(payload: Dict[str, Any], days: int) -> Dict[str, Any]:
    data = payload.get("data", {})
    real = data.get("real", {})
    predict = data.get("predict", {})
    detail = predict.get("detail", [])[:days]

    forecasts = []
    for item in detail:
        forecasts.append(
            {
                "date": item.get("date"),
                "high_c": safe_get(item, ["day", "weather", "temperature"]),
                "low_c": safe_get(item, ["night", "weather", "temperature"]),
                "day_weather": safe_get(item, ["day", "weather", "info"]),
                "night_weather": safe_get(item, ["night", "weather", "info"]),
                "day_wind": f"{safe_get(item, ['day', 'wind', 'direct'], '')} {safe_get(item, ['day', 'wind', 'power'], '')}".strip(),
                "night_wind": f"{safe_get(item, ['night', 'wind', 'direct'], '')} {safe_get(item, ['night', 'wind', 'power'], '')}".strip(),
                "precipitation": item.get("precipitation"),
            }
        )

    result = {
        "location": {
            "province": safe_get(real, ["station", "province"]),
            "city": safe_get(real, ["station", "city"]),
            "station_code": safe_get(real, ["station", "code"]),
        },
        "publish_time": real.get("publish_time") or predict.get("publish_time"),
        "real_time": {
            "weather": safe_get(real, ["weather", "info"]),
            "temperature_c": safe_get(real, ["weather", "temperature"]),
            "humidity_pct": safe_get(real, ["weather", "humidity"]),
            "rain_mm": safe_get(real, ["weather", "rain"]),
            "wind": f"{safe_get(real, ['wind', 'direct'], '')} {safe_get(real, ['wind', 'power'], '')}".strip(),
        },
        "forecast": forecasts,
    }
    return result


def print_text(result: Dict[str, Any]) -> None:
    loc = result["location"]
    rt = result["real_time"]
    print(f"{loc.get('province', '')}{loc.get('city', '')} ({loc.get('station_code', '')})")
    print(f"发布时间: {result.get('publish_time', '-')}")
    print(
        "实时: "
        f"{rt.get('weather', '-')}, {rt.get('temperature_c', '-')}C, "
        f"湿度 {rt.get('humidity_pct', '-')}%, "
        f"降水 {rt.get('rain_mm', '-')}mm, "
        f"{rt.get('wind', '-')}"
    )
    print("预报:")
    for item in result["forecast"]:
        print(
            f"- {item.get('date', '-')}: "
            f"{item.get('day_weather', '-')}/{item.get('night_weather', '-')}, "
            f"{item.get('low_c', '-')}C ~ {item.get('high_c', '-')}C, "
            f"白天{item.get('day_wind', '-')}, 夜间{item.get('night_wind', '-')}, "
            f"降水{item.get('precipitation', '-')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query China weather by city/province or station.")
    parser.add_argument("--city", help="City or district name, e.g. 北京/朝阳")
    parser.add_argument("--province", help="Province name for disambiguation, e.g. 北京市")
    parser.add_argument("--station", help="Station code, e.g. Wqsps")
    parser.add_argument("--days", type=int, default=3, help="Forecast days (default: 3)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    if not args.station and not args.city:
        parser.error("请提供 --station 或 --city")
    if args.days < 1:
        parser.error("--days 必须 >= 1")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.station:
            station_code = args.station
        else:
            stations = load_stations()
            matched = match_station(stations, args.city, args.province)
            station_code = matched["station_code"]

        payload = fetch_json(f"{BASE_URL}/weather?stationid={station_code}")
        if payload.get("code") not in (0, "0"):
            raise ValueError(f"NMC返回异常: {payload.get('msg', 'unknown error')}")

        result = build_result(payload, args.days)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_text(result)
        return 0
    except (HTTPError, URLError) as exc:
        print(f"网络请求失败: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"输入或查询失败: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"未知错误: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
