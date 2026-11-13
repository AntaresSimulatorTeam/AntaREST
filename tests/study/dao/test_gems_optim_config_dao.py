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
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.optim_config import GemsOptimConfig, GemsResolutionMode
from antarest.study.business.model.gems.system import split_library_and_model_id
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader

ASSETS_PATH = Path(__file__).parent / "assets" / "gems" / "optim-config"
EXAMPLES = ["frontal", "sequential", "parallel", "benders"]


def _load_example(name: str) -> GemsOptimConfig:
    return GemsOptimConfig.model_validate(YAMLReader().read(ASSETS_PATH / f"{name}.yml"))


def _build_library(config: GemsOptimConfig) -> GemsLibrary:
    """Builds a library containing every element referenced by the configuration."""
    library_ids = {split_library_and_model_id(model.id)[0] for model in config.models}
    assert len(library_ids) == 1
    models = []
    for model in config.models:
        variables: set[str] = set()
        constraints: set[str] = set()
        contributions: set[str] = set()
        if model.out_of_bounds_processing:
            constraints |= {c.id for c in model.out_of_bounds_processing.constraints}
        if model.model_decomposition:
            variables |= {v.id for v in model.model_decomposition.variables}
            constraints |= {c.id for c in model.model_decomposition.constraints}
            contributions |= {o.id for o in model.model_decomposition.objective_contributions}
        models.append(
            {
                "id": split_library_and_model_id(model.id)[1],
                "variables": [{"id": v, "variable-type": "continuous"} for v in variables],
                "constraints": [{"id": c, "expression": "x = 0"} for c in constraints],
                "objective-contributions": [{"id": o, "expression": "x"} for o in contributions],
            }
        )
    return GemsLibrary.model_validate({"id": library_ids.pop(), "models": models})


@pytest.mark.parametrize("example", EXAMPLES)
def test_examples_are_valid(example: str) -> None:
    config = _load_example(example)
    assert config.models


def test_examples_content() -> None:
    frontal = _load_example("frontal")
    assert frontal.time_scope is not None and frontal.time_scope.last_time_step == 167
    assert frontal.scenario_scope is not None
    assert frontal.scenario_scope.include == ["0-2"] and frontal.scenario_scope.exclude is None
    assert frontal.solver_options is not None and frontal.solver_options.name == "highs"

    sequential = _load_example("sequential")
    assert sequential.resolution is not None
    assert sequential.resolution.mode == GemsResolutionMode.SEQUENTIAL_SUBPROBLEMS
    assert sequential.resolution.carry_over_length == 24

    benders = _load_example("benders")
    assert benders.scenario_scope is not None
    assert benders.scenario_scope.include == ["0-9"] and benders.scenario_scope.exclude is None
    decomposition = benders.models[0].model_decomposition
    assert decomposition is not None
    assert decomposition.variables[0].location == "master-and-subproblems"


@pytest.mark.parametrize("dao_10_2", ["file", "db"], indirect=True)
@pytest.mark.parametrize("example", EXAMPLES)
def test_roundtrip(dao_10_2: StudyDao, example: str) -> None:
    dao = dao_10_2
    assert dao.get_optim_config() is None

    config = _load_example(example)
    dao.save_library(_build_library(config))
    dao.save_optim_config(config)
    assert dao.get_optim_config() == config

    # Saving again replaces the existing configuration
    new_config = config.model_copy(update={"models": config.models[:1], "solver_options": None})
    dao.save_optim_config(new_config)
    assert dao.get_optim_config() == new_config


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_db_foreign_keys(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    config = _load_example("frontal")
    # No library: the referenced model and constraint do not exist
    with pytest.raises(IntegrityError):
        dao.save_optim_config(config)

    dao.save_library(_build_library(config))
    wrong = GemsOptimConfig.model_validate(
        {
            "models": [
                {
                    "id": config.models[0].id,
                    "out-of-bounds-processing": {"constraints": [{"id": "unknown", "mode": "drop"}]},
                }
            ]
        }
    )
    with pytest.raises(IntegrityError):
        dao.save_optim_config(wrong)


@pytest.mark.parametrize(
    "content",
    [
        {"time-scope": {"first-time-step": 10, "last-time-step": 5}},
        {"time-scope": {"first-time-step": -1, "last-time-step": 5}},
        {"scenario-scope": {"include": [-1]}},
        {"scenario-scope": {"include": ["5-2"]}},
        {"scenario-scope": {"include": ["abc"]}},
        {"solver-options": {"parameters": "THREADS 1 MAXTIME"}},
        {"resolution": {"mode": "unknown"}},
        {"resolution": {"mode": "sequential-subproblems"}},
        {"resolution": {"mode": "parallel-subproblems"}},
        {"resolution": {"mode": "parallel-subproblems", "block-length": 168, "block-overlap": 0}},
        {"resolution": {"mode": "frontal", "carry-over-length": 0}},
        {"resolution": {"mode": "sequential-subproblems", "block-length": 10, "block-overlap": 10}},
        {
            "resolution": {
                "mode": "sequential-subproblems",
                "block-length": 10,
                "block-overlap": 4,
                "carry-over-length": 5,
            }
        },
        {"models": [{"id": "no_library_prefix"}]},
        {"models": [{"id": "lib.model"}, {"id": "lib.model"}]},
        {"models": [{"id": "lib.model", "out-of-bounds-processing": {"constraints": [{"id": "c", "mode": "x"}]}}]},
        {"models": [{"id": "lib.model", "model-decomposition": {"variables": [{"id": "v", "location": "x"}]}}]},
        {
            "models": [
                {
                    "id": "lib.model",
                    "heuristics": [
                        {
                            "id": "accurate",
                            "inputs": [],
                            "outputs": [{"heuristic-element": "e", "id": "v", "type": "parameter"}],
                        }
                    ],
                }
            ]
        },
        {
            "resolution": {"mode": "benders-decomposition"},
            "models": [{"id": "lib.model", "heuristics": [{"id": "fast", "inputs": [], "outputs": []}]}],
        },
    ],
)
def test_invalid_configs(content: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        GemsOptimConfig.model_validate(content)


def test_valid_heuristics_and_defaults() -> None:
    config = GemsOptimConfig.model_validate(
        {
            "resolution": {"mode": "sequential-subproblems", "block-length": 10, "block-overlap": 4},
            "models": [
                {
                    "id": "my_library.thermal",
                    "heuristics": [
                        {
                            "id": "accurate",
                            "inputs": [
                                {
                                    "heuristic-element": "num_units_on_opt",
                                    "id": "nb_units_on",
                                    "type": "variable-solution",
                                },
                                {"heuristic-element": "num_units_max", "id": "nb_units_max"},
                            ],
                            "outputs": [
                                {
                                    "heuristic-element": "minimum_num_units_on",
                                    "id": "nb_units_on",
                                    "type": "variable-lower-bound",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )
    assert config.models[0].heuristics is not None
    assert config.models[0].heuristics[0].inputs[1].type == "parameter"
    assert GemsOptimConfig().models == []
