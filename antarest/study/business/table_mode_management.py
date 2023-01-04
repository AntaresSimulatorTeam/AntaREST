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
from antarest.study.common.default_values import (
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
    average_unsupplied_energy_cost: Optional[Union[StrictFloat, StrictInt]]
    spread_unsupplied_energy_cost: Optional[Union[StrictFloat, StrictInt]]
    average_spilled_energy_cost: Optional[Union[StrictFloat, StrictInt]]
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
    glob_path: str
    rel_glob_path: str
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
ECONOMIC_OPTIONS_PREFIX = "input/thermal/areas"
LINK_FIELD_PATH_PREFIX = "input/links/{area1}/properties/{area2}"
CLUSTER_FIELD_PATH_PREFIX = "input/thermal/clusters/{area}/list/{cluster}"

FIELDS_INFO_BY_TYPE: Dict[TableTemplateType, Dict[str, ColumnInfo]] = {
    TableTemplateType.AREA: {
        "non_dispatchable_power": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "nodal optimization/non-dispatchable-power",
            "default_value": NodalOptimization.NON_DISPATCHABLE_POWER,
        },
        "dispatchable_hydro_power": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "nodal optimization/dispatchable-hydro-power",
            "default_value": NodalOptimization.DISPATCHABLE_HYDRO_POWER,
        },
        "other_dispatchable_power": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "nodal optimization/other-dispatchable-power",
            "default_value": NodalOptimization.OTHER_DISPATCHABLE_POWER,
        },
        "average_unsupplied_energy_cost": {
            "glob_path": ECONOMIC_OPTIONS_PREFIX,
            "rel_glob_path": "unserverdenergycost",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "spread_unsupplied_energy_cost": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "nodal optimization/spread-unsupplied-energy-cost",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "average_spilled_energy_cost": {
            "glob_path": ECONOMIC_OPTIONS_PREFIX,
            "rel_glob_path": "spilledenergycost",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "spread_spilled_energy_cost": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "nodal optimization/spread-spilled-energy-cost",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "filter_synthesis": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "filtering/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "filtering/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
        "adequacy_patch_mode": {
            "glob_path": AREA_FIELD_PATH_PREFIX,
            "rel_glob_path": "adequacy_patch/adequacy-patch/adequacy-patch-mode",
            "default_value": AdequacyPatchMode.OUTSIDE.value,
        },
    },
    TableTemplateType.LINK: {
        "hurdles_cost": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "hurdles-cost",
            "default_value": LinkProperties.HURDLES_COST,
        },
        "loop_flow": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "loop-flow",
            "default_value": LinkProperties.LOOP_FLOW,
        },
        "use_phase_shifter": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "use-phase-shifter",
            "default_value": LinkProperties.USE_PHASE_SHIFTER,
        },
        "transmission_capacities": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "transmission-capacities",
            "default_value": LinkProperties.TRANSMISSION_CAPACITIES,
        },
        "asset_type": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "asset-type",
            "default_value": LinkProperties.ASSET_TYPE,
        },
        "link_style": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "link-style",
            "default_value": LinkProperties.LINK_STYLE,
        },
        "link_width": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "link-width",
            "default_value": LinkProperties.LINK_WIDTH,
        },
        "display_comments": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "display-comments",
            "default_value": LinkProperties.DISPLAY_COMMENTS,
        },
        "filter_synthesis": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "glob_path": LINK_FIELD_PATH_PREFIX,
            "rel_glob_path": "filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
    },
    TableTemplateType.CLUSTER: {
        "group": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "group",
            "default_value": "",
        },
        "enabled": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "enabled",
            "default_value": True,
        },
        "must_run": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "must-run",
            "default_value": False,
        },
        "unit_count": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "nominalcapacity",
            "default_value": 0,
        },
        "min_stable_power": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "min-stable-power",
            "default_value": 0,
        },
        "spinning": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "spinning",
            "default_value": 0,
        },
        "min_up_time": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "min-up-time",
            "default_value": 1,
        },
        "min_down_time": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "min-down-time",
            "default_value": 1,
        },
        "co2": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "co2",
            "default_value": 0,
        },
        "marginal_cost": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "marginal-cost",
            "default_value": 0,
        },
        "fixed_cost": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "fixed-cost",
            "default_value": 0,
        },
        "startup_cost": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "startup-cost",
            "default_value": 0,
        },
        "market_bid_cost": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "market-bid-cost",
            "default_value": 0,
        },
        "spread_cost": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "spread-cost",
            "default_value": 0,
        },
        "ts_gen": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "gen-ts",
            "default_value": TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER.value,
        },
        "volatility_forced": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "volatility.forced",
            "default_value": 0,
        },
        "volatility_planned": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "volatility.planned",
            "default_value": 0,
        },
        "law_forced": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "law.forced",
            "default_value": LawOption.UNIFORM.value,
        },
        "law_planned": {
            "glob_path": CLUSTER_FIELD_PATH_PREFIX,
            "rel_glob_path": "law.planned",
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
                return TableModeManager.__get_value(
                    field_info["rel_glob_path"].split("/"),
                    data,
                    field_info["default_value"],
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
                            fields_info[col]["rel_glob_path"],
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
    def __get_value(
        path: List[str], data: Dict[str, Any], default_value: Any
    ) -> Any:
        if len(path):
            return TableModeManager.__get_value(
                path[1:], data.get(path[0], {}), default_value
            )
        return data if data != {} else default_value

    @staticmethod
    def __get_column_path(
        table_type: TableTemplateType,
        path_vars: PathVars,
        column: str,
    ) -> str:
        path = (
            FIELDS_INFO_BY_TYPE[table_type][column]["glob_path"]
            + "/"
            + FIELDS_INFO_BY_TYPE[table_type][column]["rel_glob_path"]
        )
        if table_type == TableTemplateType.LINK:
            return path.replace("{area1}", path_vars["area1"]).replace(
                "{area2}", path_vars["area2"]
            )
        if table_type == TableTemplateType.CLUSTER:
            return path.replace("{area}", path_vars["area"]).replace(
                "{cluster}", path_vars["cluster"]
            )
        # Area
        if "{id}" not in path:
            path += "/{id}"
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
            data: Dict[str, Any] = file_study.tree.get(
                AREA_FIELD_PATH_PREFIX.replace("{id}", "*").split("/")
            )
            ecopts = file_study.tree.get(ECONOMIC_OPTIONS_PREFIX.split("/"))
            for opt in ecopts:
                for area in ecopts[opt]:
                    data[area] = {**data.get(area, {}), opt: ecopts[opt][area]}
            return data
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
