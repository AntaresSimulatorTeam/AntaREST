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


from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.utils.sql_utils import upsert_one
from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    check_thematic_trimming_complete,
)
from antarest.study.dao.api.thematic_trimming_dao import ThematicTrimmingDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.thematic_trimming import THEMATIC_TRIMMING_TABLE


class DatabaseThematicTrimmingDao(ThematicTrimmingDao, DatabaseDaoBase):
    """Database implementation of ThematicTrimmingDao"""

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        study_id = self._study_id

        stmt = select(THEMATIC_TRIMMING_TABLE).where(THEMATIC_TRIMMING_TABLE.c.study_id == study_id)

        row = self._db_session.execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return ThematicTrimming.model_validate(row.thematic_trimming)

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        check_thematic_trimming_complete(trimming, self.get_impl().get_version())
        session = self._db_session
        study_id = self._study_id
        values = {"study_id": study_id, "thematic_trimming": trimming.model_dump(exclude_none=True)}

        try:
            upsert_one(session, THEMATIC_TRIMMING_TABLE, values)
        except IntegrityError as e:
            # Happens if the study does not exist -> ForeignKey constraint fails
            raise StudyNotFoundError(study_id) from e

        session.commit()
