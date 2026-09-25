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


from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.catalog import GEMS_CATALOGS_TABLE
from tests.study.dao.conftest import build_db_dao_10_2


def test_catalogs_are_isolated_and_deleted_with_study(
    db_session: Session, matrix_service: ISimpleMatrixService, gems_catalog: GemsCatalog
) -> None:
    first = build_db_dao_10_2(db_session, matrix_service)
    second = build_db_dao_10_2(db_session, matrix_service)
    other_catalog = gems_catalog.model_copy(update={"taxonomy": "another_taxonomy"})
    first.save_catalog(gems_catalog)
    second.save_catalog(other_catalog)
    assert first.get_catalogs() == [gems_catalog]
    assert second.get_catalogs() == [other_catalog]

    study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first.get_study_id())
    )
    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == study_data_id))
    db_session.commit()
    assert first.get_catalogs() == []
    assert second.get_catalogs() == [other_catalog]
    assert db_session.execute(select(GEMS_CATALOGS_TABLE)).one().taxonomy == "another_taxonomy"
