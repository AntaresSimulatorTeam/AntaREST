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

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_district import DistrictBaseFilter
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

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        base_set = study_data.sets[self.id]
        if self.id not in study_data.sets:
            return (
                CommandOutput(
                    status=False,
                    message=f"District '{self.id}' does not exist and should be created",
                ),
                dict(),
            )

        if self.base_filter:
            base_filter = self.base_filter or DistrictBaseFilter.remove_all
            inverted_set = base_filter == DistrictBaseFilter.add_all
        else:
            inverted_set = base_set.inverted_set
        study_data.sets[self.id].areas = self.filter_items or base_set.areas
        study_data.sets[self.id].output = self.output if self.output is not None else base_set.output
        study_data.sets[self.id].inverted_set = inverted_set

        item_key = "-" if inverted_set else "+"
        return CommandOutput(status=True, message=self.id), {
            "district_id": self.id,
            "item_key": item_key,
        }

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output
        sets = study_data.tree.get(["input", "areas", "sets"])
        district_id = data["district_id"]
        item_key = data["item_key"]
        apply_filter = (
            self.base_filter.value if self.base_filter else sets.get("apply-filter", DistrictBaseFilter.remove_all)
        )
        study_data.tree.save(
            {
                "caption": sets[district_id]["caption"],
                "apply-filter": apply_filter,
                item_key: self.filter_items,
                "output": study_data.config.sets[district_id].output,
                "comments": self.comments,
            },
            ["input", "areas", "sets", district_id],
        )

        return output

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
