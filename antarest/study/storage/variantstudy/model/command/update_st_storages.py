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
from typing import Any, List, Optional, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.sts_model import (
    STStorageUpdates,
    update_st_storage,
    validate_st_storage_against_version,
)
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


class UpdateSTStorages(ICommand):
    """
    Command used to update several short-term storages
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_ST_STORAGES

    # Command parameters
    # ==================

    storage_properties: STStorageUpdates

    @model_validator(mode="after")
    def validate_against_version(self) -> Self:
        for value in self.storage_properties.values():
            for properties in value.values():
                validate_st_storage_against_version(self.study_version, properties)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        all_storages = study_data.get_all_st_storages()

        for area_id, value in self.storage_properties.items():
            if area_id not in all_storages:
                return command_failed(f"The area '{area_id}' is not found.")

            new_storages = []
            for storage_id, new_properties in value.items():
                if storage_id not in all_storages[area_id]:
                    return command_failed(
                        f"The short-term storage '{storage_id}' in the area '{area_id}' is not found."
                    )

                current_storage = all_storages[area_id][storage_id]
                new_storage = update_st_storage(current_storage, new_properties, self.study_version)
                new_storages.append(new_storage)

            memory_mapping[area_id] = new_storages

        for area_id, new_storages in memory_mapping.items():
            study_data.save_st_storages(area_id, new_storages)

        return command_succeeded("The short-term storages were successfully updated.")

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}

        for area_id, value in self.storage_properties.items():
            for storage_id, properties in value.items():
                args.setdefault(area_id, {})[storage_id] = properties.model_dump(mode="json", exclude_unset=True)

        return CommandDTO(
            action=self.command_name.value, args={"storage_properties": args}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
