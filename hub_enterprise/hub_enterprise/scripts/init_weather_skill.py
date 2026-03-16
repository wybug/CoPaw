# -*- coding: utf-8 -*-
"""Initialize weather skill in enterprise hub.

This script creates and approves a weather query skill for the enterprise store.
"""
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path to import hub_enterprise modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hub_enterprise.storage.skills import SkillStorage
from hub_enterprise.signature import generate_key_pair, sign_bundle

logger = logging.getLogger(__name__)


# Weather skill content
WEATHER_SKILL_CONTENT = """---
name: weather_query
description: Query weather information for locations worldwide
version: 1.0.0
---

# Weather Query Skill

This skill allows the agent to query weather information for any location worldwide.

## Usage

The agent can request weather information using natural language:
- "What's the weather like in Tokyo?"
- "Temperature in New York"
- "Is it raining in London?"

## Features

- Current weather conditions
- Temperature (Celsius/Fahrenheit)
- Humidity
- Wind speed and direction
- Weather forecasts

## API

This skill uses a free weather API that doesn't require authentication for basic queries.
"""


WEATHER_SKILL_BUNDLE = {
    "name": "weather_query",
    "content": WEATHER_SKILL_CONTENT,
    "version": "1.0.0",
    "files": {
        "SKILL.md": WEATHER_SKILL_CONTENT,
        "scripts/weather.py": '''#!/usr/bin/env python
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
        # Using wttr.in API (no authentication required)
        url = f"https://wttr.in/{city}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())

            result = {
                "location": f"{data.get('name', {})}, {data.get('country', [])}",
                "temperature": f"{data.get('temp', [])}°C",
                "feels_like": f"{data.get('feels_like', [])}°C",
                "description": data.get('weather_desc', []),
                "humidity": f"{data.get('humidity', [])}%",
                "wind_speed": f"{data.get('windspeed', [])} km/h",
                "visibility": f"{data.get('visibility', [])} km"
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Weather query failed: {str(e)}"})


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        city = sys.argv[1]
        print(get_weather(city))
    else:
        print(get_weather("Beijing"))
'''
    }
}


def init_weather_skill(signature: str = "", approver: str = "system") -> bool:
    """Initialize weather skill in enterprise hub.

    Args:
        signature: Enterprise signature for auto-approved skill.
        approver: Approver name for audit log.

    Returns:
        True if successful.
    """
    storage = SkillStorage()

    # Check if skill already exists
    existing = storage.get_by_slug("weather-query")
    if existing:
        logger.info("Weather skill already exists, skipping")
        return True

    # Create SkillBundle from dict
    from hub_enterprise.models import SkillBundle
    bundle = SkillBundle(
        name=WEATHER_SKILL_BUNDLE["name"],
        content=WEATHER_SKILL_BUNDLE["content"],
        files=WEATHER_SKILL_BUNDLE["files"],
        version=WEATHER_SKILL_BUNDLE["version"],
    )

    # Create pending skill
    storage.create_pending(
        slug="weather-query",
        name="Weather Query",
        description="Query weather information for locations worldwide",
        version="1.0.0",
        bundle=bundle,
    )

    # Generate signature if not provided
    if not signature:
        private_key, _ = generate_key_pair()
        signature = sign_bundle(bundle, private_key)

    # Auto-approve with enterprise signature
    storage.approve_skill(
        slug="weather-query",
        signature=signature,
        approver=approver,
    )

    logger.info("Weather skill initialized successfully")
    return True


def main() -> None:
    """Main entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # For enterprise mode, use a placeholder signature
    # In production, this should be replaced with actual private key signature
    signature = "ENTERPRISE_SIGNED_WEATHER"

    success = init_weather_skill(signature=signature)
    if success:
        print("✓ Weather skill 'weather-query' added to enterprise store")
    else:
        print("✗ Failed to initialize weather skill")
        sys.exit(1)


if __name__ == "__main__":
    main()
