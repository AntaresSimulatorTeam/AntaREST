# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Any, List, Sequence

from sqlalchemy import Row, delete, insert, select
from typing_extensions import override

from antarest.core.exceptions import (
    GemsInvalidConnection,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.study.business.model.gems.system import (
    GemsAreaConnection,
    GemsComponent,
    GemsSystem,
    GemsThermalCapacityConnection,
    check_legacy_connections,
)
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.library import GEMS_MODELS_PORTS_TABLE
from antarest.study.dao.database.models.gems.system import (
    GEMS_AREA_CONNECTIONS_TABLE,
    GEMS_COMPONENT_PARAMETERS_TABLE,
    GEMS_COMPONENT_PROPERTIES_TABLE,
    GEMS_COMPONENTS_TABLE,
    GEMS_SYSTEM_METADATA_TABLE,
    GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE,
)
from antarest.study.dao.database.models.thermal import THERMAL_CLUSTER_TABLE

METADATA_TABLE = GEMS_SYSTEM_METADATA_TABLE

# Maps a component id to the `(library_id, model_id)` of its model
ComponentModels = dict[str, tuple[str, str]]


def _get_component_models(components: List[GemsComponent]) -> ComponentModels:
    component_models: ComponentModels = {}
    for component in components:
        library_id, model_id = component.model.split(".", 1)
        component_models[component.id] = (library_id, model_id)
    return component_models


class DatabaseGemsSystemDao(GemsSystemDao, DatabaseDaoBase):
    """Database implementation of GemsSystemDao"""

    @override
    def get_system(self) -> GemsSystem | None:
        # System metadata
        metadata_row = self._get_system_row_if_exists()
        if not metadata_row:
            # No system found, as it is not mandatory to have one, we simply return None.
            return None

        system: dict[str, Any] = {
            "id": metadata_row.system_id,
            "description": metadata_row.description,
            "components": self.get_components(),
        }
        # Empty sections are left unset, as they are in a system file without these sections
        if area_connections := self._get_area_connections():
            system["area_connections"] = area_connections
        if thermal_capacity_connections := self._get_thermal_capacity_connections():
            system["thermal_capacity_connections"] = thermal_capacity_connections

        return GemsSystem.model_validate(system)

    def _get_system_row_if_exists(self) -> Row[tuple[Any]] | None:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(GEMS_SYSTEM_METADATA_TABLE).where(GEMS_SYSTEM_METADATA_TABLE.c.study_data_id == study_data_id)

        metadata_row = session.execute(stmt).fetchone()
        return metadata_row

    @override
    def get_components(self) -> List[GemsComponent]:
        study_data_id = self._study_data_id
        session = self._db_session

        component_parameters = self._get_components_parameters()
        component_properties = self._get_components_properties()

        components_stmt = select(GEMS_COMPONENTS_TABLE).where(GEMS_COMPONENTS_TABLE.c.study_data_id == study_data_id)
        all_components_rows = session.execute(components_stmt).fetchall()

        if not all_components_rows:
            return []

        components = []
        for component_row in all_components_rows:
            model = f"{component_row.library_id}.{component_row.model_id}"
            current_component = GemsComponent.model_validate(
                {
                    "id": component_row.component_id,
                    "model": model,
                    "scenario_group": component_row.scenario_group if component_row.scenario_group else None,
                    "parameters": component_parameters.get(component_row.component_id),
                    "properties": component_properties.get(component_row.component_id),
                }
            )

            components.append(current_component)

        return components

    def _get_components_parameters(self) -> dict[str, list[dict[str, Any]]]:
        study_data_id = self._study_data_id
        session = self._db_session

        parameters_stmt = select(GEMS_COMPONENT_PARAMETERS_TABLE).where(
            GEMS_COMPONENT_PARAMETERS_TABLE.c.study_data_id == study_data_id
        )
        parameters_rows = session.execute(parameters_stmt).fetchall()
        component_parameters: dict[str, list[dict[str, Any]]] = {}
        for parameter_row in parameters_rows:
            component_parameters.setdefault(parameter_row.component_id, []).append(
                {
                    "id": parameter_row.parameter_id,
                    "time-dependent": parameter_row.time_dependent,
                    "scenario-dependent": parameter_row.scenario_dependent,
                    "value": parameter_row.value,
                }
            )
        return component_parameters

    def _get_components_properties(self) -> dict[str, list[dict[str, Any]]]:
        study_data_id = self._study_data_id
        session = self._db_session

        properties_stmt = select(GEMS_COMPONENT_PROPERTIES_TABLE).where(
            GEMS_COMPONENT_PROPERTIES_TABLE.c.study_data_id == study_data_id
        )
        properties_rows = session.execute(properties_stmt).fetchall()
        component_properties: dict[str, list[dict[str, Any]]] = {}
        for property_row in properties_rows:
            component_properties.setdefault(property_row.component_id, []).append(
                {
                    "id": property_row.property_id,
                    "value": property_row.value,
                }
            )
        return component_properties

    def _get_area_connections(self) -> List[GemsAreaConnection]:
        table = GEMS_AREA_CONNECTIONS_TABLE
        stmt = (
            select(table.c.component_id, table.c.port_id, table.c.area_id)
            .where(table.c.study_data_id == self._study_data_id)
            .order_by(table.c.component_id, table.c.port_id)
        )
        return [
            GemsAreaConnection.model_validate({"component": row.component_id, "port": row.port_id, "area": row.area_id})
            for row in self._db_session.execute(stmt)
        ]

    def _get_thermal_capacity_connections(self) -> List[GemsThermalCapacityConnection]:
        table = GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE
        stmt = (
            select(table.c.component_id, table.c.port_id, table.c.area_id, table.c.cluster_id)
            .where(table.c.study_data_id == self._study_data_id)
            .order_by(table.c.component_id, table.c.port_id)
        )
        return [
            GemsThermalCapacityConnection.model_validate(
                {
                    "component": row.component_id,
                    "port": row.port_id,
                    "thermal_component": {"area": row.area_id, "cluster_id": row.cluster_id},
                }
            )
            for row in self._db_session.execute(stmt)
        ]

    @override
    def save_system(self, system: GemsSystem) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        row = self._get_system_row_if_exists()
        if row:
            raise GemsSystemAlreadyExists(f"A system file already exists for study {self._study_id}")

        component_models = _get_component_models(system.components)
        # Checked before writing anything, so that an invalid system leaves the study untouched
        self._check_area_connections(system.area_connections or [], component_models)
        self._check_thermal_capacity_connections(system.thermal_capacity_connections or [], component_models)

        metadata_values = {
            "study_data_id": study_data_id,
            "system_id": system.id,
            "description": system.description,
        }

        session.execute(insert(GEMS_SYSTEM_METADATA_TABLE), metadata_values)
        self._insert_components(system.components)
        self._insert_area_connections(system.area_connections or [])
        self._insert_thermal_capacity_connections(system.thermal_capacity_connections or [])

        session.commit()

    @override
    def save_components(self, components: List[GemsComponent]) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {study_data_id}")

        # Deleting the components cascades to their connections: keep them to restore them afterwards
        area_connections = self._get_area_connections()
        thermal_capacity_connections = self._get_thermal_capacity_connections()

        # Clean all existing data regarding components
        session.execute(delete(GEMS_COMPONENTS_TABLE).where(GEMS_COMPONENTS_TABLE.c.study_data_id == study_data_id))
        self._insert_components(components)

        # Connections of removed components, or of ports that no longer exist in their new model, are dropped
        component_models = _get_component_models(components)
        valid_ports = self._get_valid_ports()

        def is_still_valid(connection: GemsAreaConnection | GemsThermalCapacityConnection) -> bool:
            component_model = component_models.get(connection.component)
            return component_model is not None and (*component_model, connection.port) in valid_ports

        self._insert_area_connections([c for c in area_connections if is_still_valid(c)])
        self._insert_thermal_capacity_connections([c for c in thermal_capacity_connections if is_still_valid(c)])

        session.commit()

    @override
    def save_area_connections(self, connections: List[GemsAreaConnection]) -> None:
        component_models = self._get_saved_component_models()
        check_legacy_connections("area-connections", connections, set(component_models))
        self._check_area_connections(connections, component_models)

        table = GEMS_AREA_CONNECTIONS_TABLE
        self._db_session.execute(delete(table).where(table.c.study_data_id == self._study_data_id))
        self._insert_area_connections(connections)
        self._db_session.commit()

    @override
    def save_thermal_capacity_connections(self, connections: List[GemsThermalCapacityConnection]) -> None:
        component_models = self._get_saved_component_models()
        check_legacy_connections("thermal-capacity-connections", connections, set(component_models))
        self._check_thermal_capacity_connections(connections, component_models)

        table = GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE
        self._db_session.execute(delete(table).where(table.c.study_data_id == self._study_data_id))
        self._insert_thermal_capacity_connections(connections)
        self._db_session.commit()

    def _get_saved_component_models(self) -> ComponentModels:
        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {self._study_data_id}")

        table = GEMS_COMPONENTS_TABLE
        stmt = select(table.c.component_id, table.c.library_id, table.c.model_id).where(
            table.c.study_data_id == self._study_data_id
        )
        return {row.component_id: (row.library_id, row.model_id) for row in self._db_session.execute(stmt)}

    def _insert_components(self, components: List[GemsComponent]) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        component_values = []
        parameter_values = []
        property_values = []
        for component in components:
            library_id, model_id = component.model.split(".", 1)

            component_values.append(
                {
                    "study_data_id": study_data_id,
                    "library_id": library_id,
                    "component_id": component.id,
                    "model_id": model_id,
                    "scenario_group": component.scenario_group,
                }
            )

            for parameter in component.parameters or []:
                parameter_values.append(
                    {
                        "study_data_id": study_data_id,
                        "component_id": component.id,
                        "parameter_id": parameter.id,
                        "time_dependent": parameter.time_dependent,
                        "scenario_dependent": parameter.scenario_dependent,
                        "value": parameter.value,
                    }
                )

            for prop in component.properties or []:
                property_values.append(
                    {
                        "study_data_id": study_data_id,
                        "component_id": component.id,
                        "property_id": prop.id,
                        "value": prop.value,
                    }
                )

        if component_values:
            session.execute(insert(GEMS_COMPONENTS_TABLE), component_values)
        if parameter_values:
            session.execute(insert(GEMS_COMPONENT_PARAMETERS_TABLE), parameter_values)
        if property_values:
            session.execute(insert(GEMS_COMPONENT_PROPERTIES_TABLE), property_values)

    def _insert_area_connections(self, connections: List[GemsAreaConnection]) -> None:
        if not connections:
            return

        values = []
        for connection in connections:
            values.append(
                {
                    "study_data_id": self._study_data_id,
                    "component_id": connection.component,
                    "port_id": connection.port,
                    "area_id": connection.area,
                }
            )
        self._db_session.execute(insert(GEMS_AREA_CONNECTIONS_TABLE), values)

    def _insert_thermal_capacity_connections(self, connections: List[GemsThermalCapacityConnection]) -> None:
        if not connections:
            return

        values = []
        for connection in connections:
            values.append(
                {
                    "study_data_id": self._study_data_id,
                    "component_id": connection.component,
                    "port_id": connection.port,
                    "area_id": connection.thermal_component.area,
                    "cluster_id": connection.thermal_component.cluster_id,
                }
            )
        self._db_session.execute(insert(GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE), values)

    def _get_valid_ports(self) -> set[tuple[str, str, str]]:
        table = GEMS_MODELS_PORTS_TABLE
        stmt = select(table.c.library_id, table.c.model_id, table.c.port_id).where(
            table.c.study_data_id == self._study_data_id
        )
        return {(row.library_id, row.model_id, row.port_id) for row in self._db_session.execute(stmt)}

    def _check_ports(
        self,
        connections: Sequence[GemsAreaConnection | GemsThermalCapacityConnection],
        component_models: ComponentModels,
    ) -> None:
        valid_ports = self._get_valid_ports()
        for connection in connections:
            if (*component_models[connection.component], connection.port) not in valid_ports:
                raise GemsInvalidConnection(
                    f"Component '{connection.component}' does not have a port named '{connection.port}'"
                )

    def _check_area_connections(self, connections: List[GemsAreaConnection], component_models: ComponentModels) -> None:
        """
        Checks the references of the connections to the library and to the legacy areas.
        The references to the components must already be checked.
        """
        if not connections:
            return

        self._check_ports(connections, component_models)

        area_ids = set(self.get_impl().get_all_area_ids())
        for connection in connections:
            if connection.area not in area_ids:
                raise GemsInvalidConnection(
                    f"Component '{connection.component}' is connected to a non-existing area '{connection.area}'"
                )

    def _check_thermal_capacity_connections(
        self, connections: List[GemsThermalCapacityConnection], component_models: ComponentModels
    ) -> None:
        """
        Checks the references of the connections to the library and to the legacy thermal clusters.
        The references to the components must already be checked.
        """
        if not connections:
            return

        self._check_ports(connections, component_models)

        table = THERMAL_CLUSTER_TABLE
        stmt = select(table.c.area_id, table.c.thermal_id).where(table.c.study_data_id == self._study_data_id)
        cluster_ids = {(row.area_id, row.thermal_id) for row in self._db_session.execute(stmt)}
        for connection in connections:
            thermal = connection.thermal_component
            if (thermal.area, thermal.cluster_id) not in cluster_ids:
                raise GemsInvalidConnection(
                    f"Component '{connection.component}' is connected to a non-existing thermal cluster"
                    f" '{thermal.cluster_id}' in area '{thermal.area}'"
                )
