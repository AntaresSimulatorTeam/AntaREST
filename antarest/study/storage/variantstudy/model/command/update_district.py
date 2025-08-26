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

from typing import List, Optional

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.district_model import DistrictBaseFilter
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateDistrict(ICommand):
    """
    Command used to update a district in a study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_DISTRICT

    # Command parameters
    # ==================

    id: str
    base_filter: Optional[DistrictBaseFilter] = None
    filter_items: Optional[List[str]] = None
    output: Optional[bool] = None
    comments: Optional[str] = None

    # def update_in_config(self, study_data: FileStudyTreeConfig) -> Dict[str, Any]:
    #     base_set = study_data.sets[self.id]

    #     if self.base_filter:
    #         inverted_set = self.base_filter == DistrictBaseFilter.add_all
    #     else:
    #         inverted_set = base_set.inverted_set
    #     study_data.sets[self.id].areas = self.filter_items or base_set.areas
    #     study_data.sets[self.id].output = self.output if self.output is not None else base_set.output
    #     study_data.sets[self.id].inverted_set = inverted_set

    #     item_key = "-" if inverted_set else "+"
    #     return {
    #         "district_id": self.id,
    #         "item_key": item_key,
    #     }

    # @override
    # def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
    #     if self.id not in study_data.config.sets:
    #         return command_failed(message=f"District '{self.id}' does not exist and should be created")

    #     data = self.update_in_config(study_data.config)

    #     sets = study_data.tree.get(["input", "areas", "sets"])
    #     district_id = data["district_id"]
    #     item_key = data["item_key"]
    #     apply_filter = (
    #         self.base_filter.value if self.base_filter else sets.get("apply-filter", DistrictBaseFilter.remove_all)
    #     )
    #     study_data.tree.save(
    #         {
    #             "caption": sets[district_id]["caption"],
    #             "apply-filter": apply_filter,
    #             item_key: self.filter_items,
    #             "output": study_data.config.sets[district_id].output,
    #             "comments": self.comments,
    #         },
    #         ["input", "areas", "sets", district_id],
    #     )

    #     return command_succeeded(message=self.id)

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.district_exists(self.id):
            return command_failed(message=f"District '{self.id}' does not exist and should be created")

        district = study_data.get_district(self.id)  # to check if district exists

        updated_district = district.model_copy(
            update={
                "areas": self.filter_items,
                "output": self.output,
                "comments": self.comments,
            }
        )

        try:
            study_data.save_district(updated_district, self.base_filter)
        except AreaNotFound as e:
            return command_failed(message=f"Area not found {e}")

        return command_succeeded(message=self.id)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args={
                "id": self.id,
                "base_filter": self.base_filter.value if self.base_filter else None,
                "filter_items": self.filter_items,
                "output": self.output,
                "comments": self.comments,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
