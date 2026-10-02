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

from typing import Any, Dict

import pytest
from pydantic_core import ValidationError

from antarest.launcher.adapters.local_launcher.local_launcher import (
    SOLVER_VERSION_8_8,
    SOLVER_VERSION_9_2,
    SOLVER_VERSION_9_3,
)
from antarest.launcher.model import SolverPresets


@pytest.fixture
def base_solver_presets() -> Dict[str, Any]:
    """Base solver presets parameters for SolverPresetsDTO."""
    return {
        "id": "id123",
        "name": "test",
        "linear_solver": "xpress",
        "use_optim_1_basis_next_week": True,
        "use_optim_1_basis_optim_2": True,
        "linear_solver_param": None,
        "linear_solver_param_optim_1": None,
        "linear_solver_param_optim_2": None,
        "min_antares_version": SOLVER_VERSION_9_2,
    }


def test_basic_xpress_solver_only(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(**base_solver_presets)
    assert solver_presets.to_cli_options() == "xpress"


def test_xpress_nobasis_flags(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(
        **{**base_solver_presets, "use_optim_1_basis_next_week": False, "use_optim_1_basis_optim_2": False}
    )
    result = solver_presets.to_cli_options()
    # order should be deterministic
    assert result == "xpress nobasis1 nobasis2"


def test_xpress_single_nobasis1(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(**{**base_solver_presets, "use_optim_1_basis_next_week": False})
    assert solver_presets.to_cli_options() == "xpress nobasis1"


def test_xpress_with_common_params(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(**{**base_solver_presets, "linear_solver_param": {"THREADS": 4, "FEASTOL": 1}})
    result = solver_presets.to_cli_options()
    assert 'param-optim1="THREADS 4 FEASTOL 1"' in result
    assert 'param-optim2="THREADS 4 FEASTOL 1"' in result


def test_xpress_combined_common_and_specific_params(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(
        **{
            **base_solver_presets,
            "linear_solver_param": {"THREADS": 4},
            "linear_solver_param_optim_1": {"PRESOLVE": 1},
            "linear_solver_param_optim_2": {"MIPRELSTOP": 0.01},
        }
    )
    result = solver_presets.to_cli_options()
    assert 'param-optim1="THREADS 4 PRESOLVE 1"' in result, "common + optim1 combined"
    assert 'param-optim2="THREADS 4 MIPRELSTOP 0.01"' in result, "common + optim2 combined"


def test_presolve_detected_in_optim2_only(base_solver_presets: Dict[str, Any]) -> None:
    solver_presets = SolverPresets(
        **{**base_solver_presets, "linear_solver_param_optim_2": {"PRESOLVE": 100, "THREADS": 2}}
    )
    result = solver_presets.to_cli_options()
    assert result == 'xpress param-optim2="PRESOLVE 100 THREADS 2"'


def test_valid_solver_presets_minimal() -> None:
    cfg = SolverPresets(id="123", name="default", linear_solver="xpress")
    assert cfg.linear_solver == "xpress"
    assert cfg.use_optim_1_basis_next_week is True
    assert cfg.use_optim_1_basis_optim_2 is True


def test_name_cannot_be_empty() -> None:
    with pytest.raises(ValidationError, match="Invalid name"):
        SolverPresets(id="123", name="   ", linear_solver="xpress")


def test_min_version_must_not_exceed_max() -> None:
    with pytest.raises(ValidationError, match="min_antares_version cannot be greater"):
        SolverPresets(
            id="123",
            name="valid",
            linear_solver="xpress",
            min_antares_version=SOLVER_VERSION_9_3,
            max_antares_version=SOLVER_VERSION_9_2,
        )


def test_invalid_key_in_solver_params() -> None:
    with pytest.raises(ValidationError, match="Invalid key"):
        SolverPresets(
            name="valid",
            linear_solver="xpress",
            linear_solver_param={"INVALID-KEY!": "1"},
        )


def test_invalid_value_in_solver_params() -> None:
    with pytest.raises(ValidationError, match="Invalid value"):
        SolverPresets(
            name="valid",
            linear_solver="xpress",
            linear_solver_param={"KEY": "1.2.3"},
        )


def test_optim_params_before_9_2_not_allowed() -> None:
    with pytest.raises(ValidationError, match="not supported before Antares version 9.2"):
        SolverPresets(
            id="123",
            name="valid",
            linear_solver="xpress",
            min_antares_version=SOLVER_VERSION_8_8,
            linear_solver_param_optim_1={"PRESOLVE": "1"},
        )
