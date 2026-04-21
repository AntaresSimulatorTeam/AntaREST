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

from antarest.core.exceptions import ReservedReserveDefinitionName
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionCreation,
    ReserveDefinitionUpdate,
    ReserveType,
    create_reserve_definition,
    update_reserve_definition,
)
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_definition import (
    parse_reserve_definition,
    serialize_reserve_definition,
)


class TestReserveDefinition:
    def test_defaults_applied(self) -> None:
        reserve = ReserveDefinition(name="Reserve 1", type=ReserveType.UP)
        assert reserve.id == "reserve 1"
        assert reserve.name == "Reserve 1"
        assert reserve.type == ReserveType.UP
        assert reserve.failure_cost == 0.0
        assert reserve.spillage_cost == 0.0
        assert reserve.reference_activation_duration == 1
        assert reserve.power_activation_ratio == 0.0
        assert reserve.energy_activation_ratio == 1.0

    def test_id_derived_from_name(self) -> None:
        reserve = ReserveDefinition(name="Primary Up!!", type=ReserveType.UP)
        assert reserve.id == "primary up"

    def test_explicit_id_preserved(self) -> None:
        reserve = ReserveDefinition(id="custom_id", name="whatever", type=ReserveType.DOWN)
        assert reserve.id == "custom_id"

    def test_type_is_case_insensitive(self) -> None:
        reserve = ReserveDefinition(name="R", type="UP")  # type: ignore[arg-type]
        assert reserve.type == ReserveType.UP
        reserve = ReserveDefinition(name="R", type="Down")  # type: ignore[arg-type]
        assert reserve.type == ReserveType.DOWN

    @pytest.mark.parametrize(
        "field,value,valid",
        [
            ("failure_cost", -1.0, False),
            ("failure_cost", 0.0, True),
            ("spillage_cost", -0.5, False),
            ("reference_activation_duration", -1, False),
            ("reference_activation_duration", 0, True),
            ("power_activation_ratio", -0.1, False),
            ("power_activation_ratio", 1.1, False),
            ("power_activation_ratio", 0.5, True),
            ("energy_activation_ratio", 1.5, False),
            ("energy_activation_ratio", 1.0, True),
        ],
    )
    def test_bounds(self, field: str, value: float, valid: bool) -> None:
        kwargs = {"name": "r", "type": ReserveType.UP, field: value}
        if valid:
            ReserveDefinition(**kwargs)
        else:
            with pytest.raises(ValidationError):
                ReserveDefinition(**kwargs)


class TestReserveDefinitionCreation:
    def test_only_name_and_type_required(self) -> None:
        creation = ReserveDefinitionCreation(name="R1", type=ReserveType.UP)
        assert creation.name == "R1"
        assert creation.failure_cost is None

    @pytest.mark.parametrize(
        "name",
        ["global-parameters", "GLOBAL-PARAMETERS", "globalparameters", "GlobalParameters"],
    )
    def test_reserved_name_rejected(self, name: str) -> None:
        with pytest.raises(ReservedReserveDefinitionName):
            ReserveDefinitionCreation(name=name, type=ReserveType.UP)

    def test_missing_type_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ReserveDefinitionCreation(name="R1")  # type: ignore[call-arg]


class TestReserveDefinitionUpdate:
    def test_all_none_by_default(self) -> None:
        update = ReserveDefinitionUpdate()
        assert update.type is None
        assert update.failure_cost is None

    def test_name_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ReserveDefinitionUpdate.model_validate({"name": "new-name", "failureCost": 2.0})


class TestCreateAndUpdateHelpers:
    def test_create_applies_defaults(self) -> None:
        creation = ReserveDefinitionCreation(name="R1", type=ReserveType.UP)
        reserve = create_reserve_definition(creation)
        assert reserve.reference_activation_duration == 1
        assert reserve.energy_activation_ratio == 1.0
        assert reserve.id == "r1"

    def test_update_partial(self) -> None:
        reserve = ReserveDefinition(name="R1", type=ReserveType.UP, failure_cost=100.0, reference_activation_duration=5)
        update = ReserveDefinitionUpdate(failure_cost=200.0)
        result = update_reserve_definition(reserve, update)
        assert result.failure_cost == 200.0
        assert result.reference_activation_duration == 5
        assert result.type == ReserveType.UP


class TestFileDataRoundTrip:
    def test_serialize_excludes_id(self) -> None:
        reserve = ReserveDefinition(name="Reserve 1", type=ReserveType.DOWN, failure_cost=500.0)
        data = serialize_reserve_definition(reserve)
        assert "id" not in data
        assert data["name"] == "Reserve 1"
        assert data["type"] == "down"
        assert data["failure-cost"] == 500.0
        assert data["reference-activation-duration"] == 1

    def test_parse_kebab_case(self) -> None:
        data = {
            "name": "Reserve 1",
            "type": "up",
            "failure-cost": 500.0,
            "spillage-cost": 1111.0,
            "power-activation-ratio": 1.0,
            "energy-activation-ratio": 1.0,
            "reference-activation-duration": 10,
        }
        reserve = parse_reserve_definition(data)
        assert reserve.id == "reserve 1"
        assert reserve.name == "Reserve 1"
        assert reserve.type == ReserveType.UP
        assert reserve.failure_cost == 500.0
        assert reserve.reference_activation_duration == 10

    def test_round_trip(self) -> None:
        original = ReserveDefinition(
            name="Reserve A",
            type=ReserveType.UP,
            failure_cost=10.0,
            spillage_cost=5.0,
            reference_activation_duration=3,
            power_activation_ratio=0.4,
            energy_activation_ratio=0.9,
        )
        data = serialize_reserve_definition(original)
        restored = parse_reserve_definition(data)
        assert restored == original
