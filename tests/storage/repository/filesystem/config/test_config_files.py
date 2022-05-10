from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Link,
    Simulation,
    Set,
    Cluster,
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

    (study_path / "settings").mkdir(parents=True)
    (study_path / "settings/generaldata.ini").touch()

    return study_path


def test_parse_output_parmeters(tmp_path) -> None:
    study = build_empty_files(tmp_path)
    content = """
    [output]
    synthesis = true
    storenewset = true
    archives =
    """
    (study / "settings/generaldata.ini").write_text(content)

    config = FileStudyTreeConfig(
        study_path=study,
        path=study,
        version=-1,
        store_new_set=True,
        study_id="id",
        output_path=study / "output",
    )
    assert ConfigPathBuilder.build(study, "id") == config


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

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        version=-1,
        bindings=["bindA", "bindB"],
        study_id="id",
        output_path=study_path / "output",
    )
    assert ConfigPathBuilder.build(study_path, "id") == config


def test_parse_outputs(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    output_path = study_path / "output/20201220-1456eco-hello/"
    output_path.mkdir(parents=True)

    (output_path / "about-the-study").mkdir()
    file = output_path / "about-the-study/parameters.ini"
    content = """
    [general]
    nbyears = 1
    year-by-year = true
    user-playlist = true
    
    [output]
    synthesis = true
    
    [playlist]
    playlist_year + = 0
    """
    file.write_text(content)

    (output_path / "checkIntegrity.txt").touch()

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="id",
        version=-1,
        output_path=study_path / "output",
        outputs={
            "20201220-1456eco-hello": Simulation(
                name="hello",
                date="20201220-1456",
                mode="economy",
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=False,
                playlist=[1],
            )
        },
    )
    assert ConfigPathBuilder.build(study_path, "id") == config


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
        "hello": Set(areas=["a", "b"], output=True, inverted_set=False)
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

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="id",
        version=-1,
        output_path=study_path / "output",
        areas={
            "fr": Area(
                name="FR",
                thermals=[],
                renewables=[],
                links={},
                filters_year=["hourly", "weekly", "annual"],
                filters_synthesis=["daily", "monthly"],
            )
        },
    )
    assert ConfigPathBuilder.build(study_path, "id") == config


def test_parse_thermal(tmp_path: Path) -> None:
    study_path = build_empty_files(tmp_path)
    (study_path / "input/thermal/clusters/fr").mkdir(parents=True)
    content = """
    [t1]
    name = t1
    
    [t2]
    name = t2
    enabled = false

    [t3]
    name = t3
    enabled = true
    """
    (study_path / "input/thermal/clusters/fr/list.ini").write_text(content)

    assert ConfigPathBuilder._parse_thermal(study_path, "fr") == [
        Cluster(id="t1", name="t1", enabled=True),
        Cluster(id="t2", name="t2", enabled=False),
        Cluster(id="t3", name="t3", enabled=True),
    ]


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
