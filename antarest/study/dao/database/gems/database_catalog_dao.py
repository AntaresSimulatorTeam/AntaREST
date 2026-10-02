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
from typing_extensions import override

from antarest.core.exceptions import GemsCatalogAlreadyExists
from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.api.gems_catalog_dao import GemsCatalogDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.catalog import GEMS_CATALOG_METRICS_TABLE, GEMS_CATALOGS_TABLE


class DatabaseGemsCatalogDao(GemsCatalogDao, DatabaseDaoBase):
    @override
    def get_catalogs(self) -> list[GemsCatalog]:
        table = GEMS_CATALOGS_TABLE
        rows = self._db_session.execute(
            select(table).where(table.c.study_data_id == self._study_data_id).order_by(table.c.id)
        ).fetchall()
        if not rows:
            return []

        metrics_table = GEMS_CATALOG_METRICS_TABLE
        metrics: dict[str, list[dict[str, Any]]] = {}
        metric_rows = self._db_session.execute(
            select(metrics_table)
            .where(metrics_table.c.study_data_id == self._study_data_id)
            .order_by(metrics_table.c.catalog_id, metrics_table.c.id)
        )
        for row in metric_rows:
            row_values = get_row_representation_as_dict(row)
            metric = {"id": row.id, "terms_operator": row.terms_operator, "time_operator": row.time_operator}
            for field in ("terms", "breakdown", "filter"):
                value = row_values[field]
                if value is not None:
                    metric[field] = json.loads(value)
            metrics.setdefault(row.catalog_id, []).append(metric)

        return [
            GemsCatalog.model_validate(
                {
                    "id": row.id,
                    "taxonomy": row.taxonomy,
                    "location": {"taxonomy_category": row.location},
                    "metrics_definition": metrics.get(row.id, []),
                }
            )
            for row in rows
        ]

    @override
    def save_catalogs(self, catalogs: list[GemsCatalog]) -> None:
        if not catalogs:
            return

        table = GEMS_CATALOGS_TABLE
        session = self._db_session
        catalog_ids: set[str] = set()
        for catalog in catalogs:
            if catalog.id in catalog_ids:
                raise GemsCatalogAlreadyExists(f"Catalog '{catalog.id}' occurs several times in the batch")
            catalog_ids.add(catalog.id)

        existing = session.execute(
            select(table.c.id).where((table.c.study_data_id == self._study_data_id) & table.c.id.in_(catalog_ids))
        ).first()
        if existing:
            raise GemsCatalogAlreadyExists(f"Catalog '{existing.id}' already exists for study {self._study_id}")

        catalog_values = []
        metric_values = []
        for catalog in catalogs:
            catalog_values.append(
                {
                    "study_data_id": self._study_data_id,
                    "id": catalog.id,
                    "taxonomy": catalog.taxonomy,
                    "location": catalog.location.taxonomy_category,
                }
            )
            for metric in catalog.metrics_definition:
                content = metric.model_dump(mode="json", exclude_unset=True)
                metric_values.append(
                    {
                        "study_data_id": self._study_data_id,
                        "catalog_id": catalog.id,
                        "id": metric.id,
                        "terms_operator": metric.terms_operator,
                        "time_operator": metric.time_operator,
                        **{
                            field: json.dumps(content[field]) if field in content else None
                            for field in ("terms", "breakdown", "filter")
                        },
                    }
                )

        try:
            session.execute(insert(table), catalog_values)
            if metric_values:
                session.execute(insert(GEMS_CATALOG_METRICS_TABLE), metric_values)
            session.commit()
        except Exception:
            session.rollback()
            raise
