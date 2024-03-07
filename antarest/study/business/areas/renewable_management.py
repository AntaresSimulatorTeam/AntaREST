import json
import typing as t

from pydantic import validator

from antarest.core.exceptions import ClusterAlreadyExists, ClusterConfigNotFound, ClusterNotFound
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import AllOptionalMetaclass, camel_case_model, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfig,
    RenewableConfigType,
    RenewableProperties,
    create_renewable_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

__all__ = (
    "RenewableClusterInput",
    "RenewableClusterCreation",
    "RenewableClusterOutput",
    "RenewableManager",
    "TimeSeriesInterpretation",
)

_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/renewables/clusters/{area_id}/list"


class TimeSeriesInterpretation(EnumIgnoreCase):
    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


@camel_case_model
class RenewableClusterInput(RenewableProperties, metaclass=AllOptionalMetaclass, use_none=True):
    """
    Model representing the data structure required to edit an existing renewable cluster.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = RenewableClusterInput(
                group="Gas",
                name="2 avail and must 1",
                enabled=False,
                unitCount=100,
                nominalCapacity=1000.0,
                tsInterpretation="power-generation",
            )


class RenewableClusterCreation(RenewableClusterInput):
    """
    Model representing the data structure required to create a new Renewable cluster within a study.
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

    def to_config(self, study_version: t.Union[str, int]) -> RenewableConfigType:
        values = self.dict(by_alias=False, exclude_none=True)
        return create_renewable_config(study_version=study_version, **values)


@camel_case_model
class RenewableClusterOutput(RenewableConfig, metaclass=AllOptionalMetaclass, use_none=True):
    """
    Model representing the output data structure to display the details of a renewable cluster.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = RenewableClusterOutput(
                id="2 avail and must 1",
                group="Gas",
                name="2 avail and must 1",
                enabled=False,
                unitCount=100,
                nominalCapacity=1000.0,
                tsInterpretation="power-generation",
            )


def create_renewable_output(
    study_version: t.Union[str, int],
    cluster_id: str,
    config: t.Mapping[str, t.Any],
) -> "RenewableClusterOutput":
    obj = create_renewable_config(study_version=study_version, **config, id=cluster_id)
    kwargs = obj.dict(by_alias=False)
    return RenewableClusterOutput(**kwargs)


class RenewableManager:
    """
    A manager class responsible for handling operations related to renewable clusters within a study.

    Attributes:
        storage_service (StudyStorageService): A service responsible for study data storage and retrieval.
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def _get_file_study(self, study: Study) -> FileStudy:
        """
        Helper function to get raw study data.
        """
        return self.storage_service.get_storage(study).get_raw(study)

    def get_clusters(self, study: Study, area_id: str) -> t.Sequence[RenewableClusterOutput]:
        """
        Fetches all clusters related to a specific area in a study.

        Returns:
            List of cluster output for all clusters.

        Raises:
            ClusterConfigNotFound: If the clusters configuration for the specified area is not found.
        """
        file_study = self._get_file_study(study)
        path = _CLUSTERS_PATH.format(area_id=area_id)

        try:
            clusters = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ClusterConfigNotFound(area_id)

        return [create_renewable_output(study.version, cluster_id, cluster) for cluster_id, cluster in clusters.items()]

    def create_cluster(
        self, study: Study, area_id: str, cluster_data: RenewableClusterCreation
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
        file_study = self._get_file_study(study)
        study_version = study.version
        cluster = cluster_data.to_config(study_version)

        command = CreateRenewablesCluster(
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

        return self.get_cluster(study, area_id, cluster.id)

    def get_cluster(self, study: Study, area_id: str, cluster_id: str) -> RenewableClusterOutput:
        """
        Retrieves a single cluster's data for a specific area in a study.

        Args:
            study: The study to search within.
            area_id: The identifier of the area.
            cluster_id: The identifier of the cluster to retrieve.

        Returns:
            The cluster output representation.

        Raises:
            ClusterNotFound: If the specified cluster is not found within the area.
        """
        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ClusterNotFound(cluster_id)
        return create_renewable_output(study.version, cluster_id, cluster)

    def update_cluster(
        self,
        study: Study,
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
            ClusterNotFound: If the cluster to update is not found.
        """

        study_version = study.version
        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)

        try:
            values = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ClusterNotFound(cluster_id) from None
        else:
            old_config = create_renewable_config(study_version, **values)

        # use Python values to synchronize Config and Form values
        new_values = cluster_data.dict(by_alias=False, exclude_none=True)
        new_config = old_config.copy(exclude={"id"}, update=new_values)
        new_data = json.loads(new_config.json(by_alias=True, exclude={"id"}))

        # create the dict containing the new values using aliases
        data: t.Dict[str, t.Any] = {
            field.alias: new_data[field.alias]
            for field_name, field in new_config.__fields__.items()
            if field_name in new_values
        }

        # create the update config commands with the modified data
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        commands = [
            UpdateConfig(target=f"{path}/{key}", data=value, command_context=command_context)
            for key, value in data.items()
        ]
        execute_or_add_commands(study, file_study, commands, self.storage_service)

        values = new_config.dict(by_alias=False)
        return RenewableClusterOutput(**values, id=cluster_id)

    def delete_clusters(self, study: Study, area_id: str, cluster_ids: t.Sequence[str]) -> None:
        """
        Deletes multiple clusters from an area in the study.

        Args:
            study: The study from which clusters will be deleted.
            area_id: The identifier of the area where clusters will be deleted.
            cluster_ids: A sequence of cluster identifiers to be deleted.
        """
        file_study = self._get_file_study(study)
        command_context = self.storage_service.variant_study_service.command_factory.command_context

        commands = [
            RemoveRenewablesCluster(area_id=area_id, cluster_id=cluster_id, command_context=command_context)
            for cluster_id in cluster_ids
        ]

        execute_or_add_commands(study, file_study, commands, self.storage_service)

    def duplicate_cluster(self, study: Study, area_id: str, source_id: str, new_name: str) -> RenewableClusterOutput:
        """
        Creates a duplicate cluster within the study area with a new name.

        Args:
            study: The study in which the cluster will be duplicated.
            area_id: The identifier of the area where the cluster will be duplicated.
            source_id: The identifier of the cluster to be duplicated.
            new_name: The new name for the duplicated cluster.

        Returns:
            The duplicated cluster configuration.

        Raises:
            ClusterAlreadyExists: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_name, lower=False)
        if any(new_id.lower() == cluster.id.lower() for cluster in self.get_clusters(study, area_id)):
            raise ClusterAlreadyExists("Renewable", new_id)

        # Cluster duplication
        current_cluster = self.get_cluster(study, area_id, source_id)
        current_cluster.name = new_name
        creation_form = RenewableClusterCreation(**current_cluster.dict(by_alias=False, exclude={"id"}))
        new_cluster = self.create_cluster(study, area_id, creation_form)

        # Matrix edition
        current_path = f"input/renewables/series/{area_id}/{source_id.lower()}/series"
        new_path = f"input/renewables/series/{area_id}/{new_id.lower()}/series"
        current_matrix = self.storage_service.raw_study_service.get(study, current_path)
        command = [
            ReplaceMatrix(
                target=new_path,
                matrix=current_matrix["data"],
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        ]
        execute_or_add_commands(study, self._get_file_study(study), command, self.storage_service)

        return new_cluster
