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


from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationMatrix
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.replace_hydro_correlation import ReplaceHydroCorrelation
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class CorrelationManager:
    """
    This manager allows you to read and write the hydraulic correlation matrices of a raw study or a variant.
    Their usage is deprecated.
    """

    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_correlation_for_area(self, study: StudyInterface, area_id: str) -> HydroCorrelation:
        return study.get_study_dao().get_hydro_correlation(area_id)

    def set_correlation_for_area(self, study: StudyInterface, area_id: str, data: HydroCorrelation) -> HydroCorrelation:
        command = ReplaceHydroCorrelation(
            command_context=self._command_context, study_version=study.version, area_id=area_id, correlation=data
        )
        study.add_commands([command])
        return data

    def get_correlation_matrix(self, study: StudyInterface) -> HydroCorrelationMatrix:
        return study.get_study_dao().get_hydro_correlation_matrix()
