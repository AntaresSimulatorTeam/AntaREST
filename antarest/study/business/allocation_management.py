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

from typing import Dict

from antarest.core.exceptions import AllocationDataNotFound
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationMatrix
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AllocationManager:
    """
    Manage hydraulic allocation coefficients.
    """

    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_allocation_data(self, study: StudyInterface, area_id: str) -> Dict[str, float]:
        """
        Get hydraulic allocation data.

        Args:
            study: study to get the allocation data from.
            area_id: area to get the allocation data from.

        Returns:
            The allocation data.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """
        # sourcery skip: reintroduce-else, swap-if-else-branches, use-named-expression

        file_study = study.get_files()
        allocation_data = file_study.tree.get(f"input/hydro/allocation/{area_id}".split("/"), depth=2)

        if not allocation_data:
            raise AllocationDataNotFound(area_id)

        # allocation format can differ from the number of '[' (i.e. [[allocation]] or [allocation])
        return allocation_data.get("[allocation]", allocation_data.get("allocation", {}))  # type: ignore

    def get_allocation_for_area(self, study: StudyInterface, area_id: str) -> HydroAllocation:
        return study.get_study_dao().get_hydro_allocation(area_id)

    def set_allocation_for_area(self, study: StudyInterface, area_id: str, data: HydroAllocation) -> HydroAllocation:
        raise NotImplementedError()

    def get_allocation_matrix(self, study: StudyInterface) -> HydroAllocationMatrix:
        allocation_matrix_as_dict = study.get_study_dao().get_hydro_allocation_matrix()
        return HydroAllocationMatrix.from_hydro_allocations(allocation_matrix_as_dict)
