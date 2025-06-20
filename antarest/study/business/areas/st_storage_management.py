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

import collections
import operator
from typing import Any, List, Mapping, MutableMapping, Sequence

from antares.study.version import StudyVersion

from antarest.core.exceptions import (
    AreaNotFound,
    ChildNotFoundError,
    DuplicateSTStorage,
    STStorageConfigNotFound,
    STStorageNotFound,
)
from antarest.core.model import JSON
from antarest.core.requests import CaseInsensitiveDict
from antarest.study.business.model.sts_model import (
    STStorageCreation,
    STStorageOutput,
    STStorageUpdate,
    STStorageUpdates,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStoragePropertiesType,
    create_st_storage_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.remove_st_storage import RemoveSTStorage
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_st_storages import UpdateSTStorages
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# ============================
#  Short-term storage manager
# ============================

_STORAGE_LIST_PATH = "input/st-storage/clusters/{area_id}/list/{storage_id}"
_STORAGE_SERIES_PATH = "input/st-storage/series/{area_id}/{storage_id}/{ts_name}"
_ALL_STORAGE_PATH = "input/st-storage/clusters"


def _get_values_by_ids(file_study: FileStudy, area_id: str) -> Mapping[str, Mapping[str, Any]]:
    path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id="")[:-1]
    try:
        return CaseInsensitiveDict(file_study.tree.get(path.split("/"), depth=3))
    except ChildNotFoundError:
        raise AreaNotFound(area_id) from None
    except KeyError:
        raise STStorageConfigNotFound(path, area_id) from None


def create_storage_output(
    study_version: StudyVersion,
    cluster_id: str,
    config: Mapping[str, Any],
) -> "STStorageOutput":
    obj = create_st_storage_config(study_version=study_version, **config, id=cluster_id)
    kwargs = obj.model_dump(mode="json", by_alias=False)
    return STStorageOutput(**kwargs)


class STStorageManager:
    """
    Manage short-term storage configuration in a study
    """

    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def create_storage(
        self,
        study: StudyInterface,
        area_id: str,
        form: STStorageCreation,
    ) -> STStorageOutput:
        """
        Create a new short-term storage configuration for the given `study`, `area_id`, and `form fields`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            form: Form used to Create a new short-term storage.

        Returns:
            The ID of the newly created short-term storage.
        """
        file_study = study.get_files()
        values_by_ids = _get_values_by_ids(file_study, area_id)

        storage = form.to_properties(study.version)
        storage_id = storage.get_id()
        values = values_by_ids.get(storage_id)
        if values is not None:
            raise DuplicateSTStorage(area_id, storage_id)

        command = self._make_create_cluster_cmd(area_id, storage, study.version)
        study.add_commands([command])
        output = self.get_storage(study, area_id, storage_id=storage_id)
        return output

    def _make_create_cluster_cmd(
        self, area_id: str, cluster: STStoragePropertiesType, study_version: StudyVersion
    ) -> CreateSTStorage:
        command = CreateSTStorage(
            area_id=area_id,
            parameters=cluster,
            command_context=self._command_context,
            study_version=study_version,
        )
        return command

    def get_storages(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> Sequence[STStorageOutput]:
        """
        Get the list of short-term storage configurations for the given `study`, and `area_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.

        Returns:
            The list of forms used to display the short-term storages.
        """

        file_study = study.get_files()
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id="")[:-1]
        try:
            config = file_study.tree.get(path.split("/"), depth=3)
        except ChildNotFoundError:
            raise AreaNotFound(area_id) from None
        except KeyError:
            raise STStorageConfigNotFound(path, area_id) from None

        # Sort STStorageConfig by groups and then by name
        order_by = operator.attrgetter("group", "name")
        storages = [create_storage_output(study.version, storage_id, options) for storage_id, options in config.items()]
        return sorted(storages, key=order_by)

    def get_all_storages_props(
        self,
        study: StudyInterface,
    ) -> Mapping[str, Mapping[str, STStorageOutput]]:
        """
        Retrieve all short-term storages from all areas within a study.

        Args:
            study: Study from which to retrieve the storages.

        Returns:
            A mapping of area IDs to a mapping of storage IDs to storage configurations.

        Raises:
            STStorageConfigNotFound: If no storages are found in the specified area.
        """

        file_study = study.get_files()
        path = _ALL_STORAGE_PATH
        try:
            # may raise KeyError if the path is missing
            storages = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            storages = {area_id: cluster_list["list"] for area_id, cluster_list in storages.items()}
        except KeyError:
            raise STStorageConfigNotFound(path) from None

        storages_by_areas: MutableMapping[str, MutableMapping[str, STStorageOutput]]
        storages_by_areas = collections.defaultdict(dict)
        for area_id, cluster_obj in storages.items():
            for cluster_id, cluster in cluster_obj.items():
                storages_by_areas[area_id][cluster_id] = create_storage_output(study.version, cluster_id, cluster)

        return storages_by_areas

    def update_storages_props(
        self,
        study: StudyInterface,
        update_storages_by_areas: STStorageUpdates,
    ) -> Mapping[str, Mapping[str, STStorageOutput]]:
        old_storages_by_areas = self.get_all_storages_props(study)
        new_storages_by_areas = {area_id: dict(clusters) for area_id, clusters in old_storages_by_areas.items()}

        # Prepare the command to update the storage clusters.
        command = UpdateSTStorages(
            storage_properties=update_storages_by_areas,
            command_context=self._command_context,
            study_version=study.version,
        )

        # Prepare the return of the method
        for area_id, update_storages_by_ids in update_storages_by_areas.items():
            old_storages_by_ids = old_storages_by_areas[area_id]
            for storage_id, update_cluster in update_storages_by_ids.items():
                # Update the storage cluster properties.
                old_cluster = old_storages_by_ids[storage_id]
                new_cluster = old_cluster.model_copy(update=update_cluster.model_dump(mode="json", exclude_none=True))
                new_storages_by_areas[area_id][storage_id] = new_cluster

        study.add_commands([command])
        return new_storages_by_areas

    def get_storage(
        self,
        study: StudyInterface,
        area_id: str,
        storage_id: str,
    ) -> STStorageOutput:
        """
        Get short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.

        Returns:
            Form used to display and edit a short-term storage.
        """

        file_study = study.get_files()
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            config = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageNotFound(path, storage_id) from None
        return create_storage_output(study.version, storage_id, config)

    def update_storage(
        self,
        study: StudyInterface,
        area_id: str,
        storage_id: str,
        cluster_data: STStorageUpdate,
    ) -> STStorageOutput:
        """
        Set short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            cluster_data: Form used to Update a short-term storage.
        Returns:
            Updated form of short-term storage.
        """
        path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        file_study = study.get_files()

        try:
            area = file_study.config.areas[area_id]
        except KeyError:
            raise AreaNotFound(area_id)

        sts_storage = next((sts for sts in area.st_storages if sts.id == storage_id), None)
        if sts_storage is None:
            raise STStorageNotFound(path, storage_id)

        updated_sts = sts_storage.model_copy(update=cluster_data.model_dump(exclude_unset=True, exclude_none=True))

        command = UpdateSTStorages(
            storage_properties={area_id: {storage_id: cluster_data}},
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        return STStorageOutput(**updated_sts.model_dump(exclude={"id"}), id=storage_id)

    def delete_storages(
        self,
        study: StudyInterface,
        area_id: str,
        storage_ids: Sequence[str],
    ) -> None:
        """
        Delete short-term storage configurations form the given study and area_id.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_ids: IDs list of short-term storages to remove.
        """
        file_study = study.get_files()
        values_by_ids = _get_values_by_ids(file_study, area_id)

        for storage_id in storage_ids:
            if storage_id not in values_by_ids:
                path = _STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
                raise STStorageNotFound(path, storage_id)

        commands = []
        for storage_id in storage_ids:
            commands.append(
                RemoveSTStorage(
                    area_id=area_id,
                    storage_id=storage_id,
                    command_context=self._command_context,
                    study_version=study.version,
                )
            )
        study.add_commands(commands)

    def duplicate_cluster(
        self, study: StudyInterface, area_id: str, source_id: str, new_cluster_name: str
    ) -> STStorageOutput:
        """
        Creates a duplicate cluster within the study area with a new name.

        Args:
            study: The study in which the cluster will be duplicated.
            area_id: The identifier of the area where the cluster will be duplicated.
            source_id: The identifier of the cluster to be duplicated.
            new_cluster_name: The new name for the duplicated cluster.

        Returns:
            The duplicated cluster configuration.

        Raises:
            DuplicateSTStorage: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_cluster_name)
        lower_new_id = new_id.lower()
        if any(lower_new_id == storage.id.lower() for storage in self.get_storages(study, area_id)):
            raise DuplicateSTStorage(area_id, new_id)

        # Cluster duplication
        current_cluster = self.get_storage(study, area_id, source_id)
        current_cluster.name = new_cluster_name
        fields_to_exclude = {"id"}
        # We should remove the field 'enabled' for studies before v8.8 as it didn't exist
        if study.version < STUDY_VERSION_8_8:
            fields_to_exclude.add("enabled")
        creation_form = STStorageCreation.model_validate(
            current_cluster.model_dump(mode="json", by_alias=False, exclude=fields_to_exclude)
        )

        new_config = creation_form.to_properties(study.version)
        create_cluster_cmd = self._make_create_cluster_cmd(area_id, new_config, study.version)

        # Matrix edition
        lower_source_id = source_id.lower()
        # noinspection SpellCheckingInspection
        ts_names = ["pmax_injection", "pmax_withdrawal", "lower_rule_curve", "upper_rule_curve", "inflows"]
        if study.version >= STUDY_VERSION_9_2:
            ts_names.extend(
                [
                    "cost_injection",
                    "cost_withdrawal",
                    "cost_level",
                    "cost_variation_injection",
                    "cost_variation_withdrawal",
                ]
            )

        source_paths = [
            _STORAGE_SERIES_PATH.format(area_id=area_id, storage_id=lower_source_id, ts_name=ts_name)
            for ts_name in ts_names
        ]
        new_paths = [
            _STORAGE_SERIES_PATH.format(area_id=area_id, storage_id=lower_new_id, ts_name=ts_name)
            for ts_name in ts_names
        ]

        # Prepare and execute commands
        file_study = study.get_files()
        commands: List[CreateSTStorage | ReplaceMatrix] = [create_cluster_cmd]
        for source_path, new_path in zip(source_paths, new_paths):
            current_matrix = file_study.tree.get(source_path.split("/"))["data"]
            command = ReplaceMatrix(
                target=new_path,
                matrix=current_matrix,
                command_context=self._command_context,
                study_version=study.version,
            )
            commands.append(command)

        study.add_commands(commands)

        return STStorageOutput(**new_config.model_dump(mode="json", by_alias=False))

    @staticmethod
    def get_table_schema() -> JSON:
        return STStorageOutput.model_json_schema()
