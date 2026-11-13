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
"""
Model of the GEMS `input/optim-config.yml` file.

See https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/optimization-configuration/
"""

import re
from enum import StrEnum
from typing import Annotated, Any, Self, TypeAlias

from pydantic import AfterValidator, ConfigDict, Field, NonNegativeInt, PositiveInt, model_validator

from antarest.core.model import GemsId
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.gems.system import ModelId

_SCENARIO_RANGE_REGEX = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")  # ex: "4-35"


def _validate_scenario_entry(value: int | str) -> int | str:
    """
    A scenario entry is either a non-negative integer or a string holding an integer or a range `"a-b"`, with a <= b.
    """

    def _validate_integer(v: int) -> int:
        if v < 0:
            raise ValueError(f"Scenario index must be greater than or equal to 0, got {v}")
        return v

    if isinstance(value, int):
        return _validate_integer(value)

    try:
        integer = int(value)

    except ValueError:
        match = _SCENARIO_RANGE_REGEX.match(value)
        if not match:
            raise ValueError(f"Invalid scenario entry '{value}': expected a range 'a-b'")
        start, end = int(match.group(1)), int(match.group(2))
        if start > end:
            raise ValueError(f"Invalid scenario range '{value}': start must be lower than or equal to end")
        return value

    return _validate_integer(integer)


ScenarioEntry: TypeAlias = Annotated[int | str, AfterValidator(_validate_scenario_entry)]


class _GemsTimeScope(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    first_time_step: NonNegativeInt = 0
    last_time_step: NonNegativeInt = 0

    @model_validator(mode="after")
    def _check_time_steps(self) -> Self:
        if self.last_time_step < self.first_time_step:
            raise ValueError("'last-time-step' must be greater than or equal to 'first-time-step'")
        return self


class _GemsScenarioScope(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    include: list[ScenarioEntry] | None = None
    exclude: list[ScenarioEntry] | None = None


class SolverName(StrEnum):
    HIGHS = "highs"
    XPRESS = "xpress"
    GUROBI = "gurobi"


class _GemsSolverOptions(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    name: SolverName = SolverName.HIGHS
    logs: bool = False
    parameters: str = ""

    @model_validator(mode="after")
    def _check_parameters(self) -> Self:
        if len(self.parameters.split()) % 2 != 0:
            raise ValueError("Solver 'parameters' must hold an even number of tokens (alternating names and values)")
        return self


class GemsResolutionMode(StrEnum):
    FRONTAL = "frontal"
    SEQUENTIAL_SUBPROBLEMS = "sequential-subproblems"
    PARALLEL_SUBPROBLEMS = "parallel-subproblems"
    BENDERS_DECOMPOSITION = "benders-decomposition"


class _GemsResolution(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    mode: GemsResolutionMode = GemsResolutionMode.FRONTAL
    block_length: PositiveInt | None = None
    block_overlap: NonNegativeInt | None = None
    carry_over_length: NonNegativeInt | None = None

    @model_validator(mode="after")
    def _check_blocks(self) -> Self:
        block_modes = {GemsResolutionMode.SEQUENTIAL_SUBPROBLEMS, GemsResolutionMode.PARALLEL_SUBPROBLEMS}
        if self.mode in block_modes and self.block_length is None:
            raise ValueError(f"'block-length' is required for mode '{self.mode}'")

        if self.mode != GemsResolutionMode.SEQUENTIAL_SUBPROBLEMS:
            if self.block_overlap is not None or self.carry_over_length is not None:
                raise ValueError(
                    f"'block-overlap' and 'carry-over-length' are only allowed with mode "
                    f"'{GemsResolutionMode.SEQUENTIAL_SUBPROBLEMS}', not '{self.mode}'"
                )
            return self

        assert self.block_length is not None  # Just for mypy, we know it's not None here due to the first validation
        overlap = self.block_overlap or 0
        if overlap >= self.block_length:
            raise ValueError("'block-overlap' must be lower than 'block-length'")
        if self.carry_over_length is not None and self.carry_over_length > overlap:
            raise ValueError("'carry-over-length' must be lower than or equal to 'block-overlap'")
        return self


class GemsOutOfBoundsMode(StrEnum):
    CYCLIC = "cyclic"
    DROP = "drop"


class GemsOutOfBoundsConstraint(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: GemsId
    mode: GemsOutOfBoundsMode = GemsOutOfBoundsMode.CYCLIC


def _check_unique_ids(items: list[Any], context: str) -> None:
    ids = {getattr(item, "id") for item in items}
    if len(ids) != len(items):
        raise ValueError(f"Duplicated ids in {context}")


class GemsOutOfBoundsProcessing(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    constraints: list[GemsOutOfBoundsConstraint] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        _check_unique_ids(self.constraints, "'out-of-bounds-processing' constraints")
        return self


class GemsDecompositionLocation(StrEnum):
    MASTER = "master"
    SUBPROBLEMS = "subproblems"
    MASTER_AND_SUBPROBLEMS = "master-and-subproblems"


class _GemsDecompositionElement(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: GemsId
    location: GemsDecompositionLocation = GemsDecompositionLocation.SUBPROBLEMS


class _GemsModelDecomposition(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    variables: list[_GemsDecompositionElement] = Field(default_factory=list)
    constraints: list[_GemsDecompositionElement] = Field(default_factory=list)
    objective_contributions: list[_GemsDecompositionElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        _check_unique_ids(self.variables, "'model-decomposition' variables")
        _check_unique_ids(self.constraints, "'model-decomposition' constraints")
        _check_unique_ids(self.objective_contributions, "'model-decomposition' objective-contributions")
        return self


class GemsHeuristicId(StrEnum):
    FAST = "fast"
    ACCURATE = "accurate"


class GemsHeuristicElementType(StrEnum):
    PARAMETER = "parameter"
    VARIABLE_SOLUTION = "variable-solution"
    VARIABLE_LOWER_BOUND = "variable-lower-bound"
    VARIABLE_UPPER_BOUND = "variable-upper-bound"


class _GemsHeuristicElement(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    heuristic_element: str
    id: GemsId
    type: GemsHeuristicElementType = GemsHeuristicElementType.PARAMETER


def _check_unique_heuristic_elements(elements: list[_GemsHeuristicElement], context: str) -> None:
    names = [e.heuristic_element for e in elements]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"Heuristic elements must appear only once in {context}: {duplicates}")


class _GemsHeuristic(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: GemsHeuristicId
    inputs: list[_GemsHeuristicElement]
    outputs: list[_GemsHeuristicElement]

    @model_validator(mode="after")
    def _check_elements(self) -> Self:
        _check_unique_heuristic_elements(self.inputs, f"inputs of heuristic '{self.id}'")
        _check_unique_heuristic_elements(self.outputs, f"outputs of heuristic '{self.id}'")
        bound_types = {GemsHeuristicElementType.VARIABLE_LOWER_BOUND, GemsHeuristicElementType.VARIABLE_UPPER_BOUND}
        for output in self.outputs:
            if output.type not in bound_types:
                raise ValueError(
                    f"Output '{output.heuristic_element}' of heuristic '{self.id}' must be a variable bound, "
                    f"got type '{output.type}'"
                )
        return self


class GemsOptimConfigModel(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: ModelId
    out_of_bounds_processing: GemsOutOfBoundsProcessing | None = None
    model_decomposition: _GemsModelDecomposition | None = None
    heuristics: list[_GemsHeuristic] | None = None

    @model_validator(mode="after")
    def _check_heuristics(self) -> Self:
        if self.heuristics:
            _check_unique_ids(self.heuristics, f"heuristics of model '{self.id}'")
        return self


class GemsOptimConfig(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    time_scope: _GemsTimeScope | None = None
    scenario_scope: _GemsScenarioScope | None = None
    solver_options: _GemsSolverOptions | None = None
    resolution: _GemsResolution | None = None
    models: list[GemsOptimConfigModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        _check_unique_ids(self.models, "'models'")

        if self.resolution is not None and self.resolution.mode == GemsResolutionMode.BENDERS_DECOMPOSITION:
            for model in self.models:
                if model.heuristics:
                    raise ValueError(
                        f"Heuristics cannot be used with '{GemsResolutionMode.BENDERS_DECOMPOSITION}' "
                        f"(declared for model '{model.id}')"
                    )
        return self
