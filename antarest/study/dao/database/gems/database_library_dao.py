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
from typing import Any

from sqlalchemy import insert, select

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
from typing_extensions import override

from antarest.core.exceptions import GemsLibraryAlreadyExists
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.gems_library_dao import GemsLibraryDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.library import (
    GEMS_LIBRARY_METADATA_TABLE,
    GEMS_MODELS_PARAMETERS_TABLE,
    GEMS_MODELS_PORTS_TABLE,
    GEMS_MODELS_TABLE,
    GEMS_PORT_TYPES_TABLE,
)

METADATA_TABLE = GEMS_LIBRARY_METADATA_TABLE


class DatabaseGemsLibraryDao(GemsLibraryDao, DatabaseDaoBase):
    """Database implementation of GemsLibraryDao"""

    @override
    def get_library(self) -> GemsLibrary | None:
        study_data_id = self._study_data_id
        session = self._db_session

        # Library metadata
        stmt = select(GEMS_LIBRARY_METADATA_TABLE).where(GEMS_LIBRARY_METADATA_TABLE.c.study_data_id == study_data_id)

        row = session.execute(stmt).fetchone()
        if not row:
            # No library found, as it is not mandatory to have a library, we simply return None.
            return None

        # Port Types
        port_types_stmt = select(GEMS_PORT_TYPES_TABLE).where(GEMS_PORT_TYPES_TABLE.c.study_data_id == study_data_id)
        port_types = [
            {
                "id": port_type_row.id,
                "description": port_type_row.description,
                "fields": json.loads(port_type_row.fields),
                "area_connection": json.loads(port_type_row.area_connection),
                "thermal_capacity_connection": json.loads(port_type_row.thermal_capacity_connection),
            }
            for port_type_row in session.execute(port_types_stmt).fetchall()
        ]

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

        ## Models metadata
        models_stmt = select(GEMS_MODELS_TABLE).where(GEMS_MODELS_TABLE.c.study_data_id == study_data_id)
        models = []
        for model_row in session.execute(models_stmt).fetchall():
            models.append(
                {
                    "id": model_row.id,
                    "description": model_row.description,
                    "taxonomy_category": model_row.taxonomy_category,
                    "properties": json.loads(model_row.properties) if model_row.properties is not None else [],
                    "variables": json.loads(model_row.variables),
                    "binding_constraints": json.loads(model_row.binding_constraints),
                    "constraints": json.loads(model_row.constraints),
                    "objective_contributions": json.loads(model_row.objective_contributions),
                    "extra_outputs": json.loads(model_row.extra_outputs),
                    "ports": model_ports.get(model_row.id, []),
                    "parameters": model_parameters.get(model_row.id, []),
                    "port_field_definitions": json.loads(model_row.port_field_definitions),
                }
            )

        # Full library
        return GemsLibrary.model_validate(
            {
                "id": row.id,
                "description": row.description,
                "version": row.version,
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
        }
        session.execute(insert(GEMS_LIBRARY_METADATA_TABLE), metadata_values)

        port_type_values = [
            {
                "study_data_id": study_data_id,
                "id": port_type.id,
                "description": port_type.description,
                "fields": json.dumps([field.model_dump(mode="json") for field in port_type.fields]),
                "area_connection": port_type.area_connection.model_dump_json() if port_type.area_connection else None,
                "thermal_capacity_connection": port_type.thermal_capacity_connection.model_dump_json()
                if port_type.thermal_capacity_connection
                else None,
            }
            for port_type in library.port_types
        ]
        if port_type_values:
            session.execute(insert(GEMS_PORT_TYPES_TABLE), port_type_values)

        model_values = []
        model_port_values = []
        model_parameter_values = []
        for model in library.models:
            model_dump = model.model_dump(mode="json")
            model_values.append(
                {
                    "study_data_id": study_data_id,
                    "id": model.id,
                    "description": model.description,
                    "taxonomy_category": model.taxonomy_category,
                    "properties": json.dumps(model_dump["properties"]),
                    "variables": json.dumps(model_dump["variables"]),
                    "binding_constraints": json.dumps(model_dump["binding_constraints"]),
                    "constraints": json.dumps(model_dump["constraints"]),
                    "objective_contributions": json.dumps(model_dump["objective_contributions"]),
                    "extra_outputs": json.dumps(model_dump["extra_outputs"]),
                    "port_field_definitions": json.dumps(model_dump["port_field_definitions"]),
                }
            )

            for model_port in model_dump.get("ports", []):
                model_port_values.append(
                    {
                        "study_data_id": study_data_id,
                        "model_id": model.id,
                        "port_id": model_port["id"],
                        "type": model_port["type"],
                    }
                )

            for model_parameter in model_dump.get("parameters", []):
                model_parameter_values.append(
                    {
                        "study_data_id": study_data_id,
                        "model_id": model.id,
                        "parameter_id": model_parameter["id"],
                        "time_dependent": model_parameter["time_dependent"],
                        "scenario_dependent": model_parameter["scenario_dependent"],
                    }
                )

        if model_values:
            session.execute(insert(GEMS_MODELS_TABLE), model_values)
        if model_port_values:
            session.execute(insert(GEMS_MODELS_PORTS_TABLE), model_port_values)
        if model_parameter_values:
            session.execute(insert(GEMS_MODELS_PARAMETERS_TABLE), model_parameter_values)

        session.commit()
