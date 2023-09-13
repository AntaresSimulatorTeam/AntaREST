import json
from typing import Any, Dict, Mapping, Sequence

from pydantic import BaseModel, Extra, Field, root_validator

from antarest.core.exceptions import ClusterConfigNotFound, ClusterNotFound
from antarest.core.utils.string import to_camel_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import AllOptionalMetaclass, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class TimeSeriesGenerationOption(EnumIgnoreCase):
    USE_GLOBAL_PARAMETER = "use global parameter"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(EnumIgnoreCase):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class ThermalClusterGroup(EnumIgnoreCase):
    NUCLEAR = "Nuclear"
    LIGNITE = "Lignite"
    HARD_COAL = "Hard Coal"
    GAS = "Gas"
    OIL = "Oil"
    MIXED_FUEL = "Mixed Fuel"
    OTHER1 = "Other" or "Other 1"
    OTHER2 = "Other 2"
    OTHER3 = "Other 3"
    OTHER4 = "Other 4"


_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"


class ThermalClusterConfig(BaseModel):
    """
    Thermal cluster configuration model.
    This model describes the configuration parameters for a thermal cluster.
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    id: str = Field(..., regex=r"[a-zA-Z0-9_(),& -]+")
    name: str = Field(..., regex=r"[a-zA-Z0-9_(),& -]+")
    group: ThermalClusterGroup = Field(ThermalClusterGroup.OTHER1)
    unit_count: int = Field(1, ge=1, alias="unitcount")
    enabled: bool = Field(True)
    nominal_capacity: float = Field(0, ge=0, alias="nominalcapacity")
    gen_ts: TimeSeriesGenerationOption = Field(TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER, alias="gen-ts")
    min_stable_power: float = Field(0, ge=0, alias="min-stable-power")
    min_up_time: int = Field(1, ge=1, le=168, alias="min-up-time")
    min_down_time: int = Field(1, ge=1, le=168, alias="min-down-time")
    must_run: bool = Field(False, alias="must-run")
    spinning: float = Field(0, ge=0, le=100)
    volatility_forced: float = Field(0, ge=0, le=1, alias="volatility.forced")
    volatility_planned: float = Field(0, ge=0, le=1, alias="volatility.planned")
    law_forced: LawOption = Field(LawOption.UNIFORM, alias="law.forced")
    law_planned: LawOption = Field(LawOption.UNIFORM, alias="law.planned")
    marginal_cost: float = Field(0, ge=0, alias="marginal-cost")
    spread_cost: float = Field(0, ge=0, alias="spread-cost")
    fixed_cost: float = Field(0, ge=0, alias="fixed-cost")
    startup_cost: float = Field(0, ge=0, alias="startup-cost")
    market_bid_cost: float = Field(0, ge=0, alias="market-bid-cost")
    co2: float = Field(0, ge=0)
    so2: float = Field(0, ge=0)
    nh3: float = Field(0, ge=0)
    nox: float = Field(0, ge=0)
    nmvoc: float = Field(0, ge=0)
    pm25: float = Field(0, ge=0, alias="pm2_5")
    pm10: float = Field(0, ge=0)
    pm5: float = Field(0, ge=0)
    op1: float = Field(0, ge=0)
    op2: float = Field(0, ge=0)
    op3: float = Field(0, ge=0)
    op4: float = Field(0, ge=0)
    op5: float = Field(0, ge=0)

    @root_validator(pre=True)
    def check_id(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check and set the ID for a thermal cluster.
        The ID is automatically set based on the 'name' field if not provided.
        """
        if values.get("id") or not values.get("name"):
            return values
        cluster_name = values["name"]
        if cluster_id := transform_name_to_id(cluster_name):
            values["id"] = cluster_id
        else:
            raise ValueError(f"Invalid short term storage name '{cluster_name}'.")
        return values


class ThermalClusterConfigV860(ThermalClusterConfig):
    """
    Thermal cluster configuration model for version >= 8.6, including pollutants.
    This model describes the configuration parameters for a thermal cluster.
    """

    so2: float = Field(0, ge=0)
    nh3: float = Field(0, ge=0)
    nox: float = Field(0, ge=0)
    nmvoc: float = Field(0, ge=0)
    pm25: float = Field(0, ge=0, alias="pm2_5")
    pm10: float = Field(0, ge=0)
    pm5: float = Field(0, ge=0)
    op1: float = Field(0, ge=0)
    op2: float = Field(0, ge=0)
    op3: float = Field(0, ge=0)
    op4: float = Field(0, ge=0)
    op5: float = Field(0, ge=0)


class ThermalClusterCreation(BaseModel):
    """
    Model for creating a thermal cluster.
    This model describes the parameters needed to create a thermal cluster.
    """

    class Config:
        extra = Extra.forbid
        alias_generator = to_camel_case
        validate_assignment = True
        allow_population_by_field_name = True

    name: str = Field(regex=r"[a-zA-Z0-9_(),& -]+")
    group: ThermalClusterGroup = Field()


class ThermalClusterInput(ThermalClusterCreation, metaclass=AllOptionalMetaclass):
    """
    Input model for thermal cluster.
    This model describes the input parameters for a thermal cluster.
    """

    unit_count: int = Field(ge=1)
    enabled: bool = Field()
    nominal_capacity: float = Field(ge=0)
    gen_ts: TimeSeriesGenerationOption = Field(TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER)
    min_stable_power: float = Field(ge=0)
    min_up_time: int = Field(ge=1, le=168)
    min_down_time: int = Field(ge=1, le=168)
    must_run: bool = Field()
    spinning: float = Field(ge=0, le=100)
    volatility_forced: float = Field(ge=0, le=1)
    volatility_planned: float = Field(ge=0, le=1)
    law_forced: LawOption = Field()
    law_planned: LawOption = Field()
    marginal_cost: float = Field(ge=0)
    spread_cost: float = Field(ge=0)
    fixed_cost: float = Field(ge=0)
    startup_cost: float = Field(ge=0)
    market_bid_cost: float = Field(ge=0)
    co2: float = Field(0, ge=0)
    so2: float = Field(0, ge=0)
    nh3: float = Field(0, ge=0)
    nox: float = Field(0, ge=0)
    nmvoc: float = Field(0, ge=0)
    pm25: float = Field(0, ge=0)
    pm10: float = Field(0, ge=0)
    pm5: float = Field(0, ge=0)
    op1: float = Field(0, ge=0)
    op2: float = Field(0, ge=0)
    op3: float = Field(0, ge=0)
    op4: float = Field(0, ge=0)
    op5: float = Field(0, ge=0)


class ThermalClusterOutput(ThermalClusterInput):
    """
    Output model for thermal cluster
    """

    id: str = Field(regex=r"[a-zA-Z0-9_(),& -]+")

    @classmethod
    def from_config(cls, cluster_id: str, config: Mapping[str, Any]) -> "ThermalClusterOutput":
        """
        Create a ThermalClusterOutput instance from a cluster ID and a configuration.

        Args:
            cls (Type[ThermalClusterOutput]): The class to instantiate.
            cluster_id (str): The ID of the cluster.
            config (Mapping[str, Any]): The configuration of the cluster.
            study_version (str): The version of the study.

        Returns:
            ThermalClusterOutput: The created instance.
        """

        cluster = ThermalClusterConfig(id=cluster_id, **config)
        values = cluster.dict(by_alias=False)
        return cls(**values)


class ThermalManager:
    def __init__(self, storage_service: StudyStorageService):
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
            study (Study): The study to get the cluster from.
            area_id (str): The ID of the area where the cluster is located.
            cluster_id (str): The ID of the cluster to retrieve.

        Returns:
            ThermalClusterOutput: The cluster with the specified ID.

        Raises:
            ClusterNotFound: If the specified cluster does not exist.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ClusterNotFound(cluster_id)
        return ThermalClusterOutput.from_config(cluster_id, cluster)

    def get_clusters(
        self,
        study: Study,
        area_id: str,
    ) -> Sequence[ThermalClusterOutput]:
        """
        Get all clusters for an area.

        Args:
            study (Study): The study where the clusters will be retrieved from.
            area_id (str): The ID of the area where the clusters will be retrieved from.

        Returns:
            Sequence[ThermalClusterOutput]: A sequence of all clusters for the specified area.

        Raises:
            ClusterConfigNotFound: If the specified area does not have any clusters.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ClusterConfigNotFound(area_id)
        return [ThermalClusterOutput.from_config(cluster_id, cluster) for cluster_id, cluster in clusters.items()]

    def create_cluster(self, study: Study, area_id: str, cluster_data: ThermalClusterCreation) -> ThermalClusterOutput:
        """
        Create a new cluster.

        Args:
            study (Study): The study where the cluster will be created.
            area_id (str): The ID of the area where the cluster will be created.
            cluster_data (ThermalClusterInput): The data for the new cluster.

        Returns:
            ThermalClusterOutput: The created cluster.
        """

        file_study = self._get_file_study(study)
        cluster = cluster_data.dict(exclude_defaults=True)
        command = CreateCluster(
            area_id=area_id,
            cluster_name=cluster["name"],
            parameters=cluster,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study,
            file_study,
            [command],
            self.storage_service,
        )
        return self.get_cluster(study, area_id, cluster["name"])

    def update_cluster(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        cluster_data: ThermalClusterInput,
    ) -> ThermalClusterOutput:
        """
        Update a cluster with the given cluster_id in the given area_id of the given study with the provided cluster_data.

        Args:
        - study (Study): The study containing the area and cluster to update.
        - area_id (str): The ID of the area containing the cluster to update.
        - cluster_id (str): The ID of the cluster to update.
        - cluster_data (ThermalClusterInput): The new data to update the cluster with.

        Returns:
        - ThermalClusterOutput: The updated cluster.

        Raises:
        - ClusterNotFound: If the provided cluster_id does not match the ID of the cluster in the provided cluster_data.
        """

        file_study = self._get_file_study(study)
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=cluster_id)
        existing_cluster = file_study.tree.get(path.split("/"), depth=1)

        config = ThermalClusterConfig(**existing_cluster)
        updated_cluster = {**config.dict(exclude={"id"}), **cluster_data.dict(by_alias=False, exclude_none=True)}
        new_config = ThermalClusterConfig(**updated_cluster)
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

    def delete_clusters(self, study: Study, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Delete the clusters with the given IDs in the given area of the given study.

        Args:
        - study (Study): The study containing the area and clusters to delete.
        - area_id (str): The ID of the area containing the clusters to delete.
        - cluster_ids (Sequence[str]): The IDs of the clusters to delete.
        """

        file_study = self._get_file_study(study)
        command_context = self.storage_service.variant_study_service.command_factory.command_context

        commands = [
            RemoveCluster(area_id=area_id, cluster_id=cluster_id, command_context=command_context)
            for cluster_id in cluster_ids
        ]

        execute_or_add_commands(study, file_study, commands, self.storage_service)
