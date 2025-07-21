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
from antarest.study.business.model.config.optimization_config import (
    OptimizationPreferencesUpdate,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_optimization_preferences import (
    UpdateOptimizationPreferences,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateOptimizationPreferences:
    def _set_up(self, study: FileStudy, command_context: CommandContext) -> None:
        self.study = study

    def test_update_optimization_preferences(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880

        default_values = {
            "include-constraints": True,
            "include-hurdlecosts": True,
            "transmission-capacities": True,
            "include-tc-minstablepower": True,
            "include-exportstructure": False,
            "include-tc-min-ud-time": True,
            "include-dayahead": True,
            "include-primaryreserve": True,
            "include-strategicreserve": True,
            "include-spinningreserve": True,
            "include-exportmps": False,
            "include-unfeasible-problem-behavior": UnfeasibleProblemBehavior.ERROR_VERBOSE,
            "simplex-range": SimplexOptimizationRange.WEEK,
            "link-type": "local",
        }

        args = {
            "hurdleCosts": False,
            "transmissionCapacities": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.ERROR_DRY,
        }

        properties = OptimizationPreferencesUpdate.model_validate(args)

        command = UpdateOptimizationPreferences(
            parameters=properties, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study)
        assert output.status

        default_values.update(
            {
                "include-hurdlecosts": False,
                "transmission-capacities": False,
                "include-unfeasible-problem-behavior": UnfeasibleProblemBehavior.ERROR_DRY,
            }
        )

        optimization_preferences = study.tree.get(["settings", "generaldata", "optimization"])

        assert optimization_preferences == default_values
