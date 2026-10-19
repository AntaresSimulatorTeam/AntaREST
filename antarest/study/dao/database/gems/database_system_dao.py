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
from typing import Any, List, NoReturn, Sequence

from sqlalchemy import Row, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import (
    GemsInvalidComponents,
    GemsInvalidConnection,
    GemsInvalidParameterValue,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.study.business.model.gems.system import (
    GemsAreaConnection,
    GemsComponent,
    GemsComponentConnection,
    GemsSystem,
    GemsThermalCapacityConnection,
    _GemsParameters,
)
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.data_series import GEMS_DATA_SERIES_TABLE
from antarest.study.dao.database.models.gems.library import GEMS_MODELS_PORTS_TABLE
from antarest.study.dao.database.models.gems.system import (
    GEMS_AREA_CONNECTIONS_TABLE,
    GEMS_COMPONENT_CONNECTIONS_TABLE,
    GEMS_COMPONENT_PARAMETERS_TABLE,
    GEMS_COMPONENT_PROPERTIES_TABLE,
    GEMS_COMPONENTS_TABLE,
    GEMS_SYSTEM_METADATA_TABLE,
    GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE,
)
from antarest.study.dao.database.models.thermal import THERMAL_CLUSTER_TABLE

METADATA_TABLE = GEMS_SYSTEM_METADATA_TABLE


def _reorder_connection(connection: GemsComponentConnection) -> GemsComponentConnection:
    endpoint1 = (connection.component1, connection.port1)
    endpoint2 = (connection.component2, connection.port2)
    (component_a, port_a), (component_b, port_b) = sorted((endpoint1, endpoint2))

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


def _check_components_exist(
    components_library_and_model: dict[str, tuple[str, str]], connections: list[GemsComponentConnection]
) -> None:
    referenced_component_ids = {c for connection in connections for c in (connection.component1, connection.component2)}
    if invalid_component_ids := referenced_component_ids - components_library_and_model.keys():
        raise GemsInvalidConnection(
            f"Connection(s) reference non-existing component(s): {sorted(invalid_component_ids)}"
        )


def _check_connection_does_not_link_port_component_to_itself(connections: list[GemsComponentConnection]) -> None:
    for connection in connections:
        if connection.component1 == connection.component2 and connection.port1 == connection.port2:
            raise GemsInvalidConnection(
                f"A connection cannot link the port '{connection.port1}' of component '{connection.component1}' to itself"
            )


def _check_legacy_connections(
    section: str,
    connections: Sequence[GemsAreaConnection | GemsThermalCapacityConnection],
    component_ids: set[str],
) -> None:
    connected_ports: set[tuple[str, str]] = set()
    for connection in connections:
        if connection.component not in component_ids:
            raise GemsInvalidConnection(f"{section}: component '{connection.component}' does not exist")
        port = (connection.component, connection.port)
        if port in connected_ports:
            raise GemsInvalidConnection(
                f"{section}: port '{connection.port}' of component '{connection.component}' is connected more than once"
            )
        connected_ports.add(port)


def _encode_parameter_value(value: float | str) -> str:
    # The `value` column stores either a fixed numeric value or the `id` of a data series as text,
    # since SQL has no native "number or string" column type. `repr` keeps the float's precision so
    # it round-trips exactly through `_decode_parameter_value`.
    return repr(value) if isinstance(value, float) else value


def _decode_parameter_value(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value


def _check_parameters_values_are_correctly_typed(
    components: List[GemsComponent], original_exception: Exception
) -> None:
    incorrectly_float_typed_parameter_ids: set[str] = set()
    incorrectly_str_typed_parameter_ids: set[str] = set()

    for component in components:
        if component.parameters:
            for parameter in component.parameters:
                _check_float_value_is_correctly_typed(incorrectly_float_typed_parameter_ids, parameter)
                _check_str_value_is_correctly_typed(incorrectly_str_typed_parameter_ids, parameter)

    if incorrectly_str_typed_parameter_ids or incorrectly_float_typed_parameter_ids:
        message = _build_error_message(incorrectly_float_typed_parameter_ids, incorrectly_str_typed_parameter_ids)

        raise GemsInvalidParameterValue(message) from original_exception


def _check_str_value_is_correctly_typed(
    incorrectly_str_typed_parameter_ids: set[str], parameter: _GemsParameters
) -> None:
    is_incorrectly_typed_str = isinstance(parameter.value, str) and (
        not parameter.time_dependent and not parameter.scenario_dependent
    )

    if is_incorrectly_typed_str:
        incorrectly_str_typed_parameter_ids.add(parameter.id)


def _check_float_value_is_correctly_typed(
    incorrectly_float_typed_parameter_ids: set[str], parameter: _GemsParameters
) -> None:
    is_incorrectly_typed_float = isinstance(parameter.value, (int, float)) and (
        parameter.time_dependent or parameter.scenario_dependent
    )
    if is_incorrectly_typed_float:
        incorrectly_float_typed_parameter_ids.add(parameter.id)


def _build_error_message(
    incorrectly_float_typed_parameter_ids: set[str], incorrectly_str_typed_parameter_ids: set[str]
) -> str:
    message = ""
    if incorrectly_str_typed_parameter_ids:
        message += f"Parameter value(s) must be a float when they do not depend on time or scenario: {sorted(incorrectly_str_typed_parameter_ids)}"

    if incorrectly_float_typed_parameter_ids:
        if message:
            message += "\n"
        message += f"Parameter value(s) must be a string when they depend on time or scenario: {sorted(incorrectly_float_typed_parameter_ids)}"
    return message


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
        area_connections = self._get_area_connections()
        thermal_capacity_connections = self._get_thermal_capacity_connections()

        return GemsSystem.model_validate(
            {
                "id": metadata_row.system_id,
                "description": metadata_row.description,
                "components": components,
                "connections": connections,
                "area_connections": area_connections,
                "thermal_capacity_connections": thermal_capacity_connections,
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
                    "value": _decode_parameter_value(parameter_row.value),
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

    def _get_area_connections(self) -> List[GemsAreaConnection]:
        table = GEMS_AREA_CONNECTIONS_TABLE
        stmt = select(table.c.component_id, table.c.port_id, table.c.area_id).where(
            table.c.study_data_id == self._study_data_id
        )
        return [
            GemsAreaConnection.model_validate({"component": row.component_id, "port": row.port_id, "area": row.area_id})
            for row in self._db_session.execute(stmt)
        ]

    def _get_thermal_capacity_connections(self) -> List[GemsThermalCapacityConnection]:
        table = GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE
        stmt = select(table.c.component_id, table.c.port_id, table.c.area_id, table.c.cluster_id).where(
            table.c.study_data_id == self._study_data_id
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

        metadata_values = {
            "study_data_id": study_data_id,
            "system_id": system.id,
            "description": system.description,
        }

        session.execute(insert(GEMS_SYSTEM_METADATA_TABLE), metadata_values)

        try:
            self.save_components(system.components)
            self._save_connections(system.connections)
            self._save_area_connections(system.area_connections)
            self._save_thermal_capacity_connections(system.thermal_capacity_connections)
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
                        "value": _encode_parameter_value(parameter.value),
                        "dataseries_id": parameter.value if isinstance(parameter.value, str) else None,
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
            try:
                session.execute(insert(GEMS_COMPONENT_PARAMETERS_TABLE), parameter_values)
            except IntegrityError as e:
                self._raise_the_right_component_exception(components, e)
        if property_values:
            session.execute(insert(GEMS_COMPONENT_PROPERTIES_TABLE), property_values)

        session.commit()

    def _save_area_connections(self, connections: List[GemsAreaConnection]) -> None:
        if not connections:
            return

        study_data_id = self._study_data_id
        session = self._db_session

        rows = []
        for connection in connections:
            rows.append(
                {
                    "study_data_id": study_data_id,
                    "component_id": connection.component,
                    "port_id": connection.port,
                    "area_id": connection.area,
                }
            )

        try:
            session.execute(insert(GEMS_AREA_CONNECTIONS_TABLE), rows)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_the_right_area_connection_exception(connections, e)

    def _save_thermal_capacity_connections(self, connections: List[GemsThermalCapacityConnection]) -> None:
        if not connections:
            return

        study_data_id = self._study_data_id
        session = self._db_session

        rows = []
        for connection in connections:
            rows.append(
                {
                    "study_data_id": study_data_id,
                    "component_id": connection.component,
                    "port_id": connection.port,
                    "area_id": connection.thermal_component.area,
                    "cluster_id": connection.thermal_component.cluster_id,
                }
            )

        try:
            session.execute(insert(GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE), rows)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_the_right_thermal_capacity_connection_exception(connections, e)

    def _check_legacy_connections_components_and_ports(
        self,
        section: str,
        connections: Sequence[GemsAreaConnection | GemsThermalCapacityConnection],
        e: IntegrityError,
    ) -> None:
        component_ids = set(self._get_components_library_and_model())
        try:
            _check_legacy_connections(section, connections, component_ids)
        except GemsInvalidConnection as error:
            raise error from e

    def _raise_the_right_area_connection_exception(
        self, connections: List[GemsAreaConnection], e: IntegrityError
    ) -> NoReturn:
        self._check_legacy_connections_components_and_ports("area-connections", connections, e)

        area_ids = set(self.get_impl().get_all_area_ids())
        for connection in connections:
            if connection.area not in area_ids:
                raise GemsInvalidConnection(
                    f"Component '{connection.component}' is connected to a non-existing area '{connection.area}'"
                ) from e

        # All components and areas exist and no port is connected twice.
        # It means the DB table is not filled as it should.
        raise ValueError("The area connections table is not filled as it should") from e

    def _raise_the_right_thermal_capacity_connection_exception(
        self, connections: List[GemsThermalCapacityConnection], e: IntegrityError
    ) -> NoReturn:
        self._check_legacy_connections_components_and_ports("thermal-capacity-connections", connections, e)

        table = THERMAL_CLUSTER_TABLE
        stmt = select(table.c.area_id, table.c.thermal_id).where(table.c.study_data_id == self._study_data_id)
        cluster_ids = {(row.area_id, row.thermal_id) for row in self._db_session.execute(stmt)}
        for connection in connections:
            thermal = connection.thermal_component
            if (thermal.area, thermal.cluster_id) not in cluster_ids:
                raise GemsInvalidConnection(
                    f"Component '{connection.component}' is connected to a non-existing thermal cluster"
                    f" '{thermal.cluster_id}' in area '{thermal.area}'"
                ) from e

        # All components and clusters exist and no port is connected twice.
        # It means the DB table is not filled as it should.
        raise ValueError("The thermal capacity connections table is not filled as it should") from e

    def _raise_the_right_component_exception(self, components: list[GemsComponent], e: IntegrityError) -> None:
        _check_parameters_values_are_correctly_typed(components, e)
        self._check_parameter_values_reference_existing_data_series(components, e)

        # Default exceptio
        raise GemsInvalidComponents("Could not save components, the table is not  filled as it should") from e

    def _check_parameter_values_reference_existing_data_series(
        self, components: List[GemsComponent], original_exception: Exception
    ) -> None:
        referenced_ids = {
            parameter.value
            for component in components
            for parameter in component.parameters or []
            if isinstance(parameter.value, str)
        }
        if not referenced_ids:
            return

        study_data_id = self._study_data_id
        session = self._db_session

        existing_ids_stmt = select(GEMS_DATA_SERIES_TABLE.c.id).where(
            GEMS_DATA_SERIES_TABLE.c.study_data_id == study_data_id,
            GEMS_DATA_SERIES_TABLE.c.id.in_(referenced_ids),
        )
        existing_ids = {row.id for row in session.execute(existing_ids_stmt).fetchall()}

        if missing_ids := referenced_ids - existing_ids:
            raise GemsInvalidParameterValue(
                f"Parameter value(s) reference non-existing data series: {sorted(missing_ids)}"
            ) from original_exception

    def _get_components_library_and_model(self) -> dict[str, tuple[str, str]]:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(
            GEMS_COMPONENTS_TABLE.c.component_id, GEMS_COMPONENTS_TABLE.c.library_id, GEMS_COMPONENTS_TABLE.c.model_id
        ).where(GEMS_COMPONENTS_TABLE.c.study_data_id == study_data_id)
        return {row.component_id: (row.library_id, row.model_id) for row in session.execute(stmt).fetchall()}

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

    def _save_connections(self, connections: List[GemsComponentConnection]) -> None:

        if not connections:
            return

        study_data_id = self._study_data_id
        session = self._db_session

        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {study_data_id}")

        rows = []
        for connection in connections:
            rows.append(
                {
                    "study_data_id": study_data_id,
                    "component1": connection.component1,
                    "component2": connection.component2,
                    "port1": connection.port1,
                    "port2": connection.port2,
                }
            )

        try:
            session.execute(insert(GEMS_COMPONENT_CONNECTIONS_TABLE), rows)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_the_right_connection_exception(connections, e)

    def _raise_the_right_connection_exception(
        self,
        connections: list[GemsComponentConnection],
        e: IntegrityError,
    ) -> NoReturn:

        _check_connection_does_not_link_port_component_to_itself(connections)
        # GEMS tolerates exact duplicates (same component1/component2/port1/port2) inside a system.yml file,
        # so we have to check that the connections are not duplicated.
        _check_no_duplicated_connections(connections)

        components_library_and_model = self._get_components_library_and_model()
        _check_components_exist(components_library_and_model, connections)
        self._check_ports_exist_in_models(components_library_and_model, connections, e)

        # All components and ports exist and no self-connection was found.
        # It means the DB table is not filled as it should.
        raise ValueError("The connections table is not filled as it should") from e
