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
    DuplicateRenewableCluster,
)
from antarest.core.model import JSON
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterCreation,
    RenewableClusterUpdate,
    RenewableClusterUpdates,
    create_renewable_cluster,
    update_renewable_cluster,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_renewables_clusters import UpdateRenewablesClusters
from antarest.study.storage.variantstudy.model.command_context import CommandContext

_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/renewables/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/renewables/clusters"


class RenewableManager:
    """
    A manager class responsible for handling operations related to renewable clusters within a study.
    """

    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_clusters(self, study: StudyInterface, area_id: str) -> Sequence[RenewableCluster]:
        """
        Fetches all clusters related to a specific area in a study.

        Returns:
            List of cluster output for all clusters.

        Raises:
            RenewableClusterConfigNotFound: If the clusters configuration for the specified area is not found.
        """
        return study.get_study_dao().get_all_renewables_for_area(area_id)

    def get_all_renewables_props(
        self,
        study: StudyInterface,
    ) -> Mapping[str, Mapping[str, RenewableCluster]]:
        """
        Retrieve all renewable clusters from all areas within a study.

        Args:
            study: Study from which to retrieve the clusters.

        Returns:
            A mapping of area IDs to a mapping of cluster IDs to cluster output.

        Raises:
            RenewableClusterConfigNotFound: If no clusters are found in the specified area.
        """
        return study.get_study_dao().get_all_renewables()

    def create_cluster(
        self, study: StudyInterface, area_id: str, cluster_data: RenewableClusterCreation
    ) -> RenewableCluster:
        """
        Creates a new cluster within an area in the study.

        Args:
            study: The study to search within.
            area_id: The identifier of the area.
            cluster_data: The data used to create the cluster configuration.

        Returns:
            The newly created cluster.
        """
        command = self._make_create_cluster_cmd(area_id, cluster_data, study.version)
        study.add_commands([command])
        return create_renewable_cluster(cluster_data, study.version)

    def _make_create_cluster_cmd(
        self, area_id: str, cluster_creation: RenewableClusterCreation, study_version: StudyVersion
    ) -> CreateRenewablesCluster:
        command = CreateRenewablesCluster(
            area_id=area_id,
            parameters=cluster_creation,
            command_context=self._command_context,
            study_version=study_version,
        )
        return command

    def get_cluster(self, study: StudyInterface, area_id: str, cluster_id: str) -> RenewableCluster:
        """
        Retrieves a single cluster's data for a specific area in a study.

        Args:
            study: The study to search within.
            area_id: The identifier of the area.
            cluster_id: The identifier of the cluster to retrieve.

        Returns:
            The cluster output representation.

        Raises:
            RenewableClusterNotFound: If the specified cluster is not found within the area.
        """
        return study.get_study_dao().get_renewable(area_id, cluster_id)

    def update_cluster(
        self,
        study: StudyInterface,
        area_id: str,
        cluster_id: str,
        cluster_data: RenewableClusterUpdate,
    ) -> RenewableCluster:
        """
        Updates the configuration of an existing cluster within an area in the study.

        Args:
            study: The study where the cluster exists.
            area_id: The identifier of the area where the cluster is located.
            cluster_id: The identifier of the cluster to be updated.
            cluster_data: The new data for updating the cluster configuration.

        Returns:
            The updated cluster configuration.

        Raises:
            RenewableClusterNotFound: If the cluster to update is not found.
        """

        renewable_cluster = self.get_cluster(study, area_id, cluster_id)
        updated_renewable_cluster = update_renewable_cluster(renewable_cluster, cluster_data)

        command = UpdateRenewablesClusters(
            cluster_properties={area_id: {cluster_id: cluster_data}},
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return updated_renewable_cluster

    def delete_clusters(self, study: StudyInterface, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Deletes multiple clusters from an area in the study.

        Args:
            study: The study from which clusters will be deleted.
            area_id: The identifier of the area where clusters will be deleted.
            cluster_ids: A sequence of cluster identifiers to be deleted.
        """
        commands = [
            RemoveRenewablesCluster(
                area_id=area_id,
                cluster_id=cluster_id,
                command_context=self._command_context,
                study_version=study.version,
            )
            for cluster_id in cluster_ids
        ]

        study.add_commands(commands)

    def duplicate_cluster(
        self,
        study: StudyInterface,
        area_id: str,
        source_id: str,
        new_cluster_name: str,
    ) -> RenewableCluster:
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
            DuplicateRenewableCluster: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_cluster_name, lower=False)
        lower_new_id = new_id.lower()
        if any(lower_new_id == cluster.id.lower() for cluster in self.get_clusters(study, area_id)):
            raise DuplicateRenewableCluster(area_id, new_id)

        # Cluster duplication
        version = study.version
        current_cluster = self.get_cluster(study, area_id, source_id)
        current_cluster.name = new_cluster_name
        creation_form = RenewableClusterCreation.from_cluster(current_cluster)
        create_cluster_cmd = self._make_create_cluster_cmd(area_id, creation_form, version)

        # Matrix edition
        new_path = f"input/renewables/series/{area_id}/{lower_new_id}/series"

        # Prepare and execute commands
        current_matrix = study.get_study_dao().get_renewable_series(area_id, source_id.lower()).to_numpy().tolist()
        replace_matrix_cmd = ReplaceMatrix(
            target=new_path, matrix=current_matrix, command_context=self._command_context, study_version=version
        )
        commands = [create_cluster_cmd, replace_matrix_cmd]
        study.add_commands(commands)

        return create_renewable_cluster(creation_form, version)

    def update_renewables_props(
        self,
        study: StudyInterface,
        update_renewables_by_areas: RenewableClusterUpdates,
    ) -> Mapping[str, Mapping[str, RenewableCluster]]:
        old_renewables_by_areas = self.get_all_renewables_props(study)
        new_renewables_by_areas = {area_id: dict(clusters) for area_id, clusters in old_renewables_by_areas.items()}

        # Prepare the command to update the renewable clusters.
        command = UpdateRenewablesClusters(
            cluster_properties=update_renewables_by_areas,
            command_context=self._command_context,
            study_version=study.version,
        )

        # Prepare the return of the method
        for area_id, update_renewables_by_ids in update_renewables_by_areas.items():
            old_renewables_by_ids = old_renewables_by_areas[area_id]
            for renewable_id, update_cluster in update_renewables_by_ids.items():
                # Update the renewable cluster properties.
                old_cluster = old_renewables_by_ids[renewable_id.lower()]
                new_cluster = old_cluster.model_copy(update=update_cluster.model_dump(exclude_none=True))
                new_renewables_by_areas[area_id][renewable_id] = new_cluster

        study.add_commands([command])

        return new_renewables_by_areas

    @staticmethod
    def get_table_schema() -> JSON:
        return RenewableCluster.model_json_schema()
