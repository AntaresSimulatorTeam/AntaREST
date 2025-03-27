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
from typing import Any, List, Optional

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.model.sts_model import STStorageUpdates
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfigType,
    create_st_storage_config,
    create_st_storage_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, IdMapping
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
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
    def validate_properties_against_version(self) -> "UpdateSTStorages":
        for value in self.storage_properties.values():
            for properties in value.values():
                properties.verify_model_against_version(self.study_version)
        return self

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for area_id, value in self.storage_properties.items():
            if area_id not in study_data.areas:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found."), {}

            storage_mapping: dict[str, tuple[int, STStorageConfigType]] = {}
            for index, storage in enumerate(study_data.areas[area_id].st_storages):
                storage_mapping[transform_name_to_id(storage.id)] = (index, storage)

            for storage_id in value:
                if storage_id not in storage_mapping:
                    return (
                        CommandOutput(
                            status=False,
                            message=f"The short-term storage '{storage_id}' in the area '{area_id}' is not found.",
                        ),
                        {},
                    )
                index, storage = storage_mapping[storage_id]
                study_data.areas[area_id].st_storages[index] = self.update_st_storage_config(area_id, storage)

        return CommandOutput(status=True, message="The short-term storages were successfully updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, value in self.storage_properties.items():
            ini_path = ["input", "st-storage", "clusters", area_id, "list"]

            try:
                all_clusters_for_area = study_data.tree.get(ini_path)
            except ChildNotFoundError:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found.")

            # Validates the Ini file
            id_mapping = IdMapping(create_st_storage_properties, all_clusters_for_area, self.study_version)

            for storage_id, properties in value.items():
                if not id_mapping.asserts_id_exists(storage_id):
                    return CommandOutput(
                        status=False,
                        message=f"The short-term storage '{storage_id}' in the area '{area_id}' is not found.",
                    )
                # Performs the update
                new_properties_dict = properties.model_dump(mode="json", by_alias=False, exclude_unset=True)
                storage_key, current_properties_obj = id_mapping.get_key_and_properties(storage_id)
                updated_obj = current_properties_obj.model_copy(update=new_properties_dict)
                all_clusters_for_area[storage_key] = updated_obj.model_dump(mode="json", by_alias=True)

            study_data.tree.save(data=all_clusters_for_area, url=ini_path)

        output, _ = self._apply_config(study_data.config)

        return output

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

    def update_st_storage_config(self, area_id: str, storage: STStorageConfigType) -> STStorageConfigType:
        # Set the object to the correct version
        versioned_storage = create_st_storage_config(
            study_version=self.study_version, **storage.model_dump(exclude_unset=True, exclude_none=True)
        )
        # Update the object with the new properties
        updated_versioned_storage = versioned_storage.model_copy(
            update=self.storage_properties[area_id][transform_name_to_id(storage.id)].model_dump(
                exclude_unset=True, exclude_none=True
            )
        )
        # Create the new object to be saved
        storage_config = create_st_storage_config(
            study_version=self.study_version,
            **updated_versioned_storage.model_dump(),
        )
        return storage_config
