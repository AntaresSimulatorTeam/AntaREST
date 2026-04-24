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
from sqlalchemy.orm import Session

from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.reserve_definition import RESERVE_DEFINITION_TABLE
from tests.study.dao.utils import save_area


def _reserve(id_: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
    base = dict(
        id=id_,
        type=reserve_type,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )
    base.update(overrides)
    return ReserveDefinition(**base)


def test_cascade_delete_on_area_removal(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    db_dao.save_reserve_definitions({"paris": [_reserve("R1")]})

    with db_session:
        db_dao.delete_area("paris")
        rows = db_session.execute(select(RESERVE_DEFINITION_TABLE)).fetchall()
        assert rows == []
