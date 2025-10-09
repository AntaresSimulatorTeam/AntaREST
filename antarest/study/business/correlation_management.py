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

"""
Management of spatial correlations between the different generators.
The generators are of the same category and can be hydraulic, wind, load or solar.
"""

from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationMatrix
from antarest.study.business.study_interface import StudyInterface
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
        """
        Set the correlation coefficients of a given area from the form fields (percentage values).

        Args:
            study: study to set the correlation coefficients to.
            area_id: area to set the correlation coefficients to.
            data: correlation coefficients to set.

        Raises:
            AreaNotFound: if the area is not found or invalid.

        Returns:
            The updated correlation coefficients.
        """
        raise NotImplementedError()

    def get_correlation_matrix(self, study: StudyInterface) -> HydroCorrelationMatrix:
        return HydroCorrelationMatrix.from_hydro_correlations(study.get_study_dao().get_hydro_correlation_matrix())

    def set_correlation_matrix(self, study: StudyInterface, matrix: HydroCorrelationMatrix) -> HydroCorrelationMatrix:
        """
        Set the correlation coefficients from the coefficient matrix (values in the range -1 to 1).

        Args:
            all_areas: list of all areas in the study.
            study: study to get the correlation matrix from.
            matrix: correlation matrix to update

        Returns:
            The updated correlation matrix.
        """
        raise NotImplementedError()
