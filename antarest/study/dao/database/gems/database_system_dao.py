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
from typing import Any, List

from sqlalchemy import Row, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import (
    GemsInvalidConnection,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.study.business.model.gems.system import GemsComponent, GemsComponentConnection, GemsSystem
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.library import GEMS_MODELS_PORTS_TABLE
from antarest.study.dao.database.models.gems.system import (
    GEMS_COMPONENT_CONNECTIONS_TABLE,
    GEMS_COMPONENT_PARAMETERS_TABLE,
    GEMS_COMPONENT_PROPERTIES_TABLE,
    GEMS_COMPONENTS_TABLE,
    GEMS_SYSTEM_METADATA_TABLE,
)

METADATA_TABLE = GEMS_SYSTEM_METADATA_TABLE


def _reorder_connection(connection: GemsComponentConnection) -> GemsComponentConnection:
    component_a = connection.component1 if connection.component1 < connection.component2 else connection.component2
    component_b = connection.component2 if connection.component1 < connection.component2 else connection.component1
    port_a = connection.port1 if connection.component1 < connection.component2 else connection.port2
    port_b = connection.port2 if connection.component1 < connection.component2 else connection.port1

    return GemsComponentConnection(
        component1=component_a,
        port1=port_a,
        component2=component_b,
        port2=port_b,
    )


def _check_no_duplicated_connections(connections: list[GemsComponentConnection]) -> None:
    seen: set[GemsComponentConnection] = set()
    for connection in connections:
        ordered_connection = _reorder_connection(connection)
        if ordered_connection in seen:
            raise GemsInvalidConnection(
                f"Connection between '{ordered_connection.component1}.{ordered_connection.port1}' and "
                f"'{ordered_connection.component2}.{ordered_connection.port2}' is declared more than once"
            )
        seen.add(ordered_connection)


class DatabaseGemsSystemDao(GemsSystemDao, DatabaseDaoBase):
    """Database implementation of GemsSystemDao"""

    @override
    def get_system(self) -> GemsSystem | None:
        # System metadata
        metadata_row = self._get_system_row_if_exists()
        if not metadata_row:
            # No system found, as it is not mandatory to have one, we simply return None.
            return None

        components = self.get_components()
        connections = self._get_connections()

        return GemsSystem.model_validate(
            {
                "id": metadata_row.system_id,
                "description": metadata_row.description,
                "components": components,
                "connections": connections,
            }
        )

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

    def _get_connections(self) -> List[GemsComponentConnection]:
        study_data_id = self._study_data_id
        session = self._db_session

        connections_stmt = select(GEMS_COMPONENT_CONNECTIONS_TABLE).where(
            GEMS_COMPONENT_CONNECTIONS_TABLE.c.study_data_id == study_data_id
        )
        connections_rows = session.execute(connections_stmt).fetchall()
        connections: List[GemsComponentConnection] = []
        for connection_row in connections_rows:
            connections.append(
                GemsComponentConnection(
                    component1=connection_row.component1,
                    component2=connection_row.component2,
                    port1=connection_row.port1,
                    port2=connection_row.port2,
                )
            )
        return connections

    @override
    def save_system(self, system: GemsSystem) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        row = self._get_system_row_if_exists()
        if row:
            raise GemsSystemAlreadyExists(f"A system file already exists for study {self._study_id}")

        metadata_values = {
            "study_data_id": study_data_id,
            "system_id": system.id,
            "description": system.description,
        }

        session.execute(insert(GEMS_SYSTEM_METADATA_TABLE), metadata_values)

        try:
            self.save_components(system.components)
            self._save_connections(system.connections)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    @override
    def save_components(self, components: List[GemsComponent]) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {study_data_id}")

        # Clean all existing data regarding components
        session.execute(delete(GEMS_COMPONENTS_TABLE).where(GEMS_COMPONENTS_TABLE.c.study_data_id == study_data_id))

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

    def _get_components_library_and_model(self) -> dict[str, tuple[str, str]]:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(
            GEMS_COMPONENTS_TABLE.c.component_id, GEMS_COMPONENTS_TABLE.c.library_id, GEMS_COMPONENTS_TABLE.c.model_id
        ).where(GEMS_COMPONENTS_TABLE.c.study_data_id == study_data_id)
        return {row.component_id: (row.library_id, row.model_id) for row in session.execute(stmt).fetchall()}

    def _raise_the_right_connection_exception(
        self, connections: List[GemsComponentConnection], exc: IntegrityError
    ) -> None:

        self._check_connection_does_not_link_port_component_to_itself(connections, exc)

        components_library_and_model = self._get_components_library_and_model()
        self._check_components_exist(components_library_and_model, connections, exc)
        self._check_ports_exist_in_models(components_library_and_model, connections, exc)

        # All components and ports exist and no self-connection was found.
        # It means the DB table is not filled as it should.
        raise ValueError("The connections table is not filled as it should") from exc

    def _check_ports_exist_in_models(
        self,
        components_library_and_model: dict[str, tuple[str, str]],
        connections: list[GemsComponentConnection],
        exc: IntegrityError,
    ) -> None:
        session = self._db_session
        study_data_id = self._study_data_id

        valid_ports_stmt = select(
            GEMS_MODELS_PORTS_TABLE.c.library_id, GEMS_MODELS_PORTS_TABLE.c.model_id, GEMS_MODELS_PORTS_TABLE.c.port_id
        ).where(GEMS_MODELS_PORTS_TABLE.c.study_data_id == study_data_id)
        valid_ports = {
            (row.library_id, row.model_id, row.port_id) for row in session.execute(valid_ports_stmt).fetchall()
        }

        for connection in connections:
            for component_id, port_id in (
                (connection.component1, connection.port1),
                (connection.component2, connection.port2),
            ):
                library_id, model_id = components_library_and_model[component_id]
                if (library_id, model_id, port_id) not in valid_ports:
                    raise GemsInvalidConnection(
                        f"Component '{component_id}' does not have a port named '{port_id}'"
                    ) from exc

    def _check_components_exist(
        self,
        components_library_and_model: dict[str, tuple[str, str]],
        connections: list[GemsComponentConnection],
        exc: IntegrityError,
    ) -> None:
        referenced_component_ids = {
            c for connection in connections for c in (connection.component1, connection.component2)
        }
        if invalid_component_ids := referenced_component_ids - components_library_and_model.keys():
            raise GemsInvalidConnection(
                f"Connection(s) reference non-existing component(s): {sorted(invalid_component_ids)}"
            ) from exc

    def _check_connection_does_not_link_port_component_to_itself(
        self, connections: list[GemsComponentConnection], exc: IntegrityError
    ) -> None:
        for connection in connections:
            if connection.component1 == connection.component2 and connection.port1 == connection.port2:
                raise GemsInvalidConnection(
                    f"A connection cannot link the port '{connection.port1}' of component '{connection.component1}' to itself"
                ) from exc

    def _save_connections(self, connections: List[GemsComponentConnection] | None) -> None:

        if not connections:
            return

        # GEMS tolerates exact duplicates (same component1/component2/port1/port2) inside a system.yml file,
        # so we silently remove them to keep the primary in the gems_component_connections table.
        _check_no_duplicated_connections(connections)

        study_data_id = self._study_data_id
        session = self._db_session

        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {study_data_id}")

        # Clean all existing data regarding connections
        session.execute(
            delete(GEMS_COMPONENT_CONNECTIONS_TABLE).where(
                GEMS_COMPONENT_CONNECTIONS_TABLE.c.study_data_id == study_data_id
            )
        )

        if connections:
            # `library_idX`/`model_idX` are denormalized from `gems_components` so that the port foreign keys
            # can check that `portX` truly belongs to the model of `componentX` (see the connections table
            # definition). Unknown components fall back to an empty string, which cannot match any real
            # component and therefore still triggers a foreign key violation, correctly reported below.
            components_library_and_model = self._get_components_library_and_model()

            if missing := sorted(
                {
                    connected_component
                    for conn in connections
                    for connected_component in (conn.component1, conn.component2)
                }
                - components_library_and_model.keys()
            ):
                raise GemsInvalidConnection(f"Connection(s) reference non-existing component(s): {missing}")

            rows = []
            for connection in connections:
                library_id1, model_id1 = components_library_and_model[connection.component1]
                library_id2, model_id2 = components_library_and_model[connection.component2]
                rows.append(
                    {
                        "study_data_id": study_data_id,
                        "component1": connection.component1,
                        "component2": connection.component2,
                        "port1": connection.port1,
                        "port2": connection.port2,
                        "library_id1": library_id1,
                        "model_id1": model_id1,
                        "library_id2": library_id2,
                        "model_id2": model_id2,
                    }
                )

            try:
                session.execute(insert(GEMS_COMPONENT_CONNECTIONS_TABLE), rows)
            except IntegrityError as e:
                self._raise_the_right_connection_exception(connections, e)
                session.rollback()
