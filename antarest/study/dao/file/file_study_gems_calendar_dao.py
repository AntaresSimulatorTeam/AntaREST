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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import override

from antarest.study.business.model.gems.calendar import GemsCalendar
from antarest.study.dao.api.gems_calendar_dao import GemsCalendarDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_gems_calendar_file_path(study_path: Path) -> Path:
    return study_path / "input" / "calendar_file.csv"


class FileStudyGemsCalendarDao(GemsCalendarDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_gems_calendar(self) -> GemsCalendar | None:
        path = _get_gems_calendar_file_path(self.get_file_study().config.study_path)
        if not path.exists():
            return None
        content = path.read_bytes()
        return GemsCalendar.from_csv(content)

    @override
    def save_gems_calendar(self, calendar: GemsCalendar) -> None:
        path = _get_gems_calendar_file_path(self.get_file_study().config.study_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(calendar.to_csv())
