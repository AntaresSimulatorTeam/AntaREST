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

from antarest.study.business.model.reserves_global_parameters_model import (
    ReservesGlobalParameters,
    ReservesGlobalParametersUpdate,
    update_reserves_global_parameters,
)


class TestReservesGlobalParameters:
    def test_default_values(self) -> None:
        params = ReservesGlobalParameters()
        assert params.reference_activation_duration_up == 1
        assert params.energy_activation_ratio_up == 1.0
        assert params.reference_activation_duration_down == 1
        assert params.energy_activation_ratio_down == 1.0

    @pytest.mark.parametrize(
        "field,value,valid",
        [
            ("reference_activation_duration_up", -1, False),
            ("reference_activation_duration_down", -1, False),
            ("reference_activation_duration_up", 0, True),
            ("energy_activation_ratio_up", -0.1, False),
            ("energy_activation_ratio_up", 1.5, False),
            ("energy_activation_ratio_down", 2.0, False),
            ("energy_activation_ratio_up", 0.0, True),
            ("energy_activation_ratio_down", 1.0, True),
        ],
    )
    def test_field_bounds(self, field: str, value: float, valid: bool) -> None:
        if valid:
            params = ReservesGlobalParameters(**{field: value})
            assert getattr(params, field) == value
        else:
            with pytest.raises(ValidationError):
                ReservesGlobalParameters(**{field: value})


class TestReservesGlobalParametersUpdate:
    def test_all_none_by_default(self) -> None:
        update = ReservesGlobalParametersUpdate()
        assert update.reference_activation_duration_up is None
        assert update.energy_activation_ratio_up is None

    def test_partial_update(self) -> None:
        update = ReservesGlobalParametersUpdate(reference_activation_duration_up=10)
        assert update.reference_activation_duration_up == 10
        assert update.energy_activation_ratio_up is None


class TestUpdateFunction:
    def test_merge_partial(self) -> None:
        current = ReservesGlobalParameters(
            reference_activation_duration_up=5,
            energy_activation_ratio_up=0.8,
        )
        update = ReservesGlobalParametersUpdate(reference_activation_duration_up=10)
        result = update_reserves_global_parameters(current, update)
        assert result.reference_activation_duration_up == 10
        assert result.energy_activation_ratio_up == 0.8
        assert result.reference_activation_duration_down == 1
        assert result.energy_activation_ratio_down == 1.0

    def test_merge_full(self) -> None:
        current = ReservesGlobalParameters()
        update = ReservesGlobalParametersUpdate(
            reference_activation_duration_up=2,
            energy_activation_ratio_up=0.5,
            reference_activation_duration_down=3,
            energy_activation_ratio_down=0.7,
        )
        result = update_reserves_global_parameters(current, update)
        assert result.reference_activation_duration_up == 2
        assert result.energy_activation_ratio_up == 0.5
        assert result.reference_activation_duration_down == 3
        assert result.energy_activation_ratio_down == 0.7

    def test_empty_update_no_change(self) -> None:
        current = ReservesGlobalParameters(reference_activation_duration_up=5)
        update = ReservesGlobalParametersUpdate()
        result = update_reserves_global_parameters(current, update)
        assert result == current
