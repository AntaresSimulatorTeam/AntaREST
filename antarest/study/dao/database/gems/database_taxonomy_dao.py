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

from antarest.core.exceptions import GemsTaxonomyAlreadyExists
from antarest.study.business.model.gems.taxonomy import GemsTaxonomy
from antarest.study.dao.api.gems_taxonomy_dao import GemsTaxonomyDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.taxonomy import (
    GEMS_TAXONOMY_CATEGORIES_TABLE,
    GEMS_TAXONOMY_METADATA_TABLE,
)


class DatabaseGemsTaxonomyDao(GemsTaxonomyDao, DatabaseDaoBase):
    """Database implementation of GemsTaxonomyDao"""

    @override
    def get_taxonomy(self) -> GemsTaxonomy | None:
        study_data_id = self._study_data_id
        session = self._db_session

        # Taxonomy metadata
        stmt = select(GEMS_TAXONOMY_METADATA_TABLE).where(GEMS_TAXONOMY_METADATA_TABLE.c.study_data_id == study_data_id)

        metadata_row = session.execute(stmt).fetchone()
        if not metadata_row:
            # No taxonomy found, as it is not mandatory to have a taxonomy, we simply return None.
            return None

        # Taxonomy categories
        categories_stmt = select(GEMS_TAXONOMY_CATEGORIES_TABLE).where(
            GEMS_TAXONOMY_CATEGORIES_TABLE.c.study_data_id == study_data_id
        )
        categories = []
        for category_row in session.execute(categories_stmt).fetchall():
            category = {"id": category_row.id, "parent_category": category_row.parent_category}
            for key in ["variables", "parameters", "ports", "extra_outputs", "properties", "binding_constraints"]:
                value = getattr(category_row, key)
                if value is not None:
                    category[key] = json.loads(value)
            categories.append(category)

        return GemsTaxonomy.model_validate(
            {"id": metadata_row.id, "description": metadata_row.description, "categories": categories}
        )

    @override
    def save_taxonomy(self, taxonomy: GemsTaxonomy) -> None:
        study_data_id = self._study_data_id
        session = self._db_session

        stmt = select(GEMS_TAXONOMY_METADATA_TABLE).where(GEMS_TAXONOMY_METADATA_TABLE.c.study_data_id == study_data_id)

        row = session.execute(stmt).fetchone()
        if row:
            raise GemsTaxonomyAlreadyExists(f"A taxonomy already exists for study {self._study_id}")

        metadata_values = {
            "study_data_id": study_data_id,
            "id": taxonomy.id,
            "description": taxonomy.description,
        }
        session.execute(insert(GEMS_TAXONOMY_METADATA_TABLE), metadata_values)

        category_values = []
        for category in taxonomy.categories:
            cat_dump = category.model_dump(mode="json")
            data = {"study_data_id": study_data_id, "id": category.id, "parent_category": category.parent_category}
            for key in ["variables", "parameters", "ports", "extra_outputs", "properties", "binding_constraints"]:
                value = cat_dump.get(key)
                if value is not None:
                    data[key] = json.dumps(cat_dump[key])
            category_values.append(data)

        if category_values:
            session.execute(insert(GEMS_TAXONOMY_CATEGORIES_TABLE), category_values)

        session.commit()
