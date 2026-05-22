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

from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferencesUpdate,
    UnfeasibleProblemBehavior,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_optimization_preferences import (
    UpdateOptimizationPreferences,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestUpdateOptimizationPreferences:
    def test_update_optimization_preferences(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        study = empty_study_880
        dao = build_dao_from_file_study(study, command_context)

        default_values = study.tree.get(["settings", "generaldata", "optimization"])

        args = {
            "hurdleCosts": False,
            "transmissionCapacities": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.ERROR_DRY,
        }

        properties = OptimizationPreferencesUpdate.model_validate(args)

        command = UpdateOptimizationPreferences(
            parameters=properties, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(dao)
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

    def test_version_10(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        assert dao_10_0.get_optimization_preferences().include_reserves is False  # Default value

        version = dao_10_0.get_version()
        properties = OptimizationPreferencesUpdate(include_reserves=True)
        command = UpdateOptimizationPreferences(
            parameters=properties, command_context=command_context, study_version=version
        )
        output = command.apply(dao_10_0)
        assert output.status

        assert dao_10_0.get_optimization_preferences().include_reserves is True

        # Ensure we cannot update the field `include_reserves` for a study version before 10.0
        with pytest.raises(
            ValueError, match="Field include_reserves is not a valid field for study version before 10.0"
        ):
            UpdateOptimizationPreferences(
                parameters=properties, command_context=command_context, study_version=STUDY_VERSION_9_3
            )
