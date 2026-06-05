# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import pytest
from sqlalchemy import Engine, func, select

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.output.model import (
    AreaAndLinkVariables,
    AreaClusterVariables,
    AreaVariables,
    McAllVar,
    McIndVar,
    OutputVariablesList,
)
from antarest.output.storage.v2.repository import DbOutputMetadataV2, OutputV2Repository
from antarest.output.storage.v2.variables_metadata import (
    OUTPUT_VARIABLES_TABLE,
    get_variables_metadata,
    save_variables_metadata,
)


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    init_db_singleton(custom_engine=db_engine)


@pytest.fixture
def output_repo(init_db: None) -> OutputV2Repository:
    return OutputV2Repository()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_output_metadata() -> DbOutputMetadataV2:
    return DbOutputMetadataV2(
        study_id="study_1",
        output_name="output_1",
        archived=False,
        mode="Economy",
        synthesis=True,
        nb_years=1,
        by_year=True,
        start_month=1,
        january_first_weekday=4,
        leap_year=False,
        start_day=1,
        end_day=365,
        first_weekday=1,
    )


def _area(
    name: str,
    ind_vars: list[McIndVar] | None = None,
    all_vars: list[McAllVar] | None = None,
    ind_thermal_clusters: list[AreaClusterVariables] | None = None,
    ind_renewable_clusters: list[AreaClusterVariables] | None = None,
    ind_short_term_storages: list[AreaClusterVariables] | None = None,
) -> tuple[AreaVariables, AreaVariables]:
    """Returns a pair of (mc_ind AreaVariables, mc_all AreaVariables) for convenience."""
    return (
        AreaVariables(
            name=name,
            variables=ind_vars or [],
            thermal_clusters=ind_thermal_clusters or [],
            renewable_clusters=ind_renewable_clusters or [],
            short_term_storages=ind_short_term_storages or [],
        ),
        AreaVariables(
            name=name,
            variables=all_vars or [],
            thermal_clusters=[],
            renewable_clusters=[],
            short_term_storages=[],
        ),
    )


def _count_stored_variables() -> int:
    return db.session.execute(select(func.count()).select_from(OUTPUT_VARIABLES_TABLE)).scalar()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_roundtrip_area_variables(output_repo: OutputV2Repository) -> None:
    """save then get should return the same area-level variables for mc_ind and mc_all."""
    with db():
        output_repo.save_output_metadata(_make_output_metadata())

        variables_list = OutputVariablesList(
            mc_ind=AreaAndLinkVariables(
                areas=[
                    AreaVariables(
                        name="area_a",
                        variables=[McIndVar(name="LOAD", unit="MW"), McIndVar(name="WIND", unit="MW")],
                        thermal_clusters=[],
                        renewable_clusters=[],
                        short_term_storages=[],
                    )
                ],
                links=[],
            ),
            mc_all=AreaAndLinkVariables(
                areas=[
                    AreaVariables(
                        name="area_a",
                        variables=[
                            McAllVar(name="LOAD", unit="MW", stat="EXP"),
                            McAllVar(name="LOAD", unit="MW", stat="STD"),
                        ],
                        thermal_clusters=[],
                        renewable_clusters=[],
                        short_term_storages=[],
                    )
                ],
                links=[],
            ),
        )

        save_variables_metadata("study_1", "output_1", variables_list)
        result = get_variables_metadata("study_1", "output_1")

    assert len(result.mc_ind.areas) == 1
    assert result.mc_ind.areas[0].name == "area_a"
    assert sorted(result.mc_ind.areas[0].variables, key=lambda v: v.name) == [
        McIndVar(name="LOAD", unit="MW"),
        McIndVar(name="WIND", unit="MW"),
    ]

    assert len(result.mc_all.areas) == 1
    assert result.mc_all.areas[0].name == "area_a"
    assert sorted(result.mc_all.areas[0].variables, key=lambda v: (v.name, v.stat)) == [
        McAllVar(name="LOAD", unit="MW", stat="EXP"),
        McAllVar(name="LOAD", unit="MW", stat="STD"),
    ]


def test_roundtrip_cluster_variables(output_repo: OutputV2Repository) -> None:
    """save then get should return the correct thermal, renewable and STS cluster variables."""
    with db():
        output_repo.save_output_metadata(_make_output_metadata())

        variables_list = OutputVariablesList(
            mc_ind=AreaAndLinkVariables(
                areas=[
                    AreaVariables(
                        name="area_a",
                        variables=[],
                        thermal_clusters=[
                            AreaClusterVariables(name="nuclear", variables=[McIndVar(name="PRODUCTION", unit="MWh")])
                        ],
                        renewable_clusters=[
                            AreaClusterVariables(name="wind_farm", variables=[McIndVar(name="PRODUCTION", unit="MWh")])
                        ],
                        short_term_storages=[
                            AreaClusterVariables(name="battery", variables=[McIndVar(name="LEVEL", unit="MWh")])
                        ],
                    )
                ],
                links=[],
            ),
            mc_all=AreaAndLinkVariables(areas=[], links=[]),
        )

        save_variables_metadata("study_1", "output_1", variables_list)
        result = get_variables_metadata("study_1", "output_1")

    area = result.mc_ind.areas[0]
    assert area.name == "area_a"

    assert len(area.thermal_clusters) == 1
    assert area.thermal_clusters[0].name == "nuclear"
    assert area.thermal_clusters[0].variables == [McIndVar(name="PRODUCTION", unit="MWh")]

    assert len(area.renewable_clusters) == 1
    assert area.renewable_clusters[0].name == "wind_farm"
    assert area.renewable_clusters[0].variables == [McIndVar(name="PRODUCTION", unit="MWh")]

    assert len(area.short_term_storages) == 1
    assert area.short_term_storages[0].name == "battery"
    assert area.short_term_storages[0].variables == [McIndVar(name="LEVEL", unit="MWh")]


def test_variable_deduplication(output_repo: OutputV2Repository) -> None:
    """The same variable (same type/name/unit/stat) shared by multiple areas should be stored once."""
    shared_var = McIndVar(name="LOAD", unit="MW")
    variables_list = OutputVariablesList(
        mc_ind=AreaAndLinkVariables(
            areas=[
                AreaVariables(
                    name="area_a",
                    variables=[shared_var],
                    thermal_clusters=[],
                    renewable_clusters=[],
                    short_term_storages=[],
                ),
                AreaVariables(
                    name="area_b",
                    variables=[shared_var],
                    thermal_clusters=[],
                    renewable_clusters=[],
                    short_term_storages=[],
                ),
            ],
            links=[],
        ),
        mc_all=AreaAndLinkVariables(areas=[], links=[]),
    )

    with db():
        output_repo.save_output_metadata(_make_output_metadata())
        save_variables_metadata("study_1", "output_1", variables_list)

        # Both areas share the same variable — only one row in the variable registry
        assert _count_stored_variables() == 1

        result = get_variables_metadata("study_1", "output_1")

    ind_areas = {a.name: a for a in result.mc_ind.areas}
    assert ind_areas["area_a"].variables == [McIndVar(name="LOAD", unit="MW")]
    assert ind_areas["area_b"].variables == [McIndVar(name="LOAD", unit="MW")]


def test_mc_ind_and_mc_all_variables_are_stored_separately(output_repo: OutputV2Repository) -> None:
    """McIndVar and McAllVar with the same name must be stored as distinct rows (different type)."""
    variables_list = OutputVariablesList(
        mc_ind=AreaAndLinkVariables(
            areas=[
                AreaVariables(
                    name="area_a",
                    variables=[McIndVar(name="LOAD", unit="MW")],
                    thermal_clusters=[],
                    renewable_clusters=[],
                    short_term_storages=[],
                )
            ],
            links=[],
        ),
        mc_all=AreaAndLinkVariables(
            areas=[
                AreaVariables(
                    name="area_a",
                    variables=[McAllVar(name="LOAD", unit="MW", stat="EXP")],
                    thermal_clusters=[],
                    renewable_clusters=[],
                    short_term_storages=[],
                )
            ],
            links=[],
        ),
    )

    with db():
        output_repo.save_output_metadata(_make_output_metadata())
        save_variables_metadata("study_1", "output_1", variables_list)

        # One "mc-ind" row and one "mc-all" row = 2 distinct variable rows
        assert _count_stored_variables() == 2

        result = get_variables_metadata("study_1", "output_1")

    assert result.mc_ind.areas[0].variables == [McIndVar(name="LOAD", unit="MW")]
    assert result.mc_all.areas[0].variables == [McAllVar(name="LOAD", unit="MW", stat="EXP")]


def test_empty_variables_list(output_repo: OutputV2Repository) -> None:
    """Saving and reading an empty OutputVariablesList should not raise and return empty results."""
    empty = OutputVariablesList(
        mc_ind=AreaAndLinkVariables(areas=[], links=[]),
        mc_all=AreaAndLinkVariables(areas=[], links=[]),
    )

    with db():
        output_repo.save_output_metadata(_make_output_metadata())
        save_variables_metadata("study_1", "output_1", empty)
        result = get_variables_metadata("study_1", "output_1")

    assert result.mc_ind.areas == []
    assert result.mc_all.areas == []
    assert result.mc_ind.links == []
    assert result.mc_all.links == []


def test_multiple_areas_all_cluster_types(output_repo: OutputV2Repository) -> None:
    """Full roundtrip with two areas, each having all cluster types and mc_ind + mc_all variables."""
    ind_a, all_a = _area(
        "area_a",
        ind_vars=[McIndVar(name="LOAD", unit="MW")],
        all_vars=[McAllVar(name="LOAD", unit="MW", stat="EXP")],
        ind_thermal_clusters=[AreaClusterVariables(name="gas", variables=[McIndVar(name="PRODUCTION", unit="MWh")])],
        ind_renewable_clusters=[
            AreaClusterVariables(name="solar", variables=[McIndVar(name="PRODUCTION", unit="MWh")])
        ],
        ind_short_term_storages=[AreaClusterVariables(name="battery", variables=[McIndVar(name="LEVEL", unit="MWh")])],
    )
    ind_b, all_b = _area(
        "area_b",
        ind_vars=[McIndVar(name="WIND", unit="MW")],
        all_vars=[McAllVar(name="WIND", unit="MW", stat="EXP")],
    )

    variables_list = OutputVariablesList(
        mc_ind=AreaAndLinkVariables(areas=[ind_a, ind_b], links=[]),
        mc_all=AreaAndLinkVariables(areas=[all_a, all_b], links=[]),
    )

    with db():
        output_repo.save_output_metadata(_make_output_metadata())
        save_variables_metadata("study_1", "output_1", variables_list)
        result = get_variables_metadata("study_1", "output_1")

    ind_by_name = {a.name: a for a in result.mc_ind.areas}
    all_by_name = {a.name: a for a in result.mc_all.areas}

    assert set(ind_by_name) == {"area_a", "area_b"}
    assert ind_by_name["area_a"].variables == [McIndVar(name="LOAD", unit="MW")]
    assert ind_by_name["area_a"].thermal_clusters[0] == AreaClusterVariables(
        name="gas", variables=[McIndVar(name="PRODUCTION", unit="MWh")]
    )
    assert ind_by_name["area_a"].renewable_clusters[0] == AreaClusterVariables(
        name="solar", variables=[McIndVar(name="PRODUCTION", unit="MWh")]
    )
    assert ind_by_name["area_a"].short_term_storages[0] == AreaClusterVariables(
        name="battery", variables=[McIndVar(name="LEVEL", unit="MWh")]
    )
    assert ind_by_name["area_b"].variables == [McIndVar(name="WIND", unit="MW")]

    assert all_by_name["area_a"].variables == [McAllVar(name="LOAD", unit="MW", stat="EXP")]
    assert all_by_name["area_b"].variables == [McAllVar(name="WIND", unit="MW", stat="EXP")]
