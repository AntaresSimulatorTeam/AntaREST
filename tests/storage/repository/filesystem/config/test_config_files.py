# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import textwrap
import typing as t
from pathlib import Path
from zipfile import ZipFile

import pytest

from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageGroup
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, ThermalCostGeneration
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    _parse_bindings,
    _parse_links_filtering,
    _parse_renewables,
    _parse_sets,
    _parse_st_storage,
    _parse_thermal,
    build,
    parse_outputs,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    DistrictSet,
    FileStudyTreeConfig,
    LinkConfig,
    Simulation,
)
from tests.storage.business.assets import ASSETS_DIR


@pytest.fixture(name="study_path")
def study_path_fixture(tmp_path: Path) -> Path:
    """
    Create a study directory with the minimal structure required to build the configuration.
    """
    study_path = tmp_path / "my-study"
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


def test_parse_output_parameters(study_path: Path) -> None:
    content = """
    [output]
    synthesis = true
    storenewset = true
    archives =
    """
    (study_path / "settings/generaldata.ini").write_text(content)

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        version=0,
        store_new_set=True,
        study_id="id",
        output_path=study_path / "output",
    )
    assert build(study_path, "id") == config


def test_parse_bindings(study_path: Path) -> None:
    # Setup files
    content = """\
    [bindA]
    id = bindA
    name = bindA
    filter-synthesis = hourly
    area_1%area_2 = 4
    area_3.thermal_1 = 5.3%2
    
    [bindB]
    id = bindB
    name = bindB
    type = weekly
    group = My Group
    filter-year-by-year = weekly, annual
    """
    (study_path / "input/bindingconstraints/bindingconstraints.ini").write_text(textwrap.dedent(content))
    study_path.joinpath("study.antares").write_text("[antares] \n version = 870")

    actual = _parse_bindings(study_path)
    expected = [
        BindingConstraint(
            **{
                "name": "bindA",
                "time_step": BindingConstraintFrequency.HOURLY,
                "group": "default",
                "filter_synthesis": [FilterOption.HOURLY],
                "filter_year_by_year": [],
                "terms": [
                    ConstraintTerm(weight=4.0, offset=None, data=LinkTerm(area1="area_1", area2="area_2")),
                    ConstraintTerm(weight=5.3, offset=2, data=ClusterTerm(area="area_3", cluster="thermal_1")),
                ],
            }
        ),
        BindingConstraint(
            **{
                "name": "bindB",
                "time_step": BindingConstraintFrequency.WEEKLY,
                "group": "My Group",
                "filter_synthesis": [],
                "filter_year_by_year": [FilterOption.WEEKLY, FilterOption.ANNUAL],
            }
        ),
    ]
    assert actual == expected


def test_parse_outputs(study_path: Path) -> None:
    output_path = study_path / "output/20201220-1456eco-hello/"
    output_path.mkdir(parents=True)

    (output_path / "about-the-study").mkdir()
    file = output_path / "about-the-study/parameters.ini"
    content = """\
    [general]
    nbyears = 1
    year-by-year = true
    user-playlist = true
    
    [output]
    synthesis = true
    
    [playlist]
    playlist_year + = 0
    """
    file.write_text(textwrap.dedent(content))

    (output_path / "checkIntegrity.txt").touch()

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="id",
        version=0,
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
                xpansion="",
            )
        },
    )
    assert build(study_path, "id") == config


@pytest.mark.parametrize(
    "assets_name, expected",
    [
        (
            "test_output_zip_not_zipped.zip",
            {
                "20230127-1550eco": Simulation(
                    name="",
                    date="20230127-1550",
                    mode="economy",
                    nbyears=1,
                    synthesis=True,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=False,
                    xpansion="",
                ),
                "20230203-1530eco": Simulation(
                    name="",
                    date="20230203-1530",
                    mode="economy",
                    nbyears=1,
                    synthesis=False,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=False,
                    xpansion="1.0.2",
                ),
                "20230203-1531eco": Simulation(
                    name="",
                    date="20230203-1531",
                    mode="economy",
                    nbyears=1,
                    synthesis=False,
                    by_year=False,
                    error=False,
                    playlist=[],
                    archived=True,
                    xpansion="",
                ),
                "20230203-1600eco": Simulation(
                    name="",
                    date="20230203-1600",
                    mode="economy",
                    nbyears=1,
                    synthesis=True,
                    by_year=False,
                    error=True,
                    playlist=[],
                    archived=False,
                    xpansion="",
                ),
            },
        ),
    ],
)
def test_parse_outputs__nominal(tmp_path: Path, assets_name: str, expected: t.Dict[str, t.Any]) -> None:
    """
    This test decompresses a zipped study (stored in the `assets` directory)
    into a temporary directory and executes the parsing of the outputs.
    The result of the analysis is checked to match the expected output data.
    """
    pkg_dir = ASSETS_DIR.joinpath(assets_name)
    with ZipFile(pkg_dir) as zf:
        zf.extractall(tmp_path)
    output_path = tmp_path.joinpath("output")
    actual = parse_outputs(output_path)
    assert actual == expected


def test_parse_sets(study_path: Path) -> None:
    content = """\
    [hello]
    output = true
    + = a
    + = b
    """
    (study_path / "input/areas/sets.ini").write_text(textwrap.dedent(content))

    assert _parse_sets(study_path) == {"hello": DistrictSet(areas=["a", "b"], output=True, inverted_set=False)}


def test_parse_area(study_path: Path) -> None:
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
        version=0,
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
    assert build(study_path, "id") == config


def test_parse_area__extra_area(study_path: Path) -> None:
    """
    Test the case where an extra area is present in the `list.txt` file.

    The extra area should be taken into account with default values to avoid any parsing error.
    """

    (study_path / "input/areas/list.txt").write_text("FR\nDE\n")
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
        version=0,
        output_path=study_path / "output",
        areas={
            "fr": Area(
                name="FR",
                thermals=[],
                renewables=[],
                links={},
                filters_year=["hourly", "weekly", "annual"],
                filters_synthesis=["daily", "monthly"],
            ),
            "de": Area(
                name="DE",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
                st_storages=[],
            ),
        },
    )
    assert build(study_path, "id") == config


# noinspection SpellCheckingInspection
THERMAL_LIST_INI = """\
[t1]
name = t1

[t2]
name = UPPER2
enabled = false

[UPPER3]
name = UPPER3
enabled = true
nominalcapacity = 456.5
"""


def test_parse_thermal(study_path: Path) -> None:
    study_path.joinpath("study.antares").write_text("[antares] \n version = 700")
    ini_path = study_path.joinpath("input/thermal/clusters/fr/list.ini")

    # Error case: `input/thermal/clusters/fr` directory is missing.
    assert not ini_path.parent.exists()
    actual = _parse_thermal(study_path, "fr")
    assert actual == []

    # Error case: `list.ini` is missing.
    ini_path.parent.mkdir(parents=True)
    actual = _parse_thermal(study_path, "fr")
    assert actual == []

    # Nominal case: `list.ini` is found.
    ini_path.write_text(THERMAL_LIST_INI)
    actual = _parse_thermal(study_path, "fr")
    expected = [
        ThermalCluster(name="t1", enabled=True),
        ThermalCluster(name="UPPER2", enabled=False),
        ThermalCluster(name="UPPER3", enabled=True, nominal_capacity=456.5),
    ]
    assert actual == expected


# noinspection SpellCheckingInspection
THERMAL_860_LIST_INI = """\
[t1]
name = t1

[t2]
name = t2
co2 = 156
nh3 = 456
"""


@pytest.mark.parametrize("version", [850, 860, 870])
def test_parse_thermal_860(study_path: Path, version, caplog) -> None:
    study_path.joinpath("study.antares").write_text(f"[antares] \n version = {version}")
    ini_path = study_path.joinpath("input/thermal/clusters/fr/list.ini")
    ini_path.parent.mkdir(parents=True)
    ini_path.write_text(THERMAL_860_LIST_INI)
    with caplog.at_level(logging.WARNING):
        actual = _parse_thermal(study_path, "fr")
    if version == 860:
        expected = [
            ThermalCluster(
                name="t1",
                co2=0,
                nh3=0,
                so2=0,
                nox=0,
                pm2_5=0,
                pm5=0,
                pm10=0,
                nmvoc=0,
                op1=0,
                op2=0,
                op3=0,
                op4=0,
                op5=0,
            ),
            ThermalCluster(
                name="t2",
                co2=156,
                nh3=456,
                so2=0,
                nox=0,
                pm2_5=0,
                pm5=0,
                pm10=0,
                nmvoc=0,
                op1=0,
                op2=0,
                op3=0,
                op4=0,
                op5=0,
            ),
        ]
        assert not caplog.text
    elif version == 870:
        expected = [
            ThermalCluster(
                name="t1",
                co2=0,
                nh3=0,
                so2=0,
                nox=0,
                pm2_5=0,
                pm5=0,
                pm10=0,
                nmvoc=0,
                op1=0,
                op2=0,
                op3=0,
                op4=0,
                op5=0,
                cost_generation=ThermalCostGeneration.SET_MANUALLY,
                efficiency=100,
                variable_o_m_cost=0,
            ),
            ThermalCluster(
                name="t2",
                co2=156,
                nh3=456,
                so2=0,
                nox=0,
                pm2_5=0,
                pm5=0,
                pm10=0,
                nmvoc=0,
                op1=0,
                op2=0,
                op3=0,
                op4=0,
                op5=0,
                cost_generation=ThermalCostGeneration.SET_MANUALLY,
                efficiency=100,
                variable_o_m_cost=0,
            ),
        ]
        assert not caplog.text
    else:
        expected = [ThermalCluster(name="t1")]
        assert "Field nh3 is not a valid field for study version 8.5" in caplog.text
    assert actual == expected


# noinspection SpellCheckingInspection
REWABLES_LIST_INI = """\
[t1]
name = t1

[t2]
name = UPPER2
enabled = false

[UPPER3]
name = UPPER3
enabled = true
nominalcapacity = 456.5
"""


def test_parse_renewables(study_path: Path) -> None:
    study_path.joinpath("study.antares").write_text("[antares] \n version = 810")
    ini_path = study_path.joinpath("input/renewables/clusters/fr/list.ini")

    # Error case: `input/renewables/clusters/fr` directory is missing.
    assert not ini_path.parent.exists()
    actual = _parse_renewables(study_path, "fr")
    assert actual == []

    # Error case: `list.ini` is missing.
    ini_path.parent.mkdir(parents=True)
    actual = _parse_renewables(study_path, "fr")
    assert actual == []

    # Nominal case: `list.ini` is found.
    ini_path.write_text(REWABLES_LIST_INI)
    actual = _parse_renewables(study_path, "fr")
    expected = [
        RenewableCluster(name="t1", enabled=True),
        RenewableCluster(name="UPPER2", enabled=False),
        RenewableCluster(name="UPPER3", enabled=True, nominal_capacity=456.5),
    ]
    assert actual == expected


# noinspection SpellCheckingInspection
ST_STORAGE_LIST_INI = """\
[siemens battery]
name = Siemens Battery
group = Battery
injectionnominalcapacity = 150.0
withdrawalnominalcapacity = 150.0
reservoircapacity = 600.0
efficiency = 0.94
initiallevel = 0
initialleveloptim = True

[grand maison]
name = Grand'Maison
group = PSP_closed
injectionnominalcapacity = 1500.0
withdrawalnominalcapacity = 1800.0
reservoircapacity = 20000.0
efficiency = 0.78
initiallevel = 0.91
initialleveloptim = False
"""


def test_parse_st_storage(study_path: Path) -> None:
    study_path.joinpath("study.antares").write_text("[antares] \n version = 860")
    config_dir = study_path.joinpath("input", "st-storage", "clusters", "fr")
    config_dir.mkdir(parents=True)
    config_dir.joinpath("list.ini").write_text(ST_STORAGE_LIST_INI)
    # noinspection SpellCheckingInspection
    assert _parse_st_storage(study_path, "fr") == [
        STStorage(
            id="siemens battery",
            name="Siemens Battery",
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=150.0,
            withdrawal_nominal_capacity=150.0,
            reservoir_capacity=600.0,
            efficiency=0.94,
            initial_level=0.0,
            initial_level_optim=True,
        ),
        STStorage(
            id="grand maison",
            name="Grand'Maison",
            group=STStorageGroup.PSP_CLOSED,
            injection_nominal_capacity=1500.0,
            withdrawal_nominal_capacity=1800.0,
            reservoir_capacity=20000.0,
            efficiency=0.78,
            initial_level=0.91,
            initial_level_optim=False,
        ),
    ]

    # With a study version anterior to 860, it should always return an empty list
    study_path.joinpath("study.antares").write_text("[antares] \n version = 850")
    assert _parse_st_storage(study_path, "fr") == []


def test_parse_st_storage_with_no_file(tmp_path: Path) -> None:
    assert _parse_st_storage(tmp_path, "") == []


def test_parse_links(study_path: Path) -> None:
    (study_path / "input/links/fr").mkdir(parents=True)
    content = """
    [l1]
    filter-synthesis = annual
    filter-year-by-year = hourly
    """
    (study_path / "input/links/fr/properties.ini").write_text(content)

    link = LinkConfig(filters_synthesis=["annual"], filters_year=["hourly"])
    assert _parse_links_filtering(study_path, "fr") == {"l1": link}
