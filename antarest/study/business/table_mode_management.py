import collections
import typing as t

import pandas as pd

from antarest.core.model import JSON
from antarest.study.business.area_management import AreaManager, AreaOutput
from antarest.study.business.areas.renewable_management import RenewableClusterInput, RenewableManager
from antarest.study.business.areas.st_storage_management import STStorageInput, STStorageManager
from antarest.study.business.areas.thermal_management import ThermalClusterInput, ThermalManager
from antarest.study.business.binding_constraint_management import BindingConstraintManager, ConstraintInput
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.link_management import LinkManager, LinkOutput
from antarest.study.model import RawStudy

_TableIndex = str  # row name
_TableColumn = str  # column name
_CellValue = t.Any  # cell value (str, int, float, bool, enum, etc.)
TableDataDTO = t.Mapping[_TableIndex, t.Mapping[_TableColumn, _CellValue]]


class TableModeType(EnumIgnoreCase):
    """
    Table types.

    This enum is used to define the different types of tables that can be created
    by the user to leverage the editing capabilities of multiple objects at once.

    Attributes:
        AREA: Area table.
        LINK: Link table.
        THERMAL: Thermal clusters table.
        RENEWABLE: Renewable clusters table.
        ST_STORAGE: Short-Term Storages table.
        BINDING_CONSTRAINT: Binding constraints table.
    """

    AREA = "areas"
    LINK = "links"
    THERMAL = "thermals"
    RENEWABLE = "renewables"
    # Avoid "storages" because we may have "lt-storages" (long-term storages) in the future
    ST_STORAGE = "st-storages"
    # Avoid "constraints" because we may have other kinds of constraints in the future
    BINDING_CONSTRAINT = "binding-constraints"


class TableModeManager:
    def __init__(
        self,
        area_manager: AreaManager,
        link_manager: LinkManager,
        thermal_manager: ThermalManager,
        renewable_manager: RenewableManager,
        st_storage_manager: STStorageManager,
        binding_constraint_manager: BindingConstraintManager,
    ) -> None:
        self._area_manager = area_manager
        self._link_manager = link_manager
        self._thermal_manager = thermal_manager
        self._renewable_manager = renewable_manager
        self._st_storage_manager = st_storage_manager
        self._binding_constraint_manager = binding_constraint_manager

    def get_table_data(
        self,
        study: RawStudy,
        table_type: TableModeType,
        columns: t.Sequence[_TableColumn],
    ) -> TableDataDTO:
        if table_type == TableModeType.AREA:
            areas_map = self._area_manager.get_all_area_props(study)
            data = {area_id: area.dict(by_alias=True) for area_id, area in areas_map.items()}
        elif table_type == TableModeType.LINK:
            links_map = self._link_manager.get_all_links_props(study)
            data = {
                f"{area1_id} / {area2_id}": link.dict(by_alias=True) for (area1_id, area2_id), link in links_map.items()
            }
        elif table_type == TableModeType.THERMAL:
            thermals_by_areas = self._thermal_manager.get_all_thermals_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, thermals_by_ids in thermals_by_areas.items()
                for cluster_id, cluster in thermals_by_ids.items()
            }
        elif table_type == TableModeType.RENEWABLE:
            renewables_by_areas = self._renewable_manager.get_all_renewables_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, renewables_by_ids in renewables_by_areas.items()
                for cluster_id, cluster in renewables_by_ids.items()
            }
        elif table_type == TableModeType.ST_STORAGE:
            storages_by_areas = self._st_storage_manager.get_all_storages_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, storages_by_ids in storages_by_areas.items()
                for cluster_id, cluster in storages_by_ids.items()
            }
        elif table_type == TableModeType.BINDING_CONSTRAINT:
            bc_seq = self._binding_constraint_manager.get_binding_constraints(study)
            data = {bc.id: bc.dict(by_alias=True, exclude={"id", "name", "terms"}) for bc in bc_seq}
        else:  # pragma: no cover
            raise NotImplementedError(f"Table type {table_type} not implemented")

        df = pd.DataFrame.from_dict(data, orient="index")
        if columns:
            # Create a new dataframe with the listed columns.
            # If a column does not exist in the DataFrame, it is created with empty values.
            df = pd.DataFrame(df, columns=columns)  # type: ignore
            # noinspection PyTypeChecker
            df = df.where(pd.notna(df), other=None)  #

        obj = df.to_dict(orient="index")

        # Convert NaN to `None` because it is not JSON-serializable
        for row in obj.values():
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None

        return t.cast(TableDataDTO, obj)

        file_study = self.storage_service.get_storage(study).get_raw(study)
        columns_model = COLUMNS_MODELS_BY_TYPE[table_type]
        glob_object = _get_glob_object(file_study, table_type)
        schema_columns = columns_model.schema()["properties"]

        def get_column_value(col: str, data: t.Dict[str, t.Any]) -> t.Any:
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

        obj: t.Dict[str, t.Any] = {}
        for id_1, value_1 in glob_object.items():
            for id_2, value_2 in value_1.items():
                obj[f"{id_1} / {id_2}"] = columns_model.construct(
                    **{col: get_column_value(col, value_2) for col in columns}
                )

        return obj

    def update_table_data(
        self,
        study: RawStudy,
        table_type: TableModeType,
        data: TableDataDTO,
    ) -> TableDataDTO:
        if table_type == TableModeType.AREA:
            # Use AreaOutput to update properties of areas
            area_props_by_ids = {key: AreaOutput(**values) for key, values in data.items()}
            areas_map = self._area_manager.update_areas_props(study, area_props_by_ids)
            data = {area_id: area.dict(by_alias=True) for area_id, area in areas_map.items()}
            return data
        elif table_type == TableModeType.LINK:
            links_map = {tuple(key.split(" / ")): LinkOutput(**values) for key, values in data.items()}
            updated_map = self._link_manager.update_links_props(study, links_map)  # type: ignore
            data = {
                f"{area1_id} / {area2_id}": link.dict(by_alias=True)
                for (area1_id, area2_id), link in updated_map.items()
            }
            return data
        elif table_type == TableModeType.THERMAL:
            thermals_by_areas: t.MutableMapping[str, t.MutableMapping[str, ThermalClusterInput]]
            thermals_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                thermals_by_areas[area_id][cluster_id] = ThermalClusterInput(**values)
            thermals_map = self._thermal_manager.update_thermals_props(study, thermals_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, thermals_by_ids in thermals_map.items()
                for cluster_id, cluster in thermals_by_ids.items()
            }
            return data
        elif table_type == TableModeType.RENEWABLE:
            renewables_by_areas: t.MutableMapping[str, t.MutableMapping[str, RenewableClusterInput]]
            renewables_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                renewables_by_areas[area_id][cluster_id] = RenewableClusterInput(**values)
            renewables_map = self._renewable_manager.update_renewables_props(study, renewables_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, renewables_by_ids in renewables_map.items()
                for cluster_id, cluster in renewables_by_ids.items()
            }
            return data
        elif table_type == TableModeType.ST_STORAGE:
            storages_by_areas: t.MutableMapping[str, t.MutableMapping[str, STStorageInput]]
            storages_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                storages_by_areas[area_id][cluster_id] = STStorageInput(**values)
            storages_map = self._st_storage_manager.update_storages_props(study, storages_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.dict(by_alias=True, exclude={"id", "name"})
                for area_id, storages_by_ids in storages_map.items()
                for cluster_id, cluster in storages_by_ids.items()
            }
            return data
        elif table_type == TableModeType.BINDING_CONSTRAINT:
            bcs_by_ids = {key: ConstraintInput(**values) for key, values in data.items()}
            bcs_map = self._binding_constraint_manager.update_binding_constraints(study, bcs_by_ids)
            return {bc_id: bc.dict(by_alias=True, exclude={"id", "name", "terms"}) for bc_id, bc in bcs_map.items()}
        else:  # pragma: no cover
            raise NotImplementedError(f"Table type {table_type} not implemented")

    def get_table_schema(self, table_type: TableModeType) -> JSON:
        """
        Get the properties of the table columns which type is provided as a parameter.

        Args:
            table_type: The type of the table.

        Returns:
            JSON Schema which allows to know the name, title and type of each column.
        """
        if table_type == TableModeType.AREA:
            return self._area_manager.get_table_schema()
        elif table_type == TableModeType.LINK:
            return self._link_manager.get_table_schema()
        elif table_type == TableModeType.THERMAL:
            return self._thermal_manager.get_table_schema()
        elif table_type == TableModeType.RENEWABLE:
            return self._renewable_manager.get_table_schema()
        elif table_type == TableModeType.ST_STORAGE:
            return self._st_storage_manager.get_table_schema()
        elif table_type == TableModeType.BINDING_CONSTRAINT:
            return self._binding_constraint_manager.get_table_schema()
        else:  # pragma: no cover
            raise NotImplementedError(f"Table type {table_type} not implemented")
