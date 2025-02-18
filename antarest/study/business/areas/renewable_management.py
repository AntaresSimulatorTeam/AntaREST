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
from typing import Any, Dict, Mapping, MutableMapping, Sequence

from antares.study.version import StudyVersion

from antarest.core.exceptions import DuplicateRenewableCluster, RenewableClusterConfigNotFound, RenewableClusterNotFound
from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfig,
    RenewableProperties,
    RenewablePropertiesType,
    create_renewable_config,
    create_renewable_properties,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/renewables/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/renewables/clusters"


class TimeSeriesInterpretation(EnumIgnoreCase):
    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


@all_optional_model
@camel_case_model
class RenewableClusterInput(RenewableProperties):
    """
    Model representing the data structure required to edit an existing renewable cluster.
    """

    class Config:
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = RenewableClusterInput(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                ts_interpretation="power-generation",
            ).model_dump(mode="json")


class RenewableClusterCreation(RenewableClusterInput):
    """
    Model representing the data structure required to create a new Renewable cluster within a study.
    """

    def to_properties(self, study_version: StudyVersion) -> RenewablePropertiesType:
        values = self.model_dump(by_alias=False, exclude_none=True)
        return create_renewable_properties(study_version=study_version, data=values)


@all_optional_model
@camel_case_model
class RenewableClusterOutput(RenewableConfig):
    """
    Model representing the output data structure to display the details of a renewable cluster.
    """

    class Config:
        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = RenewableClusterOutput(
                id="Gas cluster YZ",
                group="Gas",
                name="Gas Cluster YZ",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                ts_interpretation="power-generation",
            ).model_dump()


def create_renewable_output(
    study_version: StudyVersion,
    cluster_id: str,
    config: Mapping[str, Any],
) -> "RenewableClusterOutput":
    obj = create_renewable_config(study_version=study_version, **config, id=cluster_id)
    kwargs = obj.model_dump(by_alias=False)
    return RenewableClusterOutput(**kwargs)


class RenewableManager:
    """
    A manager class responsible for handling operations related to renewable clusters within a study.
    """

    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_clusters(self, study: StudyInterface, area_id: str) -> Sequence[RenewableClusterOutput]:
        """
        Fetches all clusters related to a specific area in a study.

        Returns:
            List of cluster output for all clusters.

        Raises:
            RenewableClusterConfigNotFound: If the clusters configuration for the specified area is not found.
        """
        file_study = study.get_files()
        path = _CLUSTERS_PATH.format(area_id=area_id)

        try:
            clusters = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise RenewableClusterConfigNotFound(path, area_id)

        return [create_renewable_output(study.version, cluster_id, cluster) for cluster_id, cluster in clusters.items()]

    def get_all_renewables_props(
        self,
        study: StudyInterface,
    ) -> Mapping[str, Mapping[str, RenewableClusterOutput]]:
        """
        Retrieve all renewable clusters from all areas within a study.

        Args:
            study: Study from which to retrieve the clusters.

        Returns:
            A mapping of area IDs to a mapping of cluster IDs to cluster output.

        Raises:
            RenewableClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = study.get_files()
        path = _ALL_CLUSTERS_PATH
        try:
            # may raise KeyError if the path is missing
            clusters = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            clusters = {area_id: cluster_list["list"] for area_id, cluster_list in clusters.items()}
        except KeyError:
            raise RenewableClusterConfigNotFound(path)

        renewables_by_areas: MutableMapping[str, MutableMapping[str, RenewableClusterOutput]]
        renewables_by_areas = collections.defaultdict(dict)
        for area_id, cluster_obj in clusters.items():
            for cluster_id, cluster in cluster_obj.items():
                renewables_by_areas[area_id][cluster_id] = create_renewable_output(study.version, cluster_id, cluster)

        return renewables_by_areas

    def create_cluster(
        self, study: StudyInterface, area_id: str, cluster_data: RenewableClusterCreation
    ) -> RenewableClusterOutput:
        """
        Creates a new cluster within an area in the study.

        Args:
            study: The study to search within.
            area_id: The identifier of the area.
            cluster_data: The data used to create the cluster configuration.

        Returns:
            The newly created cluster.
        """
        cluster = cluster_data.to_properties(study.version)
        command = self._make_create_cluster_cmd(area_id, cluster, study.version)

        study.add_commands([command])
        output = self.get_cluster(study, area_id, cluster.get_id())
        return output

    def _make_create_cluster_cmd(
        self, area_id: str, cluster: RenewablePropertiesType, study_version: StudyVersion
    ) -> CreateRenewablesCluster:
        command = CreateRenewablesCluster(
            area_id=area_id,
            parameters=cluster,
            command_context=self._command_context,
            study_version=study_version,
        )
        return command

    def get_cluster(self, study: StudyInterface, area_id: str, cluster_id: str) -> RenewableClusterOutput:
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
        file_study = study.get_files()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise RenewableClusterNotFound(path, cluster_id)
        return create_renewable_output(study.version, cluster_id, cluster)

    def update_cluster(
        self,
        study: StudyInterface,
        area_id: str,
        cluster_id: str,
        cluster_data: RenewableClusterInput,
    ) -> RenewableClusterOutput:
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

        file_study = study.get_files()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)

        try:
            values = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise RenewableClusterNotFound(path, cluster_id) from None
        else:
            old_config = create_renewable_config(study.version, **values)

        new_values = cluster_data.model_dump(exclude_none=True)
        new_config = old_config.model_copy(update=new_values)
        new_data = new_config.model_dump(mode="json", by_alias=True, exclude={"id"})

        # create the dict containing the new values using aliases
        data: Dict[str, Any] = {}
        for field_name, field in new_config.model_fields.items():
            if field_name in new_values:
                name = field.alias if field.alias else field_name
                data[name] = new_data[name]

        # create the update config commands with the modified data
        commands = [
            UpdateConfig(
                target=f"{path}/{key}", data=value, command_context=self._command_context, study_version=study.version
            )
            for key, value in data.items()
        ]
        study.add_commands(commands)

        values = new_config.model_dump(exclude={"id"})
        return RenewableClusterOutput(**values, id=cluster_id)

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
    ) -> RenewableClusterOutput:
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
        current_cluster = self.get_cluster(study, area_id, source_id)
        current_cluster.name = new_cluster_name
        creation_form = RenewableClusterCreation(**current_cluster.model_dump(by_alias=False, exclude={"id"}))
        new_config = creation_form.to_properties(study.version)
        create_cluster_cmd = self._make_create_cluster_cmd(area_id, new_config, study.version)

        # Matrix edition
        lower_source_id = source_id.lower()
        source_path = f"input/renewables/series/{area_id}/{lower_source_id}/series"
        new_path = f"input/renewables/series/{area_id}/{lower_new_id}/series"

        # Prepare and execute commands
        file_study = study.get_files()
        current_matrix = file_study.tree.get(source_path.split("/"))["data"]
        replace_matrix_cmd = ReplaceMatrix(
            target=new_path, matrix=current_matrix, command_context=self._command_context, study_version=study.version
        )
        commands = [create_cluster_cmd, replace_matrix_cmd]
        study.add_commands(commands)

        return RenewableClusterOutput(**new_config.model_dump(by_alias=False))

    def update_renewables_props(
        self,
        study: StudyInterface,
        update_renewables_by_areas: Mapping[str, Mapping[str, RenewableClusterInput]],
    ) -> Mapping[str, Mapping[str, RenewableClusterOutput]]:
        old_renewables_by_areas = self.get_all_renewables_props(study)
        new_renewables_by_areas = {area_id: dict(clusters) for area_id, clusters in old_renewables_by_areas.items()}

        # Prepare the commands to update the renewable clusters.
        commands = []
        study_version = study.version
        for area_id, update_renewables_by_ids in update_renewables_by_areas.items():
            old_renewables_by_ids = old_renewables_by_areas[area_id]
            for renewable_id, update_cluster in update_renewables_by_ids.items():
                # Update the renewable cluster properties.
                old_cluster = old_renewables_by_ids[renewable_id]
                new_cluster = old_cluster.model_copy(update=update_cluster.model_dump(exclude_none=True))
                new_renewables_by_areas[area_id][renewable_id] = new_cluster

                # Convert the DTO to a configuration object and update the configuration file.
                properties = create_renewable_config(study_version, **new_cluster.model_dump(exclude_none=True))
                path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=renewable_id)
                cmd = UpdateConfig(
                    target=path,
                    data=properties.model_dump(mode="json", by_alias=True, exclude={"id"}),
                    command_context=self._command_context,
                    study_version=study_version,
                )
                commands.append(cmd)

        study.add_commands(commands)

        return new_renewables_by_areas

    @staticmethod
    def get_table_schema() -> JSON:
        return RenewableClusterOutput.model_json_schema()
