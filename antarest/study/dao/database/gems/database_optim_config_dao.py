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

from sqlalchemy import delete, insert, select
from typing_extensions import override

from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.business.model.gems.optim_config import GemsOptimConfig, GemsOptimConfigModel
from antarest.study.business.model.gems.system import split_library_and_model_id
from antarest.study.dao.api.gems_optim_config_dao import GemsOptimConfigDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.optim_config import (
    GEMS_OPTIM_CONFIG_HEURISTICS_TABLE,
    GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_CONSTRAINTS_TABLE,
    GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_OBJECTIVE_CONTRIBUTIONS_TABLE,
    GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_VARIABLES_TABLE,
    GEMS_OPTIM_CONFIG_OOB_PROCESSING_TABLE,
    GEMS_OPTIM_CONFIG_TABLE,
)


class DatabaseGemsOptimConfigDao(GemsOptimConfigDao, DatabaseDaoBase):
    """Database implementation of GemsOptimConfigDao"""

    @override
    def get_optim_config(self) -> GemsOptimConfig | None:
        study_data_id = self._study_data_id
        session = self._db_session

        table = GEMS_OPTIM_CONFIG_TABLE
        config_row = session.execute(select(table).where(table.c.study_data_id == study_data_id)).fetchone()
        if not config_row:
            return None

        optim_config_data = get_row_representation_as_dict(config_row)
        del optim_config_data["study_data_id"]
        for key in optim_config_data:
            optim_config_data[key] = json.loads(optim_config_data[key]) if optim_config_data[key] is not None else None

        # Models part
        """
        models_table = GEMS_OPTIM_CONFIG_MODELS_TABLE
        model_rows = session.execute(
            select(models_table).where(models_table.c.study_data_id == study_data_id).order_by(models_table.c.id)
        ).fetchall()

        models: dict[str, dict[str, Any]] = {}
        for row in model_rows:
            model = models.setdefault(f"{row.library_id}.{row.model_id}", {"id": f"{row.library_id}.{row.model_id}"})
            if row.variable_id is not None:
                decomposition = model.setdefault("model_decomposition", {})
                decomposition.setdefault("variables", []).append({"id": row.variable_id, "location": row.location})
            elif row.objective_contribution_id is not None:
                decomposition = model.setdefault("model_decomposition", {})
                decomposition.setdefault("objective_contributions", []).append(
                    {"id": row.objective_contribution_id, "location": row.location}
                )
            elif row.constraint_id is not None:
                if row.out_of_bounds_mode is not None:
                    processing = model.setdefault("out_of_bounds_processing", {})
                    processing.setdefault("constraints", []).append(
                        {"id": row.constraint_id, "mode": row.out_of_bounds_mode}
                    )
                if row.location is not None:
                    decomposition = model.setdefault("model_decomposition", {})
                    decomposition.setdefault("constraints", []).append(
                        {"id": row.constraint_id, "location": row.location}
                    )
            elif row.heuristics is not None:
                model["heuristics"] = json.loads(row.heuristics)

        content = {"models": list(models.values()), **optim_config_data}
        return GemsOptimConfig.model_validate(content)
        """

    @override
    def save_optim_config(self, optim_config: GemsOptimConfig) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        # The configuration is replaced as a whole
        session.execute(delete(GEMS_OPTIM_CONFIG_TABLE).where(GEMS_OPTIM_CONFIG_TABLE.c.study_data_id == study_data_id))

        optim_config_values: dict[str, Any] = {"study_data_id": study_data_id}
        for parameter in ["time_scope", "scenario_scope", "solver_options", "resolution"]:
            if value := getattr(optim_config, parameter):
                optim_config_values[parameter] = value.model_dump_json(exclude_none=True)
            else:
                optim_config_values[parameter] = None

        session.execute(insert(GEMS_OPTIM_CONFIG_TABLE), optim_config_values)

        # Models part
        self._save_models(optim_config.models)

        session.commit()

    def _save_models(self, models: list[GemsOptimConfigModel]) -> None:
        if not models:
            return

        study_data_id = self._study_data_id
        session = self._db_session

        # Heuristics
        heuristic_values = []
        for model in models:
            if not model.heuristics:
                continue
            library_id, model_id = split_library_and_model_id(model.id)
            heuristic_values.append(
                {
                    "study_data_id": study_data_id,
                    "library_id": library_id,
                    "model_id": model_id,
                    "data": json.dumps([heuristic.model_dump_json() for heuristic in model.heuristics]),
                }
            )

        if heuristic_values:
            try:
                session.execute(insert(GEMS_OPTIM_CONFIG_HEURISTICS_TABLE), heuristic_values)
            except Exception:
                session.rollback()
                raise

        # Out of bounds processing
        oob_processing_values = []
        for model in models:
            if not model.out_of_bounds_processing or not model.out_of_bounds_processing.constraints:
                continue
            library_id, model_id = split_library_and_model_id(model.id)
            for constraint in model.out_of_bounds_processing.constraints:
                oob_processing_values.append(
                    {
                        "study_data_id": study_data_id,
                        "library_id": library_id,
                        "model_id": model_id,
                        "constraint_id": constraint.id,
                        "mode": constraint.mode,
                    }
                )

        if oob_processing_values:
            try:
                session.execute(insert(GEMS_OPTIM_CONFIG_OOB_PROCESSING_TABLE), oob_processing_values)
            except Exception:
                session.rollback()
                raise

        # Model decomposition
        variables_values = []
        constraints_values = []
        objective_contributions_values = []
        for model in models:
            if model.model_decomposition:
                library_id, model_id = split_library_and_model_id(model.id)

                # Variables
                for variable in model.model_decomposition.variables:
                    variables_values.append(
                        {
                            "study_data_id": study_data_id,
                            "library_id": library_id,
                            "model_id": model_id,
                            "variable_id": variable.id,
                            "location": variable.location,
                        }
                    )

                # Constraints
                for md_constraint in model.model_decomposition.constraints:
                    constraints_values.append(
                        {
                            "study_data_id": study_data_id,
                            "library_id": library_id,
                            "model_id": model_id,
                            "constraint_id": md_constraint.id,
                            "location": md_constraint.location,
                        }
                    )

                # Objective contributions
                for objective_contribution in model.model_decomposition.objective_contributions:
                    objective_contributions_values.append(
                        {
                            "study_data_id": study_data_id,
                            "library_id": library_id,
                            "model_id": model_id,
                            "objective_contribution_id": objective_contribution.id,
                            "location": objective_contribution.location,
                        }
                    )

        if variables_values:
            try:
                session.execute(insert(GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_VARIABLES_TABLE), variables_values)
            except Exception:
                session.rollback()
                raise

        if constraints_values:
            try:
                session.execute(insert(GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_CONSTRAINTS_TABLE), constraints_values)
            except Exception:
                session.rollback()
                raise

        if objective_contributions_values:
            try:
                session.execute(
                    insert(GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_OBJECTIVE_CONTRIBUTIONS_TABLE),
                    objective_contributions_values,
                )
            except Exception:
                session.rollback()
                raise
