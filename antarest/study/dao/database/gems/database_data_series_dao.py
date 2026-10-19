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
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import GemsDuplicatedDataSeriesId, GemsInvalidParameterValue
from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.gems_data_series import GemsDataSeriesDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.data_series import GEMS_DATA_SERIES_TABLE


def _check_no_duplicated_ids(data_series: list[GemsDataSeries]) -> None:
    deduplicated_ids = {ds.id for ds in data_series}
    if len(deduplicated_ids) != len(data_series):
        count_ds_per_id = dict.fromkeys(deduplicated_ids, 0)
        duplicated_ids = []
        for current_ds in data_series:
            count_ds_per_id[current_ds.id] += 1
            if count_ds_per_id[current_ds.id] > 1:
                duplicated_ids.append(current_ds.id)

        raise GemsDuplicatedDataSeriesId(f"Duplicated data series IDs: {duplicated_ids}")


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
            try:
                session.execute(insert(table), [self._to_row(ds) for ds in data_series])
            except IntegrityError:
                session.rollback()
                _check_no_duplicated_ids(data_series)
                raise GemsInvalidParameterValue("The data series table is not saved as it should")
        session.commit()

    def _to_row(self, data_series: GemsDataSeries) -> dict[str, Any]:
        values = data_series.model_dump(mode="json")["values"]
        return {
            "study_data_id": self._study_data_id,
            "id": data_series.id,
            "values": json.dumps(values),
        }
