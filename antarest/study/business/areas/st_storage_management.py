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

from typing import Mapping, Sequence

from antares.study.version import StudyVersion

from antarest.core.exceptions import (
    DuplicateSTStorage,
    DuplicateSTStorageConstraintName,
    STStorageReferencedInsideAdditionalConstraints,
)
from antarest.core.model import JSON
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintCreation,
    STStorageAdditionalConstraintUpdate,
    STStorageCreation,
    STStorageUpdate,
    STStorageUpdates,
    create_st_storage,
    create_st_storage_constraint,
    update_st_storage,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.create_st_storage_constraints import (
    CreateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command.remove_multiple_storage_constraints import (
    RemoveMultipleSTStorageConstraints,
)
from antarest.study.storage.variantstudy.model.command.remove_st_storage import RemoveSTStorage
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_st_storages import UpdateSTStorages
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# ============================
#  Short-term storage manager
# ============================


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
    ) -> STStorage:
        """
        Create a new short-term storage configuration for the given `study`, `area_id`, and `form fields`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            form: Form used to Create a new short-term storage.

        Returns:
            The ID of the newly created short-term storage.
        """
        storage = create_st_storage(form, study.version)

        if study.get_study_dao().st_storage_exists(area_id, storage.id):
            raise DuplicateSTStorage(area_id, storage.id)

        command = self._make_create_cluster_cmd(area_id, form, study.version)
        study.add_commands([command])
        return storage

    def _make_create_cluster_cmd(
        self, area_id: str, cluster: STStorageCreation, study_version: StudyVersion
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
    ) -> Sequence[STStorage]:
        """
        Get the list of short-term storage configurations for the given `study`, and `area_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.

        Returns:
            The list of forms used to display the short-term storages.
        """

        return study.get_study_dao().get_all_st_storages_for_area(area_id)

    def get_all_storages_props(
        self,
        study: StudyInterface,
    ) -> Mapping[str, Mapping[str, STStorage]]:
        """
        Retrieve all short-term storages from all areas within a study.

        Args:
            study: Study from which to retrieve the storages.

        Returns:
            A mapping of area IDs to a mapping of storage IDs to storage configurations.

        Raises:
            STStorageConfigNotFound: If no storages are found in the specified area.
        """

        return study.get_study_dao().get_all_st_storages()

    def update_storages_props(
        self,
        study: StudyInterface,
        update_storages_by_areas: STStorageUpdates,
    ) -> Mapping[str, Mapping[str, STStorage]]:
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
    ) -> STStorage:
        """
        Get short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.

        Returns:
            Form used to display and edit a short-term storage.
        """
        return study.get_study_dao().get_st_storage(area_id, storage_id)

    def update_storage(
        self,
        study: StudyInterface,
        area_id: str,
        storage_id: str,
        cluster_data: STStorageUpdate,
    ) -> STStorage:
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
        storage = self.get_storage(study, area_id, storage_id)
        updated_storage = update_st_storage(storage, cluster_data)

        command = UpdateSTStorages(
            storage_properties={area_id: {storage_id: cluster_data}},
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return updated_storage

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
        # Checks storages are not referenced in any constraint
        existing_constraints = study.get_study_dao().get_st_storage_additional_constraints_for_area(area_id)
        for constraint in existing_constraints:
            for storage_id in storage_ids:
                if constraint.cluster == storage_id:
                    raise STStorageReferencedInsideAdditionalConstraints(storage_id, constraint.id)

        commands = [
            RemoveSTStorage(
                area_id=area_id,
                storage_id=storage_id,
                command_context=self._command_context,
                study_version=study.version,
            )
            for storage_id in storage_ids
        ]
        study.add_commands(commands)

    def duplicate_cluster(
        self, study: StudyInterface, area_id: str, source_id: str, new_cluster_name: str
    ) -> STStorage:
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
        if any(new_id == storage.id.lower() for storage in self.get_storages(study, area_id)):
            raise DuplicateSTStorage(area_id, new_id)

        # Cluster duplication
        current_cluster = self.get_storage(study, area_id, source_id)
        current_cluster.name = new_cluster_name

        creation_form = STStorageCreation.from_storage(current_cluster)
        create_cluster_cmd = self._make_create_cluster_cmd(area_id, creation_form, study.version)
        commands: list[CreateSTStorage | ReplaceMatrix] = [create_cluster_cmd]

        # Matrix edition
        lower_source_id = source_id.lower()

        matrices: list[tuple[str, list[list[float]]]] = []
        study_dao = study.get_study_dao()

        matrices_names = {"pmax_injection", "pmax_withdrawal", "lower_rule_curve", "upper_rule_curve", "inflows"}
        if study.version >= STUDY_VERSION_9_2:
            matrices_names.update(
                {
                    "cost_injection",
                    "cost_withdrawal",
                    "cost_level",
                    "cost_variation_injection",
                    "cost_variation_withdrawal",
                }
            )

        for matrix_name in matrices_names:
            method = getattr(study_dao, f"get_st_storage_{matrix_name}")
            matrix = method(area_id, lower_source_id).to_numpy().tolist()
            matrices.append((f"input/st-storage/series/{area_id}/{new_id}/{matrix_name}", matrix))

        # Add commands
        for matrix in matrices:
            cmd = ReplaceMatrix(
                target=matrix[0],
                matrix=matrix[1],
                command_context=self._command_context,
                study_version=study.version,
            )
            commands.append(cmd)

        study.add_commands(commands)

        return create_st_storage(creation_form, study.version)

    @staticmethod
    def get_table_schema() -> JSON:
        return STStorage.model_json_schema()

    ##########################
    # Additional constraints part
    ##########################

    def get_all_additional_constraints(self, study: StudyInterface) -> dict[str, list[STStorageAdditionalConstraint]]:
        """
        Gets all short-term storage additional constraints inside the study.

        Args:
            study: The study object.
        """
        return study.get_study_dao().get_all_st_storage_additional_constraints()

    def get_additional_constraints_for_area(
        self, study: StudyInterface, area_id: str
    ) -> list[STStorageAdditionalConstraint]:
        """
        Gets additional constraints for a given area.

        Args:
            study: The study object.
            area_id: The area ID.
        """
        return study.get_study_dao().get_st_storage_additional_constraints_for_area(area_id)

    def get_additional_constraints(
        self, study: StudyInterface, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        """
        Gets additional constraints for a given short-term storage.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The short-term storages ID.
        """
        return study.get_study_dao().get_st_storage_additional_constraints(area_id, storage_id)

    def create_additional_constraints(
        self, study: StudyInterface, area_id: str, constraints: list[STStorageAdditionalConstraintCreation]
    ) -> list[STStorageAdditionalConstraint]:
        """
        Creates several additional-constraints for a given area.

        Args:
            study: The study object.
            area_id: The area ID.
            constraints: List of constraints to create.
        """
        created_constraints = [create_st_storage_constraint(c) for c in constraints]

        # Checks we're not duplicating existing constraints
        existing_constraints = study.get_study_dao().get_st_storage_additional_constraints_for_area(area_id)
        existing_ids = {c.id for c in existing_constraints}
        for constraint in created_constraints:
            if constraint.id in existing_ids:
                raise DuplicateSTStorageConstraintName(area_id, constraint.id)

        # Apply the command
        command = CreateSTStorageAdditionalConstraints(
            area_id=area_id,
            constraints=constraints,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        # Return the created constraints
        return created_constraints

    def update_additional_constraint(
        self,
        study: StudyInterface,
        storage_id: str,
        constraint_id: str,
        constraint: STStorageAdditionalConstraintUpdate,
    ) -> STStorageAdditionalConstraint:
        raise NotImplementedError()

    def delete_additional_constraints(self, study: StudyInterface, area_id: str, constraint_ids: list[str]) -> None:
        """
        Removes several additional-constraints for a given area.

        Args:
            study: The study object.
            area_id: The area ID.
            constraint_ids: IDs list of constraints to remove.
        """
        command = RemoveMultipleSTStorageConstraints(
            area_id=area_id,
            ids=constraint_ids,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
