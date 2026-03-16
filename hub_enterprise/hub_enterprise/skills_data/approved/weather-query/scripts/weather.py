#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Weather query script."""
import urllib.request
import json

def get_weather(city: str) -> str:
    """Get weather information for a city.

    Args:
        city: City name

    Returns:
        Weather information as JSON string
    """
    try:
        url = f"https://wttr.in/{city}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())

            result = {
                "location": f"{data.get('name', {})}, {data.get('country', [])}",
                "temperature": f"{data.get('temp', [])}°C",
                "feels_like": f"{data.get('feels_like', [])}°C",
                "description": data.get('weather_desc', []),
                "humidity": f"{data.get('humidity', [])}%",
                "wind_speed": f"{data.get('windspeed', [])} km/h"
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Weather query failed: {str(e)}"})

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(get_weather(sys.argv[1]))
    else:
        print(get_weather("Beijing"))
