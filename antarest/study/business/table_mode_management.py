from enum import Enum
from typing import (
    Optional,
    Dict,
    TypedDict,
    Union,
    Any,
    List,
)

from pydantic import StrictFloat
from pydantic.types import StrictStr, StrictInt, StrictBool

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.default_values import (
    NodalOptimization,
    FilteringOptions,
    LinkProperties,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class TableTemplateType(str, Enum):
    AREA = "area"
    LINK = "link"
    CLUSTER = "cluster"


class AdequacyPatchMode(str, Enum):
    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


class AssetType(str, Enum):
    AC = "ac"
    DC = "dc"
    GAZ = "gaz"
    VIRT = "virt"
    OTHER = "other"


class TransmissionCapacity(str, Enum):
    INFINITE = "infinite"
    IGNORE = "ignore"
    ENABLED = "enabled"


class TimeSeriesGenerationOption(str, Enum):
    USE_GLOBAL_PARAMETER = "use global parameter"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(str, Enum):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class AreaColumns(FormFieldsBaseModel):
    # Optimization - Nodal optimization
    non_dispatchable_power: Optional[StrictBool]
    dispatchable_hydro_power: Optional[StrictBool]
    other_dispatchable_power: Optional[StrictBool]
    spread_unsupplied_energy_cost: Optional[Union[StrictFloat, StrictInt]]
    spread_spilled_energy_cost: Optional[Union[StrictFloat, StrictInt]]
    # Optimization - Filtering
    filter_synthesis: Optional[StrictStr]
    filter_year_by_year: Optional[StrictStr]
    # Adequacy patch
    adequacy_patch_mode: Optional[AdequacyPatchMode]


class LinkColumns(FormFieldsBaseModel):
    hurdles_cost: Optional[StrictBool]
    loop_flow: Optional[StrictBool]
    use_phase_shifter: Optional[StrictBool]
    transmission_capacities: Optional[TransmissionCapacity]
    asset_type: Optional[AssetType]
    link_style: Optional[StrictStr]
    link_width: Optional[StrictInt]
    display_comments: Optional[StrictBool]
    filter_synthesis: Optional[StrictStr]
    filter_year_by_year: Optional[StrictStr]


class ClusterColumns(FormFieldsBaseModel):
    group: Optional[StrictStr]
    enabled: Optional[StrictBool]
    must_run: Optional[StrictBool]
    unit_count: Optional[StrictInt]
    nominal_capacity: Optional[StrictInt]
    min_stable_power: Optional[StrictInt]
    spinning: Optional[StrictInt]
    min_up_time: Optional[StrictInt]
    min_down_time: Optional[StrictInt]
    co2: Optional[StrictInt]
    marginal_cost: Optional[StrictInt]
    fixed_cost: Optional[StrictInt]
    startup_cost: Optional[StrictInt]
    market_bid_cost: Optional[StrictInt]
    spread_cost: Optional[StrictInt]
    ts_gen: Optional[TimeSeriesGenerationOption]
    volatility_forced: Optional[StrictInt]
    volatility_planned: Optional[StrictInt]
    law_forced: Optional[LawOption]
    law_planned: Optional[LawOption]


class ColumnInfo(TypedDict):
    path: str
    default_value: Any


class PathVars(TypedDict, total=False):
    # Area
    id: str
    # Link
    area1: str
    area2: str
    # Cluster
    area: str
    cluster: str


AREA_FIELD_PATH_PREFIX = "input/areas/{id}/optimization"
LINK_FIELD_PATH_PREFIX = "input/links/{area1}/properties/{area2}"
CLUSTER_FIELD_PATH_PREFIX = "input/thermal/clusters/{area}/list/{cluster}"

FIELDS_INFO_BY_TYPE: Dict[TableTemplateType, Dict[str, ColumnInfo]] = {
    TableTemplateType.AREA: {
        "non_dispatchable_power": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/nodal optimization/non-dispatchable-power",
            "default_value": NodalOptimization.NON_DISPATCHABLE_POWER.value,
        },
        "dispatchable_hydro_power": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/nodal optimization/dispatchable-hydro-power",
            "default_value": NodalOptimization.DISPATCHABLE_HYDRO_POWER.value,
        },
        "other_dispatchable_power": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/nodal optimization/other-dispatchable-power",
            "default_value": NodalOptimization.OTHER_DISPATCHABLE_POWER.value,
        },
        "spread_unsupplied_energy_cost": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/nodal optimization/spread-unsupplied-energy-cost",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST.value,
        },
        "spread_spilled_energy_cost": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/nodal optimization/spread-spilled-energy-cost",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST.value,
        },
        "filter_synthesis": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/filtering/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS.value,
        },
        "filter_year_by_year": {
            "path": f"{AREA_FIELD_PATH_PREFIX}/filtering/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR.value,
        },
        "adequacy_patch_mode": {
            "path": "input/areas/{id}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
            "default_value": AdequacyPatchMode.OUTSIDE.value,
        },
    },
    TableTemplateType.LINK: {
        "hurdles_cost": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/hurdles-cost",
            "default_value": LinkProperties.HURDLES_COST.value,
        },
        "loop_flow": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/loop-flow",
            "default_value": LinkProperties.LOOP_FLOW.value,
        },
        "use_phase_shifter": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/use-phase-shifter",
            "default_value": LinkProperties.USE_PHASE_SHIFTER.value,
        },
        "transmission_capacities": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/transmission-capacities",
            "default_value": LinkProperties.TRANSMISSION_CAPACITIES.value,
        },
        "asset_type": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/asset-type",
            "default_value": LinkProperties.ASSET_TYPE.value,
        },
        "link_style": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/link-style",
            "default_value": LinkProperties.LINK_STYLE.value,
        },
        "link_width": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/link-width",
            "default_value": LinkProperties.LINK_WIDTH.value,
        },
        "display_comments": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/display-comments",
            "default_value": LinkProperties.DISPLAY_COMMENTS.value,
        },
        "filter_synthesis": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS.value,
        },
        "filter_year_by_year": {
            "path": f"{LINK_FIELD_PATH_PREFIX}/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR.value,
        },
    },
    TableTemplateType.CLUSTER: {
        "group": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/group",
            "default_value": "",
        },
        "enabled": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/enabled",
            "default_value": True,
        },
        "must_run": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/must-run",
            "default_value": False,
        },
        "unit_count": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/nominalcapacity",
            "default_value": 0,
        },
        "min_stable_power": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/min-stable-power",
            "default_value": 0,
        },
        "spinning": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/spinning",
            "default_value": 0,
        },
        "min_up_time": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/min-up-time",
            "default_value": 1,
        },
        "min_down_time": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/min-down-time",
            "default_value": 1,
        },
        "co2": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/co2",
            "default_value": 0,
        },
        "marginal_cost": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/marginal-cost",
            "default_value": 0,
        },
        "fixed_cost": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/fixed-cost",
            "default_value": 0,
        },
        "startup_cost": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/startup-cost",
            "default_value": 0,
        },
        "market_bid_cost": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/market-bid-cost",
            "default_value": 0,
        },
        "spread_cost": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/spread-cost",
            "default_value": 0,
        },
        "ts_gen": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/gen-ts",
            "default_value": TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER.value,
        },
        "volatility_forced": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/volatility.forced",
            "default_value": 0,
        },
        "volatility_planned": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/volatility.planned",
            "default_value": 0,
        },
        "law_forced": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/law.forced",
            "default_value": LawOption.UNIFORM.value,
        },
        "law_planned": {
            "path": f"{CLUSTER_FIELD_PATH_PREFIX}/law.planned",
            "default_value": LawOption.UNIFORM.value,
        },
    },
}

COLUMN_MODELS_BY_TYPE = {
    TableTemplateType.AREA: AreaColumns,
    TableTemplateType.LINK: LinkColumns,
    TableTemplateType.CLUSTER: ClusterColumns,
}

ColumnModelTypes = Union[AreaColumns, LinkColumns, ClusterColumns]


class TableModeManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_table_data(
        self,
        study: RawStudy,
        table_type: TableTemplateType,
        columns: List[str],
    ) -> Dict[str, ColumnModelTypes]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        column_model = COLUMN_MODELS_BY_TYPE[table_type]
        fields_info = FIELDS_INFO_BY_TYPE[table_type]
        glob_object = TableModeManager.__get_glob_object(
            file_study, table_type
        )

        if table_type == TableTemplateType.AREA:

            def get_value_from_data(col: str, data: Dict[str, Any]) -> Any:
                field_info = fields_info[col]
                parent_name, field_name = field_info["path"].split("/")[-2:]
                return data.get(parent_name, {}).get(
                    field_name, field_info["default_value"]
                )

            return {
                area_id: column_model.construct(
                    **{col: get_value_from_data(col, data) for col in columns}
                )  # type: ignore
                for area_id, data in glob_object.items()
            }

        obj: Dict[str, Any] = {}
        for id_1, value_1 in glob_object.items():
            for id_2, value_2 in value_1.items():
                obj[f"{id_1} / {id_2}"] = column_model.construct(
                    **{
                        col: value_2.get(
                            fields_info[col]["path"].split("/")[-1],
                            fields_info[col]["default_value"],
                        )
                        for col in columns
                    }
                )

        return obj

    def set_table_data(
        self,
        study: RawStudy,
        table_type: TableTemplateType,
        data: Dict[str, ColumnModelTypes],
    ) -> None:
        commands: List[UpdateConfig] = []

        for key, values in data.items():
            path_vars = TableModeManager.__get_path_vars_from_key(
                table_type, key
            )
            if path_vars is not None:
                for col, val in values.__iter__():
                    if val is not None:
                        commands.append(
                            UpdateConfig(
                                target=TableModeManager.__get_column_path(
                                    table_type, path_vars, col
                                ),
                                data=val,
                                command_context=self.storage_service.variant_study_service.command_factory.command_context,
                            )
                        )

        if len(commands) > 0:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )

    @staticmethod
    def __get_column_path(
        table_type: TableTemplateType,
        path_vars: PathVars,
        column: str,
    ) -> str:
        path = FIELDS_INFO_BY_TYPE[table_type][column]["path"]
        if table_type == TableTemplateType.LINK:
            return path.replace("{area1}", path_vars["area1"]).replace(
                "{area2}", path_vars["area2"]
            )
        if table_type == TableTemplateType.CLUSTER:
            return path.replace("{area}", path_vars["area"]).replace(
                "{cluster}", path_vars["cluster"]
            )
        # Area
        return path.replace("{id}", path_vars["id"])

    @staticmethod
    def __get_path_vars_from_key(
        table_type: TableTemplateType,
        key: str,
    ) -> Optional[PathVars]:
        if table_type == TableTemplateType.AREA:
            return PathVars(id=key)
        elif table_type == TableTemplateType.LINK:
            area1, area2 = [v.strip() for v in key.split("/")]
            return PathVars(area1=area1, area2=area2)
        elif table_type == TableTemplateType.CLUSTER:
            area, cluster = [v.strip() for v in key.split("/")]
            return PathVars(area=area, cluster=cluster)
        return None

    @staticmethod
    def __get_glob_object(
        file_study: FileStudy, table_type: TableTemplateType
    ) -> Dict[str, Any]:
        if table_type == TableTemplateType.AREA:
            return file_study.tree.get(
                AREA_FIELD_PATH_PREFIX.replace("{id}", "*").split("/")
            )
        elif table_type == TableTemplateType.LINK:
            return file_study.tree.get(
                LINK_FIELD_PATH_PREFIX.replace("{area1}", "*")
                .replace("/{area2}", "")
                .split("/")
            )
        elif table_type == TableTemplateType.CLUSTER:
            return file_study.tree.get(
                CLUSTER_FIELD_PATH_PREFIX.replace("{area}", "*")
                .replace("/{cluster}", "")
                .split("/")
            )
        return {}
