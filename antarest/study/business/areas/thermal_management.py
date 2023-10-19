import json
import typing as t

from pydantic import validator

from antarest.core.exceptions import ClusterConfigNotFound, ClusterNotFound
from antarest.study.business.utils import AllOptionalMetaclass, camel_case_model, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    Thermal860Config,
    Thermal860Properties,
    ThermalConfigType,
    create_thermal_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"


@camel_case_model
class ThermalClusterInput(Thermal860Properties, metaclass=AllOptionalMetaclass):
    """
    Model representing the data structure required to edit an existing thermal cluster within a study.
    """


class ThermalClusterCreation(ThermalClusterInput):
    """
    Model representing the data structure required to create a new thermal cluster within a study.
    """

    # noinspection Pydantic
    @validator("name", pre=True)
    def validate_name(cls, name: t.Optional[str]) -> str:
        """
        Validator to check if the name is not empty.
        """
        if not name:
            raise ValueError("name must not be empty")
        return name

    def to_config(self, study_version: t.Union[str, int]) -> ThermalConfigType:
        values = self.dict(by_alias=False, exclude_none=True)
        return create_thermal_config(study_version=study_version, **values)


@camel_case_model
class ThermalClusterOutput(Thermal860Config, metaclass=AllOptionalMetaclass):
    """
    Model representing the output data structure to display the details of a thermal cluster within a study.
    """


def create_thermal_output(
    study_version: t.Union[str, int],
    storage_id: str,
    config: t.Mapping[str, t.Any],
) -> "ThermalClusterOutput":
    obj = create_thermal_config(study_version=study_version, **config, id=storage_id)
    kwargs = obj.dict(by_alias=False)
    return ThermalClusterOutput(**kwargs)


class ThermalManager:
    """
    Manager class implementing endpoints related to Thermal Clusters within a study.
    Provides methods for creating, retrieving, updating, and deleting thermal clusters.

    Attributes:
        storage_service: The service for accessing study storage.
    """

    def __init__(self, storage_service: StudyStorageService):
        """
        Initializes an instance with the service for accessing study storage.
        """

        self.storage_service = storage_service

    def _get_file_study(self, study: Study) -> FileStudy:
        """
        Helper function to get raw study data.
        """

        return self.storage_service.get_storage(study).get_raw(study)

    def get_cluster(self, study: Study, area_id: str, cluster_id: str) -> ThermalClusterOutput:
        """
        Get a cluster by ID.

        Args:
            study: The study to get the cluster from.
            area_id: The ID of the area where the cluster is located.
            cluster_id: The ID of the cluster to retrieve.

        Returns:
            The cluster with the specified ID.

        Raises:
            ClusterNotFound: If the specified cluster does not exist.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ClusterNotFound(cluster_id)
        study_version = study.version
        return create_thermal_output(study_version, cluster_id, cluster)

    def get_clusters(
        self,
        study: Study,
        area_id: str,
    ) -> t.Sequence[ThermalClusterOutput]:
        """
        Retrieve all thermal clusters from a specified area within a study.

        Args:
            study: Study from which to retrieve the clusters.
            area_id: ID of the area containing the clusters.

        Returns:
            A list of thermal clusters within the specified area.

        Raises:
            ClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ClusterConfigNotFound(area_id)
        study_version = study.version
        return [create_thermal_output(study_version, cluster_id, cluster) for cluster_id, cluster in clusters.items()]

    def create_cluster(self, study: Study, area_id: str, cluster_data: ThermalClusterCreation) -> ThermalClusterOutput:
        """
        Create a new cluster.

        Args:
            study: The study where the cluster will be created.
            area_id: The ID of the area where the cluster will be created.
            cluster_data: The data for the new cluster.

        Returns:
            The created cluster.
        """

        file_study = self._get_file_study(study)
        study_version = study.version
        cluster = cluster_data.to_config(study_version)
        # NOTE: currently, in the `CreateCluster` class, there is a confusion
        # between the cluster name and the cluster ID (which is a section name).
        command = CreateCluster(
            area_id=area_id,
            cluster_name=cluster.id,
            parameters=cluster.dict(by_alias=True, exclude={"id"}),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study,
            file_study,
            [command],
            self.storage_service,
        )
        output = self.get_cluster(study, area_id, cluster.id)
        return output

    def update_cluster(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        cluster_data: ThermalClusterInput,
    ) -> ThermalClusterOutput:
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
            ClusterNotFound: If the provided `cluster_id` does not match the ID of the cluster
            in the provided cluster_data.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ClusterNotFound(cluster_id) from None

        study_version = study.version
        config = create_thermal_config(study_version, **cluster)
        updated_cluster = {**config.dict(exclude={"id"}), **cluster_data.dict(by_alias=False, exclude_none=True)}
        new_config = create_thermal_config(study_version, **updated_cluster)
        new_data = json.loads(new_config.json(by_alias=True, exclude={"id"}))

        data = {
            field.alias: new_data[field.alias]
            for field_name, field in new_config.__fields__.items()
            if field_name != "id"
            and (field_name in updated_cluster or getattr(new_config, field_name) != field.get_default())
        }

        command_context = self.storage_service.variant_study_service.command_factory.command_context
        command = UpdateConfig(target=path, data=data, command_context=command_context)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return self.get_cluster(study, area_id, cluster_id)

    def delete_clusters(self, study: Study, area_id: str, cluster_ids: t.Sequence[str]) -> None:
        """
        Delete the clusters with the given IDs in the given area of the given study.

        Args:
            study: The study containing the area and clusters to delete.
            area_id: The ID of the area containing the clusters to delete.
            cluster_ids: The IDs of the clusters to delete.
        """

        file_study = self._get_file_study(study)
        command_context = self.storage_service.variant_study_service.command_factory.command_context

        commands = [
            RemoveCluster(area_id=area_id, cluster_id=cluster_id, command_context=command_context)
            for cluster_id in cluster_ids
        ]

        execute_or_add_commands(study, file_study, commands, self.storage_service)
