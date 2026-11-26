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
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.conftest import build_filesystem_dao

ASSETS_PATH = Path(__file__).parent / "assets" / "gems" / "optim-config"
EXAMPLES = ["frontal", "sequential", "parallel", "benders"]


def _load_example(name: str) -> GemsOptimConfig:
    return GemsOptimConfig.model_validate(YAMLReader().read(ASSETS_PATH / f"{name}.yml"))


def _build_library(config: GemsOptimConfig) -> GemsLibrary:
    """
    Builds a library containing every element referenced by the configuration.
    This way no foreign key constraint is violated.
    """
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


def _check_optim_config_equality(config: GemsOptimConfig | None, expected: GemsOptimConfig) -> None:
    assert config is not None
    # Sort the models for test comparison
    config.models = sorted(config.models, key=lambda m: m.id)
    expected.models = sorted(expected.models, key=lambda m: m.id)
    assert config == expected


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
def test_roundtrip_on_real_examples(dao_10_2: StudyDao, example: str) -> None:
    dao = dao_10_2
    assert dao.get_optim_config() is None

    config = _load_example(example)
    dao.save_library(_build_library(config))
    dao.save_optim_config(config)
    _check_optim_config_equality(dao.get_optim_config(), config)

    # Saving again with a slightly different data -> Should not raise and return the new data
    new_config = config.model_copy(update={"solver_options": None})
    dao.save_optim_config(new_config)
    _check_optim_config_equality(dao.get_optim_config(), new_config)


@pytest.mark.parametrize("dao_builder", ["db"], indirect=True)
def test_db_foreign_keys(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    config = _load_example("frontal")
    # No library: the referenced model and constraint do not exist
    with pytest.raises(IntegrityError):
        dao.save_optim_config(config)

    dao.save_library(_build_library(config))

    # Fake constraint inside "out-of-bounds-processing" -> Should raise
    fake_constraint_oob = {"out-of-bounds-processing": {"constraints": [{"id": "unknown", "mode": "drop"}]}}

    # Fake variable inside "model-decomposition" -> Should raise
    fake_variable = {"model_decomposition": {"variables": [{"id": "unknown", "location": "master"}]}}

    # Fake constraint inside "model-decomposition" -> Should raise
    fake_constraint = {"model_decomposition": {"constraints": [{"id": "unknown", "location": "master"}]}}

    # Fake objective contribution inside "model-decomposition" -> Should raise
    fake_objective = {"model_decomposition": {"objective_contributions": [{"id": "unknown", "location": "master"}]}}

    for wrong_data in [fake_constraint_oob, fake_variable, fake_constraint, fake_objective]:
        wrong_config = GemsOptimConfig.model_validate({"models": [{"id": config.models[0].id, **wrong_data}]})
        with pytest.raises(IntegrityError):
            dao.save_optim_config(wrong_config)

    # Save real data just to ensure the test failed for the right reason and now it works
    dao.save_optim_config(config)


@pytest.mark.parametrize(
    "content",
    [
        {"time-scope": {"first-time-step": 10, "last-time-step": 5}},  # first > last
        {"time-scope": {"first-time-step": -1, "last-time-step": 5}},  # first < 0
        {"scenario-scope": {"include": [-1]}},  # negative scenario
        {"scenario-scope": {"include": ["5-2"]}},  # invalid range as 5 > 2
        {"scenario-scope": {"include": ["abc"]}},  # invalid typing: should be 5, "5" or "0-9"
        {"solver-options": {"parameters": "THREADS 1 MAXTIME"}},  # Missing a value after MAXTIME
        {"resolution": {"mode": "unknown"}},  # invalid mode
        {"resolution": {"mode": "sequential-subproblems"}},  # missing block-length
        {"resolution": {"mode": "parallel-subproblems"}},  # missing block-length
        {
            "resolution": {"mode": "parallel-subproblems", "block-length": 168, "block-overlap": 0}
        },  # block-overlap must be lower than block-length
        {
            "resolution": {"mode": "frontal", "carry-over-length": 0}
        },  # carry-over-length not compatible with frontal mode
        {
            "resolution": {"mode": "sequential-subproblems", "block-length": 10, "block-overlap": 10}
        },  # block-overlap must be strictly lower than block-length
        {"models": [{"id": "no_library_prefix"}]},  # id must be written as "library_id.model_id"
        {"models": [{"id": "lib.model"}, {"id": "lib.model"}]},  # duplicate model id
        {
            "models": [{"id": "lib.model", "out-of-bounds-processing": {"constraints": [{"id": "c", "mode": "x"}]}}]
        },  # mode must be "cyclic" or "drop"
        {
            "models": [{"id": "lib.model", "model-decomposition": {"variables": [{"id": "v", "location": "x"}]}}]
        },  # location is not a valid enum
        {
            "models": [
                {
                    "id": "lib.model",
                    "heuristics": [
                        {
                            "id": "accurate",
                            "inputs": [],
                            "outputs": [
                                {"heuristic-element": "e", "id": "v", "type": "parameter"}
                            ],  # heuristic-element is not a valid enum
                        }
                    ],
                }
            ]
        },
        {
            "resolution": {"mode": "benders-decomposition"},
            "models": [
                {"id": "lib.model", "heuristics": [{"id": "fast", "inputs": [], "outputs": []}]}
            ],  # outputs default value does not work
        },
    ],
)
def test_invalid_configs(content: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        GemsOptimConfig.model_validate(content)


@pytest.mark.parametrize("dao_builder", ["db"], indirect=True)
def test_conversion_always_write_a_file(
    dao_10_2: StudyDao, tmp_path: Path, command_context: CommandContext, study_factory: StudyFactory
) -> None:
    dao = dao_10_2
    config = _load_example("frontal")
    dao.save_library(_build_library(config))

    assert dao.get_optim_config() is None

    # Even if the DB does not have an optim config, when converting the data to FS we should write the file.
    # Because the Simulator always needs one to run the simulation.
    session = dao._db_session  # type: ignore
    fs_dao = build_filesystem_dao(session, dao.get_version(), command_context, study_factory, tmp_path)
    converter = StudyConverter(dao, fs_dao, STUDY_VERSION_10_2, dao.matrix_service)
    converter._convert_gems()

    assert (tmp_path / "my_study" / "input" / "optim-config.yml").exists()
