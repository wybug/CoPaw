# -*- coding: utf-8 -*-
"""FastAPI application for enterprise skills hub."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import get_host, get_port, get_reload, get_log_level
from .routers import skills, approvals, audit, mcp


logger = logging.getLogger(__name__)


def _init_mcp_store() -> None:
    """Initialize MCP store with pre-populated servers on startup."""
    try:
        from .storage.mcp import MCPStorage
        from .storage.mcp_init import get_pre_populated_servers

        storage = MCPStorage()
        servers = get_pre_populated_servers()

        for server_config in servers:
            slug = server_config["slug"]

            # Check if server already exists
            existing = storage.get_by_slug(slug)
            if existing:
                logger.debug(f"MCP server '{slug}' already exists, skipping")
                continue

            # Create and auto-approve server
            storage.create_pending(
                slug=slug,
                name=server_config["name"],
                description=server_config["description"],
                version=server_config["version"],
                transport=server_config["transport"],
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                url=server_config.get("url", ""),
                env_vars=server_config.get("env_vars", {}),
            )

            # Auto-approve with enterprise signature
            storage.approve_server(
                slug=slug,
                signature="ENTERPRISE_PRE_POPULATED",
                approver="system",
            )

            logger.info(f"Initialized pre-populated MCP server '{slug}'")
    except Exception as e:
        logger.warning("Failed to initialize MCP store: %s", e)


def _init_skills_store() -> None:
    """Initialize skills store with pre-populated skills on startup."""
    try:
        from .storage.skills import SkillStorage
        from .models import SkillBundle
        from .signature import generate_key_pair, SignatureGenerator

        storage = SkillStorage()

        # Check if weather skill already exists
        existing = storage.get_by_slug("weather-query")
        if existing:
            logger.debug("Weather skill already exists, skipping")
            return

        # Weather skill bundle
        skill_bundle = SkillBundle(
            name="weather_query",
            content="""---
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
""",
            files={
                "SKILL.md": """---
name: weather_query
description: Query weather information for locations worldwide
version: 1.0.0
---

# Weather Query Skill

This skill allows the agent to query weather information for any location worldwide.
""",
                "scripts/weather.py": """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"Weather query script.\"\"\"
import urllib.request
import json

def get_weather(city: str) -> str:
    \"\"\"Get weather information for a city.

    Args:
        city: City name

    Returns:
        Weather information as JSON string
    \"\"\"
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
"""
            },
            version="1.0.0",
        )

        # Create pending skill
        storage.create_pending(
            slug="weather-query",
            name="Weather Query",
            description="Query weather information for locations worldwide",
            version="1.0.0",
            bundle=skill_bundle,
        )

        # Generate signature and auto-approve
        private_key, _ = generate_key_pair()
        sig_gen = SignatureGenerator(private_key)

        # Convert bundle to dict for signing
        bundle_dict = {
            "name": skill_bundle.name,
            "content": skill_bundle.content,
            "files": skill_bundle.files,
            "version": skill_bundle.version,
        }
        signature = sig_gen.sign_skill_bundle(bundle_dict)

        storage.approve_skill(
            slug="weather-query",
            signature=signature,
            approver="system",
        )

        logger.info("Initialized pre-populated skill 'weather-query'")
    except Exception as e:
        logger.warning("Failed to initialize skills store: %s", e)


def create_app() -> FastAPI:
    """Create the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="CoPaw Enterprise Skills Hub",
        description="Private skills registry with signature verification",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(skills.router)
    app.include_router(approvals.router)
    app.include_router(audit.router)
    app.include_router(mcp.router)

    # Startup event - initialize MCP store and skills store
    @app.on_event("startup")
    async def startup_event():
        """Run startup tasks."""
        logger.info("Initializing skills store with pre-populated skills")
        _init_skills_store()
        logger.info("Initializing MCP store with pre-populated servers")
        _init_mcp_store()
        logger.info("Startup initialization complete")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "copaw-enterprise-hub"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "CoPaw Enterprise Skills Hub",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


def main() -> None:
    """Run the application."""
    import uvicorn

    # Configure logging
    log_level = get_log_level()
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    host = get_host()
    port = get_port()
    reload = get_reload()

    logger.info("Starting CoPaw Enterprise Skills Hub on %s:%s", host, port)

    uvicorn.run(
        "hub_enterprise.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
        log_level=log_level,
    )
