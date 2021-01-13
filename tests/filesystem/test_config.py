from copy import deepcopy
from pathlib import Path

from api_iso_antares.filesystem.config.files import ConfigPathBuilder
from api_iso_antares.filesystem.config.json import ConfigJsonBuilder
from api_iso_antares.filesystem.config.model import (
    Config,
    Area,
    Link,
    Simulation,
)
from tests.filesystem.utils import extract_sta

link_year = ["hourly"]
thermals = [
    "01_solar",
    "02_wind_on",
    "03_wind_off",
    "04_res",
    "05_nuclear",
    "06_coal",
    "07_gas",
    "08_non-res",
    "09_hydro_pump",
]
area_synthesis = ["daily", "hourly"]
area_year = ["annual"]

config = Config(
    study_path=Path(),
    areas={
        "de": Area(
            thermals=thermals,
            filters_synthesis=["daily", "monthly"],
            filters_year=["hourly", "weekly", "annual"],
            links={"fr": Link([], link_year)},
        ),
        "es": Area(
            thermals=thermals,
            filters_synthesis=["daily", "monthly"],
            filters_year=["hourly", "weekly", "annual"],
            links={"fr": Link([], link_year)},
        ),
        "fr": Area(
            thermals=thermals,
            filters_synthesis=[],
            filters_year=["hourly"],
            links={"it": Link([], link_year)},
        ),
        "it": Area(
            thermals=thermals,
            filters_synthesis=[],
            filters_year=["hourly"],
            links={},
        ),
    },
    outputs={
        1: Simulation(
            name="hello",
            date="20201014-1422",
            mode="economy",
            nbyears=1,
            by_year=True,
            synthesis=True,
        ),
        2: Simulation(
            name="goodbye",
            date="20201014-1425",
            mode="economy",
            nbyears=2,
            by_year=True,
            synthesis=True,
        ),
        3: Simulation(
            name="",
            date="20201014-1427",
            mode="economy",
            nbyears=1,
            by_year=False,
            synthesis=True,
        ),
        4: Simulation(
            name="",
            date="20201014-1430",
            mode="adequacy",
            nbyears=1,
            by_year=False,
            synthesis=True,
        ),
    },
)


def test_build_path(tmp_path: Path, project_path: Path) -> None:
    # Input
    study_path = extract_sta(project_path, tmp_path)

    # Expceted
    exp = deepcopy(config)
    exp.path = exp.root_path = study_path

    assert ConfigPathBuilder.build(study_path=study_path) == exp


def test_build_json() -> None:
    study_path = Path("my-study")

    json = {
        "input": {
            "bindingconstraints": {"bindingconstraints": {}},
            "areas": {
                "de": {
                    "optimization": {
                        "filtering": {
                            "filter-synthesis": "daily, monthly",
                            "filter-year-by-year": "hourly , weekly , annual",
                        }
                    }
                },
                "es": {
                    "optimization": {
                        "filtering": {
                            "filter-synthesis": "daily, monthly",
                            "filter-year-by-year": "hourly , weekly , annual",
                        }
                    }
                },
                "fr": {
                    "optimization": {
                        "filtering": {
                            "filter-synthesis": "",
                            "filter-year-by-year": "hourly",
                        }
                    }
                },
                "it": {
                    "optimization": {
                        "filtering": {
                            "filter-synthesis": "",
                            "filter-year-by-year": "hourly",
                        }
                    }
                },
            },
            "thermal": {
                "clusters": {
                    "de": {"list": {t: {} for t in thermals}},
                    "es": {"list": {t: {} for t in thermals}},
                    "fr": {"list": {t: {} for t in thermals}},
                    "it": {"list": {t: {} for t in thermals}},
                }
            },
            "links": {
                "de": {
                    "properties": {
                        "fr": {
                            "filter-synthesis": "",
                            "filter-year-by-year": "hourly",
                        }
                    }
                },
                "es": {
                    "properties": {
                        "fr": {
                            "filter-synthesis": "",
                            "filter-year-by-year": "hourly",
                        }
                    }
                },
                "fr": {
                    "properties": {
                        "it": {
                            "filter-synthesis": "",
                            "filter-year-by-year": "hourly",
                        }
                    }
                },
                "it": {"properties": {}},
            },
        },
        "output": {
            1: {
                "info": {
                    "general": {
                        "date": "2020.10.14 - 14:22",
                        "mode": "Economy",
                        "name": "hello",
                    },
                },
                "about-the-study": {
                    "parameters": {
                        "general": {"nbyears": 1, "year-by-year": True},
                        "output": {"synthesis": True},
                    }
                },
            },
            2: {
                "info": {
                    "general": {
                        "date": "2020.10.14 - 14:25",
                        "mode": "Economy",
                        "name": "goodbye",
                    }
                },
                "about-the-study": {
                    "parameters": {
                        "general": {"nbyears": 2, "year-by-year": True},
                        "output": {"synthesis": True},
                    }
                },
            },
            3: {
                "info": {
                    "general": {
                        "date": "2020.10.14 - 14:27",
                        "mode": "Economy",
                        "name": "",
                    }
                },
                "about-the-study": {
                    "parameters": {
                        "general": {"nbyears": 1, "year-by-year": False},
                        "output": {"synthesis": True},
                    }
                },
            },
            4: {
                "info": {
                    "general": {
                        "date": "2020.10.14 - 14:30",
                        "mode": "Adequacy",
                        "name": "",
                        "by_year": False,
                        "synthesis": True,
                    }
                },
                "about-the-study": {
                    "parameters": {
                        "general": {"nbyears": 1, "year-by-year": False},
                        "output": {"synthesis": True},
                    }
                },
            },
        },
    }
    exp = deepcopy(config)
    exp.path = exp.root_path = study_path
    assert ConfigJsonBuilder.build(study_path, json) == exp
