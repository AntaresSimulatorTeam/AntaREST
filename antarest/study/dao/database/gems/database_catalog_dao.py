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

from sqlalchemy import insert, select
from typing_extensions import override

from antarest.core.exceptions import GemsCatalogAlreadyExists
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.api.gems_catalog_dao import GemsCatalogDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.catalog import GEMS_CATALOGS_TABLE


class DatabaseGemsCatalogDao(GemsCatalogDao, DatabaseDaoBase):
    @override
    def get_catalogs(self) -> list[GemsCatalog]:
        table = GEMS_CATALOGS_TABLE
        rows = self._db_session.execute(
            select(table).where(table.c.study_data_id == self._study_data_id).order_by(table.c.id)
        ).fetchall()
        return [
            GemsCatalog.model_validate(
                {
                    "id": row.id,
                    "taxonomy": row.taxonomy,
                    "location": {"taxonomy-category": row.location},
                    "metrics-definition": json.loads(row.metrics_definition),
                }
            )
            for row in rows
        ]

    @override
    def save_catalog(self, catalog: GemsCatalog) -> None:
        table = GEMS_CATALOGS_TABLE
        session = self._db_session
        existing = session.execute(
            select(table.c.id).where((table.c.study_data_id == self._study_data_id) & (table.c.id == catalog.id))
        ).first()
        if existing:
            raise GemsCatalogAlreadyExists(f"Catalog '{catalog.id}' already exists for study {self._study_id}")

        content = catalog.model_dump(mode="json", exclude_unset=True, by_alias=True)
        session.execute(
            insert(table),
            {
                "study_data_id": self._study_data_id,
                "id": catalog.id,
                "taxonomy": catalog.taxonomy,
                "location": catalog.location.taxonomy_category,
                "metrics_definition": json.dumps(content.get("metrics-definition", [])),
            },
        )
        session.commit()
