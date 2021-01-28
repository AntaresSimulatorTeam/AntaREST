from pathlib import Path

from antarest.storage_api.filesystem.config.files import ConfigPathBuilder
from antarest.storage_api.filesystem.config.model import (
    Config,
    Area,
    Link,
    Simulation,
    Set,
)


def build_empty_files(tmp: Path) -> Path:
    study_path = tmp / "my-study"
    (study_path / "input/bindingconstraints/").mkdir(parents=True)
    (study_path / "input/bindingconstraints/bindingconstraints.ini").touch()

    (study_path / "input/areas").mkdir(parents=True)
    (study_path / "input/areas/list.txt").touch()
    (study_path / "input/areas/sets.ini").touch()

    (study_path / "input/links").mkdir(parents=True)
    (study_path / "input/thermal/clusters").mkdir(parents=True)

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


def test_parse_sets(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    content = """
[hello]
output = true
+ = a
+ = b
"""
    (study_path / "input/areas/sets.ini").write_text(content)

    assert ConfigPathBuilder._parse_sets(study_path) == {
        "hello": Set(areas=["a", "b"])
    }


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


def test_parse_thermal(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/thermal/clusters/fr").mkdir(parents=True)
    content = """
    [t1]
    name = t1
    
    [t2]
    name = t2
    """
    (study_path / "input/thermal/clusters/fr/list.ini").write_text(content)

    assert ConfigPathBuilder._parse_thermal(study_path, "fr") == ["t1", "t2"]


def test_parse_links(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/links/fr").mkdir(parents=True)
    content = """
    [l1]
    filter-synthesis = annual
    filter-year-by-year = hourly
    """
    (study_path / "input/links/fr/properties.ini").write_text(content)

    link = Link(filters_synthesis=["annual"], filters_year=["hourly"])
    assert ConfigPathBuilder._parse_links(study_path, "fr") == {"l1": link}
