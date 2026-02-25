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


from study.dao.conftest import build_real_case_db_study

from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_error_cases(dao_930: DatabaseStudyDao) -> None:
    result = build_real_case_db_study(dao_930)
