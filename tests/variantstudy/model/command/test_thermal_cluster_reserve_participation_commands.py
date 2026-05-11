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
from antares.study.version import StudyVersion
from pydantic import ValidationError

from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionId,
    ReserveType,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
    ThermalClusterReserveParticipationCreation,
    ThermalClusterReserveParticipationUpdate,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.create_thermal_cluster_reserve_participation import (
    CreateThermalClusterReserveParticipation,
)
from antarest.study.storage.variantstudy.model.command.remove_thermal_cluster_reserve_participations import (
    RemoveThermalClusterReserveParticipations,
)
from antarest.study.storage.variantstudy.model.command.update_thermal_cluster_reserve_participations import (
    UpdateThermalClusterReserveParticipations,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.utils import save_area


def _setup_prereqs(
    dao: StudyDao,
    area_id: str = "paris",
    thermal_ids: tuple[str, ...] = ("gas_cluster",),
    reserve_ids: tuple[str, ...] = ("R1", "R2", "R3", "Reserve 1"),
) -> None:
    """Create the area, thermal clusters and reserve definitions required by the FK
    constraints of ``thermal_cluster_reserve_participation``."""
    save_area(dao, area_id)
    dao.save_thermals({area_id: [ThermalCluster(id=cid, name=cid) for cid in thermal_ids]})
    dao.save_reserve_definitions({area_id: [ReserveDefinition(id=rid, type=ReserveType.UP) for rid in reserve_ids]})


class TestCreateThermalClusterReserveParticipation:
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _setup_prereqs(dao_10_0)

        command = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="gas_cluster",
            parameters=ThermalClusterReserveParticipationCreation(id="Reserve 1", max_power=20.0),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status
        assert isinstance(output.result, ThermalClusterReserveParticipation)
        assert output.result.id == "Reserve 1"
        assert output.result.max_power == 20.0

        assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "Reserve 1")

    def test_apply_unknown_cluster_fails(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        # Area + reserve definition exist, but the thermal cluster does not.
        save_area(dao_10_0, "paris")
        dao_10_0.save_reserve_definitions({"paris": [ReserveDefinition(id="Reserve 1", type=ReserveType.UP)]})
        command = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="ghost",
            parameters=ThermalClusterReserveParticipationCreation(id="Reserve 1"),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert not output.status
        assert "Thermal cluster 'ghost' does not exist" in output.message

    def test_apply_unknown_reserve_fails(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        # Area + cluster exist, but no reserve definition.
        save_area(dao_10_0, "paris")
        dao_10_0.save_thermals({"paris": [ThermalCluster(id="gas_cluster", name="gas_cluster")]})
        command = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="gas_cluster",
            parameters=ThermalClusterReserveParticipationCreation(id="ghost"),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert not output.status
        assert "Reserve definition 'ghost' does not exist" in output.message

    def test_apply_duplicate_fails(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _setup_prereqs(dao_10_0)

        first = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="gas_cluster",
            parameters=ThermalClusterReserveParticipationCreation(id="Reserve 1"),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        first.apply(dao_10_0)

        second = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="gas_cluster",
            parameters=ThermalClusterReserveParticipationCreation(id="Reserve 1"),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = second.apply(dao_10_0)
        assert not output.status
        assert "already exists" in output.message

    def test_version_check(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="study version before 10.0"):
            CreateThermalClusterReserveParticipation(
                area_id="paris",
                thermal_id="gas_cluster",
                parameters=ThermalClusterReserveParticipationCreation(id="Reserve 1"),
                command_context=command_context,
                study_version=StudyVersion.parse("9.2"),
            )

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = CreateThermalClusterReserveParticipation(
            area_id="paris",
            thermal_id="gas_cluster",
            parameters=ThermalClusterReserveParticipationCreation(
                id="Reserve 1",
                max_power=20.0,
                participation_cost=1.0,
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "create_thermal_cluster_reserve_participation"
        assert dto.args["area_id"] == "paris"
        assert dto.args["thermal_id"] == "gas_cluster"
        assert dto.args["parameters"]["id"] == "Reserve 1"
        assert dto.args["parameters"]["maxPower"] == 20.0
        assert dto.args["parameters"]["participationCost"] == 1.0


def _seed_two_participations(dao: StudyDao, command_context: CommandContext) -> None:
    _setup_prereqs(dao)
    CreateThermalClusterReserveParticipation(
        area_id="paris",
        thermal_id="gas_cluster",
        parameters=ThermalClusterReserveParticipationCreation(id="R1", max_power=10.0),
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    ).apply(dao)
    CreateThermalClusterReserveParticipation(
        area_id="paris",
        thermal_id="gas_cluster",
        parameters=ThermalClusterReserveParticipationCreation(id="R2", max_power=15.0),
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    ).apply(dao)


class TestUpdateThermalClusterReserveParticipations:
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _seed_two_participations(dao_10_0, command_context)

        command = UpdateThermalClusterReserveParticipations(
            participation_properties={
                "paris": {
                    "gas_cluster": {
                        ReserveDefinitionId("R1"): ThermalClusterReserveParticipationUpdate(max_power=99.0),
                    }
                }
            },
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status

        updated = dao_10_0.get_thermal_cluster_reserve_participation("paris", "gas_cluster", "R1")
        assert updated.max_power == 99.0
        # other participation untouched
        other = dao_10_0.get_thermal_cluster_reserve_participation("paris", "gas_cluster", "R2")
        assert other.max_power == 15.0

    def test_apply_unknown_fails(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _seed_two_participations(dao_10_0, command_context)
        command = UpdateThermalClusterReserveParticipations(
            participation_properties={
                "paris": {
                    "gas_cluster": {
                        ReserveDefinitionId("R3"): ThermalClusterReserveParticipationUpdate(max_power=99.0),
                    }
                }
            },
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert not output.status
        assert "is not found" in output.message


class TestRemoveThermalClusterReserveParticipations:
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _seed_two_participations(dao_10_0, command_context)

        command = RemoveThermalClusterReserveParticipations(
            area_id="paris",
            thermal_id="gas_cluster",
            reserve_ids=[ReserveDefinitionId("R1")],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status

        assert not dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R1")
        assert dao_10_0.thermal_cluster_reserve_participation_exists("paris", "gas_cluster", "R2")

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = RemoveThermalClusterReserveParticipations(
            area_id="paris",
            thermal_id="gas_cluster",
            reserve_ids=[ReserveDefinitionId("R1"), ReserveDefinitionId("R2")],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "remove_thermal_cluster_reserve_participations"
        assert dto.args["area_id"] == "paris"
        assert dto.args["thermal_id"] == "gas_cluster"
        assert dto.args["reserve_ids"] == ["R1", "R2"]
