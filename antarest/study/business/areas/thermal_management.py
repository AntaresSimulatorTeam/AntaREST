import json
import typing as t
from pathlib import Path

from pydantic import validator

from antarest.core.exceptions import (
    DuplicateThermalCluster,
    MatrixWidthMismatchError,
    ThermalClusterConfigNotFound,
    ThermalClusterNotFound,
    WrongMatrixHeightError,
)
from antarest.study.business.all_optional_meta import AllOptionalMetaclass, camel_case_model
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    Thermal870Config,
    Thermal870Properties,
    ThermalConfigType,
    create_thermal_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

__all__ = (
    "ThermalClusterInput",
    "ThermalClusterCreation",
    "ThermalClusterOutput",
    "ThermalManager",
)

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/thermal/clusters"


@camel_case_model
class ThermalClusterInput(Thermal870Properties, metaclass=AllOptionalMetaclass, use_none=True):
    """
    Model representing the data structure required to edit an existing thermal cluster within a study.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = ThermalClusterInput(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unitCount=100,
                nominalCapacity=1000.0,
                genTs="use global",
                co2=7.0,
            )


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
class ThermalClusterOutput(Thermal870Config, metaclass=AllOptionalMetaclass, use_none=True):
    """
    Model representing the output data structure to display the details of a thermal cluster within a study.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = ThermalClusterOutput(
                id="Gas cluster YZ",
                group="Gas",
                name="Gas Cluster YZ",
                enabled=False,
                unitCount=100,
                nominalCapacity=1000.0,
                genTs="use global",
                co2=7.0,
            )


def create_thermal_output(
    study_version: t.Union[str, int],
    cluster_id: str,
    config: t.Mapping[str, t.Any],
) -> "ThermalClusterOutput":
    obj = create_thermal_config(study_version=study_version, **config, id=cluster_id)
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
            ThermalClusterNotFound: If the specified cluster does not exist.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ThermalClusterNotFound(path, cluster_id) from None
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
            ThermalClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ThermalClusterConfigNotFound(path, area_id) from None
        study_version = study.version
        return [create_thermal_output(study_version, cluster_id, cluster) for cluster_id, cluster in clusters.items()]

    def get_all_thermals_props(
        self,
        study: Study,
    ) -> t.Mapping[str, t.Sequence[ThermalClusterOutput]]:
        """
        Retrieve all thermal clusters from all areas within a study.

        Args:
            study: Study from which to retrieve the clusters.

        Returns:
            A mapping of area IDs to lists of thermal clusters within the specified area.

        Raises:
            ThermalClusterConfigNotFound: If no clusters are found in the specified area.
        """

        file_study = self._get_file_study(study)
        path = _ALL_CLUSTERS_PATH
        try:
            # may raise KeyError if the path is missing
            clusters = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            clusters = {area_id: cluster_list["list"] for area_id, cluster_list in clusters.items()}
        except KeyError:
            raise ThermalClusterConfigNotFound(path) from None

        study_version = study.version
        all_clusters = {
            area_id: [
                create_thermal_output(study_version, cluster_id, cluster) for cluster_id, cluster in cluster_obj.items()
            ]
            for area_id, cluster_obj in clusters.items()
        }
        return all_clusters

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
        cluster = cluster_data.to_config(study.version)
        command = self._make_create_cluster_cmd(area_id, cluster)
        execute_or_add_commands(
            study,
            file_study,
            [command],
            self.storage_service,
        )
        output = self.get_cluster(study, area_id, cluster.id)
        return output

    def _make_create_cluster_cmd(self, area_id: str, cluster: ThermalConfigType) -> CreateCluster:
        # NOTE: currently, in the `CreateCluster` class, there is a confusion
        # between the cluster name and the cluster ID (which is a section name).
        command = CreateCluster(
            area_id=area_id,
            cluster_name=cluster.id,
            parameters=cluster.dict(by_alias=True, exclude={"id"}),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        return command

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
            ThermalClusterNotFound: If the provided `cluster_id` does not match the ID of the cluster
            in the provided cluster_data.
        """

        study_version = study.version
        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            values = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ThermalClusterNotFound(path, cluster_id) from None
        else:
            old_config = create_thermal_config(study_version, **values)

        # Use Python values to synchronize Config and Form values
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
        return ThermalClusterOutput(**values, id=cluster_id)

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

    def duplicate_cluster(
        self,
        study: Study,
        area_id: str,
        source_id: str,
        new_cluster_name: str,
    ) -> ThermalClusterOutput:
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
            ClusterAlreadyExists: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_cluster_name, lower=False)
        lower_new_id = new_id.lower()
        if any(lower_new_id == cluster.id.lower() for cluster in self.get_clusters(study, area_id)):
            raise DuplicateThermalCluster(area_id, new_id)

        # Cluster duplication
        source_cluster = self.get_cluster(study, area_id, source_id)
        source_cluster.name = new_cluster_name
        creation_form = ThermalClusterCreation(**source_cluster.dict(by_alias=False, exclude={"id"}))
        new_config = creation_form.to_config(study.version)
        create_cluster_cmd = self._make_create_cluster_cmd(area_id, new_config)

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
        if int(study.version) >= 870:
            source_paths.append(f"input/thermal/series/{area_id}/{lower_source_id}/CO2Cost")
            source_paths.append(f"input/thermal/series/{area_id}/{lower_source_id}/fuelCost")
            new_paths.append(f"input/thermal/series/{area_id}/{lower_new_id}/CO2Cost")
            new_paths.append(f"input/thermal/series/{area_id}/{lower_new_id}/fuelCost")

        # Prepare and execute commands
        commands: t.List[t.Union[CreateCluster, ReplaceMatrix]] = [create_cluster_cmd]
        storage_service = self.storage_service.get_storage(study)
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        for source_path, new_path in zip(source_paths, new_paths):
            current_matrix = storage_service.get(study, source_path)["data"]
            command = ReplaceMatrix(target=new_path, matrix=current_matrix, command_context=command_context)
            commands.append(command)

        execute_or_add_commands(study, self._get_file_study(study), commands, self.storage_service)

        return ThermalClusterOutput(**new_config.dict(by_alias=False))

    def validate_series(self, study: Study, area_id: str, cluster_id: str) -> bool:
        lower_cluster_id = cluster_id.lower()
        thermal_cluster_path = Path(f"input/thermal/series/{area_id}/{lower_cluster_id}")
        series_path = [thermal_cluster_path / "series"]
        if int(study.version) >= 870:
            series_path.append(thermal_cluster_path / "CO2Cost")
            series_path.append(thermal_cluster_path / "fuelCost")

        ts_widths: t.MutableMapping[int, t.MutableSequence[str]] = {}
        for ts_path in series_path:
            matrix = self.storage_service.get_storage(study).get(study, ts_path.as_posix())
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
