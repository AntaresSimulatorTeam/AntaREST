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

from antarest.study.business.binding_constraint_management import (
    BindingConstraintManager,
)
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
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class TableTemplateType(str, Enum):
    AREA = "area"
    LINK = "link"
    CLUSTER = "cluster"
    RENEWABLE = "renewable"
    BINDING_CONSTRAINT = "binding constraint"


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


class TimeSeriesMode(str, Enum):
    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


class BindingConstraintType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(str, Enum):
    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


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


class RenewableColumns(FormFieldsBaseModel):
    group: Optional[StrictStr]
    ts_interpretation: Optional[TimeSeriesMode]
    enabled: Optional[StrictBool]
    unit_count: Optional[StrictInt]
    nominal_capacity: Optional[StrictInt]


class BindingConstraintColumns(FormFieldsBaseModel):
    type: Optional[BindingConstraintType]
    operator: Optional[BindingConstraintOperator]
    enabled: Optional[StrictBool]


class ColumnInfo(TypedDict):
    path: str
    default_value: Any


class PathVars(TypedDict, total=False):
    # Area
    id: str
    # Link
    area1: str
    area2: str
    # Cluster, Renewable
    area: str
    cluster: str


AREA_FIELD_PATH_BASE = "input/areas/{id}/optimization"
ECONOMIC_OPTIONS_PATH_BASE = "input/thermal/areas"
LINK_FIELD_PATH_BASE = "input/links/{area1}/properties/{area2}"
CLUSTER_FIELD_PATH_BASE = "input/thermal/clusters/{area}/list/{cluster}"
RENEWABLE_FIELD_PATH_BASE = "input/renewables/clusters/{area}/list/{cluster}"
BINDING_CONSTRAINT_FIELD_PATH_BASE = (
    "input/bindingconstraints/bindingconstraints"
)

FIELDS_INFO_BY_TYPE: Dict[TableTemplateType, Dict[str, ColumnInfo]] = {
    TableTemplateType.AREA: {
        "non_dispatchable_power": {
            "path": f"{AREA_FIELD_PATH_BASE}/nodal optimization/non-dispatchable-power",
            "default_value": NodalOptimization.NON_DISPATCHABLE_POWER,
        },
        "dispatchable_hydro_power": {
            "path": f"{AREA_FIELD_PATH_BASE}/nodal optimization/dispatchable-hydro-power",
            "default_value": NodalOptimization.DISPATCHABLE_HYDRO_POWER,
        },
        "other_dispatchable_power": {
            "path": f"{AREA_FIELD_PATH_BASE}/nodal optimization/other-dispatchable-power",
            "default_value": NodalOptimization.OTHER_DISPATCHABLE_POWER,
        },
        "average_unsupplied_energy_cost": {
            "path": f"{ECONOMIC_OPTIONS_PATH_BASE}/unserverdenergycost/{{id}}",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "spread_unsupplied_energy_cost": {
            "path": f"{AREA_FIELD_PATH_BASE}/nodal optimization/spread-unsupplied-energy-cost",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "average_spilled_energy_cost": {
            "path": f"{ECONOMIC_OPTIONS_PATH_BASE}/spilledenergycost/{{id}}",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "spread_spilled_energy_cost": {
            "path": f"{AREA_FIELD_PATH_BASE}/nodal optimization/spread-spilled-energy-cost",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "filter_synthesis": {
            "path": f"{AREA_FIELD_PATH_BASE}/filtering/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "path": f"{AREA_FIELD_PATH_BASE}/filtering/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
        "adequacy_patch_mode": {
            "path": f"{AREA_FIELD_PATH_BASE}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
            "default_value": AdequacyPatchMode.OUTSIDE.value,
        },
    },
    TableTemplateType.LINK: {
        "hurdles_cost": {
            "path": f"{LINK_FIELD_PATH_BASE}/hurdles-cost",
            "default_value": LinkProperties.HURDLES_COST,
        },
        "loop_flow": {
            "path": f"{LINK_FIELD_PATH_BASE}/loop-flow",
            "default_value": LinkProperties.LOOP_FLOW,
        },
        "use_phase_shifter": {
            "path": f"{LINK_FIELD_PATH_BASE}/use-phase-shifter",
            "default_value": LinkProperties.USE_PHASE_SHIFTER,
        },
        "transmission_capacities": {
            "path": f"{LINK_FIELD_PATH_BASE}/transmission-capacities",
            "default_value": LinkProperties.TRANSMISSION_CAPACITIES,
        },
        "asset_type": {
            "path": f"{LINK_FIELD_PATH_BASE}/asset-type",
            "default_value": LinkProperties.ASSET_TYPE,
        },
        "link_style": {
            "path": f"{LINK_FIELD_PATH_BASE}/link-style",
            "default_value": LinkProperties.LINK_STYLE,
        },
        "link_width": {
            "path": f"{LINK_FIELD_PATH_BASE}/link-width",
            "default_value": LinkProperties.LINK_WIDTH,
        },
        "display_comments": {
            "path": f"{LINK_FIELD_PATH_BASE}/display-comments",
            "default_value": LinkProperties.DISPLAY_COMMENTS,
        },
        "filter_synthesis": {
            "path": f"{LINK_FIELD_PATH_BASE}/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "path": f"{LINK_FIELD_PATH_BASE}/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
    },
    TableTemplateType.CLUSTER: {
        "group": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/group",
            "default_value": "",
        },
        "enabled": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/enabled",
            "default_value": True,
        },
        "must_run": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/must-run",
            "default_value": False,
        },
        "unit_count": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/nominalcapacity",
            "default_value": 0,
        },
        "min_stable_power": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/min-stable-power",
            "default_value": 0,
        },
        "spinning": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/spinning",
            "default_value": 0,
        },
        "min_up_time": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/min-up-time",
            "default_value": 1,
        },
        "min_down_time": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/min-down-time",
            "default_value": 1,
        },
        "co2": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/co2",
            "default_value": 0,
        },
        "marginal_cost": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/marginal-cost",
            "default_value": 0,
        },
        "fixed_cost": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/fixed-cost",
            "default_value": 0,
        },
        "startup_cost": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/startup-cost",
            "default_value": 0,
        },
        "market_bid_cost": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/market-bid-cost",
            "default_value": 0,
        },
        "spread_cost": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/spread-cost",
            "default_value": 0,
        },
        "ts_gen": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/gen-ts",
            "default_value": TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER.value,
        },
        "volatility_forced": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/volatility.forced",
            "default_value": 0,
        },
        "volatility_planned": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/volatility.planned",
            "default_value": 0,
        },
        "law_forced": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/law.forced",
            "default_value": LawOption.UNIFORM.value,
        },
        "law_planned": {
            "path": f"{CLUSTER_FIELD_PATH_BASE}/law.planned",
            "default_value": LawOption.UNIFORM.value,
        },
    },
    TableTemplateType.RENEWABLE: {
        "group": {
            "path": f"{RENEWABLE_FIELD_PATH_BASE}/group",
            "default_value": "",
        },
        "ts_interpretation": {
            "path": f"{RENEWABLE_FIELD_PATH_BASE}/ts-interpretation",
            "default_value": TimeSeriesMode.POWER_GENERATION.value,
        },
        "enabled": {
            "path": f"{RENEWABLE_FIELD_PATH_BASE}/enabled",
            "default_value": True,
        },
        "unit_count": {
            "path": f"{RENEWABLE_FIELD_PATH_BASE}/unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "path": f"{RENEWABLE_FIELD_PATH_BASE}/nominalcapacity",
            "default_value": 0,
        },
    },
    TableTemplateType.BINDING_CONSTRAINT: {
        "type": {
            "path": f"{BINDING_CONSTRAINT_FIELD_PATH_BASE}/type",
            "default_value": BindingConstraintType.HOURLY.value,
        },
        "operator": {
            "path": f"{BINDING_CONSTRAINT_FIELD_PATH_BASE}/operator",
            "default_value": BindingConstraintOperator.LESS.value,
        },
        "enabled": {
            "path": f"{BINDING_CONSTRAINT_FIELD_PATH_BASE}/enabled",
            "default_value": True,
        },
    },
}

COLUMN_MODELS_BY_TYPE = {
    TableTemplateType.AREA: AreaColumns,
    TableTemplateType.LINK: LinkColumns,
    TableTemplateType.CLUSTER: ClusterColumns,
    TableTemplateType.RENEWABLE: RenewableColumns,
    TableTemplateType.BINDING_CONSTRAINT: BindingConstraintColumns,
}

ColumnModelTypes = Union[
    AreaColumns,
    LinkColumns,
    ClusterColumns,
    RenewableColumns,
    BindingConstraintColumns,
]


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

        def get_column_value(col: str, data: Dict[str, Any]) -> Any:
            f_info = fields_info[col]
            relative_path = TableModeManager.__get_relative_path(
                f_info["path"], table_type
            )
            return TableModeManager.__get_value(
                relative_path,
                data,
                f_info["default_value"],
            )

        if table_type == TableTemplateType.AREA:
            return {
                area_id: column_model.construct(
                    **{col: get_column_value(col, data) for col in columns}
                )  # type: ignore
                for area_id, data in glob_object.items()
            }

        if table_type == TableTemplateType.BINDING_CONSTRAINT:
            return {
                data["id"]: column_model.construct(
                    **{col: get_column_value(col, data) for col in columns}
                )  # type: ignore
                for data in glob_object.values()
            }

        obj: Dict[str, Any] = {}
        for id_1, value_1 in glob_object.items():
            for id_2, value_2 in value_1.items():
                obj[f"{id_1} / {id_2}"] = column_model.construct(
                    **{col: get_column_value(col, value_2) for col in columns}
                )

        return obj

    def set_table_data(
        self,
        study: RawStudy,
        table_type: TableTemplateType,
        data: Dict[str, ColumnModelTypes],
    ) -> None:
        commands: List[ICommand] = []
        bindings_by_id = None

        for key, columns in data.items():
            path_vars = TableModeManager.__get_path_vars_from_key(
                table_type, key
            )

            if table_type == TableTemplateType.BINDING_CONSTRAINT:
                file_study = self.storage_service.get_storage(study).get_raw(
                    study
                )
                bindings_by_id = bindings_by_id or {
                    binding["id"]: binding
                    for binding in TableModeManager.__get_glob_object(
                        file_study, table_type
                    ).values()
                }
                binding_id = path_vars["id"]
                current_binding = bindings_by_id.get(binding_id, None)

                if current_binding:
                    col_values = columns.dict(exclude_none=True)
                    current_binding_dto = (
                        BindingConstraintManager.process_constraint(
                            current_binding
                        )
                    )

                    commands.append(
                        UpdateBindingConstraint(
                            id=binding_id,
                            enabled=col_values.get(
                                "enabled", current_binding_dto.enabled
                            ),
                            time_step=col_values.get(
                                "type", current_binding_dto.time_step
                            ),
                            operator=col_values.get(
                                "operator", current_binding_dto.operator
                            ),
                            coeffs=BindingConstraintManager.constraints_to_coeffs(
                                current_binding_dto
                            ),
                            command_context=self.storage_service.variant_study_service.command_factory.command_context,
                        )
                    )
            else:
                for col, val in columns.__iter__():
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
    def __get_relative_path(
        path: str,
        table_type: TableTemplateType,
    ) -> List[str]:
        base_path = ""
        path_arr = path.split("/")

        if table_type == TableTemplateType.AREA:
            if path.startswith(ECONOMIC_OPTIONS_PATH_BASE):
                base_path = ECONOMIC_OPTIONS_PATH_BASE
                # Remove {id}
                path_arr = path_arr[:-1]
            else:
                base_path = AREA_FIELD_PATH_BASE
        elif table_type == TableTemplateType.LINK:
            base_path = LINK_FIELD_PATH_BASE
        elif table_type == TableTemplateType.CLUSTER:
            base_path = CLUSTER_FIELD_PATH_BASE
        elif table_type == TableTemplateType.RENEWABLE:
            base_path = RENEWABLE_FIELD_PATH_BASE
        elif table_type == TableTemplateType.BINDING_CONSTRAINT:
            base_path = BINDING_CONSTRAINT_FIELD_PATH_BASE

        return path_arr[len(base_path.split("/")) :]

    @staticmethod
    def __get_column_path(
        table_type: TableTemplateType,
        path_vars: PathVars,
        column: str,
    ) -> str:
        path = FIELDS_INFO_BY_TYPE[table_type][column]["path"]

        if table_type == TableTemplateType.AREA:
            return path.replace("{id}", path_vars["id"])
        if table_type == TableTemplateType.LINK:
            return path.replace("{area1}", path_vars["area1"]).replace(
                "{area2}", path_vars["area2"]
            )
        if table_type in [
            TableTemplateType.CLUSTER,
            TableTemplateType.RENEWABLE,
        ]:
            return path.replace("{area}", path_vars["area"]).replace(
                "{cluster}", path_vars["cluster"]
            )

        return path

    @staticmethod
    def __get_path_vars_from_key(
        table_type: TableTemplateType,
        key: str,
    ) -> PathVars:
        if table_type in [
            TableTemplateType.AREA,
            TableTemplateType.BINDING_CONSTRAINT,
        ]:
            return PathVars(id=key)
        if table_type == TableTemplateType.LINK:
            area1, area2 = [v.strip() for v in key.split("/")]
            return PathVars(area1=area1, area2=area2)
        if table_type in [
            TableTemplateType.CLUSTER,
            TableTemplateType.RENEWABLE,
        ]:
            area, cluster = [v.strip() for v in key.split("/")]
            return PathVars(area=area, cluster=cluster)

        return PathVars()

    @staticmethod
    def __get_glob_object(
        file_study: FileStudy, table_type: TableTemplateType
    ) -> Dict[str, Any]:
        if table_type == TableTemplateType.AREA:
            data: Dict[str, Any] = file_study.tree.get(
                AREA_FIELD_PATH_BASE.replace("{id}", "*").split("/")
            )

            # Add economic options in data
            economic_opts = file_study.tree.get(
                ECONOMIC_OPTIONS_PATH_BASE.split("/")
            )
            for opt in economic_opts:
                for area in economic_opts[opt]:
                    if area in data:
                        data[area] = {
                            **data[area],
                            opt: economic_opts[opt][area],
                        }

            return data
        if table_type == TableTemplateType.LINK:
            return file_study.tree.get(
                LINK_FIELD_PATH_BASE.replace("{area1}", "*")
                .replace("/{area2}", "")
                .split("/")
            )
        if table_type == TableTemplateType.CLUSTER:
            return file_study.tree.get(
                CLUSTER_FIELD_PATH_BASE.replace("{area}", "*")
                .replace("/{cluster}", "")
                .split("/")
            )
        if table_type == TableTemplateType.RENEWABLE:
            return file_study.tree.get(
                RENEWABLE_FIELD_PATH_BASE.replace("{area}", "*")
                .replace("/{cluster}", "")
                .split("/")
            )
        if table_type == TableTemplateType.BINDING_CONSTRAINT:
            return file_study.tree.get(
                BINDING_CONSTRAINT_FIELD_PATH_BASE.split("/")
            )

        return {}
