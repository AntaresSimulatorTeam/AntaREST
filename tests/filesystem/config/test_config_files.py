from pathlib import Path

from api_iso_antares.filesystem.config.files import ConfigPathBuilder
from api_iso_antares.filesystem.config.model import (
    Config,
    Area,
    Link,
    Simulation,
)


def build_empty_files(tmp: Path) -> Path:
    study_path = tmp / "my-study"
    (study_path / "input/bindingconstraints/").mkdir(parents=True)
    (study_path / "input/bindingconstraints/bindingconstraints.ini").touch()

    (study_path / "input/areas").mkdir(parents=True)
    (study_path / "input/areas/list.txt").touch()

    return study_path


def test_parse_bindings(tmp_path: Path) -> None:
    # Setup files
    study_path = build_empty_files(tmp_path)
    content = """
    [bindA]
    id = bindA
    
    [bindB]
    id = bindB
    """
    (
        study_path / "input/bindingconstraints/bindingconstraints.ini"
    ).write_text(content)

    config = Config(study_path=study_path, bindings=["bindA", "bindB"])
    assert ConfigPathBuilder.build(study_path) == config


def test_parse_outputs(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "output/20201220-1456eco-hello/about-the-study").mkdir(
        parents=True
    )
    file = (
        study_path
        / "output/20201220-1456eco-hello/about-the-study/parameters.ini"
    )
    content = """
    [general]
    nbyears = 1
    year-by-year = true
    
    [output]
    synthesis = true
    """
    file.write_text(content)

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
    assert ConfigPathBuilder.build(study_path) == config


def test_parse_area(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/areas/list.txt").write_text("FR\n")
    (study_path / "input/areas/fr").mkdir(parents=True)
    content = """
    [filtering]
    filter-synthesis = daily, monthly
    filter-year-by-year = hourly, weekly, annual
    """
    (study_path / "input/areas/fr/optimization.ini").write_text(content)

    config = Config(
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
    assert ConfigPathBuilder.build(study_path) == config


def _parse_thermal(tmp_path: Path) -> None:
    list_ini = json["input"]["thermal"]["clusters"][area]["list"]
    return list(list_ini.keys())


def _parse_links(tmp_path: Path) -> None:
    properties_ini = json["input"]["links"][area]["properties"]
    return {
        link: Link(
            filters_synthesis=Link.split(
                properties_ini[link]["filter-synthesis"]
            ),
            filters_year=Link.split(
                properties_ini[link]["filter-year-by-year"]
            ),
        )
        for link in list(properties_ini.keys())
    }


def _parse_filters_synthesis(tmp_path: Path) -> None:
    filters: str = json["input"]["areas"][area]["optimization"]["filtering"][
        "filter-synthesis"
    ]
    return Link.split(filters)


def _parse_filters_year(tmp_path: Path) -> None:
    filters: str = json["input"]["areas"][area]["optimization"]["filtering"][
        "filter-year-by-year"
    ]
    return Link.split(filters)
