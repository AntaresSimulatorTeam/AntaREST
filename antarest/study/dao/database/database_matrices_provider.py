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
from typing import Iterable

from sqlalchemy import select
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.models.area import LOAD_TABLE, MISC_GEN_TABLE, RESERVES_TABLE, SOLAR_TABLE, WIND_TABLE
from antarest.study.dao.database.models.link import (
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    LINK_SERIES_TABLE,
)

MATRIX_TABLES = [
    LOAD_TABLE,
    SOLAR_TABLE,
    WIND_TABLE,
    RESERVES_TABLE,
    MISC_GEN_TABLE,
    LINK_SERIES_TABLE,
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
]


class StudyDatabaseMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, matrix_service: ISimpleMatrixService):
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        with db():
            for table in MATRIX_TABLES:
                stmt = select(table)
                rows = db.session.execute(stmt).fetchall()
                for row in rows:
                    description = f"Matrix used inside table {table.name}, for study {row.study_id}"
                    yield MatrixReference(matrix_id=row.matrix_id, use_description=description)
