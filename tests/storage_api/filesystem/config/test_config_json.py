from pathlib import Path

from antarest.common.custom_types import JSON
from antarest.storage_api.filesystem.config.json import ConfigJsonBuilder
from antarest.storage_api.filesystem.config.model import (
    StudyConfig,
    Simulation,
    Area,
    Link,
    Set,
)


def build_empty_json() -> JSON:
    return {
        "input": {
            "areas": {"sets": {}},
            "bindingconstraints": {"bindingconstraints": {}},
            "links": {},
            "thermal": {"clusters": {}},
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
    config = StudyConfig(study_path=study_path, bindings=["bindA", "bindB"])

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

    config = StudyConfig(
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


def test_parse_areas() -> None:
    study_path = Path()

    json = build_empty_json()
    json["input"]["areas"]["fr"] = {
        "optimization": {
            "filtering": {
                "filter-synthesis": "daily, monthly",
                "filter-year-by-year": "hourly, weekly, annual",
            }
        }
    }

    config = StudyConfig(
        study_path,
        areas={
            "fr": Area(
                thermals=[],
                links={},
                filters_year=["hourly", "weekly", "annual"],
                filters_synthesis=["daily", "monthly"],
            )
        },
    )
    assert ConfigJsonBuilder.build(study_path, json) == config


def test_parse_thermal() -> None:
    json = build_empty_json()
    json["input"]["thermal"]["clusters"] = {
        "fr": {"list": {"t1": {}, "t2": {}}}
    }

    assert ConfigJsonBuilder._parse_thermal(json, "fr") == ["t1", "t2"]


def test_parse_links() -> None:
    json = build_empty_json()
    json["input"]["links"] = {
        "fr": {
            "properties": {
                "l1": {
                    "filter-synthesis": "annual",
                    "filter-year-by-year": "hourly",
                }
            }
        }
    }
    link = Link(filters_synthesis=["annual"], filters_year=["hourly"])
    assert ConfigJsonBuilder._parse_links(json, "fr") == {"l1": link}


def test_parse_sets() -> None:
    json = build_empty_json()
    json["input"]["areas"]["sets"] = {
        "hello": {"output": True, "+": ["a", "b"]}
    }

    assert ConfigJsonBuilder._parse_sets(json) == {
        "hello": Set(areas=["a", "b"])
    }
