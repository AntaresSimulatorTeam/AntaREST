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


from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_nominal_case(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    new_trimming = ThematicTrimming(ov_cost=False, op_cost=False, mrg_price=False, co2_emis=False, dtg_by_plant=False)
    dao.save_thematic_trimming(new_trimming)
    assert dao.get_thematic_trimming() == new_trimming
