from typing import Any, Dict, List, Optional, TypedDict, Union, cast
from pydantic import Field
from antarest.study.business.areas.properties_management import AdequacyPatchMode
from antarest.study.business.areas.renewable_management import TimeSeriesInterpretation
from antarest.study.business.binding_constraint_management import BindingConstraintManager
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import FormFieldsBaseModel, execute_or_add_commands, AllOptionalMetaclass
from antarest.study.common.default_values import FilteringOptions, LinkProperties, NodalOptimization
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import LawOption, LocalTSGenerationBehavior
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas"
LINK_GLOB_PATH = "input/links/{area1}/properties"
LINK_PATH = f"{LINK_GLOB_PATH}/{{area2}}"
THERMAL_CLUSTER_GLOB_PATH = "input/thermal/clusters/{area}/list"
THERMAL_CLUSTER_PATH = f"{THERMAL_CLUSTER_GLOB_PATH}/{{cluster}}"
RENEWABLE_CLUSTER_GLOB_PATH = "input/renewables/clusters/{area}/list"
RENEWABLE_CLUSTER_PATH = f"{RENEWABLE_CLUSTER_GLOB_PATH}/{{cluster}}"
BINDING_CONSTRAINT_PATH = "input/bindingconstraints/bindingconstraints"


class TableTemplateType(EnumIgnoreCase):
    AREA = "area"
    LINK = "link"
    THERMAL_CLUSTER = "thermal cluster"
    RENEWABLE_CLUSTER = "renewable cluster"
    BINDING_CONSTRAINT = "binding constraint"


class AssetType(EnumIgnoreCase):
    AC = "ac"
    DC = "dc"
    GAZ = "gaz"
    VIRT = "virt"
    OTHER = "other"


class TransmissionCapacity(EnumIgnoreCase):
    INFINITE = "infinite"
    IGNORE = "ignore"
    ENABLED = "enabled"


class BindingConstraintOperator(EnumIgnoreCase):
    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


class AreaColumns(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    # Optimization - Nodal optimization
    non_dispatchable_power: bool = Field(
        default=NodalOptimization.NON_DISPATCHABLE_POWER,
        path=f"{AREA_PATH}/optimization/nodal optimization/non-dispatchable-power",
    )
    dispatchable_hydro_power: bool = Field(
        default=NodalOptimization.DISPATCHABLE_HYDRO_POWER,
        path=f"{AREA_PATH}/optimization/nodal optimization/dispatchable-hydro-power",
    )
    other_dispatchable_power: bool = Field(
        default=NodalOptimization.OTHER_DISPATCHABLE_POWER,
        path=f"{AREA_PATH}/optimization/nodal optimization/other-dispatchable-power",
    )
    average_unsupplied_energy_cost: float = Field(
        default=NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        path=f"{THERMAL_PATH}/unserverdenergycost/{{area}}",
    )
    spread_unsupplied_energy_cost: float = Field(
        default=NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        path=f"{AREA_PATH}/optimization/nodal optimization/spread-unsupplied-energy-cost",
    )
    average_spilled_energy_cost: float = Field(
        default=NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        path=f"{THERMAL_PATH}/spilledenergycost/{{area}}",
    )
    spread_spilled_energy_cost: float = Field(
        default=NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        path=f"{AREA_PATH}/optimization/nodal optimization/spread-spilled-energy-cost",
    )
    # Optimization - Filtering
    filter_synthesis: str = Field(
        default=FilteringOptions.FILTER_SYNTHESIS,
        path=f"{AREA_PATH}/optimization/filtering/filter-synthesis",
    )
    filter_year_by_year: str = Field(
        default=FilteringOptions.FILTER_YEAR_BY_YEAR,
        path=f"{AREA_PATH}/optimization/filtering/filter-year-by-year",
    )
    # Adequacy patch
    adequacy_patch_mode: AdequacyPatchMode = Field(
        default=AdequacyPatchMode.OUTSIDE.value,
        path=f"{AREA_PATH}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
    )


class LinkColumns(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    hurdles_cost: bool = Field(default=LinkProperties.HURDLES_COST, path=f"{LINK_PATH}/hurdles-cost")
    loop_flow: bool = Field(default=LinkProperties.LOOP_FLOW, path=f"{LINK_PATH}/loop-flow")
    use_phase_shifter: bool = Field(
        default=LinkProperties.USE_PHASE_SHIFTER,
        path=f"{LINK_PATH}/use-phase-shifter",
    )
    transmission_capacities: TransmissionCapacity = Field(
        default=LinkProperties.TRANSMISSION_CAPACITIES,
        path=f"{LINK_PATH}/transmission-capacities",
    )
    asset_type: AssetType = Field(default=LinkProperties.ASSET_TYPE, path=f"{LINK_PATH}/asset-type")
    link_style: str = Field(default=LinkProperties.LINK_STYLE, path=f"{LINK_PATH}/link-style")
    link_width: int = Field(default=LinkProperties.LINK_WIDTH, path=f"{LINK_PATH}/link-width")
    display_comments: bool = Field(
        default=LinkProperties.DISPLAY_COMMENTS,
        path=f"{LINK_PATH}/display-comments",
    )
    filter_synthesis: str = Field(
        default=FilteringOptions.FILTER_SYNTHESIS,
        path=f"{LINK_PATH}/filter-synthesis",
    )
    filter_year_by_year: str = Field(
        default=FilteringOptions.FILTER_YEAR_BY_YEAR,
        path=f"{LINK_PATH}/filter-year-by-year",
    )


class ThermalClusterColumns(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    group: str = Field(
        default="",
        path=f"{THERMAL_CLUSTER_PATH}/group",
    )
    enabled: bool = Field(
        default=True,
        path=f"{THERMAL_CLUSTER_PATH}/enabled",
    )
    must_run: bool = Field(
        default=False,
        path=f"{THERMAL_CLUSTER_PATH}/must-run",
    )
    unit_count: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/unitcount",
    )
    nominal_capacity: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/nominalcapacity",
    )
    min_stable_power: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/min-stable-power",
    )
    spinning: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/spinning",
    )
    min_up_time: int = Field(
        default=1,
        path=f"{THERMAL_CLUSTER_PATH}/min-up-time",
    )
    min_down_time: int = Field(
        default=1,
        path=f"{THERMAL_CLUSTER_PATH}/min-down-time",
    )
    marginal_cost: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/marginal-cost",
    )
    fixed_cost: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/fixed-cost",
    )
    startup_cost: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/startup-cost",
    )
    market_bid_cost: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/market-bid-cost",
    )
    spread_cost: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/spread-cost",
    )
    ts_gen: LocalTSGenerationBehavior = Field(
        default=LocalTSGenerationBehavior.USE_GLOBAL_PARAMETER.value,
        path=f"{THERMAL_CLUSTER_PATH}/gen-ts",
    )
    volatility_forced: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/volatility.forced",
    )
    volatility_planned: int = Field(
        default=0,
        path=f"{THERMAL_CLUSTER_PATH}/volatility.planned",
    )
    law_forced: LawOption = Field(
        default=LawOption.UNIFORM.value,
        path=f"{THERMAL_CLUSTER_PATH}/law.forced",
    )
    law_planned: LawOption = Field(
        default=LawOption.UNIFORM.value,
        path=f"{THERMAL_CLUSTER_PATH}/law.planned",
    )
    # Pollutants
    co2: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/co2",
    )
    so2: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/so2",
    )
    nh3: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/nh3",
    )
    nox: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/nox",
    )
    nmvoc: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/nmvoc",
    )
    pm25: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/pm2_5",
    )
    pm5: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/pm5",
    )
    pm10: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/pm10",
    )
    op1: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/op1",
    )
    op2: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/op2",
    )
    op3: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/op3",
    )
    op4: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/op4",
    )
    op5: float = Field(
        default=0.0,
        path=f"{THERMAL_CLUSTER_PATH}/op5",
    )


class RenewableClusterColumns(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    group: str = Field(default="", path=f"{RENEWABLE_CLUSTER_PATH}/group")
    ts_interpretation: TimeSeriesInterpretation = Field(
        default=TimeSeriesInterpretation.POWER_GENERATION.value,
        path=f"{RENEWABLE_CLUSTER_PATH}/ts-interpretation",
    )
    enabled: bool = Field(default=True, path=f"{RENEWABLE_CLUSTER_PATH}/enabled")
    unit_count: int = Field(default=0, path=f"{RENEWABLE_CLUSTER_PATH}/unitcount")
    nominal_capacity: int = Field(default=0, path=f"{RENEWABLE_CLUSTER_PATH}/nominalcapacity")


class BindingConstraintColumns(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    type: BindingConstraintFrequency = Field(
        default=BindingConstraintFrequency.HOURLY.value,
        path=f"{BINDING_CONSTRAINT_PATH}/type",
    )
    operator: BindingConstraintOperator = Field(
        default=BindingConstraintOperator.LESS.value,
        path=f"{BINDING_CONSTRAINT_PATH}/operator",
    )
    enabled: bool = Field(
        default=True,
        path=f"{BINDING_CONSTRAINT_PATH}/enabled",
    )
    group: Optional[str] = Field(
        default="default",
        path=f"{BINDING_CONSTRAINT_PATH}/group",
    )


class ColumnInfo(TypedDict):
    path: str
    default_value: Any


class PathVars(TypedDict, total=False):
    # Area
    id: str
    # Link
    area1: str
    area2: str
    # Thermal cluster, Renewable cluster
    area: str
    cluster: str


AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas"
LINK_GLOB_PATH = "input/links/{area1}/properties"
LINK_PATH = f"{LINK_GLOB_PATH}/{{area2}}"
CLUSTER_GLOB_PATH = "input/thermal/clusters/{area}/list"
CLUSTER_PATH = f"{CLUSTER_GLOB_PATH}/{{cluster}}"
RENEWABLE_GLOB_PATH = "input/renewables/clusters/{area}/list"
RENEWABLE_PATH = f"{RENEWABLE_GLOB_PATH}/{{cluster}}"
BINDING_CONSTRAINT_PATH = "input/bindingconstraints/bindingconstraints"

FIELDS_INFO_BY_TYPE: Dict[TableTemplateType, Dict[str, ColumnInfo]] = {
    TableTemplateType.AREA: {
        "non_dispatchable_power": {
            "path": f"{AREA_PATH}/optimization/nodal optimization/non-dispatchable-power",
            "default_value": NodalOptimization.NON_DISPATCHABLE_POWER,
        },
        "dispatchable_hydro_power": {
            "path": f"{AREA_PATH}/optimization/nodal optimization/dispatchable-hydro-power",
            "default_value": NodalOptimization.DISPATCHABLE_HYDRO_POWER,
        },
        "other_dispatchable_power": {
            "path": f"{AREA_PATH}/optimization/nodal optimization/other-dispatchable-power",
            "default_value": NodalOptimization.OTHER_DISPATCHABLE_POWER,
        },
        "average_unsupplied_energy_cost": {
            "path": f"{THERMAL_PATH}/unserverdenergycost/{{area}}",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "spread_unsupplied_energy_cost": {
            "path": f"{AREA_PATH}/optimization/nodal optimization/spread-unsupplied-energy-cost",
            "default_value": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
        },
        "average_spilled_energy_cost": {
            "path": f"{THERMAL_PATH}/spilledenergycost/{{area}}",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "spread_spilled_energy_cost": {
            "path": f"{AREA_PATH}/optimization/nodal optimization/spread-spilled-energy-cost",
            "default_value": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
        },
        "filter_synthesis": {
            "path": f"{AREA_PATH}/optimization/filtering/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "path": f"{AREA_PATH}/optimization/filtering/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
        "adequacy_patch_mode": {
            "path": f"{AREA_PATH}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
            "default_value": AdequacyPatchMode.OUTSIDE.value,
        },
    },
    TableTemplateType.LINK: {
        "hurdles_cost": {
            "path": f"{LINK_PATH}/hurdles-cost",
            "default_value": LinkProperties.HURDLES_COST,
        },
        "loop_flow": {
            "path": f"{LINK_PATH}/loop-flow",
            "default_value": LinkProperties.LOOP_FLOW,
        },
        "use_phase_shifter": {
            "path": f"{LINK_PATH}/use-phase-shifter",
            "default_value": LinkProperties.USE_PHASE_SHIFTER,
        },
        "transmission_capacities": {
            "path": f"{LINK_PATH}/transmission-capacities",
            "default_value": LinkProperties.TRANSMISSION_CAPACITIES,
        },
        "asset_type": {
            "path": f"{LINK_PATH}/asset-type",
            "default_value": LinkProperties.ASSET_TYPE,
        },
        "link_style": {
            "path": f"{LINK_PATH}/link-style",
            "default_value": LinkProperties.LINK_STYLE,
        },
        "link_width": {
            "path": f"{LINK_PATH}/link-width",
            "default_value": LinkProperties.LINK_WIDTH,
        },
        "display_comments": {
            "path": f"{LINK_PATH}/display-comments",
            "default_value": LinkProperties.DISPLAY_COMMENTS,
        },
        "filter_synthesis": {
            "path": f"{LINK_PATH}/filter-synthesis",
            "default_value": FilteringOptions.FILTER_SYNTHESIS,
        },
        "filter_year_by_year": {
            "path": f"{LINK_PATH}/filter-year-by-year",
            "default_value": FilteringOptions.FILTER_YEAR_BY_YEAR,
        },
    },
    TableTemplateType.CLUSTER: {
        "group": {
            "path": f"{CLUSTER_PATH}/group",
            "default_value": "",
        },
        "enabled": {
            "path": f"{CLUSTER_PATH}/enabled",
            "default_value": True,
        },
        "must_run": {
            "path": f"{CLUSTER_PATH}/must-run",
            "default_value": False,
        },
        "unit_count": {
            "path": f"{CLUSTER_PATH}/unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "path": f"{CLUSTER_PATH}/nominalcapacity",
            "default_value": 0,
        },
        "min_stable_power": {
            "path": f"{CLUSTER_PATH}/min-stable-power",
            "default_value": 0,
        },
        "spinning": {
            "path": f"{CLUSTER_PATH}/spinning",
            "default_value": 0,
        },
        "min_up_time": {
            "path": f"{CLUSTER_PATH}/min-up-time",
            "default_value": 1,
        },
        "min_down_time": {
            "path": f"{CLUSTER_PATH}/min-down-time",
            "default_value": 1,
        },
        "co2": {
            "path": f"{CLUSTER_PATH}/co2",
            "default_value": 0,
        },
        "marginal_cost": {
            "path": f"{CLUSTER_PATH}/marginal-cost",
            "default_value": 0,
        },
        "fixed_cost": {
            "path": f"{CLUSTER_PATH}/fixed-cost",
            "default_value": 0,
        },
        "startup_cost": {
            "path": f"{CLUSTER_PATH}/startup-cost",
            "default_value": 0,
        },
        "market_bid_cost": {
            "path": f"{CLUSTER_PATH}/market-bid-cost",
            "default_value": 0,
        },
        "spread_cost": {
            "path": f"{CLUSTER_PATH}/spread-cost",
            "default_value": 0,
        },
        "ts_gen": {
            "path": f"{CLUSTER_PATH}/gen-ts",
            "default_value": LocalTSGenerationBehavior.USE_GLOBAL.value,
        },
        "volatility_forced": {
            "path": f"{CLUSTER_PATH}/volatility.forced",
            "default_value": 0,
        },
        "volatility_planned": {
            "path": f"{CLUSTER_PATH}/volatility.planned",
            "default_value": 0,
        },
        "law_forced": {
            "path": f"{CLUSTER_PATH}/law.forced",
            "default_value": LawOption.UNIFORM.value,
        },
        "law_planned": {
            "path": f"{CLUSTER_PATH}/law.planned",
            "default_value": LawOption.UNIFORM.value,
        },
    },
    TableTemplateType.RENEWABLE: {
        "group": {
            "path": f"{RENEWABLE_PATH}/group",
            "default_value": "",
        },
        "ts_interpretation": {
            "path": f"{RENEWABLE_PATH}/ts-interpretation",
            "default_value": TimeSeriesInterpretation.POWER_GENERATION.value,
        },
        "enabled": {
            "path": f"{RENEWABLE_PATH}/enabled",
            "default_value": True,
        },
        "unit_count": {
            "path": f"{RENEWABLE_PATH}/unitcount",
            "default_value": 0,
        },
        "nominal_capacity": {
            "path": f"{RENEWABLE_PATH}/nominalcapacity",
            "default_value": 0,
        },
    },
    TableTemplateType.BINDING_CONSTRAINT: {
        "type": {
            "path": f"{BINDING_CONSTRAINT_PATH}/type",
            "default_value": BindingConstraintFrequency.HOURLY.value,
        },
        "operator": {
            "path": f"{BINDING_CONSTRAINT_PATH}/operator",
            "default_value": BindingConstraintOperator.LESS.value,
        },
        "enabled": {
            "path": f"{BINDING_CONSTRAINT_PATH}/enabled",
            "default_value": True,
        },
        "group": {
            "path": f"{BINDING_CONSTRAINT_PATH}/group",
            "default_value": None,
        },
    },
}

COLUMNS_MODELS_BY_TYPE = {
    TableTemplateType.AREA: AreaColumns,
    TableTemplateType.LINK: LinkColumns,
    TableTemplateType.THERMAL_CLUSTER: ThermalClusterColumns,
    TableTemplateType.RENEWABLE_CLUSTER: RenewableClusterColumns,
    TableTemplateType.BINDING_CONSTRAINT: BindingConstraintColumns,
}

ColumnsModelTypes = Union[
    AreaColumns,
    LinkColumns,
    ThermalClusterColumns,
    RenewableClusterColumns,
    BindingConstraintColumns,
]


def _get_glob_object(file_study: FileStudy, table_type: TableTemplateType) -> Dict[str, Any]:
    """
    Retrieves the fields of an object according to its type (area, link, thermal cluster...).

    Args:
        file_study: A file study from which the configuration can be read.
        table_type: Type of the object.

    Returns:
        Dictionary containing the fields used in Table mode.

    Raises:
        ChildNotFoundError: if one of the Area IDs is not found in the configuration.
    """
    # sourcery skip: extract-method
    if table_type == TableTemplateType.AREA:
        info_map: Dict[str, Any] = file_study.tree.get(url=AREA_PATH.format(area="*").split("/"), depth=3)
        area_ids = list(file_study.config.areas)
        # If there is only one ID in the `area_ids`, the result returned from
        # the `file_study.tree.get` call will be a single object.
        # On the other hand, if there are multiple values in `area_ids`,
        # the result will be a dictionary where the keys are the IDs,
        # and the values are the corresponding objects.
        if len(area_ids) == 1:
            info_map = {area_ids[0]: info_map}
        # Add thermal fields in info_map
        thermal_fields = file_study.tree.get(THERMAL_PATH.split("/"))
        for field, field_props in thermal_fields.items():
            for area_id, value in field_props.items():
                if area_id in info_map:
                    info_map[area_id][field] = value
        return info_map

    if table_type == TableTemplateType.LINK:
        return file_study.tree.get(LINK_GLOB_PATH.format(area1="*").split("/"))
    if table_type == TableTemplateType.THERMAL_CLUSTER:
        return file_study.tree.get(THERMAL_CLUSTER_GLOB_PATH.format(area="*").split("/"))
    if table_type == TableTemplateType.RENEWABLE_CLUSTER:
        return file_study.tree.get(RENEWABLE_CLUSTER_GLOB_PATH.format(area="*").split("/"))
    if table_type == TableTemplateType.BINDING_CONSTRAINT:
        return file_study.tree.get(BINDING_CONSTRAINT_PATH.split("/"))

    return {}


def _get_value(path: List[str], data: Dict[str, Any], default_value: Any) -> Any:
    if len(path):
        return _get_value(path[1:], data.get(path[0], {}), default_value)
    return data if data != {} else default_value


def _get_relative_path(
    table_type: TableTemplateType,
    path: str,
) -> List[str]:
    base_path = ""
    path_arr = path.split("/")

    if table_type == TableTemplateType.AREA:
        if path.startswith(THERMAL_PATH):
            base_path = THERMAL_PATH
            # Remove {area}
            path_arr = path_arr[:-1]
        else:
            base_path = AREA_PATH
    elif table_type == TableTemplateType.LINK:
        base_path = LINK_PATH
    elif table_type == TableTemplateType.THERMAL_CLUSTER:
        base_path = THERMAL_CLUSTER_PATH
    elif table_type == TableTemplateType.RENEWABLE_CLUSTER:
        base_path = RENEWABLE_CLUSTER_PATH
    elif table_type == TableTemplateType.BINDING_CONSTRAINT:
        base_path = BINDING_CONSTRAINT_PATH

    return path_arr[len(base_path.split("/")) :]


def _get_column_path(
    table_type: TableTemplateType,
    column: str,
    path_vars: PathVars,
) -> str:
    columns_model = COLUMNS_MODELS_BY_TYPE[table_type]
    path = cast(str, columns_model.__fields__[column].field_info.extra["path"])

    if table_type == TableTemplateType.AREA:
        return path.format(area=path_vars["id"])
    if table_type == TableTemplateType.LINK:
        return path.format(area1=path_vars["area1"], area2=path_vars["area2"])
    if table_type in [
        TableTemplateType.THERMAL_CLUSTER,
        TableTemplateType.RENEWABLE_CLUSTER,
    ]:
        return path.format(area=path_vars["area"], cluster=path_vars["cluster"])

    return path


def _get_path_vars_from_key(
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
        TableTemplateType.THERMAL_CLUSTER,
        TableTemplateType.RENEWABLE_CLUSTER,
    ]:
        area, cluster = [v.strip() for v in key.split("/")]
        return PathVars(area=area, cluster=cluster)

    return PathVars()


class TableModeManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_table_data(
        self,
        study: RawStudy,
        table_type: TableTemplateType,
        columns: List[str],
    ) -> Dict[str, ColumnsModelTypes]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        columns_model = COLUMNS_MODELS_BY_TYPE[table_type]
        glob_object = _get_glob_object(file_study, table_type)
        schema_columns = columns_model.schema()["properties"]

        def get_column_value(col: str, data: Dict[str, Any]) -> Any:
            schema = schema_columns[col]
            relative_path = _get_relative_path(table_type, schema["path"])
            return _get_value(relative_path, data, schema["default"])

        if table_type == TableTemplateType.AREA:
            return {
                area_id: columns_model.construct(**{col: get_column_value(col, data) for col in columns})  # type: ignore
                for area_id, data in glob_object.items()
            }

        if table_type == TableTemplateType.BINDING_CONSTRAINT:
            return {
                data["id"]: columns_model.construct(**{col: get_column_value(col, data) for col in columns})  # type: ignore
                for data in glob_object.values()
            }

        obj: Dict[str, Any] = {}
        for id_1, value_1 in glob_object.items():
            for id_2, value_2 in value_1.items():
                obj[f"{id_1} / {id_2}"] = columns_model.construct(
                    **{col: get_column_value(col, value_2) for col in columns}
                )

        return obj

    def set_table_data(
        self,
        study: RawStudy,
        table_type: TableTemplateType,
        data: Dict[str, ColumnsModelTypes],
    ) -> None:
        commands: List[ICommand] = []
        bindings_by_id = None
        command_context = self.storage_service.variant_study_service.command_factory.command_context

        for key, columns in data.items():
            path_vars = _get_path_vars_from_key(table_type, key)

            if table_type == TableTemplateType.BINDING_CONSTRAINT:
                file_study = self.storage_service.get_storage(study).get_raw(study)
                bindings_by_id = bindings_by_id or {
                    binding["id"]: binding for binding in _get_glob_object(file_study, table_type).values()
                }
                binding_id = path_vars["id"]
                current_binding = bindings_by_id.get(binding_id, None)

                if current_binding:
                    col_values = columns.dict(exclude_none=True)
                    current_binding_dto = BindingConstraintManager.constraint_model_adapter(
                        current_binding, int(study.version)
                    )

                    commands.append(
                        UpdateBindingConstraint(
                            id=binding_id,
                            enabled=col_values.get("enabled", current_binding_dto.enabled),
                            time_step=col_values.get("type", current_binding_dto.time_step),
                            operator=col_values.get("operator", current_binding_dto.operator),
                            coeffs=BindingConstraintManager.terms_to_coeffs(current_binding_dto.terms),
                            command_context=command_context,
                        )
                    )
            else:
                for col, val in columns.__iter__():
                    if val is not None:
                        commands.append(
                            UpdateConfig(
                                target=_get_column_path(table_type, col, path_vars),
                                data=val,
                                command_context=command_context,
                            )
                        )

        if commands:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(study, file_study, commands, self.storage_service)
