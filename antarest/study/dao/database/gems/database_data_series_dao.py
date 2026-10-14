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

from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.gems_data_series import GemsDataSeriesDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.data_series import GEMS_DATA_SERIES_TABLE


class DatabaseGemsDataSeriesDao(GemsDataSeriesDao, DatabaseDaoBase):
    """Database implementation of GemsDataSeriesDao"""

    @override
    def get_data_series(self) -> list[GemsDataSeries]:
        table = GEMS_DATA_SERIES_TABLE
        rows = self._db_session.execute(
            select(table).where(table.c.study_data_id == self._study_data_id).order_by(table.c.id)
        ).fetchall()
        return [GemsDataSeries.model_validate({"id": row.id, "values": json.loads(row.values)}) for row in rows]

    @override
    def save_data_series(self, data_series: list[GemsDataSeries]) -> None:
        table = GEMS_DATA_SERIES_TABLE
        session = self._db_session

        # Full replace: clear what is already stored for this study, then re-insert the batch.
        session.execute(delete(table).where(table.c.study_data_id == self._study_data_id))
        if data_series:
            # Mirrors `FileStudyGemsDataSeriesDao`, which writes one file per ID: a duplicate ID
            # in the batch silently keeps the last occurrence instead of raising, so both backends
            # behave identically for the same input.
            deduplicated_by_id = {ds.id: ds for ds in data_series}
            session.execute(insert(table), [self._to_row(ds) for ds in deduplicated_by_id.values()])
        session.commit()

    def _to_row(self, data_series: GemsDataSeries) -> dict[str, Any]:
        values = data_series.model_dump(mode="json")["values"]
        return {
            "study_data_id": self._study_data_id,
            "id": data_series.id,
            "values": json.dumps(values),
        }
