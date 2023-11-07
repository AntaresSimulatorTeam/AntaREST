import json
import typing as t
from pydantic import validator

from antarest.core.exceptions import ClusterConfigNotFound, ClusterNotFound
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import execute_or_add_commands, camel_case_model, AllOptionalMetaclass
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableProperties,
    RenewableConfigType,
    create_renewable_config,
    RenewableConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

__all__ = (
    "RenewableClusterInput",
    "RenewableClusterCreation",
    "RenewableClusterOutput",
    "RenewableManager",
)

_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/renewables/clusters/{area_id}/list"


class TimeSeriesInterpretation(EnumIgnoreCase):
    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


@camel_case_model
class RenewableClusterInput(RenewableProperties, metaclass=AllOptionalMetaclass):
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
                tsIntrepretation="power-generation",
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
class RenewableClusterOutput(RenewableConfig, metaclass=AllOptionalMetaclass):
    """
    Model representing the output data structure to display the details of a renewable cluster.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = RenewableClusterInput(
                id="2 avail and must 1",
                group="Gas",
                name="2 avail and must 1",
                enabled=False,
                unitCount=100,
                nominalCapacity=1000.0,
                tsIntrepretation="power-generation",
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
        self, study: Study, area_id: str, cluster_id: str, cluster_data: RenewableClusterInput
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

        # merge old and new values
        updated_values = {
            **create_renewable_config(study_version, **values).dict(exclude={"id"}),
            **cluster_data.dict(by_alias=False, exclude_none=True),
            "id": cluster_id,
        }
        new_config = create_renewable_config(study_version, **updated_values)
        new_data = json.loads(new_config.json(by_alias=True, exclude={"id"}))

        data = {
            field.alias: new_data[field.alias]
            for field_name, field in new_config.__fields__.items()
            if field_name not in {"id"}
            and (field_name in updated_values or getattr(new_config, field_name) != field.get_default())
        }

        command = UpdateConfig(
            target=path,
            data=data,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(study, file_study, [command], self.storage_service)
        return RenewableClusterOutput(**new_config.dict(by_alias=False))

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
