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
from typing import Any, NamedTuple

from sqlalchemy import Table, delete, insert, select
from sqlalchemy.orm import Session
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


def _save_models(study_data_id: int, session: Session, models: list[GemsOptimConfigModel]) -> None:
    if not models:
        return

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
    class _ModelDecompositionMapping(NamedTuple):
        pydantic_attribute: str
        db_table: Table
        db_column_name: str

    decomposition_list = [
        _ModelDecompositionMapping("variables", GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_VARIABLES_TABLE, "variable_id"),
        _ModelDecompositionMapping(
            "constraints", GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_CONSTRAINTS_TABLE, "constraint_id"
        ),
        _ModelDecompositionMapping(
            "objective_contributions",
            GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_OBJECTIVE_CONTRIBUTIONS_TABLE,
            "objective_contribution_id",
        ),
    ]

    rows_by_kind: dict[str, list[dict[str, Any]]] = {d.pydantic_attribute: [] for d in decomposition_list}

    for model in models:
        if model.model_decomposition:
            library_id, model_id = split_library_and_model_id(model.id)
            for decomposition in decomposition_list:
                rows_by_kind[decomposition.pydantic_attribute].extend(
                    {
                        "study_data_id": study_data_id,
                        "library_id": library_id,
                        "model_id": model_id,
                        decomposition.db_column_name: item.id,
                        "location": item.location,
                    }
                    for item in getattr(model.model_decomposition, decomposition.pydantic_attribute)
                )

    for decomposition in decomposition_list:
        values = rows_by_kind.get(decomposition.pydantic_attribute)
        if values:
            try:
                session.execute(insert(decomposition.db_table), values)
            except Exception:
                session.rollback()
                raise


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
        models: dict[str, dict[str, Any]] = {}

        # Heuristics
        table = GEMS_OPTIM_CONFIG_HEURISTICS_TABLE
        heuristic_rows = session.execute(select(table).where(table.c.study_data_id == study_data_id)).fetchall()
        for heuristic_row in heuristic_rows:
            model_id = f"{heuristic_row.library_id}.{heuristic_row.model_id}"
            models.setdefault(model_id, {})["heuristics"] = json.loads(heuristic_row.data)

        # Out of bound processing
        table = GEMS_OPTIM_CONFIG_OOB_PROCESSING_TABLE
        oob_rows = session.execute(select(table).where(table.c.study_data_id == study_data_id)).fetchall()
        for oob_row in oob_rows:
            model_id = f"{oob_row.library_id}.{oob_row.model_id}"

            models.setdefault(model_id, {}).setdefault("out_of_bounds_processing", {"constraints": []})[
                "constraints"
            ].append({"id": oob_row.constraint_id, "mode": oob_row.mode})

        # Model decomposition

        # todo

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
        _save_models(study_data_id, session, optim_config.models)

        session.commit()
