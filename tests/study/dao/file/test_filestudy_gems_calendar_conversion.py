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

from datetime import datetime

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.calendar import GemsCalendar, _GemsCalendarData
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_10_2

SAMPLE_CALENDAR = GemsCalendar(
    data=[
        _GemsCalendarData(
            absolute_time_index=0,
            block=0,
            granular_date=datetime(2025, 1, 1, 0, 0, 0),
        ),
        _GemsCalendarData(
            absolute_time_index=1,
            block=0,
            granular_date=datetime(2025, 1, 1, 1, 0, 0),
        ),
    ]
)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_calendar_conversion_roundtrip(
    dao_10_2: StudyDao,
    filestudy_dao_v10_2: FileStudyTreeDao,
    matrix_service: ISimpleMatrixService,
) -> None:
    file_dao = filestudy_dao_v10_2
    file_dao.save_library(GemsLibrary(id="test_library"))
    file_dao.save_gems_calendar(SAMPLE_CALENDAR)

    # Convert from file to db
    StudyConverter(file_dao, dao_10_2, STUDY_VERSION_10_2, matrix_service).convert_study_inputs()
    assert dao_10_2.get_gems_calendar() == SAMPLE_CALENDAR

    # Remove calendar from file dao and convert back from db to file
    calendar_file = file_dao.get_file_study().config.study_path / "input" / "calendar_file.csv"
    calendar_file.unlink()
    assert file_dao.get_gems_calendar() is None
    (file_dao.get_file_study().config.study_path / "input/model-libraries/library.yaml").unlink(missing_ok=True)

    StudyConverter(dao_10_2, file_dao, STUDY_VERSION_10_2, matrix_service)._convert_gems()
    assert file_dao.get_gems_calendar() == SAMPLE_CALENDAR
