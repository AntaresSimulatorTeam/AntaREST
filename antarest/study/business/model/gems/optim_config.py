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
from typing import Annotated, Self, TypeAlias

from pydantic import AfterValidator, ConfigDict, Field, NonNegativeInt, PositiveInt, model_validator

from antarest.core.model import GemsId
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case

_SCENARIO_RANGE_REGEX = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
_SCENARIO_INDEX_REGEX = re.compile(r"^\s*(\d+)\s*$")


def _validate_scenario_entry(value: int | str) -> int | str:
    """
    A scenario entry is either a non-negative integer or a string holding an integer or a range `"a-b"`, with a <= b.
    """
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"Scenario index must be greater than or equal to 0, got {value}")
        return value
    if _SCENARIO_INDEX_REGEX.match(value):
        return value
    match = _SCENARIO_RANGE_REGEX.match(value)
    if not match:
        raise ValueError(f"Invalid scenario entry '{value}': expected an integer or a range 'a-b'")
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        raise ValueError(f"Invalid scenario range '{value}': start must be lower than or equal to end")
    return value


ScenarioEntry: TypeAlias = Annotated[int | str, AfterValidator(_validate_scenario_entry)]


def _expand_scenario_entries(entries: list[ScenarioEntry]) -> set[int]:
    indices: set[int] = set()
    for entry in entries:
        if isinstance(entry, int):
            indices.add(entry)
            continue
        match = _SCENARIO_RANGE_REGEX.match(entry)
        if match:
            indices.update(range(int(match.group(1)), int(match.group(2)) + 1))
        else:
            indices.add(int(entry))
    return indices


class GemsTimeScope(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    first_time_step: NonNegativeInt
    last_time_step: NonNegativeInt

    @model_validator(mode="after")
    def _check_time_steps(self) -> Self:
        if self.last_time_step < self.first_time_step:
            raise ValueError("'last-time-step' must be greater than or equal to 'first-time-step'")
        return self


class GemsScenarioScope(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    include: list[ScenarioEntry] | None = None
    exclude: list[ScenarioEntry] | None = None

    def get_scenarios(self) -> list[int]:
        """
        Returns the sorted list of selected scenarios.
        Without `include`, the base set is the scenario 0.
        """
        base = _expand_scenario_entries(self.include) if self.include else {0}
        excluded = _expand_scenario_entries(self.exclude) if self.exclude else set()
        return sorted(base - excluded)


class GemsSolverOptions(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    name: str = "highs"
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


class GemsResolution(AntaresBaseModel):
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

        assert self.block_length is not None
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


def _check_unique_ids(items: list[AntaresBaseModel], context: str) -> None:
    ids = [getattr(item, "id") for item in items]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"Duplicated ids in {context}: {duplicates}")


class GemsOutOfBoundsProcessing(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    constraints: list[GemsOutOfBoundsConstraint] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        _check_unique_ids(list(self.constraints), "'out-of-bounds-processing' constraints")
        return self


class GemsDecompositionLocation(StrEnum):
    MASTER = "master"
    SUBPROBLEMS = "subproblems"
    MASTER_AND_SUBPROBLEMS = "master-and-subproblems"


class GemsDecompositionElement(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: GemsId
    location: GemsDecompositionLocation = GemsDecompositionLocation.SUBPROBLEMS


class GemsModelDecomposition(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    variables: list[GemsDecompositionElement] = Field(default_factory=list)
    constraints: list[GemsDecompositionElement] = Field(default_factory=list)
    objective_contributions: list[GemsDecompositionElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique(self) -> Self:
        _check_unique_ids(list(self.variables), "'model-decomposition' variables")
        _check_unique_ids(list(self.constraints), "'model-decomposition' constraints")
        _check_unique_ids(list(self.objective_contributions), "'model-decomposition' objective-contributions")
        return self


class GemsHeuristicId(StrEnum):
    FAST = "fast"
    ACCURATE = "accurate"


class GemsHeuristicElementType(StrEnum):
    PARAMETER = "parameter"
    VARIABLE_SOLUTION = "variable-solution"
    VARIABLE_LOWER_BOUND = "variable-lower-bound"
    VARIABLE_UPPER_BOUND = "variable-upper-bound"


class GemsHeuristicElement(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    heuristic_element: str
    id: GemsId
    type: GemsHeuristicElementType = GemsHeuristicElementType.PARAMETER


def _check_unique_heuristic_elements(elements: list[GemsHeuristicElement], context: str) -> None:
    names = [e.heuristic_element for e in elements]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"Heuristic elements must appear only once in {context}: {duplicates}")


class GemsHeuristic(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: GemsHeuristicId
    inputs: list[GemsHeuristicElement]
    outputs: list[GemsHeuristicElement]

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


_MODEL_ID_REGEX = r"^[a-z0-9_]+\.[a-z0-9_]+$"


class GemsOptimConfigModel(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: Annotated[str, Field(pattern=_MODEL_ID_REGEX)]
    out_of_bounds_processing: GemsOutOfBoundsProcessing | None = None
    model_decomposition: GemsModelDecomposition | None = None
    heuristics: list[GemsHeuristic] | None = None

    @property
    def library_id(self) -> str:
        return self.id.split(".")[0]

    @property
    def model_id(self) -> str:
        return self.id.split(".")[1]

    @model_validator(mode="after")
    def _check_heuristics(self) -> Self:
        if self.heuristics:
            _check_unique_ids(list(self.heuristics), f"heuristics of model '{self.id}'")
        return self


class GemsOptimConfig(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    time_scope: GemsTimeScope | None = None
    scenario_scope: GemsScenarioScope | None = None
    solver_options: GemsSolverOptions | None = None
    resolution: GemsResolution | None = None
    models: list[GemsOptimConfigModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        _check_unique_ids(list(self.models), "'models'")

        if self.resolution is not None and self.resolution.mode == GemsResolutionMode.BENDERS_DECOMPOSITION:
            for model in self.models:
                if model.heuristics:
                    raise ValueError(
                        f"Heuristics cannot be used with '{GemsResolutionMode.BENDERS_DECOMPOSITION}' "
                        f"(declared for model '{model.id}')"
                    )
        return self
