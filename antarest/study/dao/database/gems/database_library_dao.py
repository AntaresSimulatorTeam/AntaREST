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
import json
from typing import Any, Callable

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import GemsLibraryAlreadyExists, GemsTaxonomyNotFound
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.gems_library_dao import GemsLibraryDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.library import (
    GEMS_LIBRARY_METADATA_TABLE,
    GEMS_MODELS_CONSTRAINTS_TABLE,
    GEMS_MODELS_OBJECTIVE_CONTRIBUTIONS_TABLE,
    GEMS_MODELS_PARAMETERS_TABLE,
    GEMS_MODELS_PORTS_TABLE,
    GEMS_MODELS_TABLE,
    GEMS_MODELS_VARIABLES_TABLE,
    GEMS_PORT_TYPES_TABLE,
)


class DatabaseGemsLibraryDao(GemsLibraryDao, DatabaseDaoBase):
    """Database implementation of GemsLibraryDao"""

    @override
    def get_library(self) -> GemsLibrary | None:
        study_data_id = self._study_data_id
        session = self._db_session

        # Library metadata
        stmt = select(GEMS_LIBRARY_METADATA_TABLE).where(GEMS_LIBRARY_METADATA_TABLE.c.study_data_id == study_data_id)

        metadata_row = session.execute(stmt).fetchone()
        if not metadata_row:
            # No library found, as it is not mandatory to have a library, we simply return None.
            return None

        # Port Types
        port_types_stmt = select(GEMS_PORT_TYPES_TABLE).where(GEMS_PORT_TYPES_TABLE.c.study_data_id == study_data_id)
        port_types = []
        for port_type_row in session.execute(port_types_stmt).fetchall():
            port_type = {
                "id": port_type_row.id,
                "description": port_type_row.description,
                "fields": json.loads(port_type_row.fields),
            }
            if port_type_row.area_connection is not None:
                port_type["area_connection"] = json.loads(port_type_row.area_connection)
            if port_type_row.thermal_capacity_connection is not None:
                port_type["thermal_capacity_connection"] = json.loads(port_type_row.thermal_capacity_connection)
            port_types.append(port_type)

        # Models
        ## Ports
        ports_table = GEMS_MODELS_PORTS_TABLE
        model_ports_stmt = select(ports_table).where(ports_table.c.study_data_id == study_data_id)
        model_ports_rows = session.execute(model_ports_stmt).fetchall()
        model_ports: dict[str, list[dict[str, str]]] = {}
        for model_ports_row in model_ports_rows:
            model_ports.setdefault(model_ports_row.model_id, []).append(
                {
                    "id": model_ports_row.port_id,
                    "type": model_ports_row.type,
                }
            )

        ## Parameters
        parameters_table = GEMS_MODELS_PARAMETERS_TABLE
        model_parameters_stmt = select(parameters_table).where(parameters_table.c.study_data_id == study_data_id)
        model_parameters_rows = session.execute(model_parameters_stmt).fetchall()
        model_parameters: dict[str, list[dict[str, Any]]] = {}
        for model_parameters_row in model_parameters_rows:
            model_parameters.setdefault(model_parameters_row.model_id, []).append(
                {
                    "id": model_parameters_row.parameter_id,
                    "time_dependent": model_parameters_row.time_dependent,
                    "scenario_dependent": model_parameters_row.scenario_dependent,
                }
            )

        # Variables
        variables_table = GEMS_MODELS_VARIABLES_TABLE
        model_variables_stmt = select(variables_table).where(variables_table.c.study_data_id == study_data_id)
        model_variables_rows = session.execute(model_variables_stmt).fetchall()
        model_variables: dict[str, list[dict[str, Any]]] = {}
        for model_variables_row in model_variables_rows:
            model_variables.setdefault(model_variables_row.model_id, []).append(
                {
                    "id": model_variables_row.id,
                    "type": model_variables_row.type,
                    "lower_bound": model_variables_row.lower_bound,
                    "upper_bound": model_variables_row.upper_bound,
                }
            )

        ## Constraints and Objective contributions
        model_constraints: dict[str, list[dict[str, Any]]] = {}
        model_objective_contributions: dict[str, list[dict[str, Any]]] = {}
        for table, mapping in [
            (GEMS_MODELS_CONSTRAINTS_TABLE, model_constraints),
            (GEMS_MODELS_OBJECTIVE_CONTRIBUTIONS_TABLE, model_objective_contributions),
        ]:
            stmt = select(table).where(table.c.study_data_id == study_data_id)
            rows = session.execute(stmt).fetchall()
            for row in rows:
                mapping.setdefault(row.model_id, []).append({"id": row.constraint_id, "expression": row.expression})

        ## Other data
        models_stmt = select(GEMS_MODELS_TABLE).where(GEMS_MODELS_TABLE.c.study_data_id == study_data_id)
        models = []
        for model_row in session.execute(models_stmt).fetchall():
            models.append(
                {
                    "id": model_row.id,
                    "description": model_row.description,
                    "taxonomy_category": model_row.taxonomy_category,
                    "properties": json.loads(model_row.properties) if model_row.properties is not None else [],
                    "ports": model_ports.get(model_row.id, []),
                    "parameters": model_parameters.get(model_row.id, []),
                    "constraints": model_constraints.get(model_row.id, []),
                    "objective_contributions": model_objective_contributions.get(model_row.id, []),
                    "variables": model_variables.get(model_row.id, []),
                    # These fields were dumped as is, we simply reload them.
                    "binding_constraints": json.loads(model_row.binding_constraints),
                    "extra_outputs": json.loads(model_row.extra_outputs),
                    "port_field_definitions": json.loads(model_row.port_field_definitions),
                }
            )

        # Full library
        return GemsLibrary.model_validate(
            {
                "id": metadata_row.id,
                "description": metadata_row.description,
                "version": metadata_row.version,
                "taxonomy": metadata_row.taxonomy,
                "port_types": port_types,
                "models": models,
            }
        )

    @override
    def save_library(self, library: GemsLibrary) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(GEMS_LIBRARY_METADATA_TABLE).where(GEMS_LIBRARY_METADATA_TABLE.c.study_data_id == study_data_id)

        row = session.execute(stmt).fetchone()
        if row:
            raise GemsLibraryAlreadyExists(f"A library already exists for study {self._study_id}")

        metadata_values = {
            "study_data_id": study_data_id,
            "id": library.id,
            "description": library.description,
            "version": library.version,
            "taxonomy": library.taxonomy,
        }
        try:
            session.execute(insert(GEMS_LIBRARY_METADATA_TABLE), metadata_values)
        except IntegrityError as e:
            session.rollback()
            if library.taxonomy:
                raise GemsTaxonomyNotFound(library.taxonomy, self._study_id) from e
            raise e

        port_type_values = [
            {
                "study_data_id": study_data_id,
                "library_id": library.id,
                "id": port_type.id,
                "description": port_type.description,
                "fields": json.dumps([field.model_dump() for field in port_type.fields]),
                "area_connection": port_type.area_connection.model_dump_json(exclude_none=True)
                if port_type.area_connection
                else None,
                "thermal_capacity_connection": port_type.thermal_capacity_connection.model_dump_json()
                if port_type.thermal_capacity_connection
                else None,
            }
            for port_type in library.port_types
        ]
        if port_type_values:
            session.execute(insert(GEMS_PORT_TYPES_TABLE), port_type_values)

        def _convert_model_to_rows(
            items: list[Any], dump: Callable[[Any], dict[str, Any]] = lambda x: x.model_dump(mode="json")
        ) -> list[dict[str, Any]]:
            return [
                {
                    "study_data_id": study_data_id,
                    "library_id": library.id,
                    "model_id": model.id,
                    **dump(item),
                }
                for item in items
            ]

        model_values = []
        port_values = []
        parameter_values = []
        variables_values = []
        constraints_values = []
        objective_contributions_values = []
        for model in library.models:
            model_dump = model.model_dump(mode="json")
            model_values.append(
                {
                    "study_data_id": study_data_id,
                    "library_id": library.id,
                    "id": model.id,
                    "description": model.description,
                    "taxonomy_category": model.taxonomy_category,
                    # These fields are dumped as is as we do not care about them for the moment.
                    "properties": json.dumps(model_dump["properties"]),
                    "binding_constraints": json.dumps(model_dump["binding_constraints"]),
                    "extra_outputs": json.dumps(model_dump["extra_outputs"]),
                    "port_field_definitions": json.dumps(model_dump["port_field_definitions"]),
                }
            )

            port_values += _convert_model_to_rows(model.ports, dump=lambda p: {"port_id": p.id, "type": p.type})
            parameter_values += _convert_model_to_rows(
                model.parameters, dump=lambda p: {"parameter_id": p.id, **p.model_dump()}
            )
            variables_values += _convert_model_to_rows(model.variables)
            constraints_values += _convert_model_to_rows(model.constraints)
            objective_contributions_values += _convert_model_to_rows(model.objective_contributions)

        if model_values:
            session.execute(insert(GEMS_MODELS_TABLE), model_values)
        if port_values:
            session.execute(insert(GEMS_MODELS_PORTS_TABLE), port_values)
        if parameter_values:
            session.execute(insert(GEMS_MODELS_PARAMETERS_TABLE), parameter_values)
        if variables_values:
            session.execute(insert(GEMS_MODELS_VARIABLES_TABLE), variables_values)
        if constraints_values:
            session.execute(insert(GEMS_MODELS_CONSTRAINTS_TABLE), constraints_values)
        if objective_contributions_values:
            session.execute(insert(GEMS_MODELS_OBJECTIVE_CONTRIBUTIONS_TABLE), objective_contributions_values)

        session.commit()
