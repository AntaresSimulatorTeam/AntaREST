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
    GEMS_OPTIM_CONFIG_MODELS_TABLE,
    GEMS_OPTIM_CONFIG_TABLE,
)


def _model_to_rows(study_data_id: int, model: GemsOptimConfigModel) -> list[dict[str, Any]]:
    library_id, model_id = split_library_and_model_id(model.id)
    base = {
        "study_data_id": study_data_id,
        "library_id": library_id,
        "model_id": model_id,
        "variable_id": None,
        "constraint_id": None,
        "objective_contribution_id": None,
        "out_of_bounds_mode": None,
        "location": None,
        "heuristics": None,
    }
    heuristics = None
    if model.heuristics is not None:
        heuristics = json.dumps([h.model_dump(mode="json", by_alias=True) for h in model.heuristics])
    rows = [{**base, "heuristics": heuristics}]

    # Constraints may appear both in out-of-bounds-processing and model-decomposition: they share the same row.
    constraint_rows: dict[str, dict[str, Any]] = {}
    if model.out_of_bounds_processing is not None:
        for constraint in model.out_of_bounds_processing.constraints:
            constraint_rows[constraint.id] = {
                **base,
                "constraint_id": constraint.id,
                "out_of_bounds_mode": constraint.mode,
            }
    decomposition = model.model_decomposition
    if decomposition is not None:
        for decomposed_constraint in decomposition.constraints:
            row = constraint_rows.setdefault(
                decomposed_constraint.id, {**base, "constraint_id": decomposed_constraint.id}
            )
            row["location"] = decomposed_constraint.location
        rows += [{**base, "variable_id": v.id, "location": v.location} for v in decomposition.variables]
        rows += [
            {**base, "objective_contribution_id": o.id, "location": o.location}
            for o in decomposition.objective_contributions
        ]
    rows += list(constraint_rows.values())
    return rows


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

        # Models part
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
        model_values = [row for model in optim_config.models for row in _model_to_rows(study_data_id, model)]
        if model_values:
            try:
                session.execute(insert(GEMS_OPTIM_CONFIG_MODELS_TABLE), model_values)
            except Exception:
                session.rollback()
                raise

        session.commit()
