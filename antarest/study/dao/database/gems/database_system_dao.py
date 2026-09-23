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
from typing_extensions import override

from antarest.core.exceptions import GemsSystemAlreadyExists, GemsSystemNotFound
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.system import (
    GEMS_COMPONENT_TABLE,
    GEMS_PARAMETER_TABLE,
    GEMS_PROPERTIES_TABLE,
    GEMS_SYSTEM_METADATA_TABLE,
)

METADATA_TABLE = GEMS_SYSTEM_METADATA_TABLE


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
    def get_components(self) -> List[GemsComponent] | None:
        study_data_id = self._study_data_id
        session = self._db_session

        component_parameters = self._get_components_parameters()
        component_properties = self._get_components_properties()

        components_stmt = select(GEMS_COMPONENT_TABLE).where(GEMS_COMPONENT_TABLE.c.study_data_id == study_data_id)
        all_components_rows = session.execute(components_stmt).fetchall()

        if not all_components_rows:
            return None

        components = []
        for component_row in all_components_rows:
            current_component = GemsComponent.model_validate(
                {
                    "id": component_row.component_id,
                    "model": component_row.model_id,
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

        parameters_stmt = select(GEMS_PARAMETER_TABLE).where(GEMS_PARAMETER_TABLE.c.study_data_id == study_data_id)
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

        properties_stmt = select(GEMS_PROPERTIES_TABLE).where(GEMS_PROPERTIES_TABLE.c.study_data_id == study_data_id)
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

    def _get_connections(self) -> List[str]:
        return []  # TODO: Implement connections

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

        self.save_components(system.components)

    @override
    def save_components(self, components: List[GemsComponent]) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        if not self._get_system_row_if_exists():
            raise GemsSystemNotFound(f"No system configuration found for study {study_data_id}")

        # Clean all existing data regarding components
        session.execute(delete(GEMS_PARAMETER_TABLE).where(GEMS_PARAMETER_TABLE.c.study_data_id == study_data_id))
        session.execute(delete(GEMS_PROPERTIES_TABLE).where(GEMS_PROPERTIES_TABLE.c.study_data_id == study_data_id))
        session.execute(delete(GEMS_COMPONENT_TABLE).where(GEMS_COMPONENT_TABLE.c.study_data_id == study_data_id))

        component_values = []
        parameter_values = []
        property_values = []
        for component in components:
            component_values.append(
                {
                    "study_data_id": study_data_id,
                    "component_id": component.id,
                    "model_id": component.model,
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
            session.execute(insert(GEMS_COMPONENT_TABLE), component_values)
        if parameter_values:
            session.execute(insert(GEMS_PARAMETER_TABLE), parameter_values)
        if property_values:
            session.execute(insert(GEMS_PROPERTIES_TABLE), property_values)

        session.commit()
