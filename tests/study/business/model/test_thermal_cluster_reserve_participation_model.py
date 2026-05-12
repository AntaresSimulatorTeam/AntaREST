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
from pydantic import ValidationError

from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
    ThermalClusterReserveParticipationCreation,
    ThermalClusterReserveParticipationUpdate,
    create_thermal_cluster_reserve_participation,
    update_thermal_cluster_reserve_participation,
)
from antarest.study.storage.rawstudy.model.filesystem.config.thermal_cluster_reserve_participation import (
    extract_reserve_id,
    parse_thermal_cluster_reserve_participation,
    section_name,
    serialize_thermal_cluster_reserve_participation,
)


class TestThermalClusterReserveParticipation:
    def test_defaults_applied(self) -> None:
        participation = ThermalClusterReserveParticipation(id="Reserve 1")
        assert participation.id == "Reserve 1"
        assert participation.max_power == 0.0
        assert participation.max_power_off == 0.0
        assert participation.participation_cost == 0.0
        assert participation.participation_cost_off == 0.0

    def test_cluster_name_rejected_in_model(self) -> None:
        with pytest.raises(ValidationError):
            ThermalClusterReserveParticipation.model_validate({"id": "R1", "clusterName": "c1"})

    @pytest.mark.parametrize(
        "field,value,valid",
        [
            ("max_power", -1.0, False),
            ("max_power", 0.0, True),
            ("max_power_off", -0.5, False),
            ("max_power_off", 5.0, True),
            ("participation_cost", -0.1, False),
            ("participation_cost", 100.0, True),
            ("participation_cost_off", -1.0, False),
            ("participation_cost_off", 1.0, True),
        ],
    )
    def test_bounds(self, field: str, value: float, valid: bool) -> None:
        kwargs = {"id": "r", field: value}
        if valid:
            ThermalClusterReserveParticipation(**kwargs)
        else:
            with pytest.raises(ValidationError):
                ThermalClusterReserveParticipation(**kwargs)


class TestThermalClusterReserveParticipationCreation:
    def test_only_id_required(self) -> None:
        creation = ThermalClusterReserveParticipationCreation(id="R1")
        assert creation.id == "R1"
        assert creation.max_power is None

    def test_cluster_name_rejected_in_creation(self) -> None:
        with pytest.raises(ValidationError):
            ThermalClusterReserveParticipationCreation.model_validate({"id": "R1", "clusterName": "c1"})


class TestThermalClusterReserveParticipationUpdate:
    def test_all_none_by_default(self) -> None:
        update = ThermalClusterReserveParticipationUpdate()
        assert update.max_power is None
        assert update.participation_cost is None

    def test_cluster_name_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ThermalClusterReserveParticipationUpdate.model_validate({"clusterName": "other", "maxPower": 10.0})


class TestCreateAndUpdateHelpers:
    def test_create_applies_defaults(self) -> None:
        creation = ThermalClusterReserveParticipationCreation(id="R1")
        participation = create_thermal_cluster_reserve_participation(creation)
        assert participation.max_power == 0.0
        assert participation.participation_cost_off == 0.0
        assert participation.id == "R1"

    def test_update_partial(self) -> None:
        participation = ThermalClusterReserveParticipation(
            id="R1",
            max_power=20.0,
            max_power_off=10.0,
            participation_cost=1.0,
        )
        update = ThermalClusterReserveParticipationUpdate(max_power=30.0)
        result = update_thermal_cluster_reserve_participation(participation, update)
        assert result.max_power == 30.0
        assert result.max_power_off == 10.0
        assert result.participation_cost == 1.0


class TestFileDataRoundTrip:
    def test_serialize_injects_cluster_name(self) -> None:
        participation = ThermalClusterReserveParticipation(
            id="Reserve 1",
            max_power=20.0,
            max_power_off=10.0,
            participation_cost=1.0,
            participation_cost_off=2.0,
        )
        data = serialize_thermal_cluster_reserve_participation("gas_cluster", participation)
        assert data["cluster-name"] == "gas_cluster"
        assert "id" not in data
        assert data["max-power"] == 20.0

    def test_parse_kebab_case(self) -> None:
        data = {
            "cluster-name": "gas_cluster",
            "max-power": 20.0,
            "max-power-off": 10.0,
            "participation-cost": 1.0,
            "participation-cost-off": 2.0,
        }
        participation = parse_thermal_cluster_reserve_participation("Reserve 1", data)
        assert participation.id == "Reserve 1"
        assert participation.max_power == 20.0

    def test_round_trip(self) -> None:
        original = ThermalClusterReserveParticipation(
            id="Reserve A",
            max_power=42.0,
            max_power_off=10.0,
            participation_cost=3.5,
            participation_cost_off=4.5,
        )
        data = serialize_thermal_cluster_reserve_participation("gas_cluster", original)
        restored = parse_thermal_cluster_reserve_participation(original.id, data)
        assert restored == original


class TestSectionNaming:
    def test_section_name_round_trip(self) -> None:
        name = section_name("gas_cluster", "Reserve 1")
        assert extract_reserve_id(name, "gas_cluster") == "Reserve 1"

    def test_extract_reserve_id_handles_separator_in_cluster(self) -> None:
        name = section_name("gas__1", "Reserve 1")
        assert extract_reserve_id(name, "gas__1") == "Reserve 1"
        assert extract_reserve_id(name, "gas") == "1__Reserve 1"

    def test_extract_reserve_id_handles_separator_in_reserve(self) -> None:
        name = section_name("gas", "Reserve__1")
        assert extract_reserve_id(name, "gas") == "Reserve__1"

    def test_extract_reserve_id_invalid(self) -> None:
        assert extract_reserve_id("globalparameters", "any") is None
        assert extract_reserve_id("", "any") is None
        assert extract_reserve_id("gas__", "gas") is None  # empty reserve_id
        assert extract_reserve_id("other__r1", "gas") is None  # cluster mismatch
