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
from polars import DataFrame

from antarest.study.business.study_interface import StudyInterface


class GemsInputMatrixManagement:
    """
    Interface for managing input matrices in the study.
    """

    def get_gems_matrix(self, study: StudyInterface, component_id: str, parameter_id: str) -> DataFrame:
        """
        Fetches the input matrix related to a GEMS component parameter for a given study.

        Args:
            study (StudyInterface): The interface of the study.
            component_id (str): The ID of the GEMS component.
            parameter_id (str): The ID of the GEMS parameter.

        Returns:
            The input matrix as a DataFrame.
        """
        return study.get_study_dao().get_parameter_series(component_id, parameter_id)
