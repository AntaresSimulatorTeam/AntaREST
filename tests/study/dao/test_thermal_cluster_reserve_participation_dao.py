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
from collections.abc import Iterable

import pytest

from antarest.core.exceptions import AreaNotFound, ThermalClusterReserveParticipationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveDefinitionId, ReserveType
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _participation(reserve_id: str, **overrides: float) -> ThermalClusterReserveParticipation:
    return ThermalClusterReserveParticipation(
        id=reserve_id,
        max_power=overrides.get("max_power", 20.0),
        max_power_off=overrides.get("max_power_off", 10.0),
        participation_cost=overrides.get("participation_cost", 1.0),
        participation_cost_off=overrides.get("participation_cost_off", 2.0),
    )


def _setup(
    dao: StudyDao,
    area_id: str,
    *,
    clusters: Iterable[str] = ("gas_cluster",),
    reserves: Iterable[str] = ("R1", "R2", "Reserve 1", "unknown"),
) -> None:
    save_area(dao, area_id)
    dao.save_thermals({area_id: [ThermalCluster(id=cid, name=cid) for cid in clusters]})
    dao.save_reserve_definitions({area_id: [ReserveDefinition(id=rid, type=ReserveType.UP) for rid in reserves]})


def test_save_and_retrieve(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")

    participation = _participation("Reserve 1")
    dao_10_0.save_thermal_cluster_reserve_participations({"paris": {"gas_cluster": [participation]}})

    fetched = dao_10_0.get_thermal_cluster_reserve_participation("paris", "gas_cluster", "Reserve 1")
    assert fetched == participation


def test_save_updates_existing(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")

    dao_10_0.save_thermal_cluster_reserve_participations(
        {"paris": {"gas_cluster": [_participation("R1", max_power=10.0)]}}
    )
    dao_10_0.save_thermal_cluster_reserve_participations(
        {"paris": {"gas_cluster": [_participation("R1", max_power=99.0)]}}
    )

    fetched = dao_10_0.get_thermal_cluster_reserve_participation("paris", "gas_cluster", "R1")
    assert fetched.max_power == 99.0


def test_save_raises_area_not_found_when_area_missing(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        dao_10_0.save_thermal_cluster_reserve_participations({"nonexistent": {"gas_cluster": [_participation("R1")]}})


def test_participation_exists(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris", clusters=("gas_cluster", "other_cluster"))
    dao_10_0.save_thermal_cluster_reserve_participations({"paris": {"gas_cluster": [_participation("R1")]}})

    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R1") is True
    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "unknown") is False
    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "other_cluster", "R1") is False


def test_participation_exists_on_missing_area(dao_10_0: StudyDao) -> None:
    assert dao_10_0.thermal_cluster_reserve_participation_exists("nonexistent", "c", "r") is False


def test_get_raises_area_not_found(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        dao_10_0.get_thermal_cluster_reserve_participation("nonexistent", "c", "r")


def test_get_raises_not_found_when_area_exists(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")
    with pytest.raises(ThermalClusterReserveParticipationNotFound):
        dao_10_0.get_thermal_cluster_reserve_participation("paris", "gas_cluster", "unknown")


def test_get_all_for_cluster(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris", clusters=("gas_cluster", "coal_cluster"))
    dao_10_0.save_thermal_cluster_reserve_participations(
        {
            "paris": {
                "gas_cluster": [_participation("R1"), _participation("R2")],
                "coal_cluster": [_participation("R1")],
            }
        }
    )

    fetched = list(dao_10_0.get_all_thermal_cluster_reserve_participations_for_cluster("paris", "gas_cluster"))
    assert len(fetched) == 2
    assert {p.id for p in fetched} == {"R1", "R2"}


def test_get_all_for_cluster_empty(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")
    assert list(dao_10_0.get_all_thermal_cluster_reserve_participations_for_cluster("paris", "gas_cluster")) == []


def test_get_all_for_cluster_raises_area_not_found(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        list(dao_10_0.get_all_thermal_cluster_reserve_participations_for_cluster("nonexistent", "c"))


def test_get_all_across_areas(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")
    _setup(dao_10_0, "lyon", clusters=("coal_cluster",))

    dao_10_0.save_thermal_cluster_reserve_participations(
        {
            "paris": {
                "gas_cluster": [_participation("R1"), _participation("R2")],
            },
            "lyon": {
                "coal_cluster": [_participation("R1")],
            },
        }
    )

    result = dao_10_0.get_all_thermal_cluster_reserve_participations()
    assert set(result.keys()) == {"paris", "lyon"}
    assert set(result["paris"]["gas_cluster"].keys()) == {"R1", "R2"}
    assert set(result["lyon"]["coal_cluster"].keys()) == {"R1"}


def test_delete(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")
    dao_10_0.save_thermal_cluster_reserve_participations(
        {"paris": {"gas_cluster": [_participation("R1"), _participation("R2")]}}
    )

    dao_10_0.delete_thermal_cluster_reserve_participations("paris", "gas_cluster", [ReserveDefinitionId("R1")])

    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R1") is False
    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R2") is True


def test_delete_not_found_raises(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris")
    dao_10_0.save_thermal_cluster_reserve_participations({"paris": {"gas_cluster": [_participation("R1")]}})
    with pytest.raises(ThermalClusterReserveParticipationNotFound):
        dao_10_0.delete_thermal_cluster_reserve_participations("paris", "gas_cluster", [ReserveDefinitionId("unknown")])


def test_cascade_on_thermal_cluster_delete(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris", clusters=("gas_cluster", "coal_cluster"))
    dao_10_0.save_thermal_cluster_reserve_participations(
        {
            "paris": {
                "gas_cluster": [_participation("R1")],
                "coal_cluster": [_participation("R1")],
            }
        }
    )

    dao_10_0.delete_thermal("paris", "gas_cluster")

    assert not dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R1")
    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "coal_cluster", "R1")


def test_cascade_on_reserve_definition_delete(dao_10_0: StudyDao) -> None:
    _setup(dao_10_0, "paris", clusters=("gas_cluster", "coal_cluster"))
    dao_10_0.save_thermal_cluster_reserve_participations(
        {
            "paris": {
                "gas_cluster": [_participation("R1"), _participation("R2")],
                "coal_cluster": [_participation("R1")],
            }
        }
    )

    dao_10_0.delete_reserve_definitions("paris", [ReserveDefinitionId("R1")])

    assert not dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R1")
    assert not dao_10_0.thermal_cluster_reserve_participation_exists("paris", "coal_cluster", "R1")
    assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R2")
