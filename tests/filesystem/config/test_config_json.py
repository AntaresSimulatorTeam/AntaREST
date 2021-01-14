from pathlib import Path

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config.json import ConfigJsonBuilder
from api_iso_antares.filesystem.config.model import Config, Simulation


def build_empty_json() -> JSON:
    return {
        "input": {
            "areas": {},
            "bindingconstraints": {"bindingconstraints": {}},
        }
    }


def test_parse_bindings() -> None:
    study_path = Path()
    # Setup josn
    json = build_empty_json()
    json["input"]["bindingconstraints"]["bindingconstraints"] = {
        "bindA": {"id": "bindA"},
        "bindB": {"id": "bindB"},
    }
    config = Config(study_path=study_path, bindings=["bindA", "bindB"])

    # Test
    assert ConfigJsonBuilder.build(study_path, json) == config


def test_parse_outputs() -> None:
    study_path = Path()

    json = build_empty_json()
    json["output"] = {
        1: {
            "about-the-study": {
                "parameters": {
                    "general": {"nbyears": 1, "year-by-year": True},
                    "output": {"synthesis": True},
                }
            },
            "info": {
                "general": {
                    "name": "hello",
                    "mode": "Economy",
                    "date": "2020.12.20 - 14: 56",
                }
            },
        }
    }

    config = Config(
        study_path,
        outputs={
            1: Simulation(
                name="hello",
                date="20201220-1456",
                mode="economy",
                nbyears=1,
                synthesis=True,
                by_year=True,
            )
        },
    )
    assert ConfigJsonBuilder.build(study_path, json) == config
