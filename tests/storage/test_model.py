# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import pytest

from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.model import STUDY_VERSION_7_0
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    DistrictSet,
    FileStudyTreeConfig,
    FileStudyTreeConfigDTO,
    Mode,
    Simulation,
    validate_config,
)
from antarest.study.storage.rawstudy.model.filesystem.config.validation import study_version_context


@pytest.fixture
def config() -> FileStudyTreeConfig:
    return FileStudyTreeConfig(
        study_path=Path("test"),
        path=Path("curr_path"),
        study_id="study_id",
        version=STUDY_VERSION_7_0,
        output_path=Path("output_path"),
        areas={
            "a": Area(
                name="a",
                links={},
                thermals=[ThermalCluster(name="cluster")],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
        sets={"s": DistrictSet()},
        outputs={
            "o": Simulation(
                name="o",
                date="date",
                mode=Mode.ECONOMY,
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=True,
                playlist=[0],
                xpansion="",
            )
        },
        bindings=[BindingConstraint(**{"name": "b1", "time_step": BindingConstraintFrequency.DAILY})],
        store_new_set=False,
        archive_input_series=["?"],
        enr_modelling="aggregated",
    )


def test_file_study_tree_config_dto(config: FileStudyTreeConfig):
    config_dto = FileStudyTreeConfigDTO.from_build_config(config)
    assert sorted(list(config_dto.model_dump())) == sorted(list(config.__dict__))
    assert config_dto.to_build_config() == config

    config_dict = config_dto.model_dump()
    parsed_config = FileStudyTreeConfigDTO.model_validate(
        config_dict, context=study_version_context(STUDY_VERSION_7_0)
    ).to_build_config()
    assert parsed_config == config


def test_file_study_tree_config_round_trip(config: FileStudyTreeConfig):
    config_dict = FileStudyTreeConfigDTO.from_build_config(config).model_dump()
    parsed_config = validate_config(STUDY_VERSION_7_0, config_dict)
    assert parsed_config == config
