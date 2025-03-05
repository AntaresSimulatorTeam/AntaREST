# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import collections
from typing import Any, Mapping, MutableMapping, Optional, Sequence, cast

import numpy as np
import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.study.business.area_management import AreaManager
from antarest.study.business.areas.renewable_management import RenewableManager
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.business.areas.thermal_management import ThermalManager
from antarest.study.business.binding_constraint_management import BindingConstraintManager, ConstraintInput
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.link_management import LinkManager
from antarest.study.business.model.area_model import AreaOutput
from antarest.study.business.model.link_model import LinkBaseDTO
from antarest.study.business.model.renewable_cluster_model import RenewableClusterUpdate
from antarest.study.business.model.sts_model import STStorageUpdate
from antarest.study.business.model.thermal_cluster_model import ThermalClusterUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_2

_TableIndex = str  # row name
_TableColumn = str  # column name
_CellValue = Any  # cell value (str, int, float, bool, enum, etc.)
TableDataDTO = Mapping[_TableIndex, Mapping[_TableColumn, _CellValue]]


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

    @classmethod
    @override
    def _missing_(cls, value: object) -> Optional["EnumIgnoreCase"]:
        if isinstance(value, str):
            # handle aliases of old table types
            value = value.upper()
            aliases = {
                "AREA": cls.AREA,
                "LINK": cls.LINK,
                "CLUSTER": cls.THERMAL,
                "RENEWABLE": cls.RENEWABLE,
                "BINDING CONSTRAINT": cls.BINDING_CONSTRAINT,
            }
            if value in aliases:
                return aliases[value]
        return super()._missing_(value)


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

    def _get_table_data_unsafe(self, study: StudyInterface, table_type: TableModeType) -> TableDataDTO:
        if table_type == TableModeType.AREA:
            areas_map = self._area_manager.get_all_area_props(study)
            data = {area_id: area.model_dump(mode="json", by_alias=True) for area_id, area in areas_map.items()}
        elif table_type == TableModeType.LINK:
            links_map = self._link_manager.get_all_links(study)
            excludes = set() if study.version >= STUDY_VERSION_8_2 else {"filter_synthesis", "filter_year_by_year"}
            data = {
                f"{link.area1} / {link.area2}": link.model_dump(mode="json", by_alias=True, exclude=excludes)
                for link in links_map
            }
        elif table_type == TableModeType.THERMAL:
            thermals_by_areas = self._thermal_manager.get_all_thermals_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, thermals_by_ids in thermals_by_areas.items()
                for cluster_id, cluster in thermals_by_ids.items()
            }
        elif table_type == TableModeType.RENEWABLE:
            renewables_by_areas = self._renewable_manager.get_all_renewables_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, renewables_by_ids in renewables_by_areas.items()
                for cluster_id, cluster in renewables_by_ids.items()
            }
        elif table_type == TableModeType.ST_STORAGE:
            storages_by_areas = self._st_storage_manager.get_all_storages_props(study)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, storages_by_ids in storages_by_areas.items()
                for cluster_id, cluster in storages_by_ids.items()
            }
        elif table_type == TableModeType.BINDING_CONSTRAINT:
            bc_seq = self._binding_constraint_manager.get_binding_constraints(study)
            data = {bc.id: bc.model_dump(by_alias=True, exclude={"id", "name", "terms"}) for bc in bc_seq}
        else:  # pragma: no cover
            raise NotImplementedError(f"Table type {table_type} not implemented")
        return data

    def get_table_data(
        self,
        study: StudyInterface,
        table_type: TableModeType,
        columns: Sequence[_TableColumn],
    ) -> TableDataDTO:
        """
        Get the table data of the specified type for the given study.

        Args:
            study: The study to get the table data from.
            table_type: The type of the table.
            columns: The columns to include in the table. If empty, all columns are included.

        Returns:
            The table data as a dictionary of dictionaries.
            Where keys are the row names and values are dictionaries of column names and cell values.
        """
        try:
            data = self._get_table_data_unsafe(study, table_type)
        except ChildNotFoundError:
            # It's better to return an empty table than raising an 404 error
            return {}

        df = pd.DataFrame.from_dict(data, orient="index")  # type: ignore
        if columns:
            # Create a new dataframe with the listed columns.
            df = pd.DataFrame(df, columns=columns)  # type: ignore

        # According to the study version, some properties may not be present,
        # so we need to drop columns that are all NaN.
        df = df.dropna(axis=1, how="all")

        # Convert NaN to `None` because it is not JSON-serializable
        df.replace(np.nan, None, inplace=True)

        return cast(TableDataDTO, df.to_dict(orient="index"))

    def update_table_data(
        self,
        study: StudyInterface,
        table_type: TableModeType,
        data: TableDataDTO,
    ) -> TableDataDTO:
        """
        Update the properties of the objects in the study using the provided data.

        Args:
            study: The study to update the objects in.
            table_type: The type of the table.
            data: The new properties of the objects as a dictionary of dictionaries.
                Where keys are the row names and values are dictionaries of column names and cell values.

        Returns:
            The updated properties of the objects including the old ones.
        """
        if table_type == TableModeType.AREA:
            # Use AreaOutput to update properties of areas, which may include `None` values
            area_props_by_ids = {key: AreaOutput(**values) for key, values in data.items()}
            areas_map = self._area_manager.update_areas_props(study, area_props_by_ids)
            data = {area_id: area.model_dump(by_alias=True, exclude_none=True) for area_id, area in areas_map.items()}
            return data
        elif table_type == TableModeType.LINK:
            links_map = {tuple(key.split(" / ")): LinkBaseDTO(**values) for key, values in data.items()}
            updated_map = self._link_manager.update_links(study, links_map)  # type: ignore
            excludes = set() if study.version >= STUDY_VERSION_8_2 else {"filter_synthesis", "filter_year_by_year"}
            data = {
                f"{area1_id} / {area2_id}": link.model_dump(by_alias=True, exclude=excludes)
                for (area1_id, area2_id), link in updated_map.items()
            }
            return data
        elif table_type == TableModeType.THERMAL:
            thermals_by_areas: MutableMapping[str, MutableMapping[str, ThermalClusterUpdate]]
            thermals_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                thermals_by_areas[area_id][cluster_id] = ThermalClusterUpdate(**values)
            thermals_map = self._thermal_manager.update_thermals_props(study, thermals_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, thermals_by_ids in thermals_map.items()
                for cluster_id, cluster in thermals_by_ids.items()
            }
            return data
        elif table_type == TableModeType.RENEWABLE:
            renewables_by_areas: MutableMapping[str, MutableMapping[str, RenewableClusterUpdate]]
            renewables_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                renewables_by_areas[area_id][cluster_id] = RenewableClusterUpdate(**values)
            renewables_map = self._renewable_manager.update_renewables_props(study, renewables_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, renewables_by_ids in renewables_map.items()
                for cluster_id, cluster in renewables_by_ids.items()
            }
            return data
        elif table_type == TableModeType.ST_STORAGE:
            storages_by_areas: MutableMapping[str, MutableMapping[str, STStorageUpdate]]
            storages_by_areas = collections.defaultdict(dict)
            for key, values in data.items():
                area_id, cluster_id = key.split(" / ")
                storages_by_areas[area_id][cluster_id] = STStorageUpdate(**values)
            storages_map = self._st_storage_manager.update_storages_props(study, storages_by_areas)
            data = {
                f"{area_id} / {cluster_id}": cluster.model_dump(by_alias=True, exclude={"id", "name"})
                for area_id, storages_by_ids in storages_map.items()
                for cluster_id, cluster in storages_by_ids.items()
            }
            return data
        elif table_type == TableModeType.BINDING_CONSTRAINT:
            bcs_by_ids = {key: ConstraintInput(**values) for key, values in data.items()}
            bcs_map = self._binding_constraint_manager.update_binding_constraints(study, bcs_by_ids)
            return {
                bc_id: bc.model_dump(by_alias=True, exclude={"id", "name", "terms"}) for bc_id, bc in bcs_map.items()
            }
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
