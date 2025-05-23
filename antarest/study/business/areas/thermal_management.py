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
from pathlib import Path
from typing import List, Mapping, MutableMapping, MutableSequence, Sequence

from antares.study.version import StudyVersion

from antarest.core.exceptions import (
    AreaNotFound,
    DuplicateThermalCluster,
    MatrixWidthMismatchError,
    ThermalClusterConfigNotFound,
    ThermalClusterNotFound,
    WrongMatrixHeightError,
)
from antarest.core.model import JSON
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
    ThermalClusterCreation,
    ThermalClusterUpdate,
    ThermalClusterUpdates,
    create_thermal_cluster,
    update_thermal_cluster,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_thermal_clusters import UpdateThermalClusters
from antarest.study.storage.variantstudy.model.command_context import CommandContext

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/thermal/clusters"


class ThermalManager:
    """
    Manager class implementing endpoints related to Thermal Clusters within a study.
    Provides methods for creating, retrieving, updating, and deleting thermal clusters.

    Attributes:
    """

    def __init__(self, command_context: CommandContext):
        """
        Initializes an instance with the service for accessing study storage.
        """
        self._command_context = command_context

    def get_cluster(self, study: StudyInterface, area_id: str, cluster_id: str) -> ThermalCluster:
        """
        Get a cluster by ID.

        Args:
            study: The study to get the cluster from.
            area_id: The ID of the area where the cluster is located.
            cluster_id: The ID of the cluster to retrieve.

        Returns:
            The cluster with the specified ID.

        Raises:
            ThermalClusterNotFound: If the specified cluster does not exist.
        """

        file_study = study.get_files()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster_data = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ThermalClusterNotFound(path, cluster_id) from None
        return parse_thermal_cluster(study.version, cluster_data)

    def get_clusters(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> Sequence[ThermalCluster]:
        """
        Retrieve all thermal clusters from a specified area within a study.

        Args:
            study: Study from which to retrieve the clusters.
            area_id: ID of the area containing the clusters.

        Returns:
            A list of thermal clusters within the specified area.

        Raises:
            ThermalClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = study.get_files()
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters_data = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ThermalClusterConfigNotFound(path, area_id) from None
        return [parse_thermal_cluster(study.version, c) for c in clusters_data.values()]

    def get_all_thermals_props(
        self,
        study: StudyInterface,
    ) -> Mapping[str, Mapping[str, ThermalCluster]]:
        """
        Retrieve all thermal clusters from all areas within a study.

        Args:
            study: Study from which to retrieve the clusters.

        Returns:
            A mapping of area IDs to a mapping of cluster IDs to thermal cluster configurations.

        Raises:
            ThermalClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = study.get_files()
        path = _ALL_CLUSTERS_PATH
        try:
            # may raise KeyError if the path is missing
            clusters = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            clusters = {area_id: cluster_list["list"] for area_id, cluster_list in clusters.items()}
        except KeyError:
            raise ThermalClusterConfigNotFound(path) from None

        thermals_by_areas: MutableMapping[str, MutableMapping[str, ThermalCluster]]
        thermals_by_areas = collections.defaultdict(dict)
        for area_id, cluster_obj in clusters.items():
            for cluster_id, cluster in cluster_obj.items():
                thermals_by_areas[area_id][cluster_id] = parse_thermal_cluster(study.version, cluster)
        return thermals_by_areas

    def update_thermals_props(
        self,
        study: StudyInterface,
        update_thermals_by_areas: ThermalClusterUpdates,
    ) -> Mapping[str, Mapping[str, ThermalCluster]]:
        old_thermals_by_areas = self.get_all_thermals_props(study)
        new_thermals_by_areas = {area_id: dict(clusters) for area_id, clusters in old_thermals_by_areas.items()}

        # Create the command to update the thermal clusters.
        command = UpdateThermalClusters(
            cluster_properties=update_thermals_by_areas,
            command_context=self._command_context,
            study_version=study.version,
        )

        # Prepare the return of the method
        for area_id, update_thermals_by_ids in update_thermals_by_areas.items():
            old_thermals_by_ids = old_thermals_by_areas[area_id]
            for thermal_id, update_cluster in update_thermals_by_ids.items():
                # Update the thermal cluster properties.
                old_cluster = old_thermals_by_ids[thermal_id]
                new_cluster = old_cluster.model_copy(update=update_cluster.model_dump(mode="json", exclude_none=True))
                new_thermals_by_areas[area_id][thermal_id] = new_cluster

        study.add_commands([command])
        return new_thermals_by_areas

    @staticmethod
    def get_table_schema() -> JSON:
        return ThermalCluster.model_json_schema()

    def create_cluster(
        self, study: StudyInterface, area_id: str, cluster_data: ThermalClusterCreation
    ) -> ThermalCluster:
        """
        Create a new cluster.

        Args:
            study: The study where the cluster will be created.
            area_id: The ID of the area where the cluster will be created.
            cluster_data: The data for the new cluster.

        Returns:
            The created cluster.
        """

        command = self._make_create_cluster_cmd(area_id, cluster_data, study.version)
        study.add_commands([command])
        return create_thermal_cluster(cluster_data, study.version)

    def _make_create_cluster_cmd(
        self, area_id: str, cluster: ThermalClusterCreation, study_version: StudyVersion
    ) -> CreateCluster:
        # NOTE: currently, in the `CreateCluster` class, there is a confusion
        # between the cluster name and the cluster ID (which is a section name).
        return CreateCluster(
            area_id=area_id,
            parameters=cluster,
            study_version=study_version,
            command_context=self._command_context,
        )

    def update_cluster(
        self,
        study: StudyInterface,
        area_id: str,
        cluster_id: str,
        cluster_data: ThermalClusterUpdate,
    ) -> ThermalCluster:
        """
        Update a cluster with the given `cluster_id` in the given area of the given study
        with the provided cluster data (form fields).

        Args:
            study: The study containing the area and cluster to update.
            area_id: The ID of the area containing the cluster to update.
            cluster_id: The ID of the cluster to update.
            cluster_data: The new data to update the cluster with.

        Returns:
            The updated cluster.

        Raises:
            ThermalClusterNotFound: If the provided `cluster_id` does not match the ID of the cluster
            in the provided cluster_data.
        """
        file_study = study.get_files()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)

        try:
            area = file_study.config.areas[area_id]
        except KeyError:
            raise AreaNotFound(area_id)

        thermal_cluster = next((thermal for thermal in area.thermals if thermal.id == cluster_id), None)
        if thermal_cluster is None:
            raise ThermalClusterNotFound(path, cluster_id)

        updated_thermal_cluster = update_thermal_cluster(thermal_cluster, cluster_data)

        command = UpdateThermalClusters(
            cluster_properties={area_id: {cluster_id: cluster_data}},
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return updated_thermal_cluster

    def delete_clusters(self, study: StudyInterface, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Delete the clusters with the given IDs in the given area of the given study.

        Args:
            study: The study containing the area and clusters to delete.
            area_id: The ID of the area containing the clusters to delete.
            cluster_ids: The IDs of the clusters to delete.
        """

        commands = [
            RemoveCluster(
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
    ) -> ThermalCluster:
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
            DuplicateThermalCluster: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_cluster_name, lower=False)
        lower_new_id = new_id.lower()
        if any(lower_new_id == cluster.id.lower() for cluster in self.get_clusters(study, area_id)):
            raise DuplicateThermalCluster(area_id, new_id)

        file_study = study.get_files()
        study_version = study.version

        # Cluster duplication
        source_cluster = self.get_cluster(study, area_id, source_id)
        source_cluster.name = new_cluster_name
        cluster_creation = ThermalClusterCreation(
            **source_cluster.model_dump(mode="json", by_alias=False, exclude={"id"})
        )
        create_cluster_cmd = CreateCluster(
            area_id=area_id,
            parameters=cluster_creation,
            study_version=study_version,
            command_context=self._command_context,
        )

        # Matrix edition
        lower_source_id = source_id.lower()
        source_paths = [
            f"input/thermal/series/{area_id}/{lower_source_id}/series",
            f"input/thermal/prepro/{area_id}/{lower_source_id}/modulation",
            f"input/thermal/prepro/{area_id}/{lower_source_id}/data",
        ]
        new_paths = [
            f"input/thermal/series/{area_id}/{lower_new_id}/series",
            f"input/thermal/prepro/{area_id}/{lower_new_id}/modulation",
            f"input/thermal/prepro/{area_id}/{lower_new_id}/data",
        ]
        if study_version >= STUDY_VERSION_8_7:
            source_paths.append(f"input/thermal/series/{area_id}/{lower_source_id}/CO2Cost")
            source_paths.append(f"input/thermal/series/{area_id}/{lower_source_id}/fuelCost")
            new_paths.append(f"input/thermal/series/{area_id}/{lower_new_id}/CO2Cost")
            new_paths.append(f"input/thermal/series/{area_id}/{lower_new_id}/fuelCost")

        # Prepare and execute commands
        commands: List[CreateCluster | ReplaceMatrix] = [create_cluster_cmd]
        command_context = self._command_context
        for source_path, new_path in zip(source_paths, new_paths):
            current_matrix = file_study.tree.get(source_path.split("/"))["data"]
            command = ReplaceMatrix(
                target=new_path, matrix=current_matrix, command_context=command_context, study_version=study_version
            )
            commands.append(command)

        study.add_commands(commands)

        return create_thermal_cluster(cluster_creation, study_version)

    def validate_series(self, study: StudyInterface, area_id: str, cluster_id: str) -> bool:
        lower_cluster_id = cluster_id.lower()
        thermal_cluster_path = Path(f"input/thermal/series/{area_id}/{lower_cluster_id}")
        series_path = [thermal_cluster_path / "series"]

        file_study = study.get_files()
        if study.version >= STUDY_VERSION_8_7:
            series_path.append(thermal_cluster_path / "CO2Cost")
            series_path.append(thermal_cluster_path / "fuelCost")

        ts_widths: MutableMapping[int, MutableSequence[str]] = {}
        for ts_path in series_path:
            matrix = file_study.tree.get(ts_path.as_posix().split("/"))
            matrix_data = matrix["data"]
            matrix_height = len(matrix_data)
            # We ignore empty matrices as there are default matrices for the simulator.
            if matrix_data != [[]] and matrix_height != 8760:
                raise WrongMatrixHeightError(
                    f"The matrix {ts_path.name} should have 8760 rows, currently: {matrix_height}"
                )
            matrix_width = len(matrix_data[0])
            if matrix_width > 1:
                ts_widths.setdefault(matrix_width, []).append(ts_path.name)

        if len(ts_widths) > 1:
            messages = []
            for width, name_list in ts_widths.items():
                names = ", ".join([f"'{name}'" for name in name_list])
                message = {
                    1: f"matrix {names} has {width} columns",
                    2: f"matrices {names} have {width} columns",
                }[min(2, len(name_list))]
                messages.append(message)
            raise MatrixWidthMismatchError("Mismatch widths: " + "; ".join(messages))

        return True
