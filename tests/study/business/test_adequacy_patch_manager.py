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
import copy

from antarest.study.business.adequacy_patch_management import AdequacyPatchManager
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters, PriceTakingOrder
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface

EXPECTED_PARAMS = AdequacyPatchParameters(
    enable_adequacy_patch=False,
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch=True,
    price_taking_order=PriceTakingOrder.DENS,
    include_hurdle_cost_csr=False,
    check_csr_cost_function=False,
    threshold_initiate_curtailment_sharing_rule=1,
    threshold_display_local_matching_rule_violations=0,
    threshold_csr_variable_bounds_relaxation=7,
    ntc_between_physical_areas_out_adequacy_patch=True,
    redispatch=None,
)


def test_missing_section(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    # Remove the section from the generaldata file
    study = empty_study_880
    general_data_content = study.tree.get(["settings", "generaldata"])
    del general_data_content["adequacy patch"]
    study.tree.save(general_data_content, ["settings", "generaldata"])
    # Ensures we're still able to read the data.
    manager = AdequacyPatchManager(command_context)
    params = manager.get_adequacy_patch_parameters(file_study_interface(study))
    assert params == EXPECTED_PARAMS


def test_section_not_in_lowercase(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    # Rewrite the section not in lowercase
    study = empty_study_880
    general_data_content = study.tree.get(["settings", "generaldata"])
    general_data_content["Adequacy PATCH"] = general_data_content.pop("adequacy patch")
    general_data_content["Adequacy PATCH"]["price-taking-order"] = "Load"
    study.tree.save(general_data_content, ["settings", "generaldata"])
    # Ensures we're still able to read the data.
    manager = AdequacyPatchManager(command_context)
    params = manager.get_adequacy_patch_parameters(file_study_interface(study))
    expected_params = copy.deepcopy(EXPECTED_PARAMS)
    expected_params.price_taking_order = PriceTakingOrder.LOAD
    assert params == expected_params
