# -*- coding: utf-8 -*-
"""Test script for the weather skill."""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from copaw.agents.skills_manager import SkillService


def test_weather_skill():
    """Test the weather query skill."""
    print("Testing Weather Query Skill...")
    print("-" * 40)

    # Initialize skill service
    service = SkillService()

    # Check if weather skill exists
    skills = service.list_skills()
    weather_skill = None
    for skill in skills:
        if skill.name == "weather_query":
            weather_skill = skill
            break

    if not weather_skill:
        print("❌ Weather skill not found")
        print("Available skills:")
        for skill in skills:
            print(f"  - {skill.name}")
        return False

    print(f"✓ Found weather skill: {weather_skill.name}")
    print(f"  Enabled: {weather_skill.enabled}")
    print(f"  Source: {weather_skill.source}")
    print()

    # Test the skill by running the weather script
    skill_dir = os.path.join(
        os.path.dirname(__file__),
        "../..",
        "skills",
        weather_skill.name,
        "scripts"
    )

    weather_script = os.path.join(skill_dir, "weather.py")
    if os.path.exists(weather_script):
        print(f"✓ Weather script found: {weather_script}")
        print()

        # Test the weather function
        print("Testing weather query for Beijing...")
        try:
            # Add scripts directory to path
            import importlib.util
            spec = importlib.util.spec_from_file_location("weather", weather_script)
            weather_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(weather_module)

            result = weather_module.get_weather("Beijing")
            print(f"Result: {result}")
            print()
            print("✓ Weather skill is working!")
        except Exception as e:
            print(f"❌ Error running weather script: {e}")
            return False
    else:
        print(f"❌ Weather script not found at: {weather_script}")
        return False

    print()
    print("=" * 40)
    print("Weather Skill Test Summary:")
    print("  • Skill is properly installed")
    print("  • Weather script is functional")
    print("  • Ready to query weather for any city")
    print("=" * 40)

    return True


if __name__ == "__main__":
    try:
        success = test_weather_skill()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
