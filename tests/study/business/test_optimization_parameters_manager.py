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


from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    TransmissionCapacities,
)
from antarest.study.business.optimization_management import OptimizationManager
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface


def test_missing_section(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    # Remove the section from the generaldata file
    study = empty_study_880
    general_data_content = study.tree.get(["settings", "generaldata"])
    del general_data_content["optimization"]
    study.tree.save(general_data_content, ["settings", "generaldata"])
    # Ensures we're still able to read the data.
    manager = OptimizationManager(command_context)
    params = manager.get_optimization_preferences(file_study_interface(study))
    # v8.8 study: helper initializes v8.4+ default transmission_capacities to LOCAL_VALUES.
    assert params == OptimizationPreferences(transmission_capacities=TransmissionCapacities.LOCAL_VALUES)


def test_section_not_in_lowercase(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    # Rewrite the section not in lowercase
    study = empty_study_880
    general_data_content = study.tree.get(["settings", "generaldata"])
    general_data_content["OPtimizaTION"] = general_data_content.pop("optimization")
    study.tree.save(general_data_content, ["settings", "generaldata"])
    # Ensures we're still able to read the data.
    manager = OptimizationManager(command_context)
    params = manager.get_optimization_preferences(file_study_interface(study))
    assert params == OptimizationPreferences(transmission_capacities=TransmissionCapacities.LOCAL_VALUES)
